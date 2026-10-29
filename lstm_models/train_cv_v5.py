"""Phase 2 of IMPLEMENTATION_PLAN_V4_PUBLICATION.md:
Grouped 5-fold cross-validation x 3 seeds, baselines, ablations, OOD scoring, and paired statistics.

Usage:
    python lstm_models/train_cv_v5.py cv --files datasets/StressDataset_v5_<run>.mat --run-dir runs/<date>_v5_cv5_seeds --seeds 20261021 20261022 20261023
    python lstm_models/train_cv_v5.py final --files datasets/StressDataset_v5_<run>.mat --ood datasets/StressDataset_v5OOD_<run>.mat --run-dir runs/<date>_v5_final
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
from coverage_report_v5 import group_of  # noqa: E402
from ood_labels_v5 import ood_block_labels  # noqa: E402
from v3_checks import relaxed_ok_trace  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FS = 1600
VARIANTS = ("87T alone", "LSTM alone", "Hybrid (87T gate)", "Hybrid + AI-alone path")
MIN_FAULT_PU = 0.05


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
    T.category = group_of


def load_traces(args, cache: Path) -> list[dict]:
    configure(args)
    traces = T.build_traces(ROOT, args.files, cache)
    kept = []
    for t in traces:
        if "checkPassed" in t and not relaxed_ok_trace(t):
            continue
        t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < MIN_FAULT_PU)
        kept.append(t)
    if getattr(args, "limit", 0):
        rs = np.random.RandomState(0)
        kept = [kept[i] for i in sorted(rs.choice(len(kept), size=min(args.limit, len(kept)), replace=False))]
    print(f"traces: {len(traces)} built, {len(kept)} pass the generator checks, {sum(t['undetectable'] for t in kept)} undetectable (< {MIN_FAULT_PU} pu)", flush=True)
    return kept


def rows_for(traces, ids, probs, variant: str, thr: float, solo) -> list[dict]:
    T.GATE87T = variant != "LSTM alone"
    T.SOLO_THR = solo if variant == "Hybrid + AI-alone path" else None
    pr = probs
    if variant == "87T alone":
        pr = {i: np.ones(len(traces[i]["features"]) - T.SEQ + 1, dtype=np.float32) for i in ids}
        thr = 0.5
    rep = T.relay_report(traces, ids, pr, thr)
    for r in rep["rows"]:
        r["variant"] = variant
    return rep["rows"]


def tune_variant(traces, val_ids, probs, variant: str):
    if variant == "87T alone":
        return 0.5, None
    T.GATE87T = variant != "LSTM alone"
    T.SOLO_THR = None
    thr = T.tune_threshold(traces, val_ids, probs)
    solo = T.tune_solo(traces, val_ids, probs, thr) if variant == "Hybrid + AI-alone path" else None
    T.SOLO_THR = None
    return thr, solo


def summarise(rows: list[dict]) -> dict:
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


def run_single_seed_cv(traces, args, run_dir: Path, seed: int) -> dict:
    device = torch.device("cpu")
    names = np.array([t["scenarioName"] for t in traces])
    idx = np.arange(len(traces))
    strat = names.copy()
    for c, n in zip(*np.unique(names, return_counts=True)):
        if n < args.folds:
            strat[names == c] = "_small"
    skf = StratifiedKFold(n_splits=args.folds, shuffle=True, random_state=seed)
    all_rows = {v: [] for v in VARIANTS}
    fold_summ = []
    t_all = time.time()
    for k, (tr_all, te) in enumerate(skf.split(idx, strat), 1):
        fdir = run_dir / f"fold{k}"
        if (fdir / "result.json").is_file():
            res = json.loads((fdir / "result.json").read_text(encoding="utf-8"))
            for v in VARIANTS:
                all_rows[v] += res["rows"][v]
            fold_summ.append(res["summary"])
            print(f"seed {seed} fold {k}: done, skipping", flush=True)
            continue
        fdir.mkdir(parents=True, exist_ok=True)
        trainable = [i for i in tr_all if not traces[i]["undetectable"]]
        st = strat[trainable].copy()
        for c, n_c in zip(*np.unique(st, return_counts=True)):
            if n_c < 4:
                st[st == c] = "_small"
        if (st == "_small").sum() == 1:
            st[st == "_small"] = st[0]
        tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=seed + k)
        T.set_seed(seed + k)
        args.batch_size, args.lr, args.patience = 256, 1e-3, 5
        t0 = time.time()
        model, cfg, hist = T.train(traces, {"train": sorted(tr.tolist()), "val": sorted(va.tolist())}, args, device)
        model.to(device).eval()
        torch.save({"model_state_dict": model.cpu().state_dict(), "config": cfg}, fdir / "transformer_protection_lstm_best.pth")
        model.to(device).eval()
        ids_eval = sorted(set(va.tolist()) | set(te.tolist()))
        probs = {i: T.stream_probs(model, traces[i]["features"], device) for i in ids_eval}
        va_ids = sorted(va.tolist())
        te_ids = sorted(te.tolist())
        settings, res_rows, summ = {}, {}, {}
        for v in VARIANTS:
            thr, solo = tune_variant(traces, va_ids, probs, v)
            rows = rows_for(traces, te_ids, probs, v, thr, solo)
            for r in rows:
                r["fold"] = k
                r["seed"] = seed
            annotate(rows, traces)
            settings[v] = {"ai_threshold": thr, "solo_threshold": solo}
            res_rows[v] = rows
            summ[v] = summarise(rows)
            all_rows[v] += rows
        fold_summ.append({"seed": seed, "fold": k, "n_train": int(len(tr)), "n_val": int(len(va)), "n_test": int(len(te)),
                          "settings": settings, "variants": summ, "epochs": len(hist), "train_minutes": (time.time() - t0) / 60})
        (fdir / "result.json").write_text(json.dumps({"summary": fold_summ[-1], "rows": res_rows}, default=float), encoding="utf-8")
        h = summ["Hybrid + AI-alone path"]
        print(f"seed {seed} fold {k}: {len(tr)}/{len(va)}/{len(te)} traces, {len(hist)} epochs, {(time.time() - t0) / 60:.1f} min | hybrid+solo: dep {h['dependability_pct']:.1f}% "
              f"sec {h['security_pct']:.1f}% | thresholds {settings['Hybrid + AI-alone path']}", flush=True)

    summary = {
        "seed": seed,
        "folds": fold_summ,
        "pooled": {v: summarise(all_rows[v]) for v in VARIANTS},
        "all_rows": all_rows,
        "minutes": (time.time() - t_all) / 60
    }
    return summary


def cmd_cv(args) -> None:
    run = Path(args.run_dir) if Path(args.run_dir).is_absolute() else ROOT / args.run_dir
    run.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache) if args.cache else run / "traces_cache.npz"
    traces = load_traces(args, cache)

    seeds = args.seeds if hasattr(args, "seeds") and args.seeds else [args.seed]
    print(f"Running Grouped {args.folds}-Fold CV across {len(seeds)} seed(s): {seeds}", flush=True)

    all_seed_results = []
    combined_rows = {v: [] for v in VARIANTS}
    all_fold_summ = []

    for s in seeds:
        sdir = run if len(seeds) == 1 else run / f"seed_{s}"
        res = run_single_seed_cv(traces, args, sdir, s)
        all_seed_results.append(res)
        all_fold_summ.extend(res["folds"])
        for v in VARIANTS:
            combined_rows[v].extend(res["all_rows"][v])

    # Overall Summary across all seeds
    L = [f"Grouped {args.folds}-Fold CV across {len(seeds)} seed(s) ({seeds}); total {len(all_fold_summ)} fold-models", "=" * 100, ""]
    L.append("Pooled headline metrics over all seeds and folds:")
    L.append(f"{'variant':26s} {'dep %':>7s} {'sec %':>7s} {'missed':>6s} {'false':>5s} {'pre':>4s} {'med ms':>7s} {'p90':>6s} {'max':>6s} {'<=1cyc':>6s} {'<=2cyc':>6s} | undetectable tripped")
    pooled_comb = {v: summarise(combined_rows[v]) for v in VARIANTS}
    for v in VARIANTS:
        s = pooled_comb[v]
        o = s["operate"]
        L.append(f"{v:26s} {s['dependability_pct']:7.2f} {s['security_pct']:7.2f} {s['missed']:6d} {s['false_trips']:5d} {s['pre_fault_trips']:4d} {o['median_ms'] or float('nan'):7.1f} "
                 f"{o['p90_ms'] or float('nan'):6.1f} {o['max_ms'] or float('nan'):6.1f} {o['within_1_cycle_pct'] or float('nan'):6.1f} {o['within_2_cycles_pct'] or float('nan'):6.1f} | "
                 f"{s['undetectable']['tripped_pct'] if s['undetectable']['tripped_pct'] is not None else float('nan'):.0f} % of {s['undetectable']['n']}")

    L += ["", f"Mean +/- SD over the {len(all_fold_summ)} fold-models (Hybrid + AI-alone path):"]
    for key in ("dependability_pct", "security_pct"):
        vals = np.array([f["variants"]["Hybrid + AI-alone path"][key] for f in all_fold_summ])
        L.append(f"  {key:18s} {vals.mean():.2f} +/- {vals.std(ddof=1) if len(vals) > 1 else 0:.2f}   [min {vals.min():.2f}, max {vals.max():.2f}]")

    (run / "summary.txt").write_text("\n".join(L), encoding="utf-8")
    (run / "summary.json").write_text(json.dumps({
        "seeds": seeds,
        "n_fold_models": len(all_fold_summ),
        "pooled": pooled_comb,
        "fold_summaries": all_fold_summ
    }, indent=2, default=float), encoding="utf-8")
    print("\n" + "\n".join(L), flush=True)


def cmd_final(args) -> None:
    run = Path(args.run_dir) if Path(args.run_dir).is_absolute() else ROOT / args.run_dir
    run.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache) if args.cache else run / "traces_cache_main.npz"
    traces = load_traces(args, cache)
    device = torch.device("cpu")
    trainable = [i for i in range(len(traces)) if not traces[i]["undetectable"]]
    names = np.array([traces[i]["scenarioName"] for i in trainable])
    strat = names.copy()
    for c, n in zip(*np.unique(strat, return_counts=True)):
        if n < 4:
            strat[strat == c] = "_small"
    tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=strat, random_state=args.seed)
    T.set_seed(args.seed)
    args.batch_size, args.lr, args.patience = 256, 1e-3, 5
    model, cfg, hist = T.train(traces, {"train": sorted(tr.tolist()), "val": sorted(va.tolist())}, args, device)
    torch.save({"model_state_dict": model.cpu().state_dict(), "config": cfg}, run / "transformer_protection_lstm_best.pth")
    probs = {i: T.stream_probs(model, traces[i]["features"], device) for i in sorted(va.tolist())}
    settings = {}
    for v in VARIANTS:
        thr, solo = tune_variant(traces, sorted(va.tolist()), probs, v)
        settings[v] = {"ai_threshold": thr, "solo_threshold": solo}
    hs = settings["Hybrid + AI-alone path"]
    (run / "decision_threshold.txt").write_text(f"{hs['ai_threshold']:.4f}\n", encoding="utf-8")
    (run / "decision_solo_threshold.txt").write_text(f"{hs['solo_threshold']:.4f}\n" if hs["solo_threshold"] is not None else "off\n", encoding="utf-8")
    (run / "decision_dwell.txt").write_text(f"{args.dwell}\n", encoding="utf-8")
    model.to(device).eval()
    print(f"final model: {len(tr)} train / {len(va)} val traces, {len(hist)} epochs, thresholds {hs}", flush=True)

    out = {"settings": settings, "n_train": int(len(tr)), "n_val": int(len(va)), "epochs": len(hist)}
    if args.ood:
        args.files = args.ood
        ood = load_traces(args, run / "traces_cache_ood.npz")
        oprobs = {i: T.stream_probs(model, ood[i]["features"], device) for i in range(len(ood))}
        L = [f"FINAL model ({run.name}): trained on {len(tr)} traces, thresholds tuned on {len(va)} validation traces; OOD set scored ONCE, no re-tuning", ""]
        blocks = ood_block_labels("A")   # from simulations/generator_ranges_v5.json (the range the generator used)
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
    ap.add_argument("mode", choices=["cv", "final"])
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--ood", nargs="*", default=None)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--seed", type=int, default=20261021)
    ap.add_argument("--seeds", type=int, nargs="+", default=[20261021, 20261022, 20261023])
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--train-stride", type=int, default=8)
    ap.add_argument("--dwell", type=int, default=20)
    ap.add_argument("--dep-tolerance", type=float, default=2.0)
    ap.add_argument("--sec-tolerance", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    {"cv": cmd_cv, "final": cmd_final}[args.mode](args)


if __name__ == "__main__":
    main()
