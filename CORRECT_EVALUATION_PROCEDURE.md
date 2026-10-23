# Correct Evaluation Procedure — WT-LSTM Hybrid 87T Relay

**Purpose.** Make the LSTM evaluation valid again after the LV-CT calibration fix.
The current evaluation is **not valid** because the model was trained on features from
a different pipeline than the features it is now tested on. This document explains the
mismatches, the governing principle, and the exact step-by-step fix.

---

## 1. Why the current evaluation is invalid

Empirical result (from `evaluate_simulated_cases_v2.py`, training-consistent inference):

| Case | Expected | LSTM p(final-seq) | Decision | Result |
|------|----------|-------------------|----------|--------|
| Normal Operation | BLOCK | 1.0000 | TRIP | **FAIL** |
| Magnetizing Inrush | BLOCK | 0.0038 | BLOCK | PASS |
| Internal A-G Fault | TRIP | 1.0000 | TRIP | PASS |
| External 3Φ Fault | BLOCK | 1.0000 | TRIP | **FAIL** |

The model false-trips on Normal and External. This is a **train/test distribution
mismatch**, not a model-capacity problem (its held-out test AUC is 0.983). Three concrete
inconsistencies were found:

### 1a. Calibration date mismatch
- Training features: `datasets/LSTM_Features_Combined_20260601_024803.mat` — built **2026-06-01**
  from stress datasets generated **2026-05-31**.
- Model checkpoint: `runs/20260601_lstm_training/...best.pth` — trained **2026-06-01**.
- Test features: `simulations/simulated_test_features.mat` — built **2026-07-17**, i.e.
  **after** the LV-CT per-unit calibration fix.

The calibration fix changed the differential current, so the test features live in a
different distribution than the training features.

### 1b. Differential-definition mismatch (the deep one)
- **Training** (`datasets/FeatureExtractor.m`, line ~195): `I_diff = Ip - Is` — raw
  primary minus secondary, **no Yd1 phase compensation, no per-unit normalization**.
- **Test / inference** (Simulink `Yd1 Compensation` → `chart_11` DWT): differential is
  formed from **Yd1-compensated, per-unit** currents
  (`M_Yd1 * I_hv_pu` vs `I_lv_pu`).

The DWT therefore operates on two *different signals* between train and test, even
before the calibration date issue. This alone guarantees misclassification.

### 1c. Decision-rule mismatch (minor — already addressed)
- Training uses **one full `[1569 × 9]` sequence per scenario**.
- The original `evaluate_simulated_cases.py` ran the model on **1601 rolling buffers and
  took the max probability** (including partial / zero-padded early windows), which
  over-triggers. `evaluate_simulated_cases_v2.py` fixes this by scoring the completed
  final window (training-consistent). *Note: this fixed Inrush but not Normal/External,
  confirming 1a/1b are the dominant causes.*

### What is already consistent (good)
The DWT itself matches on both sides: db4, 2-level, 32-sample (1-cycle @ 1600 Hz) window,
`1601 − 32 = 1569` timesteps, 9 features `[E_D1,E_D2,E_A2]×3 phases`, `log1p` scaling.

---

## 2. Governing principle

> Training features and test features must be produced by **one identical pipeline** —
> same calibration, same differential definition, same DWT, same windowing, same input
> scaling, same sequence representation and decision rule — and the **test scenarios must
> be independent of the training set**.

The safest way to guarantee this: **generate BOTH training and test features from the
same Simulink model's `DWT_Features` output.** Do not maintain a second, divergent
feature path in `FeatureExtractor.m`.

---

## 3. Step-by-step procedure

### Step 0 — Freeze the corrected model
- Confirm `simulations/TransformerWithCTSaturation.slx` has the fixed compensation
  (`CT_Ratio_LV = 92000/5`, `I_nom_lv ≈ 0.8557 A`). Tag/commit it as the single source of truth.

### Step 1 — Fix the test-scenario generator (data quality)
- In `simulate_all_and_extract_features.m`, the internal fault is intended at `t_fault = 0.50 s`
  but the fault switch `SwitchTimes` stays `[0.05 1]`, so it actually fires at ~0.05 s.
  Set the fault `SwitchTimes` from `t_fault` so inception matches the intended time.

### Step 2 — Regenerate the TRAINING dataset with the corrected model
- Re-run the stress/scenario generator that produced `StressTestDataset_*.mat`, but using
  the **corrected** `TransformerWithCTSaturation.slx`. Vary: fault type (AG/BG/CG/AB/ABC,
  turn-turn), location (% winding), fault resistance, inception angle, load level, and
  remanent flux for inrush. Aim for the same class balance as before.
- Store, for every scenario, the **same `DWT_Features` signal the relay uses at runtime**
  (log the model's `DWT_Features` output), OR the compensated per-unit `I_diff` that feeds it.

### Step 3 — Extract features consistently
- **Preferred:** use the model-logged `DWT_Features` directly as `X_LSTM` (guarantees
  train == test pipeline).
- **If you keep `FeatureExtractor.m`:** update its differential to match the model exactly —
  apply the `Yd1_Compensation` (per-unit bases `I_nom_hv=1.8827`, `I_nom_lv=0.8557`,
  `M_Yd1` matrix) **before** the DWT, instead of `I_diff = Ip - Is`.

### Step 4 — Build an independent split
- Stratified train/val/test split. **Ensure the 4 canonical demo cases (and any scenario
  close to them) are NOT in the training set** so the final evaluation tests generalization.
- If any input scaling/normalization is used, **fit it on train only** and save the scaler
  with the checkpoint; apply the identical scaler at eval.

### Step 5 — Retrain the LSTM
- Run `lstm_models/train_lstm_local.py` on the regenerated dataset. Keep the architecture
  (`input_size=9`, seq len 1569). Save `best_threshold` and `model_config` into the checkpoint
  (the eval reads them).

### Step 6 — Regenerate the 4-case test features
- Run the corrected `simulate_all_and_extract_features.m` to rebuild
  `simulated_test_features.mat` (and the light `simulated_trip_summary.mat`) from the same model.

### Step 7 — Evaluate (training-consistent)
- Run `simulations/evaluate_simulated_cases_v2.py`. It prints provenance dates and scores the
  completed final `[1569×9]` window (matching training). Expect, once train==test pipeline:
  Normal BLOCK, Inrush BLOCK, Internal TRIP, External BLOCK (if the AI adds security over the
  conventional relay).

### Step 8 — Fair conventional-vs-AI comparison
- Compare the conventional 87T (`trippedConventional` in the summary, settings synced to
  `chart_27`: pickup 0.30, slopes 0.25/0.60, breakpoint 3.0 pu) against the LSTM **on the same
  corrected, in-distribution cases**. Only then is the "AI improves security" claim supportable.

---

## 4. Consistency checklist (all must be TRUE before reporting results)

- [ ] Same Yd1 compensation + CT ratios + per-unit bases in training-gen and test/inference.
- [ ] Same differential signal feeding the DWT (ideally the model's own `DWT_Features`).
- [ ] Same DWT: db4, 2-level, 32-sample window, 1569 steps, 9 features, `log1p`.
- [ ] Same input scaling (fit on train only; saved and re-applied at eval).
- [ ] Same sequence representation (full `[1569×9]`) and decision rule/threshold.
- [ ] Test scenarios independent of the training set.
- [ ] Provenance: training features, checkpoint, and test features are ALL post-calibration-fix.
- [ ] Fault inception time in test cases matches the intended `t_fault`.

---

## 5. Scripts set up in this pass

- `simulations/evaluate_simulated_cases_v2.py` — training-consistent evaluation:
  scores the completed final window (one forward pass per case), prints the old max-rolling
  number for contrast, and prints train/test/model provenance dates so any mismatch is visible.
- `simulations/lstm_eval_output.txt`, `simulations/lstm_eval_v2_output.txt` — saved run logs.

**Still to do by you (require MATLAB / retraining, can't be automated from here):**
regenerate the training dataset with the corrected model (Step 2), align `FeatureExtractor.m`
or switch to model-sourced features (Step 3), and retrain (Step 5).
