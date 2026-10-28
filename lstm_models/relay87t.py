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
# v3 baseline values (thesis model with 0.5 ohm series resistors)
CT_RATIO_HV_V3, CT_RATIO_LV_V3 = 809.6, 16925.0
I_NOM_V3 = 300e6 / (np.sqrt(3) * 230e3) / CT_RATIO_HV_V3   # = 0.9302 A

# v4 calibrated values (series CT wiring, simulations/ct_calibration_v4.txt)
CT_RATIO_HV_V4, CT_RATIO_LV_V4 = 404.7288, 8460.0372
I_NOM_V4 = 1.8610                                         # = 1.8610 A

# Plant B calibrated values (simulations/plant_b_checks.txt)
CT_RATIO_HV_PLANT_B, CT_RATIO_LV_PLANT_B = 202.0119, 808.8849
I_NOM_PLANT_B = 0.8232

# Active calibration default (Plant A, v4)
CT_RATIO_HV, CT_RATIO_LV = CT_RATIO_HV_V4, CT_RATIO_LV_V4
I_NOM = I_NOM_V4
M_PLANT = (1 / np.sqrt(3)) * np.array([[1, 0, -1], [-1, 1, 0], [0, -1, 1]])   # column-vector form
I_PICKUP, I_HIGH_SET, SLOPE_1, SLOPE_2, BREAKPOINT = 0.30, 10.0, 0.25, 0.60, 3.0   # unchanged chart settings


def get_plant_config(plant: str = "A") -> dict:
    """Returns calibration and compensation matrix configuration for Plant A or Plant B."""
    p_name = plant.upper()
    if p_name == "A":
        return {
            "name": "Plant A",
            "rating_mva": 300.0,
            "v_hv_kv": 230.0,
            "v_lv_kv": 11.0,
            "vector_group": "YNd1",
            "i_nom": I_NOM_V4,
            "ct_ratio_hv": CT_RATIO_HV_V4,
            "ct_ratio_lv": CT_RATIO_LV_V4,
            "m_hv": (1 / np.sqrt(3)) * np.array([[1, 0, -1], [-1, 1, 0], [0, -1, 1]]),
            "m_lv": np.eye(3),
        }
    elif p_name == "B":
        return {
            "name": "Plant B",
            "rating_mva": 40.0,
            "v_hv_kv": 132.0,
            "v_lv_kv": 33.0,
            "vector_group": "Dyn11",
            "i_nom": I_NOM_PLANT_B,
            "ct_ratio_hv": CT_RATIO_HV_PLANT_B,
            "ct_ratio_lv": CT_RATIO_LV_PLANT_B,
            "m_hv": np.eye(3),
            "m_lv": (1 / np.sqrt(3)) * np.array([[1, -1, 0], [0, 1, -1], [-1, 0, 1]]),
        }
    else:
        raise ValueError(f"Unknown plant '{plant}'; expected 'A' or 'B'.")


def sliding_rms(x: np.ndarray) -> np.ndarray:
    """[T x 3] -> [T x 3] one-cycle sliding RMS; NaN for the first W-1 samples (block has not filled)."""
    c = np.cumsum(np.vstack([np.zeros((1, x.shape[1])), x ** 2]), axis=0)
    out = np.full(x.shape, np.nan)
    out[W - 1:] = np.sqrt((c[W:] - c[:-W]) / W)
    return out


def analyse(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP, i_nom: float | None = None,
            plant: str = "A") -> dict:
    """primary/secondary: [T x 3] CT-secondary amps (HV, LV). Returns per-sample boolean 'vote' (any-phase 87T trip
    condition), 'highset' (Id > 10 pu, bypasses the AI) and the per-phase Id/Ir RMS in pu."""
    cfg = get_plant_config(plant)
    base = i_nom if i_nom is not None else cfg["i_nom"]
    hv = (primary / base) @ cfg["m_hv"].T
    lv = (secondary / base) @ cfg["m_lv"].T
    idr = sliding_rms(lv - hv)
    irr = sliding_rms(0.5 * (np.abs(hv) + np.abs(lv)))
    dyn = np.where(irr <= BREAKPOINT, SLOPE_1 * irr, SLOPE_2 * (irr - BREAKPOINT) + SLOPE_1 * BREAKPOINT)
    with np.errstate(invalid="ignore"):
        v = (idr > pickup) & (idr > dyn)
        hs = idr > I_HIGH_SET
    return {"vote": np.nan_to_num(v.any(1)).astype(bool), "highset": np.nan_to_num(hs.any(1)).astype(bool),
            "idiff_rms": idr, "irest_rms": irr}


def fault_rise_pu(primary: np.ndarray, secondary: np.ndarray, onset: int, i_nom: float | None = None,
                  plant: str = "A") -> float:
    """Detectability: rise of the per-phase differential RMS (pu) 40-60 ms after the fault vs 10-30 ms before (as the generator did)."""
    cfg = get_plant_config(plant)
    base = i_nom if i_nom is not None else cfg["i_nom"]
    d = (secondary / base) @ cfg["m_lv"].T - (primary / base) @ cfg["m_hv"].T
    a = slice(onset + 64, onset + 96)
    b = slice(max(onset - 48, 0), max(onset - 16, 1))
    if a.stop > len(d):
        return float("nan")
    return float(np.max(np.sqrt((d[a] ** 2).mean(0)) - np.sqrt((d[b] ** 2).mean(0))))


def analyse_harmonic(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP,
                     k2_thresh: float = 0.15, k5_thresh: float = 0.35, mode: str = "per_phase",
                     i_nom: float | None = None, plant: str = "A") -> dict:
    """Conventional 87T dual-slope characteristic WITH 2nd and 5th harmonic restraint.
    Computes sliding 32-sample FFT harmonic ratios k2 = |I_100Hz| / |I_50Hz| and k5 = |I_250Hz| / |I_50Hz|.
    
    Modes:
      - 'per_phase' (recommended / standard industrial practice): each phase's trip vote is restrained
        only by its own harmonics, avoiding cross-phase blinding under CT saturation.
      - 'cross_active': cross-blocking active only from phases whose differential RMS exceeds pickup.
      - 'as_coded' (unselective cross-block): ANY phase with k2>15% or k5>35% blocks all phases.
    """
    res = analyse(primary, secondary, pickup=pickup, i_nom=i_nom, plant=plant)
    cfg = get_plant_config(plant)
    base = i_nom if i_nom is not None else cfg["i_nom"]
    hv = (primary / base) @ cfg["m_hv"].T
    lv = (secondary / base) @ cfg["m_lv"].T
    diff = lv - hv  # [T x 3]
    T_len = diff.shape[0]
    
    idr = res["idiff_rms"]
    irr = res["irest_rms"]
    dyn = np.where(irr <= BREAKPOINT, SLOPE_1 * irr, SLOPE_2 * (irr - BREAKPOINT) + SLOPE_1 * BREAKPOINT)
    with np.errstate(invalid="ignore"):
        vph = (idr > pickup) & (idr > dyn)
    vph = np.nan_to_num(vph).astype(bool)
    
    full_blocked = np.zeros((T_len, 3), dtype=bool)
    if T_len >= W:
        win = np.lib.stride_tricks.sliding_window_view(diff, W, axis=0)  # [T-W+1, 3, W]
        spec = np.abs(np.fft.fft(win, axis=-1))
        fund = spec[..., 1] + 1e-4
        k2 = spec[..., 2] / fund
        k5 = spec[..., 5] / fund
        ph_blocked = (k2 > k2_thresh) | (k5 > k5_thresh)  # [T-W+1, 3]
        full_blocked[W - 1:] = ph_blocked
        
    if mode == "as_coded":
        b = full_blocked.any(1)
        v = vph.any(1) & (~b)
    elif mode == "cross_active":
        act = np.nan_to_num(idr > pickup).astype(bool)
        b = (full_blocked & act).any(1)
        v = vph.any(1) & (~b)
    else:  # 'per_phase'
        v = (vph & (~full_blocked)).any(1)
        
    v_total = (v | res["highset"]).astype(bool)
    return {
        "vote": v_total,
        "vote_restrained": v,
        "vote_unrestrained": res["vote"],
        "highset": res["highset"],
        "blocked": full_blocked.any(1),
        "blocked_per_phase": full_blocked,
        "idiff_rms": idr,
        "irest_rms": irr
    }

