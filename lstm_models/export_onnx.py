"""Export a trained transformer-protection LSTM checkpoint to Simulink-ready ONNX.

Default artefacts are the checkpoint produced by ``train_lstm_local.py`` and a
fixed input tensor shaped [batch=1, timesteps=1569, features=9].  The fixed
shape intentionally matches the model's training data and the Simulink
Feature Window configuration used for verification.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import onnx
import torch
import torch.nn as nn


class TransformerProtectionLSTM(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float, bidirectional: bool) -> None:
        super().__init__()
        directions = 2 if bidirectional else 1
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=bidirectional,
        )
        self.layer_norm = nn.LayerNorm(hidden_size * directions)
        self.attention = nn.Linear(hidden_size * directions, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * directions, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        sequence, _ = self.lstm(x)
        sequence = self.layer_norm(sequence)
        weights = torch.softmax(self.attention(sequence), dim=1)
        context = (weights * sequence).sum(dim=1)
        return self.classifier(context).squeeze(-1)


class SimulinkWrapper(nn.Module):
    """Produce a probability tensor with stable [batch, 1] output dimensions."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.model(x)).unsqueeze(-1)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=project_root / "runs" / "20260712_lstm_optuna_training" / "transformer_protection_lstm_best.pth",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "lstm_models" / "wt_lstm_relay_20260712.onnx",
    )
    parser.add_argument("--sequence-length", type=int, default=1569)
    args = parser.parse_args()

    if args.sequence_length < 1:
        raise ValueError("sequence-length must be positive")
    if not args.checkpoint.is_file():
        raise FileNotFoundError(args.checkpoint)

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    config = checkpoint.get("config", {})
    required = {"input_size", "hidden_size", "num_layers", "dropout", "bidirectional", "sequence_length"}
    missing = required - set(config)
    if missing:
        raise KeyError(f"Checkpoint config is missing: {sorted(missing)}")
    if config["input_size"] != 9 or config["sequence_length"] != args.sequence_length:
        raise ValueError(f"Checkpoint expects [*, {config['sequence_length']}, {config['input_size']}], not [*, {args.sequence_length}, 9]")

    base = TransformerProtectionLSTM(
        input_size=int(config["input_size"]),
        hidden_size=int(config["hidden_size"]),
        num_layers=int(config["num_layers"]),
        dropout=float(config["dropout"]),
        bidirectional=bool(config["bidirectional"]),
    )
    base.load_state_dict(checkpoint["model_state_dict"])
    model = SimulinkWrapper(base).eval()
    example = torch.randn(1, args.sequence_length, int(config["input_size"]), dtype=torch.float32)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        pytorch_probability = model(example)
    torch.onnx.export(
        model,
        example,
        args.output,
        input_names=["input"],
        output_names=["probability"],
        opset_version=14,
        do_constant_folding=True,
        dynamo=False,
    )

    exported = onnx.load(args.output)
    onnx.checker.check_model(exported)
    input_shape = [dim.dim_value for dim in exported.graph.input[0].type.tensor_type.shape.dim]
    output_shape = [dim.dim_value for dim in exported.graph.output[0].type.tensor_type.shape.dim]
    if input_shape != [1, args.sequence_length, 9] or output_shape != [1, 1]:
        raise RuntimeError(f"Unexpected ONNX interface: input={input_shape}, output={output_shape}")

    try:
        import onnxruntime as ort

        session = ort.InferenceSession(str(args.output), providers=["CPUExecutionProvider"])
        onnx_probability = session.run(["probability"], {"input": example.numpy()})[0]
        max_abs_error = float(abs(onnx_probability - pytorch_probability.numpy()).max())
        if max_abs_error > 1e-5:
            raise RuntimeError(f"ONNX/PyTorch probability mismatch: {max_abs_error}")
        print(f"ONNX/PyTorch max absolute error: {max_abs_error:.3e}")
    except ModuleNotFoundError:
        print("onnxruntime is unavailable; ONNX structural validation completed.")

    print(f"ONNX model: {args.output}")
    print(f"Input:  input [1, {args.sequence_length}, 9] (BTC)")
    print("Output: probability [1, 1] (0 to 1)")


if __name__ == "__main__":
    main()
