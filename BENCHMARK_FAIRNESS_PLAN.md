# Benchmark Fairness Plan — 2026-10-31

**Goal:** make the comparison between the proposed hybrid DWT-LSTM and the other models fair enough that a journal reviewer cannot dismiss it.
**Scope:** plant A v5 data (`runs/20261029_v5_*`), plus a plant-B zero-shot check. The evaluation protocol of `IMPLEMENTATION_PLAN_V3.md` §3 stays fixed:
- trace-grouped folds;
- thresholds tuned on validation only (plateau rule);
- dwell 20;
- undetectable faults reported separately;
- OOD scored once.

**Rules:** the "Rules for the Claude Code session" in `IMPLEMENTATION_PLAN_V4_PUBLICATION.md` apply:
- numbers only from saved files;
- real dates in the log;
- no Claude trace in commits;
- no push.

---

## 0. What is already fair (keep)
- Same traces, same 5 folds (same `StratifiedKFold` code and seed as `train_cv_v5.py`), same inner validation split.
- Same 12 input features, same threshold-tuning rule, same relay mirror (dwell, high-set, hybrid wiring), same exclusion of undetectable faults.
- Repetition-1 vs Repetition-1 comparisons.

## 1. Problems found (verified in `lstm_models/benchmark_literature_models.py`, version of 2026-10-30)

| # | Problem | Evidence |
|---|---|---|
| F1 | **Unequal training budget** | Proposed LSTM: 25 epochs, patience 5 (`train_cv_v5.py`). Wavelet-ANN and 1D-CNN: 15 epochs, patience 4 (lines 439, 470). Wavelet-GRU: **10 epochs, patience 3** (line 501). |
| F2 | **No hyperparameter search for baselines** | One fixed configuration each (e.g. RF `n_estimators=100, max_depth=12`; GRU hidden 64, 2 layers). The LSTM design was refined over months, including Optuna runs. |
| F3 | **Baselines labelled as published methods** | Table names such as "Abdusalam (2022)" or "Lin (2025)", although the models are generic architectures using *our* 12 features, not reproductions of those papers. |
| F4 | **Conventional relays not tuned** | 87T pickup / slopes and harmonic thresholds (k2 15 %, k5 35 %) fixed at textbook values, while every learned model gets validation-tuned thresholds. |
| F5 | **No significance tests among learned models** | McNemar only against the 87T relays. Differences of 0.3–1 pt between ML models are untested. |
| F6 | **One seed for baselines** | Proposed: 3 seeds × 5 folds; baselines: Repetition 1 only. Seed-to-seed spread of the baselines is unknown. |
| F7 | **Static models see pooled features only** | SVM / ANN / RF get pooled statistics (48 values) of the 32-step window. That is acceptable, but it must be stated, together with the pooling used. |
| F8 | **Deterministic wavelet schemes not implemented** | BDWT / Clarke-wavelet are only discussed in the text. |

---

## 2. Work packages

### B1. Equal training budget (fixes F1) — ≈ 2 h code, runs in B2
- [ ] One shared training routine for **all** neural models (ANN, 1D-CNN, GRU, LSTM): the same max epochs (25), the same early stopping (patience 5 on validation AUC), the same optimiser, batch size 256, learning rate 1e-3, and the same window stride.
- [ ] Record the epochs actually used per model and fold in the result JSON.

### B2. Equal hyperparameter search (fixes F2) — ≈ 1 day compute
- [ ] For **each** learned model, including the proposed LSTM, run the **same search budget**: **12 random configurations** per model, chosen with a fixed seed, on the **inner validation split of each fold only**. Pick the configuration with the best validation AUC; never look at test folds.
- [ ] Search spaces, written in the code **before** running:

  | Model | Searched |
  |---|---|
  | Wavelet-SVM | kernel approximation components {60, 120, 240}, gamma {0.5, 1, 2} × 1/48, alpha {1e-5, 1e-4, 1e-3} |
  | Wavelet-RF | n_estimators {100, 200, 400}, max_depth {8, 12, 16, None}, min_samples_leaf {1, 5, 20} |
  | Wavelet-ANN | hidden {32, 64, 128} × {16, 32, 64}, dropout {0.1, 0.2, 0.3}, lr {3e-4, 1e-3, 3e-3} |
  | 1D-CNN | channels {16, 32, 64}, kernel {3, 5, 7}, layers {2, 3}, dropout {0.1, 0.2, 0.3}, lr as above |
  | Wavelet-GRU | hidden {32, 64, 128}, layers {1, 2}, dropout {0.1, 0.2, 0.3}, lr as above |
  | Proposed LSTM | hidden {32, 64, 128}, layers {1, 2}, dropout {0.1, 0.2, 0.3}, lr as above (attention pooling kept) |
- [ ] **Report two tables:** "default configuration" (today's numbers) and "tuned with equal budget". If the tuned LSTM differs from the deployed one, keep the deployed model for the closed-loop / Simulink results and say so.
- [ ] Optional, if compute is short: 3 folds of seed 1 for the search, then refit the chosen configuration on all 5 folds. Use the same approach for every model.

### B3. Honest naming (fixes F3, F7) — ≈ 1 h
- [ ] Rename the rows to architecture names: "SVM (pooled features)", "MLP (pooled features)", "Random forest (pooled features)", "1D-CNN (sequence)", "GRU (sequence)", "LSTM + attention (sequence)".
- [ ] Cite the papers in the text as "architecture families used in [refs]", not as reproductions.
- [ ] In the table note: "All models use the same 12 DWT + 2nd-harmonic features; static models receive [list the pooling statistics] over the 32-step window."

### B4. Tuned conventional relays (fixes F4) — ≈ 2–3 h
- [ ] Add a **validation-tuned harmonic 87T**: a grid over pickup {0.2, 0.3, 0.4} pu, k2 {0.12, 0.15, 0.20}, k5 {0.25, 0.35}, chosen per fold on the validation traces with the **same plateau rule** as the learned models (dependability within 2 pt and security within 1 pt of the best, centre of the plateau).
- [ ] Report it next to the textbook-setting harmonic 87T. Keep both: "textbook settings" and "tuned on validation".
- [ ] Re-run the main McNemar comparison against the **tuned** harmonic 87T as well.

### B5. Statistics among learned models (fixes F5, F6) — ≈ 0.5 day compute
- [ ] Run every **tuned** baseline (B2) on **3 seeds × 5 folds**, like the proposed model. Report mean ± sd over the 15 fold-models.
- [ ] Paired McNemar, matched on (seed, fold, trace), **proposed hybrid vs each baseline in hybrid mode** and **LSTM alone vs each baseline in standalone mode**, for dependability and security separately.
- [ ] Correct for multiple comparisons (Holm–Bonferroni across all tests reported in the table). Report the corrected p-values.
- [ ] Plant-B zero-shot for every tuned baseline in hybrid mode, with thresholds frozen from plant A. This shows whether the transfer weakness is LSTM-specific or general.

### B6. Deterministic wavelet scheme (fixes F8) — optional, ≈ 1 day
- [ ] Implement one published non-learned wavelet differential scheme (e.g. a boundary-DWT energy criterion with its paper's thresholds, then validation-tuned thresholds). Evaluate it on the same folds.
- [ ] If not done: say clearly in the paper that BDWT / Clarke-wavelet are discussed, not benchmarked.

### B7. Outputs and tables — ≈ 2 h
- [ ] Results in `runs/<date>_v5_benchmark_fair/`:
  - `summary.json|txt`;
  - per-model search logs (configurations tried, validation AUC, chosen configuration);
  - per-fold rows with (seed, fold, trace) keys;
  - `stats.json|txt`.
- [ ] Tables built by `tools/build_publication_tables_v5.py` from those files only. Table note states:
  - the search budget (12 configurations per model);
  - the training budget (25 epochs, patience 5);
  - the pooling for static models;
  - the Holm correction.

---

## 3. Acceptance criteria
1. Every learned model, including the proposed one, used the same epochs cap, early stopping and search budget. The JSON proves it.
2. No test-fold data was used for any choice: configuration, threshold or relay setting.
3. The table shows default and tuned results, 3-seed mean ± sd, and Holm-corrected p-values.
4. Names describe architectures, not papers.
5. The conclusion is written **after** the numbers, whatever they show. If a tuned baseline matches or beats the LSTM, the paper says so. The claim then rests on the **dual-path architecture**, which already improves every classifier.

## 4. Order and effort
B1 → B3 (code) → B2 (search, unattended) → B5 (3 seeds + statistics) → B4 → B7 → (B6 optional).
**About 2–3 days**, mostly unattended compute. One process at a time; RAM < 4 GB.

## 5. Log
Add a dated entry to `IMPLEMENTATION_PLAN.md` after each work package, with file paths and numbers taken from the saved outputs.

---

# Part 2 — Faithful reproductions: implement each method as its authors intended (added 2026-10-31)

**Author decision:** the baselines must be implemented **as close as possible to what each paper's authors intended**:
- their inputs and sampling rate;
- their signal processing;
- their features and feature selection;
- their classifier and training procedure;
- their decision logic.

Part 1 (B1–B5) stays as a second, clearly labelled comparison ("same 12 features, different architectures").

## 2.1 What the cited papers actually do (from the PDFs in git commit `f92ea33`, `documents/Reference Papers/`)

The current benchmark rows do **not** implement these methods. Several rows cite a paper whose method is entirely different.

| Benchmark row today | Cited as | What the paper actually does | Gap |
|---|---|---|---|
| Wavelet-SVM | Simões et al. 2021, EPSR 197:107297 [ref13] | **Real-time boundary stationary wavelet transform (RT-BSWT)** of operating and restraining currents at **15,360 Hz (256 samples/cycle, 60 Hz)**. A disturbance detector with **adaptive energy thresholds** feeds two **RBF-kernel SVMs**: SVM1 takes **32 features** (4 post-disturbance samples of operating/restraining wavelet energies) and decides internal fault / external fault / energisation; SVM2 runs a **half-cycle sliding window (768 features)** to catch evolving external-to-internal faults. Features are normalised with training statistics. | Different transform, sampling rate, features, two-stage logic |
| Wavelet-ANN | "Guzman [19] / Costa [18]" | ref19 = **Ngaopitakkul & Kunakorn**: **db4 DWT, scale-1 detail coefficients squared**, maximum after the detected inception (ATP/EMTP, **5 µs step = 200 kHz**). A **back-propagation NN with 2 hidden layers (tanh), linear output, Levenberg–Marquardt**, hidden size from the paper's formula. Built to classify **internal fault types**, not inrush vs fault. | Different features, training algorithm and target task |
| Wavelet-RF | Abdusalam et al. 2022 [ref11] | Lab transformer at **10 kHz**. **6-level DWT with 5 mother wavelets (db7, sym3, coif4, bior6.8, rbior6.8)** plus **orthogonal matching pursuit**. **30 statistical features** (mean, median, std, MAD, mean abs. deviation, …), selected with the **bees algorithm and a genetic algorithm**. **KNN (K = 3), SVM and ANN** with k-fold CV; best SVM + GA, 96 %. **No random forest appears in the paper.** | Wrong classifier; features and selection missing |
| 1D-CNN | Afrasiabi et al. 2020, IEEE TII [ref16] | **Raw normalised half-cycle differential currents** of three phases (2-D input). A **least-squares CT-saturation compensation** filter first. An **accelerated CNN** (ReLU, batch norm, product-quantised layers) with two outputs: fault / no fault, and the type of non-fault event (inrush / external fault / over-excitation). | Raw-signal input and CT compensation missing |
| Wavelet-GRU (self-attention) | "Lin et al. 2025, IEEE Access" [ref23] | The PDF is **Key, Leap, Yoon, Lee & Nam, IEEE Access 2025, DOI 10.1109/ACCESS.2025.3618747**. **Com-DNN** (CT-saturation compensation) plus **Dis-DNN** built from **stacked denoising autoencoders + softmax**, on **one-cycle, 64-sample windows normalised to [−1, 1]**, with 4 classes (normal / transient / inrush / internal fault). **No GRU and no attention.** | Wrong authors and wrong architecture |
| Standalone LSTM | Alhamd et al. 2024 [ref1] / Atiyah et al. [ref3] | Alhamd: a new wavelet-derived feature **plus differential current amplitude and bias (restraint) current** → LSTM. Atiyah (PDF: J. Electr. Eng. Technol. 2024, DOI 10.1007/s42835-024-02048-7): WT features → LSTM in a cascading, moving-window scheme. | Inputs differ from ours; extract the exact recipe |

## 2.2 Bibliography errors found while checking (fix before any submission)  🚨
The reference list contains author / venue data that does **not** match the papers in the project folder:
- **ref23:** listed as "Y. Lin, Z. Li, X. Wang, L. Chen, IEEE Access vol. 13, pp. 11234–11246". The PDF is **S. Key, S. Leap, S.-M. Yoon, H. Lee, S.-R. Nam**, IEEE Access 2025, DOI 10.1109/ACCESS.2025.3618747.
- **ref11:** listed authors "M. Abdusalam, K. F. Ali, W. M. El-Hawary". The PDF authors are **O. Abdusalam, A. Ibrahim, F. Anayi, M. Packianather** ("New Hybrid Machine Learning Method for Detecting Faults in Three-Phase Power Transformers", Energies 2022).
- **ref19:** listed as "Int. J. Comput. Appl. 28(5), 15–22". The PDF is **Int. J. Control, Automation, and Systems 4(3), 365–371, 2006** ("…in Transformer Windings using Combination of DWT and Back-propagation NN").
- **ref20:** listed as "Subramanian, Kalavathi, Sharmeela, Math. Probl. Eng. 2010". The PDF is **Subramanian, Mathur, Henry, Modern Applied Science 4(5), 2010**.
- **ref3:** the listed title, journal and volume do not match the Atiyah PDF in the folder. Confirm which paper is meant.
- The benchmark table cites "**Guzman [19]**", but ref19 is Ngaopitakkul & Kunakorn.

- [x] **R0.** (done 2026-10-31: `documents/reference_audit.md`; 10 verified as listed, 21 corrected, 9 not found and flagged in `main.tex`, still cited in the text) Check **every one of the 40 references** against the actual paper, using DOI / publisher page / Crossref: authors, title, journal, volume, pages, year. Correct the `.bib`/`bibitem` entries. A reference that cannot be verified is removed or replaced. Log each check in `documents/reference_audit.md` (reference, DOI, verified fields, source).

## 2.3 Data at each method's own sampling rate (prerequisite)
The datasets store currents at **1,600 Hz**. The papers need **3.2 kHz** (Key: 64 samples/cycle at 50 Hz), **10 kHz** (Abdusalam), **12.8 kHz** (Simões: 256 samples/cycle at 50 Hz) and **≥ 20 kHz** (Ngaopitakkul used 200 kHz).

- [x] **D1.** (done 2026-10-31: `documents/high_rate_D1.md`) Check the solver step of the v5 models. The noise block uses Ts = 1e-4 s (10 kHz), which **limits the usable bandwidth to < 5 kHz**. To feed 12.8 kHz methods, run the high-rate re-simulation with a fixed step ≤ 2.5e-5 s (40 kHz) and noise generated at that rate. Record the settings.
- [ ] **D2.** **Re-simulate the same traces at high rate.** The generators are seeded per trace (`rng(seed + k)`), so the same scenario parameters reproduce exactly. Log raw HV/LV CT-secondary currents at **20 kHz** for:
  - all plant-A v5 main traces (or, if storage/time is short, all traces of the **seed-1 test folds** — one full out-of-fold pass; the decision is made before running);
  - the plant-A OOD set;
  - plant-B zero-shot.
  
  Files: `datasets/StressDataset_v5HR_*.mat`.
- [ ] **D3.** **Equivalence check:** decimating the 20 kHz traces to 1,600 Hz must reproduce the existing traces: same events, and the proposed model's decisions identical on ≥ 99 % of traces. If not, investigate before going on.
- [ ] **D4.** Each method gets the currents resampled to **its paper's rate** (anti-alias filtered). Where the paper's rate is above 20 kHz (Ngaopitakkul), use 20 kHz and record it as a deviation.

## 2.4 Implement each method (one module per paper, `lstm_models/baselines/<name>.py`)
For **each** paper:
1. Write `documents/baselines/<name>_spec.md` **before coding**. It lists, with page/equation references to the paper:
   - input signals;
   - sampling rate;
   - window length;
   - preprocessing / normalisation;
   - transform (family, levels, boundary handling);
   - features;
   - feature selection;
   - classifier and every published hyperparameter;
   - training algorithm;
   - decision / trip logic.
   
   Mark every item the paper does **not** specify as "UNSPECIFIED", and say how it will be filled: tuned on validation folds within the range the paper suggests, or a stated default.
2. Implement exactly that spec. Deviations forced by our setup (50 Hz vs 60 Hz, 20 kHz cap, our class labels) go into a **deviation table** in the spec.
3. **Sanity check against the paper:** reproduce one qualitative result the paper reports, where its data type allows it (e.g. an RT-BSWT energy plot for an inrush and an internal fault, the feature-separation figure). Save it as `documents/baselines/<name>_sanity.png`.

| Module | Must contain |
|---|---|
| `simoes2021_rtbswt_svm.py` | RT-BSWT (boundary stationary WT, real-time form as in the paper's equations), operating/restraining energies, adaptive-threshold disturbance detector, SVM1 (32 features) + SVM2 (half-cycle sliding window, 768 features), RBF kernel, normalisation from training data, SVM1 blocking after trip, the paper's trip/warning logic. |
| `ngaopitakkul2006_dwt_bpnn.py` | db4 DWT scale-1 coefficients squared, the paper's inception detection and max-coefficient comparison, BPNN 2 hidden tanh + linear output, Levenberg–Marquardt training (e.g. `scipy.optimize.least_squares` on the weights, or a small LM implementation), hidden size from the paper's formula. Retarget the output to our task (trip / no trip) and record this as a deviation, since the paper classified fault types. |
| `abdusalam2022_dwt_omp_ga.py` | 6-level DWT with the 5 named wavelets + OMP, the 30 statistical features, bees-algorithm and GA feature selection run on the **training folds only**, KNN (K = 3), SVM and ANN as in the paper. Report the paper's best combination (SVM + GA) as the main row; the others in the appendix. **No random forest** (drop the "Wavelet-RF" attribution; RF may stay only in Part 1, unattributed). |
| `afrasiabi2020_acnn.py` | Half-cycle normalised raw differential currents (2-D, three phases), the paper's LS-based CT-saturation compensation filter, the CNN with ReLU + batch norm, two outputs as described. Implement the product-quantisation acceleration if feasible; otherwise run the uncompressed CNN and record it as a deviation (it affects speed, not accuracy, per the paper's aim). |
| `key2025_comdnn_disdnn.py` | One-cycle 64-sample windows normalised to [−1, 1], Com-DNN for CT-saturation compensation trained as in the paper, Dis-DNN = stacked denoising autoencoders (greedy unsupervised pre-training with the paper's cost: reconstruction + weight decay + sparsity) + softmax fine-tuning, 4 classes mapped to trip / no trip. |
| `alhamd2024_wavelet_lstm.py` | Alhamd's wavelet-derived feature, differential current amplitude and bias current as inputs; the LSTM as specified (layers, units, training). Extract the exact feature definition and network settings from the paper; fill gaps per rule 1. |

## 2.5 Evaluation of the reproductions (same protocol as everything else)
- [ ] Same traces, **same 5 folds and seeds**, same train / validation / test split as the proposed model (trace-level, leak-free). Methods are **retrained on our training folds**; no pre-trained weights from the papers.
- [ ] Each method uses **its own decision logic** (e.g. Simões' detector + SVM1/SVM2 trip/warning). Its trip instant is the first sample at which its logic issues a trip. Scoring: dependability, security, operate time, pre-fault trips, undetectable faults reported separately — identical to the proposed model.
- [ ] Where a method outputs a probability, report two modes: (a) **native** (its own rule, e.g. argmax / class decision), and (b) **with our 20-sample dwell and validation-tuned threshold**, for a like-for-like view. Mode (a) is the "as intended" result.
- [ ] Hyperparameters the paper leaves UNSPECIFIED: same search budget for every method (as Part 1, B2), validation folds only.
- [ ] 3 seeds × 5 folds; paired McNemar matched on (seed, fold, trace) vs the proposed hybrid and vs LSTM alone; Holm correction.
- [ ] OOD set once; plant-B zero-shot with thresholds/logic frozen from plant A.
- [ ] Measured latency of each method on the same machine (same script as `runs/20261029_v5_latency`), feature extraction + inference, single thread, at the method's own sampling rate, since a 12.8 kHz method must finish within 78 µs per sample.

## 2.6 Reporting
- [ ] **Table A — "Published methods, reproduced"**: one row per paper (correct authors, year, DOI), native decision logic, own sampling rate, measured latency. Footnote each row with its main deviations (link to the spec).
- [ ] **Table B — "Same features, different classifiers"** (Part 1, renamed architecture rows, no paper attribution).
- [ ] Text: say plainly that reproductions are re-implementations trained on our data, not the authors' code, and that results can differ from the published numbers. Where the authors offer code or data on request, ask them by e-mail and note it.

## 2.7 Order and effort (Part 2)
R0 (≈ 0.5 day) → D1–D3 (≈ 1 day, mostly unattended re-simulation) → specs for all six papers (≈ 1 day) → implementations (≈ 3–5 days; Simões and Key are the largest) → evaluation (≈ 1–2 days unattended) → tables.
**About 1.5–2 weeks in total.** If time is short, do R0 + D1–D3 + the **three most-cited / closest methods** first: Simões (SVM + wavelet), Key (dual DNN under CT saturation), Afrasiabi (CNN). Record the remaining three as "not reproduced".

## 2.8 Rules specific to Part 2
- Specs are written and committed **before** implementation and before seeing any result of that method.
- No method is tuned on test folds or OOD. No method gets less training budget than the proposed model.
- If a reproduction beats the proposed model on any metric, it is reported as such.

---

# Status and next steps — 2026-11-01 23:20, with hypotheses and pre-set decisions

## How to use this section
- Every step has three parts:
  - **Hypothesis**: what we expect and why, based on what is already measured.
  - **Test**: what is measured and from which file.
  - **Decision rules**: what we do for each possible outcome.
- Hypotheses and rules are fixed **now, before** the step runs. Commit this file first.
- After each step, log in `IMPLEMENTATION_PLAN.md`: "H… confirmed / rejected", the numbers (from saved files) and **which decision rule fired**.
- If an outcome fits no rule, or you want to act against a rule: **stop**, write the reason in the log first, and ask the author.
- A rejected hypothesis is a result, not a failure. Never re-run with changed settings to make a hypothesis come true.

## Done and verified (status at 23:20)
- **R0:** 10 references verified, 21 corrected, **9 not found** (still in `main.tex`).
- **D1:** done.
- **D2:** 20 kHz re-simulation done 13:08. 30 of 3,332 plant-A traces failed (`hr_missing_traces.txt`); plant B 12 and OOD 3 failed, no manifest yet.
- **D3:** 429/432 = 99.3 % identical decisions.
- **Specs** for all six papers.
- **Modules:** Simões, Afrasiabi (+ Hajipour), Key; harness `common.py` / `cv.py`.
- **Not yet:** no reproduction evaluated; Part 1 (B1–B5) not started.

---

## N1. Close the data loose ends (≈ 1 h)

### N1a. Missing-trace manifests and the common trace set
- [x] Write manifests for plant B (11) and OOD (1), like `hr_missing_traces.txt`.
- **Hypothesis H1a:** the failed re-simulations are scattered over scenarios. No scenario group loses more than 5 % of its traces, so using only traces present in both sets does not bias any category. The plant-A list so far shows mixed groups (Normal, inrush, over-excitation, SOTF, external).
- **Test:** count failures per scenario group, per data set.
- **Decision rules:**

| Outcome | Action |
|---|---|
| every group loses ≤ 5 % | use the intersection ("common set") for all methods; list the excluded traces in the paper's appendix |
| a group loses > 5 %, or failures share one cause (same scenario kind, same parameter range) | re-run those traces once (smaller solver step or a single-trace launch); if they still fail, keep them excluded and **report the group's reduced n** next to its results |
| plant B or OOD loses a whole category | stop and report to the author before N4 |

### N1b. Re-score the proposed relay and the 87T baselines on the common set
- [ ] From the saved predictions (no retraining): proposed hybrid, LSTM alone, unrestrained 87T and harmonic 87T on the common set → `runs/<date>_v5_common_set/`.
- **Hypothesis H1b:** removing 30 of 3,332 traces (0.9 %) changes dependability and security by **< 0.3 pt**.
- **Decision rules:**

| Outcome | Action |
|---|---|
| all changes ≤ 0.5 pt | comparison tables use common-set numbers; the headline stays the full-set number, with a footnote |
| any change > 0.5 pt | use common-set numbers everywhere, and log which excluded traces cause the difference (they matter, so N1a's retry becomes mandatory) |

### N1c. powergui frequency check (60 Hz setting, 50 Hz system)
- [ ] One trace each of Normal 100 % load, external 3-phase fault and inrush: run with powergui Frequency 60 Hz (as now) and 50 Hz. Compare the CT-secondary currents and the proposed relay's decision → `simulations/powergui_freq_check.txt`.
- **Hypothesis H1c:** the effect is negligible (< 0.1 % RMS difference, identical decisions). In discrete simulation this parameter only affects initial-state and phasor tools.
- **Decision rules:**

| Outcome | Action |
|---|---|
| RMS difference < 0.5 % and identical decisions | keep all data; one sentence in Limitations |
| 0.5–2 %, or any decision differs | set 50 Hz in the v5 models for all **new** simulations; run 100 traces (stratified) with 50 Hz and compare decisions; if ≥ 99 % identical, keep the existing data and report the check; otherwise go to the next row |
| > 2 %, or < 99 % identical decisions on the 100 traces | **stop**: the author decides whether to regenerate v5 (≈ 1 day compute + all evaluations) |

---

## N2. Simões detector setting, chosen by a rule (≈ 1 h)
- [ ] Grid of detector factors {5, 10, 15, 20, 30, 50, 100}, evaluated **per fold on validation traces only**.
- **Pre-set selection rule:** choose the **smallest** factor that gives ≤ 1 spurious firing per trace on validation Normal and over-excitation traces **and** ≥ 95 % event detection on validation fault, inrush and external traces.
- **Hypothesis H2:** no factor meets both criteria. `simoes_detector_check.txt` (15 traces/scenario) shows that at factor 30 Normal has 0.8 spurious firings, but Internal HiZ is detected in only 80 % of traces; at 10, HiZ is 93 %, but inrush has 62 spurious firings. HiZ detection will be the limiting part.
- **Decision rules:**

| Outcome | Action |
|---|---|
| a factor meets both criteria | use it (per fold) |
| no factor meets both | use the smallest factor meeting the **spurious-firing** criterion (the paper's detector is a security device). Report its detection rate per group. Undetected events count as **no trip** in native mode (missed faults). Record it in the spec amendment |
| even factor 100 gives > 1 spurious firing per Normal trace | report the method as "detector not usable at our noise level"; still evaluate with factor 100 and flag the row ⚠ |

In every case, report the paper's factor 3 as unusable here, citing `simoes_detector_check.txt` (≈ 1,500 firings per trace).

---

## N3. The three remaining modules (≈ 2–3 days)
**Common rule for all modules:**
- Before evaluation, each module must pass its **sanity check** (one qualitative behaviour from its paper, saved as `<name>_sanity.png/.txt`) **and** reach ≥ 80 % training accuracy on fold 1.
- If either fails, check the implementation against the spec checklist. **At most two debug rounds**, each logged.
- If it still fails, the method is evaluated as implemented and its row is flagged ⚠ "reproduction could not reach the paper's qualitative behaviour". **Never drop a method silently.**

### N3a. Ngaopitakkul & Kunakorn 2006 (DWT scale-1 + BPNN)
- **Hypothesis H3a:** weak transfer. It was designed for fault-**type** classification at 200 kHz; its only feature is the scale-1 (highest band) coefficient. In our lumped plant at 20 kHz that band is mostly noise (`hf_content.txt`: after an event, energy above 5 kHz ≈ 1e-4 to 1e-3 of the total for faults). Expect security on inrush and external faults **below 90 %**, and the lowest dependability on HiZ faults among all methods.
- **Decision rules:** as in the common rule. If H3a is confirmed, the paper says the method is unsuited to data without high-frequency transients. That is a statement about this test bench, not about the method.

### N3b. Abdusalam et al. 2022 (DWT × 5 wavelets + OMP + BA/GA + KNN/SVM/ANN)
- **Hypothesis H3b:** decent classification of inrush vs fault, because its statistical features over a 6-level DWT capture the 2nd-harmonic-dominated inrush shape. But it is a **whole-window** classifier, so its operate time will be at least one window after inception. Expect median operate time **≥ 20 ms**, slower than the proposed 16 ms. Dependability on HiZ will be lower than the proposed hybrid's.
- **Decision rules:**

| Outcome | Action |
|---|---|
| BA+SVM and GA+SVM differ by ≤ 3 pt on validation | report BA+SVM only (spec choice); the others in the appendix |
| they differ by > 3 pt | report both rows in Table A, because the paper's internal inconsistency then matters |

### N3c. Alhamd et al. 2024 (wavelet feature + differential and bias current → bidirectional LSTM)
- **Hypothesis H3c:** the **closest competitor**: same idea (wavelet + LSTM), trained on our data. Expect dependability and security **within 2 pt of LSTM alone** (97.7 % / 95.6 %), and **lower security than the proposed hybrid** (no 87T gate). Its bidirectional, segment-based decision makes it **much slower**: median operate time ≥ 25 ms; the paper reports 110–170 ms.
- **Decision rules:** see N4. This method is the one most likely to challenge the claim.

---

## N4. Evaluate all six reproductions (≈ 1–2 days, mostly unattended)
- [ ] 3 seeds × 5 folds on the common set, two modes (native = main row; dwell 20 + validation-tuned threshold = like-for-like row), OOD once, plant-B zero-shot frozen, measured latency at each method's own rate.

**Hypotheses (pre-registered):**
- **H4.1, dependability:** the proposed hybrid keeps the **highest dependability**. Its margin comes mainly from **Internal HiZ** faults, which it catches through the AI-alone path. Reproductions relying on high-frequency content (Simões, Ngaopitakkul) have the lowest HiZ dependability.
- **H4.2, security:** reproductions trained on our data (Key, Afrasiabi, Alhamd, Abdusalam) reach security of about **94–99 %**, similar to our LSTM alone (95.6 %), and **below the proposed hybrid** (99.0 %), because none has an 87T gate.
- **H4.3, speed:**
  - Simões is the **fastest** when its detector fires: the paper reports ≈ 4 samples, under 1 ms.
  - Afrasiabi (half-cycle window) ≥ 10 ms.
  - Key (one-cycle window) ≥ 20 ms.
  - Alhamd ≥ 25 ms.
  - The proposed median is 16 ms.
- **H4.4, transfer:** every learned method loses security in the plant-B zero-shot test, as ours did (88 %). The harmonic 87T (98.95 %) stays the most secure on plant B.
- **H4.5, latency:** all methods meet their per-sample budget on the PC, except possibly Simões' SVM2 (768 features at 12.8 kHz, 78 µs budget).

**Decision rules (Holm-corrected paired McNemar, α = 0.05, pooled over 3 seeds):**

| Outcome vs the proposed hybrid | Action |
|---|---|
| no reproduction is significantly better on dependability or security | **claim A holds** (see N8) |
| a reproduction is significantly better on **one** metric and worse on the other | **claim B**: report the trade-off and the operating points; no "best" wording |
| a reproduction is significantly better on **both** metrics, or better on one and not significantly worse on the other | **claim C**: the proposed classifier is not the best. Run **one** pre-registered extra evaluation: that method inside the dual-path supervisory logic ("hybrid with X", thresholds tuned on validation). The dual-path logic is model-agnostic; report it as the architecture's contribution |
| a reproduction has dependability or security < 60 % | apply the N3 debug rule (max 2 logged rounds), then report as measured with the explanation (e.g. HF content) |
| native and like-for-like results of a method differ by > 5 pt | report both rows and discuss; the native row is the "as intended" result |
| a method misses its per-sample latency budget | report "not real-time at its native rate on this PC"; do **not** lower its sampling rate to make it fit |
| H4.4 rejected (a reproduction transfers to plant B with security ≥ 98 %) | report it prominently; it weakens our generalisation limitation into a model-specific one, and the paper says so |

---

## N5. Statistics (≈ 0.5 day)
- [ ] Paired McNemar on (seed, fold, trace): proposed hybrid vs each reproduction (native), LSTM alone vs each, for dependability and security separately. Holm correction across all tests in the table. Mean ± sd over the 15 fold-models.
- **Hypothesis H5:** with about 1,250 fault and 1,990 healthy traces per seed, differences of about **≥ 1.5 pt** in dependability and **≥ 0.7 pt** in security will be significant after Holm. Smaller ones will not.
- **Decision rules:**

| Outcome | Action |
|---|---|
| p_Holm ≥ 0.05 | write "no significant difference"; never "better" or "comparable performance" |
| the per-seed differences change sign between seeds | report the difference as "unstable across splits", even if the pooled test is significant |
| the fold-model sd of a method > 3 pt | report its range next to the mean, and do not rank it by the mean alone |

---

## N6. Part 1, reduced (≈ 1 day)

### N6a (B1). Same-feature models with an equal training budget (25 epochs, patience 5 for every neural model)
- **Hypothesis H6a:** the GRU (trained with only 10 epochs, patience 3) and the 1D-CNN (15 / 4) improve by **0.5–2 pt**. The GRU may then **match** the LSTM, because it already had the highest standalone dependability (v5 table: 98.40 %).
- **Decision rules:**

| Outcome | Action |
|---|---|
| a same-feature model is within 1 pt of the LSTM on both metrics | run **B2** (equal hyperparameter search, 12 configurations per model, LSTM included). The paper states the choice of LSTM over GRU/CNN is **not decisive**; the claim rests on the dual-path architecture |
| the LSTM leads by > 1 pt on at least one metric and is not worse on the other | B2 optional; skip it; report B1 |

### N6b (B3). Rename the rows to architecture names; no paper attribution
No hypothesis; always done.

### N6c (B4). Validation-tuned harmonic 87T (pickup {0.2, 0.3, 0.4} pu, k2 {0.12, 0.15, 0.20}, k5 {0.25, 0.35}, plateau rule)
- **Hypothesis H6c:** tuning (mainly a lower pickup) raises the harmonic 87T's dependability by **2–5 pt**, by catching part of the HiZ faults now below 0.30 pu, while keeping security ≥ 99 %. The hybrid's dependability lead (now +8 pt, 93.92 vs 85.93 % in repetition 1) shrinks but **stays significant**.
- **Decision rules:**

| Outcome | Action |
|---|---|
| the tuned 87T stays ≥ 3 pt below the hybrid in dependability, significantly | claim stands; the tuned 87T becomes the **main** conventional baseline in the paper (the stronger one) |
| the gap drops below 3 pt, or is no longer significant | the dependability claim is **weakened** to the measured gap; the paper's headline changes to the architecture and the evaluation, and the HiZ-specific gain is reported per bin |
| the tuned 87T's security falls below 99 % at its best dependability | report both of its operating points (textbook and tuned) |

---

## N7. References — author action, gate before any submission  🚨
- [ ] Replace or remove the 9 UNVERIFIED references (ref2, 5, 10, 18, 31, 32, 33, 34, 35) and every sentence and table cell citing them, including the accuracy figures attributed to ref2 (~99.5 %) and ref18 (99.1 %).
- [ ] Run the same audit on the **EPSR paper draft** bibliography.
- **Hypothesis H7:** most of these 9 do not exist (neither Crossref nor title/author searches find them), so they cannot be repaired, only replaced or dropped.
- **Decision rules:**

| Outcome per reference | Action |
|---|---|
| a real paper supporting the same sentence is found (with DOI, read by the author) | replace, and record it in `reference_audit.md` |
| no real paper found | delete the citation **and** the claim it supported; rewrite the sentence without it |
| **Gate:** | **no submission** until the audit shows **0 UNVERIFIED** in both the thesis and the paper |

---

## N8. Paper update (≈ 2–3 days) — the claim is chosen by the N4/N6 outcome, not written in advance
- [ ] Table A (reproduced published methods), Table B (same-feature models), limitations from `REPORTING_NOTES.md`, push to GitHub.

**Claim templates (pick by the decision rule that fired):**
- **Claim A** (N4 row 1 and N6c row 1): "Under identical leak-free evaluation, the dual-path hybrid matches the security of a tuned harmonic-restrained 87T and exceeds its dependability by X pt (p…). It also outperforms six reproduced published methods on at least one metric without being worse on the other. It needs plant-specific training (plant-B zero-shot security 88 %)."
- **Claim B** (trade-off): "The hybrid offers a different operating point: [metric] higher, [metric] lower than [method]. It is the only one combining … within … ms."
- **Claim C** (beaten): "The contribution is the model-agnostic dual-path supervisory architecture and the evaluation protocol. The best classifier on this bench is X. Placing X inside the dual-path logic gives …."

**Target journal by outcome:**
- Claim A → EPSR (primary) / IJEPES.
- Claim B → EPSR.
- Claim C → EPSR or IEEE Access, as a methods/evaluation paper, with expectations lowered accordingly.

---

## Decision for later: winding capacitances (high-frequency realism)
- **Hypothesis HL:** if the HF-based methods (Simões, Ngaopitakkul) perform poorly, the main cause is the missing kHz content of the lumped plant, not the methods themselves.
- **Test (after N4):** their native dependability on **solid** internal faults, and whether their misses concentrate on traces whose post-event energy above 5 kHz is at the noise floor (`hf_content` method, per trace).
- **Decision rules:**

| Outcome | Action |
|---|---|
| solid-fault dependability ≥ 90 % | no plant change; limitation sentence only |
| < 90 %, and misses concentrate on HF-poor traces | **optional** sensitivity study: add winding capacitances to plant A, re-simulate **300 stratified traces** at 20 kHz, re-run only those two methods and the proposed relay. Report it as a separate, labelled study; v5 stays the main result |
| < 90 %, but misses do not concentrate on HF-poor traces | no plant change; the weakness is attributed to the method on this bench |

**Rough total to a submittable paper: about 1.5–2 weeks** (N1–N6 ≈ 6–8 days including unattended compute, N8 ≈ 2–3 days, N7 depends on the author).

---

## Review and decisions — 2026-11-02 09:15
Checked against `runs/20261101_v5_common_set/summary.txt`, `runs/20261101_v5_benchmark_fair/n2_simoes_factor.txt`, `simulations/powergui_freq_check.txt` and `documents/baselines/hr_missing_all.txt`. The work stopped after N2 (last commit 2026-11-01 23:45).

**N1: accepted.** H1a, H1b and H1c are confirmed; the rules were applied as written.
- N1b: the largest change is 0.04 pt. Use common-set numbers in the comparison tables.
- N1c: identical currents (0.0 A difference), so no regeneration. Add one Limitations sentence.
- **One deviation to close:** N1a's rule says "re-run once" for the plant-B OOD InternalHV family (1/14 = 7.1 %). This was skipped. **Decision D1:** do the single-trace re-run at the start of N4 (≈ 1 min of MATLAB). If it succeeds, include the trace; if not, keep n = 13 and report it. Reading "group" as the scenario family (phase suffix removed) is accepted.

**N2: accepted.** H2 is confirmed, and row 2 fired: factor 100 in 12 folds, 50 in 3.
- **Consequence, recorded now, before N4:** the detector finds only 86–92 % of events at these factors. Undetected events are "no trip" in native mode, so **Simões' native dependability is capped at about 86–92 %**. That is consistent with H4.1, and it must be explained in the paper as a detector/noise-floor limitation (`hf_content.txt`).
- **No further tuning of the detector is allowed.** The like-for-like mode (dwell + validation threshold) uses the same detector factor per fold.

**Decision D2, order of work (to use idle compute):**
1. Start **N6a (B1, equal training budget for the same-feature models)** now as an **unattended Python run**. It needs no MATLAB, and the RAM peak is ~1.7 GB, within the 4 GB rule.
2. While it runs, code **N3**: Ngaopitakkul, Abdusalam, Alhamd, each with its sanity check and the fold-1 training-accuracy gate (≥ 80 %, max two logged debug rounds).
3. Then **N4** (all six reproductions), starting with the D1 single-trace re-run. Then N5, N6b/N6c, N8.

**Decision D3:** N7 (the 9 unverified references) remains a **hard gate** for any submission. It is author work and can be done in parallel; nothing else depends on it.

**Expected time from here:** N3 ≈ 2–3 days, N4 + N5 ≈ 2 days (mostly unattended), N6 ≈ 1 day (partly overlapping), N8 ≈ 2–3 days.
