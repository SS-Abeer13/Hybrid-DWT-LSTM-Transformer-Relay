"""Python port of datasets/extract_12_features.m (must stay identical to the MATLAB/Simulink DWT).

Per 32-sample window of I_diff = Ip - Is (1600 Hz), per phase:
  log1p of the energies of db4 level-1 detail, level-2 detail, level-2 approximation
  (MATLAB wavedec default 'sym' extension == PyWavelets 'symmetric'), and the
  2nd-harmonic ratio |FFT[100 Hz]| / (|FFT[50 Hz]| + 1e-4), capped at 2.0.
Feature order: [D1 D2 A2] x phases A,B,C, then ratios A,B,C  -> 12 features.
Row j uses samples j+1 .. j+32 (0-based), so it is available at sample j+32.
"""

from __future__ import annotations

import numpy as np
import pywt

WINDOW = 32


def trace_features(i_diff: np.ndarray) -> np.ndarray:
    """[T x 3] differential current -> [T-32 x 12] float32 features."""
    n = i_diff.shape[0] - WINDOW
    # All windows ending at samples 33..T (MATLAB 1-based) at once: [n, 32, 3]
    win = np.lib.stride_tricks.sliding_window_view(i_diff, WINDOW, axis=0)[1:n + 1]  # [n, 3, 32]
    out = np.zeros((n, 12), dtype=np.float64)
    a2, d2, d1 = pywt.wavedec(win, "db4", mode="symmetric", level=2, axis=-1)
    out[:, 0:9:3] = np.log1p((d1 ** 2).sum(-1))
    out[:, 1:9:3] = np.log1p((d2 ** 2).sum(-1))
    out[:, 2:9:3] = np.log1p((a2 ** 2).sum(-1))
    spec = np.abs(np.fft.fft(win, axis=-1))
    out[:, 9:12] = np.minimum(spec[..., 2] / (spec[..., 1] + 1e-4), 2.0)
    return out.astype(np.float32)


# ---- Yd1-compensated, per-unit differential (what the relay's 87T path uses) ----------------
# Mirrors the "Yd1 Compensation" chart in the Simulink relay (300 MVA, 230/11 kV, CT 2000/5 and 92000/5).
_S, _VHV, _VLV, _CTHV, _CTLV = 300e6, 230e3, 11e3, 2000 / 5, 92000 / 5
I_NOM_HV = _S / (np.sqrt(3) * _VHV) / _CTHV
I_NOM_LV = _S / (np.sqrt(3) * _VLV) / _CTLV
M_YD1 = (1 / np.sqrt(3)) * np.array([[1, -1, 0], [0, 1, -1], [-1, 0, 1]])


def compensated_diff(primary: np.ndarray, secondary: np.ndarray) -> np.ndarray:
    """[T x 3] HV / LV CT-secondary amps -> [T x 3] per-unit Yd1-compensated differential (sign as relay's I_diff)."""
    hv = (primary / I_NOM_HV) @ M_YD1.T
    lv = secondary / I_NOM_LV
    return lv - hv


def plant_compensated_diff(primary: np.ndarray, secondary: np.ndarray) -> np.ndarray:
    """Differential in raw CT-secondary amps with the Yd1 mapping that this PLANT actually obeys.

    Fitted on healthy traces (2026-10-20): LV_amps ~= (1/sqrt3) [[1,0,-1],[-1,1,0],[0,-1,1]] @ HV_amps (residual ~2.5 % of
    load, vs 51 % for the uncompensated Ip - Is). This is the TRANSPOSE of the relay's M_YD1 and needs no per-unit scaling.
    """
    return secondary - primary @ M_YD1
