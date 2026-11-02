"""Afrasiabi et al. 2020, IEEE TII 16(2):865-876 - CNN on the normalised half-cycle differential currents (network of Fig. 1), triggered by a
percentage-differential element. Implemented from documents/baselines/afrasiabi2020_acnn_spec.md. Not implemented (and said so in the spec):
the product quantisation of the layers (affects speed only). The CT-saturation compensation of Hajipour et al. 2015 is
implemented (hajipour2015_ct_comp.py, spec hajipour2015_ct_comp_spec.md) and is the first stage (`compensate=True`); `compensate=False` is the ablation.

Data path: 20 kHz CT secondaries -> 5,600 Hz (112 samples per cycle at 50 Hz) -> plant compensation -> differential d = lv - hv (per unit).
Input of the CNN: 56 samples (half cycle) of the three phases, normalised by the maximum absolute value of the window (Eq. 2), arranged as 3 x 7 x 8.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score

from . import common as C

F0 = 50.0
SPC = 112
FS = SPC * F0                    # 5,600 Hz
HALF = SPC // 2                  # 56 samples = one half cycle
STEP = SPC // 16                 # 7 samples = 1/16 cycle between decisions (spec: 1/8 cycle = 14 for SVM-type schemes; the CNN is cheap)
PICKUP, SLOPE1, SLOPE2, BREAK = 0.30, 0.25, 0.60, 3.0           # percentage characteristic of the 87T mirror (spec section 4)


# ---------------------------------------------------------------------------------------------------------------- signals
def percentage_pickup(hv: np.ndarray, lv: np.ndarray) -> np.ndarray:
    """Boolean [N]: the percentage differential element of Eq. (1), evaluated on one-cycle sliding RMS values of the three phases (any phase)."""
    def srms(x):
        c = np.concatenate([np.zeros((1, x.shape[1])), np.cumsum(x ** 2, axis=0)], axis=0)
        out = np.full(x.shape, np.nan)
        out[SPC - 1:] = np.sqrt((c[SPC:] - c[:-SPC]) / SPC)
        return out
    idr, irr = srms(lv - hv), srms(0.5 * (np.abs(hv) + np.abs(lv)))
    dyn = np.where(irr <= BREAK, SLOPE1 * irr, SLOPE2 * (irr - BREAK) + SLOPE1 * BREAK)
    with np.errstate(invalid="ignore"):
        return np.nan_to_num(((idr > PICKUP) & (idr > dyn)).any(axis=1)).astype(bool)


def window(d: np.ndarray, end: int) -> np.ndarray:
    """Half-cycle window ending at sample `end` (inclusive): [3, 56] normalised by the maximum absolute value over the three phases (Eq. 2)."""
    w = d[end - HALF + 1:end + 1].T
    return w / max(float(np.abs(w).max()), 1e-9)


def prepare(tr: dict, plant: str = "A", compensate: bool = True) -> dict:
    ip, is_ = tr["Ip"].astype(np.float64), tr["Is"].astype(np.float64)
    if compensate:      # Hajipour et al.: at 4 kHz (80 samples/cycle) with the NOMINAL burden, then on to the CNN rate
        from . import hajipour2015_ct_comp as H
        cp = H.ct_params(plant, 1.0)
        ip, is_ = (C.resample(H.compensate(C.resample(a, H.FS_COMP), H.FS_COMP, cp), C.FS_HR, H.FS_COMP) for a in (ip, is_))
        n = min(len(ip), len(tr["Ip"])); ip, is_ = ip[:n], is_[:n]
    hv, lv = C.plant_pu(ip, is_, plant)
    hv, lv = C.resample(hv, FS), C.resample(lv, FS)
    return {"d": (lv - hv).astype(np.float32), "picked": percentage_pickup(hv, lv)}


# ---------------------------------------------------------------------------------------------------------------- network (Fig. 1)
class ACNN(nn.Module):
    """Input [B, 3, 7, 8]; conv 3 x 3 (128 filters, zero padding, stride 1) + batch norm + ReLU; max pool 2 x 2; flatten; FC 128 + ReLU; output logit."""

    def __init__(self, filters: int = 128, fc: int = 128, dropout: float = 0.0):
        super().__init__()
        self.conv = nn.Sequential(nn.Conv2d(3, filters, 3, padding=1), nn.BatchNorm2d(filters), nn.ReLU(), nn.MaxPool2d(2))
        self.fc = nn.Sequential(nn.Flatten(), nn.Linear(filters * 3 * 4, fc), nn.ReLU(), nn.Dropout(dropout), nn.Linear(fc, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(self.conv(x.reshape(-1, 3, 7, 8))).view(-1)


# ---------------------------------------------------------------------------------------------------------------- training windows
def decision_ends(proc: dict, t_start: float = 0.12) -> np.ndarray:
    """Window end samples at which the relay evaluates the CNN (native logic): from half a cycle after the first pickup, every STEP samples, while
    the percentage element is picked up. Before t_start (simulation start-up) nothing is evaluated."""
    p, n = proc["picked"], len(proc["picked"])
    k0 = np.nonzero(p[int(t_start * FS):])[0]
    if len(k0) == 0:
        return np.array([], dtype=int)
    first = int(t_start * FS) + int(k0[0]) + HALF - 1
    ends = np.arange(first, n, STEP)
    return ends[p[ends]]


def training_windows(items: list[dict], rng: np.random.RandomState, per_trace_cap: int = 40, n_neutral: int = 6) -> tuple[np.ndarray, np.ndarray]:
    """Windows and labels (1 = internal fault, 0 = everything else; spec section 4). Faults: windows lying entirely after the fault onset (ends from
    onset + half cycle), also for faults the percentage element never picks up (they are positives for the dwell/threshold mode only);
    windows overlapping the onset are left out. Non-fault traces: the windows the native logic would evaluate, plus a few random ones."""
    X, y = [], []
    for it in items:
        meta, d = it["meta"], it["proc"]["d"]
        n = len(d)
        cls = C.event_class(meta)
        onset = meta["onset_time"]
        ends = decision_ends(it["proc"])
        if cls == "IF" and onset is not None:
            lo = int(onset * FS) + HALF
            ends = np.arange(lo, min(lo + 2 * SPC, n), STEP)
            lab = np.ones(len(ends))
            # early windows (energisation or other event before the fault) of fault-in-inrush traces are negatives
            pre = decision_ends(it["proc"])
            pre = pre[pre < int(onset * FS)]
            ends = np.concatenate([ends, pre]); lab = np.concatenate([lab, np.zeros(len(pre))])
        else:
            lab = np.zeros(len(ends))
        if len(ends) > per_trace_cap:
            sel = rng.choice(len(ends), per_trace_cap, replace=False)
            ends, lab = ends[sel], lab[sel]
        for e, l in zip(ends, lab):
            X.append(window(d, int(e))); y.append(l)
        if cls != "IF":
            for e in rng.randint(int(0.15 * FS), n - 1, n_neutral):
                X.append(window(d, int(e))); y.append(0.0)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


# ---------------------------------------------------------------------------------------------------------------- method (harness adapter)
class AcnnMethod:
    """Native mode: trip at the first evaluated window whose output exceeds 0.5. Hyperparameters: learning rate chosen from LR_GRID on the validation
    traces (validation AUC); 25 epochs at most, early stopping (patience 5), batch 256, Adam, positive-class weight."""
    LR_GRID = (3e-4, 1e-3, 3e-3)

    def __init__(self, plant: str = "A", max_epochs: int = 25, patience: int = 5, threshold: float = 0.5, compensate: bool = True):
        self.compensate = compensate
        self.plant, self.max_epochs, self.patience, self.threshold = plant, max_epochs, patience, threshold
        self.model: ACNN | None = None
        self.epochs_used: dict[float, int] = {}

    def prepare(self, tr: dict) -> dict:
        return prepare(tr, self.plant, self.compensate)

    def _fit_one(self, Xtr, ytr, Xva, yva, lr, seed):
        torch.manual_seed(seed)
        m = ACNN()
        opt = torch.optim.Adam(m.parameters(), lr=lr)
        pw = torch.tensor([(1 - ytr.mean()) / max(ytr.mean(), 1e-4)])
        loss_fn = nn.BCEWithLogitsLoss(pos_weight=pw)
        xt, yt = torch.from_numpy(Xtr), torch.from_numpy(ytr)
        best, best_state, stale, ep_used = -1.0, None, 0, 0
        for ep in range(1, self.max_epochs + 1):
            m.train()
            perm = torch.randperm(len(yt))
            for b in range(0, len(perm), 256):
                i = perm[b:b + 256]
                opt.zero_grad(set_to_none=True)
                loss_fn(m(xt[i]), yt[i]).backward()
                opt.step()
            m.eval()
            with torch.no_grad():
                pv = torch.sigmoid(m(torch.from_numpy(Xva))).numpy()
            auc = float(roc_auc_score(yva, pv)) if len(set(yva)) > 1 else 0.5
            ep_used = ep
            if auc > best + 1e-4:
                best, stale = auc, 0
                best_state = {k: v.detach().clone() for k, v in m.state_dict().items()}
            else:
                stale += 1
                if stale >= self.patience:
                    break
        m.load_state_dict(best_state)
        return m.eval(), best, ep_used

    def fit(self, train: list[dict], val: list[dict], seed: int):
        rng = np.random.RandomState(seed)
        Xtr, ytr = training_windows(train, rng)
        Xva, yva = training_windows(val, rng)
        best = None
        for lr in self.LR_GRID:
            m, auc, ep = self._fit_one(Xtr, ytr, Xva, yva, lr, seed)
            self.epochs_used[lr] = ep
            if best is None or auc > best[1]:
                best = (m, auc, lr)
        self.model, self.val_auc, self.lr = best
        return self

    @torch.no_grad()
    def window_scores(self, proc: dict, ends: np.ndarray) -> np.ndarray:
        if len(ends) == 0:
            return np.array([])
        X = np.array([window(proc["d"], int(e)) for e in ends], dtype=np.float32)
        return torch.sigmoid(self.model(torch.from_numpy(X))).numpy()

    def trip_time(self, proc: dict) -> float | None:
        ends = decision_ends(proc)
        p = self.window_scores(proc, ends)
        hit = np.nonzero(p > self.threshold)[0]
        return float(ends[hit[0]] / FS) if len(hit) else None

    STEP_S, EVENT_BASED = STEP / FS, False

    def score_stream(self, proc: dict):
        """(decision times in s, score in [0, 1]) of every window the relay evaluates (like-for-like mode, N4)."""
        ends = decision_ends(proc)
        return ends / FS, self.window_scores(proc, ends)
