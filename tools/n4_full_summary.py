"""Summary of runs/20261101_v5_benchmark_fair/full/<method>: CV native vs like-for-like (mode b) and the final-model OOD / plant-B results."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C
base = ROOT / "runs" / "20261101_v5_benchmark_fair" / "full"
L = [f"{'method':20s} {'set':12s} {'folds':>5s} | {'native dep':>10s} {'sec':>6s} | {'mode b dep':>10s} {'sec':>6s} | {'|d dep|':>7s} {'|d sec|':>7s}"]
for d in sorted(p for p in base.iterdir() if p.is_dir()):
    cvf = sorted(d.glob("cv_seed*_fold*.json"))
    if cvf:
        per = {"native": {}, "modeb": {}}
        for f in cvf:
            j = json.loads(f.read_text())
            for m in per:
                per[m].setdefault(f.name.split("_")[1], []).extend(j[m])
        S = {m: [C.summarise(r) for r in per[m].values()] for m in per}
        n = {m: (np.mean([s["dependability_pct"] for s in S[m]]), np.mean([s["security_pct"] for s in S[m]])) for m in S}
        L.append(f"{d.name:20s} {'CV plant A':12s} {len(cvf):5d} | {n['native'][0]:10.2f} {n['native'][1]:6.2f} | {n['modeb'][0]:10.2f} {n['modeb'][1]:6.2f} | {abs(n['native'][0]-n['modeb'][0]):7.2f} {abs(n['native'][1]-n['modeb'][1]):7.2f}" + ("  >5 pt" if max(abs(n['native'][0]-n['modeb'][0]), abs(n['native'][1]-n['modeb'][1])) > 5 else ""))
    for f in sorted(d.glob("final_*.json")):
        j = json.loads(f.read_text()); a, b = C.summarise(j["native"]), C.summarise(j["modeb"])
        L.append(f"{d.name:20s} {f.stem[6:]:12s} {1:5d} | {a['dependability_pct']:10.2f} {a['security_pct']:6.2f} | {b['dependability_pct']:10.2f} {b['security_pct']:6.2f} | {abs(a['dependability_pct']-b['dependability_pct']):7.2f} {abs(a['security_pct']-b['security_pct']):7.2f}   (n={a['n_fault']}+{a['n_healthy']}, thr {j['thr']})")
print("\n".join(L)); (base.parent / "n4_full_summary.txt").write_text("\n".join(L))
