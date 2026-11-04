**Six published methods re-implemented and trained on the benchmark data (native decision logic and like-for-like mode), against the proposed relay. Dependability / security in %; CV = plant A, 3 seeds × 5 folds, common set (3,302 traces), mean over seeds; OOD and plant B: one final model scored once (plant B zero-shot, logic and threshold frozen from plant A). The reproductions are re-implementations trained on our data, not the authors' code.**

| Method | Mode | CV |  | OOD |  | Plant B |  | Rate | Latency per decision (median / budget) |
|  |  | dep. | sec. | dep. | sec. | dep. | sec. |  |  |
|---|---|---|---|---|---|---|---|---|---|
| Simões et al. 2021 (RT-BSWT + 2 SVMs; C, γ searched) | native | 69.7 | 92.2 | 70.9 | 73.8 | 83.2 | 89.4 | 12.8 kHz | 7.5 / 78.1 µs per sample; SVM 1 498 µs per detection |
|  | like-for-like | 76.8 | 72.1 | 75.0 | 60.4 | 86.7 | 71.7 |  |  |
| Ngaopitakkul & Kunakorn 2006 (db4 DWT + BPNN)△ | native‡ | 27.7 | 99.3 | 20.3 | 99.3 | 28.0 | 97.6 | 20 kHz | 3.3 / 50 µs per sample |
|  | like-for-like | 38.4 | 97.5 | 35.1 | 98.0 | 61.3 | 90.5 |  |  |
| Abdusalam et al. 2022 (DWT + OMP + BA + SVM) | native | 76.4 | 99.9 | 83.1 | 94.0 | 71.4 | 99.7 | 10 kHz | 609 / 2.5 ms per window: not real-time |
|  | like-for-like | 79.2 | 92.9 | 84.5 | 86.6 | 89.2 | 95.5 |  |  |
| Afrasiabi et al. 2020 (CNN, with Hajipour CT stage) | native‡ | 86.7 | 88.6 | 95.3 | 94.6 | 87.5 | 75.2 | 5.6 kHz | 117 / 1250 µs per decision |
|  | like-for-like | 87.3 | 99.6 | 86.5 | 100.0 | 93.9 | 99.9 |  |  |
| Key et al. 2025 (Com-DNN + Dis-DNN) | native‡ | 97.0 | 75.3 | 96.6 | 78.5 | 98.2 | 69.7 | 3.2 kHz | 37.0 / 312.5 µs per sample |
|  | like-for-like | 97.2 | 99.6 | 98.0 | 96.0 | 96.9 | 98.9 |  |  |
| Alhamd et al. 2024 (RT-BSWT + BiLSTM) | native‡ | 96.5 | 82.9 | 97.3 | 87.2 | 92.6 | 83.8 | 3 kHz | 1166–1169 / 1667 µs per decision (trained configs; largest search-space config 1799 µs) |
|  | like-for-like | 97.9 | 98.2 | 95.3 | 95.3 | 90.0 | 96.2 |  |  |
| Proposed relay (deployed LSTM, dual-path) | hybrid | 93.0 | 99.0 | 98.0 | 96.0 | 92.7 | 88.4 | 1.6 kHz | 140 / 625 µs (ONNX) |
| LSTM alone (same logic, no 87T path) | standalone | 97.7 | 95.6 | 99.3 | 87.3 | 92.9 | 87.3 |  |  |

*Notes.* Like-for-like = 20-sample dwell (12.5 ms) with a threshold tuned on validation traces (plateau rule) plus the relay's high-set element; Simões and Ngaopitakkul act once per detector firing (no dwell). Native = the method's own decision rule (the "as intended" row). Reproductions are scored on the traces that exist in the 20 kHz re-simulation (plant A 3,302 of 3,332, OOD 297, plant B 1,278); the proposed-relay rows use all evaluable traces (OOD 299, plant B 1,257). ‡ fold-model standard deviation >3 pt: report the range, do not rank by the mean. △ the paper's sanity check holds on noise-free currents but not on the benchmark's CT secondaries with measurement noise (detector fires in 12–38 % of internal-fault traces; spec amendment 8); the lumped plants have almost no energy above 1.6 kHz (no winding capacitances), which also limits Simões. Variants in the appendix: Simões with the published $C,\gamma$ 59.9 / 95.3; Afrasiabi without the Hajipour stage 86.4 / 88.1 (the stage is nearly inactive on our CT-stress traces); Abdusalam GA + SVM 77.2 / 99.9; Alhamd with the reduced CPU budget 85.8 / 54.9 (native, CV). Simões' detector factor was chosen on validation traces (50 or 100): it finds 86–92 % of events, which caps its dependability (decision rule fixed in a dated plan before the analysis). Latency: single thread, development PC, Python; networks at the largest search-space size except Alhamd (trained configurations listed); n/e = not evaluated. Paired comparisons with the proposed relay (native and like-for-like, 48 tests) are listed in Supplementary Table S3. Significance: trace-clustered sign-flip permutation test (test unit = trace; per-trace difference averaged over the three CV repetitions; 200,000 draws), Holm-adjusted within a family of 48 tests. Rows use the second (full) run of each reproduction; Key and Afrasiabi training is not bit-reproducible (Supplementary Section S2).

