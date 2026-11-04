**Conventional relays on the benchmark data (dependability / security, %): unrestrained dual-slope 87T, harmonic-restrained 87T with textbook settings, and harmonic-restrained 87T tuned on validation traces, against the proposed relay. Plant-A CV (3 seeds × 5 folds, common set), OOD (final scoring) and plant-B zero-shot.**

| Relay | CV |  | OOD |  | Plant B |  |
|  | dep. | sec. | dep. | sec. | dep. | sec. |
|---|---|---|---|---|---|---|
| 87T unrestrained (dual slope, 0.30 pu pickup) | 80.3 | 63.5 | 89.3 | 53.3 | 89.5 | 62.0 |
| Harmonic 87T, textbook (0.30 pu, k2 0.15, k5 0.35) | 86.0 | 99.4 | 94.0 | 88.7 | 94.1 | 99.0 |
| Harmonic 87T, tuned on validation | 91.2 | 99.1 | n/e | n/e | n/e | n/e |
| Proposed relay (deployed LSTM hybrid) | 93.0 | 99.0 | 98.0 | 96.0 | 92.7 | 88.4 |

*Notes.* Tuned = grid pickup {0.2, 0.3, 0.4} pu × k2 {0.12, 0.15, 0.20} × k5 {0.25, 0.35}, chosen per fold on validation traces by the plateau rule (fills fixed before the run); chosen settings over the 15 fold-models: (0.2, 0.2, 0.25) in 9; (0.2, 0.15, 0.25) in 6. Grid boundary: pickup at the lowest grid value in 15 of 15, k2 at the highest in 9 of 15, k5 at the lowest grid value in 15 of 15 fold-models, so a wider grid might raise the tuned relay's dependability (not tested). Tuned harmonic 87T minus proposed hybrid: dependability -1.78 pt ($p_{\mathrm{H}}=5\times10^{-3}$; per-seed differences -2.66, -2.82, +0.16, sign changes: unstable), security +0.12 pt ($p_{\mathrm{H}}=0.68$). Textbook harmonic 87T minus proposed hybrid: dependability -6.99 pt ($p_{\mathrm{H}}\le2\times10^{-5}$), security +0.44 pt ($p_{\mathrm{H}}=0.11$). Dependability, Internal_HiZ (n=459): hybrid 65.4, tuned harmonic 62.1, textbook harmonic 51.0; Dependability, other internal faults (n=3258): hybrid 96.8, tuned harmonic 95.3, textbook harmonic 90.9. Significance: trace-clustered sign-flip permutation test (test unit = trace; per-trace difference averaged over the three CV repetitions; 200,000 draws), Holm-adjusted within a family of 4 tests. n/e = not evaluated (no new experiments).

