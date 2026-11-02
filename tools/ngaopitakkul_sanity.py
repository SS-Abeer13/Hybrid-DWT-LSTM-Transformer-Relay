"""Sanity check (spec section 6, paper Fig. 4): scale-1 squared db4 coefficients of the differential currents of an internal single-phase fault at 20 kHz."""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C, ngaopitakkul2006_dwt_bpnn as N
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
L = []
for tr in C.iter_hr(C.PLANT_A_MAIN, scenarios={"Internal_AG"}):
    t0 = C.events(tr["meta"])[0][0]
    c2 = N.prepare(tr)["c2"]; t = 2 * np.arange(c2.shape[1]) / N.FS
    pre, post = (t > t0 - 0.02) & (t < t0 - 0.001), (t >= t0) & (t < t0 + 0.005)
    ratio = c2[:, post].max(1) / c2[:, pre].max(1)
    L.append(f"trace {tr['index']}: max squared coefficient in 5 ms after the fault / max in 20 ms before (A, B, C, zero seq): " + " ".join(f"{r:.2f}" for r in ratio) + f"; detections near the event: {[round(2*d/N.FS - t0, 4) for d in N.detections(c2) if abs(2*d/N.FS - t0) < 0.02]}")
    cfg = C.plant_config("A")
    hv, lv = C.plant_pu(tr["Tp"].astype(float) / cfg["ct_ratio_hv"], tr["Ts"].astype(float) / cfg["ct_ratio_lv"], "A")
    d = lv - hv; xt = np.concatenate([d, d.mean(1, keepdims=True)], 1)
    import pywt
    ct = np.stack([pywt.dwt(xt[:, k], "db4", mode="symmetric")[1] ** 2 for k in range(4)])
    L.append("   same trace on the NOISE-FREE true line currents (V-I blocks): post/pre ratio A, B, C, 0: " + " ".join(f"{r:.1e}" for r in ct[:, post].max(1) / np.maximum(ct[:, pre].max(1), 1e-30)))
    fig, axs = plt.subplots(1, 2, figsize=(12, 4)); ax = axs[0]
    for k, nm in enumerate(["A", "B", "C", "0"]):
        ax.semilogy(t, c2[k] + 1e-14, lw=.7, label=nm)
    ax.axvline(t0, c="k", ls=":"); ax.set_xlim(t0 - .03, t0 + .03); ax.legend(); ax.set_title("CT secondaries with noise (benchmark input)")
    for k, nm in enumerate(["A", "B", "C", "0"]):
        axs[1].semilogy(t, ct[k] + 1e-14, lw=.7, label=nm)
    axs[1].axvline(t0, c="k", ls=":"); axs[1].set_xlim(t0 - .03, t0 + .03); axs[1].set_title("true line currents, no noise (diagnostic)")
    fig.tight_layout(); fig.savefig(ROOT / "documents" / "baselines" / "ngaopitakkul2006_sanity.png", dpi=120)
    if len(L) >= 5: break
(ROOT / "documents" / "baselines" / "ngaopitakkul2006_sanity.txt").write_text("\n".join(L)); print("\n".join(L))
