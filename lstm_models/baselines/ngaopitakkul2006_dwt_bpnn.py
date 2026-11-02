"""Ngaopitakkul and Kunakorn 2006, IJCAS 4(3):365-371 - db4 scale-1 DWT energies of the differential currents -> two-hidden-layer tanh network.
Implemented from documents/baselines/ngaopitakkul2006_dwt_bpnn_spec.md, retargeted with an all-zero "no internal fault" pattern (spec section 4).

Data path: 20 kHz CT secondaries (the highest rate of D2; the paper uses 200 kHz) -> plant compensation -> d = lv - hv (A, B, C) and the zero-sequence
mean(d) -> db4 scale-1 detail coefficients (decimated, 10 kHz) squared -> detector (coefficient >= 5 x largest of the previous two cycles) ->
features = log10 of the largest squared coefficient of each of the four channels in the quarter cycle after the detection (min-max normalised) ->
4-h1-h2-8 network (tanh, tanh, linear), Levenberg-Marquardt (scipy 'lm'), h1 from 8 to 12, h2 = h1 - 1 (Fig. 6).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pywt
from scipy.optimize import least_squares

from . import common as C

F0 = 50.0
FS = float(C.FS_HR)
HIST = int(2 * FS / F0 / 2)        # two cycles of decimated coefficients (400)
QUARTER = int(FS / F0 / 4 / 2)     # quarter cycle of decimated coefficients (50)
FACTOR = 5.0
T_ARM = 0.12
MAX_DET = 20


# ---------------------------------------------------------------------------------------------------------------- signals
def prepare(tr: dict, plant: str = "A") -> dict:
    hv, lv = C.plant_pu(tr["Ip"].astype(np.float64), tr["Is"].astype(np.float64), plant)
    d = lv - hv
    x = np.concatenate([d, d.mean(1, keepdims=True)], 1)                     # A, B, C, zero sequence
    c2 = np.stack([pywt.dwt(x[:, k], "db4", mode="symmetric")[1] ** 2 for k in range(4)]).astype(np.float32)
    return {"c2": c2}


def detections(c2: np.ndarray, t_arm: float = T_ARM) -> np.ndarray:
    """Coefficient indices at which any channel's squared scale-1 coefficient reaches FACTOR x the largest of the previous two cycles (refractory: a quarter cycle)."""
    n = c2.shape[1]
    hit = np.zeros(n, bool)
    for k in range(4):
        h = np.full(n, np.inf)
        h[HIST:] = pd.Series(c2[k]).rolling(HIST).max().shift(1).to_numpy()[HIST:]      # largest of the previous two cycles
        hit |= (c2[k] >= FACTOR * h) & (c2[k] > 1e-12)
    hit[:int(t_arm * FS / 2)] = False
    idx, last = [], -10 ** 9
    for i in np.nonzero(hit)[0]:
        if i - last >= QUARTER:
            idx.append(int(i)); last = int(i)
        if len(idx) >= MAX_DET or i + QUARTER >= n:
            break
    return np.array(idx, dtype=int)


def cached_detections(proc: dict) -> np.ndarray:
    if "det" not in proc:
        proc["det"] = detections(proc["c2"])
    return proc["det"]


def features(c2: np.ndarray, td: int) -> np.ndarray:
    return np.log10(c2[:, td:td + QUARTER].max(1).astype(np.float64) + 1e-12)


def target(meta: dict, t_det: float) -> np.ndarray:
    """8-bit pattern A1 B1 C1 G1 | A2 B2 C2 G2 of the internal fault the detection belongs to (HV side = scenario names InternalHV_*), zeros otherwise."""
    y = np.zeros(8)
    for t, c in C.events(meta):
        if c == "IF" and -0.001 <= t_det - t <= 1.0 / F0:
            ft = str(meta.get("faultType", ""))
            off = 0 if meta["scenarioName"].startswith("InternalHV") else 4
            for j, ph in enumerate("ABC"):
                y[off + j] = float(ph in ft)
            y[off + 3] = float("G" in ft or ft in ("ABCG",))
    return y


# ---------------------------------------------------------------------------------------------------------------- network
def _unpack(p: np.ndarray, h1: int, h2: int):
    i = 0
    W1 = p[i:i + 4 * h1].reshape(4, h1); i += 4 * h1
    b1 = p[i:i + h1]; i += h1
    W2 = p[i:i + h1 * h2].reshape(h1, h2); i += h1 * h2
    b2 = p[i:i + h2]; i += h2
    W3 = p[i:i + h2 * 8].reshape(h2, 8); i += h2 * 8
    return W1, b1, W2, b2, W3, p[i:i + 8]


def forward(p: np.ndarray, X: np.ndarray, h1: int, h2: int) -> np.ndarray:
    W1, b1, W2, b2, W3, b3 = _unpack(p, h1, h2)
    return np.tanh(np.tanh(X @ W1 + b1) @ W2 + b2) @ W3 + b3


def mape_nonzero(o: np.ndarray, y: np.ndarray) -> float:
    m = y != 0
    return float(np.mean(np.abs(o[m] - y[m]) / np.abs(y[m])) * 100) if m.any() else float(np.mean(np.abs(o)) * 100)


class NgaopitakkulMethod:
    """Native mode: trip at the first detection whose network output exceeds 0.5 in any of the eight bits (decision available a quarter cycle after the detection)."""

    def __init__(self, plant: str = "A", max_nfev: int = 150, threshold: float = 0.5, seed: int = 0):
        self.plant, self.max_nfev, self.threshold, self.seed = plant, max_nfev, threshold, seed
        self.lo = self.hi = None
        self.p = None
        self.h = (8, 7)
        self.log: list[dict] = []

    def prepare(self, tr: dict) -> dict:
        return prepare(tr, self.plant)

    def _examples(self, items: list[dict]):
        X, Y = [], []
        for it in items:
            c2 = it["proc"]["c2"]
            for td in cached_detections(it["proc"])[:8]:
                X.append(features(c2, int(td))); Y.append(target(it["meta"], 2.0 * td / FS))
        return np.array(X), np.array(Y)

    def fit(self, train: list[dict], val: list[dict], seed: int):
        Xtr, Ytr = self._examples(train)
        Xva, Yva = self._examples(val)
        self.lo, self.hi = Xtr.min(0), Xtr.max(0)
        nz = lambda X: (X - self.lo) / np.maximum(self.hi - self.lo, 1e-9)       # noqa: E731
        Xtr, Xva = nz(Xtr), nz(Xva)
        rng = np.random.RandomState(seed)
        best = None
        for h1 in range(8, 13):                                                  # Fig. 6: sizes increased by one up to z_st = 12 or MAPE < 0.5 %
            h2 = h1 - 1
            n = 4 * h1 + h1 + h1 * h2 + h2 + h2 * 8 + 8
            p0 = rng.randn(n) * 0.3
            r = least_squares(lambda p: (forward(p, Xtr, h1, h2) - Ytr).ravel(), p0, method="lm", max_nfev=self.max_nfev)
            mape = mape_nonzero(forward(r.x, Xva, h1, h2), Yva)
            self.log.append({"h1": h1, "h2": h2, "val_mape": mape, "train_mse": float(np.mean(r.fun ** 2)), "nfev": int(r.nfev), "n_train": len(Xtr)})
            if best is None or mape < best[0]:
                best = (mape, r.x, (h1, h2))
            if mape < 0.5:
                break
        _, self.p, self.h = best
        return self

    def trip_time(self, proc: dict) -> float | None:
        c2 = proc["c2"]
        for td in cached_detections(proc):
            x = (features(c2, int(td)) - self.lo) / np.maximum(self.hi - self.lo, 1e-9)
            if forward(self.p, x[None], *self.h).max() > self.threshold:
                return float(2.0 * (td + QUARTER) / FS)
        return None
