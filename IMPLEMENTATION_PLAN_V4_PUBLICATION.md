# Implementation Plan v4 — From Thesis to Journal Paper

**Written:** 2026-10-26 (Asia/Dhaka)
**Starting point:** thesis results complete and verified (`REVIEW_FIXES_2026-10-26.md`, all items closed). The deployed model is `runs/20261022_v3_final`. The fair harmonic-restrained 87T baseline is `runs/20261026_harmonic87t`.
**Goal:** remove the reviewer-blocking gaps that are doable without hardware, then write a journal paper.
**Target journals** (2025 JIF, verify in JCR before citing):
- **Primary:** Int. J. Electrical Power & Energy Systems (IJEPES, 5.3) or Electric Power Systems Research (EPSR, 4.3).
- **Stretch:** Protection and Control of Modern Power Systems (≈ 11–12).
- **Fallback:** IET GTD (2.8) or IEEE Access (4.2).

**Out of scope (author decision):** hardware-in-the-loop (RTDS / OPAL-RT) and field recordings. State this as a limitation in the paper.

`IMPLEMENTATION_PLAN.md` stays the dated progress log. This file is the work plan. Resume from the first step without a ✅ entry in the log.

---

## Why these fixes (reviewer view)

| # | Gap a reviewer will raise | Fix in this plan |
|---|---|---|
| G1 | External through-faults reach only ~1.5 pu at the CTs (real: 5–20 pu). CT saturation had to be forced with 4–10× burden. The classic 87T security test is therefore soft. | Phase 1: re-wire the CT measurement so the plant can deliver strong through-faults |
| G2 | One simulated transformer only. Do the results generalise? | Phase 3: a second, different transformer (rating, vector group, CT class); zero-shot and retrained tests |
| G3 | No measured computation time. | Phase 4: measured latency (Python + ONNX Runtime; hand-written ANSI C / C99 as embedded proxy) |
| G4 | The feature-LSTM idea is known; the novelty must be clear. | Phase 5: paper framed around the dual-path supervisory logic and the leak-free evaluation protocol |
| G5 | Claims must be statistically defensible. | Phase 2.5: paired significance tests and confidence intervals |

---

## Phase 0 — Safety and baseline freeze (≈ 0.5 h)

- [ ] **0.1** Create a git tag `thesis-final-2026-10-26` on the current commit, so the thesis version can always be rebuilt.
- [ ] **0.2** Back up `simulations/TransformerWithCTSaturation.slx`, `simulations/live_relay_ai.mat` and `lstm_models/wt_lstm_relay.onnx` as `*_BACKUP_<date>_pre_v4.*`.
- [ ] **0.3** Do all Phase 1–3 model changes in a **copy**: `simulations/TransformerWithCTSaturation_v4.slx`. The thesis model stays untouched.

---

## Phase 1 — Strong external through-faults (plant A) (≈ 1–2 days)

### Background (facts from the 2026-10-21 log)
- Three 0.5 Ω resistors ('Series RLC Branch', 'Branch1', 'Branch2') sit in the LV line between the transformer terminals and the CT / load / External_Fault node. Lowering them to 0.02 Ω made the LV CT secondary collapse to 7.8 %. So they are part of how the LV CTs (CT3, CT4, CT6) are driven.
- Each CT subsystem holds a Saturable Transformer (e.g. LV "CT 92000/5 A, 25 VA", Winding1 `[5*(11/92000) 0.2 0.001]`), a `1ohm` burden branch, a Current Measurement block and two physical ports (Conn1, Conn2).
- The measured effective CT ratios (HV 809.6:1, LV 16,925:1) are **2.024×** the nameplate winding ratios. That is consistent with the CT primary sharing current with another branch instead of carrying the full line current.

### Steps
- [ ] **1.1 Confirm the topology.** In MATLAB, list the physical connections (`get_param(<block>,'PortConnectivity')`, or `find_system` + `LineHandles`) of CT1–CT6 and the three LV series resistors. Write the result to `simulations/ct_topology_v4.txt`.
  - **Hypothesis to confirm:** each CT primary (Conn1–Conn2) is connected **in parallel** with a 0.5 Ω series resistor. The CT then sees only the current share through its own primary impedance. That would explain the 2.024× ratio, the weak through-faults and why lowering R starved the CT.
  - Record what you actually find before changing anything.
- [ ] **1.2 Re-wire the CTs in series** (in the v4 copy only). Each CT primary must carry the **full line current**: put Conn1 → Conn2 in series with the phase conductor, as in the MathWorks "current transformer saturation" example. Then remove the parallel 0.5 Ω resistors, or set them to a negligible series value (≤ 1 mΩ) if the solver needs a branch. Do it for all six CTs, so the HV and LV sides are treated the same.
- [ ] **1.3 Re-calibrate.** Re-run `probe_ct_truth.m` (true line current vs CT secondary) on the v4 model:
  - Expect effective ratios close to nameplate: HV 400:1 and LV 92000/11 ÷ 5 → 1,672.7:1, for 5 A-class secondaries. Record the measured values.
  - Rated CT-secondary current changes accordingly. Expect ≈ 1.88 A at nameplate; **use the measured value**.
  - Update the base in `relay87t.py` (`CT_RATIO_*`, `I_NOM`), the Simulink `Yd1_Compensation` chart, `relay_config.m` (`cfg.I_RATED_SEC`) and the generator noise base. Re-check the plant matrix M on healthy traces. Write the results to `simulations/ct_calibration_v4.txt`.
- [ ] **1.4 Normalise the LSTM input to per unit.** Divide the plant-compensated differential by the rated secondary current **before** feature extraction, in **both** `features12.py` and the Simulink `DWT_Feature_Extraction` path. With the new ratios the current-amp scale changes ~2×, and per-unit inputs are needed anyway for Phase 3. Re-run the feature-parity check (`verify_lstm_feature_parity_plant.m`); max error must be 0.
- [ ] **1.5 Check the plant physics:**
  - External 3-phase solid fault at the LV bus: **5–20 pu** RMS at the CTs, with a realistic X/R (DC time constant 30–100 ms). If it's too low, reduce the external source / feeder impedance. If it's too high, add feeder impedance.
  - LV bus voltage at 100 % load: ≥ 0.95 pu (the old model sagged to 0.35 pu).
  - CT saturation now appears **naturally** on large DC-offset through-faults at **nominal** burden. Record the ratio error vs fault current.
  - Internal-fault, inrush and over-excitation behaviour still plausible. Re-run `hiz_sensitivity_sweep.m` (HiZ bins change with the new base).
  - Write the results to `simulations/plant_v4_checks.txt`.
- [ ] **1.6 Generator v4.** Copy `generate_stress_dataset_v3.m` → `generate_stress_dataset_v4.m` on the v4 model:
  - Keep the scenarios, quotas and stratification of v3.
  - Change the CT-stress scenarios: through-fault current and X/R drive saturation; burden 1–4× nominal (not 4–16×).
  - Add **"External fault, high current, nominal burden"** as an explicit category.
  - Run the self-test (all scenario kinds), then generate **3,040 main + 300 OOD** traces with auto-resume.
  - Run `coverage_report_v3.py` and add a check: **external faults ≥ 5 pu in ≥ 80 % of external traces**.

**Exit criterion Phase 1:** measured through-fault current ≥ 5 pu, LV voltage ≥ 0.95 pu at rated load, parity error 0, coverage report PASS.

---

## Phase 2 — Re-run the full evaluation on the v4 dataset (≈ 1 day, mostly unattended)

Same protocol as `IMPLEMENTATION_PLAN_V3.md` §3: trace-grouped folds, plateau thresholds on validation only, dwell 20, undetectable faults reported separately, OOD scored once. **Do not change the protocol after seeing results.**

- [ ] **2.1** Grouped 5-fold CV × 3 seeds (`train_cv_v3.py`, or a `train_cv_v4.py` that only changes paths) → `runs/<date>_v4_cv5_seeds/summary.txt`.
- [ ] **2.2** Final model + one OOD scoring → `runs/<date>_v4_final/`.
- [ ] **2.3** Baselines on the same folds:
  - unrestrained 87T;
  - **per-phase harmonic-restrained 87T** (`tools/evaluate_harmonic87t.py`);
  - literature models (`benchmark_literature_models.py`).
- [ ] **2.4** Closed loop in Simulink on the v4 model: the 12-case suite + the 50-trace Simulink-vs-Python agreement check (`d4_select_and_mirror.py`).
- [ ] **2.5 Statistics (new):**
  - Paired **McNemar** tests on the same traces: proposed hybrid vs harmonic 87T, and vs the best literature model, for dependability and security separately.
  - **Wilson** 95 % intervals per category.
  - Mean ± sd over the 15 fold-models.
  - Write `runs/<date>_v4_stats/stats.json` + `.txt`.

**Exit criterion Phase 2:** all result files saved; tables generated by script; nothing typed by hand.

---

## Phase 3 — Second transformer (plant B) for generalisation (≈ 2–3 days)

- [ ] **3.1 Build plant B** (`simulations/TransformerB_v4.slx`) from the v4 model, deliberately different from plant A:
  - rating **40 MVA, 132/33 kV, vector group Dyn11** (A is 300 MVA, 230/11 kV, YNd1-type);
  - different source strength and X/R;
  - CTs with 1 A secondaries and their own saturation curves.
  - Implement the matching compensation matrix in the relay chart and in `relay87t.py` (make the plant a parameter, not a constant).
- [ ] **3.2** Calibrate plant B like Phase 1 (`probe_ct_truth`, load knob calibration, HiZ sweep, through-fault check ≥ 5 pu).
- [ ] **3.3** Generate a plant-B set: **1,200 traces** with the same scenario mix and stratification, plus **150 OOD**.
- [ ] **3.4 Three experiments** (report all three, whatever they show):
  1. **Zero-shot:** the plant-A model (per-unit inputs) on plant B, with no retraining. Thresholds stay as tuned on plant A.
  2. **Cross-plant training:** train on A + B with grouped CV over both. Report per plant.
  3. **Leave-one-plant-out:** train on A and test on B, and the reverse.
  
  Also run the harmonic 87T on plant B.
- [ ] **3.5** Closed loop on plant B: the 12-case suite.

**Exit criterion Phase 3:** result files for all three experiments; an honest statement of how much performance transfers.

---

## Phase 4 — Measured computation time (≈ 0.5–1 day)

No relay hardware is available. Measure on what exists and say so.

- [ ] **4.1 Python / ONNX Runtime**, single thread, one window per call (the relay case):
  - feature extraction (DWT + FFT) and inference timed **separately**;
  - 100 warm-up calls, then ≥ 10,000 timed calls;
  - report median, p99 and max;
  - record CPU model, clock, OS and library versions.
  
  Script `tools/measure_latency.py` → `runs/<date>_latency/latency.json`.
- [x] **4.2 Hand-written ANSI C / C99 relay pipeline** (`tools/relay_c/`, generated by `tools/build_and_run_c_benchmark.py`): full feature extraction + 2-layer LSTM + attention + classifier in self-contained C99, no external libraries. Compiled with MinGW-w64 GCC 16.1.0 (-O3 -mavx2 -mfma). Timed with Windows QueryPerformanceCounter (100 warm-up + 10,000 timed calls). Numerical parity vs PyTorch: prob diff 1.94e-05, feature diff 4.81e-07 (PASS). **Note:** this is NOT MATLAB Coder / Embedded Coder output; it is hand-written C whose structure mirrors the Python pipeline and serves as an embedded-execution proxy. Describe it as such in the paper.
- [x] **4.3** Report the **FLOP count** (already ≈ 1.71 MFLOPs per inference) and the measured times, and compare with the 625 µs sample period at 1,600 Hz. **Never estimate a time for hardware you didn't run on.** If you mention a DSP/ARM figure, label it as an estimate from FLOPs and cite the device's datasheet.

---

## Phase 5 — Paper (≈ 1 week)

- [ ] **5.1 Novelty statement** (first paragraph of the paper and the cover letter):
  1. A **dual-path supervisory relay**: 87T-gated AI confirmation **plus** a persistence-filtered AI-alone path for sub-pickup faults, with the high-set kept outside the AI.
  2. A **leak-free evaluation protocol**: trace-grouped CV, onset-based labels, validation-only plateau thresholds, OOD set scored once, undetectable faults reported separately.
  3. **Fair baselines:** a per-phase harmonic-restrained 87T and five literature models on identical folds, with paired statistics.
  4. **Generalisation** to a second transformer, and Simulink closed-loop parity.
  
  Do **not** claim the DWT + LSTM feature pipeline itself as new.
- [ ] **5.2 Structure** (journal limit ~10–12 pages, double column):
  - Introduction;
  - Related work (incl. BDWT / Clarke-wavelet as discussion);
  - Plants and dataset (v4 coverage table);
  - Method (features, network, dual-path logic);
  - Evaluation protocol;
  - Results (ablation, baselines + McNemar, per-category, OOD, plant B, latency, closed loop);
  - Limitations (simulation only, no HIL, two plants, terminal faults only);
  - Conclusion.
- [ ] **5.3** Every number comes from a result file through `generate_thesis_tables_and_macros.py` (extend it for the paper). No hand-typed numbers.
- [ ] **5.4** Data and code availability statement. Consider releasing the dataset generator and the evaluation code (journals value this).
- [ ] **5.5** Before submission: a supervisor or a protection engineer reads it. AI-generated reviews are not a substitute.
- [ ] **5.6 Optional, quicker feedback:** a short conference version (IEEE PES General Meeting / IET DPSP) with the Phase 1–2 results.

---

## Rules for the Claude Code session (read before every step)

1. **Numbers only from saved files.** Every number in the plan log, tables or paper must come from a file under `runs/`, `simulations/` or `datasets/` written by a script. If a number has no source file, it does not exist. Never type a result into `rebuild_thesis_manuscript.py`, the table generator or a `.tex` file by hand.
2. **Protocol is fixed in advance** (`IMPLEMENTATION_PLAN_V3.md` §3, extended by Phase 2.5 here). Do not tune on test or OOD data. Do not change thresholds or rules after seeing test results. If something must change, log why **before** re-running.
3. **Report failures as failures.** A FAIL in a result file stays a FAIL in the paper. A result that is worse than expected is a finding.
4. **Model safety.** Change only the `_v4` copies. Back up before every `.slx` change. Never save an `.slx` with a test configuration baked in: reload the pristine file, add only the intended changes, save, reload and assert. One MATLAB at a time. Use auto-resume for long generation (heap crash 0xc0000374). Keep RAM < 4 GB.
5. **Verify before ticking.** After each step, re-open the output file and check the numbers you are about to log. Then tick the box here and add a dated entry to `IMPLEMENTATION_PLAN.md`, using the **real date and time from the system clock**.
6. **Wording.** Use measured comparisons ("+14.2 pt dependability, 11 vs 38 false trips"), not adjectives ("decisively", "superior", "100 % ready"). Cite a source for every standard or vendor claim, or leave it out.
7. **Git.** Commit after each phase, with a factual message. Leave no trace of Claude: no Claude author, no Co-Authored-By or Claude-Session lines, no mention in the message. Do not push; the author pushes.

---

## Order, effort and checkpoints

| Phase | Effort | Unattended part | Checkpoint |
|---|---|---|---|
| 0 Safety | 0.5 h | — | tag + backups exist |
| 1 Strong through-faults | 1–2 days | ~5 h generation | `plant_v4_checks.txt` PASS |
| 2 Re-evaluation (A) | 1 day | ~4 h CV | `v4_cv5_seeds/summary.txt`, stats |
| 3 Plant B | 2–3 days | ~2 h generation | three transfer experiments saved |
| 4 Latency | 0.5–1 day | — | `latency.json` |
| 5 Paper | ~1 week | — | supervisor read-through |

**Total: about 2–3 weeks of work.** Phases 3 and 4 can run in parallel with Phase 2's unattended training.

---

## Review of V4 progress (review received 2026-10-28; items numbered V1-V7 here - the review lists three must-fix and four should-fix points)

Status key: [x] fixed and verified from a re-run output file; [ ] open. Numbers below are from the files named in each item.

- [x] **V1. Significance test against the harmonic 87T paired the wrong traces.** `tools/compute_v4_statistics.py` paired the CV rows (fold order) with the harmonic rows (trace order) by position. Fixed: pairing by trace identity (`trace` = `trace_idx`),
  with assertions that scenario and label agree for every pair; the 87T-alone / LSTM-alone lists are asserted to be the same traces in the same order. Re-run: harmonic 87T is now **81.67 % dependability / 91.67 % security** (its own summary: same), the hybrid wins
  212 vs 1 (dependability) and 151 vs 9 (security) discordant traces, McNemar p = 3.3e-62 and 2.2e-34. The previous p-values (9.8e-205, 1.2e-185) were invalid. `runs/20261027_v4_stats/stats.json|txt` and `latex_source/latex/table_6_3_statistical_tests.tex` regenerated. No other file cited the wrong numbers.
- [ ] **V2. Plant B's conventional 87T is mis-calibrated; the 87T gate is almost always open, so "Proposed" = "LSTM alone" on plant B.** Verified in `runs/20261027_v4_plant_b_zeroshot/zero_shot_summary.json`: Proposed and LSTM alone are identical in every metric (83.234 % / 93.528 %, 83 missed, 40 false trips);
  87T alone false-trips 519 of 618 healthy traces. Cause (from the plant B dataset, 119 Normal traces): the 87T votes on 0 % of traces with burden multiple 1-1.5x, 11 % at 1.5-2x, 33 % at 2-2.5x, 48 % at 2.5-3x (burden = multiple x 2.5 ohm), and on 0 % of 10-60 % load, 20 % at 60-90 %, 77 % at 90-111 % load:
  the CT saturates in steady state at high burden and high load. The dataset's burden multiplier (1-3x) is applied on top of a nominal 2.5 ohm that is already close to the CT knee (plant A: nominal 1 ohm). Consequence: every plant B "hybrid" number (zero-shot, cross-plant, leave-one-out) is a LSTM-alone number and must not be reported as hybrid.
  **Open: plant B CT design must be corrected (see V3), the plant B dataset regenerated and the three transfer experiments re-run.**
- [ ] **V3. Plant B physics check was self-contradicting and wrongly scored PASS.** Diagnosis, verified: `simulations/check_plant_b_physics.m` indexed the V-I blocks' "true current" (logged at the solver rate) with indices built on the 1600 Hz relay time base, so the "true LV current" came from the pre-fault interval (about 1 pu load), not the fault.
  Fixed (each signal on its own time base; RMS and peak on separate labelled lines; the through-fault criterion applied to the TRUE current). Re-run `simulations/plant_b_checks.txt` (backup of the old report: `plant_b_checks_BACKUP_20261028_pre_timebase_fix.txt`): **true through-fault current 37.6 pu RMS (HV 6.58 kA, LV 26.3 kA) -> FAIL against the intended 5-20 pu; the CT secondaries read only 5.0 pu**,
  i.e. the CTs under-read by about 7.5x (effective ratio about 6000:1 against 809:1): heavy saturation, not a wiring error. The earlier "5 pu through-fault PASS" was the saturated CT output. Reading (inference, not yet tested): the plant is too stiff (feeder / source impedance too low) AND the CT too weak. The old report also contained a "14.47 pu" line the committed script cannot print, so it was not produced by the committed script.
  **Open: re-design plant B (raise feeder / source impedance so the TRUE through-fault is 5-20 pu, give the CTs a knee that keeps them linear to about 1.5 pu load and lets them saturate only on large DC-offset through-faults), re-calibrate, re-check, regenerate.** The reported plant B closed-loop miss of a solid internal fault has not been investigated yet and must be re-run after the redesign.
- [x] **V4. Through-fault target wording (RMS vs peak) and what was measured.** Plant A check (`check_plant_v4_physics.m`) measured the CT-SECONDARY RMS (6.41 pu), derived the "true" current from the assumed CT ratio, and accepted up to 25 pu while printing "5-20 pu". Independent measurement with the V-I blocks
  (`simulations/probe_plant_a_truth_v4.m` -> `simulations/plant_v4_truth_check.txt`): **true through-fault 23.9 pu RMS** (HV 18.0 kA, LV 376 kA), CT secondary 6.4 pu RMS, CT secondary / true = 0.27 (saturation, crest factor about 3); true LV voltage at 100 % load 0.9915 pu (the CT-based estimate had said 1.0497 pu).
  So the plan's 1.5 criterion "5-20 pu RMS" is met by the CT secondary reading but NOT by the true current (23.9 pu; inside the silently widened 25 pu limit). Papers/thesis must say which of the two is quoted. The plant B script now applies the criterion to the true current (V3).
- [x] **V5. Inrush "about 1 pu" in the new model.** The check-4 probe of `check_plant_v4_physics.m` kept the LV breaker closed with the full load, so its 0.99 pu "crest" is the load current's own peak, not inrush (its own acceptance rule, >= 2.0 pu, was not applied). Inrush in the datasets is real:
  `simulations/inrush_check_from_datasets.txt` (script `tools/check_inrush_from_datasets.py`): peak HV CT current in the 100 ms after energisation, in rated-peak units: plant A v4 no-load median 2.80 (p10 2.36, p90 3.36, max 3.96), loaded 2.65; plant B no-load median 2.03, loaded 2.15; Normal traces about 0.6. The probe in check 4 is withdrawn; cite the dataset-based numbers.
- [x] **V6. "C latency" is not MATLAB Coder output.** The C source is hand-written (Python string templates emitted by `tools/build_and_run_c_benchmark.py`), compiled with MinGW-w64 GCC on the development PC and parity-tested against PyTorch. Corrected in the script docstring (which also wrongly named MSVC) and report headers, and in the note of Table 6.6 (`tools/build_publication_tables.py`).
  The existing result files keep their old header text until the benchmark is re-run (the measured numbers are unchanged).
- [x] **V7. Log back-dating, missing overnight entries, commits.** Written below as a reconciliation using file modification times from the system clock (not the log's own times). Commits: see the log entry.

Open decisions for the author: V2/V3 mean plant B has to be rebuilt and the transfer experiments re-run; the results may be worse than the current ones. Until then the plant B / transfer numbers must not appear in a paper as "hybrid" results.

---

## Re-check of the V4 fixes — 2026-10-28 14:45

**Verified:**
- V1 McNemar now pairs by trace: harmonic 87T 81.67 / 91.67 %, p = 3.3e-62 / 2.2e-34, matching its own summary.
- V3 diagnosis (time-base bug in the plant-B check).
- V4 independent plant-A truth check.
- V5 inrush from the datasets (plant A median 2.8, plant B 2.0 × rated peak).
- V6 wording.
- Commit at 10:01.

Good, honest work. V2 and V3 correctly remain open.

### V8. Plant A has the same physics problem as plant B, only milder — author decision needed  ⚠️
`simulations/plant_v4_truth_check.txt`:
- A solid external 3-phase fault drives a **true 23.9 pu RMS** through-current.
- The CT secondaries read only **0.27×** of it (6.4 pu): every solid external fault saturates the CTs heavily at nominal burden.

Two consequences a protection reviewer will raise:
1. **Through-fault level.** A through-fault is limited mainly by the transformer's own leakage impedance: I ≈ 1 / Z_t pu. 23.9 pu implies Z_t ≈ 4 %. Large power transformers (300 MVA, 230 kV) typically have Z_t of roughly 10–15 %, which gives about 7–10 pu. Check the model's leakage R/X (the winding parameters in pu) against that.
2. **CT sizing.** Protection CTs are normally chosen (IEEE C37.110 practice) so they do **not** saturate on the maximum **symmetrical** through-fault at rated burden. Saturation should come only from DC offset, remanence or high burden. With today's CTs, "External solid" and "External CT-sat" are both heavily saturated. That blurs the categories and makes the conventional 87T baselines look worse than a well-designed relay would (unrestrained 87T: External solid 14 % correct).

**Options (author decides):**
- [ ] **(a) Recommended for a journal:** fix both plants together.
  - Set realistic transformer impedance (plant A ~12 %, plant B ~10 %) and source/feeder impedance, so the TRUE through-fault is about 7–15 pu.
  - Size the CTs so they stay linear for the maximum symmetrical through-fault at nominal burden, saturating only with DC offset / extra burden in the CT-stress scenarios.
  - Re-calibrate, regenerate plant A (≈ 5 h) and plant B (≈ 2 h), then re-run CV × 3 seeds, final + OOD, baselines, statistics, the transfer experiments and both closed loops (≈ 1 day of compute).
- [ ] **(b) Faster:** keep plant A as is. Fix only plant B (V2/V3), with plant B's CTs sized correctly. State plant A's CT undersizing and 24 pu through-fault as limitations. Report external-fault results as "with CT saturation".

Either way, the paper must say which current is quoted (TRUE or CT secondary).

### Still open from V1–V7
- [ ] V2 / V3: plant B redesign, regeneration, re-run of zero-shot / cross-plant / leave-one-out and the plant-B closed loop (including the missed solid internal fault).
- [ ] OOD block-3 label: `runs/20261027_v4_final/report_ood.txt` says "CT burden 4–8×"; the v4 harmonic summary says "12–16×" for the same block. Take the range from the generator and fix both.
- [ ] `runs/20261027_latency/latency_c.json|txt` still carry the old header (re-run or patch the header; the numbers stand).
