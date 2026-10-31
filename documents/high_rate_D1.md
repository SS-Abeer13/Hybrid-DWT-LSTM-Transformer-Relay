# D1: solver and sampling settings of the v5 plants, and the high-rate re-simulation settings (2026-10-31)

Sources: `simulations/solver_settings_v5.txt` (written by `check_solver_settings_v5.m`, read-only), `simulations/highrate_probe_v5_A.txt`, `highrate_probe_v5_B.txt` (written by `probe_highrate_v5.m`, changes in memory only).

## Current settings (both plants identical)
| Item | Value |
|---|---|
| Solver | variable-step ode23tb, MaxStep 1e-4 s, RelTol 1e-3 |
| powergui | Discrete, sample time 100 us (10 kHz), Backward Euler, Frequency parameter 60 |
| Band-limited white noise | Ts 100 us, power 0.1 per channel; the generator scales it to the target noise level from sqrt(0.1/Ts) |
| Quantizer | step 0.01 A on the six CT-secondary channels |
| Relay-input ZOH (`ZOH_1600`) and the two To Workspace blocks | 625 us (1600 Hz) |

Consequences: the electrical network is solved at 10 kHz, so the usable bandwidth is below 5 kHz and Backward Euler damps the upper part of it; the 1600 Hz data are zero-order-hold samples without an anti-alias filter. The `powergui` frequency parameter is 60 Hz while the traces use 50 Hz sources (the generator sets the source frequency per trace); this was not changed.

## High-rate settings tested (in memory)
powergui sample time 25 us (40 kHz); noise Ts 25 us; `ZOH_1600` and both To Workspace blocks 50 us (20 kHz). The logged channels are the CT-secondary currents plus noise and quantisation, as before.

## Measured (external 3-phase fault, 60 % load, one trace of 1.1 s)
| | standard | high rate |
|---|---|---|
| Plant A wall time | 13.7 s (includes model compilation) | 26.6 s |
| Plant B wall time | 11.3 s | 27.9 s |
| Samples per channel | 1761 | 22001 |
| One trace, 6 channels, float64 | 0.25 MB | 3.17 MB |
| Plant A LV RMS 0.55-0.65 s (A) | 12.987 / 12.986 / 12.987 | 13.043 / 13.042 / 13.043 |
| Plant B LV RMS 0.55-0.65 s (A) | 7.711 / 7.576 / 7.448 | 7.725 / 7.595 / 7.452 |
| Energy above 1.6 kHz / total, noise off | 0 | plant A 4e-8, plant B 5e-5 |

Observations to carry into D2-D4:
1. The high-rate run is about twice as slow, not four times. The main generation took about 5 s per trace (plant A, 3340 traces in 4.6 h), so a full high-rate pass is of the order of 10 s per trace, roughly 9 h for plant A (3340 traces) and 3.5 h for plant B (1290).
2. The step change moves the fundamental RMS by 0.4 % (plant A) and 0.2-0.3 % (plant B). D3 (decision equivalence after decimation) has to be judged on decisions, not on samples.
3. With noise off, the plant carries almost no energy above 1.6 kHz (4e-8 of the total on plant A). The transformer and CT models are lumped (no winding capacitances), so the high-frequency content that wavelet methods exploit comes mostly from the added noise and the switching transients, not from physical resonances. This limits how faithfully any method that relies on kHz content can be reproduced, and has to be stated with the results.
4. One high-rate trace is 3.17 MB (float64); 3340 traces are 10.6 GB. The generator keeps all traces of a run in memory before saving one file, so D2 needs a chunked writer (for example 100 traces per file, single precision) to stay under 4 GB of RAM.
5. The ratio 20 kHz / 1600 Hz is 12.5, not an integer: resampling to 1600 Hz in D3 needs a polyphase filter, not plain decimation. 12.8 kHz (Simoes) and 3.2 kHz (Key) are 20 kHz x 16/25 and x 4/25.

## Proposal for D2 (to be confirmed before it is run)
Re-simulate all plant-A v5 main traces (not a subset), the plant-A OOD set and all plant-B traces at 20 kHz; the seeds make every trace reproducible. Files `datasets/StressDataset_v5HR_*.mat`, chunked. Storage about 11 GB + 1 GB + 4.5 GB in float64 (half in single precision).
