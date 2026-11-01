"""Sanity check of the Hajipour et al. CT-saturation compensation on the plant-A CT-stress external-fault traces
(spec section 5): transient error (Eq. 14) of the raw secondary, the compensated one with the nominal burden and with the true burden.
Output: documents/baselines/hajipour2015_sanity.txt / .png"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C  # noqa: E402
from baselines import hajipour2015_ct_comp as H  # noqa: E402

FS = 4000.0
MAXN = 40


def main() -> None:
    cfg = C.plant_config("A")
    res, shown = [], None
    for tr in C.iter_hr(C.PLANT_A_MAIN, scenarios={s for s in ("Stress_ExtCTSat_ABC", "Stress_ExtCTSat_AB", "Stress_ExtCTSat_BC", "Stress_ExtCTSat_ABCG", "Stress_ExtCTSat_AG")}):
        if len(res) >= MAXN:
            break
        ev = C.events(tr["meta"])
        if not ev:
            continue
        t0 = ev[0][0]
        ratio_hv = cfg["ct_ratio_hv"]
        x = C.resample(tr["Ip"], FS)
        tru = C.resample(tr["Tp"], FS) / ratio_hv
        bs = float(tr["meta"].get("ctBurden", 1.0))
        nom = H.compensate(x, FS, H.ct_params("A", 1.0))
        orc = H.compensate(x, FS, H.ct_params("A", bs))
        e = lambda y: np.nanmax([H.transient_error(y[:, c], tru[:, c], FS, t0) for c in range(3)])  # noqa: E731
        res.append((tr["meta"]["scenarioName"], bs, e(x), e(nom), e(orc)))
        if shown is None or res[-1][2] > shown[0]:
            c = int(np.argmax([H.transient_error(x[:, c], tru[:, c], FS, t0) for c in range(3)]))
            shown = (res[-1][2], t0, x[:, c], nom[:, c], orc[:, c], tru[:, c], res[-1][0], bs)
    r = np.array([x[1:] for x in res], float)
    L = [f"Hajipour et al. 2015 CT compensation, plant A, {len(res)} CT-stress external-fault traces, 4 kHz (80 samples/cycle), DOCC off",
         "transient error (Eq. 14, max over the first 5 cycles after the event, worst phase), % ; burden scale = multiple of the nominal burden",
         f"burden scale: median {np.median(r[:,0]):.2f}, range {r[:,0].min():.2f}-{r[:,0].max():.2f}"]
    for name, j in (("no compensation", 1), ("compensation, nominal burden assumed", 2), ("compensation, true burden (oracle)", 3)):
        L.append(f"{name:40s} median {np.nanmedian(r[:,j-0]):7.2f}  p90 {np.nanpercentile(r[:,j],90):7.2f}  max {np.nanmax(r[:,j]):7.2f}")
    L.append("paper (PSCAD, Jiles-Atherton CT): below 1.4 / 3.21 / 1.67 % in the worst case")
    out = ROOT / "documents" / "baselines" / "hajipour2015_sanity.txt"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _, t0, x, nom, orc, tru, name, bs = shown
    t = np.arange(len(x)) / FS
    fig, ax = plt.subplots(figsize=(9, 4))
    sl = (t > t0 - 0.01) & (t < t0 + 0.12)
    ax.plot(t[sl], x[sl], label="secondary (saturated)")
    ax.plot(t[sl], nom[sl], label="compensated, nominal burden")
    ax.plot(t[sl], orc[sl], "--", label="compensated, true burden")
    ax.plot(t[sl], tru[sl], "k:", label="true primary / ratio")
    ax.set_xlabel("t (s)"); ax.set_ylabel("A"); ax.set_title(f"{name}, burden x{bs:.1f}"); ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(ROOT / "documents" / "baselines" / "hajipour2015_sanity.png", dpi=130)


if __name__ == "__main__":
    main()
