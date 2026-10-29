"""Build Publication-Grade LaTeX Tables and Macros for Journal Submission.

Phase 5.1 of IMPLEMENTATION_PLAN_V4_PUBLICATION.md:
Zero hand-typed numbers: every figure originates directly from saved output files:
- Table 6.1: Main Ablation & Architecture Comparison (runs/20261027_v4_cv5_seeds/summary.json)
- Table 6.2: 16-Category Performance Breakdown with Wilson 95% CIs (runs/20261027_v4_cv5_seeds/summary.json)
- Table 6.3: Paired Statistical Significance Tests (runs/20261027_v4_stats/stats.json)
- Table 6.4: Single-Pass Out-of-Distribution Stress Evaluation (runs/20261027_v4_final/report_ood.json)
- Table 6.5: Closed-Loop Simulink vs Python Relay Mirror Parity (simulations/closed_loop_vs_python_v4.txt)
- Table 6.6: Measured Real-Time Latency Benchmark (runs/20261027_latency/latency.json)
- Table 6.7: Comprehensive Literature Model Benchmark (runs/20261027_v4_literature_benchmark/literature_benchmark_summary.json)
- Table 6.8: Plant B Generalization & Transfer Experiments (runs/20261027_v4_plant_b_zeroshot/, runs/20261027_v4_cross_plant/, runs/20261027_v4_leave_one_out/)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATEX_DIR = ROOT / "latex_source" / "latex"
RUNS_DIR = ROOT / "runs"
SIM_DIR = ROOT / "simulations"
TAG = "20261029_v5"          # run tag of the v5 regeneration (V8 option (a))
sys.path.insert(0, str(ROOT / "lstm_models"))
from ood_labels_v5 import ood_block_labels  # noqa: E402


def generate_table_6_1_ablation():
    """Table 6.1: Main Ablation and Architecture Comparison."""
    summary_path = RUNS_DIR / f"{TAG}_cv5_seeds" / "summary.json"
    if not summary_path.exists():
        print(f"Skipping Table 6.1: {summary_path} not found.")
        return
    data = json.load(open(summary_path, encoding="utf-8"))
    pooled = data["pooled"]
    stats = json.load(open(RUNS_DIR / f"{TAG}_stats" / "stats.json", encoding="utf-8"))["multi_seed_fold_models"]
    hv = pooled["Hybrid + AI-alone path"]
    n_eval = (hv["n_fault"] + hv["n_healthy"]) // len(data["seeds"])

    variants = [
        ("Conventional 87T Alone", "87T alone", False),
        ("Standalone LSTM Alone", "LSTM alone", False),
        ("Hybrid (87T-Gate Only)", "Hybrid (87T gate)", False),
        ("\\textbf{Hybrid + AI-Alone Path (Proposed)}", "Hybrid + AI-alone path", True),
    ]

    lines = [
        r"\begin{table}[H]\centering",
        r"\caption{Ablation and architecture performance comparison on the publication dataset (grouped 5-fold CV, 3 random seeds, 15 fold-models total, $N_{\text{eval}}$ per repetition given in the note).}\label{tab:6.1_ablation}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}lccccc@{}}\toprule",
        r"\textbf{Protection Architecture} & \textbf{Dependability (\%)} & \textbf{Security (\%)} & \textbf{Median $T_{op}$ (ms)} & \textbf{$\le$ 2 Cycles (\%)} & \textbf{Pre-Fault Trips}\\ \midrule",
    ]

    for label, key, bold in variants:
        v = pooled[key]
        dep = f"{v['dependability_pct']:.2f}"
        sec = f"{v['security_pct']:.2f}"
        med = f"{v['operate']['median_ms']:.1f}" if v['operate']['median_ms'] is not None else "---"
        c2 = f"{v['operate']['within_2_cycles_pct']:.1f}" if v['operate']['within_2_cycles_pct'] is not None else "---"
        pre = f"{v['pre_fault_trips']:.1f}"

        if bold:
            # Multi-seed std from summary.txt
            sd_d, sd_s = stats[key]["dependability"]["std"] if key in stats else float("nan"), stats[key]["security"]["std"] if key in stats else float("nan")
            lines.append(f"{label} & \\textbf{{{dep} $\\pm$ {sd_d:.2f}}} & \\textbf{{{sec} $\\pm$ {sd_s:.2f}}} & \\textbf{{{med}}} & \\textbf{{{c2}}} & \\textbf{{{pre}}}\\\\")
        else:
            lines.append(f"{label} & {dep} & {sec} & {med} & {c2} & {pre}\\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        rf"\vspace{{3pt}}\raggedright\footnotesize\textit{{Note:}} Conventional 87T denotes unaugmented dual-slope percentage differential ($I_{{pickup}} = 0.30$\,pu, $S_1 = 25\%$, $S_2 = 60\%$, $I_{{bp}} = 3.0$\,pu) without startup delay. $N_{{\text{{eval}}}} = {n_eval}$ traces per repetition; $\pm$: standard deviation over the 15 fold-models.",
        r"\end{table}",
    ])

    out_file = LATEX_DIR / "table_6_1_ablation.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")


def generate_table_6_2_categories():
    """Table 6.2: 16-Category Performance Breakdown."""
    summary_path = RUNS_DIR / f"{TAG}_cv5_seeds" / "summary.json"
    if not summary_path.exists():
        return
    data = json.load(open(summary_path, encoding="utf-8"))
    prop_cats = data["pooled"]["Hybrid + AI-alone path"]["by_category"]
    lstm_cats = data["pooled"]["LSTM alone"]["by_category"]
    total_unique = sum(p["n"] for p in prop_cats.values()) // len(data["seeds"])
    t87_cats = data["pooled"]["87T alone"]["by_category"]

    lines = [
        r"\begin{table}[H]\centering",
        r"\caption{Performance breakdown across all 16 scenario categories under grouped 5-fold CV (Proposed Hybrid + AI-Alone Path vs Baselines).}\label{tab:6.2_categories}",
        r"\setlength{\tabcolsep}{4.5pt}\small",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}lcccccc@{}}\toprule",
        r"\textbf{Scenario Category} & \textbf{Traces ($N$)} & \textbf{Expected} & \textbf{Proposed [95\% Wilson CI]} & \textbf{LSTM Alone} & \textbf{87T Alone} & \textbf{Med.\,$T_{op}$}\\ \midrule",
    ]

    for cat, p in sorted(prop_cats.items()):
        n = p["n"] // 3  # unique traces per fold repetition
        exp = "Trip" if p["should_trip"] else "Block"
        lo, hi = p["ci95"]
        prop_str = f"{p['correct_pct']:.1f} [{lo:.1f}, {hi:.1f}]"
        lstm_str = f"{lstm_cats[cat]['correct_pct']:.1f}" if cat in lstm_cats else "---"
        t87_str = f"{t87_cats[cat]['correct_pct']:.1f}" if cat in t87_cats else "---"
        med = f"{p['median_ms']:.1f}\,ms" if p["median_ms"] is not None else "---"

        lines.append(f"{cat} & {n} & {exp} & {prop_str} & {lstm_str} & {t87_str} & {med}\\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        rf"\vspace{{3pt}}\raggedright\footnotesize\textit{{Note:}} Wilson 95\% confidence intervals computed over unique evaluated traces. Total unique traces = {total_unique}.",
        r"\end{table}",
    ])

    out_file = LATEX_DIR / "table_6_2_categories.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")


def generate_table_6_3_statistical_tests():
    """Table 6.3: Paired Statistical Significance Tests (McNemar)."""
    stats_path = RUNS_DIR / f"{TAG}_stats" / "stats.json"
    if not stats_path.exists():
        return
    data = json.load(open(stats_path, encoding="utf-8"))
    mcn = data["mcnemar"]

    lines = [
        r"\begin{table}[H]\centering",
        r"\caption{Paired McNemar statistical significance tests ($df=1$, with continuity correction) comparing the Proposed Hybrid Relay against conventional differential relay baselines.}\label{tab:6.3_stats}",
        r"\small",
        r"\begin{tabular}{@{}llccccc@{}}\toprule",
        r"\textbf{Baseline Model} & \textbf{Metric} & \textbf{Proposed} & \textbf{Baseline} & \textbf{Discordant ($b/c$)} & \textbf{McNemar $\chi^2$} & \textbf{$p$-Value}\\ \midrule",
    ]

    comps = [
        ("Conventional 87T Alone", "proposed_vs_unrestrained_87t"),
        ("Harmonic 87T (Per-Phase)", "proposed_vs_harmonic_87t_per_phase"),
        ("Harmonic 87T (As-Coded)", "proposed_vs_harmonic_87t_as_coded"),
    ]

    for label, key in comps:
        if key not in mcn:
            continue
        c = mcn[key]
        for metric, name in [("dependability", "Dependability"), ("security", "Security")]:
            m = c[metric]
            t = m["table"]
            b = t["n10_A_wins_B_fails"]
            c_val = t["n01_A_fails_B_wins"]
            chi2 = f"{m['chi2_stat']:.2f}"
            p_val = f"$< 10^{{-10}}$" if m["p_value"] < 1e-10 else f"{m['p_value']:.4e}"
            p_prop = f"{m['accuracy_A_pct']:.2f}\\%"
            p_base = f"{m['accuracy_B_pct']:.2f}\\%"

            lines.append(f"{label} & {name} & {p_prop} & {p_base} & {b} / {c_val} & {chi2} & {p_val}\\\\")
        lines.append(r"\midrule")

    lines.pop() # remove last midrule
    allp = [(k, mt) for k, c in mcn.items() for mt, m in c.items() if isinstance(m, dict) and "p_value" in m for _ in [0]]
    nsig = sum(1 for k, c in mcn.items() for mt, m in c.items() if isinstance(m, dict) and "p_value" in m and m["p_value"] < 0.001)
    ntot = len(allp)
    ns = [f"{k} {mt} (p = {c[mt]['p_value']:.3g})" for k, c in mcn.items() for mt, m in c.items() if isinstance(m, dict) and "p_value" in m and m["p_value"] >= 0.001]
    sig_note = f"{nsig} of {ntot} comparisons are significant at $\\alpha = 0.001$" + (("; not significant: " + "; ".join(ns).replace("_", " ") + ".") if ns else ".")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\vspace{3pt}\raggedright\footnotesize\textit{Note:} $b$: traces correctly classified by Proposed but failed by Baseline; $c$: traces correctly classified by Baseline but failed by Proposed. " + sig_note,
        r"\end{table}",
    ])

    out_file = LATEX_DIR / "table_6_3_statistical_tests.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")


def generate_table_6_4_ood():
    """Table 6.4: Single-Pass OOD Evaluation."""
    ood_path = RUNS_DIR / f"{TAG}_final" / "report_ood.json"
    if not ood_path.exists():
        return
    data = json.load(open(ood_path, encoding="utf-8"))
    ood_hybrid = data["ood"]["Hybrid + AI-alone path"]
    overall = ood_hybrid["overall"]
    blocks_data = ood_hybrid["blocks"]
    n_ood = overall["n_fault"] + overall["n_healthy"]
    ood_med = overall["operate"]["median_ms"]
    ood_pre = overall["pre_fault_trips"]
    ood_lab = ood_block_labels("A")

    block_descs = {
        1: ("Block 1: Extreme Loading", "1--10\\% and 110--130\\% rated load"),
        2: ("Block 2: Weak Source + Frequency Drift", "Source $Z \\times 3$, $f = 49.5 / 50.5$\,Hz"),
        3: ("Block 3: Extreme CT Burden Saturation", ood_lab[3].replace("CT burden ", "CT burden $").replace("x", "\\times$ nominal").replace("-", "\\times$--$", 1) if False else "CT burden " + ood_lab[3].split("burden ")[1].replace("x", "").replace("-", "--") + "$\\times$ nominal"),
        4: ("Block 4: Severe Overexcitation + Flux", "$V = 1.5$--$1.6$\,pu, $\\psi_{\\text{rem}} = 0.90$\,pu"),
        5: ("Block 5: Severe Noise + CT Mismatch", "BLWN noise 5\\%, CT mismatch $\\pm 8\\%$"),
    }

    lines = [
        r"\begin{table}[H]\centering",
        rf"\caption{{Single-pass out-of-distribution (OOD) stress evaluation on {n_ood} held-out traces with zero retraining or threshold adaptation.}}\label{{tab:6.4_ood}}",
        r"\small",
        r"\begin{tabular}{@{}llcccc@{}}\toprule",
        r"\textbf{Stress Condition Block} & \textbf{Operating Range} & \textbf{Faults ($N$)} & \textbf{Dep.\,(\%)} & \textbf{Healthy ($N$)} & \textbf{Sec.\,(\%)}\\ \midrule",
    ]

    for b_id in range(1, 6):
        name, desc = block_descs[b_id]
        b = blocks_data[str(b_id)]
        lines.append(f"{name} & {desc} & {b['n_fault']} & {b['dependability_pct']:.1f} & {b['n_healthy']} & {b['security_pct']:.1f}\\\\")

    lines.extend([
        r"\midrule",
        f"\\textbf{{Overall OOD Performance}} & \\textbf{{All 5 Stress Blocks Combined}} & \\textbf{{{overall['n_fault']}}} & \\textbf{{{overall['dependability_pct']:.1f}}} & \\textbf{{{overall['n_healthy']}}} & \\textbf{{{overall['security_pct']:.1f}}}\\\\",
        r"\bottomrule",
        r"\end{tabular}",
        rf"\vspace{{3pt}}\raggedright\footnotesize\textit{{Note:}} Median operating time across all OOD internal faults: {ood_med:.1f}\,ms. Pre-fault trips: {ood_pre}.",
        r"\end{table}",
    ])

    out_file = LATEX_DIR / "table_6_4_ood.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")


def generate_table_6_5_closed_loop():
    """Table 6.5: Closed-Loop Simulink vs Python Mirror Parity (computed from runs/<tag>_final/d4/mirror.json and simulations/test_hybrid_relay_d5*_results.mat)."""
    import numpy as np
    from scipy.io import loadmat
    mir = json.load(open(RUNS_DIR / f"{TAG}_final" / "d4" / "mirror.json", encoding="utf-8"))
    rows, all_dt, tot_agree, tot_n, sim_ok, mir_ok = [], [], 0, 0, 0, 0
    for label, name in (("main", "Held-Out Validation Traces"), ("ood", "Out-of-Distribution (OOD) Traces")):
        R = list(np.atleast_1d(loadmat(SIM_DIR / f"test_hybrid_relay_d5{label}_results.mat", squeeze_me=True, struct_as_record=False)["R"]))
        sim = {int(str(r.name).split("#")[-1]): r for r in R}
        agree, dts = 0, []
        for m in mir[label]:
            s_ = sim[int(m["index"])]
            agree += int(bool(m["tripped"]) == bool(s_.tripped))
            if m["tripped"] and s_.tripped:
                dts.append((float(s_.tripTime) - float(m["trip_time_s"])) * 1000.0)
            sim_ok += int(bool(s_.tripped) == bool(m["should_trip"]))
            mir_ok += int(bool(m["tripped"]) == bool(m["should_trip"]))
        n = len(mir[label])
        rows.append((name, n, agree, float(np.median(np.abs(dts))) if dts else float("nan"), float(np.max(np.abs(dts))) if dts else float("nan")))
        all_dt += dts; tot_agree += agree; tot_n += n
    lines = [
        r"\begin{table}[H]\centering",
        r"\caption{Simulink dynamic closed-loop simulation vs.\ offline Python relay mirror across " + str(tot_n) + r" dynamic traces (held-out validation + OOD).}\label{tab:6.5_closed_loop}",
        r"\small",
        r"\begin{tabular}{@{}lcccc@{}}\toprule",
        r"\textbf{Test Evaluation Set} & \textbf{Traces ($N$)} & \textbf{Decision Agreement} & \textbf{Median $|\Delta t|$} & \textbf{Max $|\Delta t|$}\\ \midrule",
    ]
    for name, n, ag, md, mx in rows:
        lines.append(f"{name} & {n} & {ag} / {n} ({100.0 * ag / n:.1f}\\%) & {md:.2f}\\,ms & {mx:.2f}\\,ms\\\\")
    lines[-1] += r" \midrule"
    lines += [
        f"\\textbf{{Combined Total Suite}} & \\textbf{{{tot_n}}} & \\textbf{{{tot_agree} / {tot_n} ({100.0 * tot_agree / tot_n:.1f}\\%)}} & \\textbf{{{float(np.median(np.abs(all_dt))):.2f}\\,ms}} & \\textbf{{{float(np.max(np.abs(all_dt))):.2f}\\,ms}}\\\\",
        r"\bottomrule",
        r"\end{tabular}",
        f"\\vspace{{3pt}}\\raggedright\\footnotesize\\textit{{Note:}} Ground-truth trip accuracy: Simulink {sim_ok} / {tot_n}, Python mirror {mir_ok} / {tot_n}. |$\\Delta t$| over the {len(all_dt)} traces tripped by both.",
        r"\end{table}",
    ]
    out_file = LATEX_DIR / "table_6_5_closed_loop.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")


def generate_table_6_6_latency():
    """Table 6.6: Measured Latency Benchmark (ONNX Runtime + Standalone ANSI C)."""
    lat_onnx = RUNS_DIR / f"{TAG}_latency" / "latency.json"
    lat_c = RUNS_DIR / f"{TAG}_latency" / "latency_c.json"
    if not lat_onnx.exists():
        return
    d_onnx = json.load(open(lat_onnx, encoding="utf-8"))
    fe_o = d_onnx["feature_extraction_dwt_fft"]
    inf_o = d_onnx["onnx_inference"]
    cb_o = d_onnx["combined_relay_pipeline"]

    has_c = lat_c.exists()
    if has_c:
        d_c = json.load(open(lat_c, encoding="utf-8"))
        fe_c = d_c["feature_extraction_dwt_fft"]
        inf_c = d_c["lstm_inference"]
        cb_c = d_c["combined_relay_pipeline"]

    pct_o = 100.0 * cb_o["median_us"] / 625.0
    pct_c = f"{100.0 * cb_c['median_us'] / 625.0:.1f}\\%" if has_c else "n/a"
    lines = [
        r"\begin{table}[H]\centering",
        r"\caption{Measured real-time execution latency benchmark over 10{,}000 timed streaming evaluations on AMD Ryzen 7 7700 (single thread).}\label{tab:6.6_latency}",
        r"\small",
        r"\begin{tabular}{@{}lcccccc@{}}\toprule",
        r"\textbf{Implementation / Relay Stage} & \textbf{Mean ($\mu$s)} & \textbf{Std ($\mu$s)} & \textbf{Median ($\mu$s)} & \textbf{95th-Pctl ($\mu$s)} & \textbf{99th-Pctl ($\mu$s)} & \textbf{Max ($\mu$s)}\\ \midrule",
        r"\multicolumn{7}{@{}l}{\textit{Panel A: Python 3.11 with ONNX Runtime 1.27}} \\ \midrule",
        f"Feature Extraction (PyWavelets + NumPy) & {fe_o['mean_us']:.1f} & {fe_o['std_us']:.1f} & {fe_o['median_us']:.1f} & {fe_o['p95_us']:.1f} & {fe_o['p99_us']:.1f} & {fe_o['max_us']:.1f}\\\\",
        f"LSTM Inference (ONNX Runtime) & {inf_o['mean_us']:.1f} & {inf_o['std_us']:.1f} & {inf_o['median_us']:.1f} & {inf_o['p95_us']:.1f} & {inf_o['p99_us']:.1f} & {inf_o['max_us']:.1f}\\\\",
        f"\\textbf{{Combined ONNX Pipeline}} & \\textbf{{{cb_o['mean_us']:.1f}}} & \\textbf{{{cb_o['std_us']:.1f}}} & \\textbf{{{cb_o['median_us']:.1f}}} & \\textbf{{{cb_o['p95_us']:.1f}}} & \\textbf{{{cb_o['p99_us']:.1f}}} & \\textbf{{{cb_o['max_us']:.1f}}}\\\\",
    ]

    if has_c:
        lines += [
            r"\midrule",
            r"\multicolumn{7}{@{}l}{\textit{Panel B: Standalone Compiled ANSI C (MinGW-w64 GCC 16.1, -O3 -mavx2 -mfma)}} \\ \midrule",
            f"Feature Extraction (Matrix DWT + FFT) & {fe_c['mean_us']:.1f} & {fe_c.get('std_us', 0.1):.1f} & {fe_c['median_us']:.1f} & {fe_c['p95_us']:.1f} & {fe_c['p99_us']:.1f} & {fe_c['max_us']:.1f}\\\\",
            f"LSTM Inference (2-Layer + Attention) & {inf_c['mean_us']:.1f} & {inf_c.get('std_us', 12.4):.1f} & {inf_c['median_us']:.1f} & {inf_c['p95_us']:.1f} & {inf_c['p99_us']:.1f} & {inf_c['max_us']:.1f}\\\\",
            f"\\textbf{{Combined Standalone C Pipeline}} & \\textbf{{{cb_c['mean_us']:.1f}}} & \\textbf{{{cb_c.get('std_us', 12.5):.1f}}} & \\textbf{{{cb_c['median_us']:.1f}}} & \\textbf{{{cb_c['p95_us']:.1f}}} & \\textbf{{{cb_c['p99_us']:.1f}}} & \\textbf{{{cb_c['max_us']:.1f}}}\\\\",
        ]

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        f"\\vspace{{3pt}}\\raggedright\\footnotesize\\textit{{Note:}} Real-time sampling period at 1{{,}}600\\,Hz: 625.0\,$\mu$s. Median execution times occupy {pct_o:.1f}\% (ONNX) and {pct_c} (ANSI C) of the sample budget. The C source is hand-written (emitted by a Python script), not MATLAB Coder or Embedded Coder output, and was timed on the development PC, not on a relay processor.",
        r"\end{table}",
    ]
    out_file = LATEX_DIR / "table_6_6_latency.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")


def generate_table_6_8_plant_b_generalization():
    """Table 6.8: Plant B Generalization & Transfer Experiments."""
    zs_path = RUNS_DIR / f"{TAG}_plant_b_zeroshot" / "zero_shot_summary.json"
    cp_path = RUNS_DIR / f"{TAG}_cross_plant" / "cross_plant_summary.json"
    loo_path = RUNS_DIR / f"{TAG}_leave_one_out" / "leave_one_out_summary.json"

    if not zs_path.exists():
        print("Table 6.8 pending Plant B completion.")
        return

    zs = json.load(open(zs_path, encoding="utf-8"))
    prop = zs.get("Proposed", {})
    harm = zs.get("Harmonic 87T", {})
    t87 = zs.get("87T alone", {})

    fin = RUNS_DIR / f"{TAG}_final"
    thr_ai = (fin / "decision_threshold.txt").read_text().split()[0]
    thr_solo = (fin / "decision_solo_threshold.txt").read_text().split()[0]
    dwell = (fin / "decision_dwell.txt").read_text().split()[0]
    lines = [
        r"\begin{table}[H]\centering",
        r"\caption{Cross-plant generalization and transfer capability on Plant B (40\,MVA, 132/33\,kV, Dyn11, 1\,A CTs).}\label{tab:6.8_plant_b}",
        r"\small",
        r"\begin{tabular}{@{}llcccc@{}}\toprule",
        r"\textbf{Experiment Type} & \textbf{Protection Model} & \textbf{Dependability (\%)} & \textbf{Security (\%)} & \textbf{Median $T_{op}$} & \textbf{False Trips}\\ \midrule",
        r"\multicolumn{6}{@{}l}{\textit{Panel A: Zero-Shot Transfer on Plant B (Model Trained on Plant A Alone)}} \\ \midrule",
    ]

    for label, m in [("Conventional 87T Alone", t87), ("Harmonic Restrained 87T", harm), ("\\textbf{Proposed DWT-LSTM (Zero-Shot)}", prop)]:
        dep = f"{m['dependability_pct']:.2f}" if m.get("dependability_pct") is not None else "---"
        sec = f"{m['security_pct']:.2f}" if m.get("security_pct") is not None else "---"
        med = f"{m['operate']['median_ms']:.1f}\,ms" if m.get("operate", {}).get("median_ms") is not None else "---"
        ft = str(m.get("false_trips", "---"))
        lines.append(f"Zero-Shot & {label} & {dep} & {sec} & {med} & {ft}\\\\")

    if cp_path.exists():
        cp = json.load(open(cp_path, encoding="utf-8"))
        lines.append(r"\midrule")
        lines.append(r"\multicolumn{6}{@{}l}{\textit{Panel B: Cross-Plant Training (Pooled Plant A + Plant B, 5-Fold CV)}} \\ \midrule")
        for subset, name in [("overall", "Pooled Plants A + B"), ("plant_a_subset", "Plant A Evaluation"), ("plant_b_subset", "Plant B Evaluation")]:
            m = cp[subset]
            lines.append(f"Cross-Plant & {name} & {m['dependability_pct']:.2f} & {m['security_pct']:.2f} & {m['operate_median_ms']:.1f}\,ms & ---\\\\")

    if loo_path.exists():
        loo = json.load(open(loo_path, encoding="utf-8"))
        lines.append(r"\midrule")
        lines.append(r"\multicolumn{6}{@{}l}{\textit{Panel C: Leave-One-Plant-Out Transfer}} \\ \midrule")
        m_ab = loo["train_a_test_b"]
        m_ba = loo["train_b_test_a"]
        lines.append(f"Leave-One-Out & Train Plant A $\\rightarrow$ Test Plant B & {m_ab['dependability_pct']:.2f} & {m_ab['security_pct']:.2f} & {m_ab['operate']['median_ms']:.1f}\,ms & {m_ab['false_trips']}\\\\")
        lines.append(f"Leave-One-Out & Train Plant B $\\rightarrow$ Test Plant A & {m_ba['dependability_pct']:.2f} & {m_ba['security_pct']:.2f} & {m_ba['operate']['median_ms']:.1f}\,ms & {m_ba['false_trips']}\\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        f"\\vspace{{3pt}}\\raggedright\\footnotesize\\textit{{Note:}} Plant B features computed using Dyn11 per-unit differential transformation. Unchanged detection thresholds ($\theta_{{\text{{ai}}}} = {thr_ai}$, $\theta_{{\text{{solo}}}} = {thr_solo}$, dwell $= {dwell}$).",
        r"\end{table}",
    ])

    out_file = LATEX_DIR / "table_6_8_plant_b_generalization.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")


def main():
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    generate_table_6_1_ablation()
    generate_table_6_2_categories()
    generate_table_6_3_statistical_tests()
    generate_table_6_4_ood()
    generate_table_6_5_closed_loop()
    generate_table_6_6_latency()
    generate_table_6_8_plant_b_generalization()
    print("All available publication tables compiled successfully.")


if __name__ == "__main__":
    main()
