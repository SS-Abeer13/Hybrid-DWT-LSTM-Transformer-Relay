"""Relaxed acceptance of v3 generator checks (documented in IMPLEMENTATION_PLAN.md, 2026-10-21).

The generator's checkPassed is strict. Two benign failure types are accepted here, everything else (duplicates, wrong event time > 20 ms,
noise failures outside over-excitation, simulation errors) stays rejected:
  * timing 'late': the cycle-difference detector fired 12.5-20 ms after the intended time (detector latency on very large / saturated currents;
    the training labels use the exact intended time, so labels are unaffected);
  * noise-only failure in the Overexcitation scenario: the saturated core's harmonics leak through the 20 ms cycle-difference at f != 50 Hz
    (check artefact; fixed in the generator for traces generated after 2026-10-21 09:30).
"""
from __future__ import annotations

import numpy as np

LATE_LIMIT_S = 0.020


def relaxed_ok(num: dict, names, status=None) -> np.ndarray:
    """Boolean array: strict pass OR one of the two benign failures. `num` maps field -> 1-D float array (from the dataset)."""
    n = len(names)
    strict = num["checkPassed"] == 1
    isover = np.array([nm == "Overexcitation" for nm in names])
    dup = num["duplicate"] == 1
    late = (num["timingOK"] == 0) & (num["noiseOK"] != 0) & ~dup & (np.abs(num["eventDetected"] - num["inceptionTime"]) <= LATE_LIMIT_S)
    noise_only = isover & (num["noiseOK"] == 0) & (num["timingOK"] != 0) & ~dup
    ok = strict | late | noise_only
    if status is not None:
        ok &= np.array([s == "Success" for s in status])
    return ok[:n]


def relaxed_ok_trace(t: dict) -> bool:
    """Same rule for one trace dict (fields as loaded by stress_dataset.load_traces)."""
    if t.get("checkPassed") == 1:
        return True
    if t.get("duplicate") == 1:
        return False
    late = t.get("timingOK") == 0 and t.get("noiseOK") != 0 and abs(t.get("eventDetected", np.nan) - t.get("inceptionTime", np.nan)) <= LATE_LIMIT_S
    noise_only = t.get("scenarioName") == "Overexcitation" and t.get("noiseOK") == 0 and t.get("timingOK") != 0
    return bool(late or noise_only)
