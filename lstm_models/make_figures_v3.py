"""E2: thesis figures from saved files -> documents/results_v3/*.png

    python lstm_models/make_figures_v3.py [coverage|cdf|sweep|waveforms|all]
(the HiZ sensitivity figure comes from hiz_bins_fit.py -> figures/hiz_sensitivity.png)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_cv_v3 as C  # noqa: E402
import train_trace_split as T  # noqa: E402
from coverage_report_v3 import group_of, load_meta  # noqa: E402
from v3_checks import relaxed_ok, relaxed_ok_trace  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "documents" / "results_v3"
RUN = ROOT / "runs" / "20261021_v3_cv5"
DATA = [ROOT / "datasets" / n for n in ("StressDataset_v3_20261021_021053.mat", "StressDataset_v3Only_topup_inrush_loaded.mat", "StressDataset_v3Only_topup_overexc.mat")]
COL = {"87T alone": "#888888", "LSTM alone": "#1f77b4", "Hybrid (87T gate)": "#ff7f0e", "Hybrid + AI-alone path": "#2ca02c"}


def coverage() -> None:
    parts = [load_meta(p) for p in DATA]
    keys = set.intersection(*[set(x[1]) for x in parts])
    num = {k: np.concatenate([x[1][k] for x in parts]) for k in keys}
    names = [n for x in parts for n in x[2]]; status = [s for x in parts for s in x[3]]
    ok = relaxed_ok(num, names, status)
    g = np.array([group_of(n) for n in names])
    groups = [k for k in sorted(set(g)) if not k.startswith("other")]
    M = np.array([[int(((g == k) & ok & (num["loadBin"] == b)).sum()) for b in (1, 2, 3, 4)] for k in groups])
    fig, ax = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1, 1.05]})
    im = ax[0].imshow(M, cmap="Blues", aspect="auto")
    ax[0].set_xticks(range(4), ["10-30", "30-60", "60-90", "90-110"]); ax[0].set_yticks(range(len(groups)), groups, fontsize=8)
    ax[0].set_xlabel("load, % of rated current"); ax[0].set_title("Traces per scenario group and load bin")
    for i in range(M.shape[0]):
        for j in range(4):
            ax[0].text(j, i, M[i, j], ha="center", va="center", fontsize=7, color="white" if M[i, j] > M.max() / 2 else "black")
    cells, labels = [], []
    for k in ("Inrush no-load", "Inrush loaded"):
        for q in range(4):
            row = []
            for b in (1, 2, 3):
                sel = (g == k) & ok & (num["inceptionAngle"] >= 90 * q) & (num["inceptionAngle"] < 90 * (q + 1)) & (num["fluxBin"] == b)
                row.append(int(sel.sum()))
            cells.append(row); labels.append(f"{k.split()[1]}  {90 * q}-{90 * (q + 1)} deg")
    cells = np.array(cells)
    ax[1].imshow(cells, cmap="Greens", aspect="auto", vmin=0)
    ax[1].set_xticks(range(3), ["0-0.27", "0.27-0.53", "0.53-0.8"]); ax[1].set_yticks(range(len(labels)), labels, fontsize=8)
    ax[1].set_xlabel("largest residual flux, pu"); ax[1].set_title("Inrush cells: closing angle x residual flux (min 10 required)")
    for i in range(cells.shape[0]):
        for j in range(3):
            ax[1].text(j, i, cells[i, j], ha="center", va="center", fontsize=8, color="white" if cells[i, j] > cells.max() / 2 else "black")
    fig.tight_layout(); fig.savefig(OUT / "fig_coverage.png", dpi=150); plt.close(fig)
    print("coverage figure written")


def pooled_rows() -> dict:
    rows = {v: [] for v in C.VARIANTS}
    for f in sorted(RUN.glob("fold*/result.json")):
        res = json.loads(f.read_text(encoding="utf-8"))
        for v in C.VARIANTS:
            rows[v] += res["rows"][v]
    return rows


def cdf() -> None:
    rows = pooled_rows()
    fig, ax = plt.subplots(figsize=(7, 4.4))
    for v in C.VARIANTS:
        ms = np.sort([r["operate_ms"] for r in rows[v] if r["should_trip"] and r["operate_ms"] is not None and not r.get("undetectable")])
        ax.step(ms, np.arange(1, len(ms) + 1) / len(ms), where="post", label=f"{v} (n={len(ms)})", color=COL[v], lw=1.6)
    for x, lab in ((20, "1 cycle"), (40, "2 cycles")):
        ax.axvline(x, color="k", ls=":", lw=0.8); ax.text(x + 0.5, 0.05, lab, fontsize=8)
    ax.set_xscale("symlog", linthresh=5); ax.set_xlim(0, 400); ax.set_xlabel("operate time after the measured fault onset, ms"); ax.set_ylabel("fraction of tripped faults")
    ax.set_title("Operate-time distribution (out-of-fold, repetition 1)"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(OUT / "fig_operate_time_cdf.png", dpi=150); plt.close(fig)
    print("cdf figure written")


def sweep() -> None:
    """Dependability vs security as the AI threshold varies, from the five fold models of repetition 1 (out-of-fold decisions)."""
    C.configure(type("A", (), {"dwell": 20, "dep_tolerance": 2.0, "sec_tolerance": 1.0, "limit": 0})())
    traces = [t for t in np.load(ROOT / "runs" / "20261021_v3data_baseline" / "traces_cache_main.npz", allow_pickle=True)["traces"] if "checkPassed" not in t or relaxed_ok_trace(t)]
    for t in traces:
        t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < C.MIN_FAULT_PU)
    grid = [0.5, 0.7, 0.8, 0.9, 0.95, 0.97, 0.98, 0.99, 0.995, 0.998, 0.999]
    out = {"LSTM alone": [], "Hybrid (87T gate)": [], "Hybrid + AI-alone path (solo 0.998)": []}
    store = {k: [] for k in out}
    for k in range(1, 6):
        res = json.loads((RUN / f"fold{k}" / "result.json").read_text(encoding="utf-8"))
        te = sorted({r["trace"] for r in res["rows"]["LSTM alone"]})
        ck = torch.load(RUN / f"fold{k}" / "transformer_protection_lstm_best.pth", map_location="cpu", weights_only=False)
        cfg = ck["config"]
        m = T.TransformerProtectionLSTM(int(cfg["input_size"]), int(cfg["hidden_size"]), int(cfg["num_layers"]), float(cfg["dropout"]), bool(cfg["bidirectional"]))
        m.load_state_dict(ck["model_state_dict"]); m.eval()
        probs = {i: T.stream_probs(m, traces[i]["features"], torch.device("cpu")) for i in te}
        for gi, thr in enumerate(grid):
            for name, (var, solo) in {"LSTM alone": ("LSTM alone", None), "Hybrid (87T gate)": ("Hybrid (87T gate)", None), "Hybrid + AI-alone path (solo 0.998)": ("Hybrid + AI-alone path", max(thr, 0.998))}.items():
                rows = C.rows_for(traces, te, probs, var, thr, solo)
                C.annotate(rows, traces)
                if gi == 0 and k == 1 and name == "LSTM alone":
                    pass
                store[name].append((gi, rows))
        print(f"sweep fold {k} done", flush=True)
    fig, ax = plt.subplots(figsize=(7, 4.6))
    for name, color in zip(out, ("#1f77b4", "#ff7f0e", "#2ca02c")):
        pts = []
        for gi, thr in enumerate(grid):
            rows = [r for g_, rr in store[name] if g_ == gi for r in rr]
            s = C.summarise(rows)
            pts.append((s["security_pct"], s["dependability_pct"]))
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "o-", ms=4, label=name, color=color)
        out[name] = pts
    ax.set_xlabel("security, % of healthy traces not tripped"); ax.set_ylabel("dependability, % of faults tripped"); ax.set_xlim(94, 100.2); ax.set_ylim(80, 100.5)
    ax.set_title("Threshold trade-off (AI threshold 0.5 ... 0.999, out-of-fold)"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout(); fig.savefig(OUT / "fig_threshold_tradeoff.png", dpi=150); plt.close(fig)
    (OUT / "threshold_tradeoff.json").write_text(json.dumps({"grid": grid, "points_security_dependability": out}, indent=1), encoding="utf-8")
    print("sweep figure written")


def waveforms() -> None:
    from stress_dataset import load_traces
    import features12 as F
    tr = load_traces(DATA[0])
    names = np.array([group_of(t["scenarioName"]) for t in tr])
    fig, axes = plt.subplots(4, 4, figsize=(15, 9.5))
    cats = sorted(set(names))
    for ax, c in zip(axes.ravel(), cats):
        cand = [i for i in np.flatnonzero(names == c) if tr[i].get("checkPassed") == 1 and (not tr[i]["should_trip"] or tr[i].get("faultDiffPu", 1) > 0.3 or "HiZ" in c)]
        i = cand[len(cand) // 3] if cand else int(np.flatnonzero(names == c)[0])
        t = tr[i]; d = F.plant_compensated_diff(t["primary"], t["secondary"]) / 0.9302
        tt = np.arange(len(d)) / 1600.0
        lim = 1.0 if c not in ("Internal LV solid", "Internal HV-side", "Internal CT-sat", "SOTF", "Evolving", "Fault in inrush", "Recovery inrush", "Over-excitation") else max(np.abs(d).max() * 1.05, 0.2)
        for ph, col in zip(range(3), ("#d62728", "#2ca02c", "#1f77b4")):
            ax.plot(tt, d[:, ph], lw=0.7, color=col)
        ev = t.get("inceptionTime", np.nan)
        if np.isfinite(ev) and t["should_trip"]:
            ax.axvline(ev, color="k", ls="--", lw=0.8)
        ax.set_title(f"{c}  [{t['scenarioName']}]", fontsize=8); ax.set_xlim(0, 1.1); ax.tick_params(labelsize=7); ax.grid(True, alpha=0.25)
    for ax in axes.ravel()[len(cats):]:
        ax.axis("off")
    fig.supxlabel("time, s (dashed = fault onset)"); fig.supylabel("plant-compensated differential, pu of rated current")
    fig.tight_layout(); fig.savefig(OUT / "fig_example_waveforms.png", dpi=130); plt.close(fig)
    print("waveform figure written")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in (("coverage", coverage), ("cdf", cdf), ("sweep", sweep), ("waveforms", waveforms)):
        if what in (name, "all"):
            fn()
