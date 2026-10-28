"""Read StressTestDataset_*.mat / StressDataset_v2_*.mat (MATLAB v7.3) traces with their metadata.

v2 files (generate_stress_dataset_v2.m) also carry verified timing and per-sample checks
(checkPassed, timingOK, eventVisible, faultDiffPu, loadPu, noisePct, ...). Every numeric
1 x N field in the file is loaded automatically.

Each trace keeps: primary/secondary currents [T x 3], scenario name, zone,
fault type, shouldTrip, inception time, fault resistance, noise level,
inception angle, source file and a content fingerprint (SHA-1 of the raw
currents) used to detect duplicate traces across files.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import h5py
import numpy as np

FS = 1600.0
NUMERIC_FIELDS = ("inceptionTime", "faultResistance", "noiseLevel", "inceptionAngle", "energisationTime")
TEXT_FIELDS = ("scenarioName", "zone", "faultType", "simulationStatus", "scenarioKind")


def _cell(handle: h5py.File, field: h5py.Dataset, i: int):
    refs = field[()].reshape(-1)
    return handle[refs[i]][()]


def _text(arr) -> str:
    arr = np.asarray(arr)
    if arr.dtype.kind in "ui" and arr.size:
        return "".join(chr(int(c)) for c in arr.reshape(-1))
    return ""


def _currents(arr) -> np.ndarray | None:
    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim != 2 or arr.size < 6 or 3 not in arr.shape:
        return None
    return arr if arr.shape[1] == 3 else arr.T   # MATLAB [T x 3] arrives as [3 x T]


def load_traces(path: Path) -> list[dict]:
    traces: list[dict] = []
    with h5py.File(path, "r") as handle:
        ds = handle["dataset"]
        n = ds["primaryCurrent"].shape[-1] if ds["primaryCurrent"].shape[0] == 1 else ds["primaryCurrent"].shape[0]
        should = np.asarray(ds["shouldTrip"][()]).reshape(-1)
        numeric = {}
        for k in ds.keys():                       # every numeric 1 x N field (v1 and v2 files)
            obj = ds[k]
            if isinstance(obj, h5py.Dataset) and obj.dtype.kind in "fiub" and obj.size == n and k != "shouldTrip":
                numeric[k] = np.asarray(obj[()], dtype=float).reshape(-1)
        for i in range(n):
            ip = _currents(_cell(handle, ds["primaryCurrent"], i))
            is_ = _currents(_cell(handle, ds["secondaryCurrent"], i))
            if ip is None or is_ is None or ip.shape != is_.shape:
                continue
            rec = {
                "source_file": path.name,
                "source_index": i,
                "plant": "B" if ("plantb" in path.name.lower() or "plant_b" in path.name.lower()) else "A",
                "primary": ip,
                "secondary": is_,
                "should_trip": int(should[i]),
                "fingerprint": hashlib.sha1(np.ascontiguousarray(ip).tobytes() + np.ascontiguousarray(is_).tobytes()).hexdigest(),
            }
            for k in TEXT_FIELDS:
                rec[k] = _text(_cell(handle, ds[k], i)) if k in ds else ""
            for k, v in numeric.items():
                rec[k] = float(v[i])
            traces.append(rec)
    return traces


def detect_fault_onset(primary: np.ndarray, secondary: np.ndarray, fraction: float = 0.35) -> int:
    """Sample index where the fault disturbance starts, measured from the waveform.

    Uses the cycle-difference detector |i(t) - i(t - 1 cycle)| on the raw
    differential current (the same I_diff the features use) and returns the first
    sample exceeding `fraction` of its maximum. The metadata inceptionTime is not
    used because it does not match the simulated waveforms for internal faults.
    Returns -1 when no disturbance is found.
    """
    d = primary - secondary
    cd = np.abs(d[32:] - d[:-32]).max(axis=1)
    if cd.max() <= 1e-6:
        return -1
    idx = np.flatnonzero(cd >= fraction * cd.max())
    return int(idx[0] + 32) if idx.size else -1
