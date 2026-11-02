"""Metadata (+ 1600 Hz 87T high-set vector) of the plant-B main traces for the HR benchmark: same filtering / de-duplication / fields as
run_plant_b_generalization_v5.load_dataset_traces (features dropped). Output: runs/20261101_v5_benchmark_fair/cache/traces_cache_plantB_main.npz"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models")); sys.path.insert(0, str(ROOT / "tools"))
import relay87t, stress_dataset, train_trace_split as T
from stress_dataset import FS
import run_plant_b_generalization_v5 as G
files = [ROOT / "datasets" / n for n in ("StressDataset_PlantBv5_20261028_212041.mat", "StressDataset_PlantBv5Only_20261029_111005.mat", "StressDataset_PlantBv5Only_20261029_111251.mat")]
traces, seen = [], set()
for fp in files:
    for t in stress_dataset.load_traces(fp):
        if not G.relaxed_ok_trace(t) or t["fingerprint"] in seen:
            continue
        seen.add(t["fingerprint"]); t["plant"] = "B"
        t["onset"] = int(round(t["inceptionTime"] * FS)) if t.get("inceptionTime") is not None and not np.isnan(t["inceptionTime"]) else stress_dataset.detect_fault_onset(t["primary"], t["secondary"])
        a = relay87t.analyse(t["primary"], t["secondary"], plant="B")
        t["vote87"], t["highset"] = a["vote"], a["highset"]
        t["fault_pu"] = relay87t.fault_rise_pu(t["primary"], t["secondary"], t["onset"], plant="B") if t["onset"] >= 0 else float("nan")
        t["category"] = T.category(t["scenarioName"])
        t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < G.MIN_FAULT_PU)
        del t["primary"], t["secondary"]
        traces.append(t)
out = ROOT / "runs" / "20261101_v5_benchmark_fair" / "cache" / "traces_cache_plantB_main.npz"
np.savez_compressed(out, traces=np.array(traces, dtype=object))
print(len(traces), "plant-B traces; undetectable", sum(t["undetectable"] for t in traces))
