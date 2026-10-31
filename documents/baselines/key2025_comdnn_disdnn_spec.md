# Spec: Key, Leap, Yoon, Lee and Nam 2025 (Com-DNN CT-saturation compensation + Dis-DNN stacked denoising autoencoders)

Paper: S. Key, S. Leap, S.-M. Yoon, H. Lee, S.-R. Nam, "A dual deep neural network approach for discriminating internal faults and inrush currents in transformers under CT saturation," *IEEE Access* 13, 178492-178504, 2025, DOI 10.1109/ACCESS.2025.3618747 (author's accepted-manuscript PDF, 13 pages; read from the PDF; section and equation numbers are the paper's). Written 2026-11-01, before any code or result of this method.
Module (to be written): `lstm_models/baselines/key2025_comdnn_disdnn.py`.
The thesis lists this paper as "Lin et al., IEEE Access 13, pp. 11234-11246" and the benchmark table called it "Wavelet-GRU (attention)". There is no GRU and no attention in the paper.

## 1. What the method is
Two networks in sequence. The Com-DNN takes one-cycle windows of each CT secondary current and estimates the undistorted primary current; the differential current computed from the two estimates is cut into one-cycle windows that the Dis-DNN (stacked denoising autoencoders with a softmax output) classifies into four classes: normal, transient, inrush current, internal fault. Disturbance detection is part of the classification (the "normal" and "transient" classes), without a separate threshold. (Sec. II, Fig. 1)

## 2. Specification
| Item | Paper | Reference |
|---|---|---|
| Input signals | secondary currents of CT1 and CT2 (both sides), single phase windows (the paper's example: phase A) | Sec. II-A, II-B |
| Sampling | 3,840 Hz = 64 samples per cycle at 60 Hz ("hardware implementation constraints"); data acquired with PSCAD; SNR 20-30 dB tested | Sec. III-A |
| Windowing | data windows (DW) of m = N = 64 samples, one sample step: rows of the matrix in Eq. (1); each window normalised to [-1, 1] by Eq. (2) with one row element as reference | Sec. II-A, Eq. (1)-(2) |
| Com-DNN | SDAE-based network that maps the distorted secondary-current window to the estimated primary current (no saturation); trained on windows of distorted input and undistorted target "by generalizing various parameters of CT saturation and noises"; layer sizes not given | Sec. II-B, Fig. 1, 6 |
| Differential current | calculated from the Com-DNN estimates of the two sides; instantaneous differential current in a one-cycle DW is the Dis-DNN input | Sec. II-C, Fig. 2 |
| Dis-DNN classes | 4 classes by one-hot labels: normal (0 0 0 1), transient (0 0 1 0), inrush (0 1 0 0), internal fault (1 0 0 0); the transient state is the first part of a disturbance before the cases separate; the delay between t0 and t1 is less than one cycle, 58 samples of 64 | Sec. II-C, Table I |
| Unsupervised stage | denoising autoencoder, leaky-ReLU: h(x) = W_de f(W_en x + b_en) + b; cost J = (1/N) sum ||h(x_i) - x_i||^2 (RMSE term) + weight decay + sparsity penalty (KL divergence to a small target); trained layer by layer on windows with additive white Gaussian noise; layers are frozen after each DAE, the code layer of one DAE feeds the next | Sec. II-D-1, Eqs. (4)-(6), Fig. 3-4 |
| Supervised stage | softmax output layer (4 classes) added on top; all weights and biases fine-tuned jointly by back-propagation with cross-entropy plus weight decay (Eq. 9); class = argmax of the softmax (Eqs. 7-8) | Sec. II-D-2 |
| Optimiser | Adam; learning rate initially set to 1, exponentially decayed after a number of epochs; Bayesian optimisation (Gaussian process, expected improvement) of 3 hyperparameters: learning rate, batch size, number of neurons | Sec. II-E, III-B |
| Data | 40 MVA 154/23 kV Y-Y, 10.99 % reactance, CT 1200:5 and 2000:5 (JA model); inrush: switching angle 0-180 deg step 10, residual flux -80..80 % step 10 (323 cases, 412,794 training windows); internal A-G faults: inception angle 0-180 step 10, winding location 0-80 % step 10 (171 cases, 218,538 windows) | Sec. III-A, Table II |
| Evaluation | ACC, DEP, SEC; compared at the 58th (N-6) and 61st (N-3) sample after the event (one cycle) against a harmonic blocking scheme, a unidirectional/quartering similarity index and an EKF method | Sec. III-C, III-D, Tables III-IV |
| Reported result | at the 61st sample 100 % ACC/DEP/SEC; at the 58th sample ACC 98.87 %, DEP 99.49 %, SEC 99.25 % (inrush) and 99.37 / 99.74 / 99.01 % (inrush + internal fault) | Tables III-IV |
| Cost | about 28,353 floating-point operations per inference for the two networks; INT8 on a C66x DSP at 12 GFLOPS: about 2.36 us | Sec. IV |

## 3. UNSPECIFIED items and how they are filled
| Item | Fill |
|---|---|
| Layer sizes of Com-DNN and Dis-DNN, number of stacked DAEs | the paper's cost (28,353 FLOPs for both) bounds the size: about 14,000 multiply-accumulates in total. Search space (same 12-configuration budget as every method): Com-DNN 64 - n - 64 with n in {32, 48, 64}; Dis-DNN two stacked DAEs 64 - h1 - h2 with h1 in {32, 48, 64}, h2 in {16, 24, 32}, softmax 4; learning rate {3e-4, 1e-3, 3e-3}, batch size {128, 256}. Sizes above the paper's FLOP count are reported with their cost. |
| Bayesian optimisation | replaced by random search with the same budget as all other methods (documented deviation; the search space is the paper's three variables). |
| Learning-rate schedule | "initially set to 1, decayed exponentially": Adam with 1.0 diverges on our scaling; fill: the searched learning rate with exponential decay by 0.9 every 5 epochs. |
| Epochs, early stopping | up to 25 epochs, validation-based early stopping (patience 5), as for every neural model of Part 1. |
| DAE noise level, sparsity target and weights, weight decay | additive white Gaussian noise at 30 dB SNR (the paper tests 20 and 30 dB), sparsity target 0.05 with weight 1e-3, weight decay 1e-4. |
| Which phase / phases | the paper's examples are single-phase; fill: the same networks (shared weights) run on each of the three phases of the compensated differential current, trip if any phase is classified as internal fault. The Com-DNN is applied to each of the six CT signals. |
| Com-DNN training target | the true line current divided by the nominal CT ratio, from the V-I measurement blocks (stored in the 20 kHz re-simulation, fields `Tp`, `Ts`), normalised with the same reference as the input window. Traces without saturation give identity examples, saturated traces the distorted-to-clean mapping. |
| Window labelling (the paper gives t0 and t1 only qualitatively) | for each event with inception t0: windows ending before t0 = normal; windows ending in [t0, t0 + 58 samples) = transient; windows ending at or after t0 + 58 samples = inrush or internal fault according to the scenario; external faults and over-excitation: transient in [t0, t0 + 58) and normal afterwards. 58 samples scale with the sampling rate (58 of 64 per cycle). |
| Decision / trip logic | none in the paper beyond the class output. Native: the Dis-DNN classifies the latest 64-sample window at every sample; trip at the first sample at which any phase's argmax is "internal fault". Mode (b): internal-fault softmax probability through our 20-sample dwell and validation-tuned threshold. |
| Handling of "N-6 / N-3" evaluation | not used for scoring; our scoring is the first sample at which the trip is issued (same for every method). The one-cycle operating time follows from the 58-sample transient class. |

## 4. Deviations forced by our setup
| Paper | Ours | Effect |
|---|---|---|
| 3,840 Hz, 64 samples per cycle at 60 Hz | 50 Hz, 64 samples per cycle = 3,200 Hz; resampled from 20 kHz (anti-alias filtered, factor 4/25) | window length in samples is kept; one cycle is 20 ms |
| PSCAD 154/23 kV, JA CT model | plants A and B in Simulink with the saturable-transformer CT | retrained |
| Training data: A-G internal faults and inrush on a grid of angles and flux | our scenario mix, all fault types, CT-stress cases, HiZ, SOTF | broader |
| Random split | trace-grouped CV | leak-free |
| Bayesian optimisation | random search, same budget as the other methods | |
| INT8 hardware, 2.36 us | measured FP32 latency on the development PC | not comparable to the paper's DSP |

## 5. Sanity check to reproduce
Their Fig. 6 / Fig. 7: the Com-DNN output overlays the undistorted primary current during CT saturation, and Fig. 2: the instantaneous differential current of an inrush stays positive after t0 while that of an internal fault becomes zero or negative. Plot, for one saturated external-fault trace of ours, the secondary current, the target and the Com-DNN estimate; save as `documents/baselines/key2025_sanity.png`.

## 6. Cost to report
Parameter count and floating-point operations of both networks per inference (compare with the paper's 28,353 FLOPs), and the measured latency per decision at 3,200 Hz (budget 312.5 us per sample).
