# Implementation Plan — Honest, Leak-Free LSTM Evaluation (12-feature, W=32)

**Started:** 2026-10-18 · **Working on:** copies only — no existing file is overwritten.
**New outputs go to:** `runs/20261018_trace_split/` and new scripts with clear names.

---

## Why (findings from the 2026-10-18 review)

1. **Only saved closed-loop result is 2/4 PASS** (`simulations/test_hybrid_relay_results.txt`, Aug 8):
   Inrush → TRIP (fail), External → TRIP (fail). The 4/4 table in `walkthrough.md` matches no saved output.
2. **LSTM is not driving decisions:** internal fault gets the *lowest* probability (0.56 / 0.64);
   the 17.5 ms trip comes from the high-set overcurrent bypass.
3. **Data leakage:** `train_lstm_local.py` cuts each trace into overlapping 32-step windows
   (stride 16) and splits *windows* randomly, so the same trace is in train and test.
4. **Wrong window labels:** `window.max() > 0.05` is almost always true (load energy, harmonic
   ratio), so healthy pre-fault windows of fault traces are labelled TRIP.
5. **Stress table uses training data:** `evaluate_all_stress_categories.py` scores the old
   9-feature 0722 model on its own 80 training traces.
6. **Model mix-up:** `run_closed_loop_benchmark.bat` exports the 0723 checkpoint, not 0808.
7. (To check) the three `StressTestDataset_POSTCALIB_*` files have identical sizes — possible
   duplicate traces across files, which would add more leakage.

---

## Plan

| # | Step | Status |
|---|---|---|
| 1 | Load source stress datasets; check for duplicate traces across files | ✅ done |
| 2 | Rebuild the 12 features per trace in Python **with metadata** (scenario, inception time); verify bit-level parity against MATLAB `LSTM_Features_Combined_20260807_193459.mat` | ✅ done |
| 3 | **Split by trace** (deduplicated) → train/val/test; **label windows by fault inception** (healthy before, TRIP after) | ✅ done |
| 4 | Retrain 12-feature W=32 model; tune threshold on **validation traces** only | ✅ done |
| 5 | Evaluate: window metrics **and** a streaming relay simulation per test trace (dependability, security, operate time, per scenario) | ✅ done |
| 6 | One deployed checkpoint used by export, `.bat`, and evaluation | ✅ done (`run_closed_loop_benchmark_v2.bat`) |
| 7 | You (MATLAB): re-run closed-loop `test_hybrid_relay.m` with the new model; report only saved results | ⏳ (needs MATLAB) |

---

## Progress log

- **2026-10-18 11:53** — Plan created. Staging `StressTestDataset_POSTCALIB_20260723_014046.mat` to inspect structure.
- **2026-10-18 12:10** — **Step 1 done. Data-generation findings (serious):**
  - The 3 source files (`POSTCALIB_20260723_014046`, `_20260730_072010`, `_CHECKPOINT`) contain the
    **same 600 traces**. `extract_12_features.m` loads all three, so every trace appears **3×**.
  - Within those 600 traces only **528 are unique**. All **168 "Normal" traces are byte-identical**
    (one waveform, despite different `noiseLevel` metadata). 30 `Internal_HiZ_BG` + 9 `Internal_BG`
    traces are one identical waveform. ⇒ scenario parameters (noise, Rf, timing) were **not applied**
    in many runs.
  - **`inceptionTime` metadata is wrong for internal faults:** in every internal trace the current is
    **zero until ~0.781 s**, then the fault appears (metadata says 0.30–0.75 s). External faults do
    match the metadata. ⇒ internal cases are effectively "energise onto a fault at 0.78 s".
  - Fault onset is therefore measured **from the waveform** (`detect_fault_onset`, cycle-difference
    detector on `Ip − Is`), visually verified on internal, HiZ, evolving and fault-in-inrush traces.
  - Unique traces: **330 trip / 198 no-trip**.
  - Script: `lstm_models/stress_dataset.py` (loader + fingerprints + onset detector).
- **Recommended later (MATLAB, by you):** regenerate the stress dataset so noise, Rf, inception time
  and pre-fault energisation are actually applied, and vary Normal loading. This is the single
  biggest improvement available; the steps below make the evaluation honest on the data you have.

---

- **2026-10-18 12:35** — **Steps 2–3 done.**
  - `lstm_models/features12.py` = Python port of `extract_12_features.m`. Parity vs the MATLAB file:
    **max abs error 1.9e-9** (float32 rounding) → identical features.
  - `lstm_models/train_trace_split.py`: deduplicated **528 unique traces**, split by trace
    **368 train / 79 val / 81 test** (stratified by category; the single Normal waveform is held out in test).
    Window labels: TRIP only when the window holds ≥ 8 samples (5 ms) after the measured onset.
  - **Baseline — existing Aug 8 model on these test traces (relay simulation, 5 ms dwell):**
    dependability 94.0 %, security 96.8 %, 3 trips *before* fault onset, 1 false trip, needs threshold **0.98**.
    Still optimistic: that model trained on these same traces (window-level leakage).
- **2026-10-18 12:40** — **Two more causes of the 2/4 closed-loop result found in the local `.slx`:**
  1. LSTM input is still the **Yd1-compensated per-unit `I_diff`**; training used **raw `Ip − Is`**.
     Fix: `simulations/fix_lstm_input_raw_idiff.m` (adds `I_diff_LSTM = Mux − Mux1`, 87T path untouched),
     check: `simulations/verify_lstm_feature_parity.m` (must print PASS).
  2. Decision chart hard-codes **`AI_Threshold = 0.50`**; the models need ~0.9+. With 0.5, the 87T vote plus
     a mid-range LSTM score trips on inrush/external. Fix: `simulations/set_ai_threshold.m` reads the tuned
     value from `runs/20261018_trace_split/decision_threshold.txt`.
  - `repair_hybrid_relay_for_lstm_verification.m` does not touch the LSTM input wiring, so the fix persists.
  - New one-click runner: `run_closed_loop_benchmark_v2.bat` (one `DEPLOYED_RUN` for every step).
- **2026-10-18 13:05** — **Steps 4–6 done. Leak-free model: `runs/20261018_trace_split/`**
  - Same architecture (12 features, W=32, 2×64 LSTM, unidirectional). 17 epochs on CPU, val window AUC 0.9987.
  - **Test, relay simulation (81 unseen traces: 50 faults, 31 healthy), threshold 0.99, 5 ms dwell:**
    dependability **100 %** (0 missed, 0 trips before fault), security **96.8 %** (1 false trip: an `External_BG`),
    operate time median **11.9 ms**, p90 35.6 ms, max 36.3 ms (100 % within 2 cycles, 56 % within 1 cycle).
    Internal median 9.4 ms; high-impedance internal median 35.6 ms.
  - **Validation (79 traces):** 100 % dependability, **90 % security** (3 of 30 healthy false-trip: inrush no-load
    and external). ⇒ security on unseen data is realistically ~90–97 %, not 100 %.
  - **Trade-off (test_tradeoff_dwell_threshold.json):** raising the threshold to ≥ 0.995 gives 100 % security
    but misses ~22–24 % of faults (high-impedance and low-level internal). Chosen: **dependability-first, 0.99**
    (`decision_threshold.txt`). Present the curve in the thesis rather than one cherry-picked point.
  - Exported with your own `lstm_models/export_onnx.py`: ONNX/PyTorch error 3.9e-8, real input **[1, 32, 12]**
    (the script's printout says "9"; that print line is stale, the model is 12-feature).
  - Caveat: internal-fault traces energise from zero at ~0.78 s, which is easier than a fault on an energised
    transformer, so operate times are optimistic until the dataset is regenerated.

- **2026-10-18 17:20** — All files written to the project and **re-verified**: running the delivered
  `train_trace_split.py --evaluate-only` on the delivered checkpoint reproduces the numbers above exactly.
  Nothing existing was overwritten; the `.bat` backs up the `.slx` and `live_relay_ai.mat` before changing them.

- **2026-10-18 18:40** — First `.bat` run: steps 1–2 OK (ONNX error 5.8e-8; "[1, 32, 9]" is only a stale
  print label, the model is 12-feature). Step 3 failed in `fix_lstm_input_raw_idiff.m` (PortConnectivity is a
  struct array). Model was **not** saved. Fixed, plus a second bug found on review: deleting the old wire by
  line handle would also delete its branches (87T RMS path). Now only that one connection is removed, and the
  script asserts the 87T path (`Abs2` ← `I_diff`) is intact. → Re-run the `.bat`.

- **2026-10-18 18:45** — Second `.bat` run:
  - **Feature parity: PASS, max error exactly 0** (Normal and Internal A-G). The relay now computes the
    training features bit-for-bit. ✅ Main root cause fixed.
  - Closed loop **3/4** (Normal, Inrush, External BLOCK ✅; Internal A-G **BLOCK ✗**).
  - LSTM outputs were only **0.5000 / 0.7311** = sigmoid(0) / sigmoid(1). **Double-sigmoid bug** in
    `simulations/lstm_predict_wrapper.m`: the ONNX already ends in `Sigmoid` (checked in the graph), and the
    wrapper applied sigmoid again → outputs squeezed into 0.50–0.73, so the 0.99 threshold could never be met.
    This bug also affected all earlier closed-loop runs (their 0.64–0.73 "probabilities").
  - Fixed: wrapper now uses the network output directly. Original kept as
    `simulations/lstm_predict_wrapper_BACKUP_20261018.m`. → Re-run the `.bat`.

- **2026-10-19 15:10** — Third `.bat` run (after the double-sigmoid fix): parity PASS (error 0); real
  probabilities now (Normal 0.0000, External 0.0001, Internal 1.0000) but **Inrush TRIP** (3/4).
  - Logged raw scores: inrush is above 0.99 for only **9 samples (5.6 ms)** at ~29 ms after energisation;
    the internal fault stays above for 1,631 samples. A short spike, not a decision.
  - **The Simulink decision chart had no persistence timer:** one sample of 87T vote AND score ≥ threshold
    tripped, and the S-R latch held it. The Python evaluation assumed 8 samples → **mismatch** (now fixed).
  - **Correction of my earlier note:** the old tuning grid stopped at 0.99, so the documented rule
    "0 false trips on validation" was never met (validation had 3 false trips at 0.99). Rule now stated and
    implemented as: on validation, max dependability → max security → fastest median operate time.
  - Settings that tie on validation (100 % dependability, 93.3 % security) differ only in speed vs margin.
    Closed-loop inrush spike length vs threshold: 8 @0.993, 9 @0.99, 10 @0.98, 12 @0.95, 14 @0.90.
    **Chosen: dwell 20 samples (12.5 ms), threshold 0.95** (rule picks 0.95 for dwell 20 automatically):
    8-sample margin over the spike. ⚠ The closed-loop inrush case informed this tie-break, so the 4-case
    benchmark is **not an independent test of the dwell choice**; the independent evidence is the test traces.
  - **Leak-free test (81 traces) with dwell 20 / 0.95:** dependability 100 %, 0 pre-fault trips, security 96.8 %
    (1 false trip, External_BG), operate median **16.2 ms**, max 26.3 ms, 78 % within 1 cycle, 100 % within 2.
    Validation: 100 % / 93.3 %. Files: `runs/20261018_trace_split/report_deployed.json`, `decision_threshold.txt` (0.95),
    `decision_dwell.txt` (20). (`report_trained.json` is the earlier dwell-8 / 0.99 evaluation, kept for history.)
  - Implemented in Simulink via `lstm_predict_wrapper.m` (confirmed score = min of last `cfg.AI_DWELL` raw outputs;
    raw values still logged) and `relay_config.m` (`cfg.AI_DWELL = 20`). Backups: `relay_config_BACKUP_20261019.m`,
    `lstm_predict_wrapper_BACKUP_20261018.m`.
  - **Replay of the logged Simulink scores with the new rule predicts 4/4:** inrush max confirmed 0.80 (veto holds);
    internal A-G confirmed **43 ms** after the fault. ⚠ Slower than the 16 ms test median because this benchmark
    faults an *energised* transformer, a case missing from the training data → dataset regeneration is priority #1.

- **2026-10-19 16:40** — ✅ **Closed-loop benchmark 4/4 PASS** (`simulations/test_hybrid_relay_results.txt/.mat`,
  run 16:35). Feature parity PASS (error 0). Exactly as the replay predicted:
  Normal BLOCK (max 0.0000) · Inrush BLOCK (confirmed max 0.8036; raw spike 0.9996 vetoed by the 12.5 ms timer) ·
  Internal A-G TRIP at 0.0931 s = **43.1 ms after the fault** (AI-confirmed; high-set did not fire first) ·
  External 3Φ BLOCK (max 0.0000).
  - Honest framing for the thesis: 4 hand-picked cases, one of which (inrush) informed the timer tie-break; the
    statistical evidence is the 81-trace leak-free test. The 43 ms trip (> 2 cycles) on an energised transformer
    is a known gap caused by the training data (internal faults only from de-energised state).
  - `walkthrough.md` still holds the old, unsupported numbers (4/4 at 17.5 ms, 95.45 % accuracy). Do not use them.

- **2026-10-19 18:50** — **Stress generator diagnosis** (`simulations/generate_stress_dataset_headless.m` + model XML):
  1. **Noise never applied:** `injectNoiseCT` is an empty placeholder; noise block has a fixed seed (23341) →
     all 168 Normal traces identical.
  2. **Noise cancels in I_diff anyway:** ONE Band-Limited White Noise source feeds all six `Noise_Gain_*`
     (same signal on primary and secondary) → it cancels exactly in `Ip − Is`. The model has never seen noise.
  3. **Breaker state leaks between samples:** breaker set_param calls are inside silent `try/catch`. Inrush
     samples leave the HV breaker closing at up to 0.80 s; a failed reset makes later internal faults
     "energise at ~0.78 s" — exactly the 0.781–0.787 s onsets in the data.
  4. **Hidden always-on faults:** `Internal_Fault2` (B-G) and `Internal_Fault3` (C) are switched on at 0.05 s
     by `Step_Evolve2/3` and never reset. On the delta winding B-G alone draws no current, but combined with
     Fault1 it changes the fault type (e.g. "Internal_AG" → A-B-G).
  5. **Physics:** internal faults sit on the 11 kV **delta** winding (ungrounded, `Winding2Connection = Delta (D1)`),
     so single-line-to-ground faults there draw ~no current. "Internal_BG"/"Internal_HiZ_BG" traces are
     therefore energisation transients **labelled TRIP** → likely cause of the model's inrush false trips.
  6. Load fixed at 10 MW (~3 % of the 300 MVA rating); CT mismatch only written to metadata, never applied;
     load block name contains a newline (`Three-Phase⏎Series RLC Load `).
  → Writing `generate_stress_dataset_v2.m` (runtime-only changes, model never saved) + `audit_stress_dataset.py`.

- **2026-10-19 20:10** — ✅ **Generator v2 delivered: `simulations/generate_stress_dataset_v2.m`.**
  (The inspector was named `lstm_models/check_stress_dataset_v2.py` instead of `audit_stress_dataset.py`.)
  - Additional root causes confirmed in generation order on the July traces:
    the **breaker bug** is `SwitchTimes '[]'` (fails; `test_hybrid_relay.m` uses `'[10 11]'`, which works) — after the
    last `Inrush_Loaded` sample every Internal and early External trace was energised at **0.7812 s**;
    the noise σ was ~0.002 A; the **quantizer step is 0.01 A** (≈0.5 % of rated HV / 1.2 % LV secondary);
    HV winding is **ungrounded Y**, LV **delta** (confirmed in model XML; all 39 'B-G' traces identical whatever Rf).
  - **v2 design:** every `set_param` read back (mismatch stops the run, no silent catch); breakers disconnected from the
    relay; all 4 fault blocks and steps reset each sample; faults on an **energised, loaded** transformer at 0.30–0.75 s;
    load 5–120 % of 300 MVA, pf 0.85–1.0, source 0.95–1.05 pu, random source phase (point-on-wave);
    **6 independent noise channels** (Demux inserted in memory), 0.05–1 % of rated (1–3 % stress), CT mismatch ±2 % (±5 %);
    scenarios rebalanced to **phase-phase / 3-phase** faults (single-line-to-ground on the delta side kept rare);
    HiZ 1–25 Ω phase-phase; evolving A-B → A-B-C; switch-onto-fault, fault-in-inrush, external-in-inrush, CT stress.
    Default 1200 samples ≈ 480 trip / 720 no-trip.
  - **Per-sample verification:** energisation time, event time (±12.5 ms), event visibility, noise level vs expected
    (incl. quantisation), duplicate waveform → `checkPassed`; logs the relay's compensated differential → `faultDiffPu`.
    Reproducible (`rng(seed + k)`), resumable, **ONE output file**, `.slx` never saved (closed with `close_system(model, 0)`).
  - Verification here: MISS_HIT lint clean (6 MATLAB bugs fixed in review, e.g. anonymous functions calling no-output
    `setp`, `struct()` with cell values, eval-based `str2num('open')`, `cd` shadowing). Checks validated in Python on the
    July traces (inrush energisation found within 2.5 ms; weak external faults reported "not visible", not as errors).
    **Not run in MATLAB yet → run the self-test first.**
  - Python: `stress_dataset.py` reads all v2 fields; `train_trace_split.py` uses the verified fault time for labels,
    skips failed-check samples and internal faults below `--min-fault-pu` (0.05 pu; counted in the report), spreads Normal
    traces over train/val/test. Regression on July data: identical split and results. Mock v2 file: end-to-end OK.
  - ⚠ Open design question: LSTM features use **raw `Ip − Is`** (no Yd1 compensation). With load now 5–120 %, the healthy
    raw "differential" grows with load. If security suffers, switch features to the compensated differential
    (v2 already logs it as `I_diff_comp`).

- **2026-10-19 20:30** — Self-test run 1 (20:16) stopped at the first step, **as designed**: the read-back caught
  `Three-Phase Breaker: Failed to evaluate mask initialization commands — Index exceeds the number of array elements`.
  This is the old generator's hidden bug made visible: with `External = off` the breaker mask reads `SwitchTimes(1)`,
  and the model's `SwitchTimes` is `[]`. Fix: switch `External` off **in the same call** as `SwitchTimes '[10 11]'`;
  likewise the noise source's 6-element `Cov` is now set together with a 6-element `seed`. → Re-run the self-test.

- **2026-10-19 20:45** — Self-test run 3 (20:39): breaker fix confirmed (all 7 scenarios configured and read back OK),
  but every simulation failed to compile: "underspecified signal dimensions". Cause: commenting out the DWT and LSTM
  blocks left downstream signal sizes undefined. Fix: nothing is commented out any more; the generator sets
  `setappdata(0,'HybridRelaySkipLSTM',true)` and `lstm_predict_wrapper.m` returns 0 immediately while it is set
  (flag removed on exit). Also: the two `run_stress_v2_*.bat` files now end with `pause` so the window stays open.
  Earlier run 2 (20:29) used a stale copy of the generator (my sync error); all deliveries are now verified by
  re-reading the files from F: and comparing byte-for-byte.

- **2026-10-19 21:05** — ✅ **Generator self-test PASSED 7/7** (`simulations/stress_v2_selftest.txt`, 20:51).
  Every parameter now reaches the simulation: fault/energisation times detected within 1–5 ms
  (e.g. Internal A-B set 0.330 s → seen 0.331 s; inrush 0.263 → 0.268 s; switch-onto-fault 0.453 → 0.454 s);
  noise measured ≈ expected on independent channels (0.0158 vs 0.0156 A, 0.0273 vs 0.0264 A); loads 31–100 %.
  Differential (pu): Internal A-B 2.86, HiZ A-B 0.068 (borderline), SOTF A-B 4.82, External ABC 0.71 (CT stress).
  - **Correction:** single-line-to-ground faults on the delta side are NOT generally undetectable: Internal A-G gave
    **0.55 pu at 61 % load**. The fault current returns through the grounded-Y load neutral, so detectability scales with
    load (the July data used a fixed 3 % load, hence the identical 'B-G' traces). SLG weights restored
    (AG 3, BG 2, CG 2, HiZ_AG 2) → 1200 samples ≈ 503 trip / 697 no-trip.
  - Harmless Simulink diagnostics (algebraic loop, unconnected ports) are muted in memory to keep the log readable.

- **2026-10-21 09:00** — **Plan v3 started (`IMPLEMENTATION_PLAN_V3.md`). Author decisions (section 7):** (1) HV-side internal faults: **add** (back up the .slx first; if the self-test fails, drop it and list as a limitation);
  (2) sympathetic inrush: **skip, list as a limitation** (recovery inrush stays); (3) dataset size: **full, 3,040 main + 300 OOD**.
  - ✅ **A1 done: `simulations/generate_stress_dataset_v3.m`** (derived from v2 by `simulations/tools_make_v3_from_v2.py`; v2 untouched). New options: `'Run'` (resume automatically if a PARTIAL file exists, else start fresh),
    `'Chunk'` (clean stop after N sims in this process, partial saved, returns ''), `'Set'` ('main' | 'OOD'; OOD default seed 20261022), `'Only'` (scenario names / kinds / zones, own seed range so top-ups never duplicate the main run),
    `'Seed'` (default 20261021), default N 3040. Files: `StressDataset_v3_<run>.mat`, `StressDataset_v3OOD_<run>.mat`, `StressDataset_v3Only_<run>.mat`.
    Wrapper `run_stress_v3_generate.bat [N] [main|OOD] [Only-name]`: run id stored in `datasets\stress_v3_<tag>_runid.txt` (re-launch continues the run), MATLAB restarted every 100 sims and after any crash, log
    `datasets\stress_v3_<tag>_generate_log.txt`.
  - Verification: `checkcode` shows only the harmless notes v2 also has (stale suppression, unused input, END alignment); functional test with `Only='Normal'`, N=4, Chunk=2: launch 1 stopped at sample 2 (CHUNK_DONE),
    launch 2 resumed at 3 and saved ONE file (4 unique traces, all checks passed, partial deleted); `stress_dataset.py` loads it. The test file was deleted afterwards.
  - Note: the v3 scenario table, ranges and load model are still v2's; A2-A8 change them. Do not use the v3 generator for a real run before A8 passes.

- **2026-10-21 10:30** — ⚠ **CORRECTION of my own 2026-10-20 87T fix (CT base).** While calibrating the load (A2) the sweep showed the CT-secondary currents far below nominal. `simulations/probe_ct_truth.m` logs the model's
  V-I measurement blocks (TRUE line currents) next to the CT outputs: true HV/LV line current ÷ CT-secondary current = **809.6 : 1 (HV) and 16,925 : 1 (LV)**, i.e. **2.024 x** the winding-voltage ratios (400 and 92000/11) I had used.
  => rated CT-secondary current is **0.9302 A on both sides** (not 1.8827 A; the original relay: HV 1.883 A, LV 0.8557 A). My earlier 87T per-unit values were therefore 2.024 x too small (87T 2x too insensitive) and every
  statement "rated 1.8827 A" / "% of 1.8827 A" in this log is wrong by that factor. The load knob itself works (true primary current 72.9 A vs 75.3 A expected at knob 0.1); the apparent
  "28 % deficit" was the CT scaling. Separate physical limit: the plant has ~1 pu series impedance on the LV side, so the LV bus voltage collapses under load (10.4 kV at knob 0.1, 6.9 kV at 1.0, 2.9 kV at 5.0)
  and the true current reaches only 9.7 % / 61 % / 118 % of rated at knobs 0.1 / 1 / 5.
  - **Fixed:** `lstm_models/relay87t.py` (I_NOM 0.9302), `simulations/fix_87t_compensation.m` (CT_Ratio_HV 809.6, CT_Ratio_LV 16925) applied to the model (backup `TransformerWithCTSaturation_BACKUP_20261021_pre_ctbase.slx`), verified in the saved .slx.
  - **Effect (87T alone, v2 data, plant matrix, base 0.9302 A):** pickup 0.30 pu detects **94 %** of internal faults within 2 cycles (was 84 % with the wrong base; 0.20 pu: 99 %, 0.10 pu: 100 %; HiZ 5 / 18 / 32 %); healthy votes unchanged (Normal 0 %, External 0 %,
    Inrush 100 %, Stress 36 %). **Closed loop still 4/4** (10:25): Normal 0.0001, Inrush 0.0024, Internal A-G TRIP 14.4 ms, External 0.0039. The LSTM path and its features do not depend on this base.
  - **Not redone:** the v2-data multi-seed numbers (dependability 74.5 % gated, 98.9 % with solo) were computed with the wrong 87T base (too insensitive) - they are conservative for the gated part and are superseded by the v3-data evaluation (C1/C2).
  - **For plan v3:** "% rated" must use 0.9302 A. The reachable load range is limited by the plant's LV series impedance (see A2 results); the v2 "5-120 % of 300 MVA" corresponded to ~2-70 % of rated current (not 1-34 %).

- **2026-10-21 11:30** — ✅ **A2 done: load calibration.** `simulations/calibrate_load.m` (3 power factors x 18 knob values, 54 sims, ground truth = the model's V-I measurement blocks) -> `simulations/load_calibration.txt/.mat`.
  - Realised load vs knob (pf 0.9, true current in % of rated): knob 0.02 -> 2 %, 0.12 -> 12 %, 0.37 -> 31 %, 0.77 -> 53 %, 1.1 -> 67 %, 2.3 -> 96 %, 3.3 -> 109 %, 4.8 -> 120 %, 10 -> 133 %. CT-secondary % (/0.9302 A) equals the true % to < 0.5 pt, so the new base is consistent.
  - **Plan check "source voltage at 110 % rated > 0.9 pu" FAILS (documented, plant unchanged):** the LV bus voltage falls as the load rises (0.84 pu at 30 %, 0.62 pu at ~67 %, 0.35 pu at 110 % rated; pf 0.8-1.0 similar) because the
    plant has roughly 1 pu of series impedance on the LV side. The relay only sees currents and HV inrush is unaffected (HV source stays 1.0 pu), but heavy-load cases are not realistic operating points - goes into the Limitations (E3).
    A plant change (lower series R) was not made: it would invalidate the closed-loop validation done so far. Reachable range 2-136 % of rated, so the plan's OOD "110-130 %" block is reachable.
  - `simulations/relay_config.m` now carries `cfg.I_RATED_SEC = 0.9302` and `cfg.LOAD_KNOB_PER_RATED` (struct pf / knob / pctRated); backup `relay_config_BACKUP_20261021.m`. `simulations/load_knob_for.m(pctRated, pf)` interpolates (pchip, linear in pf).
  - **Generator v3 (patch `simulations/tools_patch_v3_A2.py`):** loads are drawn as % of RATED current (10-110 %, stress 60-110 %), pf 0.80-1.00, converted with `load_knob_for`; `cfg.Inom` = 0.9302 A for all six channels (noise % is now % of the true rated secondary);
    new per-trace fields `loadKnob`, `loadRealisedPct`, `loadOK` (within +/-10 % or 2 points; coverage check 6) - `loadPu` is now per unit of rated CURRENT. Self-test (7 cases): all checks OK, realised 27/63/101/32/75 % for targets 26/60/104/31/72 %.
    `faultDiffPu` now uses the corrected 87T differential (0.9302 A base) because the generator logs the relay's I_diff from the corrected model.
  - Next: A3 (CT burden / remanence / ratio-error check), A4 (HiZ sensitivity sweep, needs A2/A3 base), A5 (HV-side fault block, back up the .slx first), A6 (over-excitation, recovery inrush), A7 (stratified draws), A8 (self-test, ~14 cases).

- **2026-10-21 13:00** — **Plant fix attempt (LV series resistors) FAILED and was reverted.** Finding (A3 probes `simulations/probe_ct_stress.m`, `probe_lv_series.m`): the three 0.5 ohm resistors 'Series RLC Branch', 'Branch1', 'Branch2' sit between the transformer LV terminals
  (Internal_Fault blocks) and the CT / V-I measurement / breaker / load / External_Fault node. They cause the LV voltage collapse under load (0.35 pu at 110 % rated) and limit external faults to ~1.5 pu rms at the CTs (internal faults: 28.5 pu).
  With your choice (lower to 0.02 ohm, backup `TransformerWithCTSaturation_BACKUP_20261021_pre_lvR.slx`): voltage 0.95 pu at 92 % load and external 3-phase 7.5 pu rms - BUT the LV CT secondary collapsed to ~7.8 % of its expected value (calibration column `secLV %`:
  7.8 % at 102 % true current, HV side unaffected). These resistors are part of how the LV CT subsystems (CT3/CT4/CT6) are driven, so the relay's LV measurement was destroyed. **Reverted:** the backup was copied back (verified: 18 x R = 0.5 in the .slx,
  AI_Solo_Threshold 0.9950, CT_Ratio_HV 809.6 intact); the failed model is kept as `TransformerWithCTSaturation_FAILED_20261021_lvR002.slx`; calibration regenerated on the restored plant (table identical to `relay_config.m`).
  Consequence: **plant unchanged** = the option-3 documentation path: weak external faults (max ~1.5 pu rms) and LV voltage sag are Limitations. A cleaner way to get strong through-faults would need re-engineering the CT subsystems (not done).
  - **CT remanence cannot be modelled:** the CT's `InitialFlux` has no effect (identical ratio error for 0 and 0.6 pu): the CT core-loss branch (CoreLoss 100 pu) decays the flux in ~25 ms, long before the 0.30 s fault times. Dropped from the plan (documented limitation); CT burden stays.
  - **CT burden works:** the '1ohm' branch in each CT subsystem. Ratio error (max over phases, 40 ms after a solid fault, load 80 %): External 3-phase 1.3 % (1x), 16.9 % (4x), 47.9 % (6x); External A-G 1.5 / 3.3 / 16.7 %; internal A-B solid: HV CT 91-99 % at every burden (28 pu current saturates it hard), LV CT 1.5-4.9 %.

- **2026-10-21 13:40** — ✅ **A3 done: CT stress dimensions** (`tools_patch_v3_A3.py`, `tools_patch_v3_A3b.py` on `generate_stress_dataset_v3.m`; version tag v3-2026-10-21-A3b).
  - **Burden:** the `1ohm` branch in each of the six CT subsystems, set with read-back (same multiple on all six). Burden is a per-trace parameter: ordinary traces 1-3 x, CT-stress traces **4-10 x (log-uniform)** (plan said 1-4 x; external faults here are weak, ~1.5 pu rms, so
    saturation needs more burden: probe ratio errors 4 x / 6 x / 8 x / 12 x: A-G 3 / 12 / 32 / 59 %, A-B 17 / 46 / 64 / 82 %, A-B-C 19 / 49 / 65 / 83 %). OOD block should use ~12 x. **Remanence is not modelled** (no effect, see 13:00 entry).
  - **New per-trace checks/fields:** `ctRatioErrorMax` (% RMS(N*I_ct - I_true)/RMS(I_true), 5-45 ms after the event, max over the six channels; N = 809.6 / 16925; true currents logged from the V-I measurement blocks), `ctBurden`. Realised load (`loadRealisedPct`)
    now also comes from the TRUE currents (independent of CT saturation).
  - **CT-stress scenarios for every fault type:** `Stress_ExtCTSat_<type>` and `Stress_CTSat_Int_<type>` for the 11 types AG BG CG AB BC AC ABG BCG ACG ABC ABCG (replaces the two single-type rows; weights are placeholders until A7).
  - **Self-test (10 cases, all checks OK):** ordinary External_ABC ratio error 2 %, Internal_AG 3 %; Stress_ExtCTSat_ABC (8.5 x) **61 %**, Stress_ExtCTSat_AG (7.8 x) **38 %**, Stress_CTSat_Int_AB (8.2 x) **95 %**; the saturated external 3-phase fault shows a 0.51 pu false
    differential (87T pickup 0.3) - a real security stress. Realised vs target load: 61/63, 69/69, 71/73 %.

- **2026-10-21 14:30** — ✅ **A4 done: HiZ sensitivity sweep.** `simulations/hiz_sensitivity_sweep.m` (one MATLAB per type; internal fault at the LV terminals, 13 Rf values 0.1-100 ohm x 3 loads (30/60/100 % realised), no noise, burden 1 x, corrected differential)
  for AB, BC, AC, ABC, AG (195 sims, outputs `simulations/hiz_sweep_<type>.mat`); fit/merge: `lstm_models/hiz_bins_fit.py` -> `simulations/hiz_bins.json`, `simulations/hiz_bins.txt`, `figures/hiz_sensitivity.png`. All curves monotonic.
  - Phase-phase types are **independent of load** (max/min of the crossing Rf across loads: 1.00-1.02); AG varies with load (Rf@0.30: 1.33 x spread; at 30 % load faultDiffPu is 0.72 pu at 0.1 ohm vs 1.62 pu at 100 % load, the SLG current returns through the load neutral).
  - Crossings (median over loads): Rf at 1 pu / **0.30 pu (87T pickup)** / **0.05 pu (detect limit)** / 0.015 pu: AB 0.34 / 1.14 / 6.63 / 20.6 ohm; ABC 0.40 / 1.31 / 7.50 / 22.3; AC 0.34 / 1.14 / 6.63 / 20.3; BC 0.34 / 1.14 / 6.63 / 20.8; AG 0.21 / 1.08 / 7.08 / 21.1.
  - **Bins for the generator (log-uniform Rf, ohm):** 87T-visible 0.3-1.2, AI-only 1.2-7, undetectable 7-21 (per-type values in `hiz_bins.json`). The v2 HiZ range (1-25 ohm) was 5 % visible, ~60 % AI-only and ~35 % beyond the detect limit.

- **2026-10-21 15:30** — ✅ **A5 done: HV-side internal faults** (author decision: add; backup first).
  - Model: `simulations/add_hv_internal_fault.m` adds `Internal_Fault_HV` (copy of Internal_Fault1) + `Step_HV` (copy of Step3), terminals wired to the transformer HV terminals (inside the HV CT zone), all off by default. Backup
    `TransformerWithCTSaturation_BACKUP_20261021_pre_hvfault.slx`. Built-in safety checks before saving: healthy traces bit-identical with/without the block (max |dIp|, |dIs| = 0.00 A), LV A-B fault faultDiffPu unchanged (10.095 -> 10.095),
    HV A-G solid fault faultDiffPu **16.6 pu** (HV CT peak 100 A, LV CT 0.8 A).
  - ⚠ **Mistake caught and undone:** my first version saved the model with the in-memory TEST setup baked in (noise gains 0, breaker External off, source phase, load, burden ...); the benchmark probabilities shifted (0.0000 / 0.0077 / 1.0000 / 0.0000), which exposed it.
    The bad file is kept as `TransformerWithCTSaturation_BADSAVE_20261021_hv_setup_baked.slx`, the pristine backup was restored, and the script now runs the checks in memory, then reloads the pristine file, adds ONLY the two blocks + wiring, saves, and reloads to
    assert (blocks present, breaker SwitchTimes still '[]', new block all-off). Verified in the saved .slx (breaker SwitchTimes '[]' x 2 as in the original).
  - Closed loop after the block was added: **4/4 PASS** (Normal 0.0002, Inrush 0.0025, Internal A-G TRIP 15.0 ms, External 0.0017). Small shifts vs 14.4 ms / 0.0001 / 0.0024 / 0.0039 (the extra fault block's off-state changes the numerics slightly; the test script also re-saves the model each run).
  - Generator (`tools_patch_v3_A5.py`, v3-2026-10-21-A5): 5th fault block in `B.fault`, kind `internal_hv`, scenarios `InternalHV_<type>` for the 11 types (Rf 0.01-2 ohm, placeholder weights until A7), realised-load check includes the kind.
    Self-test (12 cases, all checks OK): InternalHV_AG faultDiff 8.64 pu, InternalHV_AB 18.2 pu, both timed within 2 ms (CT ratio error 98 %: HV CT saturates at these currents).

- **2026-10-21 17:00** — ✅ **A6 done: over-excitation and recovery inrush** (sympathetic inrush skipped by author decision -> Limitations).
  - **Over-excitation range corrected from probes** (`simulations/probe_overexc_recovery.m`, differential = plant-compensated d, 5th/1st harmonic of a one-cycle DFT): the core only saturates above ~1.2 pu: source 1.22 pu -> d 0.04 pu rms, 5th/1st 0.69;
    1.28 -> 0.24 pu, 0.71; 1.40 -> 0.74 pu, 0.46; 1.55 -> 1.5 pu, 0.24; below 1.2 pu d stays at the 0.006 pu quantisation floor. The plan's 1.05-1.40 would have been mostly plain healthy traces. **Main range 1.15-1.45 pu (~83 % above 1.2),
    OOD 1.50-1.60 pu.** At the upper end the differential exceeds the 87T pickup, so the AI must veto (a real security test).
  - **Recovery inrush needed a new model block.** With the existing LV External_Fault there is no recovery transient (differential 0.006 pu = floor): stiff source, weak LV fault. `simulations/add_hv_bus_fault.m` adds `External_Fault_HV` + `Step_ExtHV` on the 230 kV bus,
    UPSTREAM of the HV breaker and CTs (outside the CT zone; terminals on the breaker's source-side LConn ports); backup `TransformerWithCTSaturation_BACKUP_20261021_pre_hvbusfault.slx`. In generation it is driven by its own SwitchTimes [t1 t2] so it clears after 40-100 ms.
    Checks before saving (all passed): Normal bit-identical (0.00 A), HV bus dips to 0.14 pu (Rf 0.05 ohm) / 0.46 pu (0.2 ohm), recovery transient after clearing up to **1.9 pu differential with 2nd/1st harmonic 0.65-0.73**, strongly dependent on the clearing angle
    (dur 50 ms: 1.9 pu; 60 ms: 0.10 pu; repeats every 20 ms) -> A7 must stratify the clearing angle. Saved with the safe procedure (pristine reload, only the two blocks added; verified: SwitchTimes '[]' x2, AI_Solo_Threshold 0.9950, CT_Ratio_HV 809.6 intact).
  - Generator (`tools_patch_v3_A6.py`, v3-2026-10-21-A6): 6th fault block; every fault block is reset each sample (External on, SwitchTimes [0.05 1]); kinds `overexc` ('Overexcitation') and `recovery_inrush` ('Recovery_Inrush', Rf 0.05-0.3 ohm, HV fault starts 0.30-0.45 s, clears after 40-100 ms,
    `faultTime2` = clearing time, event time = clearing); new per-trace measures `harm5Ratio`, `diffRmsPu` (over-excitation) and `recDiffPeakPu`, `recH2` (recovery); realised-load target now scales with the source voltage (constant-Z load).
    Self-test (14 cases, all checks OK): Recovery_Inrush HV fault 0.329 -> 0.372 s, peak differential after clearing 0.78 pu, 2nd/1st 0.86; Overexcitation (1.16 pu draw) real load 37 % vs target 37 %.

- **2026-10-21 18:30** — ✅ **A7 and A8 done: stratified sampling, quotas, OOD set, extended self-test** (`tools_patch_v3_A7.py`, `A7b`, `A8`; generator version v3-2026-10-21-A8; backup before A7 `generate_stress_dataset_v3_BACKUP_pre_A7.m`).
  - **Quotas = scenario weights, exactly 3,040 for N = 3040** (plan 1.2): Normal 303, Inrush no-load 200, loaded 120, Recovery inrush 80, Over-excitation 150, External faults 11 types x 40 = 440, External HiZ 60, External + CT saturation 11 x 22 = 242, External in inrush 100
    (healthy 1,695); Internal LV 11 x 46 = 506, Internal HV 11 x 18 = 198, Internal HiZ 5 types x 48 = 240, Evolving 80, SOTF 80, Internal + CT saturation 11 x 11 = 121, Fault in inrush 120 (faults 1,345). 11 fault types (AG BG CG AB BC AC ABG BCG ACG ABC ABCG), not 10.
  - **Stratified draws** (`balancedBin`): each bin appears floor/ceil(n/K) times per scenario, independent random order per dimension, uniform inside a bin: load bin (10-30/30-60/60-90/90-110 % rated; CT-stress 60-85/85-110 stored as bins 3-4), inception / closing / clearing angle class
    (4 quadrants + a 'worst case' class within 10 deg of 0/90 deg; the source phase is derived so the angle AT the event is the drawn one, using the drawn frequency), residual-flux bin (largest component 0-0.27 / 0.27-0.53 / 0.53-0.8 pu, three fluxes sum to zero), HiZ Rf bin from `hiz_bins.json`
    (visible / AI-only / undetectable). New continuous dimensions: source impedance scale 0.5-2 x (log-uniform; the 'Three-Phase Series RLC Branch' 0.1 ohm + 1 mH, set with read-back) and frequency 49.8-50.2 Hz; the noise check allows the cycle-difference residual of a load current at f != 50 Hz.
    New per-trace fields: loadBin, angleBin, fluxBin, hizBin, sourceZScale, frequencyHz, oodBlock (+ loadKnob, ctBurden, ctRatioErrorMax, loadRealisedPct, loadOK, harm5Ratio, diffRmsPu, recDiffPeakPu, recH2).
    Verified on a 6-trace HiZ run: Rf bins 2/2/2 with measured faultDiffPu 0.58, 0.60 (visible) / 0.22, 0.24 (AI-only) / 0.014, 0.045 (undetectable); angle classes match the drawn inception angles (283, 163, 14, 268, 8, 6 deg for classes 4, 2, 1, 3, 1, worst-case).
  - **OOD set** (`'Set','OOD'`, seed 20261022, N fixed at 300): 5 blocks x 60 (30 healthy + 30 faults): 1 extreme load (1-10 %, 110-130 %), 2 weak source 3 x + 49.5 / 50.5 Hz, 3 CT burden 12-16 x, 4 over-excitation 1.50-1.60 pu + residual flux 0.9 pu, 5 noise 5 % + CT mismatch +/-8 %. Smoke-tested (loads 6 / 128 / 129 %).
  - **Check fixes found while testing:** over-excitation realised load is taken from the LV current only (the HV current includes the saturated core's magnetising current; target = pct x source voltage); recovery inrush is validated by the HV-bus fault visibly reducing the HV current (hvDipRatio < 0.85)
    because its 'event' (voltage recovery) has no sharp edge; the event-timing tolerance for fault-in-inrush / external-in-inrush is 30 ms (fault edge masked by the inrush; the energisation-time check still guards the breaker-state bug).
  - **A8 self-test (18 cases, one per scenario kind, `simulations/stress_v3_selftest.txt`): ALL PASS** (first run 17/18, the in-inrush timing case re-run after the tolerance change). Highlights: CT saturation ratio error 49 % (ExtCTSat ABC, 5.9 x), 87 % (Int CT-sat AB); InternalHV_AG 9.7 pu, InternalHV_AB 13.6 pu;
    over-excitation 1.31 pu -> differential 0.37 pu, 5th/1st 0.63; HiZ AB faultDiff 0.82 pu at 95 % load. Known low cases (expected, reported in coverage): ExtCTSat A-G at 4.2 x shows only 4 % ratio error (single-line-to-ground external faults are weak; probe: 3 % at 4 x),
    a benign recovery-inrush angle gives 0.006 pu (probe: ~half of the clearing angles are benign), external 3-phase faults are invisible in the raw Ip - Is.

- **2026-10-21 20:30** — ✅ **B1 done: main set generated** `datasets/StressDataset_v3_20261021_021053.mat` (3,040 traces, run seed 20261021, unattended with restart every 100 sims; ~4.5 s per trace, 3 interruptions handled by resume).
  Strict generator checks: **3,015 / 3,040 (99.2 %)**, 0 duplicate waveforms, 0 simulation errors, 14 timing failures, 11 noise failures. Log `datasets/stress_v3_main_generate_log.txt`; wrapper `run_stress_v3_generate_bg.sh` (equivalent of the .bat; it died once when the session environment changed - re-launching resumes).
  - **Benign failures accepted ("relaxed pass", `lstm_models/v3_checks.py`):** (a) 14 timing failures are all the detector firing 12.5-19 ms after the intended time on very large / saturated currents (mostly HV-side internal and CT-saturation traces); labels use the exact intended time, so they are unaffected;
    (b) over-excitation noise-check failures: my check ignored that the saturated core's harmonics leak through the 20 ms cycle-difference at f != 50 Hz (fixed in the generator for traces generated after 09:30; 9 earlier traces carry the flag). Everything else stays rejected. Strict AND relaxed numbers are both reported: 99.2 % strict, **99.9 % relaxed** (3,038 / 3,040).
  - **B3 coverage (`lstm_models/coverage_report_v3.py`, output `datasets/StressDataset_v3_20261021_021053_coverage.txt/.json`):** PASS: 1 load-bin cells (every group x bin >= minimum; e.g. Internal HV-side 41-53 per bin), 3 HiZ (Rf bins 80/80/80, measured faultDiffPu bands >= 0.30 / 0.05-0.30 / < 0.05 pu = 75 / 79 / 86),
    4 CT saturation (External CT-sat 87 % of 238 traces with ratio error > 10 %, per type AG 55 %, BG 68 %, CG 80 %, others 86-100 %; Internal CT-sat 100 %), 6 realised load (100 % of 2,420 measured within tolerance), 7 checks (worst scenario Stress_ExtCTSat_BC 95 %).
    FAIL (2): **2 inrush cells** - loaded inrush has 4 of 12 angle-quadrant x flux-bin cells below 10 (6, 6, 8, 9; no-load inrush is fine, 11-28); **5 over-excitation** - 79 % of traces show 5th/1st > 0.2 with differential > 0.02 pu (target 80 %): the 1.15-1.22 pu draws are plain over-voltage (no saturation).
    Informational: recovery inrush produces a > 0.05 pu differential in 65 of 80 traces (clearing angle dependent).
  - **Top-ups planned (plan section 1.4: "top up failed cells, never train with an empty cell"):** Inrush_Loaded +120 (`'Only'`, own seed range), Overexcitation +60 with a 1.22 pu lower bound (new option `OverexcMin`; main set unchanged at 1.15-1.45).

- **2026-10-21 22:30** — ✅ **B2 and B3 done.** OOD set `datasets/StressDataset_v3OOD_20261021_132520.mat` (300 traces, seed 20261022, 5 blocks x 60): strict checks 285 / 300 (95 %), 0 duplicates, 0 simulation errors (7 timing failures).
  **Top-ups** (own seed ranges, `run_topups_bg.sh`, log `datasets/stress_v3_topup_log.txt`): `StressDataset_v3Only_topup_inrush_loaded.mat` (120 loaded-inrush traces, 120/120 pass) and `StressDataset_v3Only_topup_overexc.mat` (60 over-excitation traces, source 1.22-1.45 pu via the new
  generator option `OverexcMin`; 60/60 pass). **Training set = main + both top-ups = 3,220 traces.**
  **Coverage of the union: ALL 7 CRITERIA PASS** (`datasets/StressDataset_v3_20261021_021053_plus_topups_coverage.txt/.json`; `coverage_report_v3.py` now accepts several files): every loaded-inrush cell >= 14 (angle quadrant x flux bin; no-load inrush 11-28),
  over-excitation harmonics 85 % (178 of 210), HiZ Rf bins 80/80/80 and faultDiffPu bands 75/79/86, CT saturation 87 % (external) / 100 % (internal), realised load 100 %, relaxed generator checks 99.9 % (worst scenario 95 %), 0 duplicates.
  Note the weak spots that stay in the data by design: external single-line-to-ground CT-saturation (AG 55 %, BG 68 %, CG 80 % show > 10 % ratio error) because those external faults are weak in this plant.

- **2026-10-21 23:00** — ✅ **C1 done: baseline of the DEPLOYED model on the v3 data, no retraining** (`lstm_models/train_cv_v3.py baseline`; `runs/20261021_v3data_baseline/baseline.txt/.json`).
  Model `runs/20261020_v3_87tfix` (AI 0.90, solo 0.995, dwell 20), main + top-ups 3,220 traces (94 undetectable faults excluded from headline) and the 300 OOD traces, corrected 87T mirror.
  - **Main set:** 87T alone: dependability 79.6 % / security 53.0 %. Hybrid (87T gate): 88.0 % / 84.8 %. **Hybrid + AI-alone path: dependability 97.1 % (1,251 faults, 17 missed), security 84.1 % (1,873 healthy, 298 false trips)**, operate median 13.75 ms.
  - **Per category (hybrid + AI-alone, correct %, 95 % Wilson):** Normal 100 [98.7-100], External solid 99.3 [98.0-99.8], External HiZ 100, Internal LV solid 99.8, Internal HV-side **100** [98.1-100] (never trained on HV faults), Internal CT-sat 99.2, Evolving 100, SOTF 100, Inrush no-load 98.5,
    Internal HiZ 89.5 [83.7-93.5], Inrush loaded 86.7 [81.8-90.4], External in inrush 87.0, Fault in inrush 84.1, **Recovery inrush 65.0 [54.1-74.5], External CT-sat 60.2 [53.9-66.1], Over-excitation 41.4 [35.0-48.2]**.
  - **OOD:** hybrid + AI-alone 94.4 % dependability (144 faults) / 73.5 % security (147 healthy); worst blocks: over-excitation 1.5-1.6 pu 0 % of 12, External CT-sat 40.7 %, Inrush loaded 72.7 %.
  - Reading: the v2-trained model transfers well for faults (HV-side faults and high load included) and badly for the new healthy stress cases it never saw (over-excitation, recovery inrush, strong CT saturation, loaded inrush). This is exactly the retraining target; it is a result, not a failure (plan risk table).

- **2026-10-22 03:30** — ✅ **C2 done (and C6 ablation from the same predictions): grouped 5-fold CV** `runs/20261021_v3_cv5/` (seed 20261021; 3,218 usable traces each tested exactly once; folds stratified by scenario; 15 % of each training part = validation for the plateau
  thresholds; 12 features, W = 32, plant-compensated input, architecture unchanged; 72 min). Files: `cv_summary.txt/.json` (= `ablation.txt`), `fold1..5/` (checkpoint + per-trace results). Protocol exactly as fixed in plan section 3.
  - **Pooled out-of-fold, headline (94 undetectable faults excluded):**

    | variant | dependability | security | missed / false / pre-fault | operate median / p90 / max | <= 1 / <= 2 cycles |
    |---|---|---|---|---|---|
    | 87T alone (corrected) | 79.62 % | 52.96 % | 131 / 881 / 124 | 0.6 / 7.5 / 22.5 ms | 99.8 / 100 % |
    | LSTM alone | 99.04 % | 99.31 % | 12 / 13 / 0 | 15.0 / 27.5 / 378 ms | 79.4 / 97.7 % |
    | Hybrid (87T gate only) | 89.37 % | 99.63 % | 133 / 7 / 0 | 15.0 / 27.5 / 378 ms | 78.0 / 97.9 % |
    | **Hybrid + AI-alone path** | **98.56 %** | **99.41 %** | **18 / 11 / 0** | 15.6 / 27.5 / 378 ms | 77.1 / 97.7 % |

    Per fold (hybrid + AI-alone): dependability 96.0 / 100 / 98.3 / 99.6 / 98.8 (mean 98.55, sd 1.56); security 99.2 / 99.7 / 99.5 / 99.7 / 98.9 (mean 99.41, sd 0.35); thresholds (AI, solo) 0.98/0.998, 0.98/0.98, 0.96/0.998, 0.95/0.98, 0.995/0.999.
  - **Per category, hybrid + AI-alone (correct %, 95 % Wilson):** Over-excitation 100 [98.2-100] (n = 210) · External CT-sat 98.8 [96.4-99.6] (241) · External in inrush 99.0 [94.6-99.8] (100) · External solid 99.8 [98.7-100] (440) · External HiZ 100 · Inrush loaded 100 [98.4-100] (240) · Inrush no-load 99.5 [97.2-99.9] (200) ·
    Normal 100 (302) · **Recovery inrush 93.8 [86.2-97.3] (80)** · Internal LV solid 100 [99.2-100] (506) · Internal HV-side 100 [98.1-100] (198) · Internal CT-sat 100 [96.9-100] (121) · Evolving 100 · Fault in inrush 100 [96.7-100] · SOTF 97.5 [91.3-99.3] (80) · **Internal HiZ 89.5 [83.7-93.5] (153)**.
    The 87T alone fails exactly where expected: inrush 0 % (all categories), over-excitation 42 %, recovery inrush 24 %, external CT-sat 34 %, Internal HiZ 52 %. LSTM alone ~ matches the hybrid on security but the gate adds the 87T independence; the gate-only hybrid loses 9 points of dependability (HiZ and weak faults the 87T never votes on) - the AI-alone path recovers them.
  - **Targets of plan section 4:** security all healthy >= 99.5 %: 99.41 % (just short; 11 false trips of 1,873); inrush / over-excitation >= 99 %: met except **recovery inrush 93.8 %**; external + CT-sat >= 98 %: 98.8 % met; detectable internal faults >= 99 %: LV 100 %, HV 100 %, CT-sat 100 % met;
    HiZ AI-only bin target >= 90 %: Internal HiZ overall 89.5 % (see per-bin split next); median operate <= 16 ms met (15.6), 97.7 % within 2 cycles met (>= 95 %), pre-fault trips 0 met.
  - **C4 decision (rule fixed in advance): NOT triggered** - over-excitation security 100 % (>= 99 %) and external CT-sat security 98.8 % (>= 98 %). The 12-feature design stays; no 5th-harmonic features.
  - Next: C3 (two more seeds -> 15 models), C5 (final model + one scoring of the OOD set), per-bin HiZ analysis, D1-D4.

- **2026-10-21 12:30** — ✅ **C3 done: repeatability** (3 CV runs x 5 folds = 15 models; seeds 20261021 / 22 / 23, each seed a different fold assignment; `runs/20261021_v3_cv5_seeds/summary.txt`, `lstm_models/summarize_cv_seeds.py`; per-run dirs `runs/20261021_v3_cv5*`).
  - **Hybrid + AI-alone path, pooled per seed (dependability / security):** 98.56 / 99.41, 99.52 / 99.68, 98.96 / 99.89 -> **mean 99.01 % (sd 0.48 across seeds) / 99.66 % (sd 0.24)**. Over all 15 fold-models: dependability **99.01 %, sd 1.07, range 96.0-100**; security **99.66 %, sd 0.33, range 98.9-100**
    (plan criterion "sd of dependability and security < 2 pt": met). Pre-fault trips 0 in all three seeds; operate median 15.6 ms (sd 0.00), 96.9 % within 2 cycles (sd 0.77); thresholds over 15 models: AI 0.950-0.997 (logit sd 0.92), solo 0.980-1.000 (logit sd 1.14).
  - Other variants (mean over the 3 seeds): LSTM alone 99.31 / 99.56; hybrid with the 87T gate only 89.40 / 99.79; 87T alone 79.62 / 52.96. The hybrid + AI-alone path is the best compromise: it keeps the 87T gate's security (99.66 vs 99.79) and recovers the 10 points of dependability the gate alone loses.
  - **Per category, mean over seeds (min seed):** Normal, Internal LV, Internal HV, Internal CT-sat, Evolving, Fault in inrush, External HiZ, Over-excitation 100 (100); Inrush loaded 99.9 (99.6); Inrush no-load 99.8 (99.5); External solid 99.9 (99.8); External CT-sat 99.2 (98.8);
    External in inrush 98.7 (98.0); SOTF 97.9 (97.5); **Recovery inrush 97.5 (93.8)**; **Internal HiZ 93.0 (89.5)**. Plan targets: security >= 99.5 % met (99.66); inrush / over-excitation >= 99 % met except recovery inrush (97.5 mean; the weakest healthy category); external + CT-sat >= 98 % met (99.2).
  - Seed 1 -> seeds 2/3 differences (e.g. Internal HiZ 89.5 -> 96.7 / 92.8, Recovery inrush 93.8 -> 98.8 / 100) show the split / initialisation sensitivity of the small categories (n = 80-153): quote the 3-seed mean and the 95 % Wilson intervals, not a single seed.

- **2026-10-21 13:30** — ✅ **C5 done: final model + ONE scoring of the OOD set** (`runs/20261022_v3_final/`, `train_cv_v3.py final`). Trained on 2,655 traces (all main + top-up traces except 469 validation traces and the 94 undetectable faults), 8 epochs, seed 20261021, 12 features, W = 32, plant-compensated input.
  Thresholds by the plateau rules on the validation traces: **AI_Threshold 0.99, AI_Solo_Threshold 0.998, dwell 20** (`decision_threshold.txt`, `decision_solo_threshold.txt`, `decision_dwell.txt`). Checkpoint `transformer_protection_lstm_best.pth`. OOD scored once, no re-tuning: `report_ood.txt/.json`.
  - **OOD (300 traces; 291 pass checks: 144 faults, 147 healthy):** hybrid + AI-alone path: **security 100.0 % (0 false trips)**, dependability **92.4 %** (10 missed), 1 pre-fault trip, operate median 16.25 ms. LSTM alone 95.1 / 100; hybrid 87T gate only 89.6 / 100; 87T alone 79.2 / 43.5.
    Compared with the DEPLOYED v2-trained model on the same traces (C1): 94.4 / 73.5 -> the retraining fixed security (+26.5 points) at the cost of 2 points of OOD dependability.
  - **Per block (hybrid + AI-alone):** 1 extreme load 96.7 % dep / 100 % sec; 2 weak source + 49.5 / 50.5 Hz 100 / 100; **3 CT burden 12-16 x: dependability 68.0 % (internal CT-sat faults, 7 missed of 25), security 100 %**; 4 over-excitation 1.5-1.6 pu + flux 0.9 pu 93.3 / 100; 5 noise 5 % + CT mismatch +/-8 % 100 / 100.
    **Limitations entry (drop > 5 pt rule):** internal faults with an extreme CT burden (12-16 x, 3-4 x beyond the training range) are missed in 28 % of cases. Per category: External CT-sat 100 [87.5-100], Internal CT-sat 68.0 [48.4-82.8], SOTF 80.0 [49.0-94.3] (n = 10), all others 98.6-100 (small n).

- **2026-10-21 16:30** — ✅ **D1, D2 done; D3 done with a documented timing shortfall.**
  - **D1 deploy:** backups `TransformerWithCTSaturation_BACKUP_20261022_pre_v3.slx`, `live_relay_ai_BACKUP_20261022_pre_v3.mat`, `wt_lstm_relay_BACKUP_20261022_pre_v3.onnx`; ONNX exported from `runs/20261022_v3_final` (PyTorch vs ONNX max error 0.0), network rebuilt (`ONNXBUILDER`), thresholds
    `set_ai_threshold` 0.9900 and `fix_ai_solo_trip` 0.9980 (8 chart self-tests passed). Verified in the saved .slx: AI_Threshold 0.9900, AI_Solo_Threshold 0.9980, CT_Ratio_HV 809.6 chart, HV-fault blocks present, Yd1_plant_map present, breaker SwitchTimes '[]' x2 (original). Dwell 20 (relay_config).
  - **D2 feature parity (plant-compensated input):** Normal and Internal A-G max |relay - training| = **0** (PASS), `simulations/feature_parity_v3.txt`.
  - **D3 extended closed loop, 12 cases, LSTM active, the model's own trip logic** (new generator mode `generate_stress_dataset_v3('closedloop')`, `tools_patch_v3_closedloop.py`; results `simulations/test_hybrid_relay_v3_results.txt/.mat`, console `d3_console.txt`):
    **12 / 12 trip decisions correct** - BLOCK: Normal 30 % (max prob 0.0004) and 100 % load (0.0001), inrush with 0.8 pu remanence at 0 deg (0.0673), recovery inrush with a 50 ms HV-bus fault (0.0306), over-excitation 1.3 pu (0.0000), external 3-phase solid (0.0000),
    external A-G with 8 x CT burden (0.0002); TRIP: internal A-G LV side **15.0 ms**, internal A-B HV side **0.6 ms**, **internal HiZ A-B in the AI-only bin (Rf 3 ohm) 47.5 ms** (the AI-alone path works in Simulink), SOTF A-B **13.8 ms**, fault during inrush A-B-G **41.3 ms**.
    **Plan criterion "internal trips <= 1.5 cycles (30 ms)": met by 3 of 5 trip cases** (A-G 15.0, HV A-B 0.6, SOTF 13.8); the HiZ AI-only case (47.5 ms = 2.4 cycles) and the fault during inrush (41.3 ms = 2.1 cycles) exceed it. Both are the slowest categories in the CV too (AI confidence needs the weak / masked
    fault to build up); not tuned away. Reported as: 12 / 12 decisions correct, 10 / 12 cases also meet the 30 ms criterion.

- **2026-10-21 22:00** — ✅ **D4 and E1-E4 done: PLAN V3 COMPLETE.**
  - **D4 closed loop vs Python mirror** (`lstm_models/d4_select_and_mirror.py`, `simulations/closed_loop_vs_python_v3.txt`; Simulink runs `simulations/test_hybrid_relay_d4*_results.mat`, `d4_*_console.txt`): 50 traces re-run in Simulink with the LSTM active
    (same seeds / strata as the dataset): 25 held-out validation traces of the final model (main set) + 25 OOD traces. **Decision agreement 50 / 50 = 100 %** (criterion >= 98 %); both Simulink and the mirror are 50 / 50 correct against the ground truth.
    Trip-time difference Simulink - mirror over 21 common trips: **median 0.00 ms** (criterion <= 2 ms), mean 0.82 ms, p95 8.45 ms, max 8.85 ms (the larger differences are HV-side faults where the Simulink high-set path acts on its own RMS timing).
  - **E1 tables** `documents/results_v3/tables.md` (+ `table2_per_category.csv`), generated only from saved files (`lstm_models/make_tables_v3.py`): ablation (3 repetitions), per category with Wilson intervals, retraining effect (C1 vs C2), OOD per block, 12-case closed loop, D4, HiZ by bin.
  - **E2 figures** (`lstm_models/make_figures_v3.py`, `documents/results_v3/*.png`): coverage heat-maps, operate-time CDF, threshold trade-off, one example waveform per scenario category; `figures/hiz_sensitivity.png` from A4.
  - **E3** `documents/results_v3/limitations.md`: simulation-only / one plant; plant facts that shape the results (CT base 0.9302 A, weak external faults + LV voltage sag from the series resistors, no CT remanence, no sympathetic inrush); evaluation design (CV on one plant, undetectable faults excluded, relaxed check rule, small categories);
    measured weak spots (HiZ AI-only band 71 %, recovery inrush 97.5 % mean / 93.8 % worst, slow categories, OOD extreme CT burden 68 %).
  - **E4** `walkthrough.md` kept but marked SUPERSEDED / DO NOT CITE (banner on top; its numbers match no saved file); `CLAUDE.md` updated (deployed model `runs/20261022_v3_final`, facts and rules for the next session).
  - **Deployed relay now:** `runs/20261022_v3_final` (12 features, W = 32, plant-compensated input, AI_Threshold 0.99, AI_Solo_Threshold 0.998, dwell 20), corrected 87T chart (bases 0.9302 A, plant matrix), HV-side and HV-bus fault blocks in the model.
  - **Headline numbers for the thesis (all from saved files):** CV, 15 models, hybrid + AI-alone path: dependability 99.01 % (sd 1.07), security 99.66 % (sd 0.33), 0 pre-fault trips, operate median 15.6 ms, 96.9 % within two cycles; ablation: 87T alone 79.6 / 53.0, LSTM alone 99.3 / 99.6, hybrid (87T gate) 89.4 / 99.8;
    OOD (scored once): 92.4 % / 100 %; closed loop: 12 / 12 decisions correct (10 / 12 within 30 ms), 50 / 50 agreement with the Python mirror.
  - **Open items beyond plan V3:** (1) HiZ AI-only band 71 % and recovery inrush are below the pre-set targets (report as measured; a solo-threshold rule that weights dependability in the AI-only band would be a new, separately validated design change); (2) internal faults under 12-16 x CT burden (OOD block 3);
    (3) a plant change that makes external faults strong without breaking the LV CT drive would need the CT subsystems re-engineered; (4) the .venv-lstm environment is still dead (work uses system Python + .pylibs); (5) nothing is committed to git.

- **2026-10-23 20:00** — ✅ **Literature benchmark suite implementation & evaluation:**
  - Implemented `benchmark_literature_models.py` spanning 7 literature baselines: Conventional 87T, Wavelet-SVM, Wavelet-ANN, Wavelet-RF, 1D-CNN, Wavelet-GRU, and Standalone LSTM.
  - Evaluated on identical 5-fold cross-validation split (Seed 20261021) in both Standalone Literature Operating Mode and Proposed Supervisory Hybrid Mode.
  - Saved full outputs to `runs/literature_benchmark/literature_benchmark_summary.json` and generated `table_literature_benchmark.tex`.

- **2026-10-24 to 2026-10-25** — ✅ **Academic Review Rounds 2–4 & Repository Preparation:**
  - Conducted academic review passes, identified documentation gaps, and updated figures via `generate_all_updated_figures.py`.
  - Cleaned up local git configuration (user email set to GitHub noreply address `155192927+SS-Abeer13@users.noreply.github.com`), removed third-party binary `matlab-mcp-server.mcpb`, removed copyrighted reference PDFs, purged 36 MB diagnostics dump and local MiKTeX caches, and pushed clean baseline commit `8648eb8` to `main`.

- **2026-10-26 18:50** — ✅ **P1, P2, and P3 Manuscript Reconciliations & Data-Driven Pipeline:**
  - **P2.1 Harmonic-restrained 87T baseline:** implemented `analyse_harmonic()` in `lstm_models/relay87t.py` with 2nd-harmonic ($k_2 \le 0.15$) and 5th-harmonic ($k_5 \le 0.35$) cross-blocking and 20-sample dwell. Measured out-of-fold CV (70.65% dep / 87.48% sec with dwell, 76.05% dep / 86.14% sec instantaneous) and OOD (77.70% dep / 78.77% sec with dwell). Added to table notes and baseline comparisons.
  - **P2.4 Data-driven tables:** created `generate_thesis_tables_and_macros.py` which dynamically extracts results from saved JSON, MAT, and summary files to generate modular `.tex` tables (`table_6_1_ablation.tex`, `table_6_2_categories.tex`, `table_6_3_retraining.tex`, `table_6_4_ood.tex`, `table_6_5_closed_loop.tex`, `table_6_6_hiz.tex`, `table_literature_benchmark.tex`) and macro synchronization file `thesis_results_macros.tex`.
  - **P1.1 Closed-loop Table 6.5:** sourced directly from `simulations/test_hybrid_relay_v3_results.mat`. All 12/12 trip decisions verified correct (10/12 within 30 ms criterion; internal HiZ at 47.5 ms and fault during inrush at 41.3 ms honestly reported as exceeding 30 ms). Fabricated "10% winding" removed (terminal faults only).
  - **P1.2 87T parameters:** corrected manuscript to match exact code/Simulink implementation ($I_{pickup} = 0.30$ pu, $S_1 = 25\%$, $S_2 = 60\%$, $I_{bp} = 3.0$ pu, HighSet 10.0 pu true RMS, unrestrained baseline). Clarified that inrush false trips in the conventional 87T baseline result from lack of harmonic restraint.
  - **P1.3 & P1.5 Latency and operate time:** removed unmeasured latency column from Table 6.7; dropped 0.44 ms ONNX latency claim from text and Table A; RF complexity designated as `100 trees`. Replaced "physical fault-clearing time" with "relay operate time" (fault inception to trip decision; circuit breaker opening is not modelled).
  - **P1.4 Plant description:** corrected §4.4 to document the three existing $0.5\,\Omega$ series resistors as part of the LV CT drive circuitry, noted ~1.5 pu through-faults as a simulation limitation, and clarified that CT saturation is driven by burden ($4\times\text{--}10\times$) and DC offset without remanence.
  - **P2.2 & P2.3 Toned down claims & standards:** recognized Wavelet-RF standalone security (99.89%, 2 false trips), framed contribution around the dual-path supervisory architecture as a universal security anchor, removed non-existent recovery inrush HiZ scenario, framed BDWT as qualitative discussion, and revised standards language in Appendix B to "settings chosen with reference to applicable standards and guides".
  - **Figure updates:** updated `generate_all_updated_figures.py` (Fig 1.1 terminal faults and $0.5\,\Omega$ resistor, Fig 3.1 exact dual-slope curves) and regenerated all figures.
  - **Manuscript compilation:** regenerated `latex_source/latex/main.tex` via `rebuild_thesis_manuscript.py`, verified XeLaTeX compilation cleanly with zero errors, exactly meeting the 64-page document budget.

- **2026-10-26 20:15** — ✅ **Re-check Section R1–R3 (Harmonic Restraint Variants Evaluation):**
  - Executed `tools/review_check_harmonic87t.py` across all 3,218 traces ($N_{\text{eval}} = 3{,}124$) to evaluate three distinct harmonic restraint configurations:
    - **R1 (`as_coded` unselective cross-blocking):** Dep 55.24%, Sec 100.00%, 0 false trips. Confirmed that cross-blocking from any phase (even near-zero current phases) blinds the relay to internal faults under CT saturation (0% recall across `Stress_CTSat_Int_*`).
    - **R2 (`cross_active` active-phase cross-blocking):** Dep 61.71%, Sec 99.95%, 1 false trip.
    - **R3 (`per_phase` phase-independent restraint — commercial practice):** Dep 84.33%, Sec 97.97%, 38 false trips.
  - Demonstrated that the proposed Hybrid DWT–LSTM (98.56% dep, 99.41% sec, 11 false trips) decisively outperforms all conventional harmonic restraint schemes, achieving +14.23 pt higher dependability than R3 by recovering weak faults via the AI-alone path.
  - Updated `lstm_models/relay87t.py` with multi-mode `analyse_harmonic(mode='per_phase'|'cross_active'|'as_coded')`.
  - Added Re-check section R1–R3 to `REVIEW_FIXES_2026-10-26.md` and updated Table 6.7 note.

- **2026-10-26 21:05** — ✅ **Re-check 2 & R3 Execution & Data-Driven Baseline Finalization:**
  - **Automated evaluation script & saved result files:** implemented `tools/evaluate_harmonic87t.py` to evaluate unrestrained 87T and all three harmonic restraint configurations (R1 `as_coded`, R2 `cross_active`, R3 `per_phase`) across both 5-fold cross-validation ($N_{\text{eval}} = 3{,}124$) and the Out-of-Distribution stress suite ($N_{\text{eval}} = 291$).
  - **Result persistence:** saved exact metrics to `runs/20261026_harmonic87t/summary.json` and `runs/20261026_harmonic87t/summary.txt`:
    - R3 (`per_phase` commercial practice): CV pooled dependability **84.33%**, security **97.97%**, 38 false trips, median $T_{\text{op}}$ **18.12 ms**; 5-fold CV mean dep **84.32 $\pm$ 1.40%**, sec **97.97 $\pm$ 0.80%**; OOD overall dep **84.72%**, sec **87.07%**, 19 false trips.
    - Baseline unrestrained 87T: CV pooled dep 79.62%, sec 52.96%, 881 false trips; OOD dep 79.17%, sec 43.54%, 83 false trips.
  - **Dynamic table & macro integration:** updated `generate_thesis_tables_and_macros.py` to dynamically load `runs/20261026_harmonic87t/summary.json` without hardcoded numbers in Table 6.7 note; added macros `\HarmonicBaselineDep`, `\HarmonicBaselineSec`, `\HarmonicBaselineFalseTrips`, `\HarmonicBaselineMedOperate`, `\HarmonicBaselineOODDep`, `\HarmonicBaselineOODSec`, `\HarmonicBaselineOODFalseTrips` to `thesis_results_macros.tex`.
  - **R3 leftovers resolved:**
    - Fixed `main.tex` line 691 and rebuild scripts to describe conventional 87T baseline without harmonic blocking and cite dedicated phase-independent harmonic restraint comparison.
    - Replaced "maximizing fault-clearing velocity" with "minimising relay operate time" at `main.tex` line 676 and rebuild scripts.
    - Cleaned `benchmark_literature_models.py` and `runs/literature_benchmark/literature_benchmark_summary.json` to purge invented `latency_ms` constants and update Random Forest complexity to actual tree representation (`100 trees (nodes variable)`).
  - **Recompilation & audit verification:** recompiled `main.tex` via XeLaTeX with exit code 0, verifying exactly 64 pages (16 front-matter + 48 main-matter); marked all remaining checkboxes in `REVIEW_FIXES_2026-10-26.md` as `[x] Done`.

---

- **2026-10-26 23:41** — ✅ **Phase 0 Complete (Safety & Baseline Freeze for Publication Plan v4):**
  - Created git tag thesis-final-2026-10-26 on commit 8f5ee2a (thesis final freeze commit).
  - Created safety backups:
    - simulations/TransformerWithCTSaturation_BACKUP_20261026_pre_v4.slx (93,167 bytes)
    - simulations/live_relay_ai_BACKUP_20261026_pre_v4.mat (243,633 bytes)
    - lstm_models/wt_lstm_relay_BACKUP_20261026_pre_v4.onnx (240,516 bytes)
  - Created isolated working copy simulations/TransformerWithCTSaturation_v4.slx (93,167 bytes). All Phase 1–3 model revisions will occur exclusively in _v4.slx, leaving TransformerWithCTSaturation.slx untouched.
  - Phase 0 items in IMPLEMENTATION_PLAN_V4_PUBLICATION.md marked complete.

- **2026-10-26 23:47** — ✅ **Phase 1.1 Complete (CT & Series Resistor Topology Confirmed):**
  - Executed simulations/check_ct_topology_v4.m in MATLAB to extract the exact physical PortConnectivity of all 6 CTs (CT, CT1, CT2 on HV; CT4, CT3, CT6 on LV) and all branch RLC blocks.
  - **Hypothesis confirmed:** on both HV and LV sides, each phase CT primary is wired in series with a 0.5 Ω resistor and placed in parallel with another 0.5 Ω resistor. This 50% current-divider bridge causes the CT primary to carry only half the true line current (effective CT ratios 809.6:1 and 16,925:1, exactly 2.024× nameplate). The resulting series resistance choked LV through-faults to ~1.5 pu.
  - Documented complete port-by-port connectivity and executive summary in simulations/ct_topology_v4.txt.

---

- **2026-10-27 00:05** — ✅ **Phase 1.2 Complete (CTs Re-wired in Series):**
  - Executed simulations/rewire_cts_series_v4.m on TransformerWithCTSaturation_v4.slx.
  - Removed the parallel 0.5 Ω bypass bridge resistors; set series damping resistors to 0.001 Ω (1 mΩ) so the CT primaries carry full line current. Saved updated .slx.

- **2026-10-27 00:15** — ✅ **Phase 1.3 Complete (CT Calibration & Base Updates):**
  - Executed simulations/probe_ct_truth_v4.m; effective CT ratios re-calibrated to HV 404.7288:1, LV 8,460.0372:1.
  - Rated CT secondary current base established as {\\text{nom}} = 1.8610\\text{ A}$ (HV 1.8607 A, LV 1.8612 A).
  - Updated lstm_models/relay87t.py with I_NOM_V4 = 1.8610, CT_RATIO_HV_V4 = 404.7288, CT_RATIO_LV_V4 = 8460.0372.
  - Updated simulations/relay_config.m with cfg.I_RATED_SEC = 1.8610.
  - Executed simulations/fix_87t_compensation_v4.m to calibrate Yd1 compensation chart in the v4 model.

- **2026-10-27 00:20** — ✅ **Phase 1.4 Complete (Per-Unit Normalisation & Parity Verification):**
  - Normalised differential current by {\\text{nom}} = 1.8610\\text{ A}$ before DWT feature extraction in lstm_models/features12.py and Simulink DWT_Feature_Extraction chart.
  - Executed simulations/verify_lstm_feature_parity_v4.m: max feature error = 0.0 (exact bit-level parity).

- **2026-10-27 00:35** — ✅ **Phase 1.5 Complete (Plant Physics & HiZ Sensitivity Verified):**
  - Executed simulations/check_plant_v4_physics.m: LV bus voltage at 100% load = 1.05 pu (criterion >= 0.95 pu: PASS); through-fault current = 6.41 pu RMS (criterion 5-20 pu: PASS).
  - Calibrated load table generated across 18 points (simulations/load_calibration_v4.mat and .txt).
  - Executed HiZ sensitivity sweeps across all 5 fault types (AB, BC, AC, ABC, AG) in simulations/hiz_sensitivity_sweep_v4.m.
  - Executed lstm_models/hiz_bins_fit.py with 1.8610 A base: updated simulations/hiz_bins.json, simulations/hiz_bins.txt, and figures/hiz_sensitivity.png.

- **2026-10-27 00:43** — ✅ **Phase 1.6 Generator & Self-Test Complete:**
  - Created simulations/generate_stress_dataset_v4.m, run_stress_v4_generate.bat, and lstm_models/coverage_report_v4.py.
  - Ran self-test across all 18 representative scenario kinds: all 18 PASSED.
  - Circuit analysis verified through-fault current between 5.23 pu and 7.09 pu for Rf in [0.001, 0.03] ohm.

---

- **2026-10-27 00:43** — **Phase 1 Complete (Generator, Dataset & Verification):**
  - Executed simulations/generate_stress_dataset_v4.m, run_stress_v4_generate.bat, and lstm_models/coverage_report_v4.py.
  - Generated 3,175 main traces + 300 OOD traces across 4 .mat files in datasets/.
  - Coverage verified: 99.2% of multi-phase through-faults >= 5.0 pu (median 9.12 pu, max 14.40 pu). All 8 coverage criteria passed (100% PASS).

- **2026-10-27 17:18** — **Phase 4.1 Complete (Measured Latency Benchmark):**
  - Executed tools/measure_latency.py: 10,000 timed streaming evaluations on AMD Ryzen 7 7700.
  - Feature extraction: median 35.0 us; LSTM ONNX inference: median 124.3 us; Combined pipeline: median 205.2 us (p99 304.1 us) vs 625.0 us real-time deadline (32.8% CPU time utilization, 67.2% idle headroom).
  - Saved to runs/20261027_latency/latency.json and latency.txt.

- **2026-10-27 21:16** — **Phase 2 Complete (Evaluation, Models, OOD & Statistical Significance):**
  - Phase 2.1: Multi-seed 5-fold CV across 3 seeds (15 fold-models): Proposed Hybrid dependability 98.63% +/- 1.15%, security 99.52% +/- 0.51%, median Top = 17.5 ms. Conventional 87T alone: 80.33% dep, 30.17% sec. Saved to runs/20261027_v4_cv5_seeds/.
  - Phase 2.2: Final model trained (runs/20261027_v4_final/transformer_protection_lstm_best.pth), calibrated thresholds (ai=0.9950, solo=0.9990, dwell=20). Single-pass OOD evaluation (278 traces): dependability 92.7%, security 95.0%, median Top = 19.4 ms. ONNX model deployed to lstm_models/wt_lstm_relay.onnx with bit-level parity.
  - Phase 2.3: Literature benchmark across 6 architectures (SVM, ANN, RF, 1D-CNN, GRU, Proposed): Proposed Hybrid achieved fastest trip speed (17.5 ms median) with 98.34% dep, 99.50% sec.
  - Phase 2.4: 50 dynamic traces closed loop in Simulink vs offline Python relay mirror: 100.0% decision agreement (50/50), 0.00 ms median dt. Saved to simulations/closed_loop_vs_python_v4.txt.
  - Phase 2.5: Paired McNemar significance tests: Proposed vs Unrestrained 87T (chi2=218.34, p=2.32e-63 for dep; chi2=1255.00, p=0.0 for sec); Proposed vs Harmonic 87T (chi2=703.31, p=9.80e-205 for dep; chi2=636.26, p=1.21e-185 for sec). Saved to runs/20261027_v4_stats/.

- **2026-10-27 20:45** — **Phase 3.1 & 3.2 Complete (Plant B Model, Dyn11 & Physics Verification):**
  - Created simulations/TransformerB_v4.slx: 40 MVA, 132/33 kV, Dyn11, 1 A CT secondaries (Inom = 0.8232 A), CT ratios 202.0119:1 and 808.8849:1, nominal burden 2.5 ohm.
  - Physics verified (simulations/plant_b_checks.txt): LV voltage 0.986 pu >= 0.95 pu (PASS); Through-fault current 5.00 pu RMS >= 5.0 pu (PASS); Natural CT saturation ratio error 80.7% > 1% (PASS); Differential residual 0.0368 pu < 0.05 pu (PASS).
  - Load calibration saved to simulations/load_calibration_plant_b.mat.
  - Created simulations/generate_stress_dataset_plant_b.m, run_stress_plant_b_generate.bat.
  - Self-test executed: all 18 representative scenario kinds passed (18/18 PASS).

- **2026-10-27 22:10** — **Phase 3.3 In Progress:** Main Plant B dataset generation running unattended via run_stress_plant_b_generate.bat.
  - tools/run_plant_b_generalization.py created; tools/build_publication_tables.py created.

- **2026-10-27 23:37** — **Phase 3.3 Complete (Plant B Main Dataset):**
  - datasets/StressDataset_PlantB_20261027_215741.mat written (1,200 traces, 28.25 MB).

- **2026-10-27 23:49** — **Phase 3.3 Complete (Plant B OOD Dataset):**
  - datasets/StressDataset_PlantBOOD_20261027_233720.mat written (150 traces).

- **2026-10-27 23:59** — **Phase 3.4 Experiment 1 Complete (Zero-Shot Transfer):**
  - Plant-A model applied to Plant B with no retraining.
  - Proposed DWT-LSTM: dep 83.23%, sec 93.53%, median Top 26.3 ms.
  - Harmonic 87T on Plant B: dep 68.26% (0 harmonically-restrained trips; 94 false trips on non-faults).
  - Saved to runs/20261027_v4_plant_b_zeroshot/zero_shot_summary.json.

- **2026-10-28 01:01** — **Phase 3.4 Experiment 2 Complete (Cross-Plant 5-Fold CV):**
  - Pooled A+B (4,268 traces): dep 98.69%, sec 98.31%, median Top 16.9 ms.
  - Plant A eval: dep 98.80%, sec 98.40%; Plant B eval: dep 98.40%, sec 98.06%.
  - Saved to runs/20261027_v4_cross_plant/cross_plant_summary.json.

- **2026-10-28 01:21** — **Phase 3.4 Experiment 3 Complete (Leave-One-Plant-Out):**
  - Train A → Test B: dep 84.23%, sec 91.91%, median Top 32.5 ms.
  - Train B → Test A: dep 67.39%, sec 88.07%, median Top 18.1 ms.
  - Saved to runs/20261027_v4_leave_one_out/leave_one_out_summary.json.

- **2026-10-28 01:39** — **Phase 4.2 Complete (Hand-Written ANSI C Latency Benchmark):**
  - tools/relay_c/ (relay_pipeline.c/.h, relay_weights.h, main_benchmark.c) generated by
    tools/build_and_run_c_benchmark.py. NOT MATLAB Coder output — hand-written C mirroring the Python pipeline.
  - Compiled: MinGW-w64 GCC 16.1.0, -O3 -mavx2 -mfma.
  - Feature extraction: median 1.00 µs (p99 1.20 µs); LSTM: 190.4 µs; Combined: 191.6 µs (p99 251.1 µs).
  - CPU utilisation 30.7% of 625 µs budget (69.3% idle headroom). Parity vs PyTorch: PASS.
  - Saved to runs/20261027_latency/latency_c.json and latency_c.txt.

- **2026-10-28 01:39** — **Phase 5 Tables + LaTeX Compiled:**
  - tools/build_publication_tables.py regenerated all 7 tables from saved JSON files.
  - Table 6.6 updated to dual-panel (ONNX 205.2 µs + ANSI C 191.6 µs).
  - XeLaTeX: 64 pages, zero fatal errors.

- **2026-10-28 01:39** — **Git commit c831a02** (72 files, author SS-Abeer13, no push).

---


- **2026-10-28 10:01** — **Review of V4 progress (V1-V7): fixes, diagnoses, reconciliation** (details in the new section of `IMPLEMENTATION_PLAN_V4_PUBLICATION.md`).
  - V1 fixed and verified: harmonic-87T McNemar pairing by trace identity (`tools/compute_v4_statistics.py`); stats re-run, Table 6.3 regenerated. Harmonic 87T = 81.67 % / 91.67 % (was misreported 41.55 % / 63.65 %); p-values now 3.3e-62 / 2.2e-34.
  - V2 confirmed, OPEN: plant B "Proposed" = "LSTM alone" (identical metrics); the plant B 87T votes on 24.4 % of Normal traces (0 % below 60 % load or 1.5x burden, 77 % at 90-111 % load, 48 % at 2.5-3x burden) because the CT saturates in steady state.
  - V3 diagnosed and the CHECK fixed, plant OPEN: the plant B physics check indexed the true current with the wrong time base (pre-fault samples). Corrected report `simulations/plant_b_checks.txt`: true through-fault 37.6 pu (FAIL vs 5-20 pu), CTs read 5.0 pu (saturation, about 7.5x under-read).
  - V4/V5/V6 done: plant A true through-fault 23.9 pu RMS vs CT 6.4 pu (`simulations/plant_v4_truth_check.txt`); inrush from datasets 2.8 / 2.0 rated-peak medians (`simulations/inrush_check_from_datasets.txt`); C latency wording corrected (hand-written C, not MATLAB Coder).
  - **Reconciliation of the log with file modification times (system clock):** `runs/20261027_v4_harmonic87t/summary.json` 17:16; `v4_cv5_seeds/summary.json` 18:32; `v4_final/report_ood.json` 18:49; `TransformerB_v4.slx` 20:36; `v4_literature_benchmark` 21:15; plant B main dataset 23:37 and OOD dataset 23:49 (2026-10-27);
    `v4_plant_b_zeroshot` 23:59; `v4_cross_plant` 01:01; `v4_leave_one_out` 01:21; `latency_c.json` 01:39 (2026-10-28); `v4_stats` regenerated 10:01 (this review). The entries "Phase 4.1 17:18", "Phase 3.1 & 3.2 20:45" and "Phase 2 21:16" above are consistent with these times but are not in chronological order in the file;
    the Phase 2 statistics (V1) and the plant B checks (V3) were wrong when logged and are superseded by this entry. Phase 1 entries are timed 00:05-00:43 on 2026-10-27 while the Phase 1 dataset commit is 16:16.
  - Rule-1 finding, not yet fixed: `tools/build_publication_tables.py` still contains hand-typed result numbers in table notes (e.g. "Median operating time ... 19.4 ms", "49 / 50 (98.0 %)", "32.8 % (ONNX) and 30.7 % (ANSI C)", "Total unique traces = 3,167", plant B thresholds); they must be read from result files.

## Next steps (in order)

1. **Complete Plant B Dataset Generation:**
   - Wait for run_stress_plant_b_generate.bat 1200 main to complete (datasets/StressDataset_PlantB_<run>.mat).
   - Run run_stress_plant_b_generate.bat 150 OOD to generate Plant B OOD set (datasets/StressDataset_PlantBOOD_<run>.mat).
   - Verify coverage via python lstm_models/coverage_report_v4.py datasets/StressDataset_PlantB_<run>.mat.
2. **Execute Plant B Generalization Experiments:**
   - Run python tools/run_plant_b_generalization.py --mode all.
3. **Execute Plant B Closed-Loop 12-Case Test:**
   - Run matlab -batch "cd('F:\Transformer Thesis\simulations'); generate_stress_dataset_plant_b('closedloop'); exit;".
4. **Standalone Generated C Code Latency Benchmark (Phase 4.2):**
   - DONE (2026-10-28 01:39): hand-written ANSI C / C99 (`tools/relay_c/`); see Phase 4.2 in plan.
5. **Compile LaTeX Publication Tables & Update Manuscript:**
   - Run python tools/build_publication_tables.py to populate all final metrics into latex_source/latex/.
6. **Local Git Commit:**
   - Clean commit under SS-Abeer13 <155192927+SS-Abeer13@users.noreply.github.com>, strictly no git push.

### V8 option (a), step 1: v5 plant models (2026-10-28 15:21)
- `simulations/build_plants_v5.m` creates `TransformerWithCTSaturation_v5.slx` and `TransformerB_v5.slx` from the v4 files (v4 untouched). Transformer X 11 % (A) / 10 % (B), R 0.54 % / 0.5 % (X/R ~20), plant A source 0.12 ohm + 11.2 mH. CT saturation flux column x0.5 (A, knee ~9 pu) and x6 (B, knee ~108 pu; the 1 A / 2.5 ohm CT needs this to stay linear in steady state at 8.6 pu through-fault).
- Trial builds (X/R 55/40, knee 18 pu for both) are kept in `simulations/_v5_trial_xr40/` and `_v5_trial_knee18/` (not committed): plant B CTs were saturated in steady state at nominal burden (flux demand 88-124 pu, `probe_flux_demand_v5.m`).
- Results (`simulations/plant_v5_checks_A.txt`, `plant_v5_checks_B.txt`): TRUE through-fault 7.39 pu (A), 8.64 pu (B); CT steady deviation 1.7 % / 1.5 %; normal differential residual <= 0.0065 pu.
  - Plant A: C1-C6 PASS.
  - Plant B: C4 FAIL (maximum DC offset does not saturate the CT at nominal burden, 1.5 % deviation; saturation only with raised burden, C5 19.5 %), C6 FAIL by 0.02 percentage points (ratio change 2.02 % at 150 % load, 3x burden; plant A 1.98 %). Criteria not changed after the result.
- MATLAB MCP config points at `R2023a\bin\bin\win64\MATLAB.exe` (nonexistent); runs here use `matlab.exe -batch` directly.

### V8 option (a), step 2: calibration, generators, regeneration started (2026-10-28 16:26)
- Load calibration v5: `simulations/load_calibration_v5.txt|mat` (plant A), `load_calibration_plant_b_v5.txt|mat` (plant B; base 0.8658 A).
- HiZ sweeps v5 per plant: `hiz_sweep_v5_<plant>_<type>.mat`, bins `hiz_bins_v5_A.json`, `hiz_bins_v5_B.json` (plant B Rf range 3-3000 ohm; the first plant-B sweep over 0.01-100 ohm is kept in `simulations/_hiz_B_Rf_0p01_100/`, the 0.05 pu crossing was outside its range). v4 plant B had used the plant-A bins.
- Plant B chart constants (`patch_charts_plant_b_v5.m`): Yd1_Compensation I_nom 0.8232 -> 0.8658 A, ratios 201.98 / 808.58; DWT_Feature_Extraction I_base 1.8610 (the plant-A base) -> 0.8658 A. Python: `relay87t.py` plant B constants, `features12.py`, `coverage_report_v4.py` base updated.
- Generators `generate_stress_dataset_v5.m`, `generate_stress_dataset_plant_b_v5.m`: v5 models, own calibration/bins, CT burden ranges from `generator_ranges_v5.json` (chosen from `burden_sweep_v5_console.txt` before any data), new field `extFaultTruePu` (true through-fault RMS 10-50 ms after inception), timing tolerance 50 ms for `ct_stress_ext` (plant B self-test: Stress_ExtCTSat_AG 35 ms late; a CT sized for the through-fault saturates after the DC-offset flux has built up). Self-tests: plant A passed; plant B passed after the tolerance change.
- Old plant B results renamed `*_INVALID_87Tcal` (runs/20261027_v4_plant_b_zeroshot, _cross_plant, _leave_one_out; simulations/test_hybrid_relay_plant_b_results.*).
- 2026-10-28 16:23: `run_v5_generation_all.bat` started (plant A main 3040 -> A OOD 300 -> B main 1200 -> B OOD 150, auto-resume). First ETA from the generator log: ~264 min for plant A main.
- MATLAB MCP is misconfigured (`R2023a\bin\bin\win64`); MATLAB is run with `matlab.exe -batch`.

### V8 option (a), step 3: v5 datasets generated (2026-10-29 11:30)
- Plant A main `StressDataset_v5_20261028_162333.mat` (3040, 16:23-20:57), OOD `StressDataset_v5OOD_20261028_205712.mat` (300); top-ups (Inrush_Loaded 80, Overexcitation 100 and 60 with OverexcMin 1.22, Stress_ExtCTSat multi-phase 60). Plant B main `StressDataset_PlantBv5_20261028_212041.mat` (1200), OOD `StressDataset_PlantBv5OOD_20261029_010052.mat` (150), top-ups Inrush_Loaded 30, Overexcitation 60. Coverage (`*_plus_topups_coverage.txt`): all 8 criteria pass for both plants.
- Interruptions: plant B main stopped at trace 313 and OOD at 111 when processes were killed (my kill of duplicate waiter processes at 21:45; the session end on 10-29); both resumed from PARTIAL files with the same run id. The plant B over-excitation top-up crashed once (MATLAB heap corruption) and was resumed from its PARTIAL file. Logs of the interrupted parts are kept as `*_part1_*`.
- 8 of the 80 plant-A loaded-inrush top-up simulations aborted early (solver stopped, truncated identical stubs, status Failed); coverage criterion 7 now counts aborted simulations separately from duplicates (`coverage_report_v5.py`); they are excluded from training and evaluation.

### V8 option (a), step 4: plant A v5 results, deployment (2026-10-29 15:00)
- CV x3 seeds (`runs/20261029_v5_cv5_seeds`, 15 fold-models): Hybrid + AI-alone dependability 92.99 %, security 98.96 % (v4: 98.63 / 99.52); LSTM alone 97.68 / 95.60; 87T alone 80.34 / 63.41; most missed faults: Internal HiZ (hybrid 65.8 % correct).
- Final model `runs/20261029_v5_final` (thresholds AI 0.9950, solo 0.9980, dwell 20); OOD scored once: hybrid + AI-alone 98.0 % dependability / 96.0 % security. OOD block 3 label "CT burden 8-12x" is derived from `generator_ranges_v5.json`.
- Harmonic 87T on v5 (`runs/20261029_v5_harmonic87t`): per-phase restraint 85.93 % / 99.40 % (main), 93.96 % / 88.67 % (OOD).
- Deployment: `lstm_models/wt_lstm_relay.onnx` replaced by the v5 export (backup `wt_lstm_relay_BACKUP_20261029_pre_v5.onnx`; PyTorch/ONNX error 2.4e-8); `deploy_thresholds_v5.m` wrote 0.9950 / 0.9980 into both v5 models (read back from the saved files).
- Feature parity v5 (`verify_feature_parity_v5.m`, no model saved): plant A Normal / Internal A-G max error 0 / 0. Plant B first FAILED (0.448 / 7.13): the plant-B model applied the plant-A Yd1 map to the HV currents in the LSTM input path (I_diff_LSTM = K Ip - Is) while the generator and Python use Dyn11 on the LV currents. Fixed with `patch_lstm_path_plant_b_v5.m` (backup `TransformerB_v5_BACKUP_20261029_pre_lstmpath.slx`); parity now 0 / 0. The v4 plant-B closed loop was affected by this as well (results already renamed INVALID_87Tcal).

### V8 option (a), step 5: closed loops, transfer, statistics, latency, tables (2026-10-29 18:10)
- Closed loop plant A (`simulations/test_hybrid_relay_d5main|d5ood_results.*`): 23/25 and 25/25 correct; Simulink vs Python mirror 50/50 agreement, median |dt| 0.00 ms, max 0.30 ms (`simulations/closed_loop_vs_python_v5.txt`); failures: Stress_FaultInInrush #1096 tripped 59.9 ms after the fault (> 30 ms), Internal_HiZ_BC #2854 missed (max prob 0.9933 < 0.995).
- Closed loop plant B (12-case suite): 12/12 pass; the solid internal LV A-G fault trips at probability 1.0 after 15.6 ms (v4: missed, max prob 0.89; the plant-B LSTM path used the plant-A Yd1 map, fixed in step 4).
- Literature baselines `runs/20261029_v5_literature_benchmark`; statistics `runs/20261029_v5_stats` (hybrid vs unrestrained 87T and vs per-phase harmonic 87T on dependability p < 0.001; vs per-phase harmonic 87T on security p = 0.46, not significant).
- Plant B transfer (`runs/20261029_v5_plant_b_zeroshot|cross_plant|leave_one_out`): zero-shot Proposed 92.70 % dep / 88.35 % sec (89 false trips of 764; harmonic 87T 94.12 / 98.95; the false trips are concentrated in Stress_ExtCTSat_*); cross-plant pooled 94.78 / 98.22; train A -> test B 93.10 / 89.79; train B -> test A 62.51 / 97.28. 87T alone on plant B: 100 % on Normal and External solid.
- C relay code: in-place hidden-state update bug fixed in `tools/build_and_run_c_benchmark.py` (C probability disagreed with PyTorch, e.g. 0.557 vs 0.918, also for the v4 model); the parity check now uses 12 fixed random inputs. Latency re-measured with the machine idle: `runs/20261029_v5_latency` (C median 175.9 us, p99 228.9 us, max 376.9 us; the first measurement was taken while training ran and is discarded).
- Tables: `tools/build_publication_tables_v5.py` computes the numbers that were hand-typed in tables 6.1-6.6, 6.8 notes and 6.4/6.5 (SD, trace counts, OOD median, closed-loop rows, latency percentages, thresholds).

### BENCHMARK_FAIRNESS_PLAN.md Part 2: R0 and D1 (2026-10-31)
- R0 reference audit: `tools/audit_references.py` (Crossref search for all 40 entries of `latex_source/latex/main.tex`, results in `documents/reference_audit.json`), `tools/reference_audit_report.py` (decisions, fetch by DOI, `documents/reference_audit.md`, corrected `\bibitem` lines applied to `main.tex`; backup `main_BACKUP_20261031_pre_R0.tex`). Result: 10 verified as listed, 21 refer to a real paper with at least one wrong field (corrected from the Crossref record or the PDF), 9 not found (ref2, ref5, ref10, ref18, ref31, ref32, ref33, ref34, ref35): left in the bibliography with a `% R0 ... UNVERIFIED` comment because the text cites them; the citing sentences have to be replaced or dropped. `ref19` (Ngaopitakkul and Kunakorn, IJCAS 4(3), 2006) is not in Crossref and was read from the PDF. The PDFs were taken from git commit `f92ea33` into a temporary folder (not committed).
- D1 solver and sampling check: `simulations/check_solver_settings_v5.m`, `solver_settings_v5.txt`; high-rate probe `probe_highrate_v5.m` (plant A 26.6 s and plant B 27.9 s per trace at 20 kHz vs 13.7 / 11.3 s standard; 3.17 MB per trace); write-up `documents/high_rate_D1.md`. The v5 plants carry almost no energy above 1.6 kHz when noise is off (lumped models): limitation for wavelet methods that rely on kHz content.

### BENCHMARK_FAIRNESS_PLAN.md Part 2: D2 started (2026-10-31 22:26)
- Generators `simulations/generate_stress_dataset_hr_v5.m` (plant A) and `generate_stress_dataset_plant_b_hr_v5.m` (plant B): copies of the v5 generators with, in memory only, powergui 25 us (40 kHz), noise Ts 25 us and the two To Workspace blocks (CT secondary + noise + quantisation) at 50 us (20 kHz). The relay's own ZOH_1600 stays at 1600 Hz: a first version that also moved it to 20 kHz ran the relay's wavelet chart at 20 kHz and needed about 28 s per trace (ETA 27 h for plant A main); with it at 1600 Hz about 8-9 s per trace. Per-trace waveform checks are skipped (they assume 1600 Hz); before each trace the scenario name, sample seed and the parameters load, CT burden, noise, power factor, fault resistance, inception and energisation time are asserted equal to the original dataset (`Reference` option). Output: blocks of 25 traces, single precision, `datasets/hr/StressDataset_v5HR*_blk*.mat` (Ip, Is as 22001 x 3 x k, idx, scenario, seed), plus a metadata-only final file per run.
- Driver `run_v5_hr_all.sh` (one MATLAB at a time, auto-resume with Chunk 100): plant A main (3040) + four top-ups (80, 100, 60, 60) + OOD (300), plant B main (1200) + two top-ups (30, 60) + OOD (150): 5080 traces, replayed with the original run ids and arguments. Started 22:25; log `datasets/hr_resim_log.txt`.
- A second MATLAB (PID 31712, 3.7 GB) is the user's own desktop session, not part of this job.

### BENCHMARK_FAIRNESS_PLAN.md Part 2: method specs written; D2 restarted with true currents (2026-11-01 00:20)
- Specs (written before any code or result of the methods; `documents/baselines/`): `simoes2021_rtbswt_svm_spec.md`, `ngaopitakkul2006_dwt_bpnn_spec.md`, `abdusalam2022_dwt_omp_ga_spec.md`, `afrasiabi2020_acnn_spec.md`, `key2025_comdnn_disdnn_spec.md`, `alhamd2024_wavelet_lstm_spec.md`. Each lists the paper's inputs, rates, transform, features, classifier, training and decision logic with section/equation references, the UNSPECIFIED items with their fill, the deviations forced by our setup, the label mapping, the sanity check and the cost to report.
- Findings from reading the papers (to be carried into the paper text): Simões uses 15,360 Hz at 60 Hz (12.8 kHz at 50 Hz) and its second SVM targets external-to-internal evolving faults that our dataset does not contain; Ngaopitakkul classifies internal-fault types at 200 kHz and has no inrush or external-fault class (an all-zero output is added as the minimal retargeting); Abdusalam contains no random forest and is internally inconsistent (best selector BA or GA, 30/40/14/12 features, 200 vs 300 samples per cycle at 10 kHz; BA + SVM is used as the main row); Afrasiabi's text and Fig. 1 disagree on the network (500 filters of 5 x 6 vs 128 of 3 x 3; Fig. 1 followed) and its CT-compensation filter is a separate paper (Hajipour et al. 2015) that is not in the project folder; Key's Com-DNN needs the true line currents; Alhamd's proposed LSTM is bidirectional (decision after a whole 20 ms segment, reported detection times 110-170 ms).
- D2 restarted at 00:15 because Key's Com-DNN needs the undistorted line currents: the high-rate runs now also store `Tp`, `Ts` (V-I block currents interpolated to the 20 kHz grid, single precision) in every block file. The first run (725 traces without them) was moved to `datasets/hr_noTrue_partial_20261101` and `datasets/StressDataset_v5HR_20261028_162333_PARTIAL_noTrue.mat` (not used). Expected end of the whole job: about 12:30 on 2026-11-01 (8-9 s per trace, 5080 traces). A check on block 1 shows true current / CT ratio equal to the CT-secondary RMS within 1 % on a loaded Normal trace.

### 2026-11-01 18:50 - Fairness plan Part 2: D2 finished, completeness, D3, Hajipour stage
- D2 (20 kHz re-simulation, ALL_HR_DONE 2026-11-01 13:08): plant A main 3,012/3,040 + top-ups; 30 of the 3,332 kept plant-A traces have no 20 kHz copy (the re-run logged empty/short signals, flagged failed; list in documents/baselines/hr_missing_traces.txt, tools/hr_missing_manifest.py). All baselines are scored on the 3,302 traces that exist in both data sets. Plant B and OOD sets: 12 and 3 traces failed likewise (counts from the MATLAB log; manifests still to write).
- D3 (tools/d3_equivalence_check.py -> documents/baselines/d3_equivalence.txt): 432 traces (6 per scenario) decimated to 1,600 Hz and run through the proposed final model: identical trip/no-trip on 429/432 = 99.31 % (criterion >= 99 %: met), trip-time difference median 0.000 ms, p5/p95 -1.9/+3.1 ms. Noise realisations differ (noise sample time changed), so 3 discordant traces (Stress_ExtCTSat_AC, Internal_ACG, Internal_HiZ_AC) are listed in the file.
- Hajipour 2015 CT compensation reproduced (commit 975dd0e): nearly inactive on our CT-stress traces (documents/baselines/hajipour2015_ct_comp_spec.md section 6).

### 2026-11-01 23:42 - N1 (data loose ends), rules from BENCHMARK_FAIRNESS_PLAN.md
- **N1a** (tools/hr_missing_manifest_all.py -> documents/baselines/hr_missing_all.txt): failed 20 kHz re-simulations: plant A main 30/3,340 (0.90 %), A OOD 3/300, plant B main 11/1,290 (0.85 %), B OOD 1/150 (an earlier note said 12 for plant B: that was main + OOD). H1a **confirmed** at the level of scenario families (phase suffix removed): max 3.6 % (A OOD Normal 1/28), plant B main 3.1 %; every plant-A-main family <= 2.0 %. Single scenario names with n = 4-48 exceed 5 % with one failure (e.g. Internal_HiZ_BC 3/48) - I read "group" as family. One exception: plant-B OOD family InternalHV 1/14 = 7.1 %. Rule: re-run once; **not done** (one trace of 150, OOD is used once; needs a single-trace MATLAB launch). It stays excluded and the family's n is reported as 13. Decision rule fired: "every group <= 5 %" (common set for all methods) with the stated exception.
- **N1b** (tools/common_set_rescore.py -> runs/20261101_v5_common_set/summary.txt, from saved rows, no retraining): common set (3,302 traces) vs full, mean of 3 seeds, dependability / security change: hybrid + AI-alone 92.99 -> 92.95 / 98.96 -> 98.95; LSTM alone 97.68 -> 97.66 / 95.60 -> 95.57; 87T alone 80.34 -> 80.31 / 63.41 -> 63.45; harmonic 87T per-phase 85.93 -> 85.96 / 99.40 -> 99.39. H1b (< 0.3 pt) **confirmed**, largest change 0.04 pt. Rule fired: all <= 0.5 pt -> comparison tables use common-set numbers; headline stays full-set with a footnote.
- **N1c** (simulations/powergui_freq_check.txt; generator option GuiFreq, model not saved): 12 traces (8 Normal, 3 Inrush_Loaded, 1 External_ABC; the 'Only' draw, not a 1/1/1 split) at powergui Frequency 60 vs 50 Hz, identical seeds: Ip, Is, Tp, Ts identical (max abs difference 0.0 A). H1c **confirmed**. Rule fired: RMS < 0.5 % and identical decisions -> keep all data; one sentence in Limitations. Note: only one external fault was in the sample (stated, not extended).

### 2026-11-01 23:45 - N2 Simoes detector factor (rule from BENCHMARK_FAIRNESS_PLAN.md)
- tools/cache_simoes_energies.py (RT-BSWT energies of all 3,302 common-set plant-A traces, 46 s) and tools/n2_simoes_factor.py -> runs/20261101_v5_benchmark_fair/n2_simoes_factor.txt/.json. 15 fold-models, validation traces only.
- H2 (no factor meets both criteria) **confirmed**: spurious firings per Normal/over-excitation trace 395 / 54 / 22 / 10 / 3.2 / 1.3 / 0.78 for factors 5 / 10 / 15 / 20 / 30 / 50 / 100; detection 99.9 / 99.2 / 97.8 / 96.5 / 94.5 / 91.5 / 86.1 %. (Hypothesis text said 0.8 spurious at 30; on the validation sets, which include over-excitation, it is 3.2 - the qualitative statement stands.) **Rule fired: row 2** - the smallest factor meeting the spurious-firing criterion: 100 in 12 folds, 50 in 3 folds; undetected events = no trip in native mode. Row 3 (unusable) did not fire since factor 100 gives 0.78 spurious per trace. Spec amendment 9 added; SimoesMethod.select_factor implements the rule.

### 2026-11-02 09:16 - Author decisions recorded (after N1/N2)
- N1 accepted. Gap to close: re-run the single plant-B OOD InternalHV trace (1 of 14, 7.1 %) at the start of N4; if it fails again report n = 13.
- N2 accepted; consequence fixed BEFORE the Simoes results are interpreted: at the chosen factor (50-100) the detector finds only 86-92 % of events (validation, mean 86.1 % at factor 100), so Simoes' native dependability cannot exceed about 90 %; this is a property of the detector at our noise level, stated in the plan in advance and not to be explained away later. No further tuning of the Simoes detector is allowed.
- Order of work: N6a now (unattended), N3 modules meanwhile, then N4 (all six), statistics, paper.
- Noted at decision time (Simoes native, published / grid): dependability 59.9 / 69.7 %, security 95.3 / 92.2 % (runs/20261101_v5_benchmark_fair/simoes_*).

### 2026-11-02 09:56 - N1a closed: plant-B OOD trace re-run; N3 modules coded; B1 (N6a) started
- N1a gap (author decision 1): the single failed plant-B OOD trace (index 57, InternalHV_AG; run 'REDO57', generator option Redo, same seeded parameters, identity asserted against the original file) was re-simulated at 20 kHz: 1 of 1 checks passed, no timing failure, 22,001 samples, finite. Block file datasets/hr/StressDataset_PlantBv5HROOD_REDO57_blk00057_00057.mat. Plant-B OOD family InternalHV is now complete (n = 14). Plant-B OOD set = 150 traces. (The MATLAB process exited with a heap-corruption code after saving, as seen before.)
- N6a (B1) started 09:17: tools via lstm_models/benchmark_literature_models.py --epochs 25 --patience 5 (all neural same-feature models: MLP, 1D-CNN, GRU), seeds 20261021-23, runs/20261101_v5_benchmark_fair/b1_equal_budget/; epochs used per model and fold recorded in the fold JSON (meta.epochs_used). run_n6a.sh.
- Intermediate native results (plant A common set, 15 fold-models each, runs/20261101_v5_benchmark_fair/n4_progress.txt): Afrasiabi with Hajipour stage 87.06 / 89.56 % (dep / sec), without 86.41 / 88.09; Key 96.91 / 74.86; Simoes grid 69.68 / 92.20, published 59.91 / 95.31; Ngaopitakkul so far (2 of 15 folds) 27 / 99.5. Not yet compared with the proposed model, no decision rule applied yet.
- Modules coded: Ngaopitakkul (sanity passes without measurement noise, fails with it, spec amendment 8), Abdusalam (features cached in parallel), Alhamd (search once, 25 epochs): spec amendments committed 6a0b943.

### 2026-11-02 12:27 - GPU enabled; Abdusalam and Alhamd runs
- GPU: the system PyTorch is CPU-only (2.3.1+cpu); RTX 5060 Ti (sm_120) needs CUDA 12.8 wheels. Created venv F:/venv_gpu (system site packages + torch 2.9.1+cu128; pip temp/cache on F: because C: had 4.5 GB free). Used for: B1 benchmark (--device cuda; restarted 12:08, cached folds kept), Alhamd (BiLSTM). sklearn-based methods stay on CPU.
- Abdusalam (features cached in parallel, 7,457 s; CV on CPU, about 1 min per fold): BA+SVM (main row) 76.06 % dep / 99.93 % sec on 13 of 15 folds so far; further variants running.
- Alhamd: first run with the reduced CPU budget (kept as alhamd_reduced_budget): 85.79 / 54.91 %. With the GPU the paper's budget became affordable, so the run was repeated with the original spec budget (per-fold 12-configuration search, up to 200 epochs); reason is compute, not the result; both runs are reported (spec amendment 9).
- Ngaopitakkul finished 15 fold-models: 27.71 % dep / 99.26 % sec (native). Key 96.91 / 74.86, Afrasiabi 87.06 / 89.56 (with Hajipour stage), 86.41 / 88.09 (without). No decision rule applied yet.

### 2026-11-02 21:55 - D-B1 fix, D-N4 infrastructure and first like-for-like results (work in progress)
- **D-B1.** Cause of the crash: checkpoints trained earlier on CPU were loaded with map_location=device but the model object was not moved (benchmark_literature_models.py, three load branches); fixed (`.to(device)` after load_state_dict). Seed 20261021: fold 2 checkpoints deleted (CPU-trained, would have lacked epochs_used), run restarted on the GPU (run_n6a.sh); fold 1 kept (CPU-trained, epochs recorded). Seed 20261021 is at fold 3-4 of 5; the N6a rule on all 3 seeds is evaluated when it finishes. Note recorded for the rule: the B1 benchmark models use window stride 8 (default of the script) while the deployed LSTM of the CV used stride 4; B2 uses stride 4 for every model.
- **D-N4 infrastructure.** (1) score_stream() added to the six method classes (decision times + score in [0, 1]; event-based methods: one score per detector firing). (2) lstm_models/baselines/modeb.py: 20-sample dwell (12.5 ms), threshold grid and plateau rule of train_trace_split.tune_threshold (dependability within 2 pt, security within 1 pt, centre in logit space) on the validation traces of each fold, plus the relay mirror's high-set element for every method; event-based methods: first firing above the threshold, no dwell. (3) tools/run_full_eval.py: one pass per method gives native AND mode-b rows for 3 seeds x 5 folds (same folds), and a final model (85/15 split, seed 20261021) scored ONCE on the plant-A OOD set and the plant-B main set (zero-shot, logic and threshold frozen). Plant-B metadata cache: tools/build_plantb_trace_cache.py (1,289 traces, as in the zero-shot run; 1,278 have a 20 kHz copy). OOD plant A: 297 of 300. Runs: runs/20261101_v5_benchmark_fair/full/<method>/; summary tools/n4_full_summary.py -> n4_full_summary.txt. (4) tools/measure_latency_baselines.py written; to be run on an idle machine after the jobs finish. (5) tools/n5_statistics.py (exact McNemar on (seed, fold, trace), Holm over all tests, per-seed sign stability, fold-model sd) written, waits for the CV runs.
- **Results so far** (n4_full_summary.txt; native vs mode b, dependability / security): Simoes grid CV 69.68 / 92.20 vs 76.84 / 72.08, OOD 70.95 / 73.83 vs 75.00 / 60.40, plant B zero-shot 83.23 / 89.43 vs 86.71 / 71.73; Abdusalam BA+SVM CV 76.38 / 99.95 vs 79.23 / 92.91 (reproduces the earlier native run exactly), OOD 83.11 / 93.96 vs 84.46 / 86.58. Afrasiabi (4 folds so far) 85.70 / 87.48 vs 86.81 / 100.0, Alhamd (2 folds) 97.59 / 81.90 vs 97.59 / 98.73, Ngaopitakkul (8 folds) 27.36 / 99.34 vs 38.35 / 97.48. The rule "native vs like-for-like > 5 pt: report both rows" fires for every method so far (mostly on security); decision pending the end of the runs. Still running: Afrasiabi, Ngaopitakkul, Alhamd, Key (CV + final); Abdusalam finishing plant B; Simoes done.
- Not started yet: D-N5 (waits for the CV runs), D-B2.

### 2026-11-02 23:11 - D-B1 finished: N6a rule on all 3 seeds
- Seed 20261021 re-run completed on the GPU (all 5 folds, summary runs/20261101_v5_benchmark_fair/b1_equal_budget/seed_20261021/literature_benchmark_summary.json). Standalone dependability / security, same-feature models vs standalone LSTM, per seed (seed 21 / 22 / 23): LSTM 97.92 / 96.78, 97.04 / 94.61, 98.08 / 95.42; 1D-CNN 97.52 / 97.08, 96.16 / 96.63, 97.84 / 97.43; GRU 98.16 / 96.83, 97.36 / 95.37, 97.44 / 94.67; MLP 97.76 / 96.43, 96.64 / 96.28, 97.36 / 96.98. Hybrid mode: proposed 93.92 / 99.14, 94.24 / 98.69, 90.81 / 99.04; CNN 93.84 / 98.84, 93.21 / 99.40, 94.16 / 99.30; GRU 93.76 / 98.89, 93.92 / 98.79, 94.00 / 98.84.
- **Rule (N6a): fires.** The GRU is within 1 pt of the LSTM on both metrics (standalone) in all 3 seeds (differences GRU minus LSTM, seed 21: +0.24 / +0.05; seed 22: +0.32/+0.76; seed 23: -0.64/-0.75), the 1D-CNN in seed 21 only strictly (it is better on security by 2.0 / 2.0 pt in seeds 22 / 23, i.e. not worse). Seed 1 does not change the picture; the condition (>= 2 of 3 seeds) holds -> **B2 is required**, and the paper states that the choice of LSTM is not decisive. Epochs used per model and fold are in each fold JSON (meta.epochs_used).

### 2026-11-03 08:17 - D-N4 finished, latency measured, D-N5 statistics (hypotheses and decision rules from BENCHMARK_FAIRNESS_PLAN.md)
- **D-N4 complete** (runs/20261101_v5_benchmark_fair/n4_full_summary.txt; CV = 3 seeds x 5 folds, common set; OOD and plant B = one final model, scored once, plant B zero-shot with frozen logic and threshold). Native / like-for-like (dependability / security): Key CV 96.99 / 75.28 -> 97.23 / 99.56, OOD 96.62 / 78.52 -> 97.97 / 95.97, plant B 98.16 / 69.75 -> 96.93 / 98.94. Alhamd CV 96.53 / 82.91 -> 97.93 / 98.17, OOD 97.30 / 87.25 -> 95.27 / 95.30, plant B 92.64 / 83.75 -> 89.98 / 96.17. Rows for Afrasiabi, Abdusalam, Simoes, Ngaopitakkul as in the previous entry (completed unchanged for the CV).
- **Rule "native vs like-for-like > 5 pt": fires for all six methods** (security, for Ngaopitakkul dependability +11 pt): both rows are reported, native = the "as intended" row. The like-for-like mode raises the security of the neural methods to 95.3-99.6 % at 87.3-97.9 % dependability but lowers Simoes (72.1 %) and Abdusalam (92.9 %).
- **H4.4 (every learned method loses security on plant B): partly REJECTED.** Native plant-B security: Afrasiabi 75.17, Key 69.75, Alhamd 83.75, Simoes 89.43 (loses), but Abdusalam 99.74 (at 71.37 % dependability) and Ngaopitakkul 97.62 (at 28.02 %). In like-for-like mode with plant-A thresholds Afrasiabi 99.87 and Key 98.94 keep security >= 98 %, Alhamd 96.17, Abdusalam 95.51. Rule fired: "a reproduction transfers to plant B with security >= 98 %": **reported prominently** - the plant-B security loss (88.35 % for the proposed hybrid zero-shot) is therefore not an LSTM-specific weakness that every other method shares; the transfer comparison has to be made per mode and per dependability level.
- **H4.5 (latency; tools/measure_latency_baselines.py, idle machine, single thread, largest search-space architectures, random weights):** per decision median / budget: Afrasiabi CNN 116.7 / 1,250 us pass; Key 37.0 / 312.5 us pass; Ngaopitakkul 3.3 / 50 us per sample pass; Simoes wavelet 7.5 / 78.1 us pass (SVM 1 at a detection 498 us, event-based, not per sample); **Alhamd 1,809 / 1,667 us: not real-time in this implementation (largest config; borderline)**; **Abdusalam feature extraction 608,796 us per decision window vs 2,500 us: not real-time (OMP over five dictionaries)**. The Hajipour stage per sample in the file (0.1 us) was measured on a signal without saturation and is not representative; stated as such. H4.5 REJECTED for Abdusalam (and borderline for Alhamd's largest config).
- **D-N5** (tools/n5_statistics.py -> n5_statistics.txt/.json; exact McNemar on 3,717 fault / 5,910 healthy (seed, fold, trace) pairs, Holm over 24 tests). Proposed hybrid vs reproduction (native): dependability Key +4.04 pt and Alhamd +3.58 pt (reproduction higher, p_Holm 1.8e-15 and 2.1e-12), Afrasiabi -6.24, Abdusalam -16.57, Simoes -23.27, Ngaopitakkul -65.24 (all p_Holm < 1e-45); security Key -23.67, Alhamd -16.04, Afrasiabi -10.32, Simoes -6.75 (all p_Holm < 1e-79), Abdusalam +1.00 (reproduction higher, p_Holm 1.5e-14), Ngaopitakkul +0.30 (p_Holm 0.126, n.s.). LSTM alone vs Key dependability: -0.67 pt, p_Holm 0.126 (n.s.); vs Alhamd -1.13 (p_Holm 5.4e-3). No per-seed sign changes. Fold-model sd > 3 pt (range reported next to the mean): Afrasiabi security 4.39, Key security 8.62, Alhamd security 4.36, Ngaopitakkul dependability 3.39.
- **H5 confirmed** (differences >= 1.5 pt dependability and >= 0.7 pt security are significant after Holm; Ngaopitakkul's +0.30 security is not). **N4 main rule: claim B** (Key and Alhamd better on dependability, much worse on security; Abdusalam better on security, much worse on dependability; no method better on both). No claim wording changed; the headline waits for B2 (author's order). Statement supported by the tests: the proposed hybrid is the only evaluated method with dependability >= 92.9 % and security >= 98.9 % simultaneously.

### 2026-11-03 08:31 - D-B2 started (equal hyperparameter search)
- tools/run_b2_search.py (GPU venv). Search spaces = the plan's table (fixed before running), 12 random configurations per model with a fixed seed (SEARCH_SEED 20261102 + model name), the SAME training routine for all six models (25 epochs, patience 5 on validation AUC, AdamW, batch 256, window stride 4), proposed LSTM included (attention pooling kept; trained with benchmark_literature_models.train_torch_model, which is the routine of train_trace_split.train). Compute-saving option of the plan applied identically to every model: search on the inner validation split of folds 1-3 of seed 20261021, score = mean validation window AUC; the chosen configuration then goes to all 3 seeds x 5 folds ('final' stage: standalone and hybrid rows, thresholds tuned on validation). Output runs/20261101_v5_benchmark_fair/b2_equal_search/.
- Search so far: SVM (12/12) validation AUC 0.971-0.972 range, RF 0.996-0.998, ANN config 1 0.9987; CNN, GRU, LSTM still to run. The deployed LSTM and the closed-loop / Simulink results stay as they are, whatever the search finds.

### 2026-11-03 09:08 - Hypothesis H5b logged BEFORE D-N5b (BENCHMARK_FAIRNESS_PLAN.md "Review and decisions - 2026-11-03 09:00")
- **H5b:** Key like-for-like is significantly better than the proposed hybrid on dependability and not significantly worse on security (CV plant A, exact McNemar on (seed, fold, trace), Holm over all 48 tests = 24 native + 24 like-for-like). Also written down: prediction for B2 + D-N5b together - every classifier inside the dual-path gives about 93-94 % dependability and >= 98.8 % security. Decision table of D-N5b exactly as in the plan (claim C -> pre-registered "hybrid with X" for that method only, Key first; significantly better on one and worse on the other -> claim B with the like-for-like table in the main text; no significant differences -> claim B with the same sentence). Order: D-N5b and D-diag (CPU) -> D-lat (after B2) -> B2 -> claim-C extra if triggered. No thresholds are changed.

### 2026-11-03 09:10 - D-N5b (like-for-like rows, Holm over 48 tests) and D-diag; decision table applied
- **D-N5b** (tools/n5_statistics.py modeb -> runs/20261101_v5_benchmark_fair/n5_statistics_modeb.txt/.json): exact McNemar on (seed, fold, trace) pairs (3,717 fault / 5,910 healthy), proposed hybrid and LSTM alone vs each method's native and like-for-like rows, Holm over all 48 tests. Native p-values re-reported under 48 tests: no native conclusion changes (largest change: LSTM alone vs Key dependability p_Holm 0.126 -> 0.252, still n.s.).
- Like-for-like vs proposed hybrid (92.95 / 98.95), dependability / security difference in pt and p_Holm(48): **Key +4.28 (3.9e-24) / +0.61 (1.1e-3); Alhamd +4.98 (6.1e-36) / -0.78 (1.3e-3)**; Afrasiabi -5.68 (5.3e-47) / +0.69 (5.5e-6); Abdusalam -13.72 / -6.04; Simoes -16.12 / -26.87; Ngaopitakkul -54.56 / -1.47 (all p_Holm < 1e-6). Like-for-like vs LSTM alone (97.66 / 95.57): Key -0.43 (n.s., 0.31, per-seed sign changes: 'unstable') / +3.99 (2.3e-49); Alhamd +0.27 (n.s., 0.36) / +2.61 (3.6e-19); Afrasiabi -10.38 / +4.08.
- **H5b CONFIRMED** (and exceeded): Key like-for-like is significantly better than the proposed hybrid on dependability and is not significantly worse on security - it is significantly better on security as well (+0.61 pt). Per-seed signs of the Key-vs-hybrid differences are stable.
- **Decision table, row 1 fires for Key: claim C.** Key like-for-like is significantly better on both metrics. For Alhamd row 2 applies (better on dependability, significantly worse on security -0.78 pt): claim B for Alhamd, its like-for-like table goes in the main text with the sentence "With our relay logic, Key's / Alhamd's classifier matches or exceeds our LSTM; the gain comes from the supervisory architecture". **Action fixed by the table: run the pre-registered extra evaluation for Key only: "hybrid with Key"** = the identical dual-path logic of the proposed hybrid (87T vote AND confirmed classifier output >= AI_Threshold, or confirmed output >= AI_Solo_Threshold, or high-set; plateau-rule thresholds tuned on validation, dwell 20), 3 seeds x 5 folds, OOD once, plant-B zero-shot with frozen thresholds; the Key classifier output is the only change. Wording of the claim stays unchanged until this and B2 are done. Started after this entry.
- **D-diag** (tools/ddiag_falsetrip_paths.py -> runs/20261101_v5_benchmark_fair/plantB_falsetrip_paths.txt; the saved trip_path_check.json was also regenerated by re-running tools/plantb_trip_path_v5.py and is byte-identical): of the 89 plant-B false trips of the deployed hybrid (764 detectable healthy traces), **87 (97.8 %) were first caused by the AI-alone (solo) path**, 2 by the gated path, 0 by the high-set; 62 are external faults with CT saturation, 23 solid-external, 4 external-in-inrush. Switching the solo path off (same thresholds): security 99.21 %, dependability 90.47 % (11 of 493 faults, 2.2 %, are tripped only by the solo path). Per the decision table: the limitations say "the solo path is the transfer weakness"; **no threshold was changed** (that would be tuning on plant B).

### 2026-11-03 09:41 - Review 2026-11-03 09:45: H6 logged BEFORE the Key-hybrid results are final; RAM check; unique B2 configurations
- **H6 (pre-registered, written before any "hybrid with Key" result is final; the first fold, seed 22 fold 1, 94.1 / 100.0, is already known and was not used to set this):** "Hybrid with Key reaches >= 93 % dependability and >= 99 % security on the plant-A CV and is not significantly worse than the proposed hybrid on either metric." Tests: hybrid with Key vs proposed hybrid, dependability and security, exact McNemar on the same (seed, fold, trace) pairs, **Holm over 50 tests** (the 48 of D-N5b + these 2); plus OOD and plant-B rows (single final model, descriptive, Wilson intervals). Decision rules fixed in the plan: significantly better on >= 1 metric and not significantly worse on the other -> claim C final (Key-hybrid = best configuration on this bench; the LSTM hybrid stays the deployed / closed-loop configuration, no closed-loop run with Key); no significant difference -> architecture claim in its strongest form (same operating point with two classifiers); significantly worse on >= 1 metric -> report it with "the gate's benefit depends on the classifier's calibration". No headline until the statistics are done.
- **RAM check (step 1):** python processes now: key_hybrid_cv0/1/2 + key_hybrid_final + B2 = 2,570 + 1,646 + 1,598 + 1,595 + 1,440 MB = **8.8 GB** in total (largest 2.6 GB each), system free 9.0 of 31.6 GB (the rest is other applications). Threshold given for this step: 12 GB -> **no throttling**. (CLAUDE.md's per-process 4 GB limit is respected by every process; the 12 GB total limit of this instruction is not reached.) The jobs are resumable per fold; timings under contention are not compared across methods and D-lat is run on an idle machine.

### 2026-11-03 09:42 - Unique B2 configurations (step 3) and gated-only ablation (step 5); RAM instruction
- **RAM:** author's follow-up: ignore the RAM instruction when usage is within the acceptable range. It was (python total 8.8 GB < 12 GB at 09:41; re-checked just now, see the plan's running state), so nothing was throttled and nothing is to be restarted for RAM reasons. Only the 'final' Key-hybrid process was restarted (at fit start, no result lost) to add the per-path false-trip counts and the gated-only counterfactual for plant B / OOD.
- **B2 unique configurations** (runs/20261101_v5_benchmark_fair/b2_equal_search/unique_configs.json, from the deterministic sampler; the sampler is NOT changed mid-run): of 12 drawn, unique = SVM 10, RF 11, ANN 11, 1D-CNN 10, GRU 11, **proposed LSTM 10**. The LSTM does not have more unique configurations than any baseline (it has the fewest, tied with SVM and CNN), so the unequal budget, if anything, works against the proposed model; stated in the Table B note. (search_results.json is rewritten by the running search; the unique counts are merged into it when the search ends.)
- **Gated-only ablation of the proposed hybrid** (tools/gated_only_ablation.py -> gated_only_ablation.txt/.json; from saved decisions, no retraining; post-hoc, labelled ablation, not adoption). Plant-A CV (common set): deployed 92.95 / 98.95 vs gated-only 88.43 / 99.42: **dependability -4.52 pt** (168 traces tripped only with the AI-alone path, 0 the other way, exact McNemar p = 5e-51), security +0.47 pt (28 / 0, p = 7e-9). OOD (final model, once): 97.99 / 96.00 deployed vs 94.63 / 98.67 gated-only. Plant B zero-shot (same thresholds): 92.70 / 88.35 vs 90.47 / 99.21. **Correction to the plan's wording:** the plan says the AI-alone path "buys about 2 pt of dependability"; that is the plant-B number (2.2 pt). On the plant-A CV it is 4.5 pt (OOD 3.4 pt); the discussion must say "2-5 pt (2.2 on plant B, 4.5 on the plant-A CV)". The practical recommendation (disable the solo path on an unseen plant until retraining) stays labelled as a post-hoc counterfactual; the deployed logic remains the main result everywhere.

### 2026-11-03 13:47 - "Hybrid with Key" finished; Holm-50 decision table applied (H6)
- Runs: runs/20261101_v5_benchmark_fair/full/key_hybrid/ (15 CV folds + final OOD / plant B), tools/run_key_hybrid.py (same dual-path logic as the proposed hybrid via benchmark_literature_models.rows_for / tune_variant; Key's Dis-DNN internal-fault probability sampled at the relay's 1,600 Hz decision instants; thresholds by the plateau rule on each fold's validation traces: AI 0.15-0.7, solo 0.9-0.95). Statistics tools/n5c_keyhybrid.py -> n5_statistics_keyhybrid.txt/.json, Holm over 50 tests (the 48 of D-N5b + 2).
- **Plant-A CV (3,717 fault / 5,910 healthy pairs):** proposed hybrid 92.95 / 98.95 vs hybrid with Key **94.11 / 99.86**: dependability **+1.16 pt** (discordant 68 / 111, p = 1.6e-3, **p_Holm50 = 9.7e-3**), security **+0.91 pt** (8 / 62, p_Holm50 = 2.4e-10). Fold-model mean +- sd: 94.13 +- 2.37 (min 90.1) / 99.86 +- 0.36 (min 99.0). **Per-seed signs:** security +0.66 / +1.12 / +0.96 (stable); **dependability -0.16 / 0.00 / +3.63 (changes sign; the pooled gain comes from seed 3) -> per the N5 rule it is reported as "unstable across splits"**.
- **H6 CONFIRMED:** dependability 94.13 % >= 93 %, security 99.86 % >= 99 %, not significantly worse on either metric (it is significantly better on both).
- **Decision rule fired (row 1): significantly better on >= 1 metric, not significantly worse on the other -> claim C is final.** Caveats that go with it, fixed now: the security advantage is stable over the 3 seeds; the dependability advantage is significant after Holm-50 but unstable across seeds, so the text claims "higher security, dependability at least equal" and does not claim a dependability gain. The proposed LSTM hybrid stays the deployed / closed-loop configuration (Simulink closed-loop results are with the LSTM); no closed-loop run with Key (not pre-registered; future work).
- **OOD (final model, once, descriptive):** hybrid with Key 97.97 % [94.2, 99.3] (n = 148) / 95.30 % [90.6, 97.7] (n = 149) vs proposed hybrid 97.99 / 96.00. **Plant B zero-shot (thresholds frozen from plant A):** hybrid with Key 95.50 % [93.3, 97.0] (n = 489) / **99.87 % [99.3, 100.0]** (n = 757) vs proposed hybrid 92.70 / 88.35. Per-path check (same logic as D-diag): the Key hybrid's plant-B false trips: 1 of 757, first path = solo 1, gate 0, high-set 0; gated-only counterfactual 94.07 / 100.0. On OOD: 7 false trips, all via the gated path; gated-only 94.59 / 95.30. So the solo path is not a transfer weakness for Key's classifier; the weakness belongs to the LSTM's solo-path calibration (the 'gate's benefit depends on the classifier's calibration').
- B2 search finished (runs/20261101_v5_benchmark_fair/b2_equal_search/chosen_configs.json; unique counts merged into search_results.json): best / worst mean validation AUC per model SVM 0.99300 / 0.97045, RF 0.99870 / 0.99607, ANN 0.99897 / 0.99786, 1D-CNN 0.99925 / 0.99806, GRU 0.99888 / 0.99766, LSTM 0.99899 / 0.99691; the chosen LSTM is hidden 128, 2 layers, dropout 0.2, lr 3e-3 (the deployed one is 64 / 2 / 0.22 / 1e-3). B2 final stage (3 seeds x 5 folds, GPU) started. Next: B2 statistics, D-lat on the idle machine, N6c, then N8. No headline written yet.

### 2026-11-03 17:53 - D-B2 finished: Table B (tuned, equal budget) and statistics
- Runs: runs/20261101_v5_benchmark_fair/b2_equal_search/ (final_seed*_fold*.json, 15 fold-models per model, GPU), tools/b2_summary.py -> b2_summary.txt/.json. All six models: 12 random configurations (10-11 unique, LSTM 10), same routine (25 epochs max, patience 5; epochs actually used about 10 per neural model), stride 4, config search on folds 1-3 of seed 20261021, chosen config trained on all 15 fold-models.
- **Table B, tuned** (standalone dep / sec; hybrid dep / sec; common set): SVM 90.93 / 90.41; 87.01 / 97.73. RF 97.07 / 95.45; 93.49 / 99.49. ANN 97.69 / 97.14; 94.92 / 99.20. 1D-CNN 97.96 / 97.28; **95.75 / 99.02**. GRU 98.01 / 97.28; 95.59 / 98.82. LSTM (tuned: hidden 128, 2 layers, dropout 0.2, lr 3e-3) 98.44 / 97.26; 93.60 / 99.10. Deployed LSTM (default config): 97.66 / 95.57; 92.95 / 98.95.
- **Statistics** (exact McNemar on (seed, fold, trace); first family of 12 tests as planned; a second family - every tuned hybrid vs the DEPLOYED hybrid - was added after seeing the first and is labelled post-hoc; Holm over all 22 reported): tuned LSTM hybrid vs deployed hybrid +0.65 / +0.15 pt, not significant (p_Holm 0.79 / 1.0): tuning the LSTM changes nothing. vs the deployed hybrid: **1D-CNN hybrid +2.80 pt dependability (p_Holm 1.3e-17), +0.07 security (n.s.)**; **GRU hybrid +2.64 (5.4e-15), -0.14 (n.s.)**; ANN hybrid +1.96 (3.4e-8), +0.25 (n.s.); RF hybrid +0.54 dependability (n.s.), +0.54 security (p_Holm 4.5e-3); SVM hybrid -5.95 / -1.22 (both significant). The three same-feature hybrids' security differences change sign between seeds ('unstable').
- **Rule (plan decision 5, B2 + D-N5b): fired.** A same-feature model in hybrid mode (1D-CNN, GRU, ANN) is significantly better than the proposed hybrid on dependability and not worse on security. The headline therefore names the **dual-path architecture**, not the LSTM (claim-C wording); no extra evaluation is needed because Table B already contains those hybrids. My prediction in the plan ("every classifier about 93-94 % / >= 98.8 % inside the dual-path") was **partly rejected**: RF, ANN, CNN, GRU, LSTM all have security 98.8-99.5 % as predicted, but dependability ranges 93.5-95.8 % (CNN / GRU above the range) and SVM is clearly worse (87.0 / 97.7). Together with D-N5b: Key-hybrid 94.11 / 99.86 has the highest security, 1D-CNN hybrid 95.75 / 99.02 the highest dependability among the tuned hybrids; no direct test between them was pre-registered (descriptive: two operating points). Statistics are now complete; headline wording still waits for N6c (tuned harmonic 87T) and the author's reading of this log.


### 2026-11-03 17:55 - N6c fills fixed before running (hypothesis H6c is already in the plan)
- H6c (plan): tuning raises the harmonic 87T dependability by 2-5 pt with security >= 99 %; the hybrid dependability lead stays significant (>= 3 pt). Fills for the unspecified details of the plateau rule over the 3-D grid (pickup {0.2, 0.3, 0.4} x k2 {0.12, 0.15, 0.20} x k5 {0.25, 0.35}), chosen now: keep settings whose validation security is within 1 pt of the best, take the best dependability D* among them, keep those within 2 pt of D*, return the member closest to the centroid of that set in grid-index space (ties: higher validation dependability, then the textbook setting). Tests: Holm over 4 (textbook and tuned vs the deployed hybrid, dependability and security), exact McNemar on (seed, fold, trace). Script tools/n6c_tuned_harmonic.py; run after D-lat (idle machine).


### 2026-11-03 23:41 - D-lat (Alhamd trained configuration) and N6c (tuned harmonic 87T): results and decision rules
- **D-lat** (tools/dlat_alhamd.py -> runs/20261101_v5_benchmark_fair/latency_alhamd_trained.txt; idle machine, single thread CPU, features of 5 new samples + BiLSTM 60x48, 500 calls). The per-fold chosen configurations had not been stored, so the two fits that matter were repeated (same seeds, GPU) and the configuration each per-fold search selected was timed: seed 20261021 fold 1: hidden 128, 1 layer, dropout 0.2, lr 0.03 -> median 1,166 us (p99 1,747 us); final-model split: hidden 128, 1 layer, dropout 0.1, lr 0.03 -> median 1,169 us (p99 1,674 us); the largest configuration of the search space (hidden 128, 2 layers, earlier measurement) 1,799 us. Budget 1,667 us (decision every 5 samples at 3 kHz). **Rule: the trained configurations are under the budget (median 70 % of it, p99 at / just above it), so the "not real-time" label for Alhamd is dropped**; it is reported as "meets its budget in median (trained configuration); the largest search-space configuration would not". Abdusalam stays "not real-time" (OMP features, about 240 x over the budget).
- **N6c** (tools/n6c_tuned_harmonic.py -> n6c_tuned_harmonic.txt/.json; fills fixed before running, see the previous entry; 3 seeds x 5 folds, common set, Holm over 4 tests). Chosen settings over the 15 fold-models: pickup 0.2 pu always; k2/k5 = 0.2/0.25 (9 folds) or 0.15/0.25 (6 folds). Textbook 0.30/0.15/0.35: 85.96 / 99.39 (reproduces the earlier 85.93 / 99.40). **Tuned on validation: 91.18 / 99.07.** Proposed hybrid 92.95 / 98.95. Tuned harmonic vs hybrid: dependability **-1.78 pt** (discordant 138 / 72, p_Holm4 1.9e-5; per-seed -2.66, -2.82, **+0.16**: sign changes -> 'unstable across splits'), security **+0.12 pt** (47 / 54, p_Holm4 0.55, not significant). Textbook vs hybrid: -6.99 pt dependability, +0.44 pt security (p_Holm4 5.8e-69, 1.2e-2). By family (dependability): Internal_HiZ (n = 459) hybrid 65.4, tuned harmonic 62.1, textbook 51.0; other internal faults (n = 3,258) hybrid 96.8, tuned 95.3, textbook 90.9.
- **H6c:** dependability gain from tuning +5.2 pt (predicted 2-5: marginally above), security 99.07 % (>= 99 % as predicted); the hybrid's lead stays significant (p_Holm4 1.9e-5) but is **1.78 pt, below the predicted >= 3 pt**: **partly rejected.**
- **N6c decision table: the row "the gap drops below 3 pt (or is no longer significant)" fires -> the dependability claim is weakened to the measured gap (1.78 pt vs the tuned conventional relay, unstable across seeds; 7.0 pt vs the textbook settings), the headline is the architecture and the evaluation, and the HiZ-specific gain is reported per bin (hybrid +3.3 pt on Internal_HiZ, +1.5 pt on other internal faults, vs the tuned harmonic 87T).** The tuned harmonic 87T is as secure as the hybrid (99.07 vs 98.95, n.s.). Both conventional rows (textbook and tuned) are reported in Table A/B. The third row (security below 99 %) did not fire.
- Status: all statistics requested in the review (D-N5, D-N5b, Holm-50, B2, N6c) are complete; the claim wording is now to be derived from this log (N8) and read by the author first. Still open: N7 references (hard gate).


### 2026-11-04 00:08 - D-N8a (post-hoc, added after N6c): architecture instances vs the validation-tuned harmonic 87T
- tools/n8a_instances_vs_tuned_harmonic.py -> runs/20261101_v5_benchmark_fair/n8a_instances_vs_tuned_harmonic.txt/.json (needs n6c_tuned_rows.json, written by a re-run of tools/n6c_tuned_harmonic.py; the re-run output is byte-identical to the earlier n6c_tuned_harmonic.txt). Exact McNemar on (seed, fold, trace) pairs (3,717 fault / 5,910 healthy), hybrid mode of each instance vs the tuned harmonic 87T (91.18 / 99.07), **Holm over 16 tests = these 12 + the 4 of N6c; labelled post-hoc, added after N6c**.
- Dependability difference (instance minus tuned harmonic), p_Holm16: 1D-CNN +4.57 pt (3.0e-37), GRU +4.41 (3.3e-31), ANN +3.74 (2.4e-27), Key +2.93 (1.0e-18), tuned LSTM +2.42 (1.3e-7), RF +2.31 (4.3e-13). **6 of 6 instances significantly higher; range +2.31 to +4.57 pt; the per-seed signs are all positive.** Security difference: Key +0.80 pt (p_Holm16 9.8e-9) and RF +0.42 (1.1e-2) significantly higher; 1D-CNN -0.05, GRU -0.25, ANN +0.14, tuned LSTM +0.03 not significant (per-seed signs change: 'unstable'); no instance significantly lower. Per the plan the headline may cite this only as a range over the six instances.
- Reading flagged for the author (from saved numbers, no new experiment): the like-for-like rows (no 87T vote, no solo path) of Key (97.23 / 99.56) and Alhamd (97.93 / 98.17) are as secure as or more dependable than the corresponding hybrids (Key hybrid 94.11 / 99.86), i.e. for a well-calibrated classifier the 87T gate costs about 3 pt of dependability for +0.3 pt of security, whereas for the LSTM it buys +3.4 pt of security (LSTM alone 97.66 / 95.57 -> hybrid 92.95 / 98.95) at -4.7 pt of dependability. The wording of D-N8b must not claim that the 87T gate is what makes a classifier secure.
