"""C3: aggregate several grouped-CV runs (different seeds) into mean +/- sd over all fold models, plus per-category spread.

    python lstm_models/summarize_cv_seeds.py runs/20261021_v3_cv5 runs/20261021_v3_cv5_seed20261022 runs/20261021_v3_cv5_seed20261023 --out runs/20261021_v3_cv5_seeds
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

VARIANTS = ("87T alone", "LSTM alone", "Hybrid (87T gate)", "Hybrid + AI-alone path")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs = [json.loads((Path(r) / "cv_summary.json").read_text(encoding="utf-8")) for r in a.runs]
    L = [f"Repeatability: {len(runs)} CV runs x {len(runs[0]['folds'])} folds = {sum(len(r['folds']) for r in runs)} models; each run tests every trace once", "=" * 100, ""]
    L.append("Headline metrics of the pooled out-of-fold decisions, per seed:")
    L.append(f"{'variant':26s} " + " | ".join(f"seed {Path(r).name[-8:]:>8s} dep/sec" for r in a.runs) + " | mean dep / sec  (sd across seeds)")
    for v in VARIANTS:
        dep = [r["pooled"][v]["dependability_pct"] for r in runs]; sec = [r["pooled"][v]["security_pct"] for r in runs]
        L.append(f"{v:26s} " + " | ".join(f"{d:8.2f} / {s:6.2f}" for d, s in zip(dep, sec)) + f" | {np.mean(dep):.2f} ({np.std(dep, ddof=1):.2f}) / {np.mean(sec):.2f} ({np.std(sec, ddof=1):.2f})")
    L += ["", "Per fold-model (all models), hybrid + AI-alone path:"]
    for key in ("dependability_pct", "security_pct"):
        v = np.array([f["variants"]["Hybrid + AI-alone path"][key] for r in runs for f in r["folds"]])
        L.append(f"  {key:18s} mean {v.mean():.2f}  sd {v.std(ddof=1):.2f}  min {v.min():.2f}  max {v.max():.2f}  (n = {len(v)} models)")
    ms = np.array([r["pooled"]["Hybrid + AI-alone path"]["operate"]["median_ms"] for r in runs])
    w2 = np.array([r["pooled"]["Hybrid + AI-alone path"]["operate"]["within_2_cycles_pct"] for r in runs])
    pre = [r["pooled"]["Hybrid + AI-alone path"]["pre_fault_trips"] for r in runs]
    L.append(f"  operate median {ms.mean():.1f} ms (sd {ms.std(ddof=1):.2f}); within 2 cycles {w2.mean():.1f} % (sd {w2.std(ddof=1):.2f}); pre-fault trips per seed {pre}")
    th = [(f["settings"]["Hybrid + AI-alone path"]["ai_threshold"], f["settings"]["Hybrid + AI-alone path"]["solo_threshold"]) for r in runs for f in r["folds"]]
    ai = np.array([t[0] for t in th]); so = np.array([t[1] for t in th])
    lg = lambda x: np.log(x / (1 - x))
    L.append(f"  thresholds over {len(th)} models: AI {ai.min():.3f}-{ai.max():.3f} (logit sd {lg(ai).std(ddof=1):.2f}), solo {so.min():.3f}-{so.max():.3f} (logit sd {lg(so).std(ddof=1):.2f})")
    L += ["", "Per category, hybrid + AI-alone path: correct % per seed, mean, worst seed:"]
    cats = sorted({c for r in runs for c in r["pooled"]["Hybrid + AI-alone path"]["by_category"]})
    for c in cats:
        vals = [r["pooled"]["Hybrid + AI-alone path"]["by_category"][c]["correct_pct"] for r in runs if c in r["pooled"]["Hybrid + AI-alone path"]["by_category"]]
        n = runs[0]["pooled"]["Hybrid + AI-alone path"]["by_category"][c]["n"]
        L.append(f"  {c:20s} n={n:4d}  " + "  ".join(f"{x:6.1f}" for x in vals) + f"   mean {np.mean(vals):6.1f}  min {np.min(vals):6.1f}")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
