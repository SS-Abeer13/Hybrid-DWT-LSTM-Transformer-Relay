**Instances of the dual-path supervisory logic with interchangeable classifiers (dependability / security, %): plant-A CV (3 seeds × 5 folds, common set, mean over seeds), OOD and plant-B zero-shot where a final model was scored; difference to the validation-tuned harmonic 87T (91.2 / 99.1; post-hoc, Holm over 16 tests); and the gated-only ablation (AI-alone path off).**

| Instance (hybrid mode) | CV |  | Δ dep. vs tuned | Δ sec. vs tuned | OOD |  | Plant B |  |
|  | dep. | sec. | harmonic 87T (pt) | harmonic 87T (pt) | dep. | sec. | dep. | sec. |
|---|---|---|---|---|---|---|---|---|
| LSTM, deployed (closed-loop configuration) | 93.0 | 99.0 | n/e | n/e | 98.0 | 96.0 | 92.7 | 88.4 |
| LSTM, tuned (B2) | 93.6 | 99.1 | +2.42\* | +0.03† | n/e | n/e | n/e | n/e |
| 1D-CNN, tuned (B2) | 95.7 | 99.0 | +4.57\* | -0.05† | n/e | n/e | n/e | n/e |
| GRU, tuned (B2) | 95.6 | 98.8 | +4.41\* | -0.25† | n/e | n/e | n/e | n/e |
| MLP, tuned (B2) | 94.9 | 99.2 | +3.74\* | +0.14† | n/e | n/e | n/e | n/e |
| Random forest, tuned (B2) | 93.5 | 99.5 | +2.31\* | +0.42\* | n/e | n/e | n/e | n/e |
| Key et al. network (Dis-DNN output) | 94.1 | 99.9 | +2.93\* | +0.80\* | 98.0 | 95.3 | 95.5 | 99.9 |
| *Ablation, AI-alone path off (gated only; post-hoc, from saved decisions)* |  |  |  |  |  |  |  |  |
| LSTM, deployed, gated only | 88.4 | 99.4 |  |  | 94.6 | 98.7 | 90.5 | 99.2 |
| Key et al. network, gated only | n/e | n/e |  |  | 94.6 | 95.3 | 94.1 | 100.0 |

*Notes.* \* significant after Holm over 16 tests (12 post-hoc tests added after N6c plus the 4 of the tuned-harmonic comparison); † per-seed differences change sign (unstable across splits). 6 of 6 instances are significantly more dependable than the tuned harmonic 87T (+2.3 to +4.6 pt); none is significantly less secure. The B2 instances were evaluated in cross-validation only (n/e = not evaluated: no OOD or plant-B run, no new experiments after the review). Key's classifier is the Dis-DNN internal-fault probability sampled at the relay's decision instants inside the identical logic (87T vote, confirmed output, AI-alone path, high-set; thresholds by the plateau rule). Plant B, deployed hybrid: 87 of 89 false trips first came from the AI-alone path, 2 from the gated path, none from the high-set; Key hybrid: 1 of 757 from the AI-alone path, 0 gated, 0 high-set. Gated-only (post-hoc counterfactual, not adopted): on the plant-A CV the AI-alone path adds 4.5 pt dependability and costs 0.5 pt security (exact McNemar p 5e-51 and 7e-09, raw). Key hybrid vs proposed hybrid: dependability +1.16 pt (unstable across seeds), security +0.91 pt (stable), Holm over 50 tests.

