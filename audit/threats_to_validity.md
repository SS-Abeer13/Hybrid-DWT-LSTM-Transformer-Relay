# Threats to validity: draft section for the paper (audit task G)

Every number below is quoted from a saved file (path given) or recomputed by `audit/scripts/` from saved files. This is a draft for the author to shorten and edit; the wording aims to be specific, not defensive.

---

### Construct validity: does the benchmark measure relay performance?

**1. Simulated data only.**
- All traces come from two Simulink / Specialized Power Systems models. There is no hardware-in-the-loop test, no record from a real transformer and no field data (`README.md`, Status).
- The closed loop shows only that the Simulink relay reproduces the Python mirror: 50 of 50 decisions agree (`simulations/closed_loop_vs_python_v5.txt`). It is not an independent validation.
- Half of those 50 traces are validation traces of the final model, i.e. traces that set its thresholds (`closed_loop_vs_python_v5.txt`, header).

**2. Two plants, both lumped.**
- Plant A: 300 MVA YNd1. Plant B: 40 MVA Dyn11 (`README.md`).
- There are no winding capacitances. After an event, the share of differential-current energy above 5 kHz ranges from 3.27e-6 (fault in inrush) to 3.22e-1 (recovery inrush), and is at most 3.49e-3 for every internal-fault group (Internal HiZ; `documents/baselines/hf_content.txt`, 12 traces per group). Before the event, noise alone puts 4.5e-2 to 5.0e-1 of the energy above 5 kHz.
- Methods that rely on high-frequency content therefore work off-design here:
  - Simões et al.: the detector finds 86.1 % of events at the chosen factor 100 (`n2_simoes_factor.txt`);
  - Ngaopitakkul & Kunakorn: its own sanity check holds on noise-free currents but fails with measurement noise (`documents/baselines/ngaopitakkul2006_sanity.txt`).
- Their low scores are a statement about this bench, not about the methods.

**3. Plant B fails two of its own pre-set physics criteria** (`simulations/plant_v5_checks_B.txt`):
- C4: a DC offset at maximum asymmetry does not saturate its CTs at nominal burden (max deviation 1.5 % vs the > 10 % criterion);
- C6: ratio drift at 3× burden, the "2.02 %" reported in `main.tex`;
- overall: FAIL.

Plant-B results, including every zero-shot number, carry this caveat.

**4. CT remanence is not modelled.** The CT subsystems have no remanent flux. External faults with a remanent CT, which are the classic source of 87T mis-operation on re-energisation, are therefore absent (thesis model note in `CLAUDE.md`; no remanence parameter in `trace_metas_plantA.json`, which lists residual flux only for the power transformer: `fluxBin`).

**5. No sympathetic inrush.**
- Sympathetic interaction between parallel transformers was not modelled (author decision A6, `IMPLEMENTATION_PLAN_V3.md` §8.1).
- The scenario called "Recovery_Inrush" is the inrush of the protected transformer after an external fault is cleared. It must not be described as sympathetic (the current `main.tex` §3.2 does).

**6. Fault model.**
- Internal faults are terminal faults through a fault resistance (LV and HV side). There are no turn-to-turn faults (`main.tex` Limitations).
- The "Internal_HiZ" category is therefore a resistive terminal fault class. It is not a proxy for inter-turn faults.

**7. Strength of external faults.**
- On the **v5 plants used in the paper**, the true steady through-fault current is 7.39 pu RMS (plant A) and 8.64 pu (plant B) (`simulations/plant_v5_checks_A.txt` C2; `README.md`). This is inside the 7–15 pu criterion.
- With nominal burden, CT deviation in the first two cycles is 8.1–11.5 % (plant A, ibid. 3.1–3.2). That is mild: CT-saturation stress comes mainly from the 4–10× burden traces.
- The thesis model (v3) had only ~1.5 pu RMS external faults at the CTs because of the LV series resistors (`IMPLEMENTATION_PLAN.md:259-263`). Thesis results must keep that limitation; paper (v5) results need not, but should state the through-fault level.

### Internal validity: are the comparisons fair and the conclusions supported?

**8. Reproductions are built from papers, not from the authors' code.**
- Each of the six methods follows a written specification (`documents/baselines/*_spec.md`). UNSPECIFIED details were filled before any result, and amendments were logged.
- Amendments that came after a first result:
  - Ngaopitakkul sanity (amendment 8);
  - Alhamd re-run with the paper's budget after a reduced-budget result of 85.79 / 54.91 (amendment 9; both reported, `alhamd_reduced_budget/`);
  - Simões detector factor (pre-set rule N2).
- Several papers are internally inconsistent: Abdusalam (selector and feature counts), Afrasiabi (text vs Fig. 1). Where both variants were run, the gap is reported (e.g. Abdusalam BA vs GA + SVM: 76.4 / 99.9 vs 77.2 / 99.9, Table A note).
- A different reasonable fill could change a reproduction's row by several points. The rows are evidence about method families on this bench, not verdicts on the papers.

**9. Native vs like-for-like.**
- Every reproduction changes by more than 5 pt between its native decision rule and the like-for-like mode (`n4_full_summary.txt`).
- In like-for-like mode, Key's classifier reaches 97.23 / 99.56 and Alhamd's 97.93 / 98.17. That is more dependable than the proposed hybrid (92.95 / 98.95) at similar security.
- "Which method is better" therefore depends on the decision layer, and the paper's claim is limited to it.

**10. Post-hoc analyses**, labelled as such in the log and tables, which must stay labelled in the paper:
- the like-for-like extension of the claim-C rule (written after the descriptive like-for-like numbers);
- the second B2 test family (tuned hybrids vs the deployed hybrid);
- the gated-only ablation;
- the N8a comparison of six instances with the tuned harmonic 87T (its Holm-16 family and "range-only" rule are dated after the result: `audit/results_audit.md` B3);
- the plant-B trip-path counterfactual;
- the Alhamd latency re-measurement.

Only the rules committed in `38c5eaa` (2026-11-01) can be called pre-registered.

**11. Unequal details in the "equal budget" comparison** (`audit/code_audit.md` C-1, C-3, C-4):
- the deployed LSTM was trained at window stride 8, the B2 models at stride 4;
- the B2 configuration search used validation traces of seed 1, folds 1–3, which are test traces of other fold-models (not nested);
- SVM and random forest were fitted on 30,000 / 50,000 subsampled windows.

**12. Baseline tuning range.**
- The validation-tuned harmonic 87T chose the lowest pickup of its grid (0.2 pu) and the lowest k5 (0.25) in all 15 fold-models (`n6c_tuned_harmonic.txt`). Its optimum may lie outside the grid.
- The gaps reported against it are the deployed hybrid's −1.78 pt and the instances' +2.31 to +4.57 pt (`n6c_tuned_harmonic.txt`, `n8a_instances_vs_tuned_harmonic.txt`). They are upper bounds for a better-tuned conventional relay.

### Statistical conclusion validity

**13. Repeated-CV pairs are not independent.**
- The McNemar tests pool three repetitions, so each trace counts three times (3,717 fault "pairs" from 1,239 traces).
- With a trace-clustered permutation test, the pre-registered decisions are unchanged, but individual results lose significance (`audit/scripts/out/clustered_sensitivity.txt`). Examples:
  - hybrid with Key vs proposed hybrid, dependability +1.16 pt: p_Holm50 9.7e-3 → 0.063;
  - textbook harmonic security +0.44 pt;
  - random-forest hybrid security vs tuned harmonic +0.42 pt.

**14. Per-seed instability.**
- Fold-model spread of the deployed hybrid: dependability 93.03 ± 3.60 % (min 86.43, max 97.59); security 98.96 ± 0.81 % (min 96.73) (`runs/20261029_v5_cv5_seeds/summary.txt`).
- The Key-hybrid dependability gain is −0.16 / 0.00 / +3.63 pt over the three seeds (`n5_statistics_keyhybrid.txt`). The tuned-harmonic gap is −2.66 / −2.82 / +0.16 pt (`n6c_tuned_harmonic.txt`).
- 9 of the 22 B2 tests and 4 of the 12 N8a tests carry the "unstable" flag (`b2_summary.txt`, `n8a_instances_vs_tuned_harmonic.txt`). Fold-model sd exceeds 3 pt for Key security (8.62), Afrasiabi security (4.39), Alhamd security (4.36) and Ngaopitakkul dependability (3.39) (`n5_statistics.txt`).
- Per-fold thresholds of the deployed hybrid range from 0.75 to 0.999. The AI-alone path was switched off by the plateau rule in 3 of 15 fold-models (`runs/20261029_v5_cv5_seeds/seed_*/fold*/result.json`, settings).

**15. Training is not bit-reproducible.** Two native runs of Key and Afrasiabi on identical folds disagree on 74 and 367 of 9,906 (seed, fold, trace) decisions. Afrasiabi: 87.06 / 89.56 vs 86.71 / 88.63 (`key/`, `afrasiabi/` vs `full/key/`, `full/afrasiabi/`; `audit/results_audit.md` B-3).

### External validity: does it generalise?

**16. Zero-shot transfer fails for the deployed LSTM.**
- On plant B, security is 88.35 % (89 false trips of 764 healthy traces), and 87 of the 89 come from the AI-alone path (`plantB_falsetrip_paths.txt`).
- The same logic with Key's classifier gives 99.87 % (`n5_statistics_keyhybrid.txt`). Transfer therefore depends on the classifier, and only two classifiers were scored zero-shot in hybrid mode.

**17. High-impedance internal faults remain the main weakness.**
- Internal_HiZ dependability (n = 459): 65.4 % for the hybrid, 62.1 % for the tuned harmonic 87T, 51.0 % for the textbook 87T (`n6c_tuned_harmonic.txt`).
- About one in three such faults is missed by every method evaluated.

**18. OOD set.**
- The OOD set extends the generator's ranges: extreme load, weak source, frequency offset, extreme burden, severe over-excitation, high noise (`main.tex` §3.2).
- It is scored once, but it is small (reproductions: n = 148 fault / 149 healthy; `n5_statistics_keyhybrid.txt`) and designed by the authors. It is a shifted-range test, not an unknown-distribution test.

**19. Latency is measured on a PC, not a relay.**
- Deployed pipeline: median 139.6 µs, p99 218.9 µs with ONNX Runtime (`runs/20261029_v5_latency/latency.txt`); hand-written ANSI C median 175.9 µs, p99 228.9 µs (`latency_c.txt`). Both on an AMD Ryzen 7 7700, against a 625 µs sample period.
- Reproductions: single-thread Python on the same PC (`latency_baselines.txt`). Alhamd's trained configurations: median 1,166–1,169 µs against a 1,667 µs budget, with p99 at or above it (1,674–1,747 µs) (`latency_alhamd_trained.txt`). Abdusalam's features take 608,796 µs per decision against 2,500 µs.
- None of these figures transfers directly to a relay processor.

**20. Data-path differences.**
- Reproductions use 20 kHz re-simulations with a different noise realisation. The proposed relay decides identically on 429 of 432 checked traces (`documents/baselines/d3_equivalence.txt`).
- 30 of the 3,332 plant-A traces have no 20 kHz copy and are excluded from all comparisons (`documents/baselines/hr_missing_traces.txt`). The effect on the proposed relay is ≤ 0.04 pt (`runs/20261101_v5_common_set/summary.txt`).
