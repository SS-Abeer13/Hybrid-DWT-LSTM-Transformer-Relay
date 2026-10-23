# Implementation Plan v3 — Full Dataset Coverage and Final Thesis Evaluation

**Project:** Hybrid DWT-LSTM transformer differential relay (87T), `F:\Transformer Thesis`
**Written:** 2026-10-20 23:45 (Asia/Dhaka)
**STATUS 2026-10-22: ALL STEPS A1-E4 DONE** (see the dated entries of 2026-10-21 / 22 in `IMPLEMENTATION_PLAN.md`; results in `documents/results_v3/`). Original status line follows.
**Status at writing:** paused at a clean checkpoint. Deployed relay is `runs/20261020_v3_87tfix` with the corrected 87T, the AI-alone trip path (AI_Threshold 0.90, AI_Solo_Threshold 0.995) and closed-loop 4/4 PASS. See the progress log in `IMPLEMENTATION_PLAN.md`.

This document is the **work plan from here to final thesis numbers**. `IMPLEMENTATION_PLAN.md` stays the dated **progress log**. Log every finished step there, with exact paths and saved numbers.

---

## 0. Why a v3 dataset is needed

The v2 dataset (`datasets/StressDataset_v2_20261020_005715.mat`, 1,200 traces) fixed the old generator bugs. The 2026-10-20 audits found these gaps. Each one limits what the thesis can claim.

| # | Gap in v2 | Evidence | Consequence |
|---|---|---|---|
| G1 | **Load is unrealistically low.** The load knob delivers only ~0.28 of nominal current (0.535 A per pu vs 1.8827 A rated). The v2 range 5-120 % "pu" is really **~1-34 % of rated current**. | Plant audit, log entry 2026-10-20 22:30 | Every result holds only for light load. Healthy differential, SLG fault current (returns through the load neutral) and CT stress all scale with load. |
| G2 | **Test cells are tiny.** Several categories have only 3-7 test traces per split. | v2 test reports | Per-category percentages (for example 85.7 % worst run) carry ±15-30 pt uncertainty. |
| G3 | **CT saturation only for 3-phase faults**, and only through low Rf and heavy load. CT burden and CT remanence are never varied. | `scenarioTable`: Stress_CTSat_Int / Stress_ExtCTSat are A-B-C only | The weakest category (Stress_ExtCTSat, 97.6 % mean / 85.7 % worst) is under-sampled and one-dimensional. |
| G4 | **No over-excitation (V/f) cases.** | Not in the scenario table | This is a classic 87T security case (5th harmonic) and is absent from both training and test. |
| G5 | **No recovery or sympathetic inrush.** Inrush is only switch-on energisation. | Not in the scenario table | Inrush after an external fault clears is a known false-trip trigger. |
| G6 | **Internal faults only at the LV (11 kV delta) terminals.** | Fault blocks `Internal_Fault1/2` | No HV-side internal faults. Single-line-to-ground behaviour is dominated by the delta / load-neutral path (Internal_BG miss). |
| G7 | **High-impedance internal faults are poorly bounded.** 83 of 499 internal faults were below 0.05 pu and were dropped. The HiZ range (1-25 Ω) is not tied to the relay's sensitivity. | `check_stress_dataset_v2.py` output | Unclear where the detectable limit lies. The AI-solo path (HiZ 0 → 97 %) needs a well-sampled boundary. |
| G8 | **No point-on-wave control.** The inception angle is random but not stratified. Residual flux is random but not stratified. | `drawParameters` | Worst-case inrush (closing at voltage zero with high remanence) and DC-offset faults may be rare. |
| G9 | **No frequency deviation and no source-strength sweep** beyond ±5 % voltage. | `drawParameters` | Robustness to 49.5-50.5 Hz and weak or strong sources is untested. |
| G10 | **No out-of-distribution (OOD) test.** | Single-distribution splits | Cannot show generalisation outside the training ranges. |

---

## 1. Coverage targets (the v3 dataset)

### 1.1 Parameter dimensions and ranges

All loads below are **% of rated CT-secondary current (1.8827 A)**, after the calibration in Step A2. They are not knob values.

| Dimension | Range (train / main test) | OOD-only range | Sampling |
|---|---|---|---|
| Load | 10-110 % rated (4 bins: 10-30, 30-60, 60-90, 90-110) | 0-10 %, 110-130 % | Stratified per bin |
| Power factor | 0.80-1.00 lagging | 0.70-0.80 | Uniform |
| Source voltage | 0.95-1.05 pu | — | Uniform |
| Source strength (series Z scale) | 0.5-2.0 × nominal | 3 × (weak) | Log-uniform |
| Frequency | 49.8-50.2 Hz | 49.5, 50.5 Hz | Uniform |
| Inception / closing angle | 0-360° (4 quadrants, stratified; extra weight near 0° and 90°) | — | Stratified |
| Residual flux (inrush) | 0-0.8 pu peak, random sign pattern (sum = 0) | 0.9 pu | Stratified in 3 bins |
| Fault resistance, solid | 0.01-2 Ω | — | Log-uniform |
| Fault resistance, HiZ | Set by the **sensitivity sweep** (Step A4): from the 0.3 pu 87T pickup edge to below the 0.05 pu limit | Beyond the limit | Log-uniform, 3 bins (87T-visible / AI-only / undetectable) |
| CT burden | 1-4 × nominal | 6 × | Uniform |
| CT remanence | 0-0.6 pu | 0.8 pu | Uniform |
| CT ratio mismatch | ±2 % (±5 % in stress) | ±8 % | Uniform |
| Noise | 0.05-1 % rated (1-3 % in stress) | 5 % | Log-uniform |
| Over-excitation (V/f) | 1.05-1.40 pu | 1.5 pu | Uniform |
| Fault timing | 0.30-0.75 s inception, 1.1 s run | — | Uniform |

### 1.2 Scenario quotas (main dataset, about 3,000 traces)

Target: **≥ 60 traces in every reported category**. With 5-fold grouped cross-validation (Section 3), every trace is tested once, so each category gets ≥ 60 test decisions instead of 3-7.

| Group | Scenario | Count | Should trip | Notes |
|---|---|---|---|---|
| **Healthy** | Normal (load sweep) | 300 | No | 75 per load bin |
| | Inrush, no load | 200 | No | Angle × residual-flux stratified |
| | Inrush, loaded | 120 | No | |
| | Recovery inrush (external fault cleared) | 80 | No | **New (G5).** External fault 40-100 ms, then clears |
| | Sympathetic inrush (parallel unit energised) | 50 | No | **New (G5).** Only if the model can host a second unit (Step A6); otherwise drop and record |
| | Over-excitation | 150 | No | **New (G4)** |
| | External faults, 10 fault types × 40 | 400 | No | Solid, Rf 0.01-5 Ω |
| | External HiZ | 60 | No | |
| | External + CT saturation, all fault types | 240 | No | **Extended (G3).** SLG, LL, LLG, 3Φ × burden × remanence |
| | External fault during inrush | 100 | No | |
| | **Healthy total** | **≈ 1,700** | | |
| **Faults** | Internal LV-side, 10 fault types × 50 | 500 | Yes | Solid |
| | Internal HV-side, 10 fault types × 20 | 200 | Yes | **New (G6).** Only if Step A5 adds the block |
| | Internal HiZ, 3 Rf bins × 5 types × 16 | 240 | Yes | **Redefined (G7).** Boundary from Step A4 |
| | Evolving | 80 | Yes | |
| | Switch-on-to-fault (SOTF) | 80 | Yes | |
| | Internal + CT saturation, all types | 120 | Yes | **Extended (G3)** |
| | Internal fault during inrush | 120 | Yes | |
| | **Fault total** | **≈ 1,340** | | |
| | **Grand total** | **≈ 3,040** | | About 57 % healthy / 43 % fault |

### 1.3 Separate OOD test set (about 300 traces, never used for training or tuning)

| Block | Count | What it tests |
|---|---|---|
| Extreme load (0-10 %, 110-130 %) | 60 | Generalisation in load |
| Weak source (3 ×), frequency ±0.5 Hz | 60 | Source robustness |
| CT burden 6 ×, remanence 0.8 pu | 60 | CT saturation beyond training |
| Over-excitation 1.5 pu, residual flux 0.9 pu | 60 | Harmonic-heavy healthy cases |
| Noise 5 %, CT mismatch ±8 % | 60 | Measurement robustness |

Half of each block is healthy and half fault. Report it separately and **never tune on it**.

### 1.4 Coverage acceptance (must pass before training)

A new script, `lstm_models/coverage_report_v3.py`, writes `datasets/StressDataset_v3_<run>_coverage.txt`. It must show:

1. Every scenario × load-bin cell has **≥ 10 traces that pass all checks** (≥ 5 for HV-side and sympathetic cells).
2. Every inrush cell (angle quadrant × residual-flux bin) has ≥ 10 traces.
3. Every HiZ Rf bin has ≥ 40 traces, and the measured `faultDiffPu` histogram straddles the 0.3 pu and 0.05 pu lines.
4. CT-saturation cases show **measured** saturation: CT ratio error > 10 % in ≥ 70 % of `*CTSat*` traces (new per-trace check, Step A3).
5. Over-excitation cases show a 5th-harmonic ratio > 0.2 in ≥ 80 % of traces.
6. Realised load is within ±10 % of target in ≥ 95 % of traces.
7. Generator checks pass in ≥ 97 % of traces overall and ≥ 90 % in every scenario, and there are 0 duplicate fingerprints.

If a cell fails, top it up with `generate_stress_dataset_v3(..., 'Only', '<scenario>')`. Do not move to training with an empty cell.

---

## 2. Work packages

Time estimates assume about 5 s per simulated trace (measured on v2), one process at a time, and a 4 GB RAM cap.

### Phase A — Generator v3 (MATLAB) · about 1 day

| Step | Task | Output | Check |
|---|---|---|---|
| **A1** | Copy `simulations/generate_stress_dataset_v2.m` → `generate_stress_dataset_v3.m`. Keep v2 untouched for reproducibility. Add `'Only'` and `'Chunk'` options (Chunk = restart MATLAB proactively every 200 traces; the heap crash 0xc0000374 appears after about 50-150 sims). | `generate_stress_dataset_v3.m`, `run_stress_v3_generate.bat` (auto-resume loop like `run_stress_v2_resume.bat`) | mh_lint / MATLAB MCP `check_matlab_code` clean |
| **A2** | **Calibrate load (fixes G1).** Sweep the load knob over 0.1-5 in 10 steps on a Normal case. Fit realised CT-secondary RMS vs knob. Store the map in `relay_config.m` as `cfg.LOAD_KNOB_PER_RATED`. `drawParameters` then samples **% rated** and converts it to a knob value. Check that the source voltage at 110 % rated stays > 0.9 pu; if not, document it. | `simulations/calibrate_load.m`, `simulations/load_calibration.txt` | Realised load ±10 % of target over the range |
| **A3** | **CT stress dimensions (fixes G3).** Find the CT burden and remanence parameters in the CT saturation subsystems. Expose them via `setp` with read-back. Add a per-trace check `ctRatioErrorMax` (max over the post-event cycle of \|I_sec·N − I_prim\| / \|I_prim\|). Extend the CT-stress scenarios to all 10 fault types. | Updated generator, new field `ctRatioErrorMax` | Self-test: burden 4 × visibly saturates (ratio error > 10 %) |
| **A4** | **HiZ sensitivity sweep (fixes G7).** For each fault type, sweep Rf (log, 0.1-100 Ω) at 3 load levels. Record `faultDiffPu` with the corrected differential. Fit Rf at 0.3 pu (87T pickup) and at 0.05 pu (detect limit). Set the three HiZ Rf bins from these curves. | `simulations/hiz_sensitivity_sweep.m`, `figures/hiz_sensitivity.png`, `hiz_bins.json` | Curves are monotonic; bins are non-empty |
| **A5** | **HV-side internal fault (fixes G6).** Back up the `.slx`. Add a Three-Phase Fault block plus a timer step on the HV winding terminals, inside the CT zone, named `Internal_Fault_HV`. Wire it like `Internal_Fault1`. If the model structure makes this unsafe, **skip it and state the limitation** in the thesis. | `TransformerWithCTSaturation_BACKUP_<date>_pre_hvfault.slx`, updated `.slx` | Self-test: HV A-G solid fault gives `faultDiffPu` > 1 pu |
| **A6** | **New healthy scenarios (fixes G4, G5).** `overexcitation`: set srcScale to 1.05-1.40 from t = 0. `recovery_inrush`: an external 3Φ fault at t1, cleared at t1 + 40-100 ms via the fault block's switching times. `sympathetic`: only if a second transformer + breaker can be added safely; otherwise drop it and log the decision. | Generator `applyScenario` cases | Self-test shows a 5th harmonic for over-excitation and inrush-like 2nd harmonic after clearing |
| **A7** | **Stratified sampling (fixes G8, G9).** Replace pure `rand` with stratified draws per scenario: load bin, angle quadrant, residual-flux bin (round-robin over cells, random inside a cell). Add frequency and source impedance draws. Log every realised value in the dataset. | Generator | Coverage report cells balanced to within ±20 % |
| **A8** | **Self-test v3:** at least 1 case per scenario kind (about 14 cases), nothing saved, all checks printed. | `simulations/stress_v3_selftest.txt` | All pass, or each failure explained |

### Phase B — Generate · about 5-6 h unattended

| Step | Task | Output |
|---|---|---|
| **B1** | Main set: `run_stress_v3_generate.bat 3040` (auto-resume; seed 20261021). | `datasets/StressDataset_v3_<run>.mat` |
| **B2** | OOD set: `run_stress_v3_generate.bat 300 OOD` (separate seed, OOD ranges). | `datasets/StressDataset_v3OOD_<run>.mat` |
| **B3** | `python lstm_models/check_stress_dataset_v2.py` (works on v3 fields) + `coverage_report_v3.py`. Top up failed cells. | Coverage report passes §1.4 |

### Phase C — Training and evaluation (Python) · about 1 day CPU

| Step | Task | Output | Pass criterion |
|---|---|---|---|
| **C1** | **No-change baseline:** score the deployed `runs/20261020_v3_87tfix` checkpoint on the full v3 data (`--evaluate-only`, hybrid + solo) and on OOD. This shows how the current relay does at realistic load **before** retraining. | `runs/<date>_v3data_baseline/` | — (reference) |
| **C2** | **Grouped 5-fold cross-validation** (new `--cv 5` in `train_trace_split.py`). Folds are grouped by trace and **stratified by scenario**. In each fold, 15 % of the training part is validation for threshold tuning (plateau rule, AI and solo thresholds). Keep the features (12, W = 32, plant-compensated input) and the architecture **unchanged** for this run. | `runs/<date>_v3_cv5/fold{1..5}/`, `cv_summary.json/.txt` | See §4 targets |
| **C3** | **Repeatability:** repeat C2 with 3 seeds. Report mean ± sd across the 15 models. | `runs/<date>_v3_cv5_seeds/summary.txt` | sd of dependability and security < 2 pt |
| **C4** | **Conditional feature change:** only if over-excitation security < 99 % or CT-sat external security < 98 % after C2, add **5th-harmonic ratios (3 features → 15 total)** in `features12.py` / `extract_12_features.m` (rename to `features15`), redo parity, repeat C2. Otherwise keep 12 features. | `runs/<date>_v3_cv5_f15/` | Must beat C2 on the weak category without losing > 0.5 pt elsewhere |
| **C5** | **Final model:** train on all main-set traces minus a 15 % validation hold-out, with the tuned settings. Evaluate once on **OOD**. | `runs/<date>_v3_final/`, `report_ood.json` | Report as-is; no re-tuning after seeing OOD |
| **C6** | **Ablations for the thesis:** (a) 87T alone (corrected), (b) LSTM alone, (c) hybrid gated only, (d) hybrid + solo. All use the same CV folds. | `runs/<date>_v3_ablation/ablation.txt` | Table for the results chapter |

### Phase D — Simulink deployment and closed-loop validation · about 0.5 day

| Step | Task | Output | Pass |
|---|---|---|---|
| **D1** | Back up `.slx`, `live_relay_ai.mat`, ONNX. Export the C5 model to ONNX (PyTorch vs ONNX error < 1e-6). Rebuild `live_relay_ai.mat`. Set `AI_Threshold` and `AI_Solo_Threshold`. Verify in the saved `.slx`. | `*_BACKUP_<date>_pre_v3.*` | Values read back |
| **D2** | Feature parity check (plant-compensated), plus the 5th harmonic if C4 was adopted. | `simulations/feature_parity_v3.txt` | Max error ≤ 1e-6 |
| **D3** | **Extended closed-loop benchmark: 12 cases** (was 4): Normal at 30 % and 100 % load; inrush with 0.8 pu remanence at a 0° closing angle; recovery inrush; over-excitation 1.3 pu; external 3Φ; external SLG with CT saturation; internal A-G solid; internal A-B HV-side (if A5); **internal HiZ in the AI-only bin (exercises the solo path)**; SOTF; fault during inrush. Retry on heap crash. | `simulations/test_hybrid_relay_v3_results.txt/.mat` | 12/12 correct; internal trips ≤ 1.5 cycles (30 ms) |
| **D4** | **Closed-loop statistical spot-check:** run 50 random OOD + test traces through Simulink. Compare the Simulink trip/no-trip and trip time with the Python relay mirror. | `simulations/closed_loop_vs_python_v3.txt` | Decision agreement ≥ 98 %; trip-time difference ≤ 2 ms median |

### Phase E — Thesis reporting · about 1 day

| Step | Task |
|---|---|
| **E1** | Results tables only from saved files: CV mean ± sd (C2/C3), per-category with 95 % Wilson intervals, OOD (C5), ablation (C6), closed loop (D3/D4). |
| **E2** | Figures: HiZ sensitivity curve (A4), threshold sweep curve (dependability vs security), operate-time CDF, coverage heat-map, one example waveform per category. |
| **E3** | Limitations section: simulation-only; transformer model (no turn-to-turn faults); the load model; HV-side faults (if A5 was skipped); sympathetic inrush (if skipped); one plant rating. |
| **E4** | Replace or retire `walkthrough.md` (it has unsupported numbers). Update `CLAUDE.md` with the new deployed run. |

---

## 3. Evaluation protocol (fixed before training — do not change after seeing results)

1. **Unit of evaluation:** one trace. Leak-free: every window of a trace lives in one fold only, and fingerprints are deduplicated.
2. **Labels:** trip windows start 8 samples (5 ms) after the **measured** onset. Faults below 0.05 pu corrected differential are counted as "undetectable" and reported separately, not dropped silently.
3. **Relay mirror:** trip = high-set OR (87T vote AND confirmed LSTM ≥ AI_Threshold) OR (confirmed LSTM ≥ AI_Solo_Threshold). "Confirmed" = minimum of the last 20 outputs (dwell 20 samples = 12.5 ms), matching `lstm_predict_wrapper.m`.
4. **Thresholds:** plateau rule on validation traces only (dependability within 2 pt and security within 1 pt of best, logit centre).
5. **Metrics:** dependability (faults tripped), security (healthy not tripped), pre-fault trips, operate time (median, p90, max, % ≤ 1 cycle, % ≤ 2 cycles), per category with 95 % Wilson intervals.
6. **OOD set** is scored once with the final model.

## 4. Targets (to judge success, not to tune on)

| Metric | Target |
|---|---|
| Security, all healthy (CV mean) | ≥ 99.5 % |
| Security, inrush / recovery inrush / over-excitation | ≥ 99 % each |
| Security, external + CT saturation | ≥ 98 % (now 97.6 % mean, 85.7 % worst, at light load) |
| Dependability, detectable internal faults | ≥ 99 % |
| Dependability, HiZ AI-only bin | ≥ 90 % (report honestly whatever it is) |
| Median operate time | ≤ 16 ms; ≥ 95 % within 2 cycles |
| Pre-fault trips | 0 |
| OOD | Report as measured; a drop of > 5 pt in any block goes into Limitations |

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| MATLAB heap corruption (0xc0000374) | `Chunk` restarts every 200 traces + auto-resume loop; partial saves every 25 traces |
| Load calibration needs knob values > 4, and the source sags | Check in A2; if the sag is > 10 %, lower the source impedance or cap at the reachable load and document it |
| Adding blocks (A5, A6) breaks the model | Backups before every `.slx` change; each block addition gets its own self-test; skip and document if unsafe |
| CT saturation too mild to matter | The A3 ratio-error check; raise burden or remanence until ≥ 70 % of CT-sat traces exceed 10 % |
| CPU training time (5 folds × 3 seeds × about 10 min) | About 2.5 h; run overnight; one process at a time (4 GB cap) |
| Results get worse at realistic load | That is a finding, not a failure. C1 measures it first. Report it, then retrain |

## 6. Order of work and resume points

```
A1 → A2 → A3 → A4 → (A5) → A6 → A7 → A8 self-test ✅
→ B1 + B2 generate (unattended) → B3 coverage ✅
→ C1 baseline → C2 CV → C3 seeds → (C4 if needed) → C5 final + OOD → C6 ablations
→ D1 deploy → D2 parity → D3 12-case closed loop → D4 spot-check
→ E1-E4 thesis
```

After each step, add a dated entry to `IMPLEMENTATION_PLAN.md` (what ran, paths, numbers, decisions). If a session stops, resume from the first step here without a ✅ in the log.

## 7. Decisions needed from the author (before Phase A finishes)

1. **HV-side internal faults (A5):** add the block to the model, or document it as a limitation?
2. **Sympathetic inrush (A6):** add a second transformer, or document it as a limitation?
3. **Dataset size:** 3,040 + 300 OOD (about 5-6 h generation) as planned, or a smaller 2,000-trace version (about 3 h) with ≥ 40 per category?


---

## 8. Erratum and author decisions (added 2026-10-21 during A1-A2)

1. **Decisions (author, 2026-10-21):** HV-side internal faults (A5): **add**, back up the .slx first, drop and document if the self-test fails. Sympathetic inrush (A6): **skip**, list as a limitation. Dataset size: **full, 3,040 main + 300 OOD**.
2. **Rated CT-secondary current is 0.9302 A (both sides), not 1.8827 A.** Ground truth from the V-I measurement blocks (`simulations/probe_ct_truth.m`): effective CT ratios HV 809.6:1, LV 16925:1 (2.024 x the winding-voltage ratios). Every "% rated" in this plan uses 0.9302 A.
   Section 0, G1 changes accordingly: the v2 range "5-120 % of 300 MVA" was ~2-70 % of rated current (the load knob itself works; the CT scaling was the cause of the apparent 28 %). The 87T chart was corrected twice (see `IMPLEMENTATION_PLAN.md`, 2026-10-21 10:30).
3. **LV voltage sag (A2):** the plant has ~1 pu series impedance on the LV side; LV bus voltage is 0.84 pu at 30 % and 0.35 pu at 110 % of rated current. The A2 check "> 0.9 pu at 110 %" fails; the plant is left unchanged and this is a Limitation (E3).
   The reachable load range is 2-136 % of rated current, so every load bin of section 1.1 (and the OOD 110-130 % block) can be generated.
