"""Supplementary tables (paper-v1) from audit/scripts/out/clustered_sensitivity.json: every paired test with its difference, the pooled
McNemar p (Holm, unit = (seed, fold, trace) decision, reported for transparency only) and the trace-clustered p (Holm, unit = trace) used in the paper.
Also the list of reproduction specification files. Output: paper_epsr/generated/supp_*.tex.   python tools/build_supplement_tables.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import publication_tables_AD as AD  # noqa: E402

ROOT = AD.ROOT
OUT = ROOT / "paper_epsr" / "generated"
FAMS = [("N5b", "S3", "Reproductions vs the proposed relay and vs the LSTM alone, native and like-for-like"),
        ("B2", "S4", "Same-feature hybrids (B2): vs the tuned LSTM hybrid (planned) and vs the deployed hybrid (post-hoc; window stride 4 vs 8)"),
        ("N8a", "S5", "Instances of the logic vs the validation-tuned harmonic 87T (post-hoc)"),
        ("N6c", "S6", "Harmonic 87T (textbook and tuned) vs the proposed relay"),
        ("Key hybrid", "S7", "Key's network inside the logic vs the deployed LSTM instance")]


def esc(s: str, names: bool = True) -> str:
    s = s.replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")
    return s.replace("simoes\\_grid", r"Sim\~oes") if names else s


def p(x: float, floor: bool) -> str:
    if x >= 0.01:
        return f"{x:.2f}"
    m, e = f"{x:.0e}".split("e")
    return f"${'\\le ' if floor else ''}{m}\\times10^{{{int(e)}}}$"


def main() -> None:
    for fam, tab, title in FAMS:
        key = [k for k in AD.CLU if k.startswith(fam)][0]
        n = AD.clu_n(fam)
        L = [r"\begin{longtable}{@{}p{8.6cm}rrr@{}}",
             r"\caption{" + f"{title}. " + AD.test_unit(n) + r" Pooled = exact McNemar on (seed, fold, trace) decisions, Holm in the same family (each trace counted up to three times; shown for transparency, not used for the marks).}\label{tab:" + tab + r"}\\",
             r"\toprule Comparison (difference = first minus second, pt) & diff. & $p_{\mathrm{H}}$ pooled & $p_{\mathrm{H}}$ clustered \\ \midrule \endfirsthead",
             r"\toprule Comparison & diff. & $p_{\mathrm{H}}$ pooled & $p_{\mathrm{H}}$ clustered \\ \midrule \endhead"]
        for t in AD.CLU[key]:
            floor = t["p_clust"] <= AD.PERM_FLOOR * 1.0001
            L.append(f"{esc(t['label'])} & {t['diff']:+.2f} & {p(t['holm_pooled'], False)} & {p(t['holm_clust'], floor)}"
                     + (r"$^{*}$" if t["holm_clust"] < 0.05 else "") + r" \\")
        L += [r"\bottomrule", r"\end{longtable}"]
        (OUT / f"supp_{tab}.tex").write_text("\n".join(L), encoding="utf-8")
    specs = sorted((ROOT / "documents" / "baselines").glob("*_spec.md"))
    L = [r"\begin{itemize}"]
    for s_ in specs:
        first = next((ln for ln in s_.read_text(encoding="utf-8").splitlines() if ln.startswith("Paper:") or ln.startswith("# ")), s_.stem)
        L.append(r"\item \texttt{" + esc(str(s_.relative_to(ROOT)), names=False) + "}: " + esc(re.sub(r"[*`#]", "", first)[:200]))
    L.append(r"\end{itemize}")
    (OUT / "supp_specs.tex").write_text("\n".join(L), encoding="utf-8")
    print("supplementary tables written:", ", ".join(t for _, t, _ in FAMS), "+ spec list")


if __name__ == "__main__":
    main()
