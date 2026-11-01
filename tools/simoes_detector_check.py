"""Detector firings per trace of the Simoes et al. detector on noise-only / event traces for several threshold factors (spec amendment 1).
Output: documents/baselines/simoes_detector_check.txt"""
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lstm_models"))
from baselines import common as C, simoes2021_rtbswt_svm as S

FACT = (3.0, 10.0, 30.0, 100.0)
want = {"Normal", "Overexcitation", "Inrush_NoLoad", "Internal_AB", "External_ABC", "Internal_HiZ_AB"}
res, seen = defaultdict(lambda: {f: [] for f in FACT}), defaultdict(int)
for tr in C.iter_hr(scenarios=want):
    n = tr["meta"]["scenarioName"]
    if seen[n] >= 15:
        continue
    seen[n] += 1
    E = S.energies(tr["Ip"], tr["Is"])
    for f in FACT:
        kd = S.detect(E, f)
        lab = S.label_events(tr["meta"], kd)
        res[n][f].append((len(kd), sum(l is None for l in lab), int(any(l is not None for l in lab))))
    if all(seen[w] >= 15 for w in want):
        break
L = ["Simoes et al. detector (adaptive threshold = factor x mean of the previous two cycles), 15 traces per scenario, plant A, 12.8 kHz, armed from 0.12 s",
     "per scenario and factor: mean firings per trace | mean firings that match no known event | fraction of traces with at least one matched firing", ""]
for n in sorted(res):
    L.append(n)
    for f in FACT:
        a = np.array(res[n][f], dtype=float)
        L.append(f"   factor {f:5.0f}: {a[:, 0].mean():8.1f} | {a[:, 1].mean():8.1f} | {a[:, 2].mean():.2f}")
out = Path(__file__).resolve().parent.parent / "documents" / "baselines" / "simoes_detector_check.txt"
out.write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
