"""Phase C of IMPLEMENTATION_PLAN_V3.md: grouped 5-fold cross-validation, baseline of the deployed model, ablations, OOD scoring.

    python lstm_models/train_cv_v3.py cv --files datasets/StressDataset_v3_<run>.mat --run-dir runs/<date>_v3_cv5 --seed 20261021
    python lstm_models/train_cv_v3.py baseline --files <v3 main> [--ood <v3 OOD>] --checkpoint runs/20261020_v3_87tfix/transformer_protection_lstm_best.pth \
           --ai-threshold 0.90 --solo-threshold 0.995 --run-dir runs/<date>_v3data_baseline

Evaluation protocol (plan section 3, fixed before training):
  * unit = one trace; every trace is tested exactly once (5 folds stratified by scenario, grouped by trace; fingerprints are de-duplicated)
  * in each fold 15 % of the training part (stratified) is the VALIDATION set used for the plateau threshold rules (AI and solo thresholds); the LSTM
    sees the training traces only
  * relay mirror: trip = high-set OR (87T vote AND confirmed LSTM >= AI_Threshold) OR (confirmed LSTM >= AI_Solo_Threshold); confirmed = min of the last
    20 outputs (dwell 20); 87T = corrected calibration (relay87t.py)
  * labels: trip windows start 8 samples after the MEASURED onset. Internal faults whose corrected differential rise is < 0.05 pu are 'undetectable':
    excluded from training and from the headline numbers, but scored and reported separately (never dropped silently)
  * four variants from the SAME predictions (C6 ablation): 87T alone, LSTM alone, hybrid (87T gate), hybrid + AI-alone path; thresholds tuned per variant
  * per category: dependability / security with Wilson 95 % intervals on the pooled out-of-fold decisions
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_trace_split as T  # noqa: E402
from coverage_report_v3 import group_of  # noqa: E402
from v3_checks import relaxed_ok_trace  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FS = 1600
VARIANTS = ("87T alone", "LSTM alone", "Hybrid (87T gate)", "Hybrid + AI-alone path")
MIN_FAULT_PU = 0.05


# ------------------------------------------------------------------------------------------------ helpers
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0.0, c - h), 100 * min(1.0, c + h))


def configure(args) -> None:
    T.DWELL = args.dwell
    T.FEATURE_MODE = "plant"
    T.THRESHOLD_MODE = "plateau"
    T.DEP_TOLERANCE = args.dep_tolerance
    T.SEC_TOLERANCE = args.sec_tolerance
    T.category = group_of          # v3 scenario groups are the reporting categories


def load_traces(args, cache: Path) -> list[dict]:
    configure(args)
    traces = T.build_traces(ROOT, args.files, cache)
    kept = []
    for t in traces:
        if "checkPassed" in t and not relaxed_ok_trace(t):
            continue                                         # failed generator checks (beyond the two benign types of v3_checks.py): never used
        t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < MIN_FAULT_PU)
        kept.append(t)
    if getattr(args, "limit", 0):
        rs = np.random.RandomState(0)
        kept = [kept[i] for i in sorted(rs.choice(len(kept), size=min(args.limit, len(kept)), replace=False))]
    print(f"traces: {len(traces)} built, {len(kept)} pass the generator checks, {sum(t['undetectable'] for t in kept)} undetectable (< {MIN_FAULT_PU} pu)", flush=True)
    return kept


def rows_for(traces, ids, probs, variant: str, thr: float, solo) -> list[dict]:
    """Relay-mirror decisions for one variant (sets the module globals of train_trace_split for the call)."""
    T.GATE87T = variant != "LSTM alone"
    T.SOLO_THR = solo if variant == "Hybrid + AI-alone path" else None
    pr = probs
    if variant == "87T alone":                                # confirmed LSTM always true -> trip at the first 87T vote / high-set
        pr = {i: np.ones(len(traces[i]["features"]) - T.SEQ + 1, dtype=np.float32) for i in ids}
        thr = 0.5
    rep = T.relay_report(traces, ids, pr, thr)
    for r in rep["rows"]:
        r["variant"] = variant
    return rep["rows"]


def tune_variant(traces, val_ids, probs, variant: str):
    """(AI threshold, solo threshold) for a variant by the plateau rules on the validation traces."""
    if variant == "87T alone":
        return 0.5, None
    T.GATE87T = variant != "LSTM alone"
    T.SOLO_THR = None
    thr = T.tune_threshold(traces, val_ids, probs)
    solo = T.tune_solo(traces, val_ids, probs, thr) if variant == "Hybrid + AI-alone path" else None
    T.SOLO_THR = None
    return thr, solo


def summarise(rows: list[dict]) -> dict:
    """Headline metrics on rows of ONE variant (undetectable faults separate)."""
    head = [r for r in rows if not r.get("undetectable")]
    faults = [r for r in head if r["should_trip"]]
    healthy = [r for r in head if not r["should_trip"]]
    ms = np.array([r["operate_ms"] for r in faults if r["operate_ms"] is not None])
    undet = [r for r in rows if r.get("undetectable")]
    out = {
        "n_fault": len(faults), "n_healthy": len(healthy),
        "dependability_pct": 100 * float(np.mean([r["correct"] for r in faults])) if faults else None,
        "security_pct": 100 * float(np.mean([r["correct"] for r in healthy])) if healthy else None,
        "missed": sum(1 for r in faults if not r["tripped"]), "false_trips": sum(1 for r in healthy if r["tripped"]),
        "pre_fault_trips": sum(1 for r in faults if r["tripped_before_fault"]),
        "operate": {"n": int(len(ms)), "median_ms": float(np.median(ms)) if len(ms) else None, "p90_ms": float(np.percentile(ms, 90)) if len(ms) else None,
                    "max_ms": float(ms.max()) if len(ms) else None, "within_1_cycle_pct": float(100 * np.mean(ms <= 20)) if len(ms) else None,
                    "within_2_cycles_pct": float(100 * np.mean(ms <= 40)) if len(ms) else None},
        "undetectable": {"n": len(undet), "tripped_pct": 100 * float(np.mean([r["tripped"] for r in undet])) if undet else None},
    }
    cats = defaultdict(list)
    for r in head:
        cats[r["category"]].append(r)
    out["by_category"] = {}
    for c, v in sorted(cats.items()):
        k = sum(1 for r in v if r["correct"])
        lo, hi = wilson(k, len(v))
        ms_c = np.array([r["operate_ms"] for r in v if r["operate_ms"] is not None])
        out["by_category"][c] = {"n": len(v), "correct": k, "correct_pct": 100 * k / len(v), "ci95": [lo, hi], "should_trip": bool(v[0]["should_trip"]),
                                 "median_ms": float(np.median(ms_c)) if len(ms_c) else None}
    return out


def annotate(rows, traces) -> None:
    for r in rows:
        t = traces[r["trace"]]
        r["undetectable"] = bool(t["undetectable"])
        r["scenario"] = t["scenarioName"]


# ------------------------------------------------------------------------------------------------ cross-validation
def cmd_cv(args) -> None:
    run = Path(args.run_dir) if Path(args.run_dir).is_absolute() else ROOT / args.run_dir
    run.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache) if args.cache else run / "traces_cache.npz"
    traces = load_traces(args, cache)
    device = torch.device("cpu")
    names = np.array([t["scenarioName"] for t in traces])
    idx = np.arange(len(traces))
    strat = names.copy()
    for c, n in zip(*np.unique(names, return_counts=True)):
        if n < args.folds:
            strat[names == c] = "_small"
    skf = StratifiedKFold(n_splits=args.folds, shuffle=True, random_state=args.seed)
    all_rows = {v: [] for v in VARIANTS}
    fold_summ = []
    t_all = time.time()
    for k, (tr_all, te) in enumerate(skf.split(idx, strat), 1):
        fdir = run / f"fold{k}"
        if (fdir / "result.json").is_file():
            res = json.loads((fdir / "result.json").read_text(encoding="utf-8"))
            for v in VARIANTS:
                all_rows[v] += res["rows"][v]
            fold_summ.append(res["summary"]); print(f"fold {k}: done, skipping", flush=True)
            continue
        fdir.mkdir(exist_ok=True)
        trainable = [i for i in tr_all if not traces[i]["undetectable"]]
        st = strat[trainable].copy()
        for c, n_c in zip(*np.unique(st, return_counts=True)):
            if n_c < 4:
                st[st == c] = "_small"                          # rare classes cannot be stratified
        if (st == "_small").sum() == 1:
            st[st == "_small"] = st[0]
        tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=args.seed + k)
        T.set_seed(args.seed + k)
        args.batch_size, args.lr, args.patience = 256, 1e-3, 5
        t0 = time.time()
        model, cfg, hist = T.train(traces, {"train": sorted(tr.tolist()), "val": sorted(va.tolist())}, args, device)
        model.to(device).eval()
        torch.save({"model_state_dict": model.cpu().state_dict(), "config": cfg}, fdir / "transformer_protection_lstm_best.pth")
        model.to(device).eval()
        ids_eval = sorted(set(va.tolist()) | set(te.tolist()))
        probs = {i: T.stream_probs(model, traces[i]["features"], device) for i in ids_eval}
        va_ids = sorted(va.tolist()); te_ids = sorted(te.tolist())
        settings, res_rows, summ = {}, {}, {}
        for v in VARIANTS:
            thr, solo = tune_variant(traces, va_ids, probs, v)
            rows = rows_for(traces, te_ids, probs, v, thr, solo)
            for r in rows:
                r["fold"] = k
            annotate(rows, traces)
            settings[v] = {"ai_threshold": thr, "solo_threshold": solo}
            res_rows[v] = rows
            summ[v] = summarise(rows)
            all_rows[v] += rows
        fold_summ.append({"fold": k, "n_train": int(len(tr)), "n_val": int(len(va)), "n_test": int(len(te)), "settings": settings, "variants": summ,
                          "epochs": len(hist), "train_minutes": (time.time() - t0) / 60})
        (fdir / "result.json").write_text(json.dumps({"summary": fold_summ[-1], "rows": res_rows}, default=float), encoding="utf-8")
        h = summ["Hybrid + AI-alone path"]
        print(f"fold {k}: {len(tr)}/{len(va)}/{len(te)} traces, {len(hist)} epochs, {(time.time() - t0) / 60:.1f} min | hybrid+solo: dependability {h['dependability_pct']:.1f} % "
              f"security {h['security_pct']:.1f} % | thresholds {settings['Hybrid + AI-alone path']}", flush=True)
    write_cv_summary(run, all_rows, fold_summ, args, (time.time() - t_all) / 60)


def write_cv_summary(run: Path, all_rows, fold_summ, args, minutes: float) -> None:
    pooled = {v: summarise(all_rows[v]) for v in VARIANTS}
    L = [f"Grouped {args.folds}-fold CV, seed {args.seed}; {sum(len(set(r['trace'] for r in all_rows[VARIANTS[0]])) for _ in [0])} traces tested once; run time {minutes:.0f} min", "=" * 100, ""]
    L.append("Pooled out-of-fold headline metrics (undetectable faults excluded and reported below):")
    L.append(f"{'variant':26s} {'dep %':>7s} {'sec %':>7s} {'missed':>6s} {'false':>5s} {'pre':>4s} {'med ms':>7s} {'p90':>6s} {'max':>6s} {'<=1cyc':>6s} {'<=2cyc':>6s} | undetectable tripped")
    for v in VARIANTS:
        s = pooled[v]; o = s["operate"]
        L.append(f"{v:26s} {s['dependability_pct']:7.2f} {s['security_pct']:7.2f} {s['missed']:6d} {s['false_trips']:5d} {s['pre_fault_trips']:4d} {o['median_ms'] or float('nan'):7.1f} "
                 f"{o['p90_ms'] or float('nan'):6.1f} {o['max_ms'] or float('nan'):6.1f} {o['within_1_cycle_pct'] or float('nan'):6.1f} {o['within_2_cycles_pct'] or float('nan'):6.1f} | "
                 f"{s['undetectable']['tripped_pct'] if s['undetectable']['tripped_pct'] is not None else float('nan'):.0f} % of {s['undetectable']['n']}")
    L += ["", "Per fold, hybrid + AI-alone path (mean +/- sd over folds):"]
    for key in ("dependability_pct", "security_pct"):
        v = np.array([f["variants"]["Hybrid + AI-alone path"][key] for f in fold_summ])
        L.append(f"  {key:18s} {v.mean():.2f} +/- {v.std(ddof=1) if len(v) > 1 else 0:.2f}   folds: " + ", ".join(f"{x:.1f}" for x in v))
    thr = [(f["settings"]["Hybrid + AI-alone path"]["ai_threshold"], f["settings"]["Hybrid + AI-alone path"]["solo_threshold"]) for f in fold_summ]
    L.append(f"  thresholds (AI, solo) per fold: {thr}")
    L += ["", "Per category, pooled out-of-fold, 95 % Wilson intervals (correct = trip after onset for faults, no trip for healthy):"]
    cats = sorted({c for v in VARIANTS for c in pooled[v]["by_category"]})
    L.append(f"{'category':22s} {'n':>4s} " + " | ".join(f"{v[:22]:>26s}" for v in VARIANTS))
    for c in cats:
        n = pooled[VARIANTS[-1]]["by_category"].get(c, {}).get("n", 0)
        cells = []
        for v in VARIANTS:
            b = pooled[v]["by_category"].get(c)
            cells.append(f"{b['correct_pct']:6.1f}% [{b['ci95'][0]:5.1f},{b['ci95'][1]:5.1f}]" if b else " " * 26)
        L.append(f"{c:22s} {n:4d} " + " | ".join(f"{x:>26s}" for x in cells))
    (run / "cv_summary.txt").write_text("\n".join(L), encoding="utf-8")
    (run / "cv_summary.json").write_text(json.dumps({"pooled": pooled, "folds": fold_summ, "args": {k: str(v) for k, v in vars(args).items()}}, default=float, indent=1), encoding="utf-8")
    print("\n".join(L))


# ------------------------------------------------------------------------------------------------ baseline / OOD scoring of a fixed checkpoint
def cmd_baseline(args) -> None:
    run = Path(args.run_dir) if Path(args.run_dir).is_absolute() else ROOT / args.run_dir
    run.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")
    ckpt = torch.load(ROOT / args.checkpoint, map_location="cpu", weights_only=False)
    cfg = ckpt.get("config", ckpt.get("model_config"))
    model = T.TransformerProtectionLSTM(int(cfg["input_size"]), int(cfg["hidden_size"]), int(cfg["num_layers"]), float(cfg["dropout"]), bool(cfg["bidirectional"]))
    model.load_state_dict(ckpt["model_state_dict"]); model.eval()
    out = {}
    for label, files in (("main", args.files), ("ood", args.ood or [])):
        if not files:
            continue
        args.files = files
        traces = load_traces(args, run / f"traces_cache_{label}.npz")
        ids = list(range(len(traces)))
        probs = {i: T.stream_probs(model, traces[i]["features"], device) for i in ids}
        rows_all = {}
        for v in ("87T alone", "Hybrid (87T gate)", "Hybrid + AI-alone path"):
            rows = rows_for(traces, ids, probs, v, args.ai_threshold, args.solo_threshold)
            annotate(rows, traces)
            rows_all[v] = summarise(rows)
        out[label] = rows_all
        print(f"[{label}] {len(traces)} traces: " + " | ".join(f"{v}: dep {s['dependability_pct']:.1f} % sec {s['security_pct']:.1f} %" for v, s in rows_all.items()), flush=True)
    (run / "baseline.json").write_text(json.dumps(out, default=float, indent=1), encoding="utf-8")
    L = [f"Deployed checkpoint {args.checkpoint} (AI {args.ai_threshold}, solo {args.solo_threshold}, dwell {args.dwell}) scored on v3 data - NO retraining", ""]
    for label, d in out.items():
        for v, s in d.items():
            L.append(f"[{label}] {v}: dependability {s['dependability_pct']:.2f} % ({s['n_fault']} faults), security {s['security_pct']:.2f} % ({s['n_healthy']} healthy), missed {s['missed']}, false {s['false_trips']}, "
                     f"operate median {s['operate']['median_ms']} ms; undetectable tripped {s['undetectable']['tripped_pct']} % of {s['undetectable']['n']}")
        L.append(f"[{label}] per category, 'Hybrid + AI-alone path':")
        for c, b in d["Hybrid + AI-alone path"]["by_category"].items():
            L.append(f"    {c:20s} n={b['n']:4d}  {b['correct_pct']:6.1f} % [{b['ci95'][0]:5.1f}, {b['ci95'][1]:5.1f}]  median {b['median_ms']}")
        L.append("")
    (run / "baseline.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))



# ------------------------------------------------------------------------------------------------ C5: final model + one OOD scoring
def cmd_final(args) -> None:
    """Train on ALL main-set traces except a 15 % validation hold-out (thresholds by the plateau rules), then score the OOD set ONCE.
    No re-tuning after seeing the OOD result (plan section 3.6)."""
    run = Path(args.run_dir) if Path(args.run_dir).is_absolute() else ROOT / args.run_dir
    run.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")
    traces = load_traces(args, Path(args.cache) if args.cache else run / "traces_cache.npz")
    names = np.array([t["scenarioName"] for t in traces])
    trainable = [i for i, t in enumerate(traces) if not t["undetectable"]]
    st = names[trainable].copy()
    for c, n_c in zip(*np.unique(st, return_counts=True)):
        if n_c < 4:
            st[st == c] = "_small"
    tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=args.seed)
    T.set_seed(args.seed)
    args.batch_size, args.lr, args.patience = 256, 1e-3, 5
    model, cfg, hist = T.train(traces, {"train": sorted(tr.tolist()), "val": sorted(va.tolist())}, args, device)
    model.to(device).eval()
    probs = {i: T.stream_probs(model, traces[i]["features"], device) for i in va.tolist()}
    va_ids = sorted(va.tolist())
    settings = {v: dict(zip(("ai_threshold", "solo_threshold"), tune_variant(traces, va_ids, probs, v))) for v in VARIANTS}
    hs = settings["Hybrid + AI-alone path"]
    torch.save({"model_state_dict": model.cpu().state_dict(), "config": cfg, "best_threshold": hs["ai_threshold"]}, run / "transformer_protection_lstm_best.pth")
    (run / "decision_threshold.txt").write_text(f"{hs['ai_threshold']:.4f}\n", encoding="utf-8")
    (run / "decision_solo_threshold.txt").write_text(f"{hs['solo_threshold']:.4f}\n" if hs["solo_threshold"] is not None else "off\n", encoding="utf-8")
    (run / "decision_dwell.txt").write_text(f"{args.dwell}\n", encoding="utf-8")
    model.to(device).eval()
    print(f"final model: {len(tr)} train / {len(va)} val traces, {len(hist)} epochs, thresholds {hs}", flush=True)
    out = {"settings": settings, "n_train": int(len(tr)), "n_val": int(len(va)), "epochs": len(hist)}
    # ---- OOD, scored once
    args.files = args.ood
    ood = load_traces(args, run / "traces_cache_ood.npz")
    oprobs = {i: T.stream_probs(model, ood[i]["features"], device) for i in range(len(ood))}
    L = [f"FINAL model ({run.name}): trained on {len(tr)} traces, thresholds tuned on {len(va)} validation traces; OOD set scored ONCE, no re-tuning", ""]
    blocks = {1: "extreme load (1-10 %, 110-130 %)", 2: "weak source 3x + 49.5/50.5 Hz", 3: "CT burden 12-16x", 4: "over-excitation 1.5-1.6 pu + residual flux 0.9 pu", 5: "noise 5 % + CT mismatch +/-8 %"}
    out["ood"] = {}
    for v in VARIANTS:
        rows = rows_for(ood, list(range(len(ood))), oprobs, v, settings[v]["ai_threshold"], settings[v]["solo_threshold"])
        annotate(rows, ood)
        sm = summarise(rows)
        out["ood"][v] = {"overall": sm, "blocks": {}}
        L.append(f"[{v}] OOD overall: dependability {sm['dependability_pct']:.1f} % ({sm['n_fault']} faults), security {sm['security_pct']:.1f} % ({sm['n_healthy']} healthy), missed {sm['missed']}, false {sm['false_trips']}, pre-fault {sm['pre_fault_trips']}, operate median {sm['operate']['median_ms']} ms")
        for b, label in blocks.items():
            ids = [i for i, t in enumerate(ood) if int(t.get("oodBlock", 0)) == b]
            rb = [r for r in rows if r["trace"] in set(ids)]
            sb = summarise(rb)
            out["ood"][v]["blocks"][b] = sb
            if v == "Hybrid + AI-alone path":
                L.append(f"    block {b} {label:52s} dependability {sb['dependability_pct'] if sb['dependability_pct'] is not None else float('nan'):5.1f} % ({sb['n_fault']})  security {sb['security_pct'] if sb['security_pct'] is not None else float('nan'):5.1f} % ({sb['n_healthy']})  missed {sb['missed']} false {sb['false_trips']}")
    L.append("")
    L.append("Per category (OOD, hybrid + AI-alone):")
    for c, b in out["ood"]["Hybrid + AI-alone path"]["overall"]["by_category"].items():
        L.append(f"    {c:20s} n={b['n']:4d}  {b['correct_pct']:6.1f} % [{b['ci95'][0]:5.1f}, {b['ci95'][1]:5.1f}]")
    (run / "report_ood.json").write_text(json.dumps(out, default=float, indent=1), encoding="utf-8")
    (run / "report_ood.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["cv", "baseline", "final"])
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--ood", nargs="*", default=None)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--seed", type=int, default=20261021)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--train-stride", type=int, default=8)
    ap.add_argument("--dwell", type=int, default=20)
    ap.add_argument("--dep-tolerance", type=float, default=2.0)
    ap.add_argument("--sec-tolerance", type=float, default=1.0)
    ap.add_argument("--checkpoint", default="runs/20261020_v3_87tfix/transformer_protection_lstm_best.pth")
    ap.add_argument("--ai-threshold", type=float, default=0.90)
    ap.add_argument("--solo-threshold", type=float, default=0.995)
    ap.add_argument("--limit", type=int, default=0, help="DEBUG: use a random subset of this many traces (smoke test only).")
    args = ap.parse_args()
    {"cv": cmd_cv, "baseline": cmd_baseline, "final": cmd_final}[args.mode](args)


if __name__ == "__main__":
    main()
