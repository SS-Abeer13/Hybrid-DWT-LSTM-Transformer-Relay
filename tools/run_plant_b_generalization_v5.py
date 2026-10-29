"""Plant B Generalization Experiments (Phase 3.4 of IMPLEMENTATION_PLAN_V4_PUBLICATION.md).

Implements the three publication experiments:
1. Zero-shot transfer:
   - Evaluates the Plant A final model directly on Plant B with NO retraining.
   - Thresholds frozen from Plant A: ai_thr=0.9950, solo_thr=0.9990, dwell=20.
   - Evaluates conventional Harmonic 87T baseline on Plant B for comparison.
   - Saves to runs/<date>_v5_plant_b_zeroshot/

2. Cross-plant training:
   - Trains on pooled Plant A + Plant B dataset with 5-fold CV.
   - Reports overall pooled metrics and per-plant breakdown (Plant A vs Plant B).
   - Saves to runs/<date>_v5_cross_plant/

3. Leave-one-plant-out:
   - Train on Plant A -> Test on Plant B.
   - Train on Plant B -> Test on Plant A.
   - Saves to runs/<date>_v5_leave_one_out/
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedKFold

# Add lstm_models directory to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))

import features12 as F
import relay87t
import stress_dataset
import train_trace_split as T
from stress_dataset import FS

# Plant A thresholds: read from the v5 final run (decision_*.txt written by train_cv_v5.py final); set in the main block below, never hard-coded
PLANT_A_AI_THR = None
PLANT_A_SOLO_THR = None
PLANT_A_DWELL = None
MIN_FAULT_PU = 0.05


def wilson_ci(k: int, n: int, z: float = 1.95996) -> tuple[float, float]:
    """Wilson score 95% confidence interval."""
    if n == 0:
        return 0.0, 100.0
    p = k / n
    denom = 1 + (z ** 2) / n
    centre = (p + (z ** 2) / (2 * n)) / denom
    margin = (z * np.sqrt((p * (1 - p) + (z ** 2) / (4 * n)) / n)) / denom
    return float(np.clip(100 * (centre - margin), 0.0, 100.0)), float(np.clip(100 * (centre + margin), 0.0, 100.0))


def relaxed_ok_trace(t: dict) -> bool:
    """Accept traces where generator checks passed or harmless noise flag."""
    if t.get("timingOK", 1) == 0:
        return False
    if t.get("duplicate", 0) == 1:
        return False
    return True


def load_dataset_traces(file_paths: list[Path]) -> list[dict]:
    """Loads traces from .mat files, computes plant-compensated features and metadata."""
    traces = []
    unique = {}
    for fp in file_paths:
        raw = stress_dataset.load_traces(fp)
        for t in raw:
            if not relaxed_ok_trace(t):
                continue
            fp_hash = t["fingerprint"]
            if fp_hash in unique:
                continue
            plant = t.get("plant", "B" if ("plantb" in fp.name.lower() or "plant_b" in fp.name.lower()) else "A")
            t["plant"] = plant
            t["features"] = F.trace_features(F.plant_compensated_diff(t["primary"], t["secondary"], plant=plant))
            if t.get("inceptionTime") is not None and not np.isnan(t["inceptionTime"]):
                t["onset"] = int(round(t["inceptionTime"] * FS))
            else:
                t["onset"] = stress_dataset.detect_fault_onset(t["primary"], t["secondary"])
            
            # 87T conventional analysis
            a87 = relay87t.analyse(t["primary"], t["secondary"], plant=plant)
            t["vote87"], t["highset"] = a87["vote"], a87["highset"]
            t["fault_pu"] = relay87t.fault_rise_pu(t["primary"], t["secondary"], t["onset"], plant=plant) if t["onset"] >= 0 else float("nan")
            
            # Harmonic 87T analysis
            h87 = relay87t.analyse_harmonic(t["primary"], t["secondary"], plant=plant)
            t["vote87_harm"], t["highset_harm"] = h87["vote"], h87["highset"]

            t["category"] = T.category(t["scenarioName"])
            t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < MIN_FAULT_PU)

            del t["primary"], t["secondary"]
            unique[fp_hash] = t
            traces.append(t)
    return traces


def evaluate_relay_on_traces(traces: list[dict], probs: list[np.ndarray], ai_thr: float, solo_thr: float | None,
                             variant: str = "Proposed") -> dict:
    """Evaluates trip logic on a list of traces given precomputed window probabilities."""
    dwell = PLANT_A_DWELL
    rows = []
    for i, t in enumerate(traces):
        p_seq = probs[i]
        vote87 = t["vote87"]
        highset = t["highset"]
        
        trip_at = -1
        if variant == "87T alone":
            if highset.any():
                trip_at = int(np.argmax(highset))
            if trip_at < 0 and vote87.any():
                trip_at = int(np.argmax(vote87))
        elif variant == "Harmonic 87T":
            vote87_h = t["vote87_harm"]
            highset_h = t["highset_harm"]
            if highset_h.any():
                trip_at = int(np.argmax(highset_h))
            if trip_at < 0 and vote87_h.any():
                trip_at = int(np.argmax(vote87_h))
        else: # Proposed Hybrid / LSTM
            run_gate = 0
            run_solo = 0
            for s, prob in enumerate(p_seq):
                run_gate = run_gate + 1 if prob >= ai_thr else 0
                run_solo = run_solo + 1 if (solo_thr is not None and prob >= solo_thr) else 0
                ds = int(T.decision_sample(np.array(s)))
                if variant in ("Proposed", "Hybrid (87T gate)"):
                    if run_gate >= dwell and (ds < len(vote87) and vote87[ds]):
                        trip_at = ds
                        break
                if variant == "Proposed" and solo_thr is not None and run_solo >= dwell:
                    trip_at = ds
                    break
                if variant == "LSTM alone" and run_gate >= dwell:
                    trip_at = ds
                    break
            if highset.any():
                hs = int(np.argmax(highset))
                trip_at = hs if trip_at < 0 else min(trip_at, hs)

        tripped = trip_at >= 0
        early = bool(t["should_trip"] and tripped and trip_at < t["onset"])
        operate_ms = (trip_at - t["onset"]) / FS * 1e3 if (t["should_trip"] and tripped and not early) else None
        correct = bool((t["should_trip"] and tripped and not early) or (not t["should_trip"] and not tripped))
        
        rows.append({
            "trace_idx": i,
            "plant": t["plant"],
            "scenario": t["scenarioName"],
            "category": t["category"],
            "should_trip": int(t["should_trip"]),
            "tripped": tripped,
            "trip_sample": trip_at,
            "onset_sample": int(t["onset"]),
            "operate_ms": operate_ms,
            "tripped_before_fault": early,
            "correct": correct,
            "undetectable": t["undetectable"],
        })

    # Summary metrics excluding undetectable faults (< 0.05 pu)
    detectable_rows = [r for r in rows if not r["undetectable"]]
    faults = [r for r in detectable_rows if r["should_trip"]]
    healthy = [r for r in detectable_rows if not r["should_trip"]]
    ms = np.array([r["operate_ms"] for r in faults if r["operate_ms"] is not None])
    undetectable_faults = [r for r in rows if r["undetectable"]]

    dep_pct = 100 * float(np.mean([r["correct"] for r in faults])) if faults else None
    sec_pct = 100 * float(np.mean([r["correct"] for r in healthy])) if healthy else None
    dep_ci = wilson_ci(sum(1 for r in faults if r["correct"]), len(faults)) if faults else [None, None]
    sec_ci = wilson_ci(sum(1 for r in healthy if r["correct"]), len(healthy)) if healthy else [None, None]

    # Breakdown by category
    by_cat = defaultdict(list)
    for r in detectable_rows:
        by_cat[r["category"]].append(r)
    
    cat_summary = {}
    for c, v in sorted(by_cat.items()):
        k_c = sum(1 for r in v if r["correct"])
        lo_c, hi_c = wilson_ci(k_c, len(v))
        ms_c = np.array([r["operate_ms"] for r in v if r["operate_ms"] is not None])
        cat_summary[c] = {
            "n": len(v),
            "correct": k_c,
            "correct_pct": 100.0 * k_c / len(v) if len(v) else 0.0,
            "ci95": [lo_c, hi_c],
            "should_trip": bool(v[0]["should_trip"]),
            "median_operate_ms": float(np.median(ms_c)) if len(ms_c) else None,
        }

    return {
        "variant": variant,
        "n_fault": len(faults),
        "n_healthy": len(healthy),
        "dependability_pct": dep_pct,
        "dependability_ci95": dep_ci,
        "security_pct": sec_pct,
        "security_ci95": sec_ci,
        "missed_trips": sum(1 for r in faults if not r["tripped"]),
        "false_trips": sum(1 for r in healthy if r["tripped"]),
        "pre_fault_trips": sum(1 for r in faults if r["tripped_before_fault"]),
        "operate": {
            "n": int(len(ms)),
            "median_ms": float(np.median(ms)) if len(ms) else None,
            "p90_ms": float(np.percentile(ms, 90)) if len(ms) else None,
            "max_ms": float(ms.max()) if len(ms) else None,
            "within_1_cycle_pct": float(100 * np.mean(ms <= 20)) if len(ms) else None,
            "within_2_cycles_pct": float(100 * np.mean(ms <= 40)) if len(ms) else None,
        },
        "undetectable": {
            "n": len(undetectable_faults),
            "tripped": sum(1 for r in undetectable_faults if r["tripped"]),
            "tripped_pct": 100 * float(np.mean([r["tripped"] for r in undetectable_faults])) if undetectable_faults else None,
        },
        "by_category": cat_summary,
        "rows": rows,
    }


def compute_model_probs(model: nn.Module, traces: list[dict], device: torch.device) -> list[np.ndarray]:
    """Computes streaming window probabilities for all traces."""
    model.eval()
    all_probs = []
    with torch.no_grad():
        for t in traces:
            feat = t["features"]
            if len(feat) < T.SEQ:
                all_probs.append(np.zeros(0, dtype=np.float32))
                continue
            pr = T.stream_probs(model, feat, device)
            all_probs.append(pr)
    return all_probs


def load_saved_model(model_path: Path, device: torch.device) -> T.TransformerProtectionLSTM:
    """Loads a trained TransformerProtectionLSTM checkpoint."""
    ckpt = torch.load(model_path, map_location=device)
    cfg = ckpt.get("config", ckpt.get("model_config", {}))
    input_size = int(cfg.get("input_size", 12))
    hidden_size = int(cfg.get("hidden_size", 64))
    num_layers = int(cfg.get("num_layers", 2))
    dropout = float(cfg.get("dropout", 0.2))
    bidirectional = bool(cfg.get("bidirectional", False))
    model = T.TransformerProtectionLSTM(input_size, hidden_size, num_layers, dropout, bidirectional).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def run_experiment_1_zero_shot(plant_a_model_path: Path, plant_b_files: list[Path], out_dir: Path):
    """Experiment 1: Zero-shot transfer of Plant A model on Plant B."""
    print("=" * 80)
    print("EXPERIMENT 1: ZERO-SHOT TRANSFER (Plant A Model -> Plant B Traces)")
    print("=" * 80)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    device = torch.device("cpu")
    model = load_saved_model(plant_a_model_path, device)
    print(f"Loaded Plant A Model: {plant_a_model_path}")
    print(f"Fixed Operating Thresholds: ai_thr={PLANT_A_AI_THR}, solo_thr={PLANT_A_SOLO_THR}, dwell={PLANT_A_DWELL}")

    print("\nLoading Plant B dataset traces...", flush=True)
    traces = load_dataset_traces(plant_b_files)
    print(f"Loaded {len(traces)} valid Plant B traces (undetectable: {sum(t['undetectable'] for t in traces)})")

    print("\nComputing streaming inference probabilities with Plant A model...", flush=True)
    probs = compute_model_probs(model, traces, device)

    variants = ["Proposed", "Harmonic 87T", "87T alone", "LSTM alone"]
    results = {}
    for v in variants:
        res = evaluate_relay_on_traces(traces, probs, PLANT_A_AI_THR, PLANT_A_SOLO_THR, variant=v)
        # Omit detailed rows from high-level summary dict
        res_summary = {k: val for k, val in res.items() if k != "rows"}
        results[v] = res_summary
        print(f"\n--- {v} on Plant B ---")
        dep_str = f"{res['dependability_pct']:.2f}% [{res['dependability_ci95'][0]:.2f}, {res['dependability_ci95'][1]:.2f}]%" if res['dependability_pct'] is not None else "N/A"
        sec_str = f"{res['security_pct']:.2f}% [{res['security_ci95'][0]:.2f}, {res['security_ci95'][1]:.2f}]%" if res['security_pct'] is not None else "N/A"
        print(f"  Dependability: {dep_str}")
        print(f"  Security:      {sec_str}")
        if res["operate"]["median_ms"] is not None:
            print(f"  Operate Time:  median={res['operate']['median_ms']:.1f} ms, <=1 cycle={res['operate']['within_1_cycle_pct']:.1f}%, <=2 cycles={res['operate']['within_2_cycles_pct']:.1f}%")
        print(f"  False Trips:   {res['false_trips']} / {res['n_healthy']} | Missed Trips: {res['missed_trips']} / {res['n_fault']} | Pre-fault Trips: {res['pre_fault_trips']}")

    # Save summary
    out_json = out_dir / "zero_shot_summary.json"
    out_txt = out_dir / "zero_shot_summary.txt"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("EXPERIMENT 1: ZERO-SHOT TRANSFER SUMMARY\n")
        f.write(f"Date: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Source Model: {plant_a_model_path}\n")
        f.write(f"Evaluation Traces: {len(traces)} from Plant B\n")
        f.write("=" * 80 + "\n\n")
        for v in variants:
            r = results[v]
            f.write(f"Variant: {v}\n")
            dep_fmt = f"{r['dependability_pct']:.2f}% [{r['dependability_ci95'][0]:.2f}, {r['dependability_ci95'][1]:.2f}]%" if r['dependability_pct'] is not None else "N/A"
            sec_fmt = f"{r['security_pct']:.2f}% [{r['security_ci95'][0]:.2f}, {r['security_ci95'][1]:.2f}]%" if r['security_pct'] is not None else "N/A"
            f.write(f"  Dependability: {dep_fmt}\n")
            f.write(f"  Security:      {sec_fmt}\n")
            f.write(f"  Missed Trips:  {r['missed_trips']} / {r['n_fault']}\n")
            f.write(f"  False Trips:   {r['false_trips']} / {r['n_healthy']}\n")
            f.write(f"  Operate Median: {r['operate']['median_ms']} ms (<=1 cyc: {r['operate']['within_1_cycle_pct']}%, <=2 cyc: {r['operate']['within_2_cycles_pct']}%)\n\n")

    print(f"\nZero-shot results successfully written to {out_json} and {out_txt}")
    return results


def run_experiment_2_cross_plant(plant_a_files: list[Path], plant_b_files: list[Path], out_dir: Path, n_folds: int = 5):
    """Experiment 2: Cross-plant pooled training with 5-fold CV."""
    print("=" * 80)
    print("EXPERIMENT 2: CROSS-PLANT TRAINING (Pooled Plant A + Plant B with 5-Fold CV)")
    print("=" * 80)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")

    print("\nLoading Plant A and Plant B traces...", flush=True)
    traces_a = load_dataset_traces(plant_a_files)
    traces_b = load_dataset_traces(plant_b_files)
    all_traces = traces_a + traces_b
    print(f"Loaded: {len(traces_a)} from Plant A, {len(traces_b)} from Plant B -> Total {len(all_traces)} traces")

    # Stratified 5-Fold Split by scenario + plant tag
    strat = np.array([f"{t['plant']}_{t['scenarioName']}" for t in all_traces])
    for c, n in zip(*np.unique(strat, return_counts=True)):
        if n < n_folds:
            strat[strat == c] = f"{c.split('_')[0]}_small"
    
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=20261021)
    
    fold_results = []
    pooled_rows = []
    args_train = argparse.Namespace(train_stride=8, batch_size=256, lr=1e-3, epochs=15, patience=5, seed=20261021)
    
    for fold, (tr_idx, test_idx) in enumerate(skf.split(np.arange(len(all_traces)), strat), 1):
        print(f"\n>>> Fold {fold} / {n_folds} (train={len(tr_idx)}, test={len(test_idx)}) <<<", flush=True)
        trainable = [i for i in tr_idx if not all_traces[i]["undetectable"]]
        st = strat[trainable].copy()
        for c, n_c in zip(*np.unique(st, return_counts=True)):
            if n_c < 4:
                st[st == c] = "_small"
        if (st == "_small").sum() == 1:
            st[st == "_small"] = st[0]
        
        from sklearn.model_selection import train_test_split
        tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=20261021 + fold)
        T.set_seed(20261021 + fold)

        # Train model
        model, cfg, hist = T.train(all_traces, {"train": sorted(tr.tolist()), "val": sorted(va.tolist())}, args_train, device)
        model.to(device).eval()

        # Tune thresholds on validation traces of the training split
        val_traces = [all_traces[i] for i in va]
        val_probs = compute_model_probs(model, val_traces, device)
        ai_thr = T.tune_threshold(val_traces, list(range(len(val_traces))), {i: val_probs[i] for i in range(len(val_traces))})
        solo_thr = T.tune_solo(val_traces, list(range(len(val_traces))), {i: val_probs[i] for i in range(len(val_traces))}, ai_thr)
        print(f"  Fold {fold} Tuned Thresholds: ai_thr={ai_thr:.4f}, solo_thr={solo_thr}")

        # Evaluate on held-out test fold traces
        test_traces = [all_traces[i] for i in test_idx]
        test_probs = compute_model_probs(model, test_traces, device)
        res = evaluate_relay_on_traces(test_traces, test_probs, ai_thr, solo_thr, variant="Proposed")
        fold_results.append({
            "fold": fold,
            "ai_threshold": float(ai_thr),
            "solo_threshold": float(solo_thr) if solo_thr is not None else None,
            "dependability_pct": res["dependability_pct"],
            "security_pct": res["security_pct"],
            "operate": res["operate"],
        })
        pooled_rows.extend(res["rows"])

    # Compute overall pooled metrics and per-plant breakdown
    def calc_metrics(r_list: list[dict], label: str) -> dict:
        det = [r for r in r_list if not r["undetectable"]]
        f = [r for r in det if r["should_trip"]]
        h = [r for r in det if not r["should_trip"]]
        ms = np.array([r["operate_ms"] for r in f if r["operate_ms"] is not None])
        dep = 100 * float(np.mean([r["correct"] for r in f])) if f else None
        sec = 100 * float(np.mean([r["correct"] for r in h])) if h else None
        return {
            "subset": label,
            "n_fault": len(f),
            "n_healthy": len(h),
            "dependability_pct": dep,
            "dependability_ci95": wilson_ci(sum(1 for r in f if r["correct"]), len(f)) if f else [None, None],
            "security_pct": sec,
            "security_ci95": wilson_ci(sum(1 for r in h if r["correct"]), len(h)) if h else [None, None],
            "operate_median_ms": float(np.median(ms)) if len(ms) else None,
            "within_1_cycle_pct": float(100 * np.mean(ms <= 20)) if len(ms) else None,
            "within_2_cycles_pct": float(100 * np.mean(ms <= 40)) if len(ms) else None,
        }

    overall = calc_metrics(pooled_rows, "Overall (Pooled A + B)")
    plant_a_metrics = calc_metrics([r for r in pooled_rows if r["plant"] == "A"], "Plant A Subset")
    plant_b_metrics = calc_metrics([r for r in pooled_rows if r["plant"] == "B"], "Plant B Subset")

    print("\n" + "=" * 80)
    print("CROSS-PLANT 5-FOLD CV SUMMARY:")
    for m in (overall, plant_a_metrics, plant_b_metrics):
        print(f"\n{m['subset']}:")
        dep_str = f"{m['dependability_pct']:.2f}% (95% CI: [{m['dependability_ci95'][0]:.2f}, {m['dependability_ci95'][1]:.2f}]%)" if m['dependability_pct'] is not None else "N/A"
        sec_str = f"{m['security_pct']:.2f}% (95% CI: [{m['security_ci95'][0]:.2f}, {m['security_ci95'][1]:.2f}]%)" if m['security_pct'] is not None else "N/A"
        print(f"  Dependability: {dep_str}")
        print(f"  Security:      {sec_str}")
        if m['operate_median_ms'] is not None:
            print(f"  Operate Time:  median={m['operate_median_ms']:.1f} ms, <=1 cyc={m['within_1_cycle_pct']:.1f}%, <=2 cyc={m['within_2_cycles_pct']:.1f}%")

    out_summary = {
        "folds": fold_results,
        "overall": overall,
        "plant_a_subset": plant_a_metrics,
        "plant_b_subset": plant_b_metrics,
    }
    with open(out_dir / "cross_plant_summary.json", "w", encoding="utf-8") as f:
        json.dump(out_summary, f, indent=2)

    with open(out_dir / "cross_plant_summary.txt", "w", encoding="utf-8") as f:
        f.write("EXPERIMENT 2: CROSS-PLANT TRAINING SUMMARY (5-FOLD CV)\n")
        f.write(f"Date: {datetime.datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        for m in (overall, plant_a_metrics, plant_b_metrics):
            dep_fmt = f"{m['dependability_pct']:.2f}% [{m['dependability_ci95'][0]:.2f}, {m['dependability_ci95'][1]:.2f}]%" if m['dependability_pct'] is not None else "N/A"
            sec_fmt = f"{m['security_pct']:.2f}% [{m['security_ci95'][0]:.2f}, {m['security_ci95'][1]:.2f}]%" if m['security_pct'] is not None else "N/A"
            f.write(f"Subset: {m['subset']}\n")
            f.write(f"  Dependability: {dep_fmt}\n")
            f.write(f"  Security:      {sec_fmt}\n")
            f.write(f"  Operate Median: {m['operate_median_ms']} ms (<=1 cyc: {m['within_1_cycle_pct']}%, <=2 cyc: {m['within_2_cycles_pct']}%)\n\n")

    print(f"\nCross-plant results written to {out_dir / 'cross_plant_summary.json'}")
    return out_summary


def run_experiment_3_leave_one_out(plant_a_files: list[Path], plant_b_files: list[Path], out_dir: Path):
    """Experiment 3: Leave-one-plant-out (Train on A -> Test on B; Train on B -> Test on A)."""
    print("=" * 80)
    print("EXPERIMENT 3: LEAVE-ONE-PLANT-OUT (A -> B and B -> A)")
    print("=" * 80)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")
    from sklearn.model_selection import train_test_split

    traces_a = load_dataset_traces(plant_a_files)
    traces_b = load_dataset_traces(plant_b_files)
    args_train = argparse.Namespace(train_stride=8, batch_size=256, lr=1e-3, epochs=15, patience=5, seed=20261021)

    # 1. Train on A -> Test on B
    print("\n--- Sub-experiment 3a: Train on Plant A -> Test on Plant B ---", flush=True)
    trainable_a = [i for i in range(len(traces_a)) if not traces_a[i]["undetectable"]]
    names_a = np.array([traces_a[i]["scenarioName"] for i in trainable_a])
    st_a = names_a.copy()
    for c, n in zip(*np.unique(st_a, return_counts=True)):
        if n < 4:
            st_a[st_a == c] = "_small"
    tr_a, va_a = train_test_split(np.array(trainable_a), test_size=0.15, stratify=st_a, random_state=20261021)
    
    model_a, cfg_a, _ = T.train(traces_a, {"train": sorted(tr_a.tolist()), "val": sorted(va_a.tolist())}, args_train, device)
    model_a.to(device).eval()

    val_traces_a = [traces_a[i] for i in va_a]
    probs_a_val = compute_model_probs(model_a, val_traces_a, device)
    ai_thr_a = T.tune_threshold(val_traces_a, list(range(len(val_traces_a))), {i: probs_a_val[i] for i in range(len(val_traces_a))})
    solo_thr_a = T.tune_solo(val_traces_a, list(range(len(val_traces_a))), {i: probs_a_val[i] for i in range(len(val_traces_a))}, ai_thr_a)
    print(f"Tuned on Plant A val: ai_thr={ai_thr_a:.4f}, solo_thr={solo_thr_a}")

    probs_b = compute_model_probs(model_a, traces_b, device)
    res_a_to_b = evaluate_relay_on_traces(traces_b, probs_b, ai_thr_a, solo_thr_a, variant="Proposed")
    print(f"Results on Plant B: Dependability={res_a_to_b['dependability_pct']}%, Security={res_a_to_b['security_pct']}%")

    # 2. Train on B -> Test on A
    print("\n--- Sub-experiment 3b: Train on Plant B -> Test on Plant A ---", flush=True)
    trainable_b = [i for i in range(len(traces_b)) if not traces_b[i]["undetectable"]]
    names_b = np.array([traces_b[i]["scenarioName"] for i in trainable_b])
    st_b = names_b.copy()
    for c, n in zip(*np.unique(st_b, return_counts=True)):
        if n < 4:
            st_b[st_b == c] = "_small"
    tr_b, va_b = train_test_split(np.array(trainable_b), test_size=0.15, stratify=st_b, random_state=20261021)

    model_b, cfg_b, _ = T.train(traces_b, {"train": sorted(tr_b.tolist()), "val": sorted(va_b.tolist())}, args_train, device)
    model_b.to(device).eval()

    val_traces_b = [traces_b[i] for i in va_b]
    probs_b_val = compute_model_probs(model_b, val_traces_b, device)
    ai_thr_b = T.tune_threshold(val_traces_b, list(range(len(val_traces_b))), {i: probs_b_val[i] for i in range(len(val_traces_b))})
    solo_thr_b = T.tune_solo(val_traces_b, list(range(len(val_traces_b))), {i: probs_b_val[i] for i in range(len(val_traces_b))}, ai_thr_b)
    print(f"Tuned on Plant B val: ai_thr={ai_thr_b:.4f}, solo_thr={solo_thr_b}")

    probs_a = compute_model_probs(model_b, traces_a, device)
    res_b_to_a = evaluate_relay_on_traces(traces_a, probs_a, ai_thr_b, solo_thr_b, variant="Proposed")
    print(f"Results on Plant A: Dependability={res_b_to_a['dependability_pct']}%, Security={res_b_to_a['security_pct']}%")

    out_summary = {
        "train_a_test_b": {k: v for k, v in res_a_to_b.items() if k != "rows"},
        "train_b_test_a": {k: v for k, v in res_b_to_a.items() if k != "rows"},
    }
    with open(out_dir / "leave_one_out_summary.json", "w", encoding="utf-8") as f:
        json.dump(out_summary, f, indent=2)

    with open(out_dir / "leave_one_out_summary.txt", "w", encoding="utf-8") as f:
        f.write("EXPERIMENT 3: LEAVE-ONE-PLANT-OUT GENERALIZATION SUMMARY\n")
        f.write(f"Date: {datetime.datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        f.write("1. Train on Plant A -> Test on Plant B:\n")
        r = out_summary["train_a_test_b"]
        dep_fmt = f"{r['dependability_pct']:.2f}% [{r['dependability_ci95'][0]:.2f}, {r['dependability_ci95'][1]:.2f}]%" if r['dependability_pct'] is not None else "N/A"
        sec_fmt = f"{r['security_pct']:.2f}% [{r['security_ci95'][0]:.2f}, {r['security_ci95'][1]:.2f}]%" if r['security_pct'] is not None else "N/A"
        f.write(f"   Dependability: {dep_fmt}\n")
        f.write(f"   Security:      {sec_fmt}\n")
        f.write(f"   Operate Median: {r['operate']['median_ms']} ms\n\n")
        f.write("2. Train on Plant B -> Test on Plant A:\n")
        r2 = out_summary["train_b_test_a"]
        dep_fmt2 = f"{r2['dependability_pct']:.2f}% [{r2['dependability_ci95'][0]:.2f}, {r2['dependability_ci95'][1]:.2f}]%" if r2['dependability_pct'] is not None else "N/A"
        sec_fmt2 = f"{r2['security_pct']:.2f}% [{r2['security_ci95'][0]:.2f}, {r2['security_ci95'][1]:.2f}]%" if r2['security_pct'] is not None else "N/A"
        f.write(f"   Dependability: {dep_fmt2}\n")
        f.write(f"   Security:      {sec_fmt2}\n")
        f.write(f"   Operate Median: {r2['operate']['median_ms']} ms\n")

    print(f"\nLeave-one-plant-out results written to {out_dir / 'leave_one_out_summary.json'}")
    return out_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "zeroshot", "crossplant", "leaveoneout"], default="all")
    parser.add_argument("--plant-a-run", type=str, required=True, help="runs/<date>_v5_final (model + decision_*.txt)")
    parser.add_argument("--plant-a-files", nargs="+", required=True)
    parser.add_argument("--plant-b-files", nargs="+", required=True)
    parser.add_argument("--out-tag", type=str, required=True, help="e.g. 20261029_v5 -> runs/<tag>_plant_b_zeroshot etc.")
    args = parser.parse_args()

    run_a = ROOT / args.plant_a_run
    PLANT_A_AI_THR = float((run_a / "decision_threshold.txt").read_text().split()[0])
    PLANT_A_SOLO_THR = float((run_a / "decision_solo_threshold.txt").read_text().split()[0])
    PLANT_A_DWELL = int((run_a / "decision_dwell.txt").read_text().split()[0])
    plant_a_files = [ROOT / f for f in args.plant_a_files]
    plant_b_files = [ROOT / f for f in args.plant_b_files]

    print(f"Plant A thresholds from {run_a.name}: ai={PLANT_A_AI_THR}, solo={PLANT_A_SOLO_THR}, dwell={PLANT_A_DWELL}")
    print(f"Plant A files: {[f.name for f in plant_a_files]}")
    print(f"Plant B files: {[f.name for f in plant_b_files]}")

    if args.mode in ("all", "zeroshot"):
        run_experiment_1_zero_shot(run_a / "transformer_protection_lstm_best.pth", plant_b_files, ROOT / "runs" / f"{args.out_tag}_plant_b_zeroshot")
    if args.mode in ("all", "crossplant"):
        run_experiment_2_cross_plant(plant_a_files, plant_b_files, ROOT / "runs" / f"{args.out_tag}_cross_plant")
    if args.mode in ("all", "leaveoneout"):
        run_experiment_3_leave_one_out(plant_a_files, plant_b_files, ROOT / "runs" / f"{args.out_tag}_leave_one_out")
