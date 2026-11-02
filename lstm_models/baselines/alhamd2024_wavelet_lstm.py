"""Alhamd, Saniei, Seifossadat and Mashhour 2024, Algorithms 17(9):397 - first-level RT-BSWT (db4, 8 taps) coefficients of the differential current over 20 ms
segments -> bidirectional LSTM -> event type. Implemented from documents/baselines/alhamd2024_wavelet_lstm_spec.md.

Data path: 20 kHz CT secondaries -> 3 kHz (anti-aliased, 3/20) -> plant compensation -> differential d = lv - hv (3 phases) -> RT-BSWT coefficients w(l, k) and
scaling coefficients S(l, k), l = 0 .. 7 (16 channels per phase, 48 in total, scaled by arcsinh(10 x)) -> segments of 60 samples (20 ms) -> bidirectional LSTM
(hidden / layers / dropout / lr searched once, see AlhamdMethod) -> 5 outputs (inrush, internal fault, internal fault with CT saturation, external fault, no event),
MSE against one-hot targets, class = argmax. Native trip: first segment (every 5 samples from 0.12 s) classified as internal fault (with or without CT saturation).
"""
from __future__ import annotations

import numpy as np
import pywt
import torch
import torch.nn as nn

from . import common as C

F0, FS = 50.0, 3000.0
SEG, STEP = 60, 5
_w = pywt.Wavelet("db4")
L = len(_w.dec_hi)
H = np.array(_w.dec_hi[::-1])      # high-pass analysis filter h(n)
G = np.array(_w.dec_lo[::-1])      # low-pass (scaling) filter
DK = L                              # sliding window length of the boundary transform (Δk = L, as for Simões et al.)
CLASSES = ["inrush", "internal", "internal_ctsat", "external", "noevent"]
IDX = {c: i for i, c in enumerate(CLASSES)}
T_START = 0.12


def _shift(x: np.ndarray, o: int) -> np.ndarray:
    y = np.zeros_like(x)
    if o == 0:
        return x.copy()
    y[-o:] = x[:o]
    return y


def rtbswt_both(x: np.ndarray) -> np.ndarray:
    """Eqs. (11)-(12): w(l,k) with the high-pass and S(l,k) with the low-pass filter, l = 0 .. L-1, for x [N] -> [N, 2L]."""
    N = len(x)
    out = np.zeros((N, 2 * L))
    for l in range(L):
        w = np.zeros(N); s = np.zeros(N)
        for n in range(L):
            o = -L + n + 1 + l
            if o > 0:
                o -= DK
            xs = _shift(x, o)
            w += H[n] * xs; s += G[n] * xs
        out[:, l], out[:, L + l] = w / np.sqrt(2.0), s / np.sqrt(2.0)
    out[:L - 1] = 0.0
    return out


def prepare(tr: dict, plant: str = "A") -> dict:
    hv, lv = C.plant_pu(tr["Ip"].astype(np.float64), tr["Is"].astype(np.float64), plant)
    hv, lv = C.resample(hv, FS), C.resample(lv, FS)
    d = lv - hv
    X = np.concatenate([rtbswt_both(d[:, p]) for p in range(3)], 1)
    return {"X": np.arcsinh(10.0 * X).astype(np.float16)}      # [N, 48]


def segment_label(meta: dict, t_start: float, t_end: float) -> str | None:
    """Class of a segment [t_start, t_end] by the events of the trace, None for segments that mix two states (left out of training)."""
    evs = sorted(C.events(meta))
    if not evs or t_end < evs[0][0]:
        return "noevent"
    last = None
    for t, c in evs:
        if t_start >= t:
            last = (t, c)
    if last is None:
        return None
    c = last[1]
    if c == "IF":
        return "internal_ctsat" if meta["scenarioName"].startswith("Stress_CTSat_Int") else "internal"
    return {"EF": "external", "EN": "inrush"}[c]


class BiLSTM(nn.Module):
    def __init__(self, hidden: int = 64, layers: int = 1, dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(48, hidden, layers, batch_first=True, bidirectional=True, dropout=dropout if layers > 1 else 0.0)
        self.drop = nn.Dropout(dropout)
        self.out = nn.Linear(2 * hidden, len(CLASSES))

    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.out(self.drop(torch.cat([h[-2], h[-1]], 1)))


GRID = dict(hidden=(32, 64, 128), layers=(1, 2), dropout=(0.1, 0.2, 0.3), lr=(3e-3, 1e-2, 3e-2))


class AlhamdMethod:
    """SGDM (momentum 0.9), learning rate dropped by 10 after half of the epochs, early stopping on validation loss. The 12-configuration random search
    (spec section 4) is run ONCE (first fold of the first seed, on its validation traces) and the chosen configuration is trained on every fold: the 200-epoch
    schedule of the paper makes a per-fold search days long (deviation recorded). Budget actually used: 6 windows per trace, search 8 epochs, final training 25 epochs
    (early stopping on validation loss, patience 5; LR dropped by 10 after half of the epochs) instead of 200: stated as a deviation, it is the same epoch limit as the Part 1 models."""
    FROZEN: dict | None = None

    def __init__(self, plant: str = "A", per_trace: int = 6, epochs: int = 25, patience: int = 5, search_epochs: int = 8, n_configs: int = 12, seed: int = 0):
        self.plant, self.per_trace, self.epochs, self.patience, self.search_epochs, self.n_configs, self.seed = plant, per_trace, epochs, patience, search_epochs, n_configs, seed
        self.model: BiLSTM | None = None
        self.cfg: dict | None = None
        self.log: list[dict] = []

    def prepare(self, tr: dict) -> dict:
        return prepare(tr, self.plant)

    def _windows(self, items: list[dict], rng: np.random.RandomState):
        Xs, ys = [], []
        for it in items:
            X = it["proc"]["X"]
            n = len(X)
            t_ev = [t for t, _ in C.events(it["meta"])]
            cand = []
            for t in t_ev:                                           # windows starting at / after each event (up to 3 cycles after the event)
                s0 = int(t * FS)
                cand += list(range(s0 + SEG - 1, min(s0 + SEG - 1 + 3 * int(FS / F0), n - 1), STEP))
            cand += list(rng.randint(int(T_START * FS) + SEG, n - 1, 8))
            rng.shuffle(cand)
            kept = 0
            for e in cand:
                lab = segment_label(it["meta"], (e - SEG + 1) / FS, e / FS)
                if lab is None:
                    continue
                Xs.append(X[e - SEG + 1:e + 1]); ys.append(IDX[lab]); kept += 1
                if kept >= self.per_trace:
                    break
        return np.array(Xs, dtype=np.float32), np.array(ys)

    def _train(self, cfg: dict, Xtr, ytr, Xva, yva, epochs: int, patience: int, seed: int):
        torch.manual_seed(seed)
        m = BiLSTM(cfg["hidden"], cfg["layers"], cfg["dropout"])
        opt = torch.optim.SGD(m.parameters(), lr=cfg["lr"], momentum=0.9)
        sched = torch.optim.lr_scheduler.MultiStepLR(opt, [epochs // 2], 0.1)
        xt, yt = torch.from_numpy(Xtr), torch.eye(len(CLASSES))[torch.from_numpy(ytr)]
        xv, yv = torch.from_numpy(Xva), torch.eye(len(CLASSES))[torch.from_numpy(yva)]
        best, state, stale, ep = 1e9, None, 0, 0
        for ep in range(1, epochs + 1):
            m.train()
            perm = torch.randperm(len(xt))
            for b in range(0, len(perm), 256):
                i = perm[b:b + 256]
                opt.zero_grad(set_to_none=True)
                loss = ((m(xt[i]) - yt[i]) ** 2).mean()
                loss.backward()
                nn.utils.clip_grad_norm_(m.parameters(), 1.0)
                opt.step()
            sched.step()
            m.eval()
            with torch.no_grad():
                vl = float(((m(xv) - yv) ** 2).mean())
            if vl < best - 1e-5:
                best, state, stale = vl, {k: v.clone() for k, v in m.state_dict().items()}, 0
            else:
                stale += 1
                if stale >= patience:
                    break
        m.load_state_dict(state)
        return m, best, ep

    def fit(self, train: list[dict], val: list[dict], seed: int):
        rng = np.random.RandomState(seed)
        Xtr, ytr = self._windows(train, rng)
        Xva, yva = self._windows(val, rng)
        if AlhamdMethod.FROZEN is None:
            cr = np.random.RandomState(20261101)
            configs = [{k: v[cr.randint(len(v))] for k, v in GRID.items()} for _ in range(self.n_configs)]
            res = []
            for cfg in configs:
                m, vl, ep = self._train(cfg, Xtr, ytr, Xva, yva, self.search_epochs, 4, seed)
                res.append({**cfg, "val_loss": vl, "epochs": ep}); self.log.append(res[-1])
            AlhamdMethod.FROZEN = {"cfg": min(res, key=lambda r: r["val_loss"]), "search": res}
        self.cfg = {k: AlhamdMethod.FROZEN["cfg"][k] for k in GRID}
        self.model, vl, ep = self._train(self.cfg, Xtr, ytr, Xva, yva, self.epochs, self.patience, seed)
        self.log.append({"final": self.cfg, "val_loss": vl, "epochs": ep, "n_train": len(Xtr)})
        return self

    def class_stream(self, proc: dict):
        X = proc["X"].astype(np.float32)
        n = len(X)
        ends = np.arange(int(T_START * FS) + SEG, n, STEP)
        W = np.lib.stride_tricks.sliding_window_view(X, SEG, axis=0)             # [n-SEG+1, 48, SEG]
        idx = ends - SEG + 1
        out = []
        self.model.eval()
        with torch.no_grad():
            for b in range(0, len(idx), 512):
                xb = torch.from_numpy(np.ascontiguousarray(W[idx[b:b + 512]].transpose(0, 2, 1)))
                out.append(self.model(xb).argmax(1).numpy())
        return ends, np.concatenate(out)

    def trip_time(self, proc: dict) -> float | None:
        ends, cls = self.class_stream(proc)
        hit = np.nonzero((cls == IDX["internal"]) | (cls == IDX["internal_ctsat"]))[0]
        return float(ends[hit[0]] / FS) if len(hit) else None
