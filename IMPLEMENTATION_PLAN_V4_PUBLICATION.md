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
| G3 | No measured computation time. | Phase 4: measured latency (Python, ONNX Runtime, MATLAB generated C code) |
| G4 | The feature-LSTM idea is known; the novelty must be clear. | Phase 5: paper framed around the dual-path supervisory logic and the leak-free evaluation protocol |
| G5 | Claims must be statistically defensible. | Phase 2.5: paired significance tests and confidence intervals |

---

## Phase 0 — Safety and baseline freeze (≈ 0.5 h)

- [x] **0.1** Create a git tag `thesis-final-2026-10-26` on the current commit, so the thesis version can always be rebuilt.
- [x] **0.2** Back up `simulations/TransformerWithCTSaturation.slx`, `simulations/live_relay_ai.mat` and `lstm_models/wt_lstm_relay.onnx` as `*_BACKUP_<date>_pre_v4.*`.
- [x] **0.3** Do all Phase 1–3 model changes in a **copy**: `simulations/TransformerWithCTSaturation_v4.slx`. The thesis model stays untouched.

---

## Phase 1 — Strong external through-faults (plant A) (≈ 1–2 days)

### Background (facts from the 2026-10-21 log)
- Three 0.5 Ω resistors ('Series RLC Branch', 'Branch1', 'Branch2') sit in the LV line between the transformer terminals and the CT / load / External_Fault node. Lowering them to 0.02 Ω made the LV CT secondary collapse to 7.8 %. So they are part of how the LV CTs (CT3, CT4, CT6) are driven.
- Each CT subsystem holds a Saturable Transformer (e.g. LV "CT 92000/5 A, 25 VA", Winding1 `[5*(11/92000) 0.2 0.001]`), a `1ohm` burden branch, a Current Measurement block and two physical ports (Conn1, Conn2).
- The measured effective CT ratios (HV 809.6:1, LV 16,925:1) are **2.024×** the nameplate winding ratios. That is consistent with the CT primary sharing current with another branch instead of carrying the full line current.

### Steps
- [x] **1.1 Confirm the topology.** In MATLAB, list the physical connections (`get_param(<block>,'PortConnectivity')`, or `find_system` + `LineHandles`) of CT1–CT6 and the three LV series resistors. Write the result to `simulations/ct_topology_v4.txt`.
  - **Hypothesis to confirm:** each CT primary (Conn1–Conn2) is connected **in parallel** with a 0.5 Ω series resistor. The CT then sees only the current share through its own primary impedance. That would explain the 2.024× ratio, the weak through-faults and why lowering R starved the CT.
  - Record what you actually find before changing anything.
- [x] **1.2 Re-wire the CTs in series** (in the v4 copy only). Each CT primary must carry the **full line current**: put Conn1 → Conn2 in series with the phase conductor, as in the MathWorks "current transformer saturation" example. Then remove the parallel 0.5 Ω resistors, or set them to a negligible series value (≤ 1 mΩ) if the solver needs a branch. Do it for all six CTs, so the HV and LV sides are treated the same.
- [x] **1.3 Re-calibrate.** Re-run `probe_ct_truth.m` (true line current vs CT secondary) on the v4 model:
  - Expect effective ratios close to nameplate: HV 400:1 and LV 92000/11 ÷ 5 → 1,672.7:1, for 5 A-class secondaries. Record the measured values.
  - Rated CT-secondary current changes accordingly. Expect ≈ 1.88 A at nameplate; **use the measured value**.
  - Update the base in `relay87t.py` (`CT_RATIO_*`, `I_NOM`), the Simulink `Yd1_Compensation` chart, `relay_config.m` (`cfg.I_RATED_SEC`) and the generator noise base. Re-check the plant matrix M on healthy traces. Write the results to `simulations/ct_calibration_v4.txt`.
- [x] **1.4 Normalise the LSTM input to per unit.** Divide the plant-compensated differential by the rated secondary current **before** feature extraction, in **both** `features12.py` and the Simulink `DWT_Feature_Extraction` path. With the new ratios the current-amp scale changes ~2×, and per-unit inputs are needed anyway for Phase 3. Re-run the feature-parity check (`verify_lstm_feature_parity_plant.m`); max error must be 0.
- [x] **1.5 Check the plant physics:**
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
- [ ] **4.2 Generated C code:** use MATLAB Coder / Embedded Coder (both installed) to generate C for the feature extraction + LSTM (Deep Learning Toolbox code generation, generic C, no external libraries). Time it the same way in a small C harness. This is the closest proxy to embedded execution.
- [ ] **4.3** Report the **FLOP count** (already ≈ 1.71 MFLOPs per inference) and the measured times, and compare with the 625 µs sample period at 1,600 Hz. **Never estimate a time for hardware you didn't run on.** If you mention a DSP/ARM figure, label it as an estimate from FLOPs and cite the device's datasheet.

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
