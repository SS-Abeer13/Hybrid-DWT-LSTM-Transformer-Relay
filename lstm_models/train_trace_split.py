"""Leak-free training and honest evaluation of the 12-feature, 32-step WT-LSTM relay.

What is different from train_lstm_local.py (and why):
  * Traces are DEDUPLICATED by content fingerprint. The three POSTCALIB source files
    hold the same 600 traces, and identical waveforms repeat inside them.
  * The split is made over TRACES, not windows, so overlapping windows of one
    trace can never sit in both train and test (that leakage inflated test scores).
  * Window labels come from the fault onset measured on the waveform: a window is
    TRIP only once it contains >= 8 samples (5 ms) of fault. Windows straddling the
    onset by fewer samples are ignored. No-trip traces are 0 everywhere.
    (The old rule `window.max() > 0.05` labelled healthy pre-fault windows TRIP.)
  * The threshold is tuned on VALIDATION traces with a relay simulation, and the
    test set is scored the way the relay works: a window at every sample, a trip
    declared after the score stays above threshold for --dwell consecutive samples
    (default 20 = 12.5 ms, the same persistence lstm_predict_wrapper.m applies in Simulink).
    Reported: dependability, security, operate time, trips before fault onset,
    per scenario.
  * The single 'Normal' waveform is held out in TEST so normal-operation security
    is measured on a trace the model never saw.

Usage (from the project root):
    python lstm_models/train_trace_split.py --run-dir runs/20261018_trace_split
    python lstm_models/train_trace_split.py --evaluate-only runs/20260808_lstm_training/transformer_protection_lstm_best.pth --run-dir runs/20261018_trace_split
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import relay87t
from features12 import WINDOW as DWT_WINDOW, trace_features, compensated_diff, plant_compensated_diff
from stress_dataset import FS, detect_fault_onset, load_traces

FEATURE_MODE = "raw"      # 'raw' = Ip - Is (deployed); 'comp' = Yd1-compensated per-unit differential
SOLO_THR = None        # option 2: LSTM may trip alone when its confirmed score >= SOLO_THR (no 87T vote needed); None = off
SOLO_GRID = [0.9, 0.95, 0.98, 0.99, 0.995, 0.998, 0.999, 0.9995, 0.9999]
GATE87T = True          # hybrid evaluation: trip = (87T vote AND confirmed LSTM) OR high-set, as in the Simulink decision chart
THRESHOLD_MODE = "plateau" # "best" = argmax on validation (unstable on a flat plateau); "plateau" = centre of the feasible plateau
SEC_TOLERANCE = 1.0     # plateau mode: security within this many points of the best feasible
DEP_TOLERANCE = 0.0     # threshold tuning: accept dependability within this many points of the best, then maximise security
SEQ = 32               # LSTM sequence length (feature rows), as deployed in Simulink
ONSET_MARGIN = 8       # samples of fault a window must contain to be labelled TRIP (5 ms)
DWELL = 20             # consecutive above-threshold decisions needed to trip (20 samples = 12.5 ms); set by --dwell
DEFAULT_FILES = [
    "datasets/StressTestDataset_POSTCALIB_20260730_072010.mat",
    "datasets/StressTestDataset_POSTCALIB_20260723_014046.mat",
    "datasets/StressTestDataset_POSTCALIB_CHECKPOINT.mat",
]


class TransformerProtectionLSTM(nn.Module):
    """Identical to the class in train_lstm_local.py / export_onnx.py."""

    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float, bidirectional: bool) -> None:
        super().__init__()
        directions = 2 if bidirectional else 1
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers, batch_first=True,
                            dropout=dropout if num_layers > 1 else 0.0, bidirectional=bidirectional)
        self.layer_norm = nn.LayerNorm(hidden_size * directions)
        self.attention = nn.Linear(hidden_size * directions, 1)
        self.classifier = nn.Sequential(nn.Linear(hidden_size * directions, 64), nn.ReLU(), nn.Dropout(dropout), nn.Linear(64, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        sequence, _ = self.lstm(x)
        sequence = self.layer_norm(sequence)
        weights = torch.softmax(self.attention(sequence), dim=1)
        context = (weights * sequence).sum(dim=1)
        return self.classifier(context).squeeze(-1)


# ----------------------------------------------------------------------------- data
def category(scenario: str) -> str:
    s = scenario
    if s.startswith("Normal"):
        return "Normal"
    if s.startswith("Inrush"):
        return "Inrush"
    if s.startswith("Internal_HiZ"):
        return "Internal_HiZ"
    if s.startswith("Internal_SOTF"):
        return "Internal_SOTF"
    if s.startswith("Internal"):
        return "Internal"
    if s.startswith("External_HiZ"):
        return "External_HiZ"
    if s.startswith("External"):
        return "External"
    return s  # Stress_FaultInInrush, Stress_ExtInInrush, Stress_CTSat


def build_traces(root: Path, files: list[str], cache: Path) -> list[dict]:
    if cache.is_file():
        return list(np.load(cache, allow_pickle=True)["traces"])
    unique: dict[str, dict] = {}
    copies: dict[str, int] = defaultdict(int)
    for f in files:
        for t in load_traces(root / f):
            copies[t["fingerprint"]] += 1
            if t["fingerprint"] in unique:
                continue
            if FEATURE_MODE == "plant":
                t["features"] = trace_features(plant_compensated_diff(t["primary"], t["secondary"], plant=t.get("plant", "A")))
            elif FEATURE_MODE == "comp":
                t["features"] = trace_features(compensated_diff(t["primary"], t["secondary"]))
            else:
                t["features"] = trace_features(t["primary"] - t["secondary"])
            if not t["should_trip"]:
                t["onset"] = -1
            elif "checkPassed" in t and np.isfinite(t.get("inceptionTime", np.nan)):
                t["onset"] = int(round(t["inceptionTime"] * FS))   # v2: applied AND verified fault time
            else:
                t["onset"] = detect_fault_onset(t["primary"], t["secondary"])   # v1: metadata time is unreliable
            t["category"] = category(t["scenarioName"])
            plant = t.get("plant", "A")
            a87 = relay87t.analyse(t["primary"], t["secondary"], plant=plant)
            t["vote87"], t["highset"] = a87["vote"], a87["highset"]
            t["fault_pu"] = relay87t.fault_rise_pu(t["primary"], t["secondary"], t["onset"], plant=plant) if t["onset"] >= 0 else float("nan")
            del t["primary"], t["secondary"]
            unique[t["fingerprint"]] = t
    traces = list(unique.values())
    for t in traces:
        t["copies"] = copies[t["fingerprint"]]
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, traces=np.array(traces, dtype=object))
    return traces


def usable(t: dict, min_fault_pu: float) -> str:
    """'' if the trace is used, else the reason it is left out (v2 files only; v1 traces are always used)."""
    if "checkPassed" not in t:
        return ""
    if t["checkPassed"] != 1:
        return "failed generation checks"
    if t["should_trip"] and np.isfinite(t.get("fault_pu", t.get("faultDiffPu", np.nan))) and t.get("fault_pu", t.get("faultDiffPu")) < min_fault_pu:
        return f"internal fault below sensitivity (< {min_fault_pu} pu differential, corrected 87T calibration)"
    return ""


def split_traces(traces: list[dict], seed: int) -> dict[str, list[int]]:
    idx = np.arange(len(traces))
    cats = np.array([t["category"] for t in traces])
    # Fewer than 10 distinct Normal waveforms (v1 data had ONE): keep them all in test.
    held = idx[cats == "Normal"] if (cats == "Normal").sum() < 10 else np.array([], dtype=int)
    rest = np.setdiff1d(idx, held)
    strat = cats[rest].copy()
    for c, n in zip(*np.unique(strat, return_counts=True)):
        if n < 7:                                   # too small to stratify into 3 splits
            strat[strat == c] = "_small"
    tr, tmp = train_test_split(rest, test_size=0.30, stratify=strat, random_state=seed)
    strat_tmp = np.array([strat[np.flatnonzero(rest == i)[0]] for i in tmp])
    va, te = train_test_split(tmp, test_size=0.50, stratify=strat_tmp, random_state=seed)
    return {"train": sorted(tr.tolist()), "val": sorted(va.tolist()), "test": sorted(te.tolist() + held.tolist())}


def window_starts(n_rows: int, stride: int) -> np.ndarray:
    return np.arange(0, n_rows - SEQ + 1, stride)


def decision_sample(start: np.ndarray) -> np.ndarray:
    """0-based current sample at which the window starting at feature row `start` is complete."""
    return start + SEQ - 1 + DWT_WINDOW


def window_labels(trace: dict, starts: np.ndarray) -> np.ndarray:
    """1 = trip, 0 = no trip, -1 = ignore (window holds < ONSET_MARGIN samples of fault)."""
    if not trace["should_trip"]:
        return np.zeros(len(starts), dtype=np.int8)
    end = decision_sample(starts)
    lab = np.full(len(starts), -1, dtype=np.int8)
    lab[end < trace["onset"]] = 0
    lab[end >= trace["onset"] + ONSET_MARGIN] = 1
    return lab


def make_windows(traces: list[dict], ids: list[int], stride: int) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for i in ids:
        f = traces[i]["features"]
        s = window_starts(len(f), stride)
        lab = window_labels(traces[i], s)
        keep = lab >= 0
        xs.append(np.lib.stride_tricks.sliding_window_view(f, SEQ, axis=0)[s[keep]].transpose(0, 2, 1))
        ys.append(lab[keep])
    return np.concatenate(xs).astype(np.float32), np.concatenate(ys).astype(np.float32)


# ----------------------------------------------------------------------------- relay simulation
@torch.no_grad()
def stream_probs(model: nn.Module, features: np.ndarray, device, batch: int = 4096) -> np.ndarray:
    win = np.lib.stride_tricks.sliding_window_view(features, SEQ, axis=0).transpose(0, 2, 1)
    out = []
    for b in range(0, len(win), batch):
        out.append(torch.sigmoid(model(torch.from_numpy(np.ascontiguousarray(win[b:b + batch])).to(device))).cpu().numpy())
    return np.concatenate(out)


def relay_decision(probs: np.ndarray, threshold: float, vote=None, highset=None, solo=None) -> int:
    """Current-sample index of the trip decision, or -1.

    LSTM-confirmed = score >= threshold for DWELL consecutive windows. With the 87T gate (vote/highset given) the relay trips at the first
    sample where (confirmed AND 87T vote) OR high-set (Id > 10 pu, no AI veto). With `solo` (option 2) it ALSO trips where the confirmed
    score at the stricter threshold `solo` is reached, with no 87T vote - as the Simulink decision chart + S-R latch do."""
    trip = -1
    run = 0
    run_solo = 0
    for s, p in enumerate(probs):
        run = run + 1 if p >= threshold else 0
        run_solo = run_solo + 1 if (solo is not None and p >= solo) else 0
        ds = int(decision_sample(np.array(s)))
        if run >= DWELL and (vote is None or (ds < len(vote) and vote[ds])):
            trip = ds
            break
        if solo is not None and run_solo >= DWELL:
            trip = ds
            break
    if highset is not None and highset.any():
        hs = int(np.argmax(highset))
        trip = hs if trip < 0 else min(trip, hs)
    return trip


def relay_report(traces: list[dict], ids: list[int], probs: dict[int, np.ndarray], threshold: float) -> dict:
    rows = []
    for i in ids:
        t = traces[i]
        trip_at = relay_decision(probs[i], threshold, t["vote87"] if GATE87T else None, t["highset"] if GATE87T else None, SOLO_THR)
        tripped = trip_at >= 0
        early = bool(t["should_trip"] and tripped and trip_at < t["onset"])
        rows.append({
            "trace": i, "scenario": t["scenarioName"], "category": t["category"], "should_trip": int(t["should_trip"]),
            "tripped": tripped, "trip_sample": trip_at, "onset_sample": int(t["onset"]),
            "operate_ms": (trip_at - t["onset"]) / FS * 1e3 if (t["should_trip"] and tripped and not early) else None,
            "tripped_before_fault": early,
            "correct": bool((t["should_trip"] and tripped and not early) or (not t["should_trip"] and not tripped)),
        })
    faults = [r for r in rows if r["should_trip"]]
    healthy = [r for r in rows if not r["should_trip"]]
    ms = np.array([r["operate_ms"] for r in faults if r["operate_ms"] is not None])

    def stats(v: np.ndarray) -> dict:
        if not len(v):
            return {"n": 0}
        return {"n": int(len(v)), "median_ms": float(np.median(v)), "p90_ms": float(np.percentile(v, 90)), "max_ms": float(v.max()),
                "within_1_cycle_pct": float(100 * np.mean(v <= 20)), "within_2_cycles_pct": float(100 * np.mean(v <= 40))}

    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
    return {
        "threshold": float(threshold),
        "n_fault_traces": len(faults), "n_healthy_traces": len(healthy),
        "dependability_pct": float(100 * np.mean([r["correct"] for r in faults])) if faults else None,
        "security_pct": float(100 * np.mean([r["correct"] for r in healthy])) if healthy else None,
        "missed_trips": sum(1 for r in faults if not r["tripped"]),
        "trips_before_fault_onset": sum(1 for r in faults if r["tripped_before_fault"]),
        "false_trips": sum(1 for r in healthy if r["tripped"]),
        "operate_time": stats(ms),
        "gate87t": bool(GATE87T),
        "fault_traces_87t_ever_votes_after_onset_pct": float(100 * np.mean([bool((traces[r["trace"]]["vote87"] | traces[r["trace"]]["highset"])[max(r["onset_sample"], 0):].any()) for r in faults])) if faults else None,
        "by_category": {c: {"n": len(v), "correct_pct": float(100 * np.mean([r["correct"] for r in v])),
                            "operate_time": stats(np.array([r["operate_ms"] for r in v if r["operate_ms"] is not None]))}
                        for c, v in sorted(by_cat.items())},
        "rows": rows,
    }


THRESHOLD_GRID = np.round(np.concatenate([np.arange(0.05, 0.95, 0.05), np.arange(0.95, 0.99, 0.01),
                                          [0.99, 0.993, 0.995, 0.997, 0.999, 0.9995]]), 4)
THRESHOLD_RULE = ("on VALIDATION traces: maximise dependability (faults tripped after onset), then security "
                  "(healthy traces kept closed), then the fastest median operate time")


def tune_solo(traces, val_ids, probs, threshold) -> float | None:
    """Plateau rule for the AI-alone trip threshold: among SOLO_GRID (+ 'off'), keep those whose validation security is within SEC_TOLERANCE of
    the best, take the best dependability D* among them, keep those within DEP_TOLERANCE of D*, return the logit-centre of the longest
    contiguous run (a threshold equal to or above the gated one). None = no solo path (off)."""
    global SOLO_THR
    grid = [g for g in SOLO_GRID if g >= threshold] + [None]
    rows = []
    for g in grid:
        SOLO_THR = g
        r = relay_report(traces, val_ids, probs, threshold)
        rows.append((g, r["dependability_pct"], r["security_pct"]))
    SOLO_THR = None
    secs = [r[2] for r in rows if r[2] is not None]
    best_sec = max(secs) if secs else 100.0
    feas = [r for r in rows if r[2] is None or r[2] >= best_sec - SEC_TOLERANCE]
    deps = [r[1] for r in feas if r[1] is not None]
    dstar = max(deps) if deps else 100.0
    plat = [r for r in feas if r[1] is None or r[1] >= dstar - DEP_TOLERANCE]
    names = [r[0] for r in rows]
    pset = {r[0] for r in plat}
    runs, cur = [], []
    for g in names:
        if g in pset:
            cur.append(g)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    run = max(runs, key=lambda r: (len(r), -1 if r[-1] is None else r[-1]))
    num = [g for g in run if g is not None]
    if not num:
        return None
    logit = lambda x: float(np.log(x / (1 - x)))
    mid = 0.5 * (logit(num[0]) + logit(num[-1]))
    return min(num, key=lambda g: abs(logit(g) - mid))


def tune_threshold(traces, val_ids, probs) -> float:
    """Pick the threshold by THRESHOLD_RULE (dependability first) for the current DWELL."""
    rows = []
    for thr in THRESHOLD_GRID:
        r = relay_report(traces, val_ids, probs, float(thr))
        med = r["operate_time"].get("median_ms", 1e9)
        rows.append((r["dependability_pct"], r["security_pct"], med, float(thr)))
    deps = [r[0] for r in rows if r[0] is not None]
    top = max(deps) if deps else 100.0
    ok = [r for r in rows if r[0] is None or r[0] >= top - DEP_TOLERANCE]
    if THRESHOLD_MODE == "best":
        return min(ok, key=lambda r: (-100.0 if r[1] is None else -r[1], r[2], r[3]))[3]
    # plateau mode: every grid threshold whose validation dependability AND security are within tolerance of the best,
    # take the longest contiguous run of such thresholds and return its centre in logit space (the most robust choice:
    # equally far from both ends of the range where the relay still works). Not sensitive to which single trace flips.
    secs = [r[1] for r in ok if r[1] is not None]
    best_sec = max(secs) if secs else 100.0
    feas = {r[3] for r in ok if r[1] is None or r[1] >= best_sec - SEC_TOLERANCE}
    grid = [float(g) for g in THRESHOLD_GRID]
    runs, cur = [], []
    for g in grid:
        if g in feas:
            cur.append(g)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    run = max(runs, key=lambda r: (len(r), r[-1]))
    logit = lambda x: float(np.log(x / (1 - x)))
    mid = 0.5 * (logit(run[0]) + logit(run[-1]))
    return min(run, key=lambda g: abs(logit(g) - mid))


# ----------------------------------------------------------------------------- training
def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


@torch.no_grad()
def window_metrics(model, x, y, device) -> dict:
    model.eval()
    p = np.concatenate([torch.sigmoid(model(torch.from_numpy(x[b:b + 8192]).to(device))).cpu().numpy() for b in range(0, len(x), 8192)])
    return {"auc": float(roc_auc_score(y, p)), "acc_at_0_5": float(np.mean((p >= 0.5) == (y == 1)))}


def train(traces, split, args, device) -> tuple[nn.Module, dict, list]:
    xtr, ytr = make_windows(traces, split["train"], args.train_stride)
    xva, yva = make_windows(traces, split["val"], args.train_stride)
    print(f"Windows: train {len(ytr)} ({ytr.mean():.1%} trip) | val {len(yva)} ({yva.mean():.1%} trip)")
    config = {"input_size": 12, "hidden_size": 64, "num_layers": 2, "dropout": 0.22137852035542321, "bidirectional": False,
              "sequence_length": SEQ, "batch_size": args.batch_size, "learning_rate": args.lr, "weight_decay": 1e-4,
              "seed": args.seed, "feature_mode": FEATURE_MODE, "split": "by-trace (deduplicated)", "labels": f"onset+{ONSET_MARGIN} samples"}
    model = TransformerProtectionLSTM(12, 64, 2, config["dropout"], False).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    pos_weight = torch.tensor([(1 - ytr.mean()) / ytr.mean()], device=device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    xt, yt = torch.from_numpy(xtr), torch.from_numpy(ytr)
    best, stale, history, state = -1.0, 0, [], None
    for epoch in range(1, args.epochs + 1):
        model.train()
        perm = torch.randperm(len(yt))
        losses = []
        t0 = time.time()
        for b in range(0, len(perm), args.batch_size):
            idx = perm[b:b + args.batch_size]
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(xt[idx].to(device)), yt[idx].to(device))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            losses.append(loss.item())
        m = window_metrics(model, xva, yva, device)
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), **{f"val_{k}": v for k, v in m.items()}})
        print(f"Epoch {epoch:02d} loss {np.mean(losses):.4f} | val AUC {m['auc']:.4f} acc {m['acc_at_0_5']:.4f} | {time.time() - t0:.0f}s")
        if m["auc"] > best + 1e-4:
            best, stale = m["auc"], 0
            state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= args.patience:
                break
    model.load_state_dict(state)
    config["best_validation_window_auc"] = best
    return model, config, history


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--files", nargs="*", default=DEFAULT_FILES)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--evaluate-only", type=Path, default=None, help="Score an existing checkpoint on the leak-free test traces.")
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--train-stride", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20261018)
    ap.add_argument("--dwell", type=int, default=20,
                    help="Samples the score must stay above threshold before the AI confirms a trip (20 = 12.5 ms). "
                         "20 ties for best on validation and is 8 samples longer than the worst closed-loop inrush spike.")
    ap.add_argument("--min-fault-pu", type=float, default=0.05,
                    help="v2 data: internal faults whose compensated differential rises by less than this (per unit) "
                         "are physically below relay sensitivity; they are left out and counted in the report.")
    ap.add_argument("--write-settings", action="store_true",
                    help="With --evaluate-only: also write decision_threshold.txt / decision_dwell.txt to --run-dir.")
    ap.add_argument("--solo", action="store_true", help="Option 2: AI-alone trip above a stricter, validation-tuned threshold (no 87T vote needed).")
    ap.add_argument("--no-gate87t", action="store_true", help="Evaluate the LSTM alone (old behaviour) instead of the hybrid 87T-gated relay.")
    ap.add_argument("--features", choices=["raw", "comp", "plant"], default="raw",
                    help="raw = Ip-Is (deployed); comp = Yd1-compensated per-unit differential.")
    ap.add_argument("--threshold-mode", choices=["best", "plateau"], default="plateau",
                    help="best = validation argmax; plateau = centre (logit) of the longest run of thresholds within tolerance.")
    ap.add_argument("--sec-tolerance", type=float, default=1.0, help="plateau mode: security tolerance in points.")
    ap.add_argument("--dep-tolerance", type=float, default=0.0,
                    help="Threshold tuning: accept dependability within this many points of the best, then maximise security.")
    args = ap.parse_args()
    global DWELL, FEATURE_MODE, DEP_TOLERANCE, THRESHOLD_MODE, SEC_TOLERANCE, GATE87T
    GATE87T = not args.no_gate87t
    THRESHOLD_MODE = args.threshold_mode
    SEC_TOLERANCE = args.sec_tolerance
    DWELL = args.dwell
    FEATURE_MODE = args.features
    DEP_TOLERANCE = args.dep_tolerance

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run_dir = args.run_dir if args.run_dir.is_absolute() else args.root / args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    traces = build_traces(args.root, args.files, run_dir / "unique_traces_cache.npz")
    excluded: dict[str, list[str]] = defaultdict(list)
    kept = []
    for t in traces:
        why = usable(t, args.min_fault_pu)
        if why:
            excluded[why].append(t["scenarioName"])
        else:
            kept.append(t)
    traces = kept
    for why, names in excluded.items():
        print(f"Left out {len(names)} traces: {why}")
    split = split_traces(traces, args.seed)
    print(f"Unique traces {len(traces)} | split train {len(split['train'])} val {len(split['val'])} test {len(split['test'])}")
    (run_dir / "split.json").write_text(json.dumps({
        k: [{"trace": i, "scenario": traces[i]["scenarioName"], "source_file": traces[i]["source_file"],
             "source_index": int(traces[i]["source_index"]), "copies_in_sources": int(traces[i]["copies"])} for i in v]
        for k, v in split.items()}, indent=1), encoding="utf-8")

    if args.evaluate_only:
        ckpt = torch.load(args.evaluate_only, map_location="cpu", weights_only=False)
        cfg = ckpt.get("config", ckpt.get("model_config"))
        model = TransformerProtectionLSTM(int(cfg["input_size"]), int(cfg["hidden_size"]), int(cfg["num_layers"]),
                                          float(cfg["dropout"]), bool(cfg["bidirectional"]))
        model.load_state_dict(ckpt["model_state_dict"])
        tag, history = "existing_" + args.evaluate_only.parent.name, []
    else:
        model, cfg, history = train(traces, split, args, device)
        tag = "trained"
    model.to(device).eval()

    probs = {i: stream_probs(model, traces[i]["features"], device) for i in split["val"] + split["test"]}
    threshold = tune_threshold(traces, split["val"], probs)
    global SOLO_THR
    SOLO_THR = tune_solo(traces, split["val"], probs, threshold) if (args.solo and GATE87T) else None
    val_r = relay_report(traces, split["val"], probs, threshold)
    test_r = relay_report(traces, split["test"], probs, threshold)
    sweep = []
    for thr in (0.3, 0.5, 0.7, 0.9, 0.95, 0.98, 0.99, 0.995):
        r = relay_report(traces, split["test"], probs, thr)
        sweep.append({**{k: r[k] for k in ("threshold", "dependability_pct", "security_pct", "missed_trips",
                                             "trips_before_fault_onset", "false_trips")}, "dwell_samples": DWELL})
    xte, yte = make_windows(traces, split["test"], 1)
    win = window_metrics(model, xte, yte, device)

    report = {"model": tag, "config": cfg, "threshold": threshold, "solo_threshold": SOLO_THR, "dwell_samples": DWELL, "threshold_rule": THRESHOLD_RULE + f" [mode {THRESHOLD_MODE}; dependability tolerance {DEP_TOLERANCE} pt; security tolerance {SEC_TOLERANCE} pt; features={FEATURE_MODE}; 87T gate={GATE87T}; solo={SOLO_THR}]",
              "decision_rule": f"score >= threshold for {DWELL} consecutive samples ({DWELL / FS * 1e3:.1f} ms)",
              "test_window_metrics": win, "validation_relay": {k: v for k, v in val_r.items() if k != "rows"},
              "test_relay": {k: v for k, v in test_r.items() if k != "rows"}, "test_threshold_sweep": sweep,
              "data_files": args.files, "n_traces_used": len(traces),
              "excluded_traces": {why: {"count": len(n), "scenarios": sorted(set(n))} for why, n in excluded.items()}}
    (run_dir / f"report_{tag}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (run_dir / f"test_traces_{tag}.json").write_text(json.dumps(test_r["rows"], indent=1), encoding="utf-8")
    if not args.evaluate_only:
        (run_dir / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
        torch.save({"model_state_dict": model.cpu().state_dict(), "config": cfg, "best_threshold": threshold},
                   run_dir / "transformer_protection_lstm_best.pth")
    if not args.evaluate_only or args.write_settings:
        # Plain-text settings so MATLAB can push them into Simulink (set_ai_threshold.m, lstm_predict_wrapper.m).
        (run_dir / "decision_threshold.txt").write_text(f"{threshold:.4f}\n", encoding="utf-8")
        (run_dir / "decision_dwell.txt").write_text(f"{DWELL}\n", encoding="utf-8")
        (run_dir / "decision_solo_threshold.txt").write_text((f"{SOLO_THR:.4f}" if SOLO_THR is not None else "off") + "\n", encoding="utf-8")

    t = report["test_relay"]
    print(f"\n[{tag}] threshold {threshold:.2f} | window AUC {win['auc']:.4f}")
    print(f"TEST relay: dependability {t['dependability_pct']:.1f}% ({t['n_fault_traces']} faults) | security {t['security_pct']:.1f}% "
          f"({t['n_healthy_traces']} healthy) | missed {t['missed_trips']} | pre-fault trips {t['trips_before_fault_onset']} | "
          f"false trips {t['false_trips']} | operate {t['operate_time']}")
    for c, v in t["by_category"].items():
        print(f"  {c:22s} n={v['n']:3d} correct {v['correct_pct']:5.1f}%  operate {v['operate_time'].get('median_ms', float('nan')):.1f} ms median")


if __name__ == "__main__":
    main()
