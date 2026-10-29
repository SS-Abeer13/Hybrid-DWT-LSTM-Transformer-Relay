"""Evaluate Harmonic Restrained 87T Relay Variants (R1, R2, R3) and Unrestrained Baseline.

Evaluates across:
1. 5-Fold Grouped Cross-Validation (3,218 traces, N_eval = 3,124; 94 undetectable segregated)
2. Out-of-Distribution (OOD) Stress Suite (300 traces, N_eval = 291; 9 undetectable segregated)

Saves full metrics into:
  runs/20261026_harmonic87t/summary.json
  runs/20261026_harmonic87t/summary.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))

import relay87t as R
import train_trace_split as T
from stress_dataset import FS, load_traces
from v3_checks import relaxed_ok_trace
from ood_labels_v5 import ood_block_labels


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / d
    h = z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / d
    return (100.0 * max(0.0, c - h), 100.0 * min(1.0, c + h))


def load_main_dataset(files: list[str | Path] | None = None) -> list[dict]:
    mat_files = [Path(f) for f in files] if files else [
        ROOT / "datasets" / "StressDataset_v3_20261021_021053.mat",
        ROOT / "datasets" / "StressDataset_v3Only_topup_inrush_loaded.mat",
        ROOT / "datasets" / "StressDataset_v3Only_topup_overexc.mat",
    ]
    raw_traces: dict[str, dict] = {}
    for mf in mat_files:
        for t in load_traces(mf):
            if t["fingerprint"] in raw_traces:
                continue
            if "checkPassed" in t and not relaxed_ok_trace(t):
                continue
            t["onset"] = int(round(t["inceptionTime"] * FS)) if t["should_trip"] else -1
            t["category"] = T.category(t["scenarioName"])
            t["fault_pu"] = R.fault_rise_pu(t["primary"], t["secondary"], t["onset"]) if t["onset"] >= 0 else np.nan
            t["undetectable"] = bool(t["should_trip"] and np.isfinite(t["fault_pu"]) and t["fault_pu"] < 0.05)
            raw_traces[t["fingerprint"]] = t
    return list(raw_traces.values())


def load_ood_dataset(ood_files: list[str | Path] | None = None) -> list[dict]:
    mat_files = [Path(f) for f in ood_files] if ood_files else [
        ROOT / "datasets" / "StressDataset_v3OOD_20261021_132520.mat",
    ]
    raw_traces: dict[str, dict] = {}
    for mf in mat_files:
        for t in load_traces(mf):
            if t["fingerprint"] in raw_traces:
                continue
            if "checkPassed" in t and not relaxed_ok_trace(t):
                continue
            t["onset"] = int(round(t["inceptionTime"] * FS)) if t["should_trip"] else -1
            t["category"] = T.category(t["scenarioName"])
            t["fault_pu"] = R.fault_rise_pu(t["primary"], t["secondary"], t["onset"]) if t["onset"] >= 0 else np.nan
            t["undetectable"] = bool(t["should_trip"] and np.isfinite(t["fault_pu"]) and t["fault_pu"] < 0.05)
            raw_traces[t["fingerprint"]] = t
    return list(raw_traces.values())


def evaluate_traces(traces: list[dict], mode: str | None, dwell: int = 20) -> list[dict]:
    """Evaluate 87T decision per trace using the official streaming logic."""
    T.DWELL = dwell
    T.SOLO_THR = None
    T.GATE87T = True
    
    rows = []
    for idx, t in enumerate(traces):
        if mode is None:
            a87 = R.analyse(t["primary"], t["secondary"])
        else:
            a87 = R.analyse_harmonic(t["primary"], t["secondary"], mode=mode)
        
        v, hs = a87["vote"], a87["highset"]
        n_windows = len(t["primary"]) - 32 - T.SEQ + 1
        probs_dummy = np.ones(n_windows, dtype=np.float32)
        trip_sample = T.relay_decision(probs_dummy, 0.5, v, hs, None)
        
        tripped = trip_sample >= 0
        early = bool(t["should_trip"] and tripped and trip_sample < t["onset"])
        operate_ms = ((trip_sample - t["onset"]) / FS * 1e3) if (t["should_trip"] and tripped and not early) else None
        correct = bool((t["should_trip"] and tripped and not early) or (not t["should_trip"] and not tripped))
        
        rows.append({
            "trace_idx": idx,
            "scenario": t.get("scenarioName", ""),
            "category": t.get("category", ""),
            "ood_block": int(t.get("oodBlock", 0)),
            "should_trip": int(t["should_trip"]),
            "undetectable": bool(t.get("undetectable", False)),
            "tripped": tripped,
            "trip_sample": int(trip_sample),
            "onset_sample": int(t["onset"]),
            "early": early,
            "operate_ms": operate_ms,
            "correct": correct,
        })
    return rows


def summarize_rows(rows: list[dict]) -> dict:
    head = [r for r in rows if not r["undetectable"]]
    faults = [r for r in head if r["should_trip"]]
    healthy = [r for r in head if not r["should_trip"]]
    undet = [r for r in rows if r["undetectable"]]
    
    dep = 100.0 * float(np.mean([r["correct"] for r in faults])) if faults else None
    sec = 100.0 * float(np.mean([r["correct"] for r in healthy])) if healthy else None
    acc = 100.0 * float(np.mean([r["correct"] for r in head])) if head else None
    
    ms_values = np.array([r["operate_ms"] for r in faults if r["operate_ms"] is not None])
    
    operate_stats = {
        "n": int(len(ms_values)),
        "median_ms": float(np.median(ms_values)) if len(ms_values) else None,
        "p90_ms": float(np.percentile(ms_values, 90)) if len(ms_values) else None,
        "min_ms": float(np.min(ms_values)) if len(ms_values) else None,
        "max_ms": float(np.max(ms_values)) if len(ms_values) else None,
        "within_1_cycle_pct": float(100.0 * np.mean(ms_values <= 20.0)) if len(ms_values) else None,
        "within_2_cycles_pct": float(100.0 * np.mean(ms_values <= 40.0)) if len(ms_values) else None,
    }
    
    # By category
    cats = defaultdict(list)
    for r in head:
        cats[r["category"]].append(r)
    by_category = {}
    for cat_name, c_rows in sorted(cats.items()):
        k_corr = sum(1 for r in c_rows if r["correct"])
        lo, hi = wilson_interval(k_corr, len(c_rows))
        ms_c = np.array([r["operate_ms"] for r in c_rows if r["operate_ms"] is not None])
        by_category[cat_name] = {
            "n": len(c_rows),
            "correct": k_corr,
            "correct_pct": 100.0 * k_corr / len(c_rows),
            "ci95": [lo, hi],
            "should_trip": bool(c_rows[0]["should_trip"]),
            "median_ms": float(np.median(ms_c)) if len(ms_c) else None,
        }
    
    return {
        "n_fault": len(faults),
        "n_healthy": len(healthy),
        "n_total": len(head),
        "dependability_pct": dep,
        "security_pct": sec,
        "accuracy_pct": acc,
        "missed": sum(1 for r in faults if not (r["tripped"] and not r["early"])),
        "false_trips": sum(1 for r in healthy if r["tripped"]),
        "pre_fault_trips": sum(1 for r in faults if r["early"]),
        "operate": operate_stats,
        "undetectable": {
            "n": len(undet),
            "tripped_pct": 100.0 * float(np.mean([r["tripped"] for r in undet])) if undet else None,
        },
        "by_category": by_category,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Harmonic Restrained 87T Relay Variants")
    parser.add_argument("--files", nargs="*", default=None, help="Main dataset MAT files")
    parser.add_argument("--ood", nargs="*", default=None, help="OOD dataset MAT files")
    parser.add_argument("--cv-dir", default=None, help="CV fold results directory")
    parser.add_argument("--output-dir", default="runs/20261026_harmonic87t", help="Output directory")
    args = parser.parse_args()

    t_start = time.time()
    out_dir = Path(args.output_dir) if Path(args.output_dir).is_absolute() else ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading main dataset...", flush=True)
    main_traces = load_main_dataset(args.files)
    print(f"Loaded {len(main_traces)} main traces ({sum(t['undetectable'] for t in main_traces)} undetectable).", flush=True)
    
    print("Loading OOD dataset...", flush=True)
    ood_traces = load_ood_dataset(args.ood)
    print(f"Loaded {len(ood_traces)} OOD traces ({sum(t['undetectable'] for t in ood_traces)} undetectable).", flush=True)
    
    # Load 5-fold CV test trace partition
    cv_dir = Path(args.cv_dir) if args.cv_dir else ROOT / "runs" / "20261021_v3_cv5"
    folds_indices = []
    if (cv_dir / "fold1" / "result.json").is_file():
        for k in range(1, 6):
            fold_res = json.loads((cv_dir / f"fold{k}" / "result.json").read_text(encoding="utf-8"))
            idx = [r["trace"] for r in fold_res["rows"]["87T alone"]]
            folds_indices.append(idx)
    elif (cv_dir / "seed_20261021" / "fold1" / "result.json").is_file():
        for k in range(1, 6):
            fold_res = json.loads((cv_dir / "seed_20261021" / f"fold{k}" / "result.json").read_text(encoding="utf-8"))
            idx = [r["trace"] for r in fold_res["rows"]["87T alone"]]
            folds_indices.append(idx)
    
    modes = [
        ("unrestrained", None, "Classical dual-slope percentage restraint, no harmonic blocking"),
        ("as_coded", "as_coded", "R1: Unselective cross-blocking (any phase k2>15% or k5>35% blocks all)"),
        ("cross_active", "cross_active", "R2: Active cross-blocking (only phases with Id > 0.30 pu cross-block)"),
        ("per_phase", "per_phase", "R3: Phase-independent restraint (standard industrial commercial practice)"),
    ]
    
    results = {
        "metadata": {
            "created_at": "2026-10-26",
            "eval_dwell": 20,
            "k2_threshold_pct": 15.0,
            "k5_threshold_pct": 35.0,
            "pickup_pu": 0.30,
            "slope1": 0.25,
            "slope2": 0.60,
            "breakpoint_pu": 3.0,
            "highset_pu": 10.0,
        },
        "variants": {},
    }
    
    summary_lines = [
        "=" * 80,
        "Harmonic-Restrained 87T Relay Variants vs Unrestrained Baseline Evaluation",
        "=" * 80,
        f"Evaluation Date: 2026-10-26 | Dwell: 20 samples (12.5 ms) | k2: 15% | k5: 35%",
        "",
    ]
    
    for key, mode_param, desc in modes:
        print(f"\n--- Evaluating variant: {key} ({desc}) ---", flush=True)
        # 1. Main dataset evaluation
        main_rows = evaluate_traces(main_traces, mode=mode_param, dwell=20)
        main_summary = summarize_rows(main_rows)
        
        # 2. 5-Fold Cross-Validation evaluation
        fold_summaries = []
        for k, fold_idx in enumerate(folds_indices, 1):
            fold_rows = [main_rows[i] for i in fold_idx]
            fold_summ = summarize_rows(fold_rows)
            fold_summaries.append(fold_summ)
            
        cv_deps = [f["dependability_pct"] for f in fold_summaries]
        cv_secs = [f["security_pct"] for f in fold_summaries]
        cv_accs = [f["accuracy_pct"] for f in fold_summaries]
        cv_fts = [f["false_trips"] for f in fold_summaries]
        
        cv_stats = {
            "dependability_mean": float(np.mean(cv_deps)),
            "dependability_std": float(np.std(cv_deps, ddof=1)),
            "security_mean": float(np.mean(cv_secs)),
            "security_std": float(np.std(cv_secs, ddof=1)),
            "accuracy_mean": float(np.mean(cv_accs)),
            "accuracy_std": float(np.std(cv_accs, ddof=1)),
            "total_false_trips": int(sum(cv_fts)),
            "folds": fold_summaries,
        }
        
        # 3. OOD dataset evaluation
        ood_rows = evaluate_traces(ood_traces, mode=mode_param, dwell=20)
        ood_summary = summarize_rows(ood_rows)
        
        # OOD Blocks 1-5
        ood_blocks = ood_block_labels("A")   # from simulations/generator_ranges_v5.json
        ood_block_summaries = {}
        for b_id, b_label in ood_blocks.items():
            b_rows = [r for r in ood_rows if r["ood_block"] == b_id]
            ood_block_summaries[b_id] = {
                "label": b_label,
                "summary": summarize_rows(b_rows),
            }
        
        results["variants"][key] = {
            "description": desc,
            "main_pooled": main_summary,
            "cv_5fold": cv_stats,
            "ood_overall": ood_summary,
            "ood_blocks": ood_block_summaries,
            "rows": main_rows,
        }
        
        # Text summary formatting
        summary_lines.append(f"Variant: {key.upper()} - {desc}")
        summary_lines.append(
            f"  [Main CV Pooled] Dep: {main_summary['dependability_pct']:.2f}% (n={main_summary['n_fault']}), "
            f"Sec: {main_summary['security_pct']:.2f}% (n={main_summary['n_healthy']}), "
            f"Acc: {main_summary['accuracy_pct']:.2f}%, False Trips: {main_summary['false_trips']}, "
            f"Med T_op: {main_summary['operate']['median_ms']:.2f} ms"
        )
        summary_lines.append(
            f"  [Main 5-Fold CV] Dep: {cv_stats['dependability_mean']:.2f} +/- {cv_stats['dependability_std']:.2f}%, "
            f"Sec: {cv_stats['security_mean']:.2f} +/- {cv_stats['security_std']:.2f}%, "
            f"Total False Trips: {cv_stats['total_false_trips']}"
        )
        summary_lines.append(
            f"  [OOD Overall]    Dep: {ood_summary['dependability_pct']:.2f}% (n={ood_summary['n_fault']}), "
            f"Sec: {ood_summary['security_pct']:.2f}% (n={ood_summary['n_healthy']}), "
            f"Acc: {ood_summary['accuracy_pct']:.2f}%, False Trips: {ood_summary['false_trips']}, "
            f"Pre-fault: {ood_summary['pre_fault_trips']}, Med T_op: {ood_summary['operate']['median_ms']:.2f} ms"
        )
        summary_lines.append("  OOD Blocks:")
        for b_id, b_info in ood_block_summaries.items():
            bs = b_info["summary"]
            summary_lines.append(
                f"    Block {b_id} ({b_info['label']}): "
                f"Dep: {bs['dependability_pct']:.1f}% ({bs['n_fault']}), "
                f"Sec: {bs['security_pct']:.1f}% ({bs['n_healthy']}), "
                f"Missed: {bs['missed']}, False: {bs['false_trips']}"
            )
        summary_lines.append("")
    
    summary_lines.append(f"Completed in {time.time() - t_start:.2f} seconds.")
    
    # Save outputs
    json_path = out_dir / "summary.json"
    txt_path = out_dir / "summary.txt"
    json_path.write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")
    txt_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\nSaved evaluation summary to:\n  {json_path}\n  {txt_path}", flush=True)


if __name__ == "__main__":
    main()
