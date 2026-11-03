# Mock peer review for Electric Power Systems Research (audit task D)

**What was reviewed:**
- `paper_epsr/main.tex` (last changed in commit `71a950b`, 2026-10-30), with its generated macros and tables;
- the newer `paper_epsr/abstract_draft_N8b.txt` and Tables A–D (`paper_epsr/generated/table_[A-D]_*.tex`, 2026-11-04);
- the result files under `runs/20261101_v5_benchmark_fair/`.

**Important for the author.** `main.tex` still carries the **October framing**:
- the LSTM relay vs a textbook harmonic 87T;
- "five literature classifiers";
- McNemar "with continuity correction" on repetition 1;
- the abstract numbers 92.99 / 98.96 vs 85.93 / 99.40.

The November results (six reproductions, tuned harmonic 87T, claim C: "architecture, not classifier") are only in the abstract draft and Tables A–D. Reviewers would see both stories if the draft were sent as is. The reviews below assume the paper is rewritten to the N8b abstract and Tables A–D, and they flag where the current `main.tex` text would be attacked.

---

## Reviewer 1: protection engineer

**Summary.** A dual-path trip logic (87T vote AND confirmed classifier, OR a high-confidence classifier-alone path, OR high-set) evaluated on two simulated transformers against six re-implemented ML methods and a validation-tuned harmonic 87T. The testing effort is unusual and welcome. My concerns are about whether the logic is deployable and whether the conventional baseline is as strong as a practising engineer would set it.

**Major**
1. **The AI-alone (solo) path is a protection-philosophy problem.** A relay that can trip with no differential pickup at all needs a strong justification and supervision. In your own data:
   - on the unseen plant, the solo path caused 87 of the 89 false trips (`plantB_falsetrip_paths.txt`);
   - the plateau rule switched it off in 3 of 15 CV folds (`runs/20261029_v5_cv5_seeds/*/result.json`, settings);
   - it buys 4.52 pt of dependability on plant A (`gated_only_ablation.txt`).

   Please present the gated-only relay as at least an equal option, and give setting guidance (when the solo path should be enabled, and with what supervision: overcurrent? a fault detector?).
2. **The "tuned" harmonic 87T sits on the corner of its grid.**
   - Pickup 0.2 pu was chosen in **15 of 15** folds and k5 = 0.25 in 15 of 15: both are the lowest grid values.
   - k2 = 0.20 (the highest value) was chosen in 9 folds (`n6c_tuned_harmonic.txt`, chosen settings).
   - An optimum on the boundary means the conventional relay was not given room to improve. The 1.78 pt dependability gap of the deployed hybrid, and the 2.3–4.6 pt range of the instances, could shrink with pickup 0.1–0.15 pu or k5 < 0.25.

   Also missing: cross-blocking or 2-of-3 harmonic logic, and a waveform-based (dead-angle / gap) restraint, which most numerical relays offer.
3. **High-impedance "internal faults" are resistive terminal faults, not turn-to-turn faults.** About 65 % detection (`n6c_tuned_harmonic.txt`: hybrid 65.4 %, tuned harmonic 62.1 %, n = 459) is reported honestly. But the paper should say what these faults are physically and cite the turn-to-turn literature (see `literature_review.md` A4). Dedicated negative-sequence or incremental elements are the industry answer to this class.
4. **Operate time.**
   - The deployed hybrid's median is about 16 ms (the thesis protocol target is ≤ 16 ms). Reviewers from industry will compare this with commercial 87T operate times (to be cited from vendor or standard documents, not assumed).
   - Please give operate-time distributions (median / p90 / max) per method and per fault class from the saved rows (`operate_ms` is in every row file), and compare with the harmonic 87T's.
   - Also say what IEC 60255-187-1 asks you to declare.
5. **Plant realism.**
   - Lumped plants with no winding capacitance (almost no energy above 1.6 kHz) penalise the HF-based methods (Simões, Ngaopitakkul). You say this, but it means two of the six reproductions are tested off-design.
   - No CT remanence. No sympathetic inrush. Plant B fails two of its own physics criteria.
   - The current `main.tex` §3.2 calls the recovery inrush "sympathetic recovery after an external fault". Sympathetic inrush between parallel transformers was **not** modelled (`IMPLEMENTATION_PLAN_V3.md` §8.1). Remove the word.

**Minor**
- Give the 87T settings of plant B and how they were derived (they must not depend on plant-B outcomes).
- The latency numbers are PC measurements. Fine, but do not compare them with relay processing budgets as if they were relay figures.
- Table C: the tuned harmonic 87T is "n/e" on OOD and plant B. It is the strongest conventional baseline, so readers will want it there too (it needs only the saved traces, no retraining).

**Recommendation:** major revision.

---

## Reviewer 2: ML-methods reviewer

**Summary.** Unusually careful protocol: trace-grouped CV, validation-only thresholds, OOD scored once, six faithful reproductions with written specs, paired tests with Holm correction, and an explicit search budget. My concerns are about the statistics, fairness details and what the claim C framing implies.

**Major**
1. **Non-independent pairs in McNemar.** The three CV repetitions reuse the same traces, so 3,717 / 5,910 "pairs" are ~1,239 / ~1,970 traces counted three times.
   - A trace-clustered permutation test (`audit/scripts/out/clustered_sensitivity.txt`) removes significance from several reported results. Examples: hybrid-with-Key dependability p_Holm 9.7e-3 → 0.063; RF vs tuned harmonic security; textbook harmonic security; LSTM alone vs Alhamd dependability.
   - The pre-registered decisions survive, but the p-values in the tables are overstated. Use a cluster-aware test, or test per repetition and report the three.
2. **B2 is not nested, and the training data are not equal.**
   - The configuration search uses validation splits of seed 1, folds 1–3. The chosen configuration is then scored on all 15 fold-models, which include those traces as test data.
   - SVM / RF see 30 k / 50 k subsampled windows; the neural models see all of them.
   - The deployed LSTM was trained at window stride 8, the B2 models at stride 4. The Table B note and `b2_summary.txt` wrongly say "stride 4" for the deployed LSTM (`code_audit.md` C-1, C-3, C-4).
   - The post-hoc "tuned hybrid vs deployed hybrid" comparisons are therefore confounded. Compare against the tuned LSTM hybrid instead.
3. **What exactly is "model-agnostic"?**
   - Key's classifier with only dwell + threshold + high-set (no 87T gate, no solo path) reaches 97.23 / 99.56 on the CV (`n4_full_summary.txt`). Inside the dual-path logic it reaches 94.11 / 99.86 (`n5_statistics_keyhybrid.txt`). So for a well-calibrated classifier the 87T gate costs ~3 pt of dependability for ~0.3 pt of security.
   - The benefit of the gate is large only for the poorly calibrated LSTM: security 95.57 → 98.95 at a cost of −4.7 pt dependability.
   - The data support "a supervisory decision layer (dwell, validation threshold, high-set) works with any classifier". They do not support "the 87T gate is what makes classifiers secure". The author's own N8b notes say this. Make it the explicit conclusion, not a footnote.
4. **Reproducibility of training.** Two native runs of Key and Afrasiabi on identical folds disagree on 74 and 367 trace decisions (`results_audit.md` B-3). Report the run used for each row. Quantify run-to-run variance at least for these two methods; the data for that already exist.
5. **Reproductions with filled-in details.** Every UNSPECIFIED fill and every spec amendment (Ngaopitakkul's sanity check fails with noise; Alhamd re-run with a larger budget after a first result; Simões' detector factor) should be listed in a supplementary table, with its effect where both variants exist.

**Minor**
- Thresholds vary from 0.75 to 0.999 across fold-models of the same architecture (`result.json` settings). Say so, and show the per-fold sd (available: 3.60 / 0.81 pt for the deployed hybrid in the old macros).
- The OOD set was designed by the authors as range extensions. Call it a "shifted-range test", not general OOD. Give Wilson intervals: n ≈ 148 / 149, so ±3–4 pt.
- State that ~10 epochs were actually used under the 25 / 5 rule (B2 `epochs_used`). The budget cap was rarely binding.
- The paper's threshold rule says "lowest threshold in the longest range". The code (`train_trace_split.tune_threshold`) returns the **logit centre** of the longest run. Fix the text.

**Recommendation:** major revision. The work is publishable once the statistics are made cluster-robust and the claim is aligned with Table D and the like-for-like rows.

---

## Reviewer 3: sceptical "Reviewer 2"

**Summary.** Under the evaluation apparatus, the contribution is an AND/OR combination of an 87T vote and a classifier. The proposed LSTM is the weakest good instance of its own architecture.

**Major**
1. **Novelty of the logic.**
   - Combining a learned discriminator with the 87T and harmonic restraint by Boolean logic dates back at least to Rebizant, Bejmert & Schiel 2007 (PowerTech, DOI 10.1109/PCT.2007.4538488).
   - ML pre-filtering of the 87T input (Lin et al., TPWRD 2023, DOI 10.1109/TPWRD.2022.3230468) and ML adaptation of 87T settings (Rezaei, IET GTD 2026) also exist.
   - The role reversal (87T gates the AI) and the solo path are new as far as I can tell, but small. The paper should claim the **evaluation** as the main contribution and the logic as a secondary one.
2. **Why propose the LSTM at all?**
   - Table D shows CNN 95.7 / 99.0, GRU 95.6 / 98.8, MLP 94.9 / 99.2 and Key 94.1 / 99.9, all above the deployed LSTM (93.0 / 99.0).
   - The LSTM also has the worst zero-shot security (88.4 % vs 99.9 % for Key).
   - If the LSTM is kept only because the Simulink closed loop uses it, say so in the abstract. Otherwise the title's "wavelet-feature LSTM" (current `main.tex`) is misleading.
3. **The headline moved with the results.**
   - The plan pre-registered claims A/B/C (`BENCHMARK_FAIRNESS_PLAN.md`, git `38c5eaa`, 2026-11-01). That is good, and the original rules were never edited.
   - But several later rules were written after their descriptive results were visible:
     - the like-for-like extension of claim C;
     - H6, after one fold was seen;
     - the D-N8a family and the "range-only" wording, timestamped after the D-N8a result.
   - The plan sections containing them were committed only at the end (`results_audit.md` B3).
   - "Pre-registered" should be used only for the 2026-11-01 rules.
4. **Draft inconsistent with results.** See the note at the top: abstract, contributions, Table 6.x set and statistics all describe the October analysis.
5. **References.**
   - Related work is all `[cite: …]` placeholders.
   - The thesis has 9 unverifiable references (`documents/reference_audit.md`).
   - Lin et al. would be cited as an arXiv 2026 preprint although it is a 2023 TPWRD paper.
6. **Data availability.**
   - The datasets (.mat) and trained models are not public.
   - "Regenerated by the scripts" requires MATLAB R2023a with Simscape and about a day of simulation (`reproducibility.md`).
   - EPSR asks for a data statement. A Zenodo deposit of the traces, or at least the features plus per-trace results, would make the benchmark claim credible.

**Minor**
- Generative-AI use: the repository shows that much of the code and analysis was produced with an AI coding assistant. The journal requires a declaration (`journal_checklist.md`).
- Length: the material (6 reproductions, 4 tables, 2 plants, closed loop, latency) is close to two papers.

**Recommendation:** major revision (borderline reject if the novelty claim is not reduced).

---

## Meta-review

**Consensus.** Rigorous and honest evaluation, above the usual standard for ML-based 87T papers. The paper must:
- (i) be rewritten to the results it actually has (claim C);
- (ii) fix the statistics (clustered pairs) and the B2 confounds;
- (iii) strengthen or qualify the conventional baseline;
- (iv) reduce the novelty claim for the logic itself and treat the solo path as an option.

### The 10 most likely reviewer requests, ranked

| # | Request | Already answered in the repo? | What is missing (text / reporting / analysis of existing data only) |
|---|---|---|---|
| 1 | Rewrite the paper to the current results: abstract, contributions, tables, and no "LSTM beats" framing | Partly: `abstract_draft_N8b.txt`, `generated/table_[A-D]_*.tex` | `main.tex` sections 1, 5, 6, 8, 9 and the title still use the October story; the old tables 6.1–6.8 must be replaced or reconciled with Tables A–D |
| 2 | Cluster-robust significance tests (repeated-CV pairs are not independent) | **Yes, by this audit:** `audit/scripts/clustered_sensitivity.py` and its output | Report clustered (or per-repetition) p-values in Tables A–D. Five "*" marks must go: Key-hybrid dependability, RF-hybrid security vs tuned harmonic, textbook-harmonic security, LSTM alone vs Alhamd dependability, and the per-test list in `results_audit.md` B1a |
| 3 | Justify the conventional baseline: grid-corner optimum, cross-blocking, waveform restraint | No | Text: admit the grid-corner choice (`n6c_tuned_harmonic.txt`). Analysis without new simulations: the harmonic 87T is computed from saved currents, so a wider pickup / k5 grid (e.g. 0.1, 0.15 pu; k5 0.15–0.25) is cheap. But it needs the .mat datasets (local machine), and it must be labelled post-hoc. Otherwise state it as a limitation |
| 4 | Is the AI-alone path acceptable? Present the gated-only relay | Yes: `gated_only_ablation.txt`, `plantB_falsetrip_paths.txt`, Table D ablation rows | Text: make the gated-only variant a first-class option with its numbers (88.43 / 99.42 CV, 90.47 / 99.21 plant B); say that the solo path was off in 3 / 15 folds |
| 5 | What does "model-agnostic" mean, given that Key like-for-like beats Key-hybrid on dependability? | Yes: `n4_full_summary.txt`, `n5_statistics_modeb.txt`, `n5_statistics_keyhybrid.txt`, log 2026-11-04 00:08 | Text: one paragraph saying the gate's value depends on classifier calibration, with the 97.23/99.56 → 94.11/99.86 (Key) and 95.57 → 98.95 security (LSTM) numbers |
| 6 | B2 fairness: nested search, stride, subsampling | Partly: the B2 note mentions the search budget and unique configs | Text: correct "stride 4" → **stride 8** for the deployed LSTM (Table B note, `b2_summary.txt` label). Add "search on seed-1 folds 1–3, not nested" and "SVM / RF fitted on 30 k / 50 k windows". Make the tuned LSTM hybrid the like-for-like reference |
| 7 | Operate-time comparison across methods and fault classes, vs relay practice and IEC 60255-187-1 | Data yes: `operate_ms` in every row file; median times in `n4_progress.txt` | Analysis: a table of median / p90 per method and class from saved rows (no new run). Text: cite IEC 60255-187-1 / C37.91-2021 without inventing a limit |
| 8 | Related work and novelty against Rebizant 2007, Lin 2023, Rezaei 2026; recent EPSR/IET competitors | **Yes, by this audit:** `audit/literature_review.md`, `audit/literature_table.csv` | Text: related-work section; replace every `[cite: …]`; add Holm, Roberts, C37.91-2021; cite Lin et al. as TPWRD |
| 9 | Physical meaning of "HiZ internal faults"; turn-to-turn limitation; sympathetic inrush wording | Partly: limits in `main.tex` §8; HiZ numbers in `n6c_tuned_harmonic.txt` | Text: define the HiZ fault model (terminal fault through Rf). Cite the turn-to-turn literature. Remove "sympathetic" from the recovery-inrush description |
| 10 | Data and code availability, reproducibility of training | Partly: code and per-trace results on GitHub; trace metadata light file | Data deposit (features or traces) or an explicit statement of what is withheld; seeds and run order (`audit/reproducibility.md`); report run-to-run variance for Key / Afrasiabi from the two existing runs |

**Also likely:** a pre-registration wording fix (`results_audit.md` B3); the threshold-rule text ("logit centre", not "lowest"); a list of spec fills and amendments in a supplementary table; the generative-AI declaration.
