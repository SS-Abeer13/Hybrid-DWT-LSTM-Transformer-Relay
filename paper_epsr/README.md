# Paper draft (Electric Power Systems Research)

Build: `python tools/build_paper_macros_v5.py` (writes `generated/results_macros.tex` and the tables from the saved result files), then
`pdflatex main; bibtex main; pdflatex main; pdflatex main` in this folder.

- `main.tex`: draft; every number is a macro from `generated/results_macros.tex`; red `[cite: ...]` marks a reference that is not yet looked up.
- `refs.bib`: only entries that still have to be checked against the publisher record before submission.
- `REFERENCES_TO_VERIFY.md`: the 37 thesis bibliography entries as unverified candidates.
- `highlights.txt`: five highlights, each at most 85 characters (journal requirement).
- Open: figures from the v5 data (per-category results, trip-time distribution, plant schematic), related work text, author block, declarations, cover letter, review by a supervisor or protection engineer.
