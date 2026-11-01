# Spec: Simões et al. 2021 (RT-BSWT + two SVMs)

Paper: L. D. Simões, H. J. D. Costa, M. N. O. Aires, R. P. Medeiros, F. B. Costa, A. S. Bretas, "A power transformer differential protection based on support vector machine and wavelet transform," *Electric Power Systems Research* 197 (2021) 107297, DOI 10.1016/j.epsr.2021.107297. Read from the PDF (8 pages); equation numbers and sections below are the paper's. Written 2026-11-01, before any code and before any result of this method (BENCHMARK_FAIRNESS_PLAN.md rule 2.8).
Module (to be written): `lstm_models/baselines/simoes2021_rtbswt_svm.py`.

## 1. What the method is
A disturbance detector on wavelet-coefficient energies of the differential currents enables a first SVM (SVM 1) that classifies the event as external fault (EF), internal fault (IF) or energisation (EN) from four post-disturbance energy samples; an IF gives a trip, an EN a warning, an EF enables a second SVM (SVM 2) that looks at half-cycle energy windows to separate external faults (with or without CT saturation) from evolving external-to-internal faults (trip). (Sec. 3, Fig. 1)

## 2. Specification
| Item | Paper | Reference |
|---|---|---|
| Input signals | CT-secondary phase currents of both sides, iH = {iHA, iHB, iHC} and iX = {iXA, iXB, iXC}, plus the negative-sequence currents iHQ, iXQ from stored samples: iQ(k) = 1/3 [iA(k) + iB(k - fs/(3f)) + iC(k - 2fs/(3f))] | Sec. 3.1.1, Eqs. (2)-(3) |
| Sampling rate | fs = 15,360 Hz = 256 samples/cycle at 60 Hz ("ideal for methods based on fault-induced transients" per their ref. [13]); anti-aliasing filters and A/D in the relay; SNR 65 dB in their simulations | Sec. 3.1.1, Sec. 4 |
| Transform | RT-BSWT, wavelet part only: w(l,k) = (1/sqrt2) sum_{n=0}^{L-1} h(n) i(k-L+n+1+l), 0 <= l < L; sliding window length Δk >= L; periodised signal i(k+m) = i(k-Δk+m); mother wavelet "Daubechies with four coefficients, db(4)" | Eq. (4), Sec. 4 |
| Phase/magnitude/zero-sequence adjustment | applied to the wavelet coefficients "according to [7]" (not in this paper) | Sec. 3.1.3 |
| Differential coefficients | w_op(0,k) = 1/2 (w'_H(0,k) + w'_X(0,k)); w_op(l != 0,k) = w'_H(l,k) + w'_X(l,k); w_res(l,k) = w'_H(l,k) - w'_X(l,k), 0 <= l < L, for phases A, B, C and Q | Eqs. (5)-(7) |
| Differential energies | E_diff(k) = E_a(k) + E_b(k); E_a(k) = sum_{l=1}^{L-1} w_diff^2(l,k); E_b(k) = sum_{n=k-Δk+L}^{k} w_diff^2(0,n); for op and res | Eqs. (8)-(10) |
| Disturbance detector | a disturbance at k_d = k when E(k-1) <= E_th and E(k) > E_th, E_th = {E_op, E_res} adaptive: E_th = 3/(k2-k1+1) sum_{n=k1}^{k2} E(n), over a window of two cycles | Eqs. (11)-(12) |
| SVM 1 features | 32 features = 4 post-disturbance samples (k_d ... k_d+3) of the operating and restraining energies of phases A, B, C and Q; min-max normalised with the training-set minimum and maximum of each feature | Sec. 3.3, 4.1 |
| SVM 1 classifier | RBF kernel, one-versus-all with three binary SVMs (EF, IF, EN), C = 500, gamma = 100 (same for the three); LIBSVM; 10-fold cross-validation during training; grid search for C and gamma | Sec. 4.1, 4.2 |
| SVM 1 decision | IF -> trip; EN -> warning; EF -> enable SVM 2. After a trip SVM 1 is blocked (the breaker-opening transient would be misclassified) | Sec. 3.3 |
| SVM 2 features | 768 features = half-cycle window (128 samples at 256/cycle) of operating and restraining energies of phases A, B, C (no negative sequence), min-max normalised | Sec. 3.4 |
| SVM 2 window | starts 1/2 cycle after k_d, slides in steps of 1/8 cycle (32 samples) until 2 cycles after k_d (8 classifications per event) | Sec. 3.4 |
| SVM 2 classifier | linear kernel (regularisation C from the grid search; value not given); trained with 60 % of its training set (no gain beyond that) | Sec. 4.1 |
| SVM 2 decision | ordinary external fault with or without CT saturation -> warning; evolving external-to-internal fault -> trip; after a trip the SVMs are blocked | Sec. 3.4 |
| Training data | 80 % / 20 % random split keeping class proportions; SVM 1 from databases 1-4 (external faults 1820, internal 1820, critical internal turn faults 1176, energisations 362 records), SVM 2 from databases 1, 5, 6 (external, external with forced CT saturation, evolving external-to-internal) | Sec. 4, 4.1 |
| Reported result | SVM 1 accuracy 100 %, SVM 2 accuracy 98.7 %; operating time 4 samples = about 260 us (SVM 1) and at most 2.1 ms (SVM 2) | Sec. 4.2-4.4, Table 1 |

## 3. UNSPECIFIED items and how they are filled
| Item | Fill |
|---|---|
| Number of taps of "db(4)" (the text says four coefficients, which would be the 4-tap Daubechies filter, called db2 in MATLAB/PyWavelets; "db4" there has 8 taps) | Use the 4-tap filter as written in the paper (`pywt` db2 coefficients); L = 4. Recorded as an ambiguity. |
| Sliding-window length Δk (only Δk >= L is stated) | Δk = L. |
| Phase/magnitude/zero-sequence adjustment of "[7]" | Apply the same plant compensation matrices as the proposed relay (YNd1 on the HV side, Dyn11 on the LV side) to the coefficient vectors of the three phases; for Q use the unmodified negative sequence of each side. |
| Phase shift/zero-sequence handling of the negative-sequence terms | As above (Q is unaffected by delta/wye phase displacement except a fixed angle; magnitude ratio applied from the CT ratios). |
| Grid for C and gamma of SVM 1 and for C of SVM 2 | The paper's values (C = 500, gamma = 100 for SVM 1) are used as one grid point; the search around them (C in {10, 100, 500, 1000}, gamma in {1, 10, 100, 1000}) is run with 10-fold CV on the training folds only, same 12-configuration budget rule as the other methods (Part 1, B2) if it applies; the paper's point is kept as the "as published" variant. SVM 2: C in {0.1, 1, 10, 100}. |
| Count of operating-restraining sample normalisation for E_th at the start of a trace (needs two cycles of history) | Detector armed after two cycles (40 ms at 50 Hz); our traces have at least 0.4 s of pre-event data. |
| Handling of events after a trip | SVM 1/2 blocked for the rest of the trace, as in the paper. |
| Event-to-class labelling for our scenarios | See section 5. |
| 87T/high-set element | The paper has none; the native mode has no high-set. In the "same dwell and validation-tuned threshold" mode the relay mirror adds the same high-set as for all methods. |

## 4. Deviations forced by our setup
| Paper | Ours | Effect |
|---|---|---|
| 60 Hz, 256 samples/cycle = 15,360 Hz | 50 Hz; 256 samples/cycle = 12,800 Hz; traces re-simulated at 20 kHz (D2) and resampled (anti-alias filtered, ratio 16/25) to 12,800 Hz | the detector and windows keep their per-cycle lengths; time-domain delays scale with 1/50 s |
| SNR 65 dB, fixed | noise 0.05-1 % (and up to 3 % in stress traces) of rated CT current plus 0.01 A quantisation | harder than the paper's data; SVM 1 is retrained on our data |
| Transformer 100 MVA, 230:69 kV, own CT models | our plants A and B; CT burden and saturation per our generator | |
| Training records: grid of inception angle and Rf; critical turn-to-turn and turn-to-earth faults | our scenario mix (terminal faults only, no inter-turn faults) | the critical-internal-fault class of the paper is not represented; reported as a limitation |
| Evolving external-to-internal faults (databases 5 and 6) | not in our dataset (we have "Internal_Evolving": internal fault that spreads to other phases, and fault-in-inrush cases) | SVM 2 is implemented but its positive class (evolving external-to-internal) is absent, so it can only produce warnings; the method's trip then comes from SVM 1 only. Reported as "not exercised". |
| Our classes beyond the paper's: over-excitation, recovery/sympathetic inrush, normal operation, HiZ faults | mapped as in section 5 | |
| Random 80/20 split | our trace-grouped 5-fold CV x 3 seeds with an inner validation split | leak-free; SVM models are retrained per fold |
| Operating time = 4 samples after k_d | scored with our rule: first sample at which the method's logic issues a trip; trip time from fault inception | |

## 5. Label mapping used for training and scoring
| Our scenario group | SVM 1 class | Trip expected |
|---|---|---|
| Internal LV solid, Internal HV-side, Internal HiZ (visible and AI-only bins), Evolving, Internal CT-sat | IF | yes |
| SOTF (switch onto fault), Fault in inrush | IF (a fault during energisation: the paper has no such class; recorded) | yes |
| Inrush no-load, Inrush loaded, Recovery inrush | EN | no |
| External solid, External HiZ, External CT-sat, External in inrush | EF | no |
| Over-excitation, Normal | no disturbance detected, or EN if the detector fires | no |
Faults below the detectability limit (undetectable bin) are excluded from the headline numbers as for every method.

## 6. Sanity check to reproduce (before scoring)
One qualitative result of the paper: operating and restraining differential energies of phase A for an energisation and an internal fault (their Fig. 2(b) and 3(b)): the restraining energy of an internal fault on the energised side rises with the operating energy, and the energy at disturbance detection is clearly above E_th. Save as `documents/baselines/simoes2021_sanity.png` with our traces of an internal fault and an inrush at 12,800 Hz.

## 7. Cost to report
Per-sample floating-point operations of the wavelet preprocessing (paper: 730 FLOPs/sample) and of SVM 1 (paper: 73,728 FLOPs, 768 square roots, 768 exponentials) and SVM 2 (751,593 FLOPs) are counted for our implementation; the latency of one sample is measured at 12,800 Hz (budget 78.1 us).

## 8. Amendments of 2026-11-01 (made while writing the code, before any evaluation result of this method)
1. **The published detector cannot be used at our noise level.** With the threshold E_th = 3 x the mean energy of the previous two cycles (Eq. 12), the detector fires about 1,500-2,000 times per trace on noise alone (the energies of white noise are chi-square distributed and exceed three times their mean about 1.7 % of the samples in each of the eight signals; measured on 15 traces per scenario in `documents/baselines/simoes_detector_check.txt`, written by `tools/simoes_detector_check.py`: 1,100-1,600 firings per trace at factor 3, about 1 at factor 30). The factor is therefore a hyperparameter: chosen from {3, 10, 30, 100} on the training folds as the smallest value for which the normal and over-excitation traces of the training folds give at most one unmatched detection per trace on average. The published value 3 stays as a reported configuration; it fails by construction on our data and the results table has to say so.
2. The detector is armed from t = 0.12 s (start-up transient of the simulation, same limit as the generator's own checks).
3. Detector firings that match no known event of the trace (noise, repeated crossings) are left out of the training set of SVM 1 (the paper has only three classes); at test time they are classified like any other firing and can cause false trips. Firings are matched to events within one cycle after the event.
4. Negative-sequence delays of 85.33 and 170.67 samples are rounded to 85 and 171.
5. The negative-sequence and phase currents are first compensated (plant matrix) and the X side is taken as the current leaving the transformer, so that the operating energy is the differential energy.
Two SVM 1 variants are reported: "published" (C = 500, gamma = 100) and "grid" (C in {10, 100, 500, 1000} x gamma in {1, 10, 100, 1000}, chosen on the validation events of the inner split).
