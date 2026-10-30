# Hybrid DWT-LSTM Supervisory Transformer Differential Protection

Simulation study of a transformer differential relay that combines a conventional dual-slope 87T with a DWT-feature LSTM. The relay model, the data generators (MATLAB/Simulink), the training and evaluation code (Python) and the closed-loop test benches are in this repository. All numbers below are written by `tools/build_readme_v5.py` from the saved result files in `runs/` and `simulations/`.

**Status.** Simulation only (no hardware-in-the-loop, two simulated transformers, terminal faults). The v4 results in earlier commits were produced with a plant whose through-fault level (23.9 and 37.6 pu) and CT sizing were unrealistic and with a mis-calibrated plant-B 87T; they are superseded by the v5 rebuild described here.

## Relay logic

trip = high-set OR (87T vote AND confirmed LSTM score >= AI threshold) OR confirmed LSTM score >= AI-alone threshold. The confirmed score is the minimum of the last 20 network outputs (1600 Hz). Final plant-A model: AI threshold 0.9950, AI-alone threshold 0.9980, dwell 20, tuned on validation traces only.

## Plants and data (v5)

| | Plant A | Plant B |
|---|---|---|
| Transformer | 300 MVA, 230/11 kV, YNd1, 5 A CTs | 40 MVA, 132/33 kV, Dyn11, 1 A CTs |
| True external through-fault (RMS, steady) | 7.39 pu | 8.64 pu |
| CT design | linear at nominal burden; saturates with DC offset or raised burden | linear at nominal burden; saturates with raised burden only |
| Trace sets | main (3040 + top-ups) and OOD (300) | main (1200 + top-ups) and OOD (150) |

Plant checks: `simulations/plant_v5_checks_A.txt`, `plant_v5_checks_B.txt` (plant B fails check C4 and C6 as recorded there). Dataset coverage: `datasets/*_coverage.txt`.

## Results, plant A (grouped 5-fold CV, 3 seeds, 15 fold-models, pooled)

| Variant | Dependability % | Security % |
|---|---|---|
| 87T alone | 80.34 | 63.41 |
| LSTM alone | 97.68 | 95.60 |
| Hybrid (87T gate) | 88.38 | 99.43 |
| Hybrid + AI-alone path | 92.99 | 98.96 |
| Per-phase harmonic-restrained 87T | 85.93 | 99.40 |

Hybrid + AI-alone path, mean +/- SD over the 15 fold-models: dependability 93.03 +/- 3.60 %, security 98.96 +/- 0.81 %.

Paired McNemar tests (`runs/20261029_v5_stats/stats.json`), hybrid vs per-phase harmonic 87T: dependability p = 4.1e-29, security p = 0.46.

Out-of-distribution set (scored once, 299 traces): hybrid dependability 98.0 %, security 96.0 %.

Weakest category (hybrid, CV pooled): Internal HiZ 65.8 %, External in inrush 88.3 %, SOTF 90.0 %.

## Plant B

| Experiment | Dependability % | Security % |
|---|---|---|
| Zero-shot, plant-A model: Proposed | 92.70 | 88.35 |
| Zero-shot: per-phase harmonic 87T | 94.12 | 98.95 |
| Cross-plant training (A + B), pooled | 94.78 | 98.22 |
| Train A, test B | 93.10 | 89.79 |
| Train B, test A | 62.51 | 97.28 |

Zero-shot trip-path check (`trip_path_check.txt`): of 89 false trips, 87 come first through the AI-alone path; without that path the zero-shot relay gives 90.47 % dependability and 99.21 % security.

## Closed loop and timing

- Simulink closed loop (LSTM active) vs Python relay mirror, plant A: decision agreement 50 / 50.
- Plant B 12-case suite: 12 / 12 cases correct.
- Execution time of the feature extraction + LSTM pipeline, one window per call, development PC: ONNX Runtime median 139.6 us, hand-written ANSI C median 175.9 us (sample period 625 us). The C source is written by `tools/build_and_run_c_benchmark.py`; it is not MATLAB Coder output and was not run on a relay processor.

## Design variant tested after the v5 results (E1)

Using the per-phase harmonic-restrained 87T as the gate of the hybrid (protocol fixed before the run, `IMPLEMENTATION_PLAN_V4_PUBLICATION.md`): CV dependability 91.98 % / security 99.38 % (current hybrid 92.99 / 98.96); OOD security 92.67 % vs 96.00 %. Not adopted.

## Limitations

- Internal high-impedance faults: hybrid correct on 65.8 % of the CV traces.
- Simulation only; two transformers; terminal faults; no hardware-in-the-loop.
- The plant-A model does not transfer to plant B without retraining (zero-shot security above).
- Closed loop, plant A: two of the 50 traces fail the 30 ms / correct-decision check (`simulations/test_hybrid_relay_d5main_results.txt`).

## Layout

| Path | Content |
|---|---|
| `simulations/` | Simulink plants (`*_v5.slx`), builders and probes (`build_plants_v5.m`, `check_plant_physics_v5.m`), generators (`generate_stress_dataset_v5.m`, `generate_stress_dataset_plant_b_v5.m`), calibration, closed-loop scripts |
| `lstm_models/` | features, 87T mirror (`relay87t.py`), training and CV (`train_cv_v5.py`), coverage report (`coverage_report_v5.py`), literature baselines |
| `tools/` | statistics, plant-B transfer experiments, harmonic 87T, E1, latency benchmark, table builders |
| `latex_source/` | thesis sources and the generated tables (`tools/build_publication_tables_v5.py`) |
| `IMPLEMENTATION_PLAN*.md` | protocol, dated log, reviews |

## Reproduce

Requires MATLAB R2023a with Simulink, Simscape Electrical, Wavelet and Deep Learning toolboxes, and Python 3.11 (numpy, scipy, scikit-learn, pywt, torch, onnx, onnxruntime, h5py).
Datasets (`*.mat`), model files (`*.pth`, `*.onnx`) and `runs/` are not in the repository (size); regenerate them:

```
run_v5_generation_all.bat                      # plant A and B main + OOD sets (about 8 h), then the top-ups listed in IMPLEMENTATION_PLAN.md
python lstm_models/coverage_report_v5.py datasets/StressDataset_v5_<run>.mat [top-up files]
python lstm_models/train_cv_v5.py cv --files <main + top-ups> --run-dir runs/<tag>_cv5_seeds --seeds 20261021 20261022 20261023
python lstm_models/train_cv_v5.py final --files <main + top-ups> --ood <ood file> --run-dir runs/<tag>_final
python tools/evaluate_harmonic87t_v5.py --files <...> --ood <...> --cv-dir runs/<tag>_cv5_seeds --output-dir runs/<tag>_harmonic87t
python tools/compute_v4_statistics.py --cv-dir ... --harmonic-dir ... --lit-dir ... --output-dir runs/<tag>_stats
python tools/run_plant_b_generalization_v5.py --plant-a-run runs/<tag>_final --plant-a-files <...> --plant-b-files <...> --out-tag <tag>
python tools/build_publication_tables_v5.py && python tools/build_readme_v5.py
```

MATLAB is started with `matlab -batch`; every generator resumes from its `_PARTIAL.mat` with the same run id.
