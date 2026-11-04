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
import re
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


PAPER_DIR = ROOT / "paper_epsr" / "generated" / "paper"   # manuscript copies: same cells, short notes (full notes go to the supplement)


def fit_width(lines: list[str]) -> list[str]:
    """Scale the tabular to the text width (the elsarticle preprint column is narrow); cells are unchanged."""
    out = []
    for ln in lines:
        ln = ln.replace(r"\begin{table*}[t]", r"\begin{table*}[!htbp]").replace(r"\begin{table}[t]", r"\begin{table}[!htbp]")   # large tables: do not defer every float to the end
        if ln.lstrip().startswith(r"\begin{tabular}") or (r"\begin{tabular}" in ln and ln.startswith((r"\small", r"\scriptsize", r"\footnotesize"))):
            pre, tab = ln.split(r"\begin{tabular}", 1)
            out.append(pre + r"\resizebox{\textwidth}{!}{%")
            out.append(r"\begin{tabular}" + tab)
        elif r"\end{tabular}" in ln:
            out.append(ln.replace(r"\end{tabular}", r"\end{tabular}}"))
        else:
            out.append(ln)
    return out


def tex_write(name: str, lines: list[str], short_note: str | None = None) -> None:
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text("\n".join(lines if d.name == "latex" else fit_width(lines)), encoding="utf-8")
    MD_DIR.mkdir(parents=True, exist_ok=True)
    (MD_DIR / name.replace(".tex", ".md")).write_text("\n".join(tex_to_md(lines)) + "\n", encoding="utf-8")
    if short_note is not None:
        PAPER_DIR.mkdir(parents=True, exist_ok=True)
        size = r"\scriptsize" if r"\scriptsize\textit{Notes.}" in "".join(lines) else r"\footnotesize"
        paper = [(r"\vspace{3pt}\par\raggedright" + size + r"\textit{Notes.} " + short_note) if ("\\textit{Notes.}" in ln) else ln for ln in lines]
        paper = [ln.replace(r"\label{tab:", r"\label{tab:p") for ln in paper]
        (PAPER_DIR / name).write_text("\n".join(fit_width(paper)), encoding="utf-8")
    print(f"Generated {name} (+ .md" + (", paper copy)" if short_note is not None else ")"))


# ---------------------------------------------------------------------------------------------------------------- audit fixes (paper-v1)
# Significance marks and p-values come from the trace-clustered test of the audit (results_audit.md B1a), not from the pooled McNemar.
CLU = json.loads((ROOT / "audit" / "scripts" / "out" / "clustered_sensitivity.json").read_text())
_CLU_TXT = (ROOT / "audit" / "scripts" / "out" / "clustered_sensitivity.txt").read_text()
PERM_DRAWS = int(re.search(r"\((\d+) draws", _CLU_TXT).group(1))
PERM_FLOOR = float(re.search(r"floor ([0-9.]+e-\d+)", _CLU_TXT).group(1))


def clu(family_prefix: str, label: str) -> dict:
    fam = [k for k in CLU if k.startswith(family_prefix)]
    assert len(fam) == 1, family_prefix
    t = [x for x in CLU[fam[0]] if x["label"] == label]
    assert len(t) == 1, (family_prefix, label)
    return t[0]


def clu_n(family_prefix: str) -> int:
    """Holm family size of a clustered family, read from its key, e.g. 'N8a (Holm 16)'."""
    fam = [k for k in CLU if k.startswith(family_prefix)]
    return int(re.search(r"Holm (\d+)", fam[0]).group(1))


def ptex(t: dict) -> str:
    """Clustered Holm-adjusted p for LaTeX; '\\le' when the permutation floor was reached (conservative)."""
    q = t["holm_clust"]
    op = r"\le" if t["p_clust"] <= PERM_FLOOR * 1.0001 else "="
    if q >= 0.01:
        return f"$p_{{\\mathrm{{H}}}}{op}{q:.2f}$"
    m, e = f"{q:.0e}".split("e")
    return f"$p_{{\\mathrm{{H}}}}{op}{m}\\times10^{{{int(e)}}}$"


def test_unit(n: int) -> str:
    draws = f"{PERM_DRAWS:,}".replace(",", "{,}")
    return (f"Significance: trace-clustered sign-flip permutation test (test unit = trace; per-trace difference averaged over the three CV repetitions; "
            f"{draws} draws), Holm-adjusted within a family of {n} tests.")


INST_LABEL = {"Key (claim-C run)": "Key's network", "LSTM (tuned, B2)": "the tuned LSTM", "Wavelet-RF": "RF", "Wavelet-ANN": "MLP", "Wavelet-GRU": "GRU"}


def sci(q: float) -> str:
    m, e = f"{q:.0e}".split("e")
    return f"{m}\\times10^{{{int(e)}}}"


def code_constants() -> dict:
    """Training constants read from the code that produced the runs (code_audit.md C-1, C-4)."""
    b2 = (ROOT / "tools" / "run_b2_search.py").read_text()
    st = re.search(r"^STRIDE, EPOCHS, PATIENCE = (\d+), (\d+), (\d+)", b2, re.M)
    sub = re.search(r'min\(len\(ytr\), (\d+) if name == "Wavelet-SVM" else (\d+)\)', b2)
    cvsrc = (ROOT / "lstm_models" / "train_cv_v5.py").read_text()
    dep = int(re.search(r'"--train-stride", type=int, default=(\d+)', cvsrc).group(1))
    assert "--train-stride" not in (ROOT / "run_v5_cv.sh").read_text(), "run_v5_cv.sh overrides the stride"
    return {"stride_b2": int(st.group(1)), "epochs": int(st.group(2)), "patience": int(st.group(3)), "stride_deployed": dep,
            "sub_svm": int(sub.group(1)), "sub_rf": int(sub.group(2))}


def solo_settings() -> dict:
    """Plateau-rule settings of the deployed hybrid's 15 CV fold-models (code_audit.md C-12)."""
    s = [json.loads(f.read_text())["summary"]["settings"][DEP] for f in sorted(CVD.glob("seed_*/fold*/result.json"))]
    ai = [x["ai_threshold"] for x in s]
    return {"n": len(s), "solo_off": sum(x["solo_threshold"] is None for x in s), "ai_min": min(ai), "ai_max": max(ai)}


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
          f"Sim\\~oes' detector factor was chosen on validation traces ({' or '.join(f'{f:.0f}' for f in n2_chosen)}): it finds {min(n2_rate):.0f}--{max(n2_rate):.0f}\\,\\% of events, which caps its dependability (decision rule fixed in a dated plan before the analysis). Latency: single thread, development PC, Python; networks at the largest search-space size except Alhamd (trained configurations listed); n/e = not evaluated. "
          f"Paired comparisons with the proposed relay (native and like-for-like, {clu_n('N5b')} tests) are listed in Supplementary Table S3. " + test_unit(clu_n('N5b')) + " Rows use the second (full) run of each reproduction; Key and Afrasiabi training is not bit-reproducible (Supplementary Section S2).",
          r"\end{table*}"]
    short = (r"Native = the method's own decision rule; like-for-like = the same classifier with the relay's 20-sample dwell, validation-tuned threshold and high-set element. "
             f"CV on the {fmt_int(n_use)}-trace common set (traces with a 20\\,kHz re-simulation). OOD and plant B scored once with frozen thresholds. "
             r"$^{\ddagger}$ fold-model s.d.\ $>3$ pt. $^{\triangle}$ detector sanity check fails with measurement noise. Latency: single-thread Python on a development PC. "
             f"Paired tests in Supplementary Table S3 ({test_unit(clu_n('N5b'))}) Full notes: Supplementary Table S1.")
    tex_write("table_A_reproductions.tex", L, short)


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
    k = code_constants(); nb2 = clu_n("B2")
    cB = lambda a, m: clu("B2", f"{a} {m}")  # noqa: E731
    vs_t = {lab: (cB(f"{key} hybrid vs tuned LSTM hybrid", "dependability"), cB(f"{key} hybrid vs tuned LSTM hybrid", "security"))
            for lab, key in (("CNN", "1D-CNN"), ("GRU", "Wavelet-GRU"), ("ANN", "Wavelet-ANN"), ("RF", "Wavelet-RF"), ("SVM", "Wavelet-SVM"))}
    tl_c = (cB("tuned LSTM hybrid vs deployed hybrid", "dependability"), cB("tuned LSTM hybrid vs deployed hybrid", "security"))
    for lab in vs_t:  # the clustered file must describe the same comparisons as b2_summary.json
        assert abs(vs_t[lab][0]["diff"] - b2_test(f"{dict(CNN='1D-CNN', GRU='Wavelet-GRU', ANN='Wavelet-ANN', RF='Wavelet-RF', SVM='Wavelet-SVM')[lab]} hybrid vs tuned", "dependability")["diff_pt"]) < 1e-9
    sig = lambda t: "" if t["holm_clust"] < 0.05 else " (n.s.)"  # noqa: E731
    fmtd = lambda lab: f"{lab} {vs_t[lab][0]['diff']:+.1f}{sig(vs_t[lab][0])} / {vs_t[lab][1]['diff']:+.1f}{sig(vs_t[lab][1])}"  # noqa: E731
    note_B = (f"Default: SVM / RF / MLP / CNN / GRU from the B1 run ({k['epochs']} epochs maximum, patience {k['patience']}, window stride {k['stride_deployed']}); the LSTM default is the deployed model of the cross-validation (same routine, window stride {k['stride_deployed']}). "
              f"Tuned (B2): {drawn} configurations drawn at random per model with a fixed seed (with replacement: {u_lo}--{u_hi} unique per model, the LSTM {uniq['Proposed LSTM']['unique']}), chosen on the inner validation split of folds 1--3 of seed 1 (mean validation window AUC) and then trained on all 15 fold-models. "
              f"The search is not nested: those validation traces are test traces of other fold-models, an optimistic bias shared by all six models. "
              f"Same routine for all neural models ({k['epochs']} epochs maximum, patience {k['patience']}, about {ep_mean:.0f} epochs used, AdamW, batch 256, window stride {k['stride_b2']}); "
              f"SVM and RF are fitted on random subsamples of {fmt_int(k['sub_svm'])} and {fmt_int(k['sub_rf'])} training windows, the neural models on all windows, so the budget is equal in configurations and epochs, not in data. "
              + f"Like-for-like reference = the tuned LSTM hybrid (same stride and budget); difference of each tuned hybrid to it, dependability / security (pt): "
              + "; ".join(fmtd(lab) for lab in ("CNN", "GRU", "ANN", "RF", "SVM")) + ". "
              + f"The tuned LSTM hybrid vs the deployed hybrid: {tl_c[0]['diff']:+.2f} / {tl_c[1]['diff']:+.2f} pt{sig(tl_c[0]) if tl_c[0]['holm_clust'] >= 0.05 and tl_c[1]['holm_clust'] >= 0.05 else ''}. "
              + f"Comparisons with the deployed hybrid (post-hoc family) mix window stride {k['stride_b2']} with {k['stride_deployed']} and are listed only in Supplementary Table S4. "
              + test_unit(nb2) + " Table names describe architectures; they are not reproductions of the cited papers.")
    short_B = (f"Default = B1 run (stride {k['stride_deployed']}; LSTM = deployed model). Tuned = B2: {drawn} drawn configurations per model, chosen on validation traces of seed 1, folds 1--3 (not nested), "
               f"{k['epochs']} epochs / patience {k['patience']}, stride {k['stride_b2']}; SVM / RF fitted on {fmt_int(k['sub_svm'])} / {fmt_int(k['sub_rf'])} subsampled windows. "
               + "Tuned hybrid minus tuned LSTM hybrid (dep. / sec., pt): " + "; ".join(fmtd(lab) for lab in ("CNN", "GRU", "ANN", "RF", "SVM")) + ". "
               + test_unit(nb2) + " Full notes: Supplementary Table S1.")
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
          r"\vspace{3pt}\par\raggedright\scriptsize\textit{Notes.} " + note_B,
          r"\end{table*}"]
    tex_write("table_B_same_features.tex", L, short_B)


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
    ct_d, ct_s = clu("N6c", "tuned harmonic vs proposed hybrid dependability"), clu("N6c", "tuned harmonic vs proposed hybrid security")
    cb_d, cb_s = clu("N6c", "textbook harmonic vs proposed hybrid dependability"), clu("N6c", "textbook harmonic vs proposed hybrid security")
    assert abs(ct_d["diff"] - n6["tests"][2]["diff_pt"]) < 1e-9 and abs(ct_s["diff"] - n6["tests"][3]["diff_pt"]) < 1e-9
    grid = {"pickup": [0.2, 0.3, 0.4], "k2": [0.12, 0.15, 0.20], "k5": [0.25, 0.35]}   # the N6c grid as fixed in BENCHMARK_FAIRNESS_PLAN.md (printed in the note)
    chosen = [c["setting"] for c in n6["chosen"]]
    assert all(any(abs(c[ix] - g_) < 1e-9 for g_ in g) for c in chosen for ix, g in enumerate(grid.values()))
    edge = []
    for ix, (nm, g) in enumerate(grid.items()):
        lo = sum(abs(c[ix] - min(g)) < 1e-9 for c in chosen); hi = sum(abs(c[ix] - max(g)) < 1e-9 for c in chosen)
        if lo: edge.append(f"{nm} at the lowest grid value in {lo} of {len(chosen)}")
        if hi: edge.append(f"{nm} at the highest in {hi} of {len(chosen)}")
    corner = "Grid boundary: " + ", ".join(edge).replace("k2", "$k_2$").replace("k5", "$k_5$") + " fold-models, so a wider grid might raise the tuned relay's dependability (not tested)."
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
         + corner + " "
         + f"Tuned harmonic 87T minus proposed hybrid: dependability {ct_d['diff']:+.2f} pt ({ptex(ct_d)}; per-seed differences {', '.join(f'{v:+.2f}' for v in n6['tests'][2]['per_seed'].values())}, sign changes: unstable), security {ct_s['diff']:+.2f} pt ({ptex(ct_s)}). "
         + f"Textbook harmonic 87T minus proposed hybrid: dependability {cb_d['diff']:+.2f} pt ({ptex(cb_d)}), security {cb_s['diff']:+.2f} pt ({ptex(cb_s)}). "
         + "; ".join(fam).replace("dependability, ", "Dependability, ").replace("_", "\\_") + ". " + test_unit(clu_n("N6c")) + " n/e = not evaluated (no new experiments).",
         r"\end{table}"]
    short_C = (corner + f" Tuned minus proposed: dependability {ct_d['diff']:+.2f} pt ({ptex(ct_d)}), security {ct_s['diff']:+.2f} pt ({ptex(ct_s)}); textbook minus proposed: {cb_d['diff']:+.2f} pt ({ptex(cb_d)}) / {cb_s['diff']:+.2f} pt ({ptex(cb_s)}). "
               + test_unit(clu_n("N6c")) + " n/e = not evaluated. Full notes: Supplementary Table S1.")
    tex_write("table_C_conventional.tex", L, short_C)


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
    CN = {"1D-CNN": "1D-CNN hybrid", "Wavelet-GRU": "Wavelet-GRU hybrid", "Wavelet-ANN": "Wavelet-ANN hybrid", "Key (claim-C run)": "Key hybrid",
          "Wavelet-RF": "Wavelet-RF hybrid", "LSTM (tuned, B2)": "Proposed LSTM hybrid"}
    cl = {(t["instance"], t["metric"]): clu("N8a", f"{CN[t['instance']]} vs tuned harmonic {t['metric']}") for t in n8l}
    for kk, t in cl.items():
        assert abs(t["diff"] - n8[kk]["diff_pt"]) < 1e-9, kk
    n_dep_sig = sum(cl[(t["instance"], "dependability")]["holm_clust"] < 0.05 and t["diff_pt"] > 0 for t in dd)
    n_sec_lower = sum(cl[(t["instance"], "security")]["holm_clust"] < 0.05 and t["diff_pt"] < 0 for t in dsec)
    sec_up = [t["instance"] for t in dsec if cl[(t["instance"], "security")]["holm_clust"] < 0.05 and t["diff_pt"] > 0]
    dep_p = [cl[(t["instance"], "dependability")]["holm_clust"] for t in dd]
    kc = {m: clu("Key hybrid", f"Key hybrid vs proposed hybrid {m}") for m in ("dependability", "security")}
    so = solo_settings()
    sig = lambda t: ("$^{*}$" if cl[(t["instance"], t["metric"])]["holm_clust"] < 0.05 else "") + ("" if t["sign_stable"] else "$^{\\dagger}$")  # noqa: E731
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
    dg, sg = gat["dependability"], gat["security"]
    common = (f"$^{{*}}$ $p_{{\\mathrm{{H}}}}<0.05$ (post-hoc family of {clu_n('N8a')} tests: {hs['n8a_new']} added after the tuned-harmonic comparison plus its {hs['n6c']}); $^{{\\dagger}}$ per-seed differences change sign. "
              + test_unit(clu_n("N8a")) + " "
              + f"{n_dep_sig} of {len(dd)} instances are significantly more dependable than the tuned harmonic 87T ({min(t['diff_pt'] for t in dd):+.1f} to {max(t['diff_pt'] for t in dd):+.1f} pt, $p_{{\\mathrm{{H}}}}\\le{sci(max(dep_p))}$); "
              + (", ".join(INST_LABEL.get(x, x) for x in sec_up) + " significantly more secure; " if sec_up else "") + ("none is" if n_sec_lower == 0 else f"{n_sec_lower} are") + " significantly less secure. "
              + f"In {so['solo_off']} of {so['n']} CV fold-models of the deployed LSTM the plateau rule switched the AI-alone path off (AI threshold {so['ai_min']}--{so['ai_max']}), so its CV row mixes dual-path and gated-only fold-models. ")
    note_D = (common
              + r"The B2 instances were evaluated in cross-validation only (n/e = not evaluated). Key's classifier is the Dis-DNN internal-fault probability sampled at the relay's decision instants inside the identical logic. "
              + f"Plant B, deployed hybrid: {ftp.get('solo', 0)} of {n_ft} false trips first came from the AI-alone path, {ftp.get('gate', 0)} from the gated path, {ftp.get('highset', 0) or 'none'} from the high-set; Key hybrid: {pf['solo']} of {n_kb_h} healthy traces tripped by the AI-alone path, {pf['gate']} gated, {pf['highset']} high-set. "
              + f"Gated-only (post-hoc counterfactual from saved decisions, descriptive): on the plant-A CV it loses {dg['deployed_only_correct']} fault decisions and gains {sg['gated_only_correct']} healthy decisions (counted over the three repetitions), {dg['diff_pt']:+.2f} / {sg['diff_pt']:+.2f} pt. "
              + f"Key hybrid minus proposed hybrid: dependability {kc['dependability']['diff']:+.2f} pt ({ptex(kc['dependability'])}), security {kc['security']['diff']:+.2f} pt ({ptex(kc['security'])}); Holm family of {clu_n('Key hybrid')}.")
    short_D = common + f"Plant B false trips of the deployed hybrid: {ftp.get('solo', 0)} of {n_ft} via the AI-alone path. Gated only = AI-alone path off (post-hoc). n/e = not evaluated. Full notes: Supplementary Table S1."
    L += [r"\bottomrule\end{tabular}",
          r"\vspace{3pt}\par\raggedright\scriptsize\textit{Notes.} " + note_D,
          r"\end{table*}"]
    tex_write("table_D_instances.tex", L, short_D)


def build_all() -> None:
    table_A(); table_B(); table_C(); table_D()


if __name__ == "__main__":
    build_all()
