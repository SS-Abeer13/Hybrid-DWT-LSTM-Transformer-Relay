"""Like-for-like mode (b) of BENCHMARK_FAIRNESS_PLAN.md Part 2: the method's score stream put through the project's 20-sample dwell (12.5 ms at the relay's
1,600 Hz) and a validation-tuned threshold (plateau rule of train_trace_split.tune_threshold: dependability within 2 pt and security within 1 pt of the best,
centre of the longest run in logit space); the relay mirror's high-set element (Id > 10 pu) trips independently, as for the proposed relay.
Event-based methods (Simoes, Ngaopitakkul: one score per detector firing) have no dwell: trip at the first firing whose score reaches the threshold."""
from __future__ import annotations

import numpy as np

from . import common as C

DWELL_S = 20 / 1600.0
GRID = np.round(np.concatenate([np.arange(0.05, 0.95, 0.05), np.arange(0.95, 0.99, 0.01), [0.99, 0.993, 0.995, 0.997, 0.999, 0.9995]]), 4)
DEP_TOL, SEC_TOL = 2.0, 1.0


def trip_time(times: np.ndarray, scores: np.ndarray, thr: float, step_s: float, event_based: bool, hs_time: float | None, dwell_s: float = DWELL_S) -> float | None:
    cand = []
    if hs_time is not None:
        cand.append(hs_time)
    ok = scores >= thr
    if event_based:
        if ok.any():
            cand.append(float(times[np.argmax(ok)]))
    elif ok.any():
        need = max(1, int(round(dwell_s / step_s)))
        run = 0
        prev = None
        for t, o in zip(times, ok):
            if o and (prev is not None and run > 0 and abs(t - prev - step_s) < 0.5 * step_s):
                run += 1
            elif o:
                run = 1
            else:
                run = 0
            prev = t
            if run >= need:
                cand.append(float(t))
                break
    return min(cand) if cand else None


def tune(items: list[dict]) -> tuple[float, list[dict]]:
    """items: dicts with 'meta', 'id', 'stream' = (times, scores), 'step', 'event', 'hs'. Returns (threshold, per-threshold validation table)."""
    table = []
    for thr in GRID:
        rows = [C.score_row(it["meta"], trip_time(*it["stream"], float(thr), it["step"], it["event"], it["hs"]), it["id"]) for it in items]
        s = C.summarise(rows)
        table.append({"thr": float(thr), "dep": s["dependability_pct"], "sec": s["security_pct"]})
    top = max(r["dep"] for r in table)
    ok = [r for r in table if r["dep"] >= top - DEP_TOL]
    best_sec = max(r["sec"] for r in ok)
    feas = {r["thr"] for r in ok if r["sec"] >= best_sec - SEC_TOL}
    runs, cur = [], []
    for g in map(float, GRID):
        if g in feas:
            cur.append(g)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    run = max(runs, key=lambda r: (len(r), r[-1]))
    logit = lambda x: float(np.log(x / (1 - x)))  # noqa: E731
    mid = 0.5 * (logit(run[0]) + logit(run[-1]))
    return min(run, key=lambda g: abs(logit(g) - mid)), table
