"""Inrush strength of the generated datasets (replaces check 4 of simulations/check_plant_v4_physics.m, whose probe kept the LV breaker closed with the
full load connected, so its '0.99 pu crest' was just the load current's own peak).

    python tools/check_inrush_from_datasets.py     -> simulations/inrush_check_from_datasets.txt

For every no-load / loaded inrush trace: peak |HV CT secondary current| in the 100 ms after the energisation time, in units of the rated PEAK
secondary current (sqrt(2) x rated secondary RMS). Normal traces over the same kind of window are the reference.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from stress_dataset import load_traces  # noqa: E402

PLANTS = [
    ("plant A v4 (300 MVA, 230/11 kV)", ROOT / "datasets" / "StressDataset_v4_20261027_004639.mat", 1.8610),
    ("plant B   (40 MVA, 132/33 kV)", ROOT / "datasets" / "StressDataset_PlantB_20261027_215741.mat", 0.8232),
]


def main() -> None:
    L = ["Inrush strength from the generated datasets (script: tools/check_inrush_from_datasets.py)", "",
         "Peak |HV CT secondary| in the 100 ms after the energisation instant (Normal: after t = 0.3 s), in units of the rated PEAK secondary current (sqrt(2) x rated RMS).", ""]
    for label, path, i_nom in PLANTS:
        T = load_traces(path)
        L.append(label)
        for scen in ("Inrush_NoLoad", "Inrush_Loaded", "Normal"):
            sel = [t for t in T if t["scenarioName"] == scen and t.get("checkPassed") == 1]
            if not sel:
                continue
            pk = []
            for t in sel:
                e = 0.3 if scen == "Normal" else t.get("energisationTime", 0.0)
                i0 = int(round(e * 1600))
                pk.append(np.abs(t["primary"][i0:i0 + 160]).max() / (i_nom * np.sqrt(2)))
            pk = np.array(pk)
            L.append(f"  {scen:14s} n={len(pk):4d}  median {np.median(pk):5.2f}  p10 {np.percentile(pk, 10):5.2f}  p90 {np.percentile(pk, 90):5.2f}  max {pk.max():5.2f}")
        L.append("")
    out = ROOT / "simulations" / "inrush_check_from_datasets.txt"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
