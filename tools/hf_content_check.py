"""How much high-frequency energy do the simulated plants carry? (BENCHMARK_FAIRNESS_PLAN.md Part 2: to be stated next to the results of the
methods built on kHz-range transients, Simoes et al. and Ngaopitakkul and Kunakorn.)

For plant-A traces of each scenario group the 20 kHz compensated differential current (per unit) is analysed in a 20 ms window right after the event
(fault inception or energisation) and in a 20 ms window shortly before it (noise and quantisation only): fraction of the spectral energy above
1.6 kHz, 5 kHz and 8 kHz, with and without the mean removed. Output: documents/baselines/hf_content.txt
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lstm_models"))
from baselines import common as C  # noqa: E402

FS = C.FS_HR
W = int(0.02 * FS)
BANDS = (1600.0, 5000.0, 8000.0)
PER_GROUP = 12


def band_fractions(x: np.ndarray) -> list[float]:
    X = np.abs(np.fft.rfft(x - x.mean(0), axis=0)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / FS)
    tot = X.sum()
    return [float(X[f > b].sum() / tot) if tot > 0 else float("nan") for b in BANDS]


def main() -> None:
    groups = defaultdict(list)
    seen = defaultdict(int)
    for tr in C.iter_hr(C.PLANT_A_MAIN[:1]):
        g = C.event_class(tr["meta"])
        name = tr["meta"]["category"]
        if seen[name] >= PER_GROUP:
            continue
        ev = C.events(tr["meta"])
        if not ev:
            continue
        seen[name] += 1
        t0 = ev[0][0]
        hv, lv = C.plant_pu(tr["Ip"].astype(float), tr["Is"].astype(float), "A")
        d = lv - hv
        i0 = int(t0 * FS)
        groups[name].append((band_fractions(d[i0:i0 + W]), band_fractions(d[i0 - W - 100:i0 - 100]), float(np.sqrt((d[i0:i0 + W] ** 2).mean())), float(np.sqrt((d[i0 - W - 100:i0 - 100] ** 2).mean()))))
    L = ["High-frequency content of the v5 plant-A differential current at 20 kHz (compensated, per unit), 20 ms windows",
         f"{PER_GROUP} traces per scenario group (first ones of the main set); fraction of the spectral energy above {BANDS[0]:.0f}, {BANDS[1]:.0f}, {BANDS[2]:.0f} Hz",
         "columns: group | after the event: > 1.6 kHz, > 5 kHz, > 8 kHz | before the event (noise only): > 1.6 kHz, > 5 kHz, > 8 kHz | RMS after / before (pu)", ""]
    for name, v in sorted(groups.items()):
        a = np.nanmedian([x[0] for x in v], axis=0)
        b = np.nanmedian([x[1] for x in v], axis=0)
        ra, rb = np.median([x[2] for x in v]), np.median([x[3] for x in v])
        L.append(f"{name:20s} | " + " ".join(f"{q:8.2e}" for q in a) + " | " + " ".join(f"{q:8.2e}" for q in b) + f" | {ra:.3g} / {rb:.3g}")
    out = Path(__file__).resolve().parent.parent / "documents" / "baselines" / "hf_content.txt"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
