"""Simoes et al. 2021, EPSR 197:107297 - RT-BSWT energies, adaptive-threshold disturbance detector, SVM 1 (EF / IF / EN) and SVM 2
(half-cycle window, external vs evolving external-to-internal). Implemented from documents/baselines/simoes2021_rtbswt_svm_spec.md (every
choice that the paper leaves open is listed there). Equation numbers are the paper's.

Data path: 20 kHz CT-secondary currents of one trace -> anti-aliased resampling to 256 samples per cycle (12,800 Hz at 50 Hz) -> plant
compensation -> RT-BSWT of the operating (H + X) and restraining (H - X) currents of phases A, B, C and the negative sequence Q -> energies.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pywt
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC, LinearSVC

from . import common as C

F0 = 50.0
SPC = 256                       # samples per cycle (paper: 256 at 60 Hz = 15,360 Hz)
FS = SPC * F0                   # 12,800 Hz
H = np.array(pywt.Wavelet("db2").dec_hi, dtype=float)       # 4-tap Daubechies filter ("db(4)" = four coefficients, spec section 3)
L = len(H)
DK = L                          # sliding-window length Δk >= L (spec: Δk = L)
WIN_THR = 2 * SPC               # two cycles for the adaptive threshold (Eq. 12)
THR_FACTOR = 3.0                # Eq. (12)
N_POST = 4                      # post-disturbance energy samples of SVM 1 (32 features)
HALF = SPC // 2                 # SVM 2: half-cycle window = 128 samples
STEP2 = SPC // 8                # SVM 2: step of 1/8 cycle = 32 samples
SIGNALS = [f"{p}{k}" for p in ("A", "B", "C", "Q") for k in ("op", "res")]     # 8 energy signals


# ---------------------------------------------------------------------------------------------------------------- RT-BSWT
def _shifted(x: np.ndarray, o: int) -> np.ndarray:
    """y[k] = x[k + o] with zeros outside the record (o <= 0 only here)."""
    y = np.zeros_like(x)
    if o == 0:
        return x.copy()
    y[-o:] = x[:o]
    return y


def rtbswt(x: np.ndarray) -> np.ndarray:
    """First-level wavelet coefficients w(l, k), l = 0 .. L-1 (Eq. 4), for a signal x [N]: returns [N, L].
    w(l,k) = 1/sqrt2 * sum_n h(n) i(k - L + n + 1 + l); samples beyond k come from the periodised window: i(k+m) = i(k - Δk + m)."""
    N = len(x)
    W = np.zeros((N, L))
    for l in range(L):
        acc = np.zeros(N)
        for n in range(L):
            o = -L + n + 1 + l
            if o > 0:
                o -= DK
            acc += H[n] * _shifted(x, o)
        W[:, l] = acc / np.sqrt(2.0)
    W[: L - 1, :] = 0.0                 # the first samples have no complete window
    return W


def energy(w_diff: np.ndarray) -> np.ndarray:
    """Differential energy (Eqs. 8-10) from the differential coefficients [N, L]: E_a = sum_{l>=1} w^2, E_b = sum_{n=k-Δk+L}^{k} w^2(0,n)."""
    Ea = (w_diff[:, 1:] ** 2).sum(axis=1)
    sq0 = w_diff[:, 0] ** 2
    nb = DK - L + 1
    cs = np.concatenate([[0.0], np.cumsum(sq0)])
    Eb = cs[1:] - cs[np.maximum(np.arange(1, len(sq0) + 1) - nb, 0)]
    return Ea + Eb


def negative_sequence(i3: np.ndarray) -> np.ndarray:
    """Eqs. (2)-(3): iQ(k) = 1/3 [iA(k) + iB(k - fs/(3f)) + iC(k - 2fs/(3f))]; the delays 85.33 and 170.67 samples are rounded to 85 and 171."""
    d1, d2 = int(round(FS / (3 * F0))), int(round(2 * FS / (3 * F0)))
    return (i3[:, 0] + _shifted(i3[:, 1], -d1) + _shifted(i3[:, 2], -d2)) / 3.0


def energies(Ip: np.ndarray, Is: np.ndarray, plant: str = "A") -> np.ndarray:
    """20 kHz secondary currents of both sides -> the eight differential energy series [8, N] at 12,800 Hz in the order of SIGNALS."""
    hv, lv = C.plant_pu(Ip, Is, plant)
    iH, iX = C.resample(hv, FS), -C.resample(lv, FS)          # X current taken as the one leaving the transformer: op = iH + iX is small in normal operation
    chans_H = [iH[:, 0], iH[:, 1], iH[:, 2], negative_sequence(iH)]
    chans_X = [iX[:, 0], iX[:, 1], iX[:, 2], negative_sequence(iX)]
    out = []
    for xh, xx in zip(chans_H, chans_X):
        wH, wX = rtbswt(xh), rtbswt(xx)
        w_op = wH + wX
        w_op[:, 0] = 0.5 * (wH[:, 0] + wX[:, 0])             # Eq. (5)
        w_res = wH - wX                                       # Eq. (7)
        out += [energy(w_op), energy(w_res)]
    return np.array(out)


# ---------------------------------------------------------------------------------------------------------------- detector
def detect(E: np.ndarray, factor: float = THR_FACTOR, floor: float = 0.0, t_arm: float = 0.12) -> np.ndarray:
    """Disturbance detector (Eqs. 11-12). Returns the sample indices k_d at which any of the eight energies crosses its adaptive threshold
    E_th(k) = factor x mean of the previous two cycles. factor = 3 and floor = 0 are the published detector (it fires about 1,700 times per
    trace on our noise level, see spec section 3); factor/floor are the two settings chosen on the training folds. The detector is armed from
    t_arm = 0.12 s (the first 0.1 s of a simulation holds the start-up transient)."""
    n = E.shape[1]
    cs = np.concatenate([np.zeros((E.shape[0], 1)), np.cumsum(E, axis=1)], axis=1)
    k = np.arange(max(WIN_THR, int(t_arm * FS)), n)
    mean = (cs[:, k] - cs[:, k - WIN_THR]) / WIN_THR           # mean of E[k-2 cycles .. k-1]
    th = np.maximum(factor * mean, floor)
    cross = (E[:, k - 1] <= th) & (E[:, k] > th)
    return k[cross.any(axis=0)]


def svm1_features(E: np.ndarray, kd: np.ndarray) -> np.ndarray:
    """32 features of each detection: energies of the eight signals at k_d ... k_d + 3."""
    ok = kd + N_POST - 1 < E.shape[1]
    kd = kd[ok]
    F = np.stack([E[:, kd + j] for j in range(N_POST)], axis=0)       # [4, 8, n]
    return F.transpose(2, 0, 1).reshape(len(kd), N_POST * 8), ok


def svm2_windows(E: np.ndarray, kd: int) -> np.ndarray:
    """768-feature half-cycle windows of the operating and restraining energies of A, B, C (no Q), starting half a cycle after k_d, sliding by
    1/8 cycle until two cycles after k_d (8 windows)."""
    idx = [i for i, s in enumerate(SIGNALS) if not s.startswith("Q")]
    out = []
    for s in range(kd + HALF, kd + 2 * SPC - HALF + 1, STEP2):
        if s + HALF <= E.shape[1]:
            out.append(E[idx, s:s + HALF].reshape(-1))
    return np.array(out)


# ---------------------------------------------------------------------------------------------------------------- labels of detector firings
def label_events(meta: dict, kd: np.ndarray, tol_s: float = 1.0 / F0) -> list[str | None]:
    """Class of each detector firing from the known disturbances of the trace (common.events): the nearest event at or before the firing and
    not more than `tol_s` (one cycle) earlier; firings that match no known event (noise, breaker or transient echoes) get None."""
    ev = C.events(meta)
    out: list[str | None] = []
    for k in kd:
        t = k / FS
        best, bd = None, tol_s
        for te, c in ev:
            d = t - te
            if -0.002 <= d <= bd:        # allow 2 ms for the resampling filter's look-ahead
                best, bd = c, d
        out.append(best)
    return out


# ---------------------------------------------------------------------------------------------------------------- model
class Simoes2021:
    """SVM 1 (RBF, one-versus-all, min-max scaling) and SVM 2 (linear). Hyperparameters of the paper: C = 500, gamma = 100 (SVM 1)."""

    def __init__(self, C1: float = 500.0, gamma1: float = 100.0, C2: float = 1.0, factor: float = THR_FACTOR, floor: float = 0.0, plant: str = "A"):
        self.C1, self.gamma1, self.C2, self.factor, self.floor, self.plant = C1, gamma1, C2, factor, floor, plant
        self.svm1 = self.svm2 = None
        self.lo1 = self.hi1 = self.lo2 = self.hi2 = None
        self.classes1 = ["EF", "IF", "EN"]

    # --- features of one trace
    def process(self, tr: dict) -> dict:
        E = energies(tr["Ip"], tr["Is"], self.plant)
        kd = detect(E, self.factor, self.floor)
        F1, ok = svm1_features(E, kd)
        kd = kd[ok]
        return {"E": E, "kd": kd, "F1": F1}

    # --- training
    def fit(self, items: list[dict]) -> "Simoes2021":
        """items: dicts with 'meta' and the output of process() under 'proc' (so that the expensive part can be cached across folds)."""
        X1, y1, X2, y2 = [], [], [], []
        for it in items:
            p, meta = it["proc"], it["meta"]
            labs = label_events(meta, p["kd"])
            for f, k, lab in zip(p["F1"], p["kd"], labs):
                if lab is not None:
                    X1.append(f); y1.append(lab)
                    if lab == "EF" and it.get("with_svm2", True):
                        w = svm2_windows(p["E"], int(k))
                        X2.extend(w); y2.extend(["EF"] * len(w))          # evolving external-to-internal events do not exist in our data
        X1 = np.array(X1); y1 = np.array(y1)
        self.lo1, self.hi1 = X1.min(0), X1.max(0)
        self.svm1 = OneVsRestClassifier(SVC(kernel="rbf", C=self.C1, gamma=self.gamma1)).fit(self._n1(X1), y1)
        self.n_train = {c: int((y1 == c).sum()) for c in self.classes1}
        if X2 and len(set(y2)) > 1:
            X2 = np.array(X2); self.lo2, self.hi2 = X2.min(0), X2.max(0)
            self.svm2 = LinearSVC(C=self.C2, max_iter=5000).fit(self._n2(X2), np.array(y2))
        else:
            self.svm2 = None          # a single class (no evolving faults in our data): SVM 2 can only report "external fault"
        return self

    def _n1(self, X):
        return (X - self.lo1) / np.maximum(self.hi1 - self.lo1, 1e-30)

    def _n2(self, X):
        return (X - self.lo2) / np.maximum(self.hi2 - self.lo2, 1e-30)

    # --- decision (native logic of Fig. 1)
    def trip_time(self, proc: dict) -> float | None:
        """Time (s) of the first trip, or None. SVM 1 IF -> trip at k_d + 3; EN -> warning; EF -> SVM 2 over the next two cycles (trip only if an evolving fault is found)."""
        if len(proc["kd"]) == 0:
            return None
        pred = self.svm1.predict(self._n1(proc["F1"]))
        for k, c in zip(proc["kd"], pred):
            if c == "IF":
                return (k + N_POST - 1) / FS
            if c == "EF" and self.svm2 is not None:
                w = svm2_windows(proc["E"], int(k))
                if len(w):
                    p2 = self.svm2.predict(self._n2(w))
                    hit = np.nonzero(p2 == "IF")[0]
                    if len(hit):
                        return (k + HALF + hit[0] * STEP2 + HALF) / FS
        return None

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)


# ---------------------------------------------------------------------------------------------------------------- harness adapter (baselines/cv.py)
FACTORS = (5.0, 10.0, 15.0, 20.0, 30.0, 50.0, 100.0)   # N2 grid (BENCHMARK_FAIRNESS_PLAN.md); the paper's factor 3 is not usable at our noise level
GRID_C1 = (10.0, 100.0, 500.0, 1000.0)
GRID_G1 = (1.0, 10.0, 100.0, 1000.0)


class SimoesMethod:
    """prepare / fit / trip_time interface. mode 'published': C = 500, gamma = 100 of the paper; mode 'grid': (C, gamma) chosen on the validation
    events from GRID_C1 x GRID_G1 (the paper's grid search, with the inner validation split instead of 10-fold CV). In both modes the detector factor
    is chosen on the VALIDATION traces by the pre-set N2 rule (select_factor) (factor 3 of the paper fires about 1,500 times per trace on our noise level)."""

    def __init__(self, mode: str = "published", plant: str = "A"):
        self.mode, self.plant = mode, plant
        self.model: Simoes2021 | None = None
        self.factor = THR_FACTOR

    def prepare(self, tr: dict) -> dict:
        return {"E": energies(tr["Ip"], tr["Is"], self.plant).astype(np.float32)}

    def _proc(self, E: np.ndarray, factor: float) -> dict:
        E = E.astype(np.float64)
        kd = detect(E, factor)
        F1, ok = svm1_features(E, kd)
        return {"E": E, "kd": kd[ok], "F1": F1}

    @staticmethod
    def select_factor(val: list[dict]) -> tuple[float, dict]:
        """N2 pre-set rule, on VALIDATION traces only: the smallest factor with <= 1 spurious firing per trace on normal / over-excitation traces AND
        >= 95 % event detection (a firing matched to the event within one cycle) on fault / inrush / external traces. If none meets both: the smallest
        meeting the spurious-firing criterion (flag 'detection_criterion_unmet'); if none meets even that: the largest factor (flag 'unusable')."""
        neutral = [it for it in val if C.event_class(it["meta"]) == "NONE"]
        ev = [it for it in val if C.event_class(it["meta"]) != "NONE" and not it["meta"].get("undetectable")]
        rep = {}
        for f in FACTORS:
            spur = float(np.mean([len(detect(it["proc"]["E"].astype(np.float64), f)) for it in neutral])) if neutral else 0.0
            hit = [any(l is not None for l in label_events(it["meta"], detect(it["proc"]["E"].astype(np.float64), f))) for it in ev]
            rep[f] = {"spurious_per_trace": spur, "detection_rate": float(np.mean(hit)) if hit else float("nan")}
        both = [f for f in FACTORS if rep[f]["spurious_per_trace"] <= 1.0 and rep[f]["detection_rate"] >= 0.95]
        spur_ok = [f for f in FACTORS if rep[f]["spurious_per_trace"] <= 1.0]
        if both:
            chosen, flag = both[0], "ok"
        elif spur_ok:
            chosen, flag = spur_ok[0], "detection_criterion_unmet"
        else:
            chosen, flag = FACTORS[-1], "unusable"
        return chosen, {"chosen": chosen, "flag": flag, "grid": rep}

    def fit(self, train: list[dict], val: list[dict], seed: int):
        self.factor, self.factor_report = self.select_factor(val)
        tr_items = [{"meta": it["meta"], "proc": self._proc(it["proc"]["E"], self.factor)} for it in train]
        if self.mode == "published":
            self.model = Simoes2021(factor=self.factor, plant=self.plant).fit(tr_items)
            return self
        va_items = [{"meta": it["meta"], "proc": self._proc(it["proc"]["E"], self.factor)} for it in val]
        Xv, yv = [], []
        for it in va_items:
            for f, lab in zip(it["proc"]["F1"], label_events(it["meta"], it["proc"]["kd"])):
                if lab is not None:
                    Xv.append(f); yv.append(lab)
        best, best_acc = None, -1.0
        for c1 in GRID_C1:
            for g1 in GRID_G1:
                m = Simoes2021(C1=c1, gamma1=g1, factor=self.factor, plant=self.plant).fit(tr_items)
                acc = float(np.mean(m.svm1.predict(m._n1(np.array(Xv))) == np.array(yv))) if Xv else 0.0
                if acc > best_acc:
                    best, best_acc = m, acc
        self.model = best
        return self

    def trip_time(self, proc: dict) -> float | None:
        return self.model.trip_time(self._proc(proc["E"], self.factor))
