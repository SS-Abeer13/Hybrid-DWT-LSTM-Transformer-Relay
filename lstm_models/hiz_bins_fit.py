"""Step A4: merge simulations/hiz_sweep_<type>.mat, find the fault resistance at which the measured differential (faultDiffPu) crosses the
87T pickup (0.30 pu) and the detectability limit (0.05 pu), and write the three HiZ Rf bins per fault type.

    python lstm_models/hiz_bins_fit.py        (PYTHONPATH=.pylibs for numpy is not needed; scipy + matplotlib from system Python)

Outputs: simulations/hiz_bins.json, figures/hiz_sensitivity.png, simulations/hiz_bins.txt
Bins per type (all log-uniform in Rf):
  visible   : faultDiffPu 1.0 -> 0.30  (the 87T itself sees the fault)
  ai_only   : faultDiffPu 0.30 -> 0.05  (below the 87T pickup, above the detect limit: only the AI-alone path can trip)
  undetect  : faultDiffPu 0.05 -> 0.015 (below the limit; generated, reported separately, never used as 'should trip' in the headline numbers)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent.parent
SIM = ROOT / "simulations"
PICKUP, LIMIT, UPPER, LOWER = 0.30, 0.05, 1.0, 0.015


def crossing(rf: np.ndarray, d: np.ndarray, level: float) -> float:
    """Rf (ohm) where the monotone-decreasing curve d(rf) crosses `level` (log-log interpolation)."""
    order = np.argsort(rf)
    lr, ld = np.log(rf[order]), np.log(np.maximum(d[order], 1e-9))
    if level > d.max() or level < d.min():
        return float("nan")
    # d decreases with rf: interpolate rf as a function of -d
    return float(np.exp(np.interp(np.log(level), ld[::-1], lr[::-1])))


def main() -> None:
    files = sorted(SIM.glob("hiz_sweep_*.mat"))
    assert files, "run hiz_sensitivity_sweep for each type first"
    res, curves = {}, {}
    for f in files:
        m = loadmat(f, squeeze_me=True)
        t = str(m["type"])
        rf, loads, D = np.atleast_1d(m["Rf"]).astype(float), np.atleast_1d(m["loadsPct"]).astype(float), np.atleast_2d(m["faultDiffPu"]).astype(float)
        mono = all(np.all(np.diff(row) <= 1e-3 * row[:-1] + 1e-4) for row in D)
        per = {}
        for lv, row in zip(loads, D):
            per[f"{lv:.0f}"] = {"rf_1pu": crossing(rf, row, UPPER), "rf_pickup": crossing(rf, row, PICKUP), "rf_limit": crossing(rf, row, LIMIT), "rf_lower": crossing(rf, row, LOWER)}
        med = {k: float(np.nanmedian([v[k] for v in per.values()])) for k in ("rf_1pu", "rf_pickup", "rf_limit", "rf_lower")}
        spread = {k: float(np.nanmax([v[k] for v in per.values()]) / np.nanmin([v[k] for v in per.values()])) for k in ("rf_pickup", "rf_limit")}
        res[t] = {"per_load": per, "median": med, "max_over_min_across_loads": spread, "monotonic": bool(mono),
                  "bins": {"visible": [med["rf_pickup"], med["rf_1pu"]], "ai_only": [med["rf_limit"], med["rf_pickup"]], "undetect": [med["rf_lower"], med["rf_limit"]]}}
        curves[t] = (rf, loads, D)
    # a bin is [low, high] ohm; visible = from the 1.0 pu crossing UP to the pickup crossing -> store as [rf(1pu), rf(pickup)]
    for t, r in res.items():
        r["bins"]["visible"] = [r["median"]["rf_1pu"], r["median"]["rf_pickup"]]
        r["bins"]["ai_only"] = [r["median"]["rf_pickup"], r["median"]["rf_limit"]]
        r["bins"]["undetect"] = [r["median"]["rf_limit"], r["median"]["rf_lower"]]
    (SIM / "hiz_bins.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    lines = ["HiZ sensitivity (corrected differential, base 1.8610 A; no noise; burden 1x)", "",
             f"{'type':5s} {'Rf@1pu':>8s} {'Rf@0.30':>9s} {'Rf@0.05':>9s} {'Rf@0.015':>9s} | load spread (max/min) of Rf@0.30, Rf@0.05 | monotonic"]
    for t, r in res.items():
        m = r["median"]
        lines.append(f"{t:5s} {m['rf_1pu']:8.2f} {m['rf_pickup']:9.2f} {m['rf_limit']:9.2f} {m['rf_lower']:9.2f} | {r['max_over_min_across_loads']['rf_pickup']:.2f}, {r['max_over_min_across_loads']['rf_limit']:.2f} | {r['monotonic']}")
    lines += ["", "Bins (ohm, log-uniform):"]
    for t, r in res.items():
        b = r["bins"]
        lines.append(f"  {t:4s} visible {b['visible'][0]:.2f}-{b['visible'][1]:.2f} | ai_only {b['ai_only'][0]:.2f}-{b['ai_only'][1]:.2f} | undetect {b['undetect'][0]:.2f}-{b['undetect'][1]:.2f}")
    (SIM / "hiz_bins.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4.6))
        for (t, (rf, loads, D)), c in zip(curves.items(), plt.cm.tab10.colors):
            for lv, row, ls in zip(loads, D, ("-", "--", ":")):
                ax.loglog(rf, np.maximum(row, 1e-4), ls, color=c, lw=1.4, label=f"{t}" if ls == "-" else None)
        ax.axhline(PICKUP, color="k", lw=1); ax.text(0.11, PICKUP * 1.08, "87T pickup 0.30 pu", fontsize=8)
        ax.axhline(LIMIT, color="gray", lw=1); ax.text(0.11, LIMIT * 1.08, "detect limit 0.05 pu", fontsize=8)
        ax.set_xlabel("fault resistance Rf (ohm)"); ax.set_ylabel("measured differential rise, faultDiffPu (pu)")
        ax.set_title("Internal fault sensitivity: solid lines 30 % load, dashed 60 %, dotted 100 %"); ax.grid(True, which="both", alpha=0.3); ax.legend(ncol=3, fontsize=8)
        fig.tight_layout(); (ROOT / "figures").mkdir(exist_ok=True); fig.savefig(ROOT / "figures" / "hiz_sensitivity.png", dpi=150)
        print("figure: figures/hiz_sensitivity.png")
    except Exception as e:  # plotting is optional
        print("no figure:", e)


if __name__ == "__main__":
    main()
