"""N7: apply the author-approved reference fixes of documents/reference_fixes_N7.md to latex_source/latex/main.tex
(and the one citation label in generate_thesis_tables_and_macros.py).

Same approach as R0 (tools/reference_audit_report.py): main.tex is patched in place, because rebuild_thesis_manuscript.py is stale
since 2026-10-27 (re-running it would also undo R0). Every replacement must match exactly once; if any does not, nothing is written.
Keys are kept where a reference is corrected / replaced (citation numbering stays stable); ref33 and ref35 are removed;
ref41-ref43 are new (the extra sources that replace ref5 in two sentences). Every DOI was resolved on Crossref on 2026-11-04.

Defaults for the four open points of reference_fixes_N7.md (the conservative option in each case, author approved the file as a whole):
  L248 and L446 lose their citation; L259 keeps ref11 only; L254 drops the unsupported "renewables / converters" clause;
  the ref18 row of Table tab:litcompare shows n/r instead of the 99.1 % that belonged to the non-existent paper.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "latex_source" / "latex" / "main.tex"
GEN = ROOT / "generate_thesis_tables_and_macros.py"
MARK = "% N7 2026-11-04: {s} (see documents/reference_fixes_N7.md)"
R0 = "% R0 2026-10-31: UNVERIFIED (see documents/reference_audit.md)\n"

BIB = {
    "ref2": ("REPLACED", r"Q. Alhamd, M. Saniei, and S. G. Seifossadat, ``Advanced detection and discrimination of power transformer internal faults from other abnormal condition using DWT-based feature extraction and ANN classifier,'' \textit{Periodicals of Engineering and Natural Sciences}, vol.~12, no.~1, pp.~236--254, 2024. doi:10.21533/pen.v12.i1.33."),
    "ref5": ("REPLACED", r"S. Santoso, E. J. Powers, W. M. Grady, and P. Hofmann, ``Power quality assessment via wavelet transform analysis,'' \textit{IEEE Transactions on Power Delivery}, vol.~11, no.~2, pp.~924--930, 1996. doi:10.1109/61.489353."),
    "ref10": ("REPLACED", r"M. Raichura, N. Chothani, and D. Patel, ``Review of methodologies used for detection of magnetising inrush and fault conditions in power transformer,'' \textit{IET Energy Systems Integration}, vol.~3, no.~2, pp.~109--129, 2021. doi:10.1049/esi2.12012."),
    "ref18": ("REPLACED", r"P. L. Mao and R. K. Aggarwal, ``A novel approach to the classification of the transient phenomena in power transformers using combined wavelet transform and neural network,'' \textit{IEEE Transactions on Power Delivery}, vol.~16, no.~4, pp.~654--660, 2001. doi:10.1109/61.956753."),
    "ref31": ("REPLACED", r"S. A. Saleh, B. Scaplen, and M. A. Rahman, ``A new implementation method of wavelet-packet-transform differential protection for power transformers,'' \textit{IEEE Transactions on Industry Applications}, vol.~47, no.~2, pp.~1003--1012, 2011. doi:10.1109/tia.2010.2103545."),
    "ref32": ("CORRECTED", r"B. Kasztenny, E. Rosolowski, and M. Lukowicz, ``Multi-objective optimization of a neural network based differential relay for power transformers,'' \textit{1999 IEEE Transmission and Distribution Conference}, vol.~2, pp.~476--481, 1999. doi:10.1109/tdc.1999.756100."),
    "ref34": ("REPLACED", r"M. Tripathy, ``Neural network principal component analysis based power transformer differential protection,'' \textit{2009 International Conference on Power Systems}, pp.~1--6, 2009. doi:10.1109/icpws.2009.5442748."),
}
NEW = [
    ("ref41", r"S. G. Mallat, ``A theory for multiresolution signal decomposition: the wavelet representation,'' \textit{IEEE Transactions on Pattern Analysis and Machine Intelligence}, vol.~11, no.~7, pp.~674--693, 1989. doi:10.1109/34.192463."),
    ("ref42", r"\textit{IEEE Guide for Protecting Power Transformers}, IEEE Std C37.91-2021, 2021. doi:10.1109/ieeestd.2021.9471045."),
    ("ref43", r"R. Hamilton, ``Analysis of transformer inrush current and comparison of harmonic restraint methods in transformer protection,'' \textit{IEEE Transactions on Industry Applications}, vol.~49, no.~4, pp.~1890--1899, 2013. doi:10.1109/tia.2013.2257155."),
]
DROP = ("ref33", "ref35")

TEXT = [  # (old, new) - each old string must occur exactly once
    # ref2
    (r"potential cascading failures~\cite{ref2}.", r"potential cascading failures."),
    (r"\textbf{LSTM Models.} Alhamd et al.~\cite{ref1,ref2} deployed LSTM networks with wavelet features under CT saturation,",
     r"\textbf{LSTM Models.} Alhamd et al. used DWT features with an ANN classifier~\cite{ref2} and LSTM networks with improved wavelet features under CT saturation~\cite{ref1},"),
    (r"\cite{ref1,ref2} & Improved wavelet & LSTM &", r"\cite{ref1} & Improved wavelet & LSTM &"),
    (r"(e.g., Alhamd et al.~\cite{ref1,ref2}, Atiyah et al.~\cite{ref3})", r"(e.g., Alhamd et al.~\cite{ref1}, Atiyah et al.~\cite{ref3})"),
    (r"training, validation, and deployment~\cite{ref1,ref2}.", r"training, validation, and deployment."),
    # ref5 (+ ref41-43)
    (r"and overexcitation introduces additional harmonic components~\cite{ref5}.", r"and overexcitation introduces additional (mainly fifth) harmonic components~\cite{ref42}."),
    (r"Traditional current harmonic restraint (CHR) and blocking methods face increasing limitations as renewable sources, power-electronic converters, and advanced core materials alter the waveform signatures conventional relays depend upon~\cite{ref5,ref6}.",
     r"Traditional current harmonic restraint (CHR) and blocking methods face increasing limitations; for example, modern low-loss core steels can lower the second-harmonic content of inrush currents below common restraint settings~\cite{ref43}."),
    (r"with downsampling for multi-resolution decomposition~\cite{ref5}.", r"with downsampling for multi-resolution decomposition~\cite{ref41}."),
    # ref10
    (r"from non-fault transients~\cite{ref10,ref11}.", r"from non-fault transients~\cite{ref11}."),
    (r"Extensive surveys on transformer fault classification methodologies have documented this evolution~\cite{ref10}.",
     r"A recent review of inrush and internal-fault detection methods documents this evolution~\cite{ref10}."),
    # ref18 + ref32
    (r"Three-layer neural networks with wavelet feature inputs were explored by Ngaopitakkul and Kunakorn~\cite{ref19} and Costa et al.~\cite{ref18}, attaining over 99\% classification accuracy on specific test topologies.",
     r"Neural networks with wavelet feature inputs were explored by Mao and Aggarwal~\cite{ref18} and Ngaopitakkul and Kunakorn~\cite{ref19}, with high classification accuracy on their specific test systems."),
    (r"while Kasztenny and Rosolowski~\cite{ref32} explored adaptive neural network protection schemes.",
     r"while Kasztenny et al.~\cite{ref32} optimised a neural-network-based differential relay for power transformers with multiple objectives."),
    (r"\cite{ref18} & Wavelet stats & ANN & 99.1 & No temporal context\\", r"\cite{ref18} & Wavelet & ANN & n/r & No temporal context\\"),
    (r"(overall classification accuracy is 99.39\%).", r"(overall classification accuracy is 99.39\%). n/r = value not yet checked against the cited paper."),
    # ref31 + ref34
    (r"Independent component analysis (ICA)~\cite{ref34} and wavelet packet transforms~\cite{ref31} have also been explored to decompose complex transient modes.",
     r"Principal component analysis~\cite{ref34} and wavelet packet transforms~\cite{ref31} have also been used to extract features from differential-current transients."),
    # ref33, ref35: sentences deleted
    (r" Gajic et al.~\cite{ref33} investigated smart processing techniques for modern digital substations.", ""),
    (r" Statistical and volatility-tracking formulations, such as the Generalized Autoregressive Conditional Heteroskedasticity (GARCH) model proposed by Hooshyar et al.~\cite{ref35}, characterize the time-varying variance of differential currents under non-fault transients.", ""),
]
GEN_TEXT = [(r'"Wavelet-ANN": r"Ngaopitakkul \cite{ref19} / Costa \cite{ref18}",', r'"Wavelet-ANN": r"Ngaopitakkul \cite{ref19} / Mao \cite{ref18}",')]


def sub_once(s: str, old: str, new: str, where: str, errors: list[str]) -> str:
    n = s.count(old)
    if n != 1:
        errors.append(f"{where}: expected 1 match, found {n}: {old[:90]}")
        return s
    return s.replace(old, new)


def main() -> None:
    tex, gen = TEX.read_text(encoding="utf-8"), GEN.read_text(encoding="utf-8")
    if "% N7 2026-11-04" in tex:
        sys.exit("main.tex already carries the N7 fixes; nothing done")
    err: list[str] = []
    for old, new in TEXT:
        tex = sub_once(tex, old, new, "main.tex text", err)
    for k, (status, entry) in BIB.items():
        m = re.search(r"(% R0 2026-10-31: UNVERIFIED \(see documents/reference_audit\.md\)\n)?\\bibitem\{" + k + r"\}[^\n]*", tex)
        if not m:
            err.append(f"bibitem {k} not found"); continue
        tex = tex[:m.start()] + MARK.format(s=status) + "\n" + rf"\bibitem{{{k}}} " + entry + tex[m.end():]
    for k in DROP:
        tex, n = re.subn(r"(% R0 2026-10-31: UNVERIFIED \(see documents/reference_audit\.md\)\n)?\\bibitem\{" + k + r"\}[^\n]*\n", "", tex)
        if n != 1:
            err.append(f"bibitem {k}: removed {n}")
    add = "".join(MARK.format(s="NEW") + "\n" + rf"\bibitem{{{k}}} {e}" + "\n" for k, e in NEW)
    tex = sub_once(tex, "\\end{thebibliography}", add + "\\end{thebibliography}", "bibliography end", err)
    for old, new in GEN_TEXT:
        gen = sub_once(gen, old, new, "generate_thesis_tables_and_macros.py", err)
    # consistency: every cited key has a bibitem, no bibitem of a dropped key, no citation of a dropped key
    cited = {k.strip() for c in re.findall(r"\\cite\{([^}]*)\}", tex) for k in c.split(",")}
    items = set(re.findall(r"\\bibitem\{([^}]*)\}", tex))
    if cited - items:
        err.append(f"cited without bibitem: {sorted(cited - items)}")
    if set(DROP) & (cited | items):
        err.append(f"dropped keys still present: {sorted(set(DROP) & (cited | items))}")
    if R0 in tex:
        left = re.findall(r"% R0 2026-10-31: UNVERIFIED[^\n]*\n\\bibitem\{([^}]*)\}", tex)
        err.append(f"UNVERIFIED flags left: {left}")
    if err:
        sys.exit("NOT WRITTEN:\n" + "\n".join(err))
    TEX.write_text(tex, encoding="utf-8"); GEN.write_text(gen, encoding="utf-8")
    print(f"main.tex: {len(TEXT)} text edits, {len(BIB)} bibitems replaced/corrected, {len(DROP)} removed, {len(NEW)} added; "
          f"{len(items)} bibitems, all {len(cited)} cited keys resolved; uncited bibitems: {sorted(items - cited)}")


if __name__ == "__main__":
    main()
