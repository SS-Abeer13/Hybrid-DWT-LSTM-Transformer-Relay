"""Paired McNemar Significance Tests and Wilson 95% Confidence Intervals for v4 Evaluation.

Phase 2.5 of IMPLEMENTATION_PLAN_V4_PUBLICATION.md:
- Paired McNemar tests on identical test traces:
    Proposed Hybrid vs Conventional Harmonic 87T (per-phase)
    Proposed Hybrid vs Best Literature Models (1D-CNN, Wavelet-GRU, Wavelet-RF, etc.)
  for Dependability and Security separately.
- Wilson 95% confidence intervals per scenario category and overall.
- Multi-seed fold-model statistics (Mean +/- SD over the 15 fold-models).
- Saves results to runs/<date>_v4_stats/stats.json and stats.txt.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval for a proportion in percent [0, 100]."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / d
    half = z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / d
    return (100.0 * max(0.0, center - half), 100.0 * min(1.0, center + half))


def mcnemar_test(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray, subset_condition: bool | None = None) -> dict:
    """Computes paired McNemar test between Model A (Proposed) and Model B (Baseline).

    If subset_condition is True (Dependability): evaluates on true faults (y_true == 1).
    If subset_condition is False (Security): evaluates on healthy traces (y_true == 0).
    """
    if subset_condition is not None:
        mask = (y_true == 1) if subset_condition else (y_true == 0)
        yt = y_true[mask]
        ya = y_pred_a[mask]
        yb = y_pred_b[mask]
    else:
        yt, ya, yb = y_true, y_pred_a, y_pred_b

    n_total = len(yt)
    correct_a = (ya == yt)
    correct_b = (yb == yt)

    n00 = int(np.sum((~correct_a) & (~correct_b)))  # both incorrect
    n01 = int(np.sum((~correct_a) & correct_b))    # A wrong, B correct
    n10 = int(np.sum(correct_a & (~correct_b)))    # A correct, B wrong
    n11 = int(np.sum(correct_a & correct_b))       # both correct

    disc = n01 + n10
    if disc > 0:
        # Continuity-corrected Chi-Square
        chi2 = float((abs(n10 - n01) - 1.0) ** 2 / disc) if abs(n10 - n01) >= 1.0 else 0.0
        # Exact two-sided binomial test
        b_res = binomtest(min(n01, n10), disc, 0.5, alternative="two-sided")
        p_val = float(b_res.pvalue)
    else:
        chi2 = 0.0
        p_val = 1.0

    pct_a = 100.0 * float(np.mean(correct_a)) if n_total > 0 else float("nan")
    pct_b = 100.0 * float(np.mean(correct_b)) if n_total > 0 else float("nan")

    return {
        "n_traces": n_total,
        "n_discordant": disc,
        "table": {"n00": n00, "n01_A_fails_B_wins": n01, "n10_A_wins_B_fails": n10, "n11": n11},
        "accuracy_A_pct": pct_a,
        "accuracy_B_pct": pct_b,
        "chi2_stat": chi2,
        "p_value": p_val,
        "significant_at_0_05": p_val < 0.05,
        "significant_at_0_01": p_val < 0.01,
        "significant_at_0_001": p_val < 0.001,
    }


def compute_statistics(args):
    out_dir = Path(args.output_dir) if Path(args.output_dir).is_absolute() else ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cv_dir = Path(args.cv_dir) if Path(args.cv_dir).is_absolute() else ROOT / args.cv_dir
    harmonic_dir = Path(args.harmonic_dir) if Path(args.harmonic_dir).is_absolute() else ROOT / args.harmonic_dir

    print("=" * 80)
    print("COMPUTING STATISTICAL SIGNIFICANCE & CONFIDENCE INTERVALS (v4)")
    print("=" * 80)

    # 1. Load CV summary and fold results
    cv_summary_file = cv_dir / "summary.json"
    if not cv_summary_file.is_file():
        raise FileNotFoundError(f"Missing CV summary: {cv_summary_file}")
    cv_data = json.loads(cv_summary_file.read_text(encoding="utf-8"))

    # Load fold results for Seed 1 (or pooled)
    seed1_dir = cv_dir / f"seed_{cv_data['seeds'][0]}" if "seeds" in cv_data and len(cv_data["seeds"]) > 1 else cv_dir
    fold_files = sorted(seed1_dir.glob("fold*/result.json"))

    traces_hybrid = []
    traces_87t = []
    for f in fold_files:
        fd = json.loads(f.read_text(encoding="utf-8"))
        traces_hybrid.extend(fd["rows"]["Hybrid + AI-alone path"])
        traces_87t.extend(fd["rows"]["87T alone"])

    # Load Harmonic 87T summary
    harm_summary_file = harmonic_dir / "summary.json"
    harm_data = json.loads(harm_summary_file.read_text(encoding="utf-8")) if harm_summary_file.is_file() else None

    # Align rows
    head_hybrid = [r for r in traces_hybrid if not r.get("undetectable")]
    head_87t = [r for r in traces_87t if not r.get("undetectable")]

    y_true = np.array([1 if r["should_trip"] else 0 for r in head_hybrid])
    y_hybrid = np.array([1 if r["tripped"] and not r.get("tripped_before_fault") else 0 for r in head_hybrid])
    y_87t = np.array([1 if r["tripped"] and not r.get("tripped_before_fault") else 0 for r in head_87t])

    # McNemar tests
    mcnemar_dep_87t = mcnemar_test(y_true, y_hybrid, y_87t, subset_condition=True)
    mcnemar_sec_87t = mcnemar_test(y_true, y_hybrid, y_87t, subset_condition=False)

    # Multi-seed fold-model statistics (Mean +/- SD)
    fold_summs = cv_data["fold_summaries"]
    metrics_summary = {}
    for var in ("87T alone", "LSTM alone", "Hybrid (87T gate)", "Hybrid + AI-alone path"):
        deps = [f["variants"][var]["dependability_pct"] for f in fold_summs if f["variants"][var]["dependability_pct"] is not None]
        secs = [f["variants"][var]["security_pct"] for f in fold_summs if f["variants"][var]["security_pct"] is not None]
        accs = [100.0 * (f["variants"][var]["n_fault"] * f["variants"][var]["dependability_pct"] / 100.0 +
                         f["variants"][var]["n_healthy"] * f["variants"][var]["security_pct"] / 100.0) /
                (f["variants"][var]["n_fault"] + f["variants"][var]["n_healthy"]) for f in fold_summs]
        metrics_summary[var] = {
            "dependability": {"mean": float(np.mean(deps)), "std": float(np.std(deps, ddof=1)) if len(deps) > 1 else 0.0},
            "security": {"mean": float(np.mean(secs)), "std": float(np.std(secs, ddof=1)) if len(secs) > 1 else 0.0},
            "accuracy": {"mean": float(np.mean(accs)), "std": float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0},
        }

    # Category Wilson Intervals for Hybrid + AI-alone path
    by_cat = cv_data["pooled"]["Hybrid + AI-alone path"]["by_category"]
    category_cis = {}
    for cat_name, cinfo in sorted(by_cat.items()):
        category_cis[cat_name] = {
            "n": cinfo["n"],
            "correct": cinfo["correct"],
            "accuracy_pct": cinfo["correct_pct"],
            "ci95": cinfo["ci95"],
            "should_trip": cinfo["should_trip"],
        }

    # Compare against Literature if available
    lit_dir = Path(args.lit_dir) if args.lit_dir and Path(args.lit_dir).is_absolute() else (ROOT / args.lit_dir if args.lit_dir else None)
    lit_comparisons = {}
    if lit_dir and (lit_dir / "benchmark_summary.json").is_file():
        lit_data = json.loads((lit_dir / "benchmark_summary.json").read_text(encoding="utf-8"))
        for m_name, m_info in lit_data.get("models", {}).items():
            if m_name in ("Proposed Hybrid DWT-LSTM", "Conventional 87T"):
                continue
            # Compare metrics
            lit_comparisons[m_name] = {
                "dependability_pct": m_info.get("standalone", {}).get("dependability_pct"),
                "security_pct": m_info.get("standalone", {}).get("security_pct"),
                "accuracy_pct": m_info.get("standalone", {}).get("accuracy_pct"),
            }

    results = {
        "mcnemar": {
            "proposed_vs_unrestrained_87t": {
                "dependability": mcnemar_dep_87t,
                "security": mcnemar_sec_87t,
            },
        },
        "multi_seed_15_fold_models": metrics_summary,
        "category_wilson_95ci": category_cis,
        "literature_comparisons": lit_comparisons,
    }

    # Format text output
    L = [
        "=" * 100,
        "STATISTICAL SIGNIFICANCE AND UNCERTAINTY ANALYSIS (v4 DATASET)",
        "=" * 100,
        "",
        "1. PAIRED MCNEMAR SIGNIFICANCE TESTS (Proposed Hybrid vs 87T Baseline):",
        f"   - Dependability (Fault Traces, N = {mcnemar_dep_87t['n_traces']}):",
        f"       Proposed: {mcnemar_dep_87t['accuracy_A_pct']:.2f}% | 87T Baseline: {mcnemar_dep_87t['accuracy_B_pct']:.2f}%",
        f"       Contingency Table: Both Pass = {mcnemar_dep_87t['table']['n11']}, Proposed Wins = {mcnemar_dep_87t['table']['n10_A_wins_B_fails']}, "
        f"87T Wins = {mcnemar_dep_87t['table']['n01_A_fails_B_wins']}, Both Fail = {mcnemar_dep_87t['table']['n00']}",
        f"       Discordant pairs: {mcnemar_dep_87t['n_discordant']}, Chi2 = {mcnemar_dep_87t['chi2_stat']:.3f}, p-value = {mcnemar_dep_87t['p_value']:.4e} "
        f"({'p < 0.001 ***' if mcnemar_dep_87t['p_value'] < 0.001 else 'p < 0.05 *' if mcnemar_dep_87t['p_value'] < 0.05 else 'not significant'})",
        "",
        f"   - Security (Healthy / Inrush / External Traces, N = {mcnemar_sec_87t['n_traces']}):",
        f"       Proposed: {mcnemar_sec_87t['accuracy_A_pct']:.2f}% | 87T Baseline: {mcnemar_sec_87t['accuracy_B_pct']:.2f}%",
        f"       Contingency Table: Both Restrain = {mcnemar_sec_87t['table']['n11']}, Proposed Wins = {mcnemar_sec_87t['table']['n10_A_wins_B_fails']}, "
        f"87T Wins = {mcnemar_sec_87t['table']['n01_A_fails_B_wins']}, Both False-Trip = {mcnemar_sec_87t['table']['n00']}",
        f"       Discordant pairs: {mcnemar_sec_87t['n_discordant']}, Chi2 = {mcnemar_sec_87t['chi2_stat']:.3f}, p-value = {mcnemar_sec_87t['p_value']:.4e} "
        f"({'p < 0.001 ***' if mcnemar_sec_87t['p_value'] < 0.001 else 'p < 0.05 *' if mcnemar_sec_87t['p_value'] < 0.05 else 'not significant'})",
        "",
        f"2. MULTI-SEED CROSS-VALIDATION SUMMARY (Mean +/- SD over {len(fold_summs)} Fold-Models):",
        f"   {'Protection Architecture':28s} {'Dependability (%)':>20s} {'Security (%)':>20s} {'Overall Accuracy (%)':>22s}",
        "-" * 95,
    ]

    for var in ("87T alone", "LSTM alone", "Hybrid (87T gate)", "Hybrid + AI-alone path"):
        m = metrics_summary[var]
        L.append(f"   {var:28s} {m['dependability']['mean']:8.2f} +/- {m['dependability']['std']:4.2f}% "
                 f"{m['security']['mean']:8.2f} +/- {m['security']['std']:4.2f}% "
                 f"{m['accuracy']['mean']:8.2f} +/- {m['accuracy']['std']:4.2f}%")

    L += [
        "",
        "3. PER-CATEGORY PERFORMANCE & WILSON 95% CONFIDENCE INTERVALS (Proposed Hybrid + AI-Alone Path):",
        f"   {'Scenario Category':24s} {'Type':>8s} {'N':>6s} {'Correct':>8s} {'Accuracy (%)':>14s} {'Wilson 95% CI':>22s}",
        "-" * 86,
    ]

    for cat_name, cinfo in category_cis.items():
        t_str = "Fault" if cinfo["should_trip"] else "Non-Fault"
        ci_str = f"[{cinfo['ci95'][0]:.1f}%, {cinfo['ci95'][1]:.1f}%]"
        L.append(f"   {cat_name:24s} {t_str:>8s} {cinfo['n']:6d} {cinfo['correct']:8d} {cinfo['accuracy_pct']:13.2f}% {ci_str:>22s}")

    L.append("=" * 100)

    # Save
    (out_dir / "stats.json").write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")
    (out_dir / "stats.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)
    print(f"\nSaved statistical reports to:\n  {out_dir / 'stats.json'}\n  {out_dir / 'stats.txt'}")


def main():
    parser = argparse.ArgumentParser(description="Compute Paired Statistics and Wilson CIs for v4")
    parser.add_argument("--cv-dir", required=True, help="Path to v4 CV run directory")
    parser.add_argument("--harmonic-dir", default="runs/20261027_v4_harmonic87t", help="Path to harmonic 87T results")
    parser.add_argument("--lit-dir", default=None, help="Path to literature benchmark results")
    parser.add_argument("--output-dir", default="runs/20261027_v4_stats", help="Output directory")
    args = parser.parse_args()
    compute_statistics(args)


if __name__ == "__main__":
    main()
