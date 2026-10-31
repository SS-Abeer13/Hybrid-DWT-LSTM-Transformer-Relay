# Spec: Alhamd, Saniei, Seifossadat and Mashhour 2024 (improved wavelet analysis + bidirectional LSTM)

Paper: Q. Alhamd, M. Saniei, S. G. Seifossadat, E. Mashhour, "Advanced fault detection in power transformers using improved wavelet analysis and LSTM networks considering current transformer saturation and uncertainties," *Algorithms* 17(9), 397, 2024, DOI 10.3390/a17090397 (open access, 26 pages; read from the PDF; section and equation numbers are the paper's). Written 2026-11-01, before any code or result of this method.
Module (to be written): `lstm_models/baselines/alhamd2024_wavelet_lstm.py`.
The benchmark row "Standalone LSTM, Alhamd [1] / Atiyah [3]" mixed two papers. Atiyah et al. (J. Electr. Eng. Technol. 19(8), 2024, DOI 10.1007/s42835-024-02048-7, wavelet transform + LSTM in a cascading moving-window scheme) is a different method and is **not reproduced here**; if time allows it gets its own spec.

## 1. What the method is
The differential current is processed by a first-level real-time boundary stationary wavelet transform (RTBSWT, the same family as Simões et al.); features of the coefficients over 20 ms segments feed a **bidirectional** LSTM that identifies one of four conditions: inrush current, internal fault without CT saturation, internal fault with CT saturation, external fault with CT saturation. (Sec. 2-4, Algorithm 1)

## 2. Specification
| Item | Paper | Reference |
|---|---|---|
| Input signal | the differential current of the transformer from CTs on both sides (star-delta CT connections matched to the winding connection); noise and measurement uncertainty added | Sec. 3.1, Fig. 2, 4.1 |
| Sampling | 3 kHz (60 samples per 20 ms segment at 50 Hz); 132/33 kV YNd11, 63 MVA, 10 % impedance, CT 300:5 and 1200:5 | Sec. 4, Table 2 |
| Wavelet | first-level RT-SWT: S_x(k) = (1/sqrt2) sum h(l) x(k + l - L + 1), w_x(k) with the high-pass filter (Eqs. 9-10); improved version: RTBSWT with boundary coefficients, S_x(l,k) and w_x(l,k) = (1/sqrt2) sum_{n=0}^{L-1} h(n) x(k - L + n + 1 + l), 0 <= l < L, circular sliding window of Δk samples, periodised signal x(k+m) = x(k-Δk+m) (Eqs. 11-12); the db4 wavelet filter | Sec. 3.2, Algorithm 1 |
| Features | "features of the sampled signals are determined using the advanced wavelet transform"; "the mean value of each detail coefficient level of the signals" is computed (Sec. 4.2); Algorithm 1 refers to feature selection by its steps 1.13.1 and 1.13.2 (the wavelet and scaling coefficients) | Sec. 2, 4.2, Algorithm 1 |
| Network | LSTM with cell equations (21)-(26); the proposed network is **bidirectional** (forward and backward hidden sequences, Eqs. 27-29), i.e. the output at time t uses future samples; "enhanced LSTM" | Sec. 3.3 |
| Output / loss | "the model's outputs are the raw numerical predictions"; the network is trained to minimise the error between predicted and target signal types (RMSE and loss reported) | Sec. 3.3, 4.2 |
| Training | MATLAB 2024a; SGDM optimiser; 200 epochs; initial learning rate 0.01, dropped to 0.001 after about 100-150 epochs (Table 4); 25 % of the observations reserved as validation; segments of 0.02 s with 60 consecutive samples; final RMSE 0.039, loss 1.2e-4 | Sec. 4.2, Table 4 |
| Data | 2000 cases: 500 inrush, 500 internal faults (HV and LV, with and without CT saturation, Rf 0.001-75 ohm, load 5-33 MVA), 250 + 250 external faults under CT saturation (HV and LV, Rf up to 150 ohm); source phase angle 0-360 deg; real-world and augmented data (noise, scaling, rotation, SMOTE) added | Sec. 4, Table 3 |
| Reported result | about 99 % correct for each of the four conditions (Table 5), average detection times 110-170 ms | Table 5, Sec. 4.3 |

## 3. Notes on the paper (recorded)
1. The proposed LSTM is bidirectional: it cannot give an output for time t before the samples after t are available, so a decision requires a whole segment; the reported detection times (110-170 ms) are far above relay operating times. This does not make the method wrong for its purpose (event classification) but it is not comparable with a sample-by-sample relay without that being stated.
2. The task is "identify the type of event", with four classes; there is no normal-operation class and no trip logic.
3. The output is described as a regression of signal type with RMSE as metric.

## 4. UNSPECIFIED items and how they are filled
| Item | Fill |
|---|---|
| The exact feature vector | per 60-sample segment, per phase: mean, standard deviation and maximum of the first-level wavelet coefficients w(l,k) (l = 0 ... L-1, i.e. including the boundary coefficients) and of the scaling coefficients S(l,k); the sequence presented to the LSTM is the time series of these coefficient values over the segment (with L = 8 taps: 2 x 8 = 16 channels per phase, 48 for three phases). Recorded as an assumption; "mean value of each detail coefficient level" is covered by the mean of the wavelet channels. |
| db4 length | as in Simões et al. (ambiguity of db4 with 4 or 8 taps): L = 8 taps (MATLAB db4), because this paper uses "db4 wavelet filter" in MATLAB. |
| Differential-current definition | per phase, with our plant compensation, in CT-secondary amperes divided by the rated secondary current. |
| Number of layers and hidden units, dropout | not given. Search space with the same 12-configuration budget as every method: hidden units {32, 64, 128}, layers {1, 2}, dropout {0.1, 0.2, 0.3}, learning rate {3e-3, 1e-2 (the paper's), 3e-2}; bidirectional as in the paper. |
| Optimiser details | SGDM momentum 0.9 (MATLAB default), initial learning rate as searched, piecewise drop by 10 after epoch 100 of 200 (as in Table 4). The common 25-epoch budget of Part 1 is **not** used for this method: its paper's own schedule (200 epochs) is followed, but with early stopping on the validation loss (patience 20) so that the training time stays bounded; this is recorded because it gives the method a larger budget than the Part 1 models. |
| Output and loss | four output units, mean-squared error against one-hot targets (the paper's RMSE criterion), class = argmax. |
| Segment stepping and trip logic | not given. Native: every 5 samples (1/12 cycle at 3 kHz) the latest 60-sample segment is classified; trip when the class is "internal fault" or "internal fault with CT saturation" (either bit), at the first such segment after the inception; the segment must end after the event, so the earliest decision comes one segment length after the first sample of the disturbance if the segment is aligned to the event (the classifier never sees a mixed window in training; in test it does). |
| Missing classes | normal operation: our "normal", over-excitation, inrush (no-load, loaded, recovery) are mapped as follows: inrush and recovery inrush = the paper's inrush class; external faults of all kinds = external fault class; normal and over-excitation = none of the four classes (an extra "no event" output is added so that the network can say nothing happened; recorded deviation). |
| Data augmentation (SMOTE, scaling, rotation) | not applied (our data has the variation by simulation); recorded. |

## 5. Deviations forced by our setup
| Paper | Ours | Effect |
|---|---|---|
| 3 kHz, 63 MVA 132/33 kV YNd11, own CT model | 50 Hz plants A and B resampled from 20 kHz to 3 kHz (ratio 3/20) | |
| 2000 simulated + augmented cases | trace-grouped CV on our traces | leak-free |
| 4 classes | 4 + "no event" | the method gets a normal class it did not have |
| 200 epochs SGDM (own schedule) | same, with early stopping | |
| Detection times 110-170 ms | our scoring from fault inception to first trip | bidirectional windows delay the decision |

## 6. Sanity check to reproduce
Their Figs. 7-14: the differential current and its first-level wavelet and scaling coefficients for an inrush and for an internal fault, with and without noise. Plot the boundary and non-boundary coefficients for one inrush and one internal fault of ours; save as `documents/baselines/alhamd2024_sanity.png`.

## 7. Cost to report
Parameter count and operations per segment decision of the bidirectional LSTM, measured latency per decision at 3 kHz (decision every 5 samples: budget 1.67 ms).
