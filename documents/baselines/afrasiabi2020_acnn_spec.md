# Spec: Afrasiabi, Afrasiabi, Parang and Mohammadi 2020 (accelerated CNN on half-cycle differential currents)

Paper: S. Afrasiabi, M. Afrasiabi, B. Parang, M. Mohammadi, "Integration of accelerated deep neural network into power transformer differential protection," *IEEE Transactions on Industrial Informatics* 16(2), 865-876, Feb. 2020, DOI 10.1109/TII.2019.2929744 (accepted-manuscript PDF, 11 pages; read from the PDF; section numbers are the paper's). Written 2026-11-01, before any code or result of this method.
Module (to be written): `lstm_models/baselines/afrasiabi2020_acnn.py`.

## 1. What the method is
A percentage-differential element detects abnormal conditions; a CNN fed with the normalised half-cycle of the differential currents then decides "internal fault" (trip) versus "inrush, external fault or over-excitation" (no trip). CT saturation is first detected and compensated with a least-squares two-filter method of another paper; the CNN is "accelerated" by product quantisation of its convolutional and fully connected layers. (Sec. II, III, Fig. 1)

## 2. Specification
| Item | Paper | Reference |
|---|---|---|
| Input signals | differential phase currents I_P - I_S of phases a, b, c (CT secondaries) | Sec. III-A, Eq. (2) |
| Sampling | 112 samples per cycle (PSCAD, 230 kV network); N = 56 samples in a half cycle | Sec. III-A, IV |
| CT saturation | detected and compensated first by an LS-based, waveshape-independent method of two filters (first filter reproduces the chopped part of the saturated CT output, second suppresses the DC offset); this is the method of E. Hajipour, M. Vakilian, M. Sanaye-Pasand, IEEE Trans. Power Del. 30(5), 2293-2302, 2015 (their ref. [33]) | Sec. II-A |
| Abnormality detection | percentage differential: differential current > SD x restraint current, restraint = (I_P + I_S)/2, SD between 15 % and 40 %; threshold not given | Sec. II-B, Eq. (1) |
| Input data | half-cycle of the differential current normalised by its maximum: I_D-norm = (I_P - I_S) / max(|I_P - I_S|) (Eq. 2); X_i collects the three phases (Eq. 3) | Sec. III-A |
| Outputs | Y_F in B^(1x4) (fault type: L-G, L-L, LLL, P-S), Y_D in B^(1x3) (inrush, external fault, over-excitation); the network output Y = 1 if a fault, 0 if a disturbance (Eq. 4); trip if Y = 1 | Sec. III-A, III-E |
| Network (text) | the 56 samples are arranged as a 7 x 8 x 1 image (first eight samples = first row); accelerated convolutional layer 500 filters of 5 x 6; 16 subcodewords, 8 channels; max pooling; ReLU and batch normalisation; flatten; three fully connected layers; sigmoid in the last layer; stride (1,1), zero padding | Sec. III-E |
| Network (Fig. 1) | 1 x 56 -> 2-D; accelerated conv layer 128 filters of 3 x 3, 16 subcodewords, 8 channels; max pooling 2 x 2; flatten; accelerated FC 1 x 128; output 1 x 2 | Fig. 1 |
| Acceleration | product quantisation of the weight tensors: subcodebooks D(k,L) and binary assignments B(k,L) found by minimising the layer-output approximation error with alternating least squares (Eqs. 8-16, Algorithm 1) | Sec. III-B, III-D |
| Training / evaluation | random 70 % / 30 % split, K-fold cross-validation in testing; PSCAD/EMTDC data, Keras; cases: simple benchmark, CT saturation (fault- or inrush-caused), series-compensated transformer, neutral SFCL, experimental prototype | Sec. IV |
| Metrics | ACC, DEP, SEC, SAF (Eqs. 22-25) | Sec. IV |
| Reported result | ACC 99.15-99.64 %, DEP 97.7-100 %, SEC 99.3-100 % across cases (Table VI-style summary); compared with GRU, CNN, LSTM, DBM, SVM, KNN, LVQ, ANN, restricted 2nd-harmonic and gradient-vector methods | Sec. IV, V |

## 3. Inconsistencies inside the paper (recorded)
1. Text of Sec. III-E: 500 filters of 5 x 6 on a 7 x 8 image, and a 5 x 6 kernel would give a 3 x 3 map; Fig. 1: 128 filters of 3 x 3 and a 2 x 2 pooling. Both cannot be true. **This spec follows Fig. 1 (128 filters of 3 x 3, pooling 2 x 2, FC 128, output 2)** because it is internally consistent with the 7 x 8 input, and records the text's numbers as the alternative.
2. Eq. (3) stacks three phases of N = 56 samples (168 values) but the network input is 56 = 7 x 8 values (one channel).
3. Eq. (2) divides by max(|I_P - I_S|) without saying whether the maximum is over the phase or over the three phases.
4. The three metric definitions (22)-(25) assign TN/TP/FP/FN in a way that does not match their names; our scoring uses our own definitions for every method.

## 4. UNSPECIFIED items and how they are filled
| Item | Fill |
|---|---|
| Handling of the three phases | the three phases are three input channels (7 x 8 x 3); the normalising maximum is taken over the three phases of the half cycle, so that the relative amplitude between phases is kept (a per-phase maximum would blow up the noise of a healthy phase). Recorded as an assumption. |
| CT-saturation compensation (two LS filters of Hajipour et al. 2015) | **Amended 2026-11-01:** the paper (Hajipour et al. 2015) was supplied by the user and is implemented as `hajipour2015_ct_comp.py` from `hajipour2015_ct_comp_spec.md`; it is the first stage of the CNN (4 kHz, nominal burden as relay setting, then resampled to 5.6 kHz). The CNN is also reported without it (ablation). See that spec's section 6 for how well the filter works on our CT-stress traces. |
| Percentage-differential trigger | our 87T characteristic (pickup 0.30 pu, slopes 0.25 and 0.60, breakpoint 3 pu) is the abnormality detector, as in the paper's flow (Fig. 1) where an abnormality check precedes the CNN. |
| Window position | training windows: the half cycle that starts at the first pickup of the percentage element for each event (for faults, inrush, over-excitation, external faults); windows of healthy traces: random half cycles. Test: from the first pickup the CNN is evaluated every 1/8 cycle (7 samples at 5.6 kHz) on the latest half cycle while the element stays picked up, up to two cycles; the first window with Y = 1 issues the trip. The earliest decision is therefore half a cycle after the pickup. |
| Product quantisation | implementation is possible but only affects speed, not accuracy, per the paper's own aim; first version: the uncompressed CNN of Fig. 1, with the compression factor (parameter count with 16 subcodewords) computed analytically; PQ implementation is a second step if time allows. |
| Optimiser, learning rate, epochs, batch size, loss, weight decay, initialisation, dropout | not given for the proposed network (the comparison networks use 256 epochs). Fill: Adam, learning rate in {3e-4, 1e-3, 3e-3}, batch 256, up to 25 epochs with early stopping on the validation AUC (patience 5), binary cross-entropy with positive-class weight, as for every neural model of Part 1; the learning rate from the same 12-configuration search budget. |
| Sizes of the three fully connected layers (text) / one FC layer (Fig. 1) | 128 - 64 - 1 (text-compatible), versus 128 - 2 (Fig. 1): use Fig. 1 (one hidden FC layer of 128 followed by the output layer); the three-layer variant is a hyper-parameter in the search. |
| Multi-output training (Y_F, Y_D) | only the binary output Y is used; Y_F, Y_D are not needed for the trip decision. |

## 5. Deviations forced by our setup
| Paper | Ours | Effect |
|---|---|---|
| 112 samples per cycle at 60 Hz (6.72 kHz); half cycle = 56 samples | 50 Hz; 112 samples per cycle = 5.6 kHz; half cycle = 56 samples = 10 ms; resampled from 20 kHz (anti-alias filtered, factor 7/25) | window length in samples is kept; in time it is 10 ms instead of 8.33 ms |
| PSCAD 230 kV network with four transformers | plants A and B (Simulink) | retrained |
| Random 70/30 split | trace-grouped 5-fold CV x 3 seeds | leak-free |
| Fault type outputs | binary trip output | |
| CT compensation filter | implemented from Hajipour et al. (D-1 amended); the compensation is nearly inactive on our CT-stress traces (hajipour2015_ct_comp_spec.md section 6) | reported with and without |
| Product-quantised layers | uncompressed layers | affects speed/memory only |

## 6. Label mapping
Faults (all Internal*, Evolving, SOTF, HiZ visible/AI-only, CT-sat internal, fault in inrush) = Y = 1 (trip); inrush (no-load, loaded, recovery), over-excitation, external faults of every kind, normal operation = Y = 0 (no trip). HiZ faults below the 87T pickup never reach the CNN in the native mode (the percentage element does not pick up): they are missed by construction; in the "own dwell and threshold" mode the CNN scores every sliding window and they can be detected. This difference has to be reported.

## 7. Sanity check to reproduce
The 2-D arrangement and the separation of inrush and internal-fault half-cycles: plot the normalised half-cycle differential currents of one inrush and one internal fault (Eq. 2) and the CNN's output probability along the trace; save as `documents/baselines/afrasiabi2020_sanity.png`. The paper's own figures are accuracy-versus-epoch and ROC curves of its dataset, which cannot be reproduced on ours.

## 8. Cost to report
Parameter count and multiply-accumulates per decision (Fig. 1 network: conv 3 x 3 x 1 x 128 on 7 x 8, FC 128), measured latency per decision at 5.6 kHz (decision every 7 samples: budget 1.25 ms).
