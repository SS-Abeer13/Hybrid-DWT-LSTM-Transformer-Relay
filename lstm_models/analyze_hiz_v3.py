"""HiZ analysis of a CV run: dependability of the internal HiZ faults per Rf bin (87T-visible / AI-only / undetectable) for every variant.

    python lstm_models/analyze_hiz_v3.py runs/20261021_v3_cv5 runs/20261021_v3data_baseline/traces_cache_main.npz
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_cv_v3 import VARIANTS, wilson  # noqa: E402
from v3_checks import relaxed_ok_trace  # noqa: E402

run, cache = Path(sys.argv[1]), Path(sys.argv[2])
traces = [t for t in np.load(cache, allow_pickle=True)["traces"] if "checkPassed" not in t or relaxed_ok_trace(t)]   # same order as train_cv_v3.load_traces
BIN = {1: "87T-visible (Rf 0.3-1.2 ohm)", 2: "AI-only (1.2-7 ohm)", 3: "below detect limit (7-21 ohm)"}
rows = {v: [] for v in VARIANTS}
for f in sorted(run.glob("fold*/result.json")):
    res = json.loads(f.read_text(encoding="utf-8"))
    for v in VARIANTS:
        rows[v] += res["rows"][v]
L = [f"Internal HiZ faults by Rf bin, pooled out-of-fold ({run.name}); 'tripped after onset' for every trace, including the undetectable bin", ""]
L.append(f"{'bin':32s} {'n':>4s} {'faultDiffPu median':>19s} | " + " | ".join(f"{v[:24]:>24s}" for v in VARIANTS))
for b in (1, 2, 3):
    cells, n, dmed = [], 0, float("nan")
    for v in VARIANTS:
        sel = [r for r in rows[v] if traces[r["trace"]]["scenarioName"].startswith("Internal_HiZ_") and int(traces[r["trace"]].get("hizBin", 0)) == b]
        n = len(sel)
        ok = sum(1 for r in sel if r["tripped"] and not r["tripped_before_fault"])
        lo, hi = wilson(ok, n)
        cells.append(f"{100 * ok / max(n, 1):5.1f}% [{lo:4.1f},{hi:5.1f}]")
        dmed = float(np.median([traces[r["trace"]].get("fault_pu", np.nan) for r in sel])) if sel else float("nan")
    L.append(f"{BIN[b]:32s} {n:4d} {dmed:19.3f} | " + " | ".join(f"{c:>24s}" for c in cells))
out = run / "hiz_by_bin.txt"
out.write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
