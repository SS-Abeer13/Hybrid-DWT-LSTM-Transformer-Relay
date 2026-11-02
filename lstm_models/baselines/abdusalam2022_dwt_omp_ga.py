"""Abdusalam, Ibrahim, Anayi and Packianather 2022, Energies 15(11):3905 - DWT + OMP statistical features, bees / genetic feature selection, KNN / SVM / ANN.
Implemented from documents/baselines/abdusalam2022_dwt_omp_ga_spec.md (many steps are only named in the paper; every fill is listed there).

Data path: 20 kHz CT secondaries -> 10 kHz (anti-aliased) -> plant compensation -> differential d = lv - hv (3 phases). Decision windows: one cycle (200 samples)
every 25 samples (1/8 cycle) while the percentage-differential element of the 87T mirror is picked up (the paper's classifier has no trigger of its own).
Features per window and phase: 8 statistics of each of the 7 db7 sub-bands (6 levels + approximation; 56) and of the OMP coefficient vector over five dictionaries
(Sym4-Lev5, Wpsym4-Lev5, DCT, Sin, Cos; 40) = 96, x 3 phases = 288 candidates. Selection: bees algorithm (main) or genetic algorithm, fitness = 3-fold CV error of 3-NN.
Classes: 0 normal / inrush / over-excitation, 1 external fault, 2 internal fault; trip when the predicted class is 2.
"""
from __future__ import annotations

import numpy as np
import pywt
from scipy.fft import dct
from sklearn.linear_model import orthogonal_mp
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from . import common as C
from .afrasiabi2020_acnn import BREAK, PICKUP, SLOPE1, SLOPE2

F0, FS = 50.0, 10000.0
WIN, STEP = 200, 25
MAX_CYCLES = 3
WAVELET = "db7"
FIT_CACHE: dict = {}


# ---------------------------------------------------------------------------------------------------------------- dictionaries / features
def _wavelet_atoms(kind: str, n: int = WIN, level: int = 5, wav: str = "sym4") -> np.ndarray:
    atoms = []
    if kind == "wavedec":
        tmpl = pywt.wavedec(np.zeros(n), wav, level=level, mode="periodization")
        for b, c in enumerate(tmpl):
            for j in range(len(c)):
                cc = [np.zeros_like(x) for x in tmpl]
                cc[b][j] = 1.0
                atoms.append(pywt.waverec(cc, wav, mode="periodization")[:n])
    else:
        for node in [p for p in pywt.WaveletPacket(np.zeros(n), wav, mode="periodization", maxlevel=level).get_level(level, order="freq")]:
            m = len(node.data)
            for j in range(m):
                wp = pywt.WaveletPacket(np.zeros(n), wav, mode="periodization", maxlevel=level)
                for nd in wp.get_level(level, order="freq"):
                    nd.data = np.zeros(len(nd.data))
                wp[node.path].data = np.eye(m)[j]
                atoms.append(wp.reconstruct(update=False)[:n])
    A = np.array(atoms).T
    return A / np.maximum(np.linalg.norm(A, axis=0), 1e-12)


def _dictionaries(n: int = WIN) -> dict[str, np.ndarray]:
    t = np.arange(n)
    D = {"sym4": _wavelet_atoms("wavedec", n), "wpsym4": _wavelet_atoms("wp", n),
         "dct": dct(np.eye(n), norm="ortho", axis=0)}
    D["sin"] = np.stack([np.sin(np.pi * (k + 1) * (t + 0.5) / n) for k in range(n)], 1)
    D["cos"] = np.stack([np.cos(np.pi * k * (t + 0.5) / n) for k in range(n)], 1)
    for k in ("sin", "cos"):
        D[k] = D[k] / np.maximum(np.linalg.norm(D[k], axis=0), 1e-12)
    return D


_DICT: dict[str, np.ndarray] | None = None


def stats8(v: np.ndarray) -> np.ndarray:
    """Eqs. (2)-(9): mean, median, standard deviation, median absolute deviation, mean absolute deviation, L1, L2 and maximum norm."""
    v = np.asarray(v, float)
    m = v.mean()
    return np.array([m, np.median(v), v.std(), np.median(np.abs(v - np.median(v))), np.mean(np.abs(v - m)), np.abs(v).sum(), np.sqrt((v ** 2).sum()), np.abs(v).max()])


def window_features(x: np.ndarray) -> np.ndarray:
    """x: [WIN, 3] differential window (pu) -> 288 features (3 phases x (56 DWT statistics + 40 OMP statistics))."""
    global _DICT
    if _DICT is None:
        _DICT = _dictionaries()
    out = []
    for p in range(3):
        s = x[:, p].astype(np.float64)
        sc = float(np.abs(s).max())
        sn = s / sc if sc > 1e-9 else s
        out += [stats8(b) for b in pywt.wavedec(s, WAVELET, level=6, mode="symmetric")]
        for name in ("sym4", "wpsym4", "dct", "sin", "cos"):
            c = orthogonal_mp(_DICT[name], sn, n_nonzero_coefs=100, tol=(1e-4 * np.linalg.norm(sn)) ** 2) if sc > 1e-9 else np.zeros(_DICT[name].shape[1])
            out.append(stats8(c))
    return np.concatenate(out)


# ---------------------------------------------------------------------------------------------------------------- signals
def prepare(tr: dict, plant: str = "A") -> dict:
    hv, lv = C.plant_pu(tr["Ip"].astype(np.float64), tr["Is"].astype(np.float64), plant)
    hv, lv = C.resample(hv, FS), C.resample(lv, FS)

    def srms(x):
        c = np.concatenate([np.zeros((1, x.shape[1])), np.cumsum(x ** 2, 0)], 0)
        o = np.full(x.shape, np.nan)
        o[WIN - 1:] = np.sqrt((c[WIN:] - c[:-WIN]) / WIN)
        return o
    idr, irr = srms(lv - hv), srms(0.5 * (np.abs(hv) + np.abs(lv)))
    dyn = np.where(irr <= BREAK, SLOPE1 * irr, SLOPE2 * (irr - BREAK) + SLOPE1 * BREAK)
    with np.errstate(invalid="ignore"):
        picked = np.nan_to_num(((idr > PICKUP) & (idr > dyn)).any(1)).astype(bool)
    return {"d": (lv - hv).astype(np.float32), "picked": picked, "fc": {}}


def decision_ends(proc: dict, t_start: float = 0.12) -> np.ndarray:
    p, n = proc["picked"], len(proc["picked"])
    k0 = np.nonzero(p[int(t_start * FS):])[0]
    if len(k0) == 0:
        return np.array([], dtype=int)
    first = int(t_start * FS) + int(k0[0])
    ends = np.arange(first, min(n, first + MAX_CYCLES * WIN), STEP)
    return ends[p[ends]]


def feats(proc: dict, end: int) -> np.ndarray:
    fc = proc["fc"]
    if end not in fc:
        fc[end] = window_features(proc["d"][end - WIN + 1:end + 1]).astype(np.float32)
    return fc[end]


def label_windows(meta: dict, proc: dict, rng: np.random.RandomState, cap: int = 8):
    """(ends, labels 0/1/2) of training windows: after an internal fault -> 2, after an external fault -> 1, everything else (inrush, over-excitation, normal,
    windows before the first event) -> 0."""
    cls = C.event_class(meta)
    evs = C.events(meta)
    n = len(proc["d"])
    ends = list(decision_ends(proc))
    lab = [0] * len(ends)
    for t, c in evs:
        if c in ("IF", "EF"):
            lo = int(t * FS) + WIN
            e2 = list(np.arange(lo, min(lo + 2 * WIN, n), STEP))
            ends += e2; lab += [2 if c == "IF" else 1] * len(e2)
    if cls in ("NONE", "EN"):
        ends += list(rng.randint(int(0.2 * FS), n - 1, 3)); lab += [0] * 3
    ends, lab = np.array(ends, dtype=int), np.array(lab, dtype=int)
    if len(ends) > cap:
        sel = rng.choice(len(ends), cap, replace=False)
        ends, lab = ends[sel], lab[sel]
    return ends, lab


# ---------------------------------------------------------------------------------------------------------------- feature selection (fitness: 3-fold CV error of 3-NN)
def _fitness(mask: np.ndarray, X: np.ndarray, y: np.ndarray, folds) -> float:
    if not mask.any():
        return 1.0
    clf = KNeighborsClassifier(3, algorithm="brute")
    pred = cross_val_predict(clf, X[:, mask], y, cv=folds)
    return float(np.mean(pred != y))


def genetic_algorithm(X, y, rng, pop=50, gens=50, pc=0.8, pm=0.02):
    n = X.shape[1]
    folds = StratifiedKFold(3, shuffle=True, random_state=0)
    P = rng.rand(pop, n) < 0.1
    f = np.array([_fitness(m, X, y, folds) for m in P])
    for _ in range(gens):
        new = [P[np.argmin(f)].copy()]                                  # elitism
        while len(new) < pop:
            i = min(rng.randint(0, pop, 2), key=lambda k: f[k]); j = min(rng.randint(0, pop, 2), key=lambda k: f[k])
            a, b = P[i].copy(), P[j].copy()
            if rng.rand() < pc:
                cut = rng.randint(1, n); a[cut:], b[cut:] = P[j][cut:], P[i][cut:]
            for c in (a, b):
                c ^= rng.rand(n) < pm
                new.append(c)
        P = np.array(new[:pop])
        f = np.array([_fitness(m, X, y, folds) for m in P])
    return P[np.argmin(f)], float(f.min())


def bees_algorithm(X, y, rng, scouts=50, sites=5, elite=2, n_elite=20, n_other=10, iters=20, flips=3):
    n = X.shape[1]
    folds = StratifiedKFold(3, shuffle=True, random_state=0)
    P = rng.rand(scouts, n) < 0.1
    f = np.array([_fitness(m, X, y, folds) for m in P])
    for _ in range(iters):
        order = np.argsort(f)
        newP, newf = [], []
        for r, i in enumerate(order[:sites]):
            best_m, best_f = P[i], f[i]
            for _k in range(n_elite if r < elite else n_other):
                m = P[i].copy()
                m[rng.choice(n, flips, replace=False)] ^= True
                fm = _fitness(m, X, y, folds)
                if fm < best_f:
                    best_m, best_f = m, fm
            newP.append(best_m); newf.append(best_f)
        rest = rng.rand(scouts - sites, n) < 0.1                         # random scouts
        newP += list(rest); newf += [_fitness(m, X, y, folds) for m in rest]
        P, f = np.array(newP), np.array(newf)
    return P[np.argmin(f)], float(f.min())


# ---------------------------------------------------------------------------------------------------------------- method
class AbdusalamMethod:
    """selector 'BA' (main row, Table 2b) or 'GA'; classifier 'SVM' (RBF, C = 20, gamma = 1 / n_features), 'KNN' (K = 1) or 'ANN' (20 tanh units).
    The fit of a (seed, fold) is shared between the variants of one process (FIT_CACHE)."""

    def __init__(self, selector: str = "BA", clf: str = "SVM", plant: str = "A", seed: int = 0, n_select: int = 1500):
        self.selector, self.clf_name, self.plant, self.seed, self.n_select = selector, clf, plant, seed, n_select
        self.scaler = self.mask = self.clf = None

    def prepare(self, tr: dict) -> dict:
        return prepare(tr, self.plant)

    def _make_clf(self, nf: int):
        return {"SVM": lambda: SVC(C=20.0, kernel="rbf", gamma=1.0 / nf), "KNN": lambda: KNeighborsClassifier(1),
                "ANN": lambda: MLPClassifier((20,), activation="tanh", early_stopping=True, validation_fraction=0.15, max_iter=500, random_state=self.seed)}[self.clf_name]()

    def fit(self, train: list[dict], val: list[dict], seed: int):
        key = (seed, self.selector, self.n_select, len(train))
        if key not in FIT_CACHE:
            rng = np.random.RandomState(seed)
            X, y = [], []
            for it in train:
                ends, lab = label_windows(it["meta"], it["proc"], np.random.RandomState(it["id"]))
                for e, l in zip(ends, lab):
                    X.append(feats(it["proc"], int(e))); y.append(l)
            X, y = np.array(X, np.float64), np.array(y)
            sc = StandardScaler().fit(X)
            Xs = np.nan_to_num(sc.transform(X))
            sub = rng.choice(len(Xs), min(self.n_select, len(Xs)), replace=False)
            sel = (bees_algorithm if self.selector == "BA" else genetic_algorithm)(Xs[sub], y[sub], rng)
            FIT_CACHE[key] = (sc, sel[0], Xs, y, sel[1])
        sc, mask, Xs, y, err = FIT_CACHE[key]
        self.scaler, self.mask, self.sel_err = sc, mask, err
        self.clf = self._make_clf(int(mask.sum())).fit(Xs[:, mask], y)
        return self

    def predict_window(self, proc: dict, end: int) -> int:
        x = np.nan_to_num(self.scaler.transform(feats(proc, end)[None].astype(np.float64)))
        return int(self.clf.predict(x[:, self.mask])[0])

    def trip_time(self, proc: dict) -> float | None:
        for e in decision_ends(proc):
            if self.predict_window(proc, int(e)) == 2:
                return float(e / FS)
        return None

    STEP_S, EVENT_BASED = STEP / FS, False

    def score_stream(self, proc: dict):
        """Sigmoid of the SVM one-versus-rest decision value of the internal-fault class (BA/GA + SVM variants)."""
        ends = decision_ends(proc)
        if len(ends) == 0:
            return ends / FS, np.zeros(0)
        X = np.nan_to_num(self.scaler.transform(np.array([feats(proc, int(e)) for e in ends], np.float64)))[:, self.mask]
        dfun = self.clf.decision_function(X)
        col = list(self.clf.classes_).index(2)
        return ends / FS, 1.0 / (1.0 + np.exp(-dfun[:, col]))


def trace_windows(meta: dict, proc: dict, tid: int) -> list[int]:
    """Every window end that any fold can ask for: the training windows of the trace (deterministic per trace id) and the native decision windows."""
    ends, _ = label_windows(meta, proc, np.random.RandomState(tid))
    return sorted(set(int(e) for e in ends) | set(int(e) for e in decision_ends(proc)))


def compute_trace_features(args):
    """Worker for tools/cache_abdusalam_feats.py: (tid, meta, d, picked) -> (tid, {end: features})."""
    import warnings
    warnings.simplefilter("ignore")
    tid, meta, d, picked = args
    proc = {"d": d, "picked": picked, "fc": {}}
    for e in trace_windows(meta, proc, tid):
        feats(proc, e)
    return tid, proc["fc"]


def compute_decision_features(args):
    """Worker (external evaluation sets): (tid, meta, d, picked) -> (tid, {end: features}) for the native decision windows only."""
    import warnings
    warnings.simplefilter("ignore")
    tid, meta, d, picked = args
    proc = {"d": d, "picked": picked, "fc": {}}
    for e in decision_ends(proc):
        feats(proc, int(e))
    return tid, proc["fc"]
