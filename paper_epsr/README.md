# EPSR manuscript (paper-v1)

Claim C: a model-agnostic dual-path supervisory logic for transformer differential protection, evaluated with a leak-free benchmark of six reproduced methods.

## Build (no MATLAB needed; every number comes from saved files)
```
python tools/publication_tables_AD.py         # Tables A-D (full notes -> generated/, short notes -> generated/paper/); also rewrites latex_source/latex/table_[A-D]_*.tex
python tools/paper_operate_times.py          # Table E (operate time) + generated/operate_times.json
python tools/build_abstract_draft_n8b.py     # abstract (generated/abstract.tex) + ABSTRACT_DRAFT.md with its number-to-source map
python tools/build_paper_v1_macros.py        # generated/paper_macros.tex (every number in the text)
python tools/build_supplement_tables.py      # supplementary test lists S3-S7 and the spec list
python tools/make_paper_figures.py           # figures/*.pdf (vector, fonts embedded)
python tools/build_paper_bib.py              # refs.bib from audit/literature_table.csv (needs internet: Crossref)
python tools/check_paper.py                  # static checks + EPSR word count -> generated/check_report.txt
pdflatex main; bibtex main; pdflatex main; pdflatex main
pdflatex supplementary; pdflatex supplementary
```
Python: numpy, scipy, scikit-learn, statsmodels, matplotlib (see `audit/requirements.txt`). The thesis is frozen: restore `latex_source/latex/table_[A-D]_*.tex` after the first command if the thesis must not change (`git checkout latex_source/latex/`).

TeX: `texlive-publishers` (elsarticle), `texlive-latex-extra`, `texlive-fonts-recommended` (Latin Modern, vector fonts), `texlive-pictures` (TikZ).
Checked 2026-11-04 in the cloud session (TeX Live 2023): `main.tex` and `supplementary.tex` compile with 0 errors and 0 undefined references or citations;
the compiled `main.pdf` and `supplementary.pdf` are committed for review (regenerate them after any change).

## Files
- `main.tex` manuscript; `supplementary.tex` supplementary material (full table notes, reproduction specs, all paired tests, order of decisions, audit).
- `highlights.txt` 5 highlights, each <= 85 characters.
- `refs.bib` generated; verified references only (one marked TODO, see below).
- `ABSTRACT_DRAFT.md` abstract with its number-to-source map and checks; `abstract_draft_N8b.txt` is the earlier 279-word draft (record only).
- `figures/` generated figures; `generated/` generated tables, macros, abstract and check report. Do not edit generated files by hand.

## Placeholders for the author (red `[AUTHOR: ...]` in the PDF)
1. Author names; department and institution; city; country (front matter; plain-text capitals `AUTHOR NAMES`, `DEPARTMENT, INSTITUTION`, `CITY`, `COUNTRY`, because the elsarticle front matter does not take colour macros).
2. AI coding assistant: tool name, version and developer (Methods, "AI-assisted code and analysis"); confirm which prompts / plans / logs are published.
3. Data and code availability: release tag and commit; dataset / model deposit (DOI) or "on request"; MATLAB/Simulink release and toolboxes.
4. CRediT authorship statement.
5. Funding statement.
6. Declaration of competing interest.
7. Acknowledgements.
8. Declaration of generative AI and AI-assisted technologies in the manuscript preparation process (your own wording; Elsevier policy).
9. Cover letter with the word count (`generated/check_report.txt`), not in this folder.

## References still to check
- `holm1979` (Holm, Scand. J. Statist. 1979): no DOI, JSTOR blocked the audit; open JSTOR 4615733 and confirm.
- Three references outside `audit/literature_table.csv` were added and resolved on Crossref by `tools/build_paper_bib.py`: Hochreiter & Schmidhuber 1997, Mallat 1989, Hajipour et al. 2015.

## Figures that need local data (not producible in the cloud)
- Waveform examples (differential current, harmonic ratio and classifier score for an inrush, an internal fault, an external fault with CT saturation and a high-impedance fault): need the `.mat` datasets or the feature cache (`traces_cache.npz`), which are not on GitHub.
- A plant schematic (single-line diagram of plants A and B): `latex_source/latex/SLD_300MVA_Yd1_protection.pdf` exists for plant A; plant B has none.
- Optional: closed-loop trip-time traces from Simulink.
