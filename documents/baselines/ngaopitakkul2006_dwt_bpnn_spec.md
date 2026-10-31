# Spec: Ngaopitakkul and Kunakorn 2006 (db4 DWT + back-propagation network)

Paper: A. Ngaopitakkul and A. Kunakorn, "Internal fault classification in transformer windings using combination of discrete wavelet transforms and back-propagation neural networks," *International Journal of Control, Automation, and Systems* 4(3), 365-371, June 2006 (7 pages; read from the PDF; page numbers below are the journal's pages). Not in Crossref (no DOI found); the audit of the bibliography is in `documents/reference_audit.md` (ref19). Written 2026-11-01, before any code or result of this method.
Module (to be written): `lstm_models/baselines/ngaopitakkul2006_dwt_bpnn.py`.

## 1. What the method is
The differential currents (primary minus secondary) of the three phases and the zero-sequence current are decomposed with a db4 wavelet; the largest scale-1 coefficient in a quarter cycle after the fault inception, for each of the four signals, is the input of a feed-forward network with two tanh hidden layers and a linear output layer, trained with Levenberg-Marquardt. The 8 outputs (0/1 patterns, Table 1) code the type and side of an internal winding fault. A coefficient jump test finds the inception time and the faulted phase. **The paper classifies the type of an internal fault; it has no inrush, external-fault or normal class** (the external/internal discrimination is in the authors' earlier paper, their ref. [17], not in this one).

## 2. Specification
| Item | Paper | Reference |
|---|---|---|
| Input signals | differential currents of phases A, B, C (primary current minus secondary current, per phase) and the zero-sequence current | Sec. 4, p. 367 |
| Sampling | ATP/EMTP simulation, time step t1 = 5 us (= 200 kHz); loop over td = 5 us ... 0.1 s in steps of 5 us | Sec. 4, p. 367 |
| Transform | DWT, Daubechies 4, scale 1 detail coefficients squared "for a more explicit comparison" (scales 1-5 were examined; scale 1 is "enough") | Eq. (1), Sec. 4, pp. 366-368 |
| Detection / phase check | for td: if X_diff(td+t1) >= 5 x max X_diff(0..td) then X_chk = 1 else 0, per phase X in {A, B, C, zero sequence}; applied to the quarter cycle after the inception | Sec. 4, p. 367 |
| Network inputs | 4 inputs: the maximum scale-1 coefficient of A, B, C differential currents and of the zero-sequence current in the quarter cycle after the fault inception; input normalisation ("normalization input pattern", Fig. 6) | Sec. 5, p. 369 |
| Network | back-propagation, two hidden layers, tanh in both, linear output; 8 outputs; Eqs. (2)-(3) | Sec. 5, p. 368 |
| Hidden layer 1 size | initial z = 2/3 (r + q), r = 4 inputs, q = 8 outputs, so z = 8; final z_st = z + z1 with z1 = 5 (2<=z<=6), 4 (7<=z<=10), 3 (11<=z<=13), 2 (z>=14), so z_st = 12 | Eqs. (5)-(6), p. 369 |
| Hidden layer 2 size | hidden2 = hidden1 - 1 at every step | Fig. 6, p. 370 |
| Training | Levenberg-Marquardt (MATLAB `trainlm`), up to 20,000 iterations per size; sizes of both layers are increased by one and training repeated until hidden1 reaches z_st or the test-set MAPE is below 0.5 %; the weights with minimum MAPE are stored; MAPE = (1/n) sum |o_ANN - o_target| / o_target x 100 % (Eq. 4) | Sec. 5, pp. 369-370, Fig. 6 |
| Output coding | Table 1: bits A1 B1 C1 G1 (HV side) and A2 B2 C2 G2 (LV side); winding-to-ground sets the phase bit and G bit of that side, interturn only the phase bit | Table 1, p. 368 |
| Data | 50 MVA, 115/23 kV; fault inception 30 and 210 deg on phase A; winding-to-ground faults at 10-90 % and interturn faults at 10-80 % of the winding, Rf = 5 ohm; 360 training sets, 180 test cases | Sec. 4-5 |
| Reported result | 100 % (winding to ground, both sides), 98.61 % (interturn, HV), 100 % (interturn, LV) | Table 4, p. 370 |

## 3. UNSPECIFIED items and how they are filled
| Item | Fill |
|---|---|
| Whether the zero-sequence and phase differentials use CT ratio and phase-shift correction | The same plant compensation as for all methods, applied to the currents before differencing (YNd1: matrix on the HV side; Dyn11: on the LV side). The zero-sequence signal is taken from the three compensated differential currents, i0 = (iA + iB + iC) / 3 (a delta-side current has no zero-sequence component of its own); stated as a deviation. |
| Input normalisation range | min-max to [0, 1] with training-set statistics (the paper only says "normalization"). |
| Detector time base for the "5 x max" test at 20 kHz | the test is applied sample by sample on the squared scale-1 coefficient at the paper's rule (factor 5 against the largest value since the start of the record, here since the start of a rolling two-cycle history to avoid a pre-event transient from the energisation or load change). |
| Quarter cycle | 5 ms at 50 Hz = 100 samples at 20 kHz. |
| Initial weights | random (seeded per fold); one training run per size step as in Fig. 6. |
| "Test set" used for the MAPE stop rule | our inner validation split (never the outer test fold). |
| MAPE with zero targets (our all-zero "no internal fault" pattern gives a division by zero) | MAPE is evaluated only over the non-zero target entries, as the paper's targets are mostly zero too (7 of 8 outputs); stated. |
| Trip rule | not in the paper (it is a classifier): see section 4. |

## 4. Retargeting to our task (a deviation that has to be stated with the results)
The paper's classifier answers "which internal fault is it?". To use it as a protection element we keep its structure and extend the target coding by the all-zero pattern for "no internal fault" (external fault, inrush, over-excitation, normal operation): outputs 0 for all eight bits. A trip is declared at the first detection (X_chk = 1 for any phase) where any of the eight outputs exceeds 0.5. This is the minimal change that gives the network a negative class; a network trained without negative examples cannot reject anything. The method as published has no inrush or external-fault logic, and the results must be read with that in mind.
Two modes are reported (as for all methods): (a) native (the rule above); (b) the network's trip output (maximum of the eight outputs) put through our 20-sample dwell and validation-tuned threshold.

## 5. Deviations forced by our setup
| Paper | Ours | Effect |
|---|---|---|
| 200 kHz sampling (5 us) | 20 kHz (the highest rate in D2) | scale-1 detail covers 5-10 kHz instead of 50-100 kHz; the high-frequency content the paper used is mostly absent from our lumped models; recorded as a deviation |
| High-frequency transformer model with stray capacitances (ATP, Fig. 2) | lumped SimPowerSystems transformer without winding capacitances | much less high-frequency energy |
| Internal winding-to-ground and interturn faults at 10-90 % of the winding | terminal internal faults on the LV or HV side (our scenarios) | the type code is reduced to the fault phases and side |
| Training and test sets of 360 and 180 hand-picked cases | trace-grouped CV | models retrained per fold |
| Output = fault type | output = trip / no trip (extended coding) | see section 4 |

## 6. Sanity check to reproduce
Their Fig. 4: the scale-1 squared coefficients of the differential currents rise sharply at the fault inception for the faulted phase and stay near zero for the others. Reproduce with one of our internal single-phase faults at 20 kHz and save as `documents/baselines/ngaopitakkul2006_sanity.png`.

## 7. Cost to report
Network size (4 inputs, 12 and 11 neurons, 8 outputs) and the per-sample cost of the db4 filter at 20 kHz (a 8-tap FIR on the squared differential signals of four channels) are counted; the latency is measured at 20 kHz (budget 50 us per sample).
