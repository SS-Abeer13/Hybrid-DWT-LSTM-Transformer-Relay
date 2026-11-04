"""Tables A-D of the benchmark-fairness work (BENCHMARK_FAIRNESS_PLAN.md, D-N8c), built ONLY from saved result files (no hand-typed numbers).

A  six reproduced published methods: native and like-for-like, CV / OOD / plant-B zero-shot, measured latency
B  same-feature models: standalone and hybrid, default (B1) and tuned with equal budget (B2)
C  conventional relays: 87T, harmonic 87T with textbook settings, harmonic 87T tuned on validation
D  instances of the dual-path logic (deployed LSTM, tuned LSTM, CNN, GRU, ANN, RF, Key) with the gated-only ablation

Called from tools/build_publication_tables_v5.py (main). Output: latex_source/latex/table_A_*.tex ..., the same files in paper_epsr/generated/ and
paper_epsr/tables/ (LaTeX), plus a Markdown rendering of each table in paper_epsr/tables/*.md converted from the same lines (identical numbers).
Every number in the cells, captions and notes is read from a saved file; only protocol constants (sampling rates, dwell, grid values, epoch limits)
are written as text, and they are listed in paper_epsr/tables/README.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C  # noqa: E402
from baselines import cv  # noqa: E402

BASE = ROOT / "runs" / "20261101_v5_benchmark_fair"
CVD = ROOT / "runs" / "20261029_v5_cv5_seeds"
OUT_DIRS = [ROOT / "latex_source" / "latex", ROOT / "paper_epsr" / "generated", ROOT / "paper_epsr" / "tables"]
MD_DIR = ROOT / "paper_epsr" / "tables"
DEP = "Hybrid + AI-alone path"


def _bad() -> set[int]:
    excl = set()
    for line in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
        f, i, *_ = [x.strip() for x in line.split(",")]
        excl.add((f, int(i)))
    metas, _ = cv.trace_index()
    return {i for i, m in enumerate(metas) if (m["source_file"], int(m["source_index"])) in excl}


BAD = _bad()


def ds(rows: list[dict]) -> tuple[float, float]:
    f = [r["correct"] for r in rows if r["should_trip"] and not r.get("undetectable")]
    h = [r["correct"] for r in rows if not r["should_trip"] and not r.get("undetectable")]
    return 100 * float(np.mean(f)), 100 * float(np.mean(h))


def mean_over_seeds(per_seed: dict[int, list[dict]]) -> tuple[float, float]:
    v = [ds(r) for r in per_seed.values()]
    return float(np.mean([x[0] for x in v])), float(np.mean([x[1] for x in v]))


def fmt(x: tuple[float, float] | None, sec_bold: bool = False) -> str:
    return "n/e & n/e" if x is None else f"{x[0]:.1f} & {x[1]:.1f}"


# ---------------------------------------------------------------------------------------------------------------- loaders
def cv_ref(variant: str) -> dict[int, list[dict]]:
    out = {s: [] for s in cv.SEEDS}
    for s in cv.SEEDS:
        for k in range(1, 6):
            out[s] += [r for r in json.load(open(CVD / f"seed_{s}" / f"fold{k}" / "result.json"))["rows"][variant] if r["trace"] not in BAD]
    return out


def cv_method(name: str, mode: str) -> dict[int, list[dict]]:
    out = {s: [] for s in cv.SEEDS}
    for f in sorted((BASE / "full" / name).glob("cv_seed*_fold*.json")):
        j = json.loads(f.read_text())
        rows = j[mode] if mode in j else j["hybrid"]
        out[rows[0]["seed"]] += rows
    return out


def final_method(name: str, label: str, mode: str) -> tuple[float, float, int, int]:
    j = json.loads((BASE / "full" / name / f"final_{label}.json").read_text())
    rows = j[mode] if mode in j else j["hybrid"]
    f = [r for r in rows if r["should_trip"] and not r["undetectable"]]
    h = [r for r in rows if not r["should_trip"] and not r["undetectable"]]
    return 100 * np.mean([r["correct"] for r in f]), 100 * np.mean([r["correct"] for r in h]), len(f), len(h)


def _tex_inline_to_md(t: str) -> str:
    import re
    t = t.replace("\\\\", "").replace("\\textmu ", "µ").replace("\\textmu", "µ").replace("\\,", " ").replace("{,}", ",").replace("\\%", "%").replace("\\&", "&")
    t = t.replace("\\~o", "õ").replace("\\ ", " ").replace("\\_", "_").replace("--", "–").replace("``", '"').replace("''", '"')
    t = t.replace("$\\times$", "×").replace("$\\gamma$", "γ").replace("$\\Delta$", "Δ").replace("$k_2$", "k2").replace("$k_5$", "k5")
    t = t.replace("$^{*}$", "\\*").replace("$^{\\dagger}$", "†").replace("$^{\\ddagger}$", "‡").replace("$^{\\triangle}$", "△")
    t = t.replace("$>3$", ">3").replace("p$_{\\mathrm{Holm}}$", "p_Holm").replace("$\\{", "{").replace("\\}$", "}")
    t = re.sub(r"\\textit\{([^}]*)\}", r"*\1*", t)
    t = re.sub(r"\\(label|vspace)\{[^}]*\}", "", t)
    t = t.replace("\\par", "").replace("\\raggedright", "").replace("\\scriptsize", "").replace("\\footnotesize", "").replace("\\small", "")
    return " ".join(t.split())


def tex_to_md(lines: list[str]) -> list[str]:
    """Markdown rendering of the LaTeX table lines written by this module (same strings, so the numbers are identical)."""
    import re
    md: list[str] = []
    body: list[list[str]] = []
    header_done = False
    in_tab = False
    for ln in lines:
        if ln.startswith("\\caption{"):
            cap = ln[len("\\caption{"):]
            cap = cap[:cap.rfind("}\\label")] if "}\\label" in cap else cap.rstrip("}")
            md += [f"**{_tex_inline_to_md(cap)}**", ""]
        elif ln.startswith("\\begin{tabular}") or "\\begin{tabular}" in ln:
            in_tab = True
        elif "\\bottomrule" in ln:
            in_tab = False
            ncol = max(len(r) for r in body)
            for i, r in enumerate(body):
                r = r + [""] * (ncol - len(r))
                md.append("| " + " | ".join(r) + " |")
                if i == (hdr_rows - 1):
                    md.append("|" + "---|" * ncol)
            md.append("")
        elif in_tab:
            if ln.strip() in ("\\midrule", "\\addlinespace"):
                if not header_done:
                    header_done = True
                continue
            row = ln.replace("\\toprule", "").replace("\\midrule", "")
            parts = [p for p in row.split("\\\\") if p.strip()]
            for part in parts:
                cells = []
                for c in re.split(r"(?<!\\)&", part):
                    m = re.match(r"\s*\\multicolumn\{(\d+)\}\{(?:[^{}]|\{\})*\}\{(.*)\}\s*$", c)
                    if m:
                        cells += [_tex_inline_to_md(m.group(2))] + [""] * (int(m.group(1)) - 1)
                    else:
                        cells.append(_tex_inline_to_md(c))
                body.append(cells)
            if "\\midrule" in ln and not header_done:
                header_done = True
                hdr_rows = len(body)
        elif ln.startswith("\\vspace") or "\\textit{Notes.}" in ln:
            md += [_tex_inline_to_md(ln), ""]
    return md


def tex_write(name: str, lines: list[str]) -> None:
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text("\n".join(lines), encoding="utf-8")
    MD_DIR.mkdir(parents=True, exist_ok=True)
    (MD_DIR / name.replace(".tex", ".md")).write_text("\n".join(tex_to_md(lines)) + "\n", encoding="utf-8")
    print(f"Generated {name} (+ .md)")


def n_common() -> tuple[int, int]:
    """(kept plant-A traces, usable traces with a 20 kHz re-simulation) from the trace metadata and hr_missing_traces.txt."""
    metas, _ = cv.trace_index()
    return len(metas), len(metas) - len(BAD)


def b2_test(prefix: str, metric: str) -> dict:
    t = [x for x in json.loads((BASE / "b2_equal_search" / "b2_summary.json").read_text()) if x["test"].startswith(prefix) and x["metric"] == metric]
    assert len(t) == 1, (prefix, metric)
    return t[0]


def holm_sizes() -> dict[str, int]:
    """Family sizes of every Holm correction, counted from the saved test lists."""
    n5b = len(json.loads((BASE / "n5_statistics_modeb.json").read_text())["tests"])
    kh = len(json.loads((BASE / "n5_statistics_keyhybrid.json").read_text()))
    b2 = len(json.loads((BASE / "b2_equal_search" / "b2_summary.json").read_text()))
    n6 = len(json.loads((BASE / "n6c_tuned_harmonic.json").read_text())["tests"])
    n8 = len(json.loads((BASE / "n8a_instances_vs_tuned_harmonic.json").read_text()))
    return {"n5b": n5b, "keyhybrid": n5b + kh, "b2": b2, "n6c": n6, "n8a": n8 + n6, "n8a_new": n8}


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", "{,}")


def load_fold_sd() -> dict:
    return json.loads((BASE / "n5_statistics.json").read_text())["fold_sd"]


# ---------------------------------------------------------------------------------------------------------------- Table A
METHODS = [("simoes_grid", "Sim\\~oes et al.\\ 2021 (RT-BSWT + 2 SVMs; C, $\\gamma$ searched)", "12.8\\,kHz"),
           ("ngaopitakkul", "Ngaopitakkul \\& Kunakorn 2006 (db4 DWT + BPNN)$^{\\triangle}$", "20\\,kHz"),
           ("abdusalam_ba_svm", "Abdusalam et al.\\ 2022 (DWT + OMP + BA + SVM)", "10\\,kHz"),
           ("afrasiabi", "Afrasiabi et al.\\ 2020 (CNN, with Hajipour CT stage)", "5.6\\,kHz"),
           ("key", "Key et al.\\ 2025 (Com-DNN + Dis-DNN)", "3.2\\,kHz"),
           ("alhamd", "Alhamd et al.\\ 2024 (RT-BSWT + BiLSTM)", "3\\,kHz")]


def latency_cell(name: str) -> str:
    b = json.loads((BASE / "latency_baselines.json").read_text())
    a = json.loads((BASE / "latency_alhamd_trained.json").read_text())

    def f(k, unit="us"):
        v = b[k]
        return v["median_us"], v.get("budget_us")
    if name == "simoes_grid":
        m, bud = f("simoes_per_sample_wavelet"); s = b["simoes_svm1_per_detection"]["median_us"]
        return f"{m:.1f}\\,/\\,{bud:.1f}\\,\\textmu s per sample; SVM\\,1 {s:.0f}\\,\\textmu s per detection"
    if name == "ngaopitakkul":
        m, bud = f("ngaopitakkul_per_sample")
        return f"{m:.1f}\\,/\\,{bud:.0f}\\,\\textmu s per sample"
    if name == "abdusalam_ba_svm":
        m, bud = f("abdusalam_features_per_decision")
        return f"{m / 1000:.0f}\\,/\\,{bud / 1000:.1f}\\,ms per window: not real-time"
    if name == "afrasiabi":
        m, bud = f("afrasiabi_cnn_per_decision")
        return f"{m:.0f}\\,/\\,{bud:.0f}\\,\\textmu s per decision"
    if name == "key":
        m, bud = f("key_per_sample")
        return f"{m:.1f}\\,/\\,{bud:.1f}\\,\\textmu s per sample"
    t = [v["latency"] for k, v in a.items() if k.startswith(("seed", "final"))]
    big = a["largest_search_space_config (earlier measurement)"]["latency"]
    return (f"{min(x['median_us'] for x in t):.0f}--{max(x['median_us'] for x in t):.0f}\\,/\\,{t[0]['budget_us']:.0f}\\,\\textmu s per decision (trained configs; "
            f"largest search-space config {big['median_us']:.0f}\\,\\textmu s)")


def table_A() -> None:
    sd = load_fold_sd()
    ref_h, ref_l = cv_ref(DEP), cv_ref("LSTM alone")
    o = {k: v.get("overall", v) for k, v in json.load(open(ROOT / "runs" / "20261029_v5_final" / "report_ood.json"))["ood"].items()}
    z = json.load(open(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "zero_shot_summary.json"))
    L = [r"\begin{table*}[t]\centering",
         r"\caption{Six published methods re-implemented and trained on the benchmark data (native decision logic and like-for-like mode), against the proposed relay. Dependability / security in \%; CV = plant A, 3 seeds $\times$ 5 folds, common set (" + fmt_int(n_common()[1]) + r" traces), mean over seeds; OOD and plant B: one final model scored once (plant B zero-shot, logic and threshold frozen from plant A). The reproductions are re-implementations trained on our data, not the authors' code.}\label{tab:A_reproductions}",
         r"\scriptsize\setlength{\tabcolsep}{3pt}",
         r"\begin{tabular}{@{}p{3.6cm}lccccccp{1.0cm}p{4.2cm}@{}}\toprule",
         r"Method & Mode & \multicolumn{2}{c}{CV} & \multicolumn{2}{c}{OOD} & \multicolumn{2}{c}{Plant B} & Rate & Latency per decision (median / budget) \\",
         r"& & dep. & sec. & dep. & sec. & dep. & sec. & & \\ \midrule"]
    for name, label, rate in METHODS:
        for mode, mlabel in (("native", "native"), ("modeb", "like-for-like")):
            cvv = mean_over_seeds(cv_method(name, mode))
            oo = final_method(name, "plantA_OOD", mode)[:2]
            bb = final_method(name, "plantB_main", mode)[:2]
            star = "$^{\\ddagger}$" if (mode == "native" and name in sd and max(sd[name]["dep_sd"], sd[name]["sec_sd"]) > 3) else ""
            first = f"{label}" if mode == "native" else ""
            lat = latency_cell(name) if mode == "native" else ""
            rt = rate if mode == "native" else ""
            L.append(f"{first} & {mlabel}{star} & {cvv[0]:.1f} & {cvv[1]:.1f} & {oo[0]:.1f} & {oo[1]:.1f} & {bb[0]:.1f} & {bb[1]:.1f} & {rt} & {lat} \\\\")
        L.append(r"\addlinespace")
    hy, la = mean_over_seeds(ref_h), mean_over_seeds(ref_l)
    oh, ol = o[DEP], o["LSTM alone"]
    L += [r"\midrule",
          f"Proposed relay (deployed LSTM, dual-path) & hybrid & {hy[0]:.1f} & {hy[1]:.1f} & {oh['dependability_pct']:.1f} & {oh['security_pct']:.1f} & {z['Proposed']['dependability_pct']:.1f} & {z['Proposed']['security_pct']:.1f} & 1.6\\,kHz & {json.loads((ROOT / 'runs' / '20261029_v5_latency' / 'latency.json').read_text())['combined_relay_pipeline']['median_us']:.0f}\\,/\\,625\\,\\textmu s (ONNX) \\\\",
          f"LSTM alone (same logic, no 87T path) & standalone & {la[0]:.1f} & {la[1]:.1f} & {ol['dependability_pct']:.1f} & {ol['security_pct']:.1f} & {z['LSTM alone']['dependability_pct']:.1f} & {z['LSTM alone']['security_pct']:.1f} & & \\\\",
          r"\bottomrule\end{tabular}"]
    # footnote numbers (all from files)
    pub = mean_over_seeds(cv_method("simoes_grid", "native")) if False else None
    simp = json.loads((BASE / "simoes_published" / "summary.json").read_text())
    nocomp = {s: [] for s in cv.SEEDS}
    for f in sorted((BASE / "afrasiabi_nocomp").glob("rows_seed*_fold*.json")):
        rr = json.loads(f.read_text()); nocomp[rr[0]["seed"]] += rr
    nc = mean_over_seeds(nocomp)
    alr = {s: [] for s in cv.SEEDS}
    for f in sorted((BASE / "alhamd_reduced_budget").glob("rows_seed*_fold*.json")):
        rr = json.loads(f.read_text()); alr[rr[0]["seed"]] += rr
    ar = mean_over_seeds(alr)
    gas = {s: [] for s in cv.SEEDS}
    for f in sorted((BASE / "abdusalam_ga_svm").glob("rows_seed*_fold*.json")):
        rr = json.loads(f.read_text()); gas[rr[0]["seed"]] += rr
    ga = mean_over_seeds(gas)
    ns = {s: [] for s in cv.SEEDS}
    for f in sorted((BASE / "simoes_published").glob("rows_seed*_fold*.json")):
        rr = json.loads(f.read_text()); ns[rr[0]["seed"]] += rr
    sp = mean_over_seeds(ns)
    # note numbers, all read from saved files (D-N8c, cloud revision 2026-11-03)
    import re
    n_kept, n_use = n_common()
    n_ood_rep = sorted({len(json.loads((BASE / "full" / m / "final_plantA_OOD.json").read_text())["native"]) for m, _, _ in METHODS})
    n_b_rep = sorted({len(json.loads((BASE / "full" / m / "final_plantB_main.json").read_text())["native"]) for m, _, _ in METHODS})
    n_ood_prop = oh["n_fault"] + oh["n_healthy"]
    n_b_prop = z["Proposed"]["n_fault"] + z["Proposed"]["n_healthy"]
    ng = re.search(r"in only (\d+)-(\d+) % of internal-fault traces", (ROOT / "documents" / "baselines" / "ngaopitakkul2006_dwt_bpnn_spec.md").read_text())
    n2 = json.loads((BASE / "n2_simoes_factor.json").read_text())
    n2_chosen = sorted({c["chosen"] for c in n2})
    n2_rate = [100 * np.mean([c["grid"][str(f)]["detection_rate"] for c in n2]) for f in n2_chosen]
    hs = holm_sizes()
    L += [r"\vspace{3pt}\par\raggedright\scriptsize\textit{Notes.} Like-for-like = 20-sample dwell (12.5\,ms) with a threshold tuned on validation traces (plateau rule) plus the relay's high-set element; Sim\~oes and Ngaopitakkul act once per detector firing (no dwell). "
          r"Native = the method's own decision rule (the ``as intended'' row). Reproductions are scored on the traces that exist in the 20\,kHz re-simulation "
          f"(plant A {fmt_int(n_use)} of {fmt_int(n_kept)}, OOD {'/'.join(fmt_int(x) for x in n_ood_rep)}, plant B {'/'.join(fmt_int(x) for x in n_b_rep)}); the proposed-relay rows use all evaluable traces (OOD {fmt_int(n_ood_prop)}, plant B {fmt_int(n_b_prop)}). "
          r"$^{\ddagger}$ fold-model standard deviation $>3$ pt: report the range, do not rank by the mean. "
          f"$^{{\\triangle}}$ the paper's sanity check holds on noise-free currents but not on the benchmark's CT secondaries with measurement noise (detector fires in {ng.group(1)}--{ng.group(2)}\\,\\% of internal-fault traces; spec amendment 8); the lumped plants have almost no energy above 1.6\\,kHz (no winding capacitances), which also limits Sim\\~oes. "
          f"Variants in the appendix: Sim\\~oes with the published $C,\\gamma$ {sp[0]:.1f} / {sp[1]:.1f}; Afrasiabi without the Hajipour stage {nc[0]:.1f} / {nc[1]:.1f} (the stage is nearly inactive on our CT-stress traces); Abdusalam GA + SVM {ga[0]:.1f} / {ga[1]:.1f}; Alhamd with the reduced CPU budget {ar[0]:.1f} / {ar[1]:.1f} (native, CV). "
          f"Sim\\~oes' detector factor was chosen on validation traces ({' or '.join(f'{f:.0f}' for f in n2_chosen)}): it finds {min(n2_rate):.0f}--{max(n2_rate):.0f}\\,\\% of events, which caps its dependability (pre-registered). Latency: single thread, development PC, Python; networks at the largest search-space size except Alhamd (trained configurations listed); n/e = not evaluated. "
          f"Statistics (exact McNemar, Holm over {hs['n5b']} tests, native and like-for-like) are in the supplementary file n5\\_statistics\\_modeb.txt.",
          r"\end{table*}"]
    tex_write("table_A_reproductions.tex", L)


# ---------------------------------------------------------------------------------------------------------------- Table B
def b1_rows() -> dict[str, dict[str, dict[int, list[dict]]]]:
    out: dict[str, dict[str, dict[int, list[dict]]]] = {}
    for s in cv.SEEDS:
        for k in range(1, 6):
            j = json.loads((BASE / "b1_equal_budget" / f"seed_{s}" / f"fold{k}" / "benchmark_fold_results.json").read_text())["rows"]
            for m, modes in j.items():
                for mode, rows in modes.items():
                    out.setdefault(m, {}).setdefault(mode, {s_: [] for s_ in cv.SEEDS})[s] += [r for r in rows if r["trace"] not in BAD]
    return out


def table_B() -> None:
    b1 = b1_rows()
    b2 = {}
    for f in sorted((BASE / "b2_equal_search").glob("final_seed*_fold*.json")):
        j = json.loads(f.read_text())
        for m in j:
            for mode in ("standalone", "hybrid"):
                s = j[m][mode][0]["seed"]
                b2.setdefault(m, {}).setdefault(mode, {s_: [] for s_ in cv.SEEDS})[s] += [r for r in j[m][mode] if r["trace"] not in BAD]
    best = json.loads((BASE / "b2_equal_search" / "chosen_configs.json").read_text())
    uniq = json.loads((BASE / "b2_equal_search" / "unique_configs.json").read_text())
    hs = holm_sizes()
    drawn = {v["drawn"] for v in uniq.values()}; assert len(drawn) == 1; drawn = drawn.pop()
    u_lo, u_hi = min(v["unique"] for v in uniq.values()), max(v["unique"] for v in uniq.values())
    eps = [j[m]["epochs_used"] for f in sorted((BASE / "b2_equal_search").glob("final_seed*_fold*.json")) for j in [json.loads(f.read_text())] for m in j if j[m].get("epochs_used")]
    ep_mean = float(np.mean(eps))
    tl_d, tl_s = b2_test("tuned LSTM hybrid vs deployed", "dependability"), b2_test("tuned LSTM hybrid vs deployed", "security")
    vd = {lab: (b2_test(f"{k} hybrid vs deployed", "dependability"), b2_test(f"{k} hybrid vs deployed", "security"))
          for lab, k in (("CNN", "1D-CNN"), ("GRU", "Wavelet-GRU"), ("ANN", "Wavelet-ANN"), ("RF", "Wavelet-RF"), ("SVM", "Wavelet-SVM"))}
    unstable_sec = [lab for lab in ("CNN", "GRU", "ANN", "RF", "SVM") if not vd[lab][1]["sign_stable"]]
    L = [r"\begin{table*}[t]\centering",
         r"\caption{Same 12 DWT + second-harmonic features, different classifiers: default configuration (B1: equal training routine) and tuned with an equal " + str(drawn) + r"-configuration search (B2); standalone and inside the dual-path logic (hybrid). Dependability / security in \%, plant-A CV, 3 seeds $\times$ 5 folds, common set, mean over seeds.}\label{tab:B_same_features}",
         r"\scriptsize\setlength{\tabcolsep}{3pt}",
         r"\begin{tabular}{@{}lcccccccccp{4.2cm}@{}}\toprule",
         r"Classifier (architecture) & \multicolumn{4}{c}{Default configuration} & \multicolumn{4}{c}{Tuned, equal budget} & unique & chosen configuration \\",
         r"& \multicolumn{2}{c}{standalone} & \multicolumn{2}{c}{hybrid} & \multicolumn{2}{c}{standalone} & \multicolumn{2}{c}{hybrid} & configs & \\",
         r"& dep. & sec. & dep. & sec. & dep. & sec. & dep. & sec. & of " + str(drawn) + r" & \\ \midrule"]
    names = [("Wavelet-SVM", "SVM (pooled features)"), ("Wavelet-RF", "Random forest (pooled features)"), ("Wavelet-ANN", "MLP (pooled features)"),
             ("1D-CNN", "1D-CNN (sequence)"), ("Wavelet-GRU", "GRU + attention (sequence)"), ("Proposed LSTM", "LSTM + attention (sequence)")]
    for key, label in names:
        if key == "Proposed LSTM":
            d_sa = mean_over_seeds(cv_ref("LSTM alone")); d_hy = mean_over_seeds(cv_ref(DEP))
        else:
            d_sa = mean_over_seeds(b1[key]["standalone"]); d_hy = mean_over_seeds(b1[key]["hybrid"])
        t_sa = mean_over_seeds(b2[key]["standalone"]); t_hy = mean_over_seeds(b2[key]["hybrid"])
        cfg = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in best[key].items())
        L.append(f"{label} & {d_sa[0]:.1f} & {d_sa[1]:.1f} & {d_hy[0]:.1f} & {d_hy[1]:.1f} & {t_sa[0]:.1f} & {t_sa[1]:.1f} & {t_hy[0]:.1f} & {t_hy[1]:.1f} & {uniq[key]['unique']} & {cfg} \\\\")
    L += [r"\bottomrule\end{tabular}",
          r"\vspace{3pt}\par\raggedright\scriptsize\textit{Notes.} Default: SVM/RF/MLP/CNN/GRU from the B1 run (25 epochs maximum, patience 5, window stride 8); the LSTM default is the deployed model of the cross-validation (same routine, stride 4). "
          f"Tuned (B2): {drawn} configurations drawn at random per model with a fixed seed (with replacement: {u_lo}--{u_hi} unique per model, the LSTM {uniq['Proposed LSTM']['unique']}, so any unequal budget is against the proposed model), search on the inner validation split of folds 1--3 of seed 1 (mean validation window AUC), the chosen configuration then trained on all 15 fold-models; same routine for all neural models (25 epochs maximum, patience 5, about {ep_mean:.0f} epochs actually used, AdamW, batch 256, stride 4). "
          f"The deployed LSTM and the closed-loop results are unchanged by the search; the tuned LSTM is not significantly different from it ({tl_d['diff_pt']:+.2f} / {tl_s['diff_pt']:+.2f} pt, Holm-{hs['b2']}). "
          f"Tuned hybrids vs the deployed hybrid (post-hoc family; Holm over all {hs['b2']} B2 tests; per-seed security signs change for {', '.join(unstable_sec)}): "
          + ", ".join(f"{lab} {vd[lab][0]['diff_pt']:+.1f} pt dependability" + ("" if vd[lab][0]['p_holm'] < 0.05 else " (n.s.)") for lab in ("CNN", "GRU", "ANN"))
          + f", RF {vd['RF'][0]['diff_pt']:+.1f} dependability" + ("" if vd['RF'][0]['p_holm'] < 0.05 else " (n.s.)") + f" and {vd['RF'][1]['diff_pt']:+.1f} security" + (" (significant)" if vd['RF'][1]['p_holm'] < 0.05 else " (n.s.)")
          + f"; the SVM hybrid is lower on both ({vd['SVM'][0]['diff_pt']:+.1f} / {vd['SVM'][1]['diff_pt']:+.1f} pt" + (", both significant)" if max(vd['SVM'][0]['p_holm'], vd['SVM'][1]['p_holm']) < 0.05 else ")") + ". Table names describe architectures; they are not reproductions of the cited papers.",
          r"\end{table*}"]
    tex_write("table_B_same_features.tex", L)


# ---------------------------------------------------------------------------------------------------------------- Table C
def table_C() -> None:
    rows = json.loads((BASE / "n6c_tuned_rows.json").read_text())
    per = lambda key: {s: [r for r in rows[key] if r["key"][0] == s] for s in cv.SEEDS}  # noqa: E731
    h = json.load(open(ROOT / "runs" / "20261029_v5_harmonic87t" / "summary.json"))["variants"]
    o = {k: v.get("overall", v) for k, v in json.load(open(ROOT / "runs" / "20261029_v5_final" / "report_ood.json"))["ood"].items()}
    z = json.load(open(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "zero_shot_summary.json"))
    n6 = json.loads((BASE / "n6c_tuned_harmonic.json").read_text())
    ch = {}
    for c in n6["chosen"]:
        ch[str(c["setting"])] = ch.get(str(c["setting"]), 0) + 1
    t87 = mean_over_seeds(cv_ref("87T alone"))
    tb, tt = mean_over_seeds(per("textbook")), mean_over_seeds(per("tuned"))
    hy = mean_over_seeds(cv_ref(DEP))
    fam = [l for l in (BASE / "n6c_tuned_harmonic.txt").read_text().splitlines() if l.startswith("dependability, ")]
    L = [r"\begin{table}[t]\centering",
         r"\caption{Conventional relays on the benchmark data (dependability / security, \%): unrestrained dual-slope 87T, harmonic-restrained 87T with textbook settings, and harmonic-restrained 87T tuned on validation traces, against the proposed relay. Plant-A CV (3 seeds $\times$ 5 folds, common set), OOD (final scoring) and plant-B zero-shot.}\label{tab:C_conventional}",
         r"\small\begin{tabular}{@{}lcccccc@{}}\toprule",
         r"Relay & \multicolumn{2}{c}{CV} & \multicolumn{2}{c}{OOD} & \multicolumn{2}{c}{Plant B} \\ & dep. & sec. & dep. & sec. & dep. & sec. \\ \midrule",
         f"87T unrestrained (dual slope, 0.30\\,pu pickup) & {t87[0]:.1f} & {t87[1]:.1f} & {o['87T alone']['dependability_pct']:.1f} & {o['87T alone']['security_pct']:.1f} & {z['87T alone']['dependability_pct']:.1f} & {z['87T alone']['security_pct']:.1f} \\\\",
         f"Harmonic 87T, textbook (0.30\\,pu, $k_2$ 0.15, $k_5$ 0.35) & {tb[0]:.1f} & {tb[1]:.1f} & {h['per_phase']['ood_overall']['dependability_pct']:.1f} & {h['per_phase']['ood_overall']['security_pct']:.1f} & {z['Harmonic 87T']['dependability_pct']:.1f} & {z['Harmonic 87T']['security_pct']:.1f} \\\\",
         f"Harmonic 87T, tuned on validation & {tt[0]:.1f} & {tt[1]:.1f} & n/e & n/e & n/e & n/e \\\\", r"\midrule",
         f"Proposed relay (deployed LSTM hybrid) & {hy[0]:.1f} & {hy[1]:.1f} & {o[DEP]['dependability_pct']:.1f} & {o[DEP]['security_pct']:.1f} & {z['Proposed']['dependability_pct']:.1f} & {z['Proposed']['security_pct']:.1f} \\\\",
         r"\bottomrule\end{tabular}",
         r"\vspace{3pt}\par\raggedright\footnotesize\textit{Notes.} Tuned = grid pickup $\{0.2, 0.3, 0.4\}$\,pu $\times$ $k_2$ $\{0.12, 0.15, 0.20\}$ $\times$ $k_5$ $\{0.25, 0.35\}$, chosen per fold on validation traces by the plateau rule (fills fixed before the run); chosen settings over the 15 fold-models: "
         + "; ".join(f"{k.replace('[', '(').replace(']', ')')} in {v}" for k, v in ch.items()) + ". "
         + f"Proposed vs tuned harmonic 87T: dependability {n6['tests'][2]['diff_pt']:+.2f} pt for the tuned relay relative to the hybrid (Holm over 4 tests, p$_{{\\mathrm{{Holm}}}}$ {n6['tests'][2]['p_holm4']:.1e}; per-seed differences {', '.join(f'{v:+.2f}' for v in n6['tests'][2]['per_seed'].values())}, sign changes: unstable), security {n6['tests'][3]['diff_pt']:+.2f} pt (n.s.). "
         + "; ".join(fam).replace("dependability, ", "Dependability, ").replace("_", "\\_") + ". n/e = not evaluated (no new experiments were run after the review).",
         r"\end{table}"]
    tex_write("table_C_conventional.tex", L)


# ---------------------------------------------------------------------------------------------------------------- Table D
def table_D() -> None:
    n8 = {(t["instance"], t["metric"]): t for t in json.loads((BASE / "n8a_instances_vs_tuned_harmonic.json").read_text())}
    b2 = {}
    for f in sorted((BASE / "b2_equal_search").glob("final_seed*_fold*.json")):
        j = json.loads(f.read_text())
        for m in j:
            s = j[m]["hybrid"][0]["seed"]
            b2.setdefault(m, {s_: [] for s_ in cv.SEEDS})[s] += [r for r in j[m]["hybrid"] if r["trace"] not in BAD]
    o = {k: v.get("overall", v) for k, v in json.load(open(ROOT / "runs" / "20261029_v5_final" / "report_ood.json"))["ood"].items()}
    z = json.load(open(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "zero_shot_summary.json"))
    tpc = json.load(open(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "trip_path_check.json"))["variants"]
    gat = json.loads((BASE / "gated_only_ablation.json").read_text())
    kb = json.loads((BASE / "full" / "key_hybrid" / "final_plantB_main.json").read_text())
    ko = json.loads((BASE / "full" / "key_hybrid" / "final_plantA_OOD.json").read_text())

    def kd(j, k):
        rows = [r for r in j[k] if not r["undetectable"]]
        f = [r["correct"] for r in rows if r["should_trip"]]; h = [r["correct"] for r in rows if not r["should_trip"]]
        return 100 * np.mean(f), 100 * np.mean(h)
    hs = holm_sizes()
    n8l = json.loads((BASE / "n8a_instances_vs_tuned_harmonic.json").read_text())
    th_d = {round(t["tuned_harmonic_pct"], 6) for t in n8l if t["metric"] == "dependability"}; assert len(th_d) == 1; th_d = th_d.pop()
    th_s = {round(t["tuned_harmonic_pct"], 6) for t in n8l if t["metric"] == "security"}; assert len(th_s) == 1; th_s = th_s.pop()
    dd = [t for t in n8l if t["metric"] == "dependability"]; dsec = [t for t in n8l if t["metric"] == "security"]
    n_dep_sig = sum(t["p_holm16"] < 0.05 and t["diff_pt"] > 0 for t in dd)
    n_sec_lower = sum(t["p_holm16"] < 0.05 and t["diff_pt"] < 0 for t in dsec)
    tpc_all = json.load(open(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "trip_path_check.json"))
    ftp = tpc_all["false_trip_first_path"]; n_ft = tpc_all["variants"]["Proposed as evaluated (high-set + gate + solo)"]["false_trips"]
    kh = {t["metric"]: t for t in json.loads((BASE / "n5_statistics_keyhybrid.json").read_text())}
    stab = lambda d: all(v > 0 for v in d.values()) or all(v < 0 for v in d.values())  # noqa: E731
    sig = lambda t: ("$^{*}$" if t["p_holm16"] < 0.05 else "") + ("" if t["sign_stable"] else "$^{\\dagger}$")  # noqa: E731
    L = [r"\begin{table*}[t]\centering",
         r"\caption{Instances of the dual-path supervisory logic with interchangeable classifiers (dependability / security, \%): plant-A CV (3 seeds $\times$ 5 folds, common set, mean over seeds), OOD and plant-B zero-shot where a final model was scored; difference to the validation-tuned harmonic 87T (" + f"{th_d:.1f} / {th_s:.1f}; post-hoc, Holm over {hs['n8a']} tests" + r"); and the gated-only ablation (AI-alone path off).}\label{tab:D_instances}",
         r"\scriptsize\setlength{\tabcolsep}{3pt}",
         r"\begin{tabular}{@{}lcccccccc@{}}\toprule",
         r"Instance (hybrid mode) & \multicolumn{2}{c}{CV} & $\Delta$ dep. vs tuned & $\Delta$ sec. vs tuned & \multicolumn{2}{c}{OOD} & \multicolumn{2}{c}{Plant B} \\ & dep. & sec. & harmonic 87T (pt) & harmonic 87T (pt) & dep. & sec. & dep. & sec. \\ \midrule"]
    hy = mean_over_seeds(cv_ref(DEP))
    L.append(f"LSTM, deployed (closed-loop configuration) & {hy[0]:.1f} & {hy[1]:.1f} & n/e & n/e & {o[DEP]['dependability_pct']:.1f} & {o[DEP]['security_pct']:.1f} & {z['Proposed']['dependability_pct']:.1f} & {z['Proposed']['security_pct']:.1f} \\\\")
    for key, label, nm in (("Proposed LSTM", "LSTM, tuned (B2)", "LSTM (tuned, B2)"), ("1D-CNN", "1D-CNN, tuned (B2)", "1D-CNN"), ("Wavelet-GRU", "GRU, tuned (B2)", "Wavelet-GRU"),
                           ("Wavelet-ANN", "MLP, tuned (B2)", "Wavelet-ANN"), ("Wavelet-RF", "Random forest, tuned (B2)", "Wavelet-RF")):
        v = mean_over_seeds(b2[key]); td, ts = n8[(nm, "dependability")], n8[(nm, "security")]
        L.append(f"{label} & {v[0]:.1f} & {v[1]:.1f} & {td['diff_pt']:+.2f}{sig(td)} & {ts['diff_pt']:+.2f}{sig(ts)} & n/e & n/e & n/e & n/e \\\\")
    kv = mean_over_seeds(cv_method("key_hybrid", "hybrid")); td, ts = n8[("Key (claim-C run)", "dependability")], n8[("Key (claim-C run)", "security")]
    ko_, kb_ = kd(ko, "hybrid"), kd(kb, "hybrid")
    L.append(f"Key et al.\\ network (Dis-DNN output) & {kv[0]:.1f} & {kv[1]:.1f} & {td['diff_pt']:+.2f}{sig(td)} & {ts['diff_pt']:+.2f}{sig(ts)} & {ko_[0]:.1f} & {ko_[1]:.1f} & {kb_[0]:.1f} & {kb_[1]:.1f} \\\\")
    L += [r"\midrule", r"\multicolumn{9}{@{}l}{\textit{Ablation, AI-alone path off (gated only; post-hoc, from saved decisions)}} \\",
          f"LSTM, deployed, gated only & {gat['dependability']['gated_only_pct']:.1f} & {gat['security']['gated_only_pct']:.1f} & & & {o['Hybrid (87T gate)']['dependability_pct']:.1f} & {o['Hybrid (87T gate)']['security_pct']:.1f} & {tpc['without AI-alone path (high-set + gate)']['dependability_pct']:.1f} & {tpc['without AI-alone path (high-set + gate)']['security_pct']:.1f} \\\\"]
    kgo, kgb = kd(ko, "gated_only"), kd(kb, "gated_only")
    L.append(f"Key et al.\\ network, gated only & n/e & n/e & & & {kgo[0]:.1f} & {kgo[1]:.1f} & {kgb[0]:.1f} & {kgb[1]:.1f} \\\\")
    pf = json.loads((BASE / "full" / "key_hybrid" / "final_plantB_main.json").read_text())["paths"]["false_trips"]
    n_kb_h = sum(1 for r in kb["hybrid"] if not r["should_trip"] and not r["undetectable"])
    L += [r"\bottomrule\end{tabular}",
          f"\\vspace{{3pt}}\\par\\raggedright\\scriptsize\\textit{{Notes.}} $^{{*}}$ significant after Holm over {hs['n8a']} tests ({hs['n8a_new']} post-hoc tests added after N6c plus the {hs['n6c']} of the tuned-harmonic comparison); $^{{\\dagger}}$ per-seed differences change sign (unstable across splits). "
          f"{n_dep_sig} of {len(dd)} instances are significantly more dependable than the tuned harmonic 87T ({min(t['diff_pt'] for t in dd):+.1f} to {max(t['diff_pt'] for t in dd):+.1f} pt); " + ("none is" if n_sec_lower == 0 else f"{n_sec_lower} are") + " significantly less secure. "
          r"The B2 instances were evaluated in cross-validation only (n/e = not evaluated: no OOD or plant-B run, no new experiments after the review). Key's classifier is the Dis-DNN internal-fault probability sampled at the relay's decision instants inside the identical logic (87T vote, confirmed output, AI-alone path, high-set; thresholds by the plateau rule). "
          f"Plant B, deployed hybrid: {ftp.get('solo', 0)} of {n_ft} false trips first came from the AI-alone path, {ftp.get('gate', 0)} from the gated path, {ftp.get('highset', 0) or 'none'} from the high-set; Key hybrid: {pf['solo']} of {n_kb_h} from the AI-alone path, {pf['gate']} gated, {pf['highset']} high-set. "
          f"Gated-only (post-hoc counterfactual, not adopted): on the plant-A CV the AI-alone path adds {gat['dependability']['deployed_pct'] - gat['dependability']['gated_only_pct']:.1f} pt dependability and costs {gat['security']['gated_only_pct'] - gat['security']['deployed_pct']:.1f} pt security (exact McNemar p {gat['dependability']['p']:.0e} and {gat['security']['p']:.0e}, raw). "
          f"Key hybrid vs proposed hybrid: dependability {kh['dependability']['diff_pt']:+.2f} pt ({'stable' if stab(kh['dependability']['per_seed_diff_pt']) else 'unstable'} across seeds), security {kh['security']['diff_pt']:+.2f} pt ({'stable' if stab(kh['security']['per_seed_diff_pt']) else 'unstable'}), Holm over {hs['keyhybrid']} tests.",
          r"\end{table*}"]
    tex_write("table_D_instances.tex", L)


def build_all() -> None:
    table_A(); table_B(); table_C(); table_D()


if __name__ == "__main__":
    build_all()
