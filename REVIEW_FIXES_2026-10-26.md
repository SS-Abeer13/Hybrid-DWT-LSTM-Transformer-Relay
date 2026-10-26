# Review Fixes — 2026-10-26

**Reviewed:** GitHub `main` @ `f92ea33` (pushed 2026-10-26), plus the saved result files in `F:\Transformer Thesis`.
**Scope:** code, pipeline and results first; manuscript statements checked against the result files.

**Verdict:** the experiments are trustworthy, but the manuscript is not yet. The review-response rounds (Round 2–4) rewrote result text without checking it against the result files. Fix P1 before anyone reads the thesis.

---

## How to use this file (for the next Claude Code session)

1. Work top to bottom: P1, then P2, then P3.
2. For every fix, take numbers **only from saved output files** (rule in `CLAUDE.md`). Never type a number into `rebuild_thesis_manuscript.py` by hand.
3. After each fix, rebuild `latex_source/latex/main.tex` / `main.pdf`, tick the box below, and add a dated entry to `IMPLEMENTATION_PLAN.md`. Use the real date from the system clock.
4. Do not push. Commit without any Claude trace (rule in `CLAUDE.md`).

---

## What is already sound (keep as is)

- **No leakage.** Folds are by trace. Thresholds are tuned on validation traces only (plateau rule). Labels start `ONSET_MARGIN` = 8 samples after the measured fault onset. Trips before onset on fault traces count as errors (`train_trace_split.py: relay_report`).
- **Python mirror = Simulink.** `lstm_models/relay87t.py` matches the `Hybrid_87T_Decision` chart (`chart_34.xml` in the `.slx`): same pickup, slopes, high-set and handshake. `features12.py` matches `DWT_Feature_Extraction` (`chart_11.xml`).
- **The benchmark is fair.** `benchmark_literature_models.py` uses the same `StratifiedKFold` code and seed (20261021) as `train_cv_v3.py`, so the folds are identical. It also uses the same threshold rule, the same dwell (20) and the same hybrid wiring. One minor asymmetry: baselines get 15 epochs / patience 4 vs 25 / 5 for the LSTM.
- **The headline numbers match the files:**

| Claim | Value | Source |
|---|---|---|
| Hybrid + AI-alone path, CV (3 seeds × 5 folds) | dependability 99.01 %, security 99.66 % | `runs/20261021_v3_cv5_seeds/summary.txt` |
| OOD, final model | dependability 92.4 %, security 100 % | `runs/20261022_v3_final/report_ood.txt` |
| HiZ AI-only band | 71.2 % (57/80) | `analyze_hiz_v3.py` output |
| Benchmark Table (`table_literature_benchmark.tex`) | all dep / sec / acc / false-trip values | `runs/literature_benchmark/literature_benchmark_summary.json` |
| Simulink vs Python | 50/50 decision agreement | `simulations/closed_loop_vs_python_v3.txt` |

---

## P1 — Must fix: the manuscript contradicts the result files

### P1.1 Table 6.5 (closed loop) does not match the closed-loop run  🚨
- **Where:** `main.tex` Table 6.5 (`tab:6.5`), around line 723. The values are hard-coded in `rebuild_thesis_manuscript.py` (around line 744) and `update_rebuild_script.py` (around line 753). Also check the claims at line 284 ("100 % decision accuracy") and line 721.
- **Evidence:** the only 12-case run on record is `simulations/test_hybrid_relay_v3_results.txt` (21-Oct-2026 18:30:45). No result file contains the thesis values 0.9994, 16.2 ms or 0.0249.

| Case | Thesis | Saved run |
|---|---|---|
| Internal HiZ | Rf 2.0 Ω, prob 0.9994, 16.2 ms, PASS | Rf 3 Ω (AI-only bin), prob 1.0000, **47.5 ms, FAIL** |
| Fault during inrush | loaded, prob 0.9998, 15.6 ms, PASS | A-B-G, prob 1.0000, **41.3 ms, FAIL** |
| Internal HV | Phase A-G, "10 % winding", 15.0 ms | Phase A-B, HV terminal, **0.6 ms** |
| Internal LV solid | Phase A-B-G, 15.6 ms | Phase A-G, 15.0 ms |
| SOTF | 0° angle, 15.0 ms | A-B, 13.8 ms |
| External + CT saturation | prob 0.0249 | External A-G, 8× burden, prob 0.0002 |
| External 3-phase | prob 0.0001 | prob 0.0000 |

- **Fix:** generate Table 6.5 from `test_hybrid_relay_v3_results.txt` with a script, not by hand. Report "**12/12 trip decisions correct; 10/12 within the 30 ms criterion**". Remove "10 % winding": the model has **terminal faults only** (see `documents/results_v3/limitations.md` §1).
- [x] Done

### P1.2 The 87T described in the thesis is not the one that was tested  🚨
- **Code (`relay87t.py`) and Simulink chart:** `I_pickup 0.30`, `Slope_1 0.25`, `Slope_2 0.60`, `Breakpoint 3.0 pu`, high-set 10 pu on the **sliding true RMS**, and **no harmonic restraint or blocking at all**.
- **Thesis says:**
  - line 378: S1 = 15 %, S2 = 40 %, knee 2.0 A (2.15 pu), breakpoint 0.67 A;
  - line 562: `87T_Trip = 1 if Id > Iop(Ir) and k2 < 15 %`;
  - line 777: "Conventional 87T … with second-harmonic blocking";
  - line 652 (§6.3): the inrush false trips are explained by "transient sub-cycle dips in the sliding FFT harmonic ratio k2(t) … before the 2nd-harmonic filter stabilizes", and HighSet "is evaluated on the fundamental-frequency phasor".
- **Why it matters:** every "Conventional 87T" number (79.62 % / 52.96 %, 881 false trips) comes from a relay **without** harmonic restraint. The §6.3 explanation describes a mechanism that cannot occur in the tested relay.
- **Fix:** describe the 87T exactly as coded: settings, no harmonic restraint, true-RMS high-set. Rewrite §6.3: the inrush false trips occur because the tested 87T has no harmonic restraint. Remove "with second-harmonic blocking" and the k2 term from the trip equation (or label that equation "classical scheme, not implemented"). If you add P2.1, describe both relays.
- [x] Done

### P1.3 Latency numbers are typed in, not measured
- **Where:** `benchmark_literature_models.py` lines 367–369, 435, 466, 497, 525, 556 set `latency_ms` to constants (0.6, 1.15, 1.25, 0.08, 0.22, 0.95, 0.12, 0.15). Wavelet-RF `params` = `100 * 2500` (invented; a forest has no such count). `main.tex` line 818 and Table A (line 932) quote "0.44 ms ONNX latency on CPU"; no script produces that number.
- **Fix:** either **measure** latency (`onnxruntime` / `torch` inference over ≥ 1,000 windows, warm-up excluded, report median and p99, state the CPU) and write it to a results file that the table reads, or **remove the latency column and the 0.44 ms claim**. For RF, report the number of tree nodes or drop the parameter count.
- [x] Done

### P1.4 Plant description contradicts the measurements
- **Where:** `main.tex` line 470 (§4.4).
- **Thesis:** "A series limiting resistance R_series = **0.05 Ω** is **inserted** … to reflect stiff utility-feeder current limits … CT saturation is rigorously driven by burden (4×–16×) and **remanence sweeps**."
- **Measured (`IMPLEMENTATION_PLAN.md`, 2026-10-21 entries; `CLAUDE.md`):** three **0.5 Ω** resistors were **already** in the LV line and are part of the LV CT drive (lowering them to 0.02 Ω destroyed the LV CT output). The weak external faults (~1.5 pu) are a **limitation**, not a design choice. **CT remanence has no effect** in this model (the core-loss branch decays it in ~25 ms) and was dropped.
- **Fix:** rewrite §4.4 to match `limitations.md` §2: an existing 0.5 Ω resistance, weak external faults as a stated limitation, CT saturation from burden only, no remanence.
- [x] Done

### P1.5 "Fault-clearing time" is relay operate time
- **Where:** `main.tex` line 818 ("median end-to-end physical fault-clearing time is 15.6 ms") and the note under `table_literature_benchmark.tex` ("Med. T_op denotes the end-to-end median physical fault-clearing operating time").
- **Fix:** call it **relay operate time** (fault inception to trip decision). Breaker opening is not modelled.
- [x] Done

---

## P2 — Should fix: claims stronger than the evidence

### P2.1 Add a fair harmonic-restrained 87T baseline (strongly recommended)
- **Why:** reviewers and examiners will call the current baseline a straw man, because every commercial 87T has 2nd-harmonic restraint. The Round 2–4 responses argued around this instead of testing it.
- **Do:** in `relay87t.py`, add a variant `analyse_harmonic()`:
  - per-phase k2 = |I_d,100Hz| / |I_d,50Hz| over the 32-sample window, block when k2 > 15 %;
  - k5 = |I_d,250Hz| / |I_d,50Hz|, block when k5 > 35 %;
  - optional cross-blocking;
  - a start-up dwell of one cycle (vote must persist for 32 samples).
  
  Score it on the same CV folds (out-of-fold rows from `runs/20261021_v3_cv5*`) and on the OOD set, as an extra row in the ablation and benchmark tables. Report it honestly, even if it narrows the gap.
- **Effort:** a few hours of Python. No MATLAB needed.
- [x] Done

### P2.2 Tone down the benchmark narrative (§6.10, `main.tex` lines 791–795)
Data from `literature_benchmark_summary.json` (Repetition 1, same folds for all models):

| Model | Mode | Dependability | Security | Accuracy | False trips |
|---|---|---|---|---|---|
| Wavelet-RF | standalone | 98.64 % | 99.89 % | **99.39 %** | 2 |
| Standalone LSTM | standalone | 99.04 % | 99.31 % | 99.20 % | 13 |
| 1D-CNN | hybrid | 97.76 % | 99.95 % | 99.07 % | **1** |
| Wavelet-RF | hybrid | 97.12 % | 99.95 % | 98.82 % | **1** |
| **Proposed hybrid DWT-LSTM** | hybrid | **98.56 %** | 99.41 % | 99.07 % | **11** |

| Thesis claim | Correction |
|---|---|
| "achieves the highest balanced performance across the entire corpus" | Not true by accuracy: Wavelet-RF standalone is highest (99.39 %). The proposed hybrid has the **most false trips of all hybrid variants** (11 vs 1 for RF and 1D-CNN; Fisher exact test, one-sided, p ≈ 0.003). |
| "Deep sequence models decisively outperform static classifiers" | Only vs SVM. Against RF the gain is 0.3–0.6 pt dependability, with lower security. Say "slightly higher dependability". |
| "embedding … guarantees deterministic 87T security" | False: the AI-alone path trips **without** an 87T vote, and that is where the 11 false trips come from. |
| "superior resilience on high-impedance internal faults during recovery inrush" (line 792) | No such scenario exists in the dataset. Remove. |
| "Comparison with Deterministic Wavelet Schemes" (line 795) + Round-4 commit "benchmark deterministic wavelet schemes" | Nothing was run. Label it as a qualitative discussion, or implement BDWT. |

- **Honest framing that still holds:** the **dual-path supervisory architecture** is the contribution. It raises security for every classifier (e.g. 1D-CNN 99.36 → 99.95 %), and with the LSTM it gives the **highest hybrid dependability (98.56 %)** and the fastest median operate time (15.6 ms). The price is a few more AI-alone false trips. That matches the reviewer's Round-2 advice to frame the novelty around the handshake.
- [x] Done

### P2.3 Smaller statements to verify or remove
- [x] HighSet "evaluated on the fundamental phasor" (line 652): the code uses true RMS. Fix the text.
- [x] "HighSet never trips during inrush (I_d,fund < 4.5 pu)" (line 652): no file supports 4.5 pu. Compute the max high-set RMS over inrush traces from the cached traces, or remove.
- [x] "≈ 0.67 pu path impedance", "23.6 kA" (line 470): only keep if derived from model parameters; otherwise drop with P1.4.
- [x] IEC 60255-187-1:2021 / IEEE C37.91-2021 / C37.110-2023 compliance wording: state "settings chosen with reference to", not "complies with", unless a compliance test was done.

### P2.4 Make the manuscript build data-driven
- `rebuild_thesis_manuscript.py` (112 KB) holds the whole thesis text with numbers typed in. That is how a FAIL became a PASS.
- **Do:** every results table (6.1, 6.3, 6.5, 6.7, the benchmark table, OOD, HiZ bins) is generated from its result file by a script, extending `lstm_models/make_tables_v3.py`, and `\input{}` into `main.tex`. Prose numbers use `\newcommand` macros written by the same script (e.g. `\DepCV{}` = 99.01).
- **Check:** grep the rebuild script for digits in results sections; none should remain.
- [x] Done

---

## P3 — Record-keeping (low priority, but do it once)

- [x] `IMPLEMENTATION_PLAN.md`: entries are dated "2026-10-22 …" but all files were written on 2026-10-21. Re-date them from file timestamps.
- [x] Log the work of 2026-10-23 to 10-25: literature benchmark, Round 2–4 manuscript revisions, push to GitHub.
- [x] Replace the stale "Next steps" section (it still lists the v2 steps) with a pointer to this file.
- [x] Re-word overclaiming commit messages in future commits (e.g. "100 % publication readiness", "benchmark deterministic wavelet schemes", "pristine manuscript").

---

## Out of scope for the thesis (needed for a journal paper)

- Strong external through-faults (5–20 pu): needs the LV CT subsystems re-engineered so the 0.5 Ω resistors can be reduced.
- A second plant rating and/or HIL (RTDS / OPAL-RT) or field COMTRADE data.
- Measured inference latency on relay-class hardware.

## Appendix — repo hygiene (deliberately last)

If the repo is public: remove the copyrighted journal PDFs (`documents/Reference Papers/`, the bundled PDFs in the MIST template folders). Also remove the third-party binary `tools/matlab-mcp-server.mcpb`, `simulations/lstm_diagnostics.txt` (36 MB) and the `latex_source/_miktex_local*` caches, and add them to `.gitignore`. Set `git config user.email` to the GitHub noreply address (7 commits use `abeer13@local`).
