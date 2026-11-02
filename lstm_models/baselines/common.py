"""Shared infrastructure of the faithful reproductions (BENCHMARK_FAIRNESS_PLAN.md Part 2):
20 kHz data access (blocks written by generate_stress_dataset_*_hr_v5.m), anti-aliased resampling to a method's own rate, plant compensation,
and scoring in exactly the form of the relay mirror (rows with the same keys, so lstm_models/train_cv_v5.summarise and the statistics code apply).
"""
from __future__ import annotations

import glob
import re
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parent.parent.parent
HR_DIR = ROOT / "datasets" / "hr"
FS_HR = 20000
FS_RELAY = 1600
MIN_FAULT_PU = 0.05

# main-set files of plant A (original run ids) and their 20 kHz replays; (prefix of the HR block files, original dataset file name)
PLANT_A_MAIN = [("StressDataset_v5HR_20261028_162333", "StressDataset_v5_20261028_162333.mat"),
                ("StressDataset_v5HROnly_20261028_232627", "StressDataset_v5Only_20261028_232627.mat"),
                ("StressDataset_v5HROnly_20261028_233305", "StressDataset_v5Only_20261028_233305.mat"),
                ("StressDataset_v5HROnly_20261028_234041", "StressDataset_v5Only_20261028_234041.mat"),
                ("StressDataset_v5HROnly_20261029_111722", "StressDataset_v5Only_20261029_111722.mat")]
PLANT_A_OOD = [("StressDataset_v5HROOD_20261028_205712", "StressDataset_v5OOD_20261028_205712.mat")]
CACHE_A_MAIN = ROOT / "runs" / "20261029_v5_cv5_seeds" / "traces_cache.npz"
CACHE_A_OOD = ROOT / "runs" / "20261029_v5_final" / "traces_cache_ood.npz"


# ---------------------------------------------------------------------------------------------------------------- metadata
def load_meta(cache: Path = CACHE_A_MAIN) -> dict[tuple[str, int], dict]:
    """(original file name, 0-based index in that file) -> metadata of the kept, de-duplicated trace (features dropped)."""
    out = {}
    for t in np.load(cache, allow_pickle=True)["traces"]:
        m = {k: v for k, v in t.items() if k not in ("features", "vote87", "highset")}
        m["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < MIN_FAULT_PU)
        m["onset_time"] = (t["onset"] / FS_RELAY) if t["onset"] >= 0 else None
        out[(t["source_file"], int(t["source_index"]))] = m
    return out


def block_files(prefix: str) -> list[Path]:
    """Block files of one HR run, ordered by their first trace index."""
    fs = [Path(p) for p in glob.glob(str(HR_DIR / f"{prefix}_blk*.mat"))]
    key = lambda p: int(re.search(r"_blk(\d+)_(\d+)", p.name).group(1))  # noqa: E731
    return sorted(fs, key=key)


def iter_hr(runs=PLANT_A_MAIN, cache: Path = CACHE_A_MAIN, only_kept: bool = True, scenarios: set[str] | None = None):
    """Yield dicts with the 20 kHz arrays Ip, Is (CT secondaries incl. noise), Tp, Ts (true line currents) of shape [22001, 3] and the metadata."""
    meta = load_meta(cache)
    for prefix, src in runs:
        for f in block_files(prefix):
            m = loadmat(f)
            idx = np.asarray(m["idx"]).ravel().astype(int)
            for k, i in enumerate(idx):
                md = meta.get((src, int(i) - 1))
                if md is None and only_kept:
                    continue          # dropped by the generator checks or as a duplicate
                if scenarios is not None and md["scenarioName"] not in scenarios:
                    continue
                yield {"Ip": m["Ip"][:, :, k], "Is": m["Is"][:, :, k], "Tp": m["Tp"][:, :, k], "Ts": m["Ts"][:, :, k], "meta": md, "src": src, "index": int(i) - 1}


# ---------------------------------------------------------------------------------------------------------------- signals
def resample(x: np.ndarray, fs_out: float, fs_in: float = FS_HR) -> np.ndarray:
    """Anti-aliased polyphase resampling along axis 0 (Kaiser window), e.g. 20 kHz -> 12.8 kHz is 16/25."""
    from fractions import Fraction
    r = Fraction(int(round(fs_out)), int(round(fs_in))).limit_denominator(1000)
    return resample_poly(np.asarray(x, dtype=np.float64), r.numerator, r.denominator, axis=0, window=("kaiser", 5.0))


def plant_config(plant: str = "A") -> dict:
    import sys
    sys.path.insert(0, str(ROOT / "lstm_models"))
    import relay87t
    return relay87t.get_plant_config(plant)


def plant_pu(Ip: np.ndarray, Is: np.ndarray, plant: str = "A") -> tuple[np.ndarray, np.ndarray]:
    """CT-secondary currents -> per-unit, phase-compensated currents of the two sides (same convention as the relay mirror)."""
    c = plant_config(plant)
    return (Ip / c["i_nom"]) @ c["m_hv"].T, (Is / c["i_nom"]) @ c["m_lv"].T


def time_axis(n: int, fs: float) -> np.ndarray:
    return np.arange(n) / fs


# ---------------------------------------------------------------------------------------------------------------- scoring
def score_row(meta: dict, trip_time: float | None, trace_id: int | None = None) -> dict:
    """Row of the relay mirror for one trace. trip_time in seconds from the start of the record (None = no trip).
    Same rules as lstm_models/run_plant_b_generalization_v5.evaluate_relay_on_traces: a trip before the fault onset is a pre-fault trip and wrong."""
    tripped = trip_time is not None
    onset = meta["onset_time"]
    should = bool(meta["should_trip"])
    early = bool(should and tripped and onset is not None and trip_time < onset)
    operate_ms = (trip_time - onset) * 1e3 if (should and tripped and not early and onset is not None) else None
    correct = bool((should and tripped and not early) or (not should and not tripped))
    return {"trace": trace_id, "scenario": meta["scenarioName"], "category": meta.get("category"), "should_trip": int(should), "tripped": tripped,
            "trip_time_s": trip_time, "onset_time_s": onset, "operate_ms": operate_ms, "tripped_before_fault": early, "correct": correct,
            "undetectable": bool(meta["undetectable"])}


def summarise(rows: list[dict]) -> dict:
    """Headline metrics (dependability, security, operate time) with undetectable faults excluded, as in train_cv_v5.summarise."""
    head = [r for r in rows if not r["undetectable"]]
    f = [r for r in head if r["should_trip"]]
    h = [r for r in head if not r["should_trip"]]
    ms = np.array([r["operate_ms"] for r in f if r["operate_ms"] is not None])
    return {"n_fault": len(f), "n_healthy": len(h),
            "dependability_pct": 100 * float(np.mean([r["correct"] for r in f])) if f else None,
            "security_pct": 100 * float(np.mean([r["correct"] for r in h])) if h else None,
            "missed": sum(1 for r in f if not r["tripped"]), "false_trips": sum(1 for r in h if r["tripped"]),
            "pre_fault_trips": sum(1 for r in f if r["tripped_before_fault"]),
            "operate_median_ms": float(np.median(ms)) if len(ms) else None, "operate_p90_ms": float(np.percentile(ms, 90)) if len(ms) else None}


# ---------------------------------------------------------------------------------------------------------------- label mapping (spec sections 5/6 of each method)
def event_class(meta: dict) -> str:
    """Coarse event class of a trace used by the reproductions: 'IF' internal fault, 'EF' external fault, 'EN' energisation (inrush type),
    'NONE' (normal operation, over-excitation)."""
    s = meta["scenarioName"]
    if s.startswith("Internal") or s.startswith("Stress_CTSat_Int") or s == "Stress_FaultInInrush":
        return "IF"
    if s.startswith("External") or s.startswith("Stress_ExtCTSat") or s == "Stress_ExtInInrush":
        return "EF"
    if s.startswith("Inrush") or s == "Recovery_Inrush":
        return "EN"
    return "NONE"


def events(meta: dict) -> list[tuple[float, str]]:
    """Known disturbances of a trace as (time in s, class): 'EN' energisation/recovery inrush, 'EF' external fault, 'IF' internal fault.
    Used to label detector firings of the event-based reproductions (Simoes et al.)."""
    s, t_f, t_e, t_f2 = meta["scenarioName"], meta.get("inceptionTime", np.nan), meta.get("energisationTime", np.nan), meta.get("faultTime2", np.nan)
    ev: list[tuple[float, str]] = []
    if s.startswith("Inrush"):
        ev.append((float(t_e), "EN"))
    elif s == "Recovery_Inrush":
        ev += [(float(t_f), "EF"), (float(t_f2), "EN")]
    elif s == "Stress_FaultInInrush":
        ev += [(float(t_e), "EN"), (float(t_f), "IF")]
    elif s == "Stress_ExtInInrush":
        ev += [(float(t_e), "EN"), (float(t_f), "EF")]
    elif event_class(meta) in ("IF", "EF") and np.isfinite(t_f):
        ev.append((float(t_f), event_class(meta)))
        if s == "Internal_Evolving" and np.isfinite(t_f2):
            ev.append((float(t_f2), "IF"))
    return [(t, c) for t, c in ev if np.isfinite(t)]


# ---------------------------------------------------------------------------------------------------------------- plant B and OOD (N4)
PLANT_B_MAIN = [("StressDataset_PlantBv5HR_20261028_212041", "StressDataset_PlantBv5_20261028_212041.mat"),
                ("StressDataset_PlantBv5HROnly_20261029_111005", "StressDataset_PlantBv5Only_20261029_111005.mat"),
                ("StressDataset_PlantBv5HROnly_20261029_111251", "StressDataset_PlantBv5Only_20261029_111251.mat")]
CACHE_B_MAIN = ROOT / "runs" / "20261101_v5_benchmark_fair" / "cache" / "traces_cache_plantB_main.npz"


def load_highset_times(cache: Path) -> dict[tuple[str, int], float | None]:
    """(source file, index) -> time (s) of the first sample of the 87T high-set element (Id > 10 pu) at the relay's 1,600 Hz, None if it never fires."""
    out = {}
    for t in np.load(cache, allow_pickle=True)["traces"]:
        h = np.asarray(t["highset"]).astype(bool)
        out[(t["source_file"], int(t["source_index"]))] = float(np.argmax(h) / FS_RELAY) if h.any() else None
    return out
