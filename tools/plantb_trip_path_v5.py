"""Plant B zero-shot trip-path check: through which path does the Proposed relay trip (high-set / 87T-gated AI / AI-alone), and where do the
89 false trips come from? Same model, thresholds, dwell and trace set as runs/20261029_v5_plant_b_zeroshot; counterfactuals switch one path off.

    python tools/plantb_trip_path_v5.py
Outputs: runs/20261029_v5_plant_b_zeroshot/trip_path_check.{json,txt}
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
sys.path.insert(0, str(ROOT / "tools"))
import train_trace_split as T  # noqa: E402
import run_plant_b_generalization_v5 as G  # noqa: E402

RUN = ROOT / "runs" / "20261029_v5_final"
OUT = ROOT / "runs" / "20261029_v5_plant_b_zeroshot"
FILES_B = ["datasets/StressDataset_PlantBv5_20261028_212041.mat", "datasets/StressDataset_PlantBv5Only_20261029_111005.mat",
           "datasets/StressDataset_PlantBv5Only_20261029_111251.mat"]


def first_trips(p_seq: np.ndarray, vote: np.ndarray, highset: np.ndarray, ai: float, solo: float, dwell: int) -> dict[str, int]:
    """First trip sample per path (-1 = never), same logic as evaluate_relay_on_traces(variant='Proposed')."""
    gate = solo_p = -1
    run_g = run_s = 0
    for s, prob in enumerate(p_seq):
        run_g = run_g + 1 if prob >= ai else 0
        run_s = run_s + 1 if prob >= solo else 0
        ds = int(T.decision_sample(np.array(s)))
        if gate < 0 and run_g >= dwell and ds < len(vote) and vote[ds]:
            gate = ds
        if solo_p < 0 and run_s >= dwell:
            solo_p = ds
        if gate >= 0 and solo_p >= 0:
            break
    hs = int(np.argmax(highset)) if highset.any() else -1
    return {"highset": hs, "gate": gate, "solo": solo_p}


def main() -> None:
    ai = float((RUN / "decision_threshold.txt").read_text().split()[0])
    solo = float((RUN / "decision_solo_threshold.txt").read_text().split()[0])
    dwell = int((RUN / "decision_dwell.txt").read_text().split()[0])
    device = torch.device("cpu")
    model = G.load_saved_model(RUN / "transformer_protection_lstm_best.pth", device)
    traces = G.load_dataset_traces([ROOT / f for f in FILES_B])
    probs = G.compute_model_probs(model, traces, device)

    rows = []
    for t, p in zip(traces, probs):
        ft = first_trips(p, t["vote87"], t["highset"], ai, solo, dwell)
        rows.append({"scenario": t["scenarioName"], "category": t["category"], "should_trip": bool(t["should_trip"]), "undetectable": bool(t["undetectable"]),
                     "onset": int(t["onset"]), "max_prob": float(p.max()) if len(p) else 0.0, **ft})

    def trip_sample(r, paths):
        v = [r[k] for k in paths if r[k] >= 0]
        return min(v) if v else -1

    def metrics(paths):
        faults = [r for r in rows if r["should_trip"] and not r["undetectable"]]
        healthy = [r for r in rows if not r["should_trip"] and not r["undetectable"]]
        ok_f = sum(1 for r in faults if (ts := trip_sample(r, paths)) >= 0 and ts >= r["onset"])
        fa = sum(1 for r in healthy if trip_sample(r, paths) >= 0)
        return {"n_fault": len(faults), "n_healthy": len(healthy), "dependability_pct": 100 * ok_f / len(faults), "security_pct": 100 * (len(healthy) - fa) / len(healthy),
                "missed": len(faults) - ok_f, "false_trips": fa}

    variants = {"Proposed as evaluated (high-set + gate + solo)": ("highset", "gate", "solo"),
                "without AI-alone path (high-set + gate)": ("highset", "gate"),
                "AI-alone path only (+ high-set)": ("highset", "solo"),
                "high-set only": ("highset",)}
    res = {k: metrics(v) for k, v in variants.items()}

    # which path trips first on each false trip, and by category
    healthy = [r for r in rows if not r["should_trip"] and not r["undetectable"]]
    first_path, by_cat = Counter(), defaultdict(Counter)
    for r in healthy:
        c = {k: r[k] for k in ("highset", "gate", "solo") if r[k] >= 0}
        if not c:
            continue
        p = min(c, key=c.get)
        first_path[p] += 1
        by_cat[r["category"]][p] += 1
        by_cat[r["category"]]["_both_gate_and_solo"] += int(r["gate"] >= 0 and r["solo"] >= 0)
    both_paths = sum(1 for r in healthy if r["gate"] >= 0 and r["solo"] >= 0)
    faults = [r for r in rows if r["should_trip"] and not r["undetectable"]]
    fault_first = Counter()
    for r in faults:
        c = {k: r[k] for k in ("highset", "gate", "solo") if r[k] >= 0}
        if c:
            fault_first[min(c, key=c.get)] += 1
    solo_only_faults = sum(1 for r in faults if r["solo"] >= 0 and r["gate"] < 0 and r["highset"] < 0)

    out = {"thresholds": {"ai": ai, "solo": solo, "dwell": dwell}, "variants": res, "false_trip_first_path": dict(first_path), "false_trips_with_gate_and_solo_both": both_paths,
           "false_trips_by_category": {c: dict(v) for c, v in by_cat.items()}, "fault_first_path": dict(fault_first), "faults_tripped_only_by_solo": solo_only_faults}
    (OUT / "trip_path_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    L = [f"Plant B zero-shot trip-path check (plant-A final model, AI {ai}, solo {solo}, dwell {dwell}; {len(traces)} traces)", ""]
    for k, m in res.items():
        L.append(f"{k:52s} dep {m['dependability_pct']:6.2f} %  sec {m['security_pct']:6.2f} %  missed {m['missed']:3d}  false trips {m['false_trips']:3d}")
    L += ["", f"False trips (detectable healthy traces, n={len(healthy)}): first path = {dict(first_path)}; traces where BOTH gated and AI-alone paths fired: {both_paths}",
          "By category (first path; _both_gate_and_solo = traces where both fired):"]
    for c, v in sorted(by_cat.items(), key=lambda x: -sum(n for k, n in x[1].items() if not k.startswith('_'))):
        L.append(f"   {c:26s} {dict(v)}")
    L += ["", f"Faults (n={len(faults)}): first path = {dict(fault_first)}; tripped ONLY by the AI-alone path (neither gate nor high-set): {solo_only_faults}"]
    (OUT / "trip_path_check.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
