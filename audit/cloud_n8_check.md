# Cross-check of branch `cloud-n8` against this audit

Date: 2026-11-04. Branch `origin/cloud-n8` at `87fc4b2` (one commit on top of `5297507`). Nothing on `cloud-n8` was edited; this file only reports.

**Files checked:**
- `paper_epsr/ABSTRACT_DRAFT.md`, `tools/build_abstract_draft_n8b.py`;
- `tools/publication_tables_AD.py`, `paper_epsr/tables/*` and `paper_epsr/generated/table_{A,B,D}_*.tex`;
- `documents/reference_fixes_N7.md`;
- the new `IMPLEMENTATION_PLAN.md` entry.

## Verdict
The numbers are clean: every value the branch prints reproduces from the saved files, and every DOI in N7 resolves. The branch does **not** yet take in five audit findings, and one of its choices contradicts the audit (the Lin et al. citation).

## 1. What is correct (verified)

| Check | Result |
|---|---|
| 34 numbers in `ABSTRACT_DRAFT.md` | **All reproduce** from `n5_statistics.json`, `n8a_…json`, `b2_summary.json`, `n6c_tuned_harmonic.txt`, `key_hybrid/final_plantB_main.json` and the plant-check files. Instances 93.489–95.749 % dependability and 98.816–99.865 % security; vs tuned harmonic +2.314 to +4.574 and −0.254 to +0.795 pt; tuned harmonic 91.18 / 99.07; deployed 92.95 / 98.95; SVM hybrid 87.01 / 97.73 |
| Upper bound changed 95.8 → **95.7 %** | **correct** (1D-CNN 95.749 %) |
| Table B note: "per-seed security signs change for CNN, GRU" (ANN removed) | **correct**. Per-seed security differences vs the deployed hybrid (`b2_summary.json`): ANN +0.05 / +0.56 / +0.15 (stable), CNN +0.05 / +0.36 / −0.20, GRU +0.05 / −0.05 / −0.41 |
| Table A note: "of 300" / "of 1,289" dropped | acceptable (those denominators are not in a saved result file) |
| "Key's network: equal 12-configuration search" | correct: `tools/run_full_eval.py:40` uses `KeyMethod(plant, n_configs=12)`. Nuance: Key searches per fold, while B2 searched once on seed-1 folds 1–3 |
| N7: 19 DOIs (ref2, ref5 a–d, ref10, ref18 + alternative, ref31, ref32, ref34, ref35 alternatives, Oliveira 2009, Sundararaman 2023, Gajić 2021, the 4 related-work candidates) | **all resolve in Crossref, titles and authors match** (`audit/scripts/out/crossref_log.jsonl`, 2026-11-04 run) |
| `CLAUDE.md` shown as deleted in `main..cloud-n8` | **not a real deletion**: the branch forks from `5297507`, before `CLAUDE.md` was tracked. A merge keeps it. Do not resolve it with "take theirs" |

## 2. Audit findings NOT taken in on `cloud-n8` (should be before submission)

| # | Audit ref | Where on cloud-n8 | Problem | Fix (text / script only) |
|---|---|---|---|---|
| 1 | `code_audit.md` C-1 | `tools/publication_tables_AD.py:343` → Table B note | Still says the deployed LSTM used "(same routine, **stride 4**)". It was stride 8 (`run_v5_cv.sh` + `train_cv_v5.py:317` default; window counts identical to B1 stride 8). The string is hard-coded, so every rebuild re-introduces the error | change to "stride 8". Add to the note that the post-hoc "vs deployed" family compares stride 4 with stride 8 |
| 2 | C-3, C-4 | Table B note; abstract "equal training budget" | The note does not say that the B2 search is **not nested**, nor that SVM / RF were fitted on **30 k / 50 k** subsampled windows. The abstract's "equal training budget" over the six instances is therefore slightly overstated | one note sentence; abstract: "equal search and epoch budget" |
| 3 | `results_audit.md` B1a | Table D `*` marks; the abstract's "Holm-corrected"; the Key-hybrid note | Significance marks use the pooled (seeds-as-independent) McNemar. Under the trace-clustered test, **RF hybrid security +0.42* vs tuned harmonic is not significant** (p_Holm 0.191), and Key-hybrid dependability +1.16 is not (0.063). The six dependability gains of the abstract **do** survive (clustered p_Holm ≤ 1.2e-3) | drop the `*` on RF security; quote clustered p-values or add a note on the test unit |
| 4 | `literature_review.md` §0 | `reference_fixes_N7.md`, related-work row 4 | Proposes citing **Lin et al. as "arXiv:2604.01928, 2026 (preprint, not peer-reviewed)"**. It is the same paper as **Lin et al., IEEE Trans. Power Del. 38 (2023) 2000–2010, DOI 10.1109/TPWRD.2022.3230468** (same title and authors; Crossref verified) | cite the TPWRD version. "Preprint, not peer-reviewed" is wrong |
| 5 | `literature_review.md` A1 | `reference_fixes_N7.md`, related-work candidates | The two closest prior hybrids are missing: **Rebizant, Bejmert, Schiel 2007** (ANN + 2nd-harmonic stabilisation, DOI 10.1109/PCT.2007.4538488, already thesis ref15) and **Rezaei 2026** (ML adapts 87T settings, DOI 10.1049/gtd2.70379). Without them, the claim "Lin is the closest relative" does not hold | add both, with the one-sentence differences from the literature review |
| 6 | `journal_checklist.md` | `ABSTRACT_DRAFT.md` ("EPSR's abstract limit is to be checked") | The limit is **250 words** (EPSR guide, search extract); the draft has **279** | trim ≥ 29 words (no number changes) |
| 7 | `results_audit.md` B3 | new `IMPLEMENTATION_PLAN.md` entry | The entry is dated "2026-11-04 01:15 (+06:00)" and `reference_fixes_N7.md` "01:10". **The commit that contains both is 2026-11-04 00:57:32 +06:00** (`87fc4b2`). This is the same kind of timestamp inversion as the 09:41 / 09:45 and 00:08 / 00:10 cases | use the commit time, or write "written before commit 87fc4b2" |

## 3. Small items
- `reference_fixes_N7.md` ref2: the title says "…ANN **classifier**". Crossref has "…ANN **classification**".
- ref32: the proposed sentence is fine. Note that the 1999 paper is a conference paper, not the listed EPSR 2018 article.
- ref18: correctly flags that the 99.1 % table value must go. Keep that flag in the paper's literature table.
- Table D note: "none is significantly less secure" is true under both tests.
- Table C still marks the tuned harmonic 87T OOD / plant B as n/e. Its settings are at the grid corner in 15 of 15 folds (pickup 0.2, k5 0.25; `n6c_tuned_harmonic.txt`). Neither the tables nor the abstract mention this (`mock_review_EPSR.md`, R1 major 2).
