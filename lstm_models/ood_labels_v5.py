"""OOD block labels of the v5 datasets, built from the generator's own ranges (simulations/generator_ranges_v5.json).

v4 had two different labels for OOD block 3 (report_ood.txt "4-8x", harmonic summary "12-16x"); the single source of truth is now the JSON that the
generators read (cfg.burden), so a report cannot disagree with the data.
"""
from __future__ import annotations

import json
from pathlib import Path

RANGES = Path(__file__).resolve().parent.parent / "simulations" / "generator_ranges_v5.json"


def ood_block_labels(plant: str = "A") -> dict[int, str]:
    r = json.loads(RANGES.read_text(encoding="utf-8"))[plant.upper()]
    lo, hi = r["burden_ood"]
    return {
        1: "extreme load (1-10 %, 110-130 %)",
        2: "weak source 3x + 49.5/50.5 Hz",
        3: f"CT burden {lo:g}-{hi:g}x",
        4: "over-excitation 1.5-1.6 pu + residual flux 0.9 pu",
        5: "noise 5 % + CT mismatch +/-8 %",
    }
