"""Evaluate retrained WT-LSTM transformer protection model across all stress test categories."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import h5py
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


def main() -> None:
    project_root = Path(__file__).resolve().parent
    features_file = project_root / "datasets" / "LSTM_Features_Combined_20260722_134131.mat"
    model_file = project_root / "runs" / "20260722_lstm_training" / "transformer_protection_lstm_best.pth"

    if not features_file.exists():
        print(f"Error: Features file not found at {features_file}")
        return

    if not model_file.exists():
        print(f"Error: Model checkpoint not found at {model_file}")
        return

    print("Loading features from MAT file using h5py...")
    import h5py

    with h5py.File(features_file, "r") as f:
        # HDF5 stores arrays transposed: (9, T, N) -> transpose to (N, T, 9)
        x_raw = np.array(f["X_LSTM"])
        if x_raw.ndim == 3 and x_raw.shape[0] == 9:
            x_data = np.transpose(x_raw, (2, 1, 0)).astype(np.float32)
        else:
            x_data = x_raw.astype(np.float32)

        y_data = np.array(f["Y_LSTM"]).squeeze().astype(np.int64)

        meta = f["metadata"]
        sc_refs = meta["scenarioName"][()]
        scenarios = ["".join(chr(c[0]) for c in f[r][()]) for r in sc_refs.squeeze()]

    print(f"Dataset shape: {x_data.shape}, Total samples: {len(y_data)}")

    # Load PyTorch checkpoint
    checkpoint = torch.load(model_file, map_location="cpu", weights_only=False)
    config = checkpoint.get("config", checkpoint.get("model_config", {}))
    best_threshold = checkpoint.get("best_threshold", 0.50)

    print(f"Loaded checkpoint trained for {checkpoint.get('epoch', '?')} epochs.")
    print(f"Model config: {config}")
    print(f"Best decision threshold: {best_threshold:.4f}\n")

    model = TransformerProtectionLSTM(
        input_size=int(config["input_size"]),
        hidden_size=int(config["hidden_size"]),
        num_layers=int(config["num_layers"]),
        dropout=float(config["dropout"]),
        bidirectional=bool(config["bidirectional"]),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    with torch.no_grad():
        x_tensor = torch.tensor(x_data, dtype=torch.float32)
        logits = model(x_tensor)
        probs_list = torch.sigmoid(logits).squeeze().tolist()
        probs = np.array(probs_list, dtype=np.float32)

    preds = (probs >= best_threshold).astype(np.int64)
    is_correct = (preds == y_data)

    print("=" * 95)
    print("             HYBRID DWT-LSTM RELAY STRESS TEST EVALUATION REPORT")
    print("=" * 95)
    print(f"{'Sample':<8} | {'Scenario Name':<26} | {'Expected':<8} | {'Prob':<8} | {'Pred':<6} | {'Status':<6}")
    print("-" * 95)

    category_results: dict[str, list[bool]] = {}
    category_probs: dict[str, list[float]] = {}

    for idx in range(len(y_data)):
        sc_name = scenarios[idx]
        exp_str = "TRIP" if y_data[idx] == 1 else "BLOCK"
        pred_str = "TRIP" if preds[idx] == 1 else "BLOCK"
        prob_val = float(probs[idx])
        status = "PASS" if is_correct[idx] else "FAIL"

        # Categorize
        if sc_name.startswith("Normal"):
            cat = "Normal Steady State"
        elif sc_name.startswith("Inrush"):
            cat = "Magnetizing Inrush"
        elif "HiZ" in sc_name:
            cat = "High-Impedance Faults (HiZ)"
        elif sc_name.startswith("Internal"):
            cat = "Internal Low-Z Faults"
        elif sc_name.startswith("External"):
            cat = "External Low-Z Faults"
        elif "Inrush" in sc_name:
            cat = "Faults during Inrush"
        elif "CTSat" in sc_name:
            cat = "CT Saturation Stress"
        else:
            cat = "Other Scenarios"

        category_results.setdefault(cat, []).append(is_correct[idx])
        category_probs.setdefault(cat, []).append(prob_val)

        print(f"[{idx+1:2d}/80]   | {sc_name:<26} | {exp_str:<8} | {prob_val:<8.4f} | {pred_str:<6} | {status:<6}")

    print("=" * 95)
    print("\n" + "=" * 65)
    print("           CATEGORY ACCURACY & RELIABILITY BREAKDOWN")
    print("=" * 65)
    print(f"{'Category Name':<32} | {'Samples':<8} | {'Avg Prob':<10} | {'Accuracy':<8}")
    print("-" * 65)

    total_correct = int(np.sum(is_correct))
    overall_acc = (total_correct / len(y_data)) * 100.0

    for cat_name, res_list in sorted(category_results.items()):
        acc = (sum(res_list) / len(res_list)) * 100.0
        mean_p = float(np.mean(category_probs[cat_name]))
        print(f"{cat_name:<32} | {len(res_list):<8d} | {mean_p:<10.4f} | {acc:<7.1f}%")

    print("-" * 65)
    print(f"{'OVERALL ALL STRESS SCENARIOS':<32} | {len(y_data):<8d} | {'--':<10} | {overall_acc:<7.1f}%")
    print("=" * 65)


if __name__ == "__main__":
    main()
