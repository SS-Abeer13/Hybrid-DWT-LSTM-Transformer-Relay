"""Per-trace rows of every method and instance of the paper, read only from saved result files (paper-v1).

Used by tools/paper_operate_times.py, tools/make_paper_figures.py and tools/build_paper_v1_macros.py.
Every row set is restricted to the common set (plant-A traces that have a 20 kHz re-simulation), pooled over the 3 seeds x 5 folds.
Each row carries: seed, fold, trace, should_trip, correct, undetectable, category, operate_ms (None if not saved or not tripped).
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import publication_tables_AD as AD  # noqa: E402  (BAD, cv helpers)

BASE, CVD, DEP, SEEDS = AD.BASE, AD.CVD, AD.DEP, AD.cv.SEEDS

# display name -> (group, loader key)
GROUPS = ("Reproduction (native)", "Reproduction (like-for-like)", "Conventional relay", "Dual-path instance", "Ablation")
REPRO = [("simoes_grid", "Simões"), ("ngaopitakkul", "Ngaopitakkul"), ("abdusalam_ba_svm", "Abdusalam"),
         ("afrasiabi", "Afrasiabi"), ("key", "Key"), ("alhamd", "Alhamd")]
B2 = [("1D-CNN", "1D-CNN"), ("Wavelet-GRU", "GRU"), ("Wavelet-ANN", "MLP"), ("Wavelet-RF", "Random forest"), ("Proposed LSTM", "LSTM (tuned)"), ("Wavelet-SVM", "SVM")]


def _cv_variant(variant: str) -> list[dict]:
    out = []
    for s in SEEDS:
        for k in range(1, 6):
            out += [r for r in json.loads((CVD / f"seed_{s}" / f"fold{k}" / "result.json").read_text())["rows"][variant] if r["trace"] not in AD.BAD]
    return out


@lru_cache(maxsize=None)
def category_map() -> dict[int, str]:
    """trace index -> category (the same for every seed), from the deployed model's CV rows."""
    return {r["trace"]: r["category"] for r in _cv_variant(DEP)}


def _full(name: str, mode: str) -> list[dict]:
    out = []
    for f in sorted((BASE / "full" / name).glob("cv_seed*_fold*.json")):
        j = json.loads(f.read_text())
        out += j[mode] if mode in j else j["hybrid"]
    return out


def _b2(model: str, mode: str) -> list[dict]:
    out = []
    for f in sorted((BASE / "b2_equal_search").glob("final_seed*_fold*.json")):
        out += [r for r in json.loads(f.read_text())[model][mode] if r["trace"] not in AD.BAD]
    return out


def _n6c(key: str) -> list[dict]:
    cm = category_map()
    rows = json.loads((BASE / "n6c_tuned_rows.json").read_text())[key]
    return [dict(r, trace=r["key"][2], category=cm[r["key"][2]], operate_ms=None) for r in rows if r["key"][2] in cm]


def harmonic_textbook_single_pass() -> list[dict]:
    """Per-phase harmonic 87T with textbook settings, one pass over all traces (no training): the only saved operate times of a harmonic relay."""
    rows = json.loads((ROOT / "runs" / "20261029_v5_harmonic87t" / "summary.json").read_text())["variants"]["per_phase"]["rows"]
    cm = category_map()
    return [dict(r, trace=r["trace_idx"], category=cm[r["trace_idx"]]) for r in rows if r["trace_idx"] in cm]


@lru_cache(maxsize=None)
def all_methods() -> dict[str, tuple[str, list[dict]]]:
    M: dict[str, tuple[str, list[dict]]] = {}
    for key, lab in REPRO:
        M[f"{lab} (native)"] = ("Reproduction (native)", _full(key, "native"))
        M[f"{lab} (like-for-like)"] = ("Reproduction (like-for-like)", _full(key, "modeb"))
    M["87T unrestrained"] = ("Conventional relay", _cv_variant("87T alone"))
    M["Harmonic 87T, textbook"] = ("Conventional relay", _n6c("textbook"))
    M["Harmonic 87T, tuned"] = ("Conventional relay", _n6c("tuned"))
    M["LSTM, deployed"] = ("Dual-path instance", _cv_variant(DEP))
    M["Key's network"] = ("Dual-path instance", _full("key_hybrid", "hybrid"))
    for key, lab in B2:
        M[lab if lab != "LSTM (tuned)" else "LSTM, tuned"] = ("Dual-path instance", _b2(key, "hybrid"))
    M["LSTM, deployed, gated only"] = ("Ablation", _cv_variant("Hybrid (87T gate)"))
    M["LSTM alone"] = ("Ablation", _cv_variant("LSTM alone"))
    return M


def dep_sec(rows: list[dict]) -> tuple[float, float]:
    """Mean over seeds of the pooled-fold dependability and security (the convention of Tables A-D)."""
    d, s = [], []
    for seed in SEEDS:
        rs = [r for r in rows if r["seed"] == seed and not r.get("undetectable")]
        d.append(100 * np.mean([r["correct"] for r in rs if r["should_trip"]]))
        s.append(100 * np.mean([r["correct"] for r in rs if not r["should_trip"]]))
    return float(np.mean(d)), float(np.mean(s))


def operate_times(rows: list[dict], categories: set[str] | None = None) -> np.ndarray:
    """Operate times (ms) of correctly tripped, detectable fault traces, pooled over seeds and folds."""
    return np.array([r["operate_ms"] for r in rows if r["should_trip"] and r["correct"] and not r.get("undetectable")
                     and r.get("operate_ms") is not None and (categories is None or r["category"] in categories)], dtype=float)
