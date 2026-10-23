"""E1: thesis results tables, generated ONLY from saved output files (no hand-typed numbers).

    python lstm_models/make_tables_v3.py      -> documents/results_v3/tables.md (+ CSVs)

Sources: runs/20261021_v3_cv5*/cv_summary.json (C2/C3, C6), runs/20261021_v3data_baseline/baseline.json (C1), runs/20261022_v3_final/report_ood.json (C5),
         simulations/test_hybrid_relay_v3_results.mat (D3), simulations/closed_loop_vs_python_v3.txt (D4), runs/20261021_v3_cv5/hiz_by_bin.txt.
Per-category intervals are Wilson 95 % intervals of ONE repetition (seed 20261021: every trace tested once); the other columns are the 3-seed mean and worst seed
(the three repetitions test the same traces, so their decisions are not independent and are not pooled).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "documents" / "results_v3"
CV = [ROOT / "runs" / n for n in ("20261021_v3_cv5", "20261021_v3_cv5_seed20261022", "20261021_v3_cv5_seed20261023")]
VARIANTS = ("87T alone", "LSTM alone", "Hybrid (87T gate)", "Hybrid + AI-alone path")


def md_table(head: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cv = [json.loads((d / "cv_summary.json").read_text(encoding="utf-8")) for d in CV]
    base = json.loads((ROOT / "runs" / "20261021_v3data_baseline" / "baseline.json").read_text(encoding="utf-8"))
    ood = json.loads((ROOT / "runs" / "20261022_v3_final" / "report_ood.json").read_text(encoding="utf-8"))
    T: list[str] = ["# Results tables (generated from saved files by lstm_models/make_tables_v3.py)", ""]

    # ---- Table 1: ablation / main result
    rows = []
    for v in VARIANTS:
        dep = np.array([r["pooled"][v]["dependability_pct"] for r in cv]); sec = np.array([r["pooled"][v]["security_pct"] for r in cv])
        o = [r["pooled"][v]["operate"] for r in cv]
        mm = lambda k: np.mean([x[k] for x in o])
        rows.append([v, f"{dep.mean():.2f} ({dep.std(ddof=1):.2f})", f"{sec.mean():.2f} ({sec.std(ddof=1):.2f})", f"{mm('median_ms'):.1f}", f"{mm('within_2_cycles_pct'):.1f}",
                     f"{np.mean([r['pooled'][v]['pre_fault_trips'] for r in cv]):.1f}"])
    T += ["## Table 1 - Ablation and main result (grouped 5-fold CV, 3 repetitions, 3,218 traces each tested once per repetition)", "",
          "Mean (sd across the 3 repetitions) of the pooled out-of-fold decisions. Undetectable faults (< 0.05 pu, 94 traces) excluded.", "",
          md_table(["variant", "dependability %", "security %", "operate median ms", "within 2 cycles %", "pre-fault trips"], rows), ""]

    # ---- Table 2: per category
    cats = sorted(cv[0]["pooled"]["Hybrid + AI-alone path"]["by_category"])
    rows, csvrows = [], []
    for c in cats:
        b0 = cv[0]["pooled"]["Hybrid + AI-alone path"]["by_category"][c]
        vals = [r["pooled"]["Hybrid + AI-alone path"]["by_category"][c]["correct_pct"] for r in cv]
        lm = [r["pooled"]["LSTM alone"]["by_category"][c]["correct_pct"] for r in cv]
        t87 = [r["pooled"]["87T alone"]["by_category"][c]["correct_pct"] for r in cv]
        rows.append([c, b0["n"], "trip" if b0["should_trip"] else "no trip", f"{b0['correct_pct']:.1f} [{b0['ci95'][0]:.1f}, {b0['ci95'][1]:.1f}]", f"{np.mean(vals):.1f}", f"{np.min(vals):.1f}", f"{np.mean(lm):.1f}", f"{np.mean(t87):.1f}"])
        csvrows.append(rows[-1])
    T += ["## Table 2 - Per scenario category (hybrid + AI-alone path)", "",
          "Correct = trip after the measured onset (faults) or no trip (healthy). 95 % Wilson interval from repetition 1; mean and worst repetition over the 3 repetitions; LSTM-alone and 87T-alone means for comparison.", "",
          md_table(["category", "n", "expected", "correct % [95 % CI] (rep. 1)", "mean 3 rep.", "worst rep.", "LSTM alone mean", "87T alone mean"], rows), ""]
    with open(OUT / "table2_per_category.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["category", "n", "expected", "correct_ci_rep1", "mean3", "worst", "lstm_alone_mean", "t87_alone_mean"]); w.writerows(csvrows)

    # ---- Table 3: C1 baseline vs retrained
    b = base["main"]
    rows = []
    for v in ("87T alone", "Hybrid (87T gate)", "Hybrid + AI-alone path"):
        rows.append([f"deployed v2-trained model, {v}", f"{b[v]['dependability_pct']:.1f}", f"{b[v]['security_pct']:.1f}", b[v]["missed"], b[v]["false_trips"]])
    h = [r["pooled"]["Hybrid + AI-alone path"] for r in cv]
    rows.append(["retrained, hybrid + AI-alone (CV mean)", f"{np.mean([x['dependability_pct'] for x in h]):.1f}", f"{np.mean([x['security_pct'] for x in h]):.1f}", f"{np.mean([x['missed'] for x in h]):.0f}", f"{np.mean([x['false_trips'] for x in h]):.0f}"])
    T += ["## Table 3 - Effect of retraining on the realistic v3 data (C1 vs C2)", "",
          "The deployed model was trained on the light-load v2 data and is scored on all 3,218 v3 traces without retraining (so it has seen none of the new stress cases); the retrained numbers are out-of-fold.", "",
          md_table(["model / variant", "dependability %", "security %", "missed", "false trips"], rows), ""]
    cat_rows = []
    for c in cats:
        bb = b["Hybrid + AI-alone path"]["by_category"].get(c)
        if bb:
            cat_rows.append([c, f"{bb['correct_pct']:.1f}", f"{np.mean([r['pooled']['Hybrid + AI-alone path']['by_category'][c]['correct_pct'] for r in cv]):.1f}"])
    T += [md_table(["category", "deployed model %", "retrained (CV mean) %"], cat_rows), ""]

    # ---- Table 4: OOD
    O = ood["ood"]
    rows = [[v, f"{O[v]['overall']['dependability_pct']:.1f}", f"{O[v]['overall']['security_pct']:.1f}", O[v]["overall"]["missed"], O[v]["overall"]["false_trips"]] for v in VARIANTS]
    T += ["## Table 4 - Out-of-distribution set (300 traces, scored once, final model)", "", md_table(["variant", "dependability %", "security %", "missed", "false trips"], rows), ""]
    names = {"1": "extreme load (1-10 %, 110-130 %)", "2": "weak source 3x + 49.5/50.5 Hz", "3": "CT burden 12-16x", "4": "over-excitation 1.5-1.6 pu + flux 0.9 pu", "5": "noise 5 % + CT mismatch +/-8 %"}
    rows = []
    for k, label in names.items():
        sb = O["Hybrid + AI-alone path"]["blocks"][k]
        rows.append([k, label, sb["n_fault"], f"{sb['dependability_pct']:.1f}", sb["n_healthy"], f"{sb['security_pct']:.1f}"])
    T += [md_table(["block", "content", "faults", "dependability %", "healthy", "security %"], rows), ""]

    # ---- Table 5: closed loop D3
    try:
        R = np.atleast_1d(loadmat(ROOT / "simulations" / "test_hybrid_relay_v3_results.mat", squeeze_me=True, struct_as_record=False)["R"])
        rows = [[r.name, "TRIP" if r.expectTrip else "BLOCK", "TRIP" if r.tripped else "BLOCK", f"{r.maxProb:.4f}", "-" if not r.tripped else f"{r.delayMs:.1f}", "PASS" if r.passed else "FAIL"] for r in R]
        T += ["## Table 5 - Extended closed-loop benchmark (Simulink, LSTM active, 12 cases)", "", md_table(["case", "expected", "actual", "LSTM max prob", "trip delay ms", "status"], rows), ""]
    except Exception as e:
        T += [f"(D3 results not available: {e})", ""]
    p = ROOT / "simulations" / "closed_loop_vs_python_v3.txt"
    if p.is_file():
        txt = p.read_text(encoding="utf-8")
        T += ["## Table 6 - Closed-loop vs Python mirror (D4)", "", "```", txt.split("\n\n")[-1], "```", "", "Per-trace comparison:", "", "```", "\n\n".join(txt.split("\n\n")[:-1]), "```", ""]
    hz = ROOT / "runs" / "20261021_v3_cv5" / "hiz_by_bin.txt"
    if hz.is_file():
        T += ["## Table 7 - Internal HiZ faults by Rf bin (repetition 1)", "", "```", hz.read_text(encoding="utf-8"), "```", ""]
    (OUT / "tables.md").write_text("\n".join(T), encoding="utf-8")
    print("\n".join(T)[:3000])


if __name__ == "__main__":
    main()
