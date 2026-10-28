import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for seed in ["seed_20261021", "seed_20261022", "seed_20261023"]:
    files = sorted(glob.glob(str(ROOT / f"runs/20261027_v4_cv5_seeds/{seed}/fold*/result.json")))
    if not files:
        continue
    print(f"\n==================== {seed} ({len(files)}/5 folds done) ====================")
    for f in files:
        with open(f) as fp:
            d = json.load(fp)
            s = d["summary"]
            k = s["fold"]
            h = s["variants"]["Hybrid + AI-alone path"]
            ep = s["epochs"]
            tm = s["train_minutes"]
            top = h["operate"].get("median_ms", float("nan"))
            print(f"Fold {k} ({ep} ep, {tm:.1f}m): Dep={h['dependability_pct']:.2f}%, Sec={h['security_pct']:.2f}%, FalseTrips={h['false_trips']}, Missed={h['missed']}, Top={top:.1f}ms")

    # Pooled rows
    all_rows = []
    for f in files:
        with open(f) as fp:
            d = json.load(fp)
            all_rows.extend(d["rows"]["Hybrid + AI-alone path"])
    
    # summarize all_rows
    import sys
    sys.path.insert(0, str(ROOT / "lstm_models"))
    from train_cv_v4 import summarise
    pooled = summarise(all_rows)
    print(f"\n--- POOLED {seed} ({len(files)} folds) ---")
    print(f"Dependability: {pooled['dependability_pct']:.2f}%  (Missed: {pooled['missed']}/{pooled['n_fault']})")
    print(f"Security:      {pooled['security_pct']:.2f}%  (False Trips: {pooled['false_trips']}/{pooled['n_healthy']})")
    top_p = pooled["operate"].get("median_ms", float("nan"))
    print(f"Operate Time:  {top_p:.1f} ms")
