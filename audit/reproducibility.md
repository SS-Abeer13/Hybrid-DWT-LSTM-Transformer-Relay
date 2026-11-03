# Reproducibility package plan (audit task F)

Date: 2026-11-03. Based on `git ls-files` at commit `bfc2f1d`, `.gitignore`, the run scripts in the repo root, and what the audit could actually re-run in a cloud session with no MATLAB, no GPU and no local drive.

## 1. What a reader needs, and what is on GitHub

| Layer | What | In the repo? | Notes |
|---|---|---|---|
| **Plant models** | `simulations/TransformerWithCTSaturation_v5.slx` (A), `simulations/TransformerB_v5.slx` (B) | ✅ tracked | MATLAB/Simulink with Simscape Electrical (Specialized Power Systems). The release is only named indirectly (an "R2023a" path in `IMPLEMENTATION_PLAN.md:592`): **record the exact release and toolboxes** |
| **Generators** | `simulations/generate_stress_dataset_v5.m`, `generate_stress_dataset_plant_b_v5.m`, the 20 kHz copies `generate_stress_dataset_hr_v5.m`, `generate_stress_dataset_plant_b_hr_v5.m`; drivers `run_v5_generation_all.bat`, `run_v5_hr_all.sh` (auto-resume) | ✅ | Plant checks: `simulations/plant_v5_checks_A.txt` / `_B.txt` |
| **Datasets** | `datasets/StressDataset_v5_20261028_162333.mat`, the four `StressDataset_v5Only_*.mat` top-ups, `StressDataset_v5OOD_20261028_205712.mat`, plant-B main/OOD/top-ups, and the 20 kHz blocks `datasets/hr/*.mat` | ❌ **ignored (`*.mat`)** | Only coverage reports (`datasets/*_coverage.txt/json`) are tracked. Regeneration takes about a day of MATLAB (log 2026-10-28/29, 2026-11-01) and needs the `.slx` and generator versions above |
| **Feature caches** | `runs/20261029_v5_cv5_seeds/traces_cache.npz` (249 MB), `runs/.../cache/*.pkl` | ❌ ignored (`*.npz`, `*.pkl`) | A light metadata file `runs/20261101_v5_benchmark_fair/trace_metas_plantA.json` (4.9 MB) is tracked and is enough to rebuild the folds (`lstm_models/baselines/cv.py` fallback) |
| **Trained models** | 15 CV LSTM checkpoints (`runs/20261029_v5_cv5_seeds/seed_*/fold*/transformer_protection_lstm_best.pth`), the final model (`runs/20261029_v5_final/`), the ONNX export, every baseline/reproduction model | ❌ ignored (`*.pth`, `*.onnx`) | Without them the deployed relay's numbers can be re-derived only by re-training. Thresholds are tracked (`runs/20261029_v5_final/decision_*.txt`) |
| **Per-trace results** | `runs/20261029_v5_cv5_seeds/seed_*/fold*/result.json`; `runs/20261101_v5_benchmark_fair/full/*/cv_seed*_fold*.json`, `final_*.json`; `b2_equal_search/final_seed*_fold*.json`; `n6c_tuned_rows.json`; per-method `rows_seed*_fold*.json` | ✅ (488 tracked files under `runs/`) | **Enough to recompute every statistic and table.** The audit did this: all 112 tests match (`audit/results_audit.md`) |
| **Evaluation / statistics code** | `lstm_models/train_cv_v5.py`, `train_trace_split.py`, `benchmark_literature_models.py`, `baselines/*`; `tools/run_full_eval.py`, `run_b2_search.py`, `run_key_hybrid.py`, `n5_statistics.py`, `n5c_keyhybrid.py`, `n6c_tuned_harmonic.py`, `n8a_…py`, `b2_summary.py`, `gated_only_ablation.py`, `publication_tables_AD.py`, `build_publication_tables_v5.py`, `build_paper_macros_v5.py` | ✅ | |
| **Reproduction specs** | `documents/baselines/*_spec.md` (with amendments), `REPORTING_NOTES.md`, sanity checks | ✅ | The cited papers' PDFs are **not** redistributable. They were in git commit `f92ea33` and should be removed from the public history if they are copyrighted (author decision) |
| **Environment** | Python version, package versions | ❌ no `requirements.txt` / lock file | Proposal: `audit/requirements.txt` (versions found in the repo; the rest must come from `pip freeze` on the original machine) |
| **Seeds** | CV seeds 20261021 / 22 / 23 (`cv.SEEDS`); per-fold model seed = seed + fold; B2 search seed 20261102 + hash of the model name (`run_b2_search.py`); generator seeds per trace (`sampleSeed` in `trace_metas_plantA.json`); run ids in the dataset file names | ✅ in code | GPU training is **not bit-reproducible**: two runs of Key / Afrasiabi on the same folds differ on 74 / 367 decisions (`results_audit.md` B-3). Say so |

## 2. Run order (to regenerate everything)

1. **Plants and checks:** `simulations/check_plant_physics_v5.m` → `plant_v5_checks_{A,B}.txt`.
2. **Data (MATLAB):** `run_v5_generation_all.bat` (plant A main 3,040 + OOD 300, plant B main 1,200 + OOD 150), then the top-ups (`run_v5_topups_A.sh`, `run_v5_topups_B_A2.sh`), then `lstm_models/coverage_report_v5.py`.
3. **20 kHz copies for the reproductions:** `run_v5_hr_all.sh`, then `tools/hr_missing_manifest_all.py` (common set: 3,302 of 3,332 plant-A traces).
4. **Proposed relay:**
   - `run_v5_cv.sh` → `train_cv_v5.py cv` (3 seeds × 5 folds; **window stride 8, the script default**);
   - `run_v5_final.sh` → `train_cv_v5.py final` (thresholds, OOD once);
   - `run_v5_generalization.sh` (plant B);
   - `tools/common_set_rescore.py`.
5. **Conventional relays:** `tools/evaluate_harmonic87t_v5.py`; then `tools/n6c_tuned_harmonic.py` (needs the .mat files).
6. **Reproductions:**
   - `tools/cache_simoes_energies.py`, then `tools/n2_simoes_factor.py`;
   - `tools/cache_abdusalam_feats.py`;
   - `tools/run_full_eval.py <method> both` for the six methods (runs: `full_*_log.txt`);
   - `tools/run_key_hybrid.py cv 0|1|2` and `final`;
   - `tools/measure_latency_baselines.py`, `tools/dlat_alhamd.py` (idle machine).
7. **Same-feature models:** `run_n6a.sh` (B1, stride 8); then `tools/run_b2_search.py search` and `final` (stride 4).
8. **Statistics (from saved rows only, minutes, no MATLAB):**
   - `tools/n4_full_summary.py`;
   - `n5_statistics.py` and `n5_statistics.py modeb`;
   - `n5c_keyhybrid.py`, `ddiag_falsetrip_paths.py`, `gated_only_ablation.py`, `b2_summary.py`, `n8a_instances_vs_tuned_harmonic.py`.
9. **Tables and macros:** `tools/build_publication_tables_v5.py` (Tables A–D), `tools/build_paper_macros_v5.py`.

**What a reader can run from GitHub alone:** steps 8–9, plus the audit's independent checks (`audit/scripts/recompute_stats.py`, `clustered_sensitivity.py`, `check_log_claims.py`, about 2 min on a laptop CPU). The audit ran independent equivalents of step 8 itself. It did **not** run step 9, because the build scripts overwrite tracked files.

**What needs the withheld data or models:** steps 1–7, i.e. every model fit, the tuned harmonic 87T, the plant-B and OOD scoring, latency and the Simulink closed loop.

## 3. Gaps to close before release (no new experiments)
1. **A data deposit** (Zenodo or similar, with a DOI). Minimal useful option: the per-trace feature arrays (`traces_cache.npz` for plant A, about 250 MB) plus the plant-B and OOD caches and the 15 + 1 LSTM checkpoints. That lets readers re-score the proposed relay without MATLAB. Full option: the `.mat` datasets (size to be checked on the local drive).
2. **`requirements.txt` / lock file** from `pip freeze` on the original machine (the audit's proposal lists what is known), plus the MATLAB release and toolbox list.
3. **Record the window stride per run** in the result JSON. The deployed CV used 8, B2 used 4, and one log entry and the Table B note say otherwise (`code_audit.md` C-1).
4. **A top-level `REPRODUCE.md`** with the run order above, the hardware used (AMD Ryzen 7 7700, RTX 5060 Ti for the GPU runs), and run times.
5. **Licence:** add a licence file for the code. Remove the third-party PDFs from history if they cannot be redistributed.

## 4. Proposed data and code availability statement (for the author to edit)

> **Data and code availability.**
> - The Simulink plant models, data generators, evaluation code, reproduction specifications, per-trace decisions of every method and every result file used for the tables are available at https://github.com/SS-Abeer13/Hybrid-DWT-LSTM-Transformer-Relay (release vX.Y, commit ⟨hash⟩).
> - The simulated datasets (⟨N⟩ traces, ⟨size⟩ GB) and the trained models are available at ⟨Zenodo DOI⟩ [*or:* are available from the corresponding author on request because of their size; they can be regenerated with the scripts listed in REPRODUCE.md, which requires MATLAB/Simulink ⟨release⟩ with Simscape Electrical].
> - All statistics and tables can be recomputed from the per-trace result files in the repository without MATLAB.
> - No field or utility data were used.

Fill the angle-bracket fields. Do not claim "regenerated" for the 20 kHz copies without the failure manifest: 30 plant-A traces failed to re-simulate (`documents/baselines/hr_missing_traces.txt`).
