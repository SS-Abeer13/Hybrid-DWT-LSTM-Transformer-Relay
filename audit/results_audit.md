# Independent results audit (audit task B)

Date: 2026-11-03. Every number here comes from a script under `audit/scripts/` run on the files committed in `runs/` (commit `bfc2f1d`), or is quoted with its file.
Scripts (independent code path: they do not import `tools/` or `lstm_models/`):
- `audit/scripts/recompute_stats.py` → `audit/scripts/out/recompute_stats.txt`
- `audit/scripts/clustered_sensitivity.py` → `audit/scripts/out/clustered_sensitivity.txt/.json`
- `audit/scripts/check_log_claims.py` → `audit/scripts/out/log_claims.csv/.txt`

Statistics libraries: `scipy.stats.binomtest` (exact McNemar) and `statsmodels.stats.multitest.multipletests(method="holm")`.

---

## Summary (worst first)

| # | Finding | Severity | Can it change a reported number or verdict? |
|---|---|---|---|
| B-1 | **The pooled McNemar tests treat the 3 CV repetitions as independent.** Each trace is counted 3 times: 3,717 fault "pairs" = 1,239 traces × 3. Re-tested with a trace-clustered permutation test, **15 of the reported "significant after Holm" verdicts become non-significant**, including Key-hybrid dependability (+1.16 pt). **No pre-registered decision rule changes outcome.** | **major** | Yes: p-values and some "*" marks in Tables / text. Decisions: no |
| B-2 | **Rules dated after the results they govern.** The review "2026-11-04 00:10" (which sets the D-N8a Holm-16 family and the "range only" headline rule) is timestamped **after** the D-N8a result (log 00:08, commit `ac92555` 00:08:24 +0600). The review "2026-11-03 09:45" is quoted by a log entry timed 09:41. **All four review sections of `BENCHMARK_FAIRNESS_PLAN.md` from 2026-11-02 20:30 onward were first committed in `644ba1e` (2026-11-04 00:13 +0600), after every result.** | **major** (for a "pre-registered" claim) | No number. It changes what may be called "pre-registered" |
| B-3 | Two native runs of Key and Afrasiabi exist, with different decisions on the same (seed, fold, trace): Key 74 traces, Afrasiabi 367. The log/plan of 2026-11-02 quote the first run; N5 and Table A use the second. The appendix row "Afrasiabi without the Hajipour stage" comes from the first run. Run-to-run variance (Afrasiabi: 87.06 / 89.56 vs 86.71 / 88.63) is as large as the stage effect being reported. | major (reproducibility) | Yes: the "stage is nearly inactive" comparison mixes runs |
| B-4 | All **112 recomputed tests** (24 + 48 + 2 + 4 + 12 + 22) and the **gated-only ablation** match the saved files exactly: 0 mismatches > 0.01 pt, 0 count or p-value mismatches, Holm family sizes as reported. | — | No |
| B-5 | 362 of 363 numbers in the log entries of 2026-11-02, 2026-11-03 and 2026-11-04 00:08 match the files. The one mismatch is a range that mixes the CV and OOD sets. | minor | Text only |
| B-6 | `tools/n5c_keyhybrid.py:51` writes the proposed-hybrid OOD / plant-B numbers as typed literals ("OOD 97.99 / 96.00; plant B zero-shot 92.70 / 88.35") into `n5_statistics_keyhybrid.txt`. The values are correct (they match `gated_only_ablation.txt`), but this breaks the "never type numbers into a generator script" rule. | minor | No (values correct today) |
| B-7 | The header of `n5_statistics_modeb.txt` says "native decisions" but the file contains like-for-like rows. It was written before the header edit in commit `63b9e24`. Re-running `tools/n5_statistics.py` would change the header of `n5_statistics.txt`. | minor | No |

---

## B1. Recomputation from the per-trace JSON files

**Inputs found** (all present on GitHub):
- `runs/20261029_v5_cv5_seeds/seed_*/fold*/result.json` (proposed hybrid, LSTM alone, gated-only);
- `runs/20261101_v5_benchmark_fair/full/<method>/cv_seed*_fold*.json` and `final_*.json`;
- `b2_equal_search/final_seed*_fold*.json`;
- `n6c_tuned_rows.json`.

No input file was missing.

**Consistency checks** (`recompute_stats.txt`, section "fold/trace set consistency"):
- The proposed model has 9,996 (seed, fold, trace) keys = 3 × 3,332. Every reproduction has 9,906 = 3 × 3,302.
- The 30 missing traces are exactly the `hr_missing_traces.txt` set. No method has a key outside the proposed model's folds, so **the folds are identical for every method**.
- Every pair has the same label. Every pair with a scenario field has the same scenario.
- The `undetectable` flags agree with `fault_pu < 0.05` from `trace_metas_plantA.json` (0 disagreements).
- Proposed hybrid on the common set: 92.95 / 98.95 (n = 3,717 / 5,910). On all traces: 92.99 / 98.96. This matches `runs/20261101_v5_common_set/summary.txt`.

**Result per family:**

| File | Tests recomputed | Holm family (recomputed = reported) | Mismatches |
|---|---|---|---|
| `n5_statistics.json` | 24 | 24 | 0 |
| `n5_statistics_modeb.json` | 48 | 48 | 0 |
| `n5_statistics_keyhybrid.json` | 2 | 50 (48 + 2) | 0 |
| `n6c_tuned_harmonic.json` | 4 | 4 | 0 |
| `n8a_instances_vs_tuned_harmonic.json` | 12 | 16 (12 + 4 of N6c) | 0 |
| `b2_equal_search/b2_summary.json` | 22 | 22 (12 planned + 10 post-hoc) | 0 |
| `gated_only_ablation.json` | 2 (raw p) | — | 0 |

Each test compares n, both percentages, the difference, both discordant counts, the exact p and p_Holm. The Table B values recomputed from `final_seed*_fold*.json` also match `b2_summary.txt`. Line-by-line output: `audit/scripts/out/recompute_stats.txt`.

**Holm family choice (informational).** The B2 planned family alone (12 tests) gives the same significance pattern as the 22-test family; the smallest change is "RF hybrid vs tuned LSTM, security", p_Holm 0.105 → 0.067, still n.s. The Key-hybrid tests under Holm-2 instead of Holm-50 are also unchanged. The choice of family size does not drive any verdict.

### B1a. Sensitivity to the clustering of pairs (the important caveat)

The three CV repetitions re-use the same 3,332 traces with different fold assignments. A trace whose decision is the same in all three seeds contributes 3 concordant or 3 discordant "pairs". The exact McNemar test assumes independent pairs, so the pooled p-values are too small.

`clustered_sensitivity.py` re-tests every comparison with:
- (a) a **trace-clustered sign-flip permutation test**: per trace d_i = mean over seeds of (other correct − reference correct), 200,000 flips, floor 5e-6 used when no flip reaches the observed value (conservative);
- (b) an exact McNemar on **seed 20261021 only**: each trace once, but a third of the data, so low power.

Holm is applied inside the same families as reported.

Verdict changes (significant after Holm, pooled → clustered; from `clustered_sensitivity.txt`):

| Family | Comparison | Diff (pt) | p_Holm pooled | p_Holm clustered | Seed-1 only |
|---|---|---|---|---|---|
| N5 (24) | LSTM alone vs Alhamd, dependability | −1.13 | 5.4e-3 | **0.056 (n.s.)** | n.s. |
| N5b (48) | same | −1.13 | 9.0e-3 | **0.095 (n.s.)** | n.s. |
| Holm-50 | **Key hybrid vs proposed hybrid, dependability** | +1.16 | 9.7e-3 | **0.063 (n.s.)** | n.s. |
| N6c (4) | textbook harmonic vs hybrid, security | +0.44 | 1.2e-2 | **0.108 (n.s.)** | n.s. |
| N8a (16) | RF hybrid vs tuned harmonic, security | +0.42 | 1.1e-2 | **0.191 (n.s.)** | n.s. |

Significant under clustering but not with seed 1 alone (low power; reported for completeness):
- N5b: Key and Alhamd like-for-like security vs the hybrid;
- LSTM alone vs Abdusalam / Ngaopitakkul like-for-like security;
- Key hybrid security;
- B2: ANN and GRU vs the tuned LSTM, RF security vs deployed, ANN and GRU vs deployed.

The clustered p-values of these 10 stay below 0.05.

**Do the pre-registered decision rules still fire the same way under the clustered test?**

| Rule | Pooled | Clustered | Same outcome? |
|---|---|---|---|
| N4/N5 native → claim B (Key, Alhamd +dep / −sec; Abdusalam −dep / +sec) | all significant | all significant (p_Holm ≤ 2.4e-4) | yes |
| D-N5b row 1 for Key like-for-like (sig. better on ≥ 1, not sig. worse) | dep +4.28 *, sec +0.61 * | dep *, sec * (0.017) | yes |
| D-N5b row 2 for Alhamd (better dep, sig. worse sec) | * / * | * / * (0.019) | yes |
| H6 decision row 1, Key hybrid (sig. better on ≥ 1, not sig. worse) | dep *, sec * | dep **n.s.**, sec * | **yes** (fires on security alone) |
| B2 rule (a same-feature hybrid sig. better on dep, not worse on sec) | CNN / GRU / ANN * | CNN / GRU / ANN * (1.1e-4) | yes |
| N6c row 2 (gap < 3 pt) | −1.78 * | −1.78 * (4.6e-3) | yes |
| N8a "6 of 6 instances significantly higher dependability" | 6/6 | 6/6 | yes |

**Consequences for the text:**
- (i) The 13:47 log sentence "it is significantly better on both" (Key hybrid) does not survive clustering. The plan's own wording, "higher security, dependability at least equal", does. Keep that wording.
- (ii) N8a security: "Key and RF significantly higher" becomes "Key significantly higher".
- (iii) Textbook harmonic security +0.44: do not call it significant.
- (iv) State the test's unit in the paper. Better: report the clustered p-values next to the pooled ones, or use one seed per test.

---

## B2. Log claims of 2026-11-02 and 2026-11-03 against the files

`check_log_claims.py` checks **363** numbers. Each claim string is quoted from `IMPLEMENTATION_PLAN.md`; the comparison value is recomputed from the named file.

The entries covered:
- 2026-11-02: 09:16, 09:56, 12:27, 21:55, 23:11;
- 2026-11-03: 08:17, 09:10, 09:42, 13:47, 17:53, 23:41;
- 2026-11-04 00:08 (same working night).

The full table (claim | file | recomputed | match) is in **`audit/scripts/out/log_claims.csv`**.

**Result: 362 Y, 1 N.**

| Log entry | Claim | File | Match |
|---|---|---|---|
| 2026-11-03 08:17 | "The like-for-like mode raises the security of the neural methods to **95.3**–99.6 %" | `full/{afrasiabi,key,alhamd}/cv_*.json` | **N**: on the CV the lowest is Alhamd 98.17 %. 95.3 % is Alhamd's **OOD** value (95.30 in `n4_full_summary.txt`), so the sentence mixes the CV and OOD sets. Fix: "98.2–99.6 % (CV)" |

**Numbers that cannot be checked from files** (stated, not counted):
- the RAM figures of 09:41 (process memory at run time);
- "Abdusalam features cached in parallel, 7,457 s" (not in `abdusalam_cv_log.txt`);
- Ngaopitakkul "so far (2 of 15 folds) 27 / 99.5" (an intermediate snapshot overwritten by the final files);
- the interim partial-fold numbers of 21:55 for Afrasiabi, Alhamd and Ngaopitakkul (snapshots).

**Two-run discrepancy** (finding B-3). The plan review of 2026-11-02 20:30 and the log of 09:56 / 12:27 quote:
- Key 96.91 / 74.86 (`key/rows_*.json`);
- Afrasiabi 87.06 / 89.56 (`afrasiabi/rows_*.json`).

These match their files. The later `full/` re-runs on the same folds give Key 96.99 / 75.28 and Afrasiabi 86.71 / 88.63. Decisions differ on 74 (Key) and 367 (Afrasiabi) of 9,906 (seed, fold, trace) keys. Alhamd, Simões, Ngaopitakkul and Abdusalam are identical between the two runs (0 differences).

Training is evidently not bit-reproducible for the two GPU/CPU-trained neural reproductions. The paper must:
- (a) say which run each row uses (Table A uses `full/`);
- (b) use the same run for "Afrasiabi with vs without the Hajipour stage". Today 86.7 / 88.6 (`full/`, with) is compared with 86.4 / 88.1 (`afrasiabi_nocomp/`, without, first run). Compared within the first run it is 87.06 / 89.56 vs 86.41 / 88.09. Either way the stage effect is about the size of the run-to-run noise, which supports "nearly inactive", but the comparison should be within one run.

---

## B3. Pre-registration order

**Clock sources:**
- the log timestamps (local time, +0600);
- git commit times (`git log --date=iso-local`): the committer clock, so the same machine;
- git diffs showing *when a rule's text first entered the repository*.

File modification times are not usable (fresh clone).

| Rule / hypothesis | First in git | Result it governs (first in git) | Order OK? | Note |
|---|---|---|---|---|
| N1–N8 hypotheses and decision tables (H1a–H7, N4 claim table, N5, N6a, N6c table) | `38c5eaa` 2026-11-01 23:31 | N1/N2 results `b338bc2` 23:42, `14e8762` 23:45; all reproduction results later | **yes** | Log 2026-11-01 23:20: "no reproduction evaluated" at writing time. Later commits only **add** lines to the plan: `9444109` has 1 deletion (a checkbox), `644ba1e` has 0 deletions. So the original tables were never edited after results |
| Spec fills (UNSPECIFIED items of the 6 papers) | specs committed 2026-11-01 00:20 (log), modules `c53ec56`/`555e7b8` | CV runs later | yes | |
| Simões detector rule (N2) | `38c5eaa` | `14e8762` | yes | |
| Alhamd "spec budget" re-run (amendment 9) | log 2026-11-02 12:27 | the reduced-budget result 85.79 / 54.91 was **already known** | **no (post-result decision)** | Mitigated: both runs reported, and the reason (compute) is stated. Still a forking-path decision: label it |
| Like-for-like rows enter the claim-C rule (D-N5b decision table) | review 2026-11-03 09:00 (summarised in log `49f64a9` 09:08) | like-for-like **descriptive** numbers were in `n4_full_summary.txt` (log 08:17); tests `63b9e24` 09:10 | **partly** | The rule was written after the descriptive result and before the test. It pushes towards a *less* favourable claim, so it is not self-serving, but H5b ("Key significantly better…") is a prediction of a known descriptive gap. Do not call H5b a pre-registered hypothesis |
| H6 (Key hybrid ≥ 93 / ≥ 99, n.s. worse) | log 09:41, commit `d9206d4` 09:42 | first fold (94.1 / 100.0) already known; final `712b3ba` 13:47 | **partly** | Disclosed in the log. Label H6 as "set after one of 15 folds was seen" |
| Review "2026-11-03 09:45" | committed only in `644ba1e` (2026-11-04 00:13) | log 09:41 quotes it ("Review 2026-11-03 09:45: H6 logged BEFORE…") | **inconsistent timestamps** | A log entry at 09:41 cannot quote a review dated 09:45. The header time is approximate, or the text was edited later. There is no git evidence of the review's content before 00:13 |
| B2 second family (every tuned hybrid vs the deployed hybrid) | log 17:53 | same entry | **no (post-hoc)** | Correctly labelled post-hoc in log, file and table note |
| N6c fills (3-D plateau rule) | `bf3ea58` 2026-11-03 17:55 | `ac04f81` 23:41 | **yes** | Only reporting lines were added to `tools/n6c_tuned_harmonic.py` after the fills (diffs of `ac04f81`, `ac92555`); the selection code is unchanged |
| D-lat: re-measure Alhamd with the trained configuration | review 09:00 | the first measurement ("not real-time", 1,809 µs) was known | **no (post-result)** | Justified: the first measurement used the wrong configuration. Both are reported |
| Gated-only ablation | review 09:45 / log 09:42 | same | post-hoc | labelled |
| **D-N8a family (Holm-16) and the "range-only" headline rule** | review "2026-11-04 00:10", committed `644ba1e` 00:13 | D-N8a result: log 00:08, commit `ac92555` 00:08:24 | **no: the rule is dated after the result** | The script and result were committed 1.5 min before the review that "decided" them. D-N8a is labelled post-hoc, which limits the harm. But the claim that its family and headline rule were fixed before seeing it cannot be supported from the record |
| D-N8b claim wording | review 00:10 | abstract draft `8d61da3` 00:08:47 | **no: dated after the draft** | as above |

**Overall:**
- The **original** pre-registration (`38c5eaa`, 2026-11-01) is clean, verifiable in git, and was never edited.
- The later "review and decisions" layers are honest about what is post-hoc. But they were committed in one batch at the end, so their timing rests on the log alone.
- In two places the log contradicts that timing: 09:41 vs 09:45, and 00:08 vs 00:10.

**Recommendation for the paper:** call only the `38c5eaa` rules "pre-registered". Call the later ones "decision rules fixed during the analysis (timestamps in the supplementary log)". Name the post-hoc analyses: B2 family 2, gated-only, N8a, D-lat re-measurement, the Alhamd budget re-run, and the like-for-like extension of claim C.
