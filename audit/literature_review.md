# Literature review (audit task A)

Date: 2026-11-03. Auditor: independent cloud session (no MATLAB, repo + web only).
Companion table: `audit/literature_table.csv` (52 rows), built by `audit/scripts/build_literature_table.py`.
Verification trail: `audit/scripts/out/crossref_log.jsonl`. Every DOI below was resolved in Crossref during this audit.
"Read" says how much of each paper the audit could see: full text, abstract only, or bibliographic record only.
Where only the abstract was visible, details of the paper's logic are stated only as far as the abstract states them.

---

## 0. Two corrections first

1. **"Lin et al. 2026, arXiv 2604.01928" is a re-posting of a 2023 journal paper.**
   - Same title and same five authors as Lin, Yang, Zhang, Hao and Zhang: *A Data-Aided Power Transformer Differential Protection Without Inrush Blocking Module*, **IEEE Trans. Power Delivery 38 (2023) 2000–2010, DOI [10.1109/TPWRD.2022.3230468](https://doi.org/10.1109/TPWRD.2022.3230468)**.
   - The arXiv record (v1, 2026-04-02) carries the same title and authors.
   - **Cite the TPWRD version.** A reviewer will notice if a 2023 TPWRD paper is cited as a 2026 preprint.
2. **Holm (1979) has no Crossref DOI**, and JSTOR blocked the audit's request. The record agrees across several indexes: *Scand. J. Statist.* 6(2):65–70, JSTOR 4615733. It is marked **UNVERIFIED** in the CSV until the author opens the JSTOR page.

---

## A1. Novelty check: AI combined with, or supervised by, a conventional differential element

**Our logic:**
`trip = high-set OR (87T vote AND confirmed AI ≥ AI_Threshold) OR (confirmed AI ≥ AI_Solo_Threshold)`, where confirmed = min of the last 20 outputs.

**Searches run:**
- Crossref bibliographic queries and web searches (2015–2026) for ML/ANN plus "differential protection" with blocking / supervision / stabilisation / restraint / hybrid / AND / OR / cooperative.
- Transformer, line (distance) and generic-relay variants.

**What the literature does with the AI output.** Four patterns appear; none is our pattern.

| Pattern | Examples (verified) | Can the AI trip on its own? | Does a conventional element gate the AI? |
|---|---|---|---|
| **AI as restraint / blocking** of the 87T | Rebizant, Bejmert, Schiel 2007 (ANN + 2nd harmonic); Bejmert et al. 2014 (fuzzy); Ahmad et al. 2019 (ANN with harmonic restraint) | no | no: the 87T trips, the AI only blocks it |
| **AI as pre-filter** of the 87T input | Lin et al. 2023 (TPWRD) | no | no: the ratio-differential element decides on AI-cleaned phasors |
| **AI as setting supervisor** | Rezaei 2026 (IET GTD): ML recognises SSR / ferroresonance and "operates or restricts" the relay by changing settings | no | the AI supervises the 87T, not the reverse |
| **AI as the relay** (stand-alone classifier) | almost all 2019–2026 papers: Afrasiabi 2020/2022, Murugan 2022, Key 2024/2025, Alhamd 2024, Afsharisefat 2023/2024, Wang 2025, Shi 2026 | yes | no |

**Line protection** shows the mirror image:
- AI vetoes a conventional trip: Khaw et al. 2019, an autoencoder blocks distance-relay trips caused by false data.
- AI takes over a decision under stress: Sahoo et al. 2021, zone-3 supervision.

**Not found in any searched paper:**
- a conventional element gating (AND) an AI trip decision, combined with a parallel high-confidence AI-only OR path;
- a min-filter (persistence) confirmation on the AI output.

Shi et al. 2026 (*Processes*) is the only one with a related confirmation rule: trip after *s* consecutive identical outputs.

> **Verdict on novelty (honest).** The *combination* appears new in the searched literature. Its parts are well known:
> - harmonic/87T plus AI in one relay (2007);
> - AI-only trip paths (most ML papers);
> - output persistence counters (2026).
>
> A careful wording for the paper: *"to our knowledge, prior work uses the learned model either to restrain the differential element [Rebizant 2007], to condition its input [Lin 2023], to adapt its settings [Rezaei 2026], or to replace it; we use the 87T vote to gate the learned decision, with a separate high-confidence path."*
>
> Avoid "first". The search cannot exclude conference papers or non-English work.

### The three closest prior works

1. **Rebizant W., Bejmert D., Schiel L., "Transformer differential protection with neural network based inrush stabilization", 2007 IEEE Lausanne PowerTech, pp. 1209–1214, DOI [10.1109/PCT.2007.4538488](https://doi.org/10.1109/PCT.2007.4538488).** *(abstract read)*
   - **What it does:** three ANN inrush detectors, with topology chosen by a genetic algorithm. The final unit "combines the classification strengths of neural networks with commonly used second harmonic restraint, thus being a hybrid classification unit". It stabilises (blocks) the differential relay. Tested on EMTP-ATP signals.
   - **How we differ:**
     - (a) Their AI is a **restraint** of the 87T; in ours, the 87T is the **gate** of the AI's trip decision. The roles are reversed.
     - (b) They have no AI-only trip path; we have the solo path.
     - (c) They have no output-persistence (min-of-20) confirmation.
     - (d) They report no grouped split, no OOD test and no significance tests.
   - **Same thing in both:** AI and harmonic logic combined by Boolean logic in one relay. This is the paper a protection reviewer will name. It is in the thesis bibliography (ref15) but should be in the EPSR related-work section.
2. **Lin Z., Yang S., Zhang Y., Hao Z., Zhang B., IEEE TPWRD 38 (2023) 2000–2010, DOI [10.1109/TPWRD.2022.3230468](https://doi.org/10.1109/TPWRD.2022.3230468)** (also arXiv 2604.01928). *(full text read)*
   - **What it does:** an attention FCN marks the inrush (saturated) samples and zeroes them. Nonlinear least squares fits the fundamental on the remaining part. A standard ratio-differential criterion trips: I_op > I_op,0 and I_op > K·I_res.
   - **Data:** 8,600 PSCAD samples (6,020 train / 2,580 test), a further simulated test set (1,012 inrush, 917 internal, 862 slight-fault-with-inrush) and 223 records from a 6 kVA lab transformer.
   - **How we differ:**
     - (a) Their ML acts on the **signal**, before the 87T; ours acts on the **decision**, after it, gated by the 87T vote.
     - (b) Their relay cannot trip on an AI score; ours can (solo path).
     - (c) They have no supervision logic, no dwell, and no statistics.
   - **Strength of theirs:** a lab-transformer test. **Strength of ours:** grouped CV, OOD, a second plant and significance tests.
   - The two ideas are compatible: their pre-filter could feed our 87T vote. That is worth a sentence as future work.
3. **Rezaei S., "An intelligent machine learning-based algorithm to adapt the behaviour of differential protection during sub-synchronous resonance in smart grids", IET GTD 20 (2026) e70379, DOI [10.1049/gtd2.70379](https://doi.org/10.1049/gtd2.70379).** *(abstract read)*
   - **What it does:** DWT plus several ML classifiers recognise SSR and SSR-induced ferroresonance, and then "operate or restrict the relay by modifying setting parameters".
   - **How we differ:**
     - (a) Their AI supervises the conventional element through **settings**, for one phenomenon. Ours combines AI and 87T **per decision**, for all events.
     - (b) In theirs the AI never trips. Ours has the AI-solo path.
     - (c) The applications differ (SSR / ferroresonance vs inrush / CT saturation / internal faults).

   **Runner-up:** Bhatt, Rahi, Bharadwaj 2016 (ICEPES, DOI [10.1109/ICEPES.2016.7915908](https://doi.org/10.1109/ICEPES.2016.7915908)), "ANN along with the differential relay" that gives the trip command. The abstract does not describe a gating logic.

---

## A2. Evaluation-rigour landscape

**What transformer-protection ML papers usually report.** From the abstracts of the 2019–2026 competitors (CSV rows):
- accuracy / confusion matrices on simulated cases;
- sometimes a lab or prototype transformer (Afrasiabi 2020/2022, Lin 2023, Li 2022, Wang 2025);
- train/test split by sample, with the unit (case vs window) **not stated** in any abstract read;
- no significance tests in any of them;
- multi-method comparisons always against methods the authors re-implemented themselves, without stating their training budget.

Murugan 2022 (TPWRD) uses three transformers but trains one model per transformer, so it is not a transfer test.

**Papers that do part of what we do:**

| Rigour element | Who does it (verified) | Note for us |
|---|---|---|
| Grouped / blocked CV | Roberts et al. 2017, *Ecography*, DOI [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881) (methods); Yasin et al. 2026, *J. Teknik Elektro*, DOI [10.15294/jte.v18i1.40675](https://doi.org/10.15294/jte.v18i1.40675) (scenario-based split in a power-system fault detector) | cite Roberts for the principle |
| Leakage critique | Kapoor & Narayanan 2023, *Patterns*, DOI [10.1016/j.patter.2023.100804](https://doi.org/10.1016/j.patter.2023.100804); Matania et al. 2024, PHM Society Europe, DOI [10.36001/phme.2024.v8i1.4125](https://doi.org/10.36001/phme.2024.v8i1.4125) (segment-level splits inflate accuracy) | **no power-protection-specific leakage critique found** in a refereed journal. That is a gap we can claim to address, worded carefully |
| OOD / cross-system | Li, Jiao, He 2020 (IET GTD, generalisation via knowledge transfer); Li et al. 2022 (PCMP, simulation → dynamic-model experiments); Shakiba et al. 2022 (*Neurocomputing*, line transfer learning); **EvEMTBench** (Oelhaf et al., arXiv 2609.28149, 2026: four grids, committed partitions, leakage controls, zero-shot and fine-tuned cross-grid transfer) | EvEMTBench is the closest evaluation peer, for lines and grids. It is a preprint: cite it as such |
| Significance tests for paired classifiers | McNemar 1947; Dietterich 1998; Demšar 2006 (JMLR) | **no transformer-protection paper with McNemar + Holm was found** |
| Multi-method re-implementation benchmark | EvEMTBench (baselines from trivial to deep, lines); none for transformers | our six faithful reproductions with per-paper specs appear to be unusual for transformer 87T |

---

## A3. Competitors a reviewer will most likely ask for (2020–2026)

Ranked by likelihood: venue match and recency first.

| # | Paper (verified DOI) | Family | Covered by one of our 6 reproductions? | If not: one honest sentence for the paper |
|---|---|---|---|---|
| 1 | Afsharisefat, Jannati, Shams 2023, **EPSR** 219:109255, [10.1016/j.epsr.2023.109255](https://doi.org/10.1016/j.epsr.2023.109255): MRA + BiGRU | wavelet + bidirectional RNN | **partly**: Alhamd 2024 (wavelet + BiLSTM) is the same family; GRU also in Table B (same features) | "MRA–BiGRU [x] belongs to the wavelet + bidirectional-recurrent family represented by our Alhamd reproduction; it was not reproduced separately." *(the audit saw the title only: the author must check the method before writing this)* |
| 2 | Afsharisefat et al. 2024, **IET GTD** 18, [10.1049/gtd2.13112](https://doi.org/10.1049/gtd2.13112): VMD + CNN-BiLSTM | decomposition + CNN-RNN | partly (CNN: Afrasiabi; BiLSTM: Alhamd); VMD not | "Its VMD front-end is not reproduced. The CNN and BiLSTM stages are represented by the Afrasiabi and Alhamd reproductions." |
| 3 | **Afrasiabi et al. 2022, IEEE TIE 69(8):8501–8512, [10.1109/TIE.2021.3109535](https://doi.org/10.1109/TIE.2021.3109535)**: fast GRNN (GRU without reset gate) + mutual-information loss | recurrent on raw data | **no** (Afrasiabi **2020** CNN is reproduced; FGRNN is not); the GRU architecture is in Table B with our features | "We reproduced the same group's 2020 CNN, for which the paper gives a complete specification. The 2022 FGRNN differs in the recurrent cell and the loss. A GRU with the same budget is in Table B." |
| 4 | Lin et al. 2023, **TPWRD** 38 (see A1) | ML pre-filter + ratio differential | **no** | "Its ML stage conditions the phasor estimate of the differential element rather than making a trip decision. It is complementary to the proposed gate and was not benchmarked." |
| 5 | Murugan, Simon, Eapen 2022, **TPWRD** 37, [10.1109/TPWRD.2021.3080927](https://doi.org/10.1109/TPWRD.2021.3080927): signal-localised CNN on wavelet coefficients | CNN on wavelet maps | partly (Afrasiabi CNN; 1D-CNN in Table B) | "It is a CNN on wavelet coefficients, the family of our 1D-CNN (Table B) and Afrasiabi rows; its modified back-propagation was not reproduced." |
| 6 | Wang, He, Li, Jiao, Lu 2025, *Expert Syst. Appl.* 292:128632, [10.1016/j.eswa.2025.128632](https://doi.org/10.1016/j.eswa.2025.128632): RL early classification (variable window) | RL / variable window | **no** | "Variable-window RL decision-making is outside the benchmark; our relay uses a fixed 32-sample window and a 20-sample confirmation." |
| 7 | Li, Jiao, He 2020, **IET GTD** 14:5782–5791, [10.1049/iet-gtd.2020.0542](https://doi.org/10.1049/iet-gtd.2020.0542), and Li et al. 2022, PCMP 7:52, [10.1186/s41601-022-00273-8](https://doi.org/10.1186/s41601-022-00273-8) | V–I-curve CNN / knowledge transfer | **no** | "These methods need the magnetising-branch voltage, which a current-only 87T does not measure. Their focus, generalisation, is what our plant-B zero-shot test examines." |
| 8 | Key, Son, Nam 2024, *Energies* 17:963, [10.3390/en17040963](https://doi.org/10.3390/en17040963) | SDAE DNN | **yes**, via its successor Key et al. 2025 (IEEE Access), which we reproduce | none needed: say the 2025 version supersedes it |

**Also verified, lower priority:**
- Shi et al. 2026, *Processes* (capsule network with a consecutive-confirmation trip rule; cite next to our dwell);
- Tripathy et al. 2010 TPWRD (PNN);
- Afrasiabi et al. 2020 ASOC;
- Medeiros & Costa 2016/2018 TPWRD (deterministic wavelet 87T: fairness-plan item F8, discussed, not benchmarked).

---

## A4. Citations for the paper's weak points (verified)

| Topic | Use these | Note |
|---|---|---|
| High-impedance / low-level internal faults (our ~65 % on Internal_HiZ) | Farzin, Vakilian, Hajipour 2019, TPWRD, [10.1109/TPWRD.2019.2893279](https://doi.org/10.1109/TPWRD.2019.2893279); Farzin et al. 2020, IJEPES, [10.1016/j.ijepes.2020.106158](https://doi.org/10.1016/j.ijepes.2020.106158); Mieske, Solak, Rebizant et al. 2025, IET Conf. Proc. (DPSP), [10.1049/icp.2025.0483](https://doi.org/10.1049/icp.2025.0483); Oztekin, Karagol, Ozgonenel 2026, *Appl. Sci.* 16:7073, [10.3390/app16147073](https://doi.org/10.3390/app16147073) | Framing: low-level turn-to-turn faults are a known blind spot of the percentage 87T. Dedicated elements (incremental / negative-sequence) exist. Our result is consistent with that, not an anomaly |
| CT saturation and remanence | IEEE C37.110-2007, [10.1109/IEEESTD.2008.4483716](https://doi.org/10.1109/IEEESTD.2008.4483716) (a 2023 edition also exists: [10.1109/IEEESTD.2023.10132388](https://doi.org/10.1109/IEEESTD.2023.10132388), use the newest the author can access); Ivanov, Kanafeev, Terzija 2023, PowerTech, [10.1109/PowerTech55446.2023.10202781](https://doi.org/10.1109/PowerTech55446.2023.10202781); Chothani & Kumar 2025, IEEE Access, [10.1109/ACCESS.2025.3609541](https://doi.org/10.1109/ACCESS.2025.3609541) | The audit found no recent journal paper focused only on CT remanence in 87T: cite the C37.110 guide for remanence |
| Sympathetic inrush (not modelled) | Bronzeado & Yacamini 1995, IEE Proc. SMT, [10.1049/ip-smt:19951953](https://doi.org/10.1049/ip-smt:19951953); Rudez & Mihalic 2016, **EPSR** 138:3–10, [10.1016/j.epsr.2015.12.011](https://doi.org/10.1016/j.epsr.2015.12.011) | |
| Generalisation / transfer of ML relays | Li, Jiao, He 2020 (IET GTD, above); Li et al. 2022 (PCMP); Shakiba et al. 2022 (*Neurocomputing*, [10.1016/j.neucom.2022.05.022](https://doi.org/10.1016/j.neucom.2022.05.022)); EvEMTBench (arXiv, preprint) | Z. Li et al. 2020 is the requested KBANN paper: verified |
| McNemar / Holm | McNemar 1947, [10.1007/BF02295996](https://doi.org/10.1007/BF02295996); Dietterich 1998, [10.1162/089976698300017197](https://doi.org/10.1162/089976698300017197); Holm 1979 (JSTOR 4615733, **UNVERIFIED** here); Demšar 2006 (JMLR, URL verified) | `refs.bib` has McNemar, Dietterich and Wilson; **add Holm** (it is used but not in `refs.bib`) |
| Grouped cross-validation | Roberts et al. 2017, [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881) | |
| Operate-time expectations | IEEE C37.91-2021, [10.1109/IEEESTD.2021.9471045](https://doi.org/10.1109/IEEESTD.2021.9471045) (`refs.bib` lists the **2008** edition with "edition to be confirmed": update to 2021); IEC 60255-187-1:2021 (URL verified at webstore.iec.ch) | IEC 60255-187-1 defines how *typical operate time* is declared and tested. The audit did not see a single mandated limit in it. **Do not write "IEC requires ≤ X ms"** unless the author quotes the clause |

---

## A5. What to change in the paper (no new experiments)
1. Add a "Relation to prior hybrid schemes" paragraph with the A1 table (four patterns) and the three closest works. Use the careful novelty sentence above.
2. Replace the arXiv citation of Lin et al. by the TPWRD DOI.
3. Add Holm 1979 and Roberts 2017 to `refs.bib`. Update C37.91 to the 2021 edition.
4. In the related work, add Afsharisefat 2023 (EPSR, the journal itself) and Afrasiabi 2022 FGRNN, each with the one-sentence "not reproduced because…" from A3.
5. HiZ limitation: cite the turn-to-turn literature, so the 65 % reads as a known limit of differential protection, not a defect of this paper alone.

Sources used (web pages opened in this audit, in addition to the Crossref records):
- [arXiv 2604.01928](https://arxiv.org/abs/2604.01928) (PDF text read)
- [arXiv 2609.28149](https://arxiv.org/abs/2609.28149)
- [DTU Orbit record of Afrasiabi 2022](https://orbit.dtu.dk/en/publications/fast-grnn-based-method-for-distinguishing-inrush-currents-in-powe/)
- [JMLR Demšar 2006](https://jmlr.org/papers/v7/demsar06a.html)
- [IEC webstore 60255-187-1](https://webstore.iec.ch/en/publication/32570)
- [academia.edu abstract of Rebizant 2007](https://www.academia.edu/7107598/Transformer_Differential_Protection_with_Neural_Network_Based_Inrush_Stabilization) (search snippet)
- [IET GTD Rezaei 2026](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/gtd2.70379) (abstract via Crossref)
