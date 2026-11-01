"""Hajipour, Vakilian and Sanaye-Pasand 2015: CT saturation compensation (DSC + optional DOCC), IEEE TPWRD 30(5).

Specification, UNSPECIFIED fills and deviations: documents/baselines/hajipour2015_ct_comp_spec.md (written before this code).
Causal, sample by sample; the saturation detector depends only on the measured secondary current, so candidate instants are found
vectorised and the flux recursion is only run inside saturation episodes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FS_COMP = 4000.0  # 80 samples per cycle at 50 Hz
N_E = 3          # samples of the primary current reconstructed by the LES extrapolation (Sec. III-A)
LES_WIN = 12     # window of the least-error-squares filter
DELTA_R = 0.10   # resistive burden (Eq. 10)


@dataclass
class CtParams:
    inv_Linf: float   # slope of the saturated branch, A / Wb  (= 1 / L_inf)
    lam0: float       # intercept of the saturated line, Wb
    lam_sat: float    # flux of the saturation point, Wb
    R: float          # total burden R_CT + R_B, ohm
    I2n: float        # rated secondary current, A (RMS)
    LB: float = 0.0   # burden inductance, H


# Saturable-transformer curves of the plants (pu of V2*sqrt2/w and I2n*sqrt2); R from the CT blocks (summary in the spec, section 4).
_CURVE_A = np.array([[0, 0], [0.0002, 2], [0.0006, 5.5], [0.0015, 8.5], [0.004, 9.75], [0.05, 10.75], [0.5, 12]])
_PLANTS = {"A": dict(curve=_CURVE_A, V2=5.0, I2n=5.0, R_CT=0.2, R_nom=1.0),
           "B": dict(curve=_CURVE_A * np.array([1, 12.0]), V2=2.5, I2n=1.0, R_CT=0.125, R_nom=2.5)}


def ct_params(plant: str = "A", burden_scale: float = 1.0, f: float = 50.0) -> CtParams:
    """CT parameters as the relay engineer would take them from the CT's routine test. burden_scale = 1 is the NOMINAL burden
    (what the relay knows); the true burden of a stress trace can be passed for the oracle variant (ctBurden of the trace metadata
    is the multiple of the nominal burden)."""
    p = _PLANTS[plant]
    w = 2 * np.pi * f
    phi_b, i_b = p["V2"] * np.sqrt(2) / w, p["I2n"] * np.sqrt(2)
    (i1, l1), (i2, l2) = p["curve"][-2], p["curve"][-1]
    slope = (l2 - l1) / (i2 - i1)                 # pu flux per pu current
    lam0 = (l1 - slope * i1) * phi_b
    return CtParams(inv_Linf=(i_b / phi_b) / slope, lam0=float(lam0), lam_sat=float(l1 * phi_b),
                    R=p["R_CT"] + p["R_nom"] * burden_scale, I2n=p["I2n"])


def _les_extrapolate(x: np.ndarray, n_end: int, w: float, dt: float, n_ahead: int) -> np.ndarray:
    """Fit a0 + a cos(wt) + b sin(wt) on x[n_end-LES_WIN:n_end] and return the model for the next n_ahead samples."""
    t = np.arange(n_end - LES_WIN, n_end + n_ahead) * dt
    A = np.stack([np.ones_like(t), np.cos(w * t), np.sin(w * t)], 1)
    c, *_ = np.linalg.lstsq(A[:LES_WIN], x[n_end - LES_WIN:n_end], rcond=None)
    return A[LES_WIN:] @ c


def saturation_candidates(x: np.ndarray, delta_b: float, delta_r: float = DELTA_R) -> np.ndarray:
    """Eqs. (9)-(11): boolean array, True where the third-difference prediction deviates from the measured current."""
    e = np.zeros_like(x)
    e[4:] = 4 * x[3:-1] - 6 * x[2:-2] + 4 * x[1:-3] - x[:-4]
    d = e - x
    s = e + x
    with np.errstate(divide="ignore", invalid="ignore"):
        sg = np.sign(np.where(s != 0, d / s, 1.0))
    c = (np.abs(d) * sg > delta_r * np.abs(e)) & (np.abs(d) > delta_b)
    c[:4 + LES_WIN] = False
    return c


def dsc(x: np.ndarray, fs: float, cp: CtParams, f: float = 50.0, delta_b: float | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Deformed-signal compensation of one CT secondary current (A). Returns (reconstructed, saturated flag)."""
    n = len(x)
    dt, w = 1.0 / fs, 2 * np.pi * f
    db = cp.I2n / 4 if delta_b is None else delta_b
    cand = saturation_candidates(x, db)
    out = x.copy()
    flag = np.zeros(n, bool)
    k = 0
    R, inv_L = cp.R, cp.inv_Linf
    while k < n - N_E - 1:
        if not cand[k]:
            k += 1
            continue
        ts = k
        # expand the unsaturated interval by LES extrapolation (i_exp1) and estimate the flux at the expanded samples
        iexp = _les_extrapolate(x, ts, w, dt, N_E)
        im_e = iexp - x[ts:ts + N_E]
        s = 1.0 if x[ts:ts + N_E].sum() + im_e.sum() >= 0 else -1.0       # Eq. (8)
        # |lambda| from the over-determined system, Eq. (7) with L_B = 0:  (1/Linf) mu_k = s*im_k + lam0/Linf ; 2/(R dt) (mu_{k+1}-mu_k) = s(i_k + i_{k+1})
        H = np.zeros((2 * N_E - 1, N_E))
        M = np.zeros(2 * N_E - 1)
        for j in range(N_E):
            H[j, j] = inv_L
            M[j] = s * im_e[j] * 1.0 + cp.lam0 * inv_L
        for j in range(N_E - 1):
            H[N_E + j, j], H[N_E + j, j + 1] = -2 / (R * dt), 2 / (R * dt)
            M[N_E + j] = s * (x[ts + j] + x[ts + j + 1])
        mu = np.linalg.lstsq(H, M, rcond=None)[0]
        lam = s * mu[-1]
        if abs(lam) <= cp.lam_sat:          # estimated flux below the saturation point: not a saturation (false alarm), no compensation
            k = ts + 1
            continue
        # hold the output for the expanded samples, then recurse flux with the trapezoidal rule (Eq. 5-6) while |lambda| > lambda_sat
        out[ts:ts + N_E] = iexp
        flag[ts:ts + N_E] = True
        j = ts + N_E - 1
        while j < n - 1:
            j += 1
            lam += 0.5 * R * dt * (x[j - 1] + x[j])
            if abs(lam) <= cp.lam_sat:
                break
            im = np.sign(lam) * (abs(lam) - cp.lam0) * inv_L
            out[j] = x[j] + im
            flag[j] = True
        k = j + 1
    return out, flag


def docc(x: np.ndarray, fs: float, cp: CtParams, f: float = 50.0, eps: float | None = None) -> np.ndarray:
    """DC-offset current compensation (Sec. IV): returns the bias to add. LES amplitude and mean over 8 samples."""
    n = len(x)
    N = int(round(fs / f))
    eps = 0.05 * cp.I2n if eps is None else eps
    w, dt = 2 * np.pi * f, 1.0 / fs
    shift = np.zeros(n)
    for k in range(8, n):
        seg = x[k - 8:k]
        t = np.arange(k - 8, k) * dt
        A = np.stack([np.ones(8), np.cos(w * t), np.sin(w * t)], 1)
        c = np.linalg.lstsq(A, seg, rcond=None)[0]
        imag, idc = np.hypot(c[1], c[2]), seg.mean()
        shift[k] = idc if (imag < eps and abs(idc) > eps) else 0.0
    bias = np.zeros(n)
    cs_abs = np.cumsum(np.abs(shift))
    cs_sgn = np.cumsum(np.sign(shift))
    for k in range(N, n):
        den = cs_sgn[k] - cs_sgn[k - N]
        bias[k] = -(cs_abs[k] - cs_abs[k - N]) / den if den != 0 else 0.0
    return bias


def compensate(x: np.ndarray, fs: float, cp: CtParams, f: float = 50.0, use_docc: bool = False) -> np.ndarray:
    """Columns of x are independent CT secondaries (A). Returns the compensated currents, same shape."""
    x = np.asarray(x, float)
    cols = []
    for c in range(x.shape[1]):
        y, _ = dsc(x[:, c], fs, cp, f)
        if use_docc:
            y = y + docc(x[:, c], fs, cp, f)
        cols.append(y)
    return np.stack(cols, 1)


def transient_error(est: np.ndarray, truth: np.ndarray, fs: float, t0: float, f: float = 50.0) -> float:
    """Eq. (14) per trace: max over the first 5 cycles after the event of |est - truth| / AC magnitude of the true current, in %."""
    i0 = int(t0 * fs)
    seg = slice(i0, i0 + int(5 * fs / f))
    ref = np.abs(truth[seg]).max()
    return float(np.abs(est[seg] - truth[seg]).max() / ref * 100) if ref > 0 else float("nan")
