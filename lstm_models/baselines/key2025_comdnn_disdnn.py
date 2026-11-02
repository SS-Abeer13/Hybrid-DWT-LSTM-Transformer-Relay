"""Key et al. 2025, IEEE Access 13:178492-178504 - Com-DNN (CT-saturation compensation) followed by Dis-DNN (stacked denoising autoencoders + softmax,
four classes). Implemented from documents/baselines/key2025_comdnn_disdnn_spec.md (amendments of 2026-11-01 listed in its section 7).

Data path: 20 kHz -> 3,200 Hz (64 samples per cycle at 50 Hz) -> raw CT secondaries (Com-DNN input) and ideal CT secondaries true / nominal ratio
(Com-DNN target). Com-DNN: window of 64 samples of ONE CT signal, normalised by its maximum absolute value, -> estimate of the undistorted window; the
last output sample is the estimate of the current sample. The estimates of the six signals are compensated like the relay mirror and subtracted to
the differential current d (per unit); the Dis-DNN sees the window of 64 samples of the three phases of d (192 inputs, fixed per-unit scale).
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import common as C

F0 = 50.0
SPC = 64
FS = SPC * F0                     # 3,200 Hz
N = SPC
T_TRANSIENT = 58                  # samples between t0 and t1 (spec section 3: 58 of 64)
D_SCALE = 4.0                     # per-unit differential current mapped to [-1, 1] (fixed scale; spec amendment)
CLASSES = {"normal": 0, "transient": 1, "inrush": 2, "internal": 3}     # Table I class numbers


# ---------------------------------------------------------------------------------------------------------------- data
def prepare(tr: dict, plant: str = "A") -> dict:
    cfg = C.plant_config(plant)
    x = np.concatenate([tr["Ip"], tr["Is"]], axis=1)                        # raw secondaries [N, 6]
    y = np.concatenate([tr["Tp"] / cfg["ct_ratio_hv"], tr["Ts"] / cfg["ct_ratio_lv"]], axis=1)    # ideal secondaries
    return {"x": C.resample(x, FS).astype(np.float32), "y": C.resample(y, FS).astype(np.float32)}


def sliding(a: np.ndarray) -> np.ndarray:
    """[T] -> [T-N+1, N] windows (ends at N-1 ...)."""
    return np.lib.stride_tricks.sliding_window_view(a, N)


# ---------------------------------------------------------------------------------------------------------------- networks
class ComDNN(nn.Module):
    """64 -> n -> 64, leaky ReLU: distorted window -> undistorted window (both normalised by the distorted window's maximum)."""

    def __init__(self, n: int = 48):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(N, n), nn.LeakyReLU(0.1), nn.Linear(n, N))

    def forward(self, x):
        return self.net(x)


class DisDNN(nn.Module):
    """Stacked denoising autoencoders 192 -> h1 -> h2 with a softmax layer on top (4 classes); the autoencoder decoders are used only in pre-training."""

    def __init__(self, h1: int = 48, h2: int = 24, n_in: int = 3 * N):
        super().__init__()
        self.enc1, self.dec1 = nn.Linear(n_in, h1), nn.Linear(h1, n_in)
        self.enc2, self.dec2 = nn.Linear(h1, h2), nn.Linear(h2, h1)
        self.out = nn.Linear(h2, 4)

    def encode(self, x):
        return F.leaky_relu(self.enc2(F.leaky_relu(self.enc1(x), 0.1)), 0.1)

    def forward(self, x):
        return self.out(self.encode(x))


def dae_loss(x_clean, x_hat, pre, rho=0.05, w_sparse=1e-3, w_decay=1e-4, weights=()):
    """Eq. (5): RMSE term + weight decay + sparsity (KL divergence between rho and the mean sigmoid of the hidden pre-activation)."""
    rmse = torch.sqrt(F.mse_loss(x_hat, x_clean) + 1e-12)
    rho_hat = torch.sigmoid(pre).mean(0).clamp(1e-4, 1 - 1e-4)
    kl = (rho * torch.log(rho / rho_hat) + (1 - rho) * torch.log((1 - rho) / (1 - rho_hat))).sum()
    return rmse + w_decay * sum((w ** 2).sum() for w in weights) + w_sparse * kl


# ---------------------------------------------------------------------------------------------------------------- windows and labels
def com_windows(items: list[dict], rng: np.random.RandomState, per_trace: int = 120) -> tuple[np.ndarray, np.ndarray]:
    """Com-DNN training pairs: windows of the six signals at random positions after the start-up (extra weight on the first 150 ms after events)."""
    X, Y = [], []
    for it in items:
        x, y = it["proc"]["x"], it["proc"]["y"]
        n = len(x)
        ends = rng.randint(int(0.12 * FS) + N, n, per_trace)
        for t in C.events(it["meta"]):
            te = int(t[0] * FS)
            ends = np.concatenate([ends, te + rng.randint(2, int(0.15 * FS), 30)])
        ends = ends[(ends >= N) & (ends < n)]
        sig = rng.randint(0, 6, len(ends))
        for e, s in zip(ends, sig):
            xw, yw = x[e - N + 1:e + 1, s], y[e - N + 1:e + 1, s]
            sc = max(float(np.abs(xw).max()), 1e-6)
            X.append(xw / sc); Y.append(yw / sc)
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)


def estimate(com: ComDNN, proc: dict) -> np.ndarray:
    """Compensated secondaries [T, 6]: Com-DNN output at the last sample of the window ending at every sample (the first N-1 samples are copied)."""
    x = proc["x"]
    est = x.copy()
    with torch.no_grad():
        for s in range(6):
            W = sliding(x[:, s])
            sc = np.maximum(np.abs(W).max(axis=1, keepdims=True), 1e-6)
            out = com(torch.from_numpy((W / sc).astype(np.float32))).numpy()[:, -1:] * sc
            est[N - 1:, s] = out[:, 0]
    return est


def differential_pu(est: np.ndarray, plant: str = "A") -> np.ndarray:
    hv, lv = C.plant_pu(est[:, :3].astype(np.float64), est[:, 3:].astype(np.float64), plant)
    return (lv - hv).astype(np.float32)


def window_labels(meta: dict, ends: np.ndarray) -> np.ndarray:
    """Class of the window ending at each sample (spec section 3): before the first event normal; the first T_TRANSIENT samples of an event transient;
    afterwards inrush (EN), internal fault (IF) or normal (EF) according to the latest event."""
    ev = sorted((int(t * FS), c) for t, c in C.events(meta))
    lab = np.zeros(len(ends), dtype=np.int64)
    for i, e in enumerate(ends):
        cur = None
        for te, c in ev:
            if te <= e:
                cur = (te, c)
        if cur is None:
            continue
        te, c = cur
        lab[i] = CLASSES["transient"] if e < te + T_TRANSIENT else {"IF": CLASSES["internal"], "EN": CLASSES["inrush"], "EF": CLASSES["normal"]}[c]
    return lab


def dis_windows(d: np.ndarray, ends: np.ndarray) -> np.ndarray:
    W = np.stack([d[ends - N + 1 + j] for j in range(N)], axis=1)       # [n, N, 3]
    return np.clip(W.transpose(0, 2, 1).reshape(len(ends), 3 * N) / D_SCALE, -1.0, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------------------------------------------- method
class KeyMethod:
    """prepare / fit / trip_time. Search space (spec section 3): Com-DNN n in {32, 48, 64}; Dis-DNN h1 in {32, 48, 64}, h2 in {16, 24, 32}; learning rate
    {3e-4, 1e-3, 3e-3}; batch {128, 256}. n_configs random configurations (same budget as every method), chosen on the validation traces."""

    def __init__(self, plant: str = "A", n_configs: int = 4, epochs: int = 25, pre_epochs: int = 8, patience: int = 5, noise_snr_db: float = 30.0):
        self.plant, self.n_configs, self.epochs, self.pre_epochs, self.patience, self.snr = plant, n_configs, epochs, pre_epochs, patience, noise_snr_db
        self.com: ComDNN | None = None
        self.dis: DisDNN | None = None
        self.log: list[dict] = []

    def prepare(self, tr: dict) -> dict:
        return prepare(tr, self.plant)

    # --- Com-DNN
    def _fit_com(self, Xtr, Ytr, Xva, Yva, n, lr, bs, seed):
        torch.manual_seed(seed)
        m = ComDNN(n)
        opt = torch.optim.Adam(m.parameters(), lr=lr)
        xt, yt, xv, yv = map(torch.from_numpy, (Xtr, Ytr, Xva, Yva))
        best, state, stale, ep = 1e9, None, 0, 0
        for ep in range(1, self.epochs + 1):
            m.train()
            perm = torch.randperm(len(xt))
            for b in range(0, len(perm), bs):
                i = perm[b:b + bs]
                opt.zero_grad(set_to_none=True)
                F.mse_loss(m(xt[i]), yt[i]).backward()
                opt.step()
            m.eval()
            with torch.no_grad():
                v = float(F.mse_loss(m(xv), yv))
            if v < best - 1e-9:
                best, stale, state = v, 0, {k: t.clone() for k, t in m.state_dict().items()}
            else:
                stale += 1
                if stale >= self.patience:
                    break
        m.load_state_dict(state)
        return m.eval(), best, ep

    # --- Dis-DNN
    def _noisy(self, x):
        sig = x.pow(2).mean(1, keepdim=True).sqrt().clamp_min(1e-3)
        return x + torch.randn_like(x) * sig * 10 ** (-self.snr / 20)

    def _pretrain(self, m: DisDNN, X: torch.Tensor, lr: float, bs: int):
        for enc, dec, layer in ((m.enc1, m.dec1, 1), (m.enc2, m.dec2, 2)):
            opt = torch.optim.Adam(list(enc.parameters()) + list(dec.parameters()), lr=lr)
            for _ in range(self.pre_epochs):
                perm = torch.randperm(len(X))
                for b in range(0, len(perm), bs):
                    x = X[perm[b:b + bs]]
                    with torch.no_grad():
                        h_in = x if layer == 1 else F.leaky_relu(m.enc1(x), 0.1)       # earlier layers frozen
                    pre = enc(self._noisy(h_in))
                    hat = dec(F.leaky_relu(pre, 0.1))
                    opt.zero_grad(set_to_none=True)
                    dae_loss(h_in, hat, pre, weights=(enc.weight, dec.weight)).backward()
                    opt.step()

    def _fit_dis(self, Xtr, ytr, Xva, yva, h1, h2, lr, bs, seed):
        torch.manual_seed(seed)
        m = DisDNN(h1, h2)
        xt, yt, xv, yv = torch.from_numpy(Xtr), torch.from_numpy(ytr), torch.from_numpy(Xva), torch.from_numpy(yva)
        self._pretrain(m, xt, lr, bs)
        opt = torch.optim.Adam(m.parameters(), lr=lr, weight_decay=1e-4)
        cnt = np.bincount(ytr, minlength=4).astype(np.float32)
        w = torch.tensor(cnt.sum() / np.maximum(cnt, 1) / 4.0)
        best, state, stale, ep = -1.0, None, 0, 0
        for ep in range(1, self.epochs + 1):
            m.train()
            perm = torch.randperm(len(xt))
            for b in range(0, len(perm), bs):
                i = perm[b:b + bs]
                opt.zero_grad(set_to_none=True)
                F.cross_entropy(m(xt[i]), yt[i], weight=w).backward()
                opt.step()
            m.eval()
            with torch.no_grad():
                pred = m(xv).argmax(1).numpy()
            # balanced accuracy on the validation windows
            acc = float(np.mean([np.mean(pred[yva == c] == c) for c in range(4) if (yva == c).any()]))
            if acc > best + 1e-4:
                best, stale, state = acc, 0, {k: t.clone() for k, t in m.state_dict().items()}
            else:
                stale += 1
                if stale >= self.patience:
                    break
        m.load_state_dict(state)
        return m.eval(), best, ep

    def _dis_set(self, items, rng, per_trace=90):
        X, y = [], []
        for it in items:
            d = differential_pu(estimate(self.com, it["proc"]), self.plant)
            n = len(d)
            ends = list(rng.randint(int(0.12 * FS) + N, n, 40))
            for t, _ in C.events(it["meta"]):
                te = int(t * FS)
                ends += list(range(te - 16, te + 120, 4))
            ends = np.array([e for e in ends if N - 1 <= e < n])[:per_trace * 2]
            X.append(dis_windows(d, ends)); y.append(window_labels(it["meta"], ends))
        return np.concatenate(X), np.concatenate(y)

    def fit(self, train: list[dict], val: list[dict], seed: int):
        rng = np.random.RandomState(seed)
        Xtr, Ytr = com_windows(train, rng)
        Xva, Yva = com_windows(val, rng, per_trace=40)
        cfg_rng = np.random.RandomState(seed + 1)
        best = None
        for c in range(max(1, self.n_configs)):
            n, lr, bs = int(cfg_rng.choice((32, 48, 64))), float(cfg_rng.choice((3e-4, 1e-3, 3e-3))), int(cfg_rng.choice((128, 256)))
            m, v, ep = self._fit_com(Xtr, Ytr, Xva, Yva, n, lr, bs, seed + c)
            self.log.append({"stage": "com", "n": n, "lr": lr, "bs": bs, "val_mse": v, "epochs": ep})
            if best is None or v < best[1]:
                best = (m, v)
        self.com = best[0]
        Dtr, ltr = self._dis_set(train, rng)
        Dva, lva = self._dis_set(val, rng)
        best = None
        for c in range(max(1, self.n_configs)):
            h1, h2 = int(cfg_rng.choice((32, 48, 64))), int(cfg_rng.choice((16, 24, 32)))
            lr, bs = float(cfg_rng.choice((3e-4, 1e-3, 3e-3))), int(cfg_rng.choice((128, 256)))
            m, a, ep = self._fit_dis(Dtr, ltr, Dva, lva, h1, h2, lr, bs, seed + 100 + c)
            self.log.append({"stage": "dis", "h1": h1, "h2": h2, "lr": lr, "bs": bs, "val_bal_acc": a, "epochs": ep})
            if best is None or a > best[1]:
                best = (m, a)
        self.dis = best[0]
        return self

    # --- decision
    def class_sequence(self, proc: dict) -> tuple[np.ndarray, np.ndarray]:
        d = differential_pu(estimate(self.com, proc), self.plant)
        ends = np.arange(max(N - 1, int(0.12 * FS)), len(d))
        with torch.no_grad():
            cls = self.dis(torch.from_numpy(dis_windows(d, ends))).argmax(1).numpy()
        return ends, cls

    def trip_time(self, proc: dict) -> float | None:
        ends, cls = self.class_sequence(proc)
        hit = np.nonzero(cls == CLASSES["internal"])[0]
        return float(ends[hit[0]] / FS) if len(hit) else None

    STEP_S, EVENT_BASED = 1.0 / FS, False

    def score_stream(self, proc: dict):
        d = differential_pu(estimate(self.com, proc), self.plant)
        ends = np.arange(max(N - 1, int(0.12 * FS)), len(d))
        with torch.no_grad():
            p = torch.softmax(self.dis(torch.from_numpy(dis_windows(d, ends))), 1)[:, CLASSES["internal"]].numpy()
        return ends / FS, p
