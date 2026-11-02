"""Per-method dependability / security (mean over seeds of the pooled folds), operate time, from the saved row files of runs/20261101_v5_benchmark_fair/<method>/rows_seed*_fold*.json"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C
base = ROOT / "runs" / "20261101_v5_benchmark_fair"
L = [f"{'method':22s} {'folds':>5s} {'dep %':>7s} {'sec %':>7s} {'median op ms':>13s}"]
for d in sorted(p for p in base.iterdir() if p.is_dir() and list(p.glob("rows_seed*_fold*.json"))):
    per_seed = {}
    for f in sorted(d.glob("rows_seed*_fold*.json")):
        per_seed.setdefault(f.name.split("_")[1], []).extend(json.loads(f.read_text()))
    S = [C.summarise(r) for r in per_seed.values()]
    nf = len(list(d.glob("rows_seed*_fold*.json")))
    ms = np.median([s["operate_median_ms"] for s in S if s["operate_median_ms"] is not None]) if any(s["operate_median_ms"] is not None for s in S) else float("nan")
    L.append(f"{d.name:22s} {nf:5d} {np.mean([s['dependability_pct'] for s in S]):7.2f} {np.mean([s['security_pct'] for s in S]):7.2f} {ms:13.1f}")
print("\n".join(L)); (base / "n4_progress.txt").write_text("\n".join(L))
