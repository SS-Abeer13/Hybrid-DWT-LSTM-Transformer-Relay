**Instances of the dual-path supervisory logic with interchangeable classifiers (dependability / security, %): plant-A CV (3 seeds × 5 folds, common set, mean over seeds), OOD and plant-B zero-shot where a final model was scored; difference to the validation-tuned harmonic 87T on the extended grid (92.8 / 98.9; post-hoc reference, Holm over 16 tests); and the gated-only ablation (AI-alone path off).**

| Instance (hybrid mode) | CV |  | Δ dep. vs tuned | Δ sec. vs tuned | OOD |  | Plant B |  |
|  | dep. | sec. | harmonic 87T (pt) | harmonic 87T (pt) | dep. | sec. | dep. | sec. |
|---|---|---|---|---|---|---|---|---|
| LSTM, deployed (closed-loop configuration) | 93.0 | 99.0 | +0.16† | +0.02† | 98.0 | 96.0 | 92.7 | 88.4 |
| LSTM, tuned (B2) | 93.6 | 99.1 | +0.81† | +0.17† | n/e | n/e | n/e | n/e |
| 1D-CNN, tuned (B2) | 95.7 | 99.0 | +2.96\* | +0.08† | n/e | n/e | n/e | n/e |
| GRU, tuned (B2) | 95.6 | 98.8 | +2.80\* | -0.12† | n/e | n/e | n/e | n/e |
| MLP, tuned (B2) | 94.9 | 99.2 | +2.13\* | +0.27 | n/e | n/e | n/e | n/e |
| Random forest, tuned (B2) | 93.5 | 99.5 | +0.70 | +0.56\* | n/e | n/e | n/e | n/e |
| Key et al. network (Dis-DNN output) | 94.1 | 99.9 | +1.32\* | +0.93\* | 98.0 | 95.3 | 95.5 | 99.9 |
| *Ablation, AI-alone path off (gated only; post-hoc, from saved decisions)* |  |  |  |  |  |  |  |  |
| LSTM, deployed, gated only | 88.4 | 99.4 |  |  | 94.6 | 98.7 | 90.5 | 99.2 |
| Key et al. network, gated only | n/e | n/e |  |  | 94.6 | 95.3 | 94.1 | 100.0 |

*Notes.* \* $p_{\mathrm{H}}<0.05$ (post-hoc family of 16 tests: 12 against the extended-grid tuned harmonic 87T plus its 4 tests); † per-seed differences change sign. Significance: trace-clustered sign-flip permutation test (test unit = trace; per-trace difference averaged over the three CV repetitions; 200,000 draws), Holm-adjusted within a family of 16 tests. Deployed LSTM row: from the 4-test family of Table C (deployed minus tuned). 4 of 6 instances are significantly more dependable than the extended-grid tuned harmonic 87T (+1.3 to +3.0 pt; all six +0.7 to +3.0 pt); Key's network, RF significantly more secure; none is significantly less secure. In 3 of 15 CV fold-models of the deployed LSTM the plateau rule switched the AI-alone path off (AI threshold 0.75–0.999), so its CV row mixes dual-path and gated-only fold-models. The B2 instances were evaluated in cross-validation only (n/e = not evaluated). Key's classifier is the Dis-DNN internal-fault probability sampled at the relay's decision instants inside the identical logic. Plant B, deployed hybrid: 87 of 89 false trips first came from the AI-alone path, 2 from the gated path, none from the high-set; Key hybrid: 1 of 757 healthy traces tripped by the AI-alone path, 0 gated, 0 high-set. Gated-only (post-hoc counterfactual from saved decisions, descriptive): on the plant-A CV it loses 168 fault decisions and gains 28 healthy decisions (counted over the three repetitions), -4.52 / +0.47 pt. Key hybrid minus proposed hybrid: dependability +1.16 pt ($p_{\mathrm{H}}=0.06$), security +0.91 pt ($p_{\mathrm{H}}\le2\times10^{-4}$); Holm family of 50.

