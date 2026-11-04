"""Figure for the paper: three representative traces of plant A as the relay sees them (1,600 Hz CT secondaries): an inrush, an internal fault, and an external
fault with CT saturation. The trace of each class is chosen by a fixed rule, not by eye: the TRACE WHOSE KEY METRIC IS THE MEDIAN of its scenario
(inrush: Inrush_NoLoad by differential RMS; internal fault: Internal_AG by fault differential rise; CT saturation: Stress_ExtCTSat_ABC by the maximum CT ratio error).
Rows: phase-A HV and LV CT secondaries (per unit of the rated secondary current, plant-compensated as in the relay) and the three-phase differential current (pu).
Output: paper_epsr/figures/fig_waveforms.pdf / .png and fig_waveforms_traces.txt (which traces were plotted and why).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import relay87t as R  # noqa: E402
from stress_dataset import FS, load_traces  # noqa: E402

OUTD = ROOT / "paper_epsr" / "figures"
CLASSES = [("Inrush_NoLoad", "diffRms100ms", "Energisation inrush (no load)"),
           ("Internal_AG", "faultDiffPu", "Internal fault (phase A to ground)"),
           ("Stress_ExtCTSat_ABC", "ctRatioErrorMax", "External fault, CT saturation")]


def key_metric(t: dict, metric: str, cfg: dict) -> float:
    """Stored metric, or (for the inrush, whose stored differential RMS is NaN) the differential RMS in the 100 ms after the energisation, computed from the trace."""
    if metric != "diffRms100ms":
        return float(t.get(metric, np.nan))
    hv = (t["primary"] / cfg["i_nom"]) @ cfg["m_hv"].T
    lv = (t["secondary"] / cfg["i_nom"]) @ cfg["m_lv"].T
    i0 = int(event_time(t) * FS)
    return float(np.sqrt(np.mean((lv - hv)[i0:i0 + int(0.1 * FS)] ** 2)))


def event_time(t: dict) -> float:
    for k in ("energisationTime", "inceptionTime"):
        v = t.get(k)
        if v is not None and np.isfinite(v) and v > 0:
            return float(v)
    return float("nan")


def main() -> None:
    OUTD.mkdir(parents=True, exist_ok=True)
    cfg = R.get_plant_config("A")
    by = {c[0]: [] for c in CLASSES}
    metric_of = {c[0]: c[1] for c in CLASSES}
    for t in load_traces(ROOT / "datasets" / "StressDataset_v5_20261028_162333.mat"):
        if t["scenarioName"] in by and t.get("checkPassed", 1) and not t.get("duplicate", 0):
            t["_key"] = key_metric(t, metric_of[t["scenarioName"]], cfg)
            if np.isfinite(t["_key"]):
                by[t["scenarioName"]].append(t)
    fig, axs = plt.subplots(2, 3, figsize=(10.5, 5.0), sharex="col")
    notes = []
    for j, (name, metric, title) in enumerate(CLASSES):
        ts = sorted(by[name], key=lambda t: t["_key"])
        t = ts[len(ts) // 2]
        notes.append(f"{title}: scenario {name}, source index {t['source_index']}, median of {len(ts)} traces by {metric} = {t['_key']:.3g}; ctBurden {t.get('ctBurden')}, event at {event_time(t):.4f} s")
        hv = (t["primary"] / cfg["i_nom"]) @ cfg["m_hv"].T
        lv = (t["secondary"] / cfg["i_nom"]) @ cfg["m_lv"].T
        d = lv - hv
        t0 = event_time(t)
        x = (np.arange(len(hv)) / FS - t0) * 1e3
        sl = (x >= -30) & (x <= 110)
        ax = axs[0, j]
        ax.plot(x[sl], hv[sl, 0], lw=1.1, label="HV side, phase A")
        ax.plot(x[sl], lv[sl, 0], lw=1.1, label="LV side, phase A")
        ax.set_title(title, fontsize=10)
        ax.axvline(0, color="k", ls=":", lw=0.8)
        ax = axs[1, j]
        for p, c in zip(range(3), ("C0", "C1", "C2")):
            ax.plot(x[sl], d[sl, p], lw=1.0, color=c, label="phase " + "ABC"[p])
        ax.axvline(0, color="k", ls=":", lw=0.8)
        ax.set_xlabel("time from the event (ms)")
    axs[0, 0].set_ylabel("CT secondary current (pu)")
    axs[1, 0].set_ylabel("differential current (pu)")
    axs[0, 0].legend(fontsize=7, loc="upper right")
    axs[1, 0].legend(fontsize=7, loc="upper right")
    for a in axs.ravel():
        a.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTD / "fig_waveforms.pdf")
    fig.savefig(OUTD / "fig_waveforms.png", dpi=170)
    (OUTD / "fig_waveforms_traces.txt").write_text("\n".join(["Plotted traces (fixed rule: the trace with the median key metric of its scenario)"] + notes), encoding="utf-8")
    print("\n".join(notes))


if __name__ == "__main__":
    main()
