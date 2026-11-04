"""Paper figures (paper-v1) from saved JSON files only; vector PDF with embedded fonts, in paper_epsr/figures/.

fig_operating_points.pdf  dependability vs security (plant-A CV) of every method and instance (Tables A-D)
fig_categories.pdf        correct decisions per scenario category for four relays (CV)
fig_operate_ecdf.pdf      empirical CDF of the operate time of correctly tripped faults (CV)
fig_plantb_paths.pdf      plant-B zero-shot: which path tripped first, deployed LSTM vs Key's network
Data: tools/paper_data.py (per-trace rows), runs/20261029_v5_plant_b_zeroshot/trip_path_check.json, full/key_hybrid/final_plantB_main.json.
Colours: validated categorical palette, fixed order (dataviz skill); identity is also carried by marker shape / labels, never by colour alone.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_data as P  # noqa: E402

OUT = P.ROOT / "paper_epsr" / "figures"
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]   # validated (light surface), fixed order
INK, MUTED, GRID = "#1f1f1e", "#5c5b57", "#e4e3df"
MM = 1 / 25.4
plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "legend.frameon": False})


def save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, bbox_inches="tight", metadata={"Creator": "tools/make_paper_figures.py", "CreationDate": None})
    plt.close(fig)
    print("wrote", name)


# label placement only (points / text alignment), chosen by looking at the rendered figure
LABEL_OFFSET = {"Ngaopitakkul (native)": (-4, 2, "right"), "Abdusalam (native)": (-4, 3, "right"), "LSTM, tuned": (-4, 3, "right"),
                "Random forest": (2, -8, "left"), "Key's network": (-2, 4, "right"), "LSTM, deployed": (3, -6, "left"),
                "GRU": (-4, 2, "right"), "1D-CNN": (3, 2, "left"), "MLP": (3, 2, "left")}


def fig_operating_points(M) -> None:
    style = {"Reproduction (native)": ("o", SLOTS[0]), "Reproduction (like-for-like)": ("^", SLOTS[1]), "Conventional relay": ("s", SLOTS[2]),
             "Dual-path instance": ("D", SLOTS[3]), "Ablation": ("v", SLOTS[4])}
    pts = {name: (g, *P.dep_sec(rows)) for name, (g, rows) in M.items()}
    fig, axes = plt.subplots(1, 2, figsize=(180 * MM, 72 * MM), gridspec_kw={"width_ratios": [1, 1.25]})
    for ax, (xlim, ylim, label_set) in zip(axes, (((60, 100.5), (20, 100.5), "repro"), ((96.8, 100.2), (85, 99), "zoom"))):
        for g in P.GROUPS:
            xs = [v[2] for v in pts.values() if v[0] == g]; ys = [v[1] for v in pts.values() if v[0] == g]
            mk, col = style[g]
            ax.scatter(xs, ys, s=22, marker=mk, color=col, edgecolors="white", linewidths=0.8, zorder=3, label=g)
        for name, (g, d, s) in pts.items():
            inside = xlim[0] <= s <= xlim[1] and ylim[0] <= d <= ylim[1]
            show = inside and ((label_set == "repro" and g.startswith("Reproduction") and "native" in name) or
                               (label_set == "zoom" and g in ("Conventional relay", "Dual-path instance", "Ablation")))
            if show:
                dx, dy, ha = LABEL_OFFSET.get(name, (3, 2, "left"))
                ax.annotate(name.replace(" (native)", ""), (s, d), xytext=(dx, dy), textcoords="offset points", fontsize=6, color=INK, ha=ha)
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        ax.set_xlabel("Security (%)"); ax.set_ylabel("Dependability (%)")
    axes[0].set_title("All methods", fontsize=7.5, color=INK, loc="left")
    axes[1].set_title("Zoom: conventional relays and dual-path instances", fontsize=7.5, color=INK, loc="left")
    axes[0].legend(loc="lower left", fontsize=6.2, handletextpad=0.3)
    save(fig, "fig_operating_points.pdf")


def fig_categories(M) -> None:
    show = ["LSTM, deployed", "Key's network", "1D-CNN", "Harmonic 87T, tuned"]
    cats = sorted({r["category"] for r in M[show[0]][1]}, key=lambda c: (0 if any(r["should_trip"] for r in M[show[0]][1] if r["category"] == c) else 1, c))
    fault = {c: any(r["should_trip"] for r in M[show[0]][1] if r["category"] == c) for c in cats}
    fig, ax = plt.subplots(figsize=(180 * MM, 92 * MM))
    h = 0.8 / len(show); y = np.arange(len(cats))
    for i, name in enumerate(show):
        rows = [r for r in M[name][1] if not r.get("undetectable")]
        v = [100 * np.mean([r["correct"] for r in rows if r["category"] == c]) for c in cats]
        ax.barh(y + (i - (len(show) - 1) / 2) * h, v, height=h * 0.86, color=SLOTS[i], label=name, zorder=3)
    ax.set_yticks(y, [f"{c} ({'fault' if fault[c] else 'no fault'})" for c in cats])
    lo = 50
    assert min(min(100 * np.mean([r["correct"] for r in M[n][1] if r["category"] == c and not r.get("undetectable")]) for c in cats) for n in show) >= lo, "a bar would be cut at the axis start"
    ax.invert_yaxis(); ax.set_xlim(lo, 100); ax.set_xlabel("Correct decisions (%, axis from 50 %): dependability for fault categories, security otherwise")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=len(show), loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.5)
    save(fig, "fig_categories.pdf")


def fig_operate_ecdf(M) -> None:
    show = [("LSTM, deployed", M["LSTM, deployed"][1]), ("Key's network", M["Key's network"][1]), ("1D-CNN", M["1D-CNN"][1]),
            ("Harmonic 87T, textbook (single pass)", P.harmonic_textbook_single_pass()), ("87T unrestrained", M["87T unrestrained"][1])]
    fig, ax = plt.subplots(figsize=(88 * MM, 62 * MM))
    for i, (name, rows) in enumerate(show):
        t = np.sort(P.operate_times(rows))
        ax.step(t, np.arange(1, len(t) + 1) / len(t), where="post", color=SLOTS[i], lw=1.4, label=name)
    ax.set_xlim(0, 60); ax.set_ylim(0, 1.0)
    ax.set_xlabel("Operate time (ms)"); ax.set_ylabel("Fraction of tripped faults")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.22), ncol=2, fontsize=6)
    save(fig, "fig_operate_ecdf.pdf")


def fig_plantb_paths() -> None:
    tpc = json.loads((P.ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "trip_path_check.json").read_text())
    kb = json.loads((P.BASE / "full" / "key_hybrid" / "final_plantB_main.json").read_text())["paths"]
    paths = [("highset", "High-set"), ("gate", "87T-gated"), ("solo", "AI-alone")]
    data = {"LSTM, deployed": (tpc["false_trip_first_path"], tpc["fault_first_path"]), "Key's network": (kb["false_trips"], kb["faults"])}
    fig, axes = plt.subplots(1, 2, figsize=(120 * MM, 52 * MM))
    w = 0.38; x = np.arange(len(paths))
    for ax, k, title in ((axes[0], 0, "False trips (healthy traces)"), (axes[1], 1, "Fault trips (first path)")):
        for i, (name, d) in enumerate(data.items()):
            v = [d[k].get(p, 0) for p, _ in paths]
            b = ax.bar(x + (i - 0.5) * w, v, width=w * 0.92, color=SLOTS[i], label=name, zorder=3)
            ax.bar_label(b, fontsize=6, padding=1, color=INK)
        ax.set_xticks(x, [lab for _, lab in paths]); ax.set_title(title, fontsize=7.5, loc="left", color=INK); ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Traces"); axes[0].legend(fontsize=6.2, loc="upper left")
    save(fig, "fig_plantb_paths.pdf")


def main() -> None:
    M = P.all_methods()
    fig_operating_points(M); fig_categories(M); fig_operate_ecdf(M); fig_plantb_paths()


if __name__ == "__main__":
    main()
