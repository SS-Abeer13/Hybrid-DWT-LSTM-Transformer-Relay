# Publication tables A–D (D-N8c)

Built by `tools/publication_tables_AD.py` (called from `tools/build_publication_tables_v5.py`, or alone:
`python -c "import sys; sys.path.insert(0,'tools'); import publication_tables_AD as AD; AD.build_all()"`).
Each table is written as LaTeX (`*.tex`, identical to `paper_epsr/generated/` and `latex_source/latex/`) and as Markdown (`*.md`, converted
from the same LaTeX lines, so the numbers are identical). Do not edit these files by hand; re-run the script.

- **A** `table_A_reproductions` — six reproductions, native + like-for-like, CV / OOD / plant B, latency.
- **B** `table_B_same_features` — same-feature models, standalone + hybrid, default (B1) + tuned (B2).
- **C** `table_C_conventional` — 87T, harmonic 87T textbook, harmonic 87T tuned on validation.
- **D** `table_D_instances` — architecture instances vs the tuned harmonic 87T (post-hoc, Holm-16) + gated-only ablation.

Every result number in cells, captions and notes is read from a saved file under `runs/` or `documents/baselines/`
(Holm family sizes are counted from the saved test lists; per-seed instability flags come from the saved per-seed differences).
Only **protocol constants** are written as text: sampling rates of each method and of the relay (1.6 kHz, 625 µs budget), the 20-sample dwell (12.5 ms),
the N6c grid (pickup {0.2, 0.3, 0.4} pu, k2 {0.12, 0.15, 0.20}, k5 {0.25, 0.35}) and textbook setting (0.30 / 0.15 / 0.35), the training routine
(25 epochs maximum, patience 5, AdamW, batch 256, strides 4 / 8), the search split (folds 1–3 of seed 1) and the 12 DWT + second-harmonic features
(IMPLEMENTATION_PLAN_V3.md section 3, BENCHMARK_FAIRNESS_PLAN.md).
