# Transformer Thesis - Hybrid DWT-LSTM differential relay (87T)

Start every session by reading `IMPLEMENTATION_PLAN_V3.md` (the work plan, steps A1-E4, section 8 = erratum and author decisions) and `IMPLEMENTATION_PLAN.md`
(the dated PROGRESS LOG: status, findings, exact paths, how to resume). Resume from the first V3 step without a done entry in the log.
Do not trust `walkthrough.md` numbers (unsupported). Report only numbers from saved output files.

## Facts that are easy to get wrong (all measured, see the log entries of 2026-10-21)
- Rated CT-secondary current is **0.9302 A on both sides** (effective CT ratios HV 809.6:1, LV 16925:1). NOT 1.8827 A, NOT 0.8557 A.
- The plant's LV side has three 0.5 ohm series resistors that are part of the LV CT drive: do NOT change them (a 0.02 ohm attempt destroyed the LV CT output; reverted).
  Consequences (Limitations): weak external faults (~1.5 pu rms at the CTs), LV bus voltage sags under load; CT remanence cannot be modelled; no sympathetic inrush.
- Plant mapping on healthy traces: LV = (1/sqrt3)[1 0 -1;-1 1 0;0 -1 1] * HV (the old relay chart used the transpose). The LSTM input is Is - Ip*M (plant-compensated).
- Hybrid trip logic (decision chart): high-set OR (87T vote AND confirmed LSTM >= AI_Threshold) OR confirmed LSTM >= AI_Solo_Threshold. Confirmed = min of the last 20 outputs.
- Model additions (2026-10-21): `Internal_Fault_HV`/`Step_HV` (HV-side internal fault) and `External_Fault_HV`/`Step_ExtHV` (HV-bus fault for recovery inrush).
  Never save the .slx with a test configuration baked in: add_hv_*.m reload the pristine file, add only the blocks, save. Previous states: `simulations/*_BACKUP_20261021_*.slx`.

## Layout
- `simulations/`  MATLAB/Simulink plant, relay_config.m (cfg.I_RATED_SEC, load calibration table), lstm_predict_wrapper.m, `generate_stress_dataset_v3.m` (current generator; v2 kept for reference),
                  calibrate_load.m / load_knob_for.m, hiz_sensitivity_sweep.m + hiz_bins.json, add_hv_*.m, fix_*.m, probe_*.m, `stress_v3_selftest.txt`
- `lstm_models/`  train_trace_split.py (v2-era single split, still the building blocks), `train_cv_v3.py` (Phase C: CV, baseline, ablations), `coverage_report_v3.py` (B3), relay87t.py (Python mirror of the corrected 87T),
                  features12.py, stress_dataset.py, hiz_bins_fit.py, export_onnx.py
- `datasets/`     StressDataset_v3_<run>.mat (main, 3040), StressDataset_v3OOD_<run>.mat (OOD, 300), StressDataset_v3Only_<run>.mat (top-ups); v2 files are legacy
- `runs/`         trained runs; deployed model = runs\20261022_v3_final (AI 0.99, solo 0.998, dwell 20; plan V3 complete); CV runs runs\20261021_v3_cv5*, baseline runs\20261021_v3data_baseline; results documents\results_v3
- Python: `.venv-lstm` is dead. Use system Python311 with `PYTHONPATH=.pylibs` (numpy 1.26 + PyWavelets); see run_closed_loop_benchmark_v3.bat

## Rules
- Evaluate leak-free: split by trace, labels from measured fault onset, one deployed model everywhere. Protocol is fixed in IMPLEMENTATION_PLAN_V3.md section 3: do not change it after seeing results; never tune on the OOD set.
- Back up .slx / live_relay_ai.mat before changing them. Never delete user data.
- Long MATLAB runs crash (heap corruption 0xc0000374): use run_stress_v3_generate.bat / run_stress_v3_generate_bg.sh (restart every 100 sims, resume from the partial file).
  Only ONE MATLAB (about 3 GB) at a time; keep total RAM under 4 GB (Python training peaks ~1.7 GB, so do not train while MATLAB runs the generator unless the files are tiny).
- Update IMPLEMENTATION_PLAN.md (dated log + next steps) after each milestone.
- Git: do NOT push. When committing, leave no trace of Claude (no Claude author, no Co-Authored-By / Claude-Session lines, no mention in the message).
