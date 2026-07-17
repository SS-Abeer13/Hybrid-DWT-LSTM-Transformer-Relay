"""Train the 9-feature transformer-protection LSTM on the combined MATLAB dataset.

The source dataset is MATLAB v7.3 (HDF5) with X_LSTM stored as
[features, timesteps, traces].  This script converts it to PyTorch's
[traces, timesteps, features] layout, makes a reproducible stratified split,
and stores only new artefacts under runs/.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
import optuna
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Subset, TensorDataset


class TransformerProtectionLSTM(nn.Module):
    """LSTM with attention pooling and binary-logit output."""

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


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def load_dataset(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load MATLAB v7.3 arrays and validate their expected dimensions."""
    with h5py.File(path, "r") as handle:
        raw_x = handle["X_LSTM"]
        raw_y = handle["Y_LSTM"]
        if raw_x.shape[:2] != (9, 1569):
            raise ValueError(f"Unexpected MATLAB X_LSTM layout: {raw_x.shape}")
        # MATLAB saves dimensions in reverse order for this HDF5 dataset.
        x = np.transpose(raw_x[...], (2, 1, 0)).astype(np.float32, copy=False)
        y = np.asarray(raw_y[...]).reshape(-1).astype(np.float32, copy=False)

    if x.shape != (len(y), 1569, 9):
        raise ValueError(f"X/Y shape mismatch: X={x.shape}, Y={y.shape}")
    if not np.isfinite(x).all():
        raise ValueError("X_LSTM contains NaN or Inf values")
    if not np.isin(y, [0.0, 1.0]).all():
        raise ValueError("Y_LSTM must contain only binary labels")
    return x, y


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, loss_fn: nn.Module, device: torch.device) -> tuple[dict, np.ndarray, np.ndarray]:
    model.eval()
    losses: list[float] = []
    labels: list[np.ndarray] = []
    probabilities: list[np.ndarray] = []
    for xb, yb in loader:
        xb = xb.to(device, non_blocking=True)
        yb = yb.to(device, non_blocking=True)
        logits = model(xb)
        losses.append(loss_fn(logits, yb).item())
        probabilities.append(torch.sigmoid(logits).cpu().numpy())
        labels.append(yb.cpu().numpy())

    y_true = np.concatenate(labels).astype(int)
    y_prob = np.concatenate(probabilities)
    y_pred = (y_prob >= 0.5).astype(int)
    metrics = {
        "loss": float(np.mean(losses)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "auc_roc": float(roc_auc_score(y_true, y_prob)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    return metrics, y_true, y_prob


def tune_with_optuna(
    full_dataset: TensorDataset,
    labels: np.ndarray,
    train_indices: np.ndarray,
    device: torch.device,
    output_dir: Path,
    trials: int,
    hpo_epochs: int,
    hpo_samples: int,
    seed: int,
) -> dict[str, int | float | bool]:
    """Tune deployable (unidirectional) architectures on a stratified subset.

    The legacy notebook searched bidirectional models on an older 2,500-trace
    file.  This repeats its Optuna method on the current data while fixing the
    direction to causal/unidirectional for Simulink relay deployment.
    """
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    labels_int = labels.astype(int)
    pool = train_indices
    if len(pool) > hpo_samples:
        pool, _ = train_test_split(pool, train_size=hpo_samples, stratify=labels_int[pool], random_state=seed)
    hpo_train, hpo_val = train_test_split(pool, test_size=0.20, stratify=labels_int[pool], random_state=seed)
    positive = labels_int[hpo_train].sum()
    pos_weight = torch.tensor([(len(hpo_train) - positive) / positive], dtype=torch.float32, device=device)
    print(f"Optuna: {trials} trials using {len(hpo_train)} training and {len(hpo_val)} validation traces.")

    def objective(trial: optuna.Trial) -> float:
        trial_config = {
            "hidden_size": trial.suggest_categorical("hidden_size", [64, 128, 256]),
            "num_layers": trial.suggest_int("num_layers", 1, 3),
            "dropout": trial.suggest_float("dropout", 0.10, 0.50),
            "learning_rate": trial.suggest_float("learning_rate", 1e-4, 1e-2, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64]),
            "weight_decay": trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True),
        }
        model = TransformerProtectionLSTM(9, trial_config["hidden_size"], trial_config["num_layers"], trial_config["dropout"], False).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=trial_config["learning_rate"], weight_decay=trial_config["weight_decay"])
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=hpo_epochs, eta_min=1e-6)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        train_loader = DataLoader(Subset(full_dataset, hpo_train.tolist()), batch_size=trial_config["batch_size"], shuffle=True, num_workers=0, pin_memory=device.type == "cuda")
        val_loader = DataLoader(Subset(full_dataset, hpo_val.tolist()), batch_size=trial_config["batch_size"], shuffle=False, num_workers=0, pin_memory=device.type == "cuda")
        best_auc = -float("inf")
        stale = 0
        for epoch in range(hpo_epochs):
            model.train()
            for xb, yb in train_loader:
                xb, yb = xb.to(device, non_blocking=True), yb.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(model(xb), yb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
            metrics, _, _ = evaluate(model, val_loader, criterion, device)
            auc = metrics["auc_roc"]
            trial.report(auc, epoch)
            if trial.should_prune():
                raise optuna.TrialPruned()
            scheduler.step()
            if auc > best_auc + 1e-5:
                best_auc, stale = auc, 0
            else:
                stale += 1
                if stale >= 4:
                    break
        del model, optimizer
        if device.type == "cuda":
            torch.cuda.empty_cache()
        return best_auc

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed, n_startup_trials=min(10, trials)),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=min(5, trials), n_warmup_steps=3),
        study_name="transformer_protection_lstm_deployment",
    )
    study.optimize(objective, n_trials=trials)
    trial_rows = [
        {"number": trial.number, "state": trial.state.name, "value": trial.value, **trial.params}
        for trial in study.trials
    ]
    (output_dir / "optuna_trials.json").write_text(json.dumps(trial_rows, indent=2), encoding="utf-8")
    best = study.best_params
    print(f"Optuna best validation AUC: {study.best_value:.4f}; parameters: {best}")
    return {
        "input_size": 9,
        "hidden_size": int(best["hidden_size"]),
        "num_layers": int(best["num_layers"]),
        "dropout": float(best["dropout"]),
        "bidirectional": False,
        "sequence_length": 1569,
        "batch_size": int(best["batch_size"]),
        "learning_rate": float(best["learning_rate"]),
        "weight_decay": float(best["weight_decay"]),
        "seed": seed,
        "optuna_best_validation_auc": float(study.best_value),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=project_root / "datasets" / "LSTM_Features_Combined_20260601_024803.mat",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=20260712)
    parser.add_argument("--optuna-trials", type=int, default=0, help="Run this many deployment-oriented Optuna trials before final training.")
    parser.add_argument("--hpo-epochs", type=int, default=12)
    parser.add_argument("--hpo-samples", type=int, default=3000, help="Maximum stratified training traces used for Optuna.")
    args = parser.parse_args()

    if min(args.epochs, args.patience, args.batch_size, args.hpo_epochs, args.hpo_samples) < 1 or args.optuna_trials < 0:
        raise ValueError("training and HPO settings must be positive; optuna-trials may be zero")

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run_dir = args.output_dir or project_root / "runs" / f"{datetime.now():%Y%m%d}_lstm_training"
    run_dir.mkdir(parents=True, exist_ok=False)

    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Loading: {args.data}")
    x, y = load_dataset(args.data)
    print(f"Dataset: X={x.shape}, positive={int(y.sum())}, negative={int(len(y) - y.sum())}")

    indices = np.arange(len(y))
    train_idx, temp_idx = train_test_split(indices, test_size=0.20, stratify=y, random_state=args.seed)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.50, stratify=y[temp_idx], random_state=args.seed)
    print(f"Split: train={len(train_idx)}, validation={len(val_idx)}, test={len(test_idx)}")

    x_tensor = torch.from_numpy(x)
    y_tensor = torch.from_numpy(y)
    del x, y
    pin_memory = device.type == "cuda"
    full_dataset = TensorDataset(x_tensor, y_tensor)

    config: dict[str, int | float | bool] = {
        "input_size": 9,
        "hidden_size": 64,
        "num_layers": 2,
        "dropout": 0.22137852035542321,
        "bidirectional": False,
        "sequence_length": 1569,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "weight_decay": 1e-4,
        "seed": args.seed,
    }
    if args.optuna_trials:
        config = tune_with_optuna(
            full_dataset=full_dataset,
            labels=y_tensor.numpy(),
            train_indices=train_idx,
            device=device,
            output_dir=run_dir,
            trials=args.optuna_trials,
            hpo_epochs=args.hpo_epochs,
            hpo_samples=args.hpo_samples,
            seed=args.seed,
        )

    train_loader = DataLoader(Subset(full_dataset, train_idx.tolist()), batch_size=int(config["batch_size"]), shuffle=True, num_workers=0, pin_memory=pin_memory)
    val_loader = DataLoader(Subset(full_dataset, val_idx.tolist()), batch_size=int(config["batch_size"]), shuffle=False, num_workers=0, pin_memory=pin_memory)
    test_loader = DataLoader(Subset(full_dataset, test_idx.tolist()), batch_size=int(config["batch_size"]), shuffle=False, num_workers=0, pin_memory=pin_memory)
    model = TransformerProtectionLSTM(
        input_size=int(config["input_size"]),
        hidden_size=int(config["hidden_size"]),
        num_layers=int(config["num_layers"]),
        dropout=float(config["dropout"]),
        bidirectional=bool(config["bidirectional"]),
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config["learning_rate"]), weight_decay=float(config["weight_decay"]))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)
    pos_weight = torch.tensor([(len(train_idx) - y_tensor[train_idx].sum().item()) / y_tensor[train_idx].sum().item()], device=device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    print(f"Trainable parameters: {sum(p.numel() for p in model.parameters()):,}; pos_weight={pos_weight.item():.4f}")

    best_auc = -float("inf")
    stale_epochs = 0
    history: list[dict] = []
    checkpoint_path = run_dir / "transformer_protection_lstm_best.pth"
    started = time.perf_counter()

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses: list[float] = []
        for xb, yb in train_loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_losses.append(loss.item())

        validation, _, _ = evaluate(model, val_loader, loss_fn, device)
        scheduler.step(validation["auc_roc"])
        record = {"epoch": epoch, "train_loss": float(np.mean(train_losses)), "learning_rate": optimizer.param_groups[0]["lr"], **validation}
        history.append(record)
        print(
            f"Epoch {epoch:02d}/{args.epochs} | train_loss={record['train_loss']:.4f} "
            f"| val_loss={record['loss']:.4f} | val_auc={record['auc_roc']:.4f} "
            f"| val_f1={record['f1']:.4f}"
        )

        if validation["auc_roc"] > best_auc + 1e-5:
            best_auc = validation["auc_roc"]
            stale_epochs = 0
            torch.save({"model_state_dict": model.state_dict(), "config": config, "best_validation_auc": best_auc}, checkpoint_path)
        else:
            stale_epochs += 1
            if stale_epochs >= args.patience:
                print(f"Early stopping after {epoch} epochs.")
                break

    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    test_metrics, _, _ = evaluate(model, test_loader, loss_fn, device)
    result = {
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(args.data),
        "dataset_shape": [14128, 1569, 9],
        "split_sizes": {"train": len(train_idx), "validation": len(val_idx), "test": len(test_idx)},
        "config": config,
        "best_validation_auc": best_auc,
        "test_metrics": test_metrics,
        "elapsed_seconds": time.perf_counter() - started,
        "checkpoint": str(checkpoint_path),
    }
    (run_dir / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("\nFinal test metrics")
    for name, value in test_metrics.items():
        print(f"  {name}: {value}")
    print(f"Saved checkpoint: {checkpoint_path}")
    print(f"Saved report: {run_dir / 'metrics.json'}")


if __name__ == "__main__":
    main()
