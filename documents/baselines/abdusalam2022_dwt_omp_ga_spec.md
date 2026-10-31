# Spec: Abdusalam, Ibrahim, Anayi and Packianather 2022 (DWT + OMP features, bees / genetic feature selection, KNN / SVM / ANN)

Paper: O. Abdusalam, A. Ibrahim, F. Anayi, M. Packianather, "New hybrid machine learning method for detecting faults in three-phase power transformers," *Energies* 15(11), 3905, 2022, DOI 10.3390/en15113905 (open access; 15 pages; read from the PDF). Written 2026-11-01, before any code or result of this method.
Module (to be written): `lstm_models/baselines/abdusalam2022_dwt_omp_ga.py`.
**The paper contains no random forest** (the benchmark row "Wavelet-RF, Abdusalam et al." was wrong). The paper is described in terms of a laboratory transformer (60 turns per winding, 60 V phase voltage), and many of its steps are only named, not specified; the list of UNSPECIFIED items below is long, and the reproduction is correspondingly a reading of the paper, not a copy.

## 1. What the method is
Current signals of a laboratory transformer are decomposed with a 6-level DWT (five mother wavelets) and reconstructed with orthogonal matching pursuit (OMP) over several dictionaries; statistical features of the resulting signals form a feature matrix; the bees algorithm (BA) or a genetic algorithm (GA) selects a subset (fitness = error of a 3-nearest-neighbour classifier); KNN, SVM and ANN classifiers are trained with 5- or 10-fold cross-validation to classify the condition (normal, internal faults, external fault). (Sec. 3, Fig. 8)

## 2. Specification
| Item | Paper | Reference |
|---|---|---|
| Input signals | three-phase currents of a lab transformer (primary and secondary CTs 40/5 A), "phase difference" of the currents is what is decomposed ("DWT and OMP are combined to extract phase differences") | Sec. 2.1, 3.1 |
| Sampling | 10 kHz, LabVIEW/DAQ 6211, 10,000 samples per record; the text says "300 samples per cycle" at 50 Hz, which does not match 10 kHz (that is 200 per cycle) | Sec. 2.1 |
| Fault types | turn-to-turn, turn-to-ground, phase-to-ground, phase-to-phase (Rf = 5 ohm), external fault (secondary side), normal | Sec. 2.2-2.6 |
| DWT | 6-level decomposition with five mother wavelets used independently: db7, sym3, coif4, bior6.8, rbior6.8; "thirty features were retrieved" per wavelet | Sec. 3.1.1 |
| OMP | 1-D OMP over five dictionaries: Sym4-Lev5, Wpsym4-Lev5, DCT, Sin, Cos, on the phase-A current; maximum 100 iterations; maximum relative error 0.01 %; 8 statistical features: mean, median, standard deviation, median absolute deviation, mean absolute deviation, L1 norm, L2 norm, maximum norm (Eqs. 2-9) | Sec. 3.1.2 |
| Feature count | "40 distinct features per signal" (conclusion) = 5 dictionaries x 8 statistics; "instead of fourteen features, BA selected twelve" (Sec. 4) | Sec. 4, 6 |
| Feature selection | bees algorithm (population, elite bees, selected sites, neighbourhood search, random scouts; Appendix A) and genetic algorithm (population, evaluation function, reproduction, crossover, mutation, max generations; Appendix B); fitness = classification error of KNN with K = 3; BA selected 12 features, GA 21 | Sec. 3.2, 3.4, 4, Table 1 |
| Classifiers | KNN, SVM, ANN; best parameters reported: neighbours = 1, C = 20, kernel = RBF; ANN architecture not given | Sec. 3.3, 4 |
| Training | 5-fold and 10-fold cross-validation, 10-fold better | Sec. 3.4, 4 |
| Reported result | Table 2b (BA, 10-fold): SVM accuracy 96 %, ANN 76 %, KNN 93 %; Table 3b (GA, 10-fold): SVM 91 %, ANN 73 %, KNN 85 %. Values are printed with a % sign after a fraction (0.96%), and the text says the best was "96 % using the genetic algorithm" while the tables and the conclusion give BA + SVM | Tables 2-3, Sec. 4-6 |

## 3. Inconsistencies inside the paper (recorded, not resolved by guessing)
1. Which selector is best: text of Sec. 4 says GA + SVM at 96 %; Tables 2b/3b and the conclusion give BA + SVM at 96 % (GA + SVM 91 %). The benchmark plan names SVM + GA; this spec uses **BA + SVM as the main row** (Table 2b, conclusion) and reports GA + SVM and the KNN and ANN variants in the appendix.
2. The number of features: 30 (DWT), 8 per dictionary x 5 = 40, "fourteen", 12, 21.
3. Samples per cycle (300 vs 200 at 10 kHz), K = 3 in the selection fitness vs "neighbour = 1" as the best KNN parameter.

## 4. UNSPECIFIED items and how they are filled
| Item | Fill |
|---|---|
| The 30 DWT features per wavelet | For each of the 6 detail levels and the level-6 approximation (7 sub-bands) per signal: energy (sum of squares), standard deviation, and mean absolute value would give 21; to reach 30 the paper's eight statistics are not enough to infer the set. Fill: the 8 statistics of the OMP list (Eqs. 2-9) computed on each of the 7 sub-bands is 56, then reduced to 30 by dropping, on the training folds, the 26 features with the lowest ANOVA F-score. **Recorded as an assumption.** |
| Which currents form the "phase difference" | the three differential currents (primary minus secondary after our plant compensation), one DWT/OMP feature set per phase concatenated, or one feature set per phase averaged: use the concatenation of the three phases. |
| Window length for one decision | not given (10 s records in the lab). Fill: one-cycle window (20 ms) sliding in steps of 1/8 cycle, evaluated from the fault/disturbance inception onward; at 10 kHz one cycle is 200 samples (our traces are resampled to 10 kHz). |
| Bees algorithm settings (number of scout bees, elite sites, patch size, iterations) | n = 50 scouts, 5 selected sites, 2 elite sites, 20 and 10 recruited bees, patch size 1 bit flip, 50 iterations; chosen as common defaults of the algorithm; same evaluation budget as the GA. |
| GA settings (population, crossover, mutation, generations) | population 50, single-point crossover 0.8, mutation 0.02 per bit, 50 generations, binary chromosome of length = number of features; same fitness evaluations as the BA. |
| Fitness of the selectors | 3-NN classification error, 3-fold cross-validated on the training part of the fold (never on the outer test fold). |
| ANN architecture and training | one hidden layer of 20 tanh units, scaled conjugate gradient (MATLAB `patternnet` default equivalent), early stopping on a 15 % validation share; not specified in the paper. |
| SVM parameters | RBF, C = 20, gamma = 1 / (number of features) (paper gives only C and the kernel); KNN: K = 1 as reported. |
| Classes | 6 conditions in the paper; ours are mapped to {trip, no trip} and, for training, to the paper's classes where a counterpart exists (see section 6). |
| Trip rule | not in the paper (offline classifier). Native mode: trip when the classifier output at a decision step is an internal-fault class, at the first such step after the inception. |

## 5. Deviations forced by our setup
| Paper | Ours | Effect |
|---|---|---|
| Laboratory transformer, 60 V, CT 40/5 | plants A and B simulated | features retrained |
| 10 kHz, DAQ | resampled from 20 kHz (anti-alias filtered) to 10 kHz | none beyond the filter |
| Offline classification of recorded cases with random k-fold CV | trace-grouped CV, thresholds/selection on training folds only | leak-free |
| Faults: turn-to-turn, turn-to-ground | terminal faults only | the paper's inter-turn classes are absent |
| No inrush class | inrush and over-excitation are labelled "no trip" | the method is evaluated on a task it was not designed for; stated |

## 6. Label mapping
Internal faults of every kind (our Internal*, Evolving, SOTF, HiZ visible/AI-only, CT-sat internal, fault in inrush) = fault classes (trip); external faults of every kind = the paper's "external fault" class; normal operation, inrush, recovery inrush, over-excitation = "normal/no fault" (the paper has only normal operation).

## 7. Sanity check to reproduce
The paper has no waveform figure to reproduce. Sanity check instead: the classifier accuracy of BA + SVM on a random 10-fold split of a small balanced subset (internal fault / external fault / normal) must be above 90 % as an implementation check (their 96 % is a lab-data number and is not expected to be matched). Save the confusion matrix as `documents/baselines/abdusalam2022_sanity.png`.

## 8. Cost to report
Feature extraction cost per decision (6-level DWT, OMP with up to 100 iterations over five dictionaries, 12 statistics) and the classifier cost; measured at 10 kHz with the one-cycle window stepped every 1/8 cycle (budget per step 2.5 ms, since a decision is made every 25 samples at 10 kHz).
