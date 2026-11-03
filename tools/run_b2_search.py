"""D-B2 (BENCHMARK_FAIRNESS_PLAN.md B2): equal hyperparameter search for every same-feature model, the proposed LSTM included.

Stage 'search': 12 random configurations per model (fixed seed, search spaces of the plan written below BEFORE running), trained with the SAME routine
(25 epochs, patience 5 on validation AUC, AdamW, weight decay 1e-4, batch 256, window stride 4) on the inner validation split of folds 1-3 of seed 20261021
(the plan's compute-saving option, applied identically to all six models); score of a configuration = mean validation window AUC over the three folds.
Stage 'final': the chosen configuration of every model is trained on all 3 seeds x 5 folds; standalone and hybrid (87T gate + AI-alone path) relay-mirror rows
on the test traces, thresholds tuned on the fold's validation traces. Output: runs/20261101_v5_benchmark_fair/b2_equal_search/
usage (GPU venv): F:/venv_gpu/Scripts/python.exe -I tools/run_b2_search.py search|final
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.kernel_approximation import Nystroem
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
import benchmark_literature_models as B  # noqa: E402
import train_trace_split as T  # noqa: E402
from v3_checks import relaxed_ok_trace  # noqa: E402

OUT = ROOT / "runs" / "20261101_v5_benchmark_fair" / "b2_equal_search"
CACHE = ROOT / "runs" / "20261029_v5_cv5_seeds" / "traces_cache.npz"
SEEDS = (20261021, 20261022, 20261023)
STRIDE, EPOCHS, PATIENCE = 4, 25, 5
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LR = (3e-4, 1e-3, 3e-3)
SPACES = {   # the plan's table (B2), fixed before running
    "Wavelet-SVM": dict(n_components=(60, 120, 240), gamma_x=(0.5, 1.0, 2.0), alpha=(1e-5, 1e-4, 1e-3)),
    "Wavelet-RF": dict(n_estimators=(100, 200, 400), max_depth=(8, 12, 16, None), min_samples_leaf=(1, 5, 20)),
    "Wavelet-ANN": dict(hidden1=(32, 64, 128), hidden2=(16, 32, 64), dropout=(0.1, 0.2, 0.3), lr=LR),
    "1D-CNN": dict(channels=(16, 32, 64), kernel=(3, 5, 7), layers=(2, 3), dropout=(0.1, 0.2, 0.3), lr=LR),
    "Wavelet-GRU": dict(hidden=(32, 64, 128), layers=(1, 2), dropout=(0.1, 0.2, 0.3), lr=LR),
    "Proposed LSTM": dict(hidden=(32, 64, 128), layers=(1, 2), dropout=(0.1, 0.2, 0.3), lr=LR),
}
N_CONFIGS, SEARCH_SEED = 12, 20261102


class CnnTuned(nn.Module):
    def __init__(self, channels: int, kernel: int, layers: int, dropout: float):
        super().__init__()
        blocks, c_in = [], 12
        for i in range(layers):
            c_out = channels * (2 ** min(i, 1))
            blocks += [nn.Conv1d(c_in, c_out, kernel, padding=kernel // 2), nn.BatchNorm1d(c_out), nn.ReLU()]
            if i < layers - 1:
                blocks.append(nn.MaxPool1d(2))
            c_in = c_out
        self.conv = nn.Sequential(*blocks, nn.AdaptiveAvgPool1d(1), nn.Flatten())
        self.classifier = nn.Sequential(nn.Linear(c_in, 32), nn.ReLU(), nn.Dropout(dropout), nn.Linear(32, 1))

    def forward(self, x):
        return self.classifier(self.conv(x.transpose(1, 2))).view(-1)


def configs(name: str) -> list[dict]:
    rng = np.random.RandomState(SEARCH_SEED + sum(map(ord, name)))
    sp = SPACES[name]
    return [{k: v[rng.randint(len(v))] for k, v in sp.items()} for _ in range(N_CONFIGS)]


def build(name: str, cfg: dict, seed: int):
    if name == "Wavelet-ANN":
        return B.MLPModel(48, cfg["hidden1"], cfg["hidden2"], cfg["dropout"])
    if name == "1D-CNN":
        return CnnTuned(cfg["channels"], cfg["kernel"], cfg["layers"], cfg["dropout"])
    if name == "Wavelet-GRU":
        return B.GRUModel(12, cfg["hidden"], cfg["layers"], cfg["dropout"])
    if name == "Proposed LSTM":
        return T.TransformerProtectionLSTM(12, cfg["hidden"], cfg["layers"], cfg["dropout"], False)
    if name == "Wavelet-SVM":
        return make_pipeline(StandardScaler(), Nystroem(gamma=cfg["gamma_x"] / 48.0, n_components=cfg["n_components"], random_state=seed),
                             SGDClassifier(loss="log_loss", penalty="l2", alpha=cfg["alpha"], max_iter=1000, random_state=seed))
    return RandomForestClassifier(n_estimators=cfg["n_estimators"], max_depth=cfg["max_depth"], min_samples_leaf=cfg["min_samples_leaf"], n_jobs=-1, random_state=seed)


def load_traces():
    traces = []
    for t in np.load(CACHE, allow_pickle=True)["traces"]:
        if "checkPassed" in t and not relaxed_ok_trace(t):
            continue
        t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < B.MIN_FAULT_PU)
        traces.append(t)
    T.DWELL = B.DWELL; T.FEATURE_MODE = "plant"; T.THRESHOLD_MODE = "plateau"; T.DEP_TOLERANCE = 2.0; T.SEC_TOLERANCE = 1.0; T.category = B.group_of
    return traces


def folds(traces, seed):
    names = np.array([t["scenarioName"] for t in traces]); idx = np.arange(len(traces)); strat = names.copy()
    for c, n in zip(*np.unique(names, return_counts=True)):
        if n < 5:
            strat[names == c] = "_small"
    for k, (tr_all, te) in enumerate(StratifiedKFold(5, shuffle=True, random_state=seed).split(idx, strat), 1):
        trainable = [i for i in tr_all if not traces[i]["undetectable"]]
        st = strat[trainable].copy()
        for c, n_c in zip(*np.unique(st, return_counts=True)):
            if n_c < 4:
                st[st == c] = "_small"
        if (st == "_small").sum() == 1:
            st[st == "_small"] = st[0]
        tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=seed + k)
        yield k, sorted(tr.tolist()), sorted(va.tolist()), sorted(te.tolist())


def fit_eval(name, cfg, traces, tr, va, seed, k):
    """Train one model; returns (model, val window AUC, epochs used, is_torch)."""
    xtr, ytr = T.make_windows(traces, tr, stride=STRIDE)
    xva, yva = T.make_windows(traces, va, stride=STRIDE)
    m = build(name, cfg, seed + k)
    if name in ("Wavelet-SVM", "Wavelet-RF"):
        xp, xv = B.pool_window_features(xtr), B.pool_window_features(xva)
        rng = np.random.RandomState(seed + k)
        sub = rng.choice(len(ytr), min(len(ytr), 30000 if name == "Wavelet-SVM" else 50000), replace=False)
        m.fit(xp[sub], ytr[sub].astype(np.int64))
        return m, float(roc_auc_score(yva, m.predict_proba(xv)[:, 1])), None, False
    if name == "Wavelet-ANN":
        xtr, xva = B.pool_window_features(xtr), B.pool_window_features(xva)
    torch.manual_seed(seed + k)
    m, auc = B.train_torch_model(m, xtr, ytr, xva, yva, DEVICE, epochs=EPOCHS, batch_size=256, lr=cfg["lr"], patience=PATIENCE)
    return m, float(auc), int(m.epochs_used), True


def search():
    traces = load_traces()
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "search_results.json"
    res = json.loads(f.read_text()) if f.is_file() else {}
    fl = [x for x in folds(traces, SEEDS[0]) if x[0] <= 3]
    for name in SPACES:
        res.setdefault(name, [])
        for ci, cfg in enumerate(configs(name)):
            if ci < len(res[name]):
                continue
            t0 = time.time()
            aucs, eps = [], []
            for k, tr, va, te in fl:
                m, auc, ep, _ = fit_eval(name, cfg, traces, tr, va, SEEDS[0], k)
                aucs.append(auc); eps.append(ep)
            res[name].append({"config": cfg, "val_auc_per_fold": aucs, "val_auc": float(np.mean(aucs)), "epochs": eps})
            f.write_text(json.dumps(res, indent=1, default=str))
            print(f"{name} config {ci + 1}/{N_CONFIGS} {cfg} val AUC {np.mean(aucs):.5f} ({time.time() - t0:.0f}s)", flush=True)
    best = {n: max(r, key=lambda x: x["val_auc"])["config"] for n, r in res.items()}
    (OUT / "chosen_configs.json").write_text(json.dumps(best, indent=1, default=str))
    print("chosen:", json.dumps(best, default=str))


def final():
    traces = load_traces()
    best = json.loads((OUT / "chosen_configs.json").read_text())
    for seed in SEEDS:
        for k, tr, va, te in folds(traces, seed):
            f = OUT / f"final_seed{seed}_fold{k}.json"
            if f.is_file():
                continue
            out = {}
            for name in SPACES:
                cfg = best[name]
                cfg = {kk: (None if v == "None" else v) for kk, v in cfg.items()}
                m, auc, ep, is_t = fit_eval(name, cfg, traces, tr, va, seed, k)
                if is_t:
                    probs = {i: B.stream_probs_torch(m, traces[i]["features"], is_mlp=(name == "Wavelet-ANN"), device=DEVICE) for i in va + te}
                else:
                    probs = {i: B.stream_probs_sklearn(m, traces[i]["features"]) for i in va + te}
                res = {}
                for mode, variant in (("standalone", "LSTM alone"), ("hybrid", "Hybrid + AI-alone path")):
                    thr, solo = B.tune_variant(traces, va, probs, variant)
                    rows = B.rows_for(traces, te, probs, variant, thr, solo)
                    for r in rows:
                        r["seed"], r["fold"] = seed, k
                    res[mode] = rows
                out[name] = {**res, "val_auc": auc, "epochs_used": ep, "config": cfg}
                print(f"seed {seed} fold {k} {name}: val AUC {auc:.4f} epochs {ep}", flush=True)
            f.write_text(json.dumps(out, default=float))


if __name__ == "__main__":
    {"search": search, "final": final}[sys.argv[1]]()
