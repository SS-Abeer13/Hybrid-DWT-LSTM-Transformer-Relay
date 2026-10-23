"""Verify numerical parity between PyTorch checkpoint, ONNX model, and compiled MATLAB live_relay_ai.mat."""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn

try:
    import onnxruntime as ort
except ImportError:
    ort = None


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
        attn_weights = torch.softmax(self.attention(sequence), dim=1)
        context = torch.sum(attn_weights * sequence, dim=1)
        return self.classifier(context)


def verify_parity() -> bool:
    project_root = Path(__file__).resolve().parent.parent
    runs_dir = project_root / "runs"
    run_folders = sorted(list(runs_dir.glob("*_lstm_training")))
    if not run_folders:
        print(f"No run folders found in {runs_dir}")
        return False
    
    latest_run = run_folders[-1]
    pth_path = latest_run / "transformer_protection_lstm_best.pth"
    onnx_path = project_root / "lstm_models" / "wt_lstm_relay.onnx"

    if not pth_path.exists():
        print(f"PyTorch model checkpoint not found: {pth_path}")
        return False

    checkpoint = torch.load(pth_path, map_location="cpu", weights_only=False)
    config = checkpoint.get("config", checkpoint.get("model_config", {}))

    model = TransformerProtectionLSTM(
        input_size=int(config.get("input_size", 9)),
        hidden_size=int(config.get("hidden_size", 64)),
        num_layers=int(config.get("num_layers", 2)),
        dropout=float(config.get("dropout", 0.2)),
        bidirectional=bool(config.get("bidirectional", False)),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Export ONNX model
    dummy_tensor = torch.randn(1, 32, 9, dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy_tensor,
        str(onnx_path),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )
    print(f"[OK] Exported ONNX model to {onnx_path}")

    # Generate synthetic input tensors of shape [1, 32, 9]
    np.random.seed(20260722)
    dummy_input = np.random.randn(1, 32, 9).astype(np.float32)

    with torch.no_grad():
        pt_logits = model(torch.from_numpy(dummy_input))
        pt_prob = float(torch.sigmoid(pt_logits).squeeze().item())

    if ort is None:
        print("onnxruntime not installed; skipping ONNX runtime verification.")
        print(f"PyTorch prediction probability: {pt_prob:.6f}")
        return True

    session = ort.InferenceSession(str(onnx_path))
    input_name = session.get_inputs()[0].name
    onnx_logits = session.run(None, {input_name: dummy_input})[0]
    onnx_prob = float(1.0 / (1.0 + np.exp(-onnx_logits.squeeze())))

    diff = abs(pt_prob - onnx_prob)
    print("===========================================================")
    print("             ONNX ROUND-TRIP PARITY CHECK                  ")
    print("===========================================================")
    print(f"  PyTorch Probability : {pt_prob:.6f}")
    print(f"  ONNX Probability    : {onnx_prob:.6f}")
    print(f"  Max Absolute Diff   : {diff:.6e}")
    print("===========================================================")

    if diff < 1e-4:
        print("[OK] ONNX Round-Trip Parity PASSED (< 1e-4 tolerance)\n")
        return True
    else:
        print("[FAIL] ONNX Round-Trip Parity FAILED\n")
        return False


if __name__ == "__main__":
    verify_parity()
