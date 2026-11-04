"""Static checks of the paper-v1 manuscript (no LaTeX compiler needed) and the EPSR word count.

- every macro used is defined, every \\cite key is in refs.bib, every \\ref has a \\label, every \\input / \\includegraphics file exists;
- balanced braces; banned words; the word "pre-registered"; leftover [cite: ...] placeholders;
- digits typed in the prose of main.tex (must come from macros) are listed;
- word count as EPSR counts it: abstract, text, tables, figure captions and appendices; references and acknowledgements excluded.
Output: paper_epsr/generated/check_report.txt.   python tools/check_paper.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper_epsr"
BANNED = ("best", "superior", "state of the art", "state-of-the-art", "outperforms all", "pre-registered", "preregistered", "pre-registration")
LATEX_OK = set("""documentclass usepackage usetikzlibrary input newcommand journal begin end title author affiliation sep section subsection
textbf emph citep cite label ref item centering caption includegraphics textwidth node draw textit url bibliographystyle bibliography
toprule midrule bottomrule addlinespace multicolumn scriptsize footnotesize small setlength tabcolsep vspace par raggedright textmu
times le geq ge vee wedge big text mathrm hat theta Delta dagger ddagger triangle gamma placeholder textcolor appendix
makeatletter makeatother renewcommand thetable thefigure thesection setcounter clearpage linewidth hline resizebox newpage
maketitle date tableofcontents footnote noindent quad qquad ldots dots cdot pm approx sim infty alpha beta mu sigma rho tau
leq neq nolinebreak hspace smallskip medskip bigskip hfill""".split())


def strip_comments(t: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", t)


def expand(path: Path, seen: set | None = None) -> str:
    seen = seen or set()
    t = strip_comments(path.read_text(encoding="utf-8"))

    def rep(m):
        f = (path.parent / m.group(1))
        f = f if f.suffix else f.with_suffix(".tex")
        if f in seen or "macros" in f.name:
            return ""
        seen.add(f)
        return expand(f, seen) if f.is_file() else f"<<MISSING {m.group(1)}>>"
    return re.sub(r"\\input\{([^}]*)\}", rep, t)


def macros() -> dict[str, str]:
    t = (PAPER / "generated" / "paper_macros.tex").read_text(encoding="utf-8")
    return dict(re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", t))


def to_words(t: str, M: dict[str, str]) -> str:
    for _ in range(2):
        t = re.sub(r"\\(\w+)(\{\})?", lambda m: M.get(m.group(1), " " if m.group(1) not in ("textbf", "emph", "textit") else ""), t)
    t = re.sub(r"\\cite\w*\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}", " ", t)
    t = re.sub(r"[{}$&\\^_~]", " ", t)
    return t


def main() -> None:
    rep: list[str] = []
    M = macros()
    bib = set(re.findall(r"^@\w+\{([^,]+),", (PAPER / "refs.bib").read_text(encoding="utf-8"), re.M))
    for name in ("main.tex", "supplementary.tex"):
        f = PAPER / name
        if not f.is_file():
            rep.append(f"{name}: MISSING"); continue
        full = expand(f)
        own = set(re.findall(r"\\newcommand\{\\(\w+)\}", full))
        used = set(re.findall(r"\\([A-Za-z]+)", full))
        undefined = sorted(u for u in used - set(M) - own - LATEX_OK if not u.startswith(("text", "math", "small", "large", "Large", "normal")))
        rep.append(f"{name}: commands not defined by the macros file (check they are LaTeX/package commands): {undefined}")
        cites = {k.strip() for c in re.findall(r"\\cite\w*\{([^}]*)\}", full) for k in c.split(",")}
        rep.append(f"{name}: {len(cites)} cited keys; missing in refs.bib: {sorted(cites - bib)}")
        labels = set(re.findall(r"\\label\{([^}]*)\}", full)); refs = set(re.findall(r"\\ref\{([^}]*)\}", full))
        rep.append(f"{name}: refs without label: {sorted(refs - labels)}")
        rep.append(f"{name}: missing inputs: {re.findall(r'<<MISSING ([^>]*)>>', full)}")
        figs = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]*)\}", full)
        rep.append(f"{name}: missing figures: {[g for g in figs if not (PAPER / g).is_file()]}")
        depth = 0; bad = False
        for ch in re.sub(r"\\[{}]", "", full):
            depth += (ch == "{") - (ch == "}"); bad |= depth < 0
        rep.append(f"{name}: brace balance {depth} (negative at some point: {bad})")
        low = to_words(full, M).lower()
        rep.append(f"{name}: banned / forbidden words: {[b for b in BANNED if re.search(rf'(?<![a-z]){re.escape(b)}(?![a-z])', low)]}")
        rep.append(f"{name}: [cite: placeholders: {full.count('[cite:')}")
        rep.append(f"{name}: placeholders for the author: {max(0, full.count(chr(92) + "placeholder{") - 1)}")   # minus the \\newcommand definition
    # digits typed in the prose of main.tex (outside macros, math, refs, environments with generated content)
    body = strip_comments((PAPER / "main.tex").read_text(encoding="utf-8"))
    body = body[body.index("\\section{Introduction}"):body.index("\\bibliographystyle")]
    prose = re.sub(r"\$[^$]*\$|\\(cite\w*|ref|label|input|includegraphics|begin|end|url)(\[[^]]*\])?\{[^}]*\}|\\[A-Za-z]+", " ", body)
    prose = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", prose, flags=re.S)
    tikz = re.search(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", body, re.S)
    if tikz:
        prose = prose.replace(re.sub(r"\$[^$]*\$|\\[A-Za-z]+", " ", tikz.group(0)), " ")
    digits = sorted(set(re.findall(r"(?<![A-Za-z])\d[\d.,]*(?![A-Za-z]*\d)", prose)))
    rep.append(f"main.tex prose: digit strings typed by hand (allowed: 87T, 1D-CNN, figure/section numbers, years, model names): {digits}")
    # EPSR word count
    full = expand(PAPER / "main.tex")
    a = full[full.index("\\begin{abstract}"):]
    a = a[:a.index("\\section*{Acknowledgements}")] + a[a.index("\\section*{Declaration of generative AI"):a.index("\\bibliographystyle")]
    a = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", a, flags=re.S)
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.,'/+%-]*", to_words(a, M)))
    ab = full[full.index("\\begin{abstract}"):full.index("\\end{abstract}")]
    rep.append(f"EPSR word count (abstract + text + tables + captions + declarations; references and acknowledgements excluded): {words}")
    rep.append(f"abstract words: {len(re.findall(r'[A-Za-z0-9][A-Za-z0-9.,/+%-]*', to_words(ab, M)))}")
    hl = (PAPER / "highlights.txt").read_text(encoding="utf-8").strip().splitlines()
    rep.append(f"highlights: {len(hl)} bullets, lengths {[len(h) for h in hl]} (limit 85)")
    out = PAPER / "generated" / "check_report.txt"
    out.write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
