# Journal compliance checklist (audit task E)

Date: 2026-11-03. Target: **Electric Power Systems Research (EPSR, Elsevier)**; fallback **IEEE Access**.

**Sources and their limits (read this first).**
- The live EPSR Guide for Authors on ScienceDirect (https://www.sciencedirect.com/journal/electric-power-systems-research/publish/guide-for-authors) returned a captcha to this cloud session. The audit did **not** bypass it. The EPSR items below come from web-search extracts of that official page; the **source** column says so.
- Elsevier's own policy pages (generative AI, CRediT) were read directly.
- **Before submission, the author must open the live guide and tick each EPSR row again.**
- Word counts were made by `audit` one-off scripts on `paper_epsr/main.tex` (commit `bfc2f1d`): plain token counts with LaTeX commands stripped, so treat them as approximate.

Status key: ✅ met · ❌ missing · ⚠️ partly / at risk · ❓ to confirm on the live page.

## EPSR

| Item | Requirement | Source | Current draft | Status |
|---|---|---|---|---|
| **Article length** | **Word limits from 20 Feb 2026:** Full Length Article ≤ **7,000 words**; Review ≤ 9,000; Short Communication ≤ 1,000. **Abstract, tables, figures and appendices count**; references and acknowledgements do not. Over-length papers may be rejected before review. **Article length must be stated in the cover letter** | search extract of the official guide (the older 22-page rule predates 2026) | `main.tex` body ≈ 1,630 words of text so far, plus the October tables (≈ 1,030 words). Tables A–D alone ≈ **1,375 words** with their long notes. The rewrite (related work, six reproductions, two plants, closed loop) will be tight at 7,000 | ⚠️ at risk: budget it now. Move the table notes and reproduction specs to supplementary material |
| **Abstract** | ≤ **250 words**, concise and factual | search extract of the official guide | `main.tex` abstract ≈ 211 words (OK, but October content). **`abstract_draft_N8b.txt` = 279 words** (over by ~29) | ❌ for the N8b text: trim ≥ 30 words |
| **Highlights** | Required; separate editable file with "highlights" in its name; **3–5 bullets, ≤ 85 characters each incl. spaces** | search extract of the official guide | `paper_epsr/highlights.txt`: 5 bullets of 75–84 characters (format OK). **Content is outdated**: "five literature models", "Security not significantly different from harmonic 87T; dependability higher" (textbook harmonic). Not the claim-C story | ⚠️ format ✅, content ❌ |
| **Graphical abstract** | Optional, encouraged (TIFF/EPS/PDF/MS Office). Elsevier AI policy: **general-purpose generative AI must not be used** for graphical abstracts | search extract + Elsevier AI policy page (read) | none | ✅ (optional); recommended: the dual-path block diagram |
| **Keywords** | Elsevier standard: a short keyword list | elsarticle template | present (6) | ✅ ❓ confirm the maximum number |
| **CRediT statement** | Contributions by the 14 CRediT roles (Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Resources, Data Curation, Writing – Original Draft, Writing – Review & Editing, Visualization, Supervision, Project administration, Funding acquisition); provided at submission; appears above the acknowledgements | Elsevier CRediT page (read) | "to be completed by the authors" | ❌ |
| **Data availability** | Declare data availability at submission; a reason can be given if data cannot be shared | search extract of the official guide | Section present; it says datasets and models are **not** in the repository and must be regenerated | ⚠️ present, but weak. See `reproducibility.md` for a proposed statement and a deposit plan |
| **Declaration of competing interests** | Elsevier standard declaration (the author's declaration tool or statement) | Elsevier standard; ❓ wording on the live guide | "to be completed by the authors" | ❌ |
| **Funding statement** | Elsevier standard: state funding sources or "no specific grant" | Elsevier standard ❓ | missing | ❌ |
| **Generative-AI declaration** | See the box below | Elsevier generative-AI policy for journals (read) | "use of AI tools: to be completed" | ❌ (author writes it) |
| **Figures** | Elsevier artwork rules (vector or ≥ 300 dpi, embedded fonts, readable at print size; colour online). Data plots must come reproducibly from the data | Elsevier artwork guidance ❓ + AI policy (read) | One TikZ diagram; **no result figures** (the README lists per-category, trip-time and plant figures as open) | ❌ figures missing |
| **References** | The guide does not impose a strict format at submission ("any style as long as consistent"); journal style is applied at proof. **Every reference must be real and checked** (the AI policy says fabricated references can lead to rejection) | search extract + Elsevier AI policy | `refs.bib`: 8 entries. Related work: 6 `[cite: …]` placeholders. C37.91 edition "to be confirmed" (2021 edition verified: DOI 10.1109/IEEESTD.2021.9471045). Holm 1979 not in `refs.bib`. **N7 gate:** 9 thesis references unverified | ❌ |
| **Cover letter** | Must state the article length (word count) | search extract of the official guide | none | ❌ |
| **Author block** | names, affiliations, corresponding author | template | placeholders ("Author One") | ❌ |

### Generative-AI declaration: what the Elsevier policy requires (the author writes the declaration)

From the Elsevier "Generative AI policies for journals" page, read on 2026-11-03.

- **Where:** a separate section at the **end of the manuscript, immediately before the references**. Suggested title: *"Declaration of generative AI and AI-assisted technologies in the manuscript preparation process"*. It is published with the article.
- **Content:** the tool used, the purpose, and a statement that the authors reviewed and edited the output and take full responsibility. Elsevier's template: "During the preparation of this work the author(s) used [NAME OF TOOL/SERVICE] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the publication."
- **Not required** for grammar, spelling and punctuation checks only. **Required** for substantive changes to structure or text, AI translation, and AI use in selecting or editing references.
- **AI in research methods (code, data analysis):** not restricted, but it must be **described in the Methods section** (tool, version, developer), in a reproducible way. This matters here: the repository log shows that the analysis code, statistics and tables were produced in AI coding-assistant sessions.
- **Not allowed:** AI as an author; generating manuscript sections without genuine author contribution; fabricating or altering data, results or **references**; general-purpose generative AI for the graphical abstract.
- **Record keeping:** keep records of the tool, model, prompts and outputs, and of your own review, in case the editor asks.

## IEEE Access (fallback)

| Item | Requirement | Source | Status for the current draft |
|---|---|---|---|
| Length | No hard page limit; **strongly recommended < 20 pages**; longer papers get extra editorial review; flat APC | ieeeaccess.ieee.org Submission Guidelines (read) | ✅ likely |
| Abstract | Not stated on the pages read (third-party guides say ≤ 250 words) | ❓ | ❓ (use ≤ 250) |
| Template / format | IEEE Access Word or LaTeX template + PDF; IEEE editorial style for references | ieeeaccess.ieee.org Preparing Your Article (read) | ❌ (elsarticle now) |
| Graphical abstract | A submitted video is published as the graphical abstract (≤ 100 MB) | Preparing Your Article (read) | optional |
| AI disclosure | Disclose AI-generated content **in the Acknowledgments**, name the AI system, mark the sections that use it with a brief explanation; editing-only use is recommended to be disclosed; fabricated content including non-existent references → rejection | both IEEE Access pages (read) | ❌ (author) |
| Data / code | Supplementary material (code, data) can be submitted; IEEE DataPort / Code Ocean mentioned | Submission Guidelines (read) | ⚠️ |
| Competing interests / author contributions | Not stated on the pages read; contributors who are not authors go in the Acknowledgment | Submission Guidelines (read) | ❓ |

## Top fixes before submission
1. Rewrite to the claim-C results, inside a **7,000-word budget that counts tables** (decide what goes to the supplement).
2. Abstract ≤ 250 words (N8b: −29 words). Rewrite the highlights to the new results.
3. Results figures. Generate them from saved files with a script (and mention that in Methods if AI-assisted code made them).
4. Bibliography: resolve every `[cite: …]`, the N7 gate and the C37.91 edition; add Holm.
5. Declarations: CRediT, competing interests, funding, data availability (see `reproducibility.md`), generative AI (box above, author's own wording), and the cover letter with the word count.
