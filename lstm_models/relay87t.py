"""Python mirror of the Simulink conventional 87T path (Yd1_Compensation chart + RMS blocks + Hybrid_87T_Decision chart).

CALIBRATION (corrected 2026-10-21 from ground truth, simulations/probe_ct_truth.m):
  The model's V-I measurement blocks (true line currents) show the CTs behave as HV 809.6:1 and LV 16925:1, i.e. 2.024 x the
  winding-voltage ratios (400:1 and 92000/11:1) the first fix assumed. Rated line currents of the 300 MVA, 230/11 kV transformer are
  753.06 A / 15745.9 A, so the rated CT-secondary current is 0.9302 A on BOTH sides (the earlier 1.8827 A was wrong by 2.024x, the
  original relay's LV base 0.8557 A by 8 %, its HV base 1.883 A by 2x).
  Yd1 compensation on the HV (Y) side in column-vector form: M = (1/sqrt3)[1 0 -1; -1 1 0; 0 -1 1] (fitted on healthy traces;
  the original chart used the transpose).
I_diff = I_lv_pu - M*I_hv_pu, I_rest = 0.5(|M*I_hv_pu| + |I_lv_pu|), each phase RMS over one 50 Hz cycle
(32 samples at 1600 Hz; the 'RMS' blocks are sliding true-RMS with Freq 50).
"""
from __future__ import annotations

import numpy as np

FS = 1600
W = 32
CT_RATIO_HV, CT_RATIO_LV = 809.6, 16925.0            # effective ratios measured against the true line currents
I_NOM = 300e6 / (np.sqrt(3) * 230e3) / CT_RATIO_HV   # = 0.9302 A; LV: 300e6/(sqrt3*11e3)/16925 = 0.9303 A
M_PLANT = (1 / np.sqrt(3)) * np.array([[1, 0, -1], [-1, 1, 0], [0, -1, 1]])   # column-vector form
I_PICKUP, I_HIGH_SET, SLOPE_1, SLOPE_2, BREAKPOINT = 0.30, 10.0, 0.25, 0.60, 3.0   # unchanged chart settings


def sliding_rms(x: np.ndarray) -> np.ndarray:
    """[T x 3] -> [T x 3] one-cycle sliding RMS; NaN for the first W-1 samples (block has not filled)."""
    c = np.cumsum(np.vstack([np.zeros((1, x.shape[1])), x ** 2]), axis=0)
    out = np.full(x.shape, np.nan)
    out[W - 1:] = np.sqrt((c[W:] - c[:-W]) / W)
    return out


def analyse(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP) -> dict:
    """primary/secondary: [T x 3] CT-secondary amps (HV, LV). Returns per-sample boolean 'vote' (any-phase 87T trip
    condition), 'highset' (Id > 10 pu, bypasses the AI) and the per-phase Id/Ir RMS in pu."""
    hv = (primary / I_NOM) @ M_PLANT.T
    lv = secondary / I_NOM
    idr = sliding_rms(lv - hv)
    irr = sliding_rms(0.5 * (np.abs(hv) + np.abs(lv)))
    dyn = np.where(irr <= BREAKPOINT, SLOPE_1 * irr, SLOPE_2 * (irr - BREAKPOINT) + SLOPE_1 * BREAKPOINT)
    with np.errstate(invalid="ignore"):
        v = (idr > pickup) & (idr > dyn)
        hs = idr > I_HIGH_SET
    return {"vote": np.nan_to_num(v.any(1)).astype(bool), "highset": np.nan_to_num(hs.any(1)).astype(bool),
            "idiff_rms": idr, "irest_rms": irr}


def fault_rise_pu(primary: np.ndarray, secondary: np.ndarray, onset: int) -> float:
    """Detectability: rise of the per-phase differential RMS (pu) 40-60 ms after the fault vs 10-30 ms before (as the generator did)."""
    d = (secondary / I_NOM) - (primary / I_NOM) @ M_PLANT.T
    a = slice(onset + 64, onset + 96)
    b = slice(max(onset - 48, 0), max(onset - 16, 1))
    if a.stop > len(d):
        return float("nan")
    return float(np.max(np.sqrt((d[a] ** 2).mean(0)) - np.sqrt((d[b] ** 2).mean(0))))


def analyse_harmonic(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP,
                     k2_thresh: float = 0.15, k5_thresh: float = 0.35, cross_block: bool = True) -> dict:
    """Conventional 87T dual-slope characteristic WITH 2nd and 5th harmonic restraint / cross-blocking.
    Computes sliding 32-sample FFT harmonic ratios k2 = |I_100Hz| / |I_50Hz| and k5 = |I_250Hz| / |I_50Hz|.
    Blocks tripping when k2 > k2_thresh (15% inrush) or k5 > k5_thresh (35% over-excitation).
    """
    res = analyse(primary, secondary, pickup=pickup)
    hv = (primary / I_NOM) @ M_PLANT.T
    lv = secondary / I_NOM
    diff = lv - hv  # [T x 3]
    T_len = diff.shape[0]
    blocked = np.zeros(T_len, dtype=bool)
    if T_len >= W:
        win = np.lib.stride_tricks.sliding_window_view(diff, W, axis=0)  # [T-W+1, 3, W]
        spec = np.abs(np.fft.fft(win, axis=-1))
        fund = spec[..., 1] + 1e-4
        k2 = spec[..., 2] / fund
        k5 = spec[..., 5] / fund
        if cross_block:
            is_blocked = (k2 > k2_thresh).any(-1) | (k5 > k5_thresh).any(-1)
        else:
            is_blocked = ((k2 > k2_thresh) | (k5 > k5_thresh)).all(-1)
        blocked[W - 1:] = is_blocked
    v_restrained = res["vote"] & (~blocked)
    return {
        "vote": (v_restrained | res["highset"]).astype(bool),
        "vote_restrained": v_restrained.astype(bool),
        "vote_unrestrained": res["vote"],
        "highset": res["highset"],
        "blocked": blocked,
        "idiff_rms": res["idiff_rms"],
        "irest_rms": res["irest_rms"]
    }

