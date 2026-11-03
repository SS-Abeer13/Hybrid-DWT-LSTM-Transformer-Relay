"""Builds audit/literature_table.csv.
Bibliographic fields (authors, title, venue, year, volume, pages) are taken from the Crossref records saved in
audit/scripts/out/crossref_log.jsonl (written by crossref.py); nothing bibliographic is typed here except for the three
items that have no Crossref DOI (arXiv preprints, IEC standard, Holm 1979, Demsar 2006, Ngaopitakkul 2006), whose source URL
was opened in this audit and is given in the row.
The qualitative columns (method, data, interaction, split, OOD, significance, metrics, relevance) are the auditor's reading of
the abstract / full text available to the audit; 'n/r' = not reported in the material the audit could read (usually abstract only).
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "literature_table.csv"
rec = {}
for line in (HERE / "out" / "crossref_log.jsonl").read_text().splitlines():
    for r in json.loads(line)["result"]:
        if r.get("doi") and r.get("title"):
            rec[r["doi"].lower()] = r

# doi -> (method, data, interaction, split, ood, sig, metrics, relevance, read)
# read: A = abstract only, F = full text read in this audit, R = repository copy / spec in documents/baselines
Q = {
    # ---- closest prior work (novelty) ----
    "10.1109/pct.2007.4538488": ("3 ANN inrush detectors (GA-tuned topology) combined with 2nd-harmonic restraint into a 'hybrid classification unit' that stabilises (blocks) a differential relay",
                                 "simulated (EMTP-ATP), size n/r", "blocking (AI + harmonic restraint jointly restrain the 87T; AI cannot trip alone)", "n/r", "N", "N", "n/r",
                                 "CLOSEST #1: AI and harmonic restraint combined by logic inside the 87T; differs: AI only restrains, no AI-trip path, no confirmation dwell", "A"),
    "10.1109/tpwrd.2022.3230468": ("attention FCN marks inrush (saturated) samples; NLS fits the fundamental on the non-inrush part; ratio-differential criterion on the fitted phasors",
                                   "simulated PSCAD 8,600 samples (6,020 train / 2,580 test) + 2,791-sample sim test set + 223 records of a 6 kVA lab transformer", "pre-filter (no inrush blocking; differential element decides)",
                                   "sample-level split (cases vs windows n/r)", "Y (lab transformer)", "N", "precision/recall/F1 of the segmentation, trip time",
                                   "CLOSEST #2 (= arXiv 2604.01928, which is a 2026 posting of this 2023 TPWRD paper): ML conditions the input of the 87T; no AND/OR supervision of an AI decision", "F"),
    "10.1049/gtd2.70379": ("DWT + several ML classifiers recognise SSR / SSR-ferroresonance and change the differential relay's settings (operate or restrict)", "simulated, size n/r",
                           "other: supervisory adaptation of relay settings (AI restricts or releases the 87T)", "n/r", "n/r", "n/r", "n/r",
                           "CLOSEST #3: AI supervises a conventional differential element, but by changing settings for one phenomenon, not by a trip vote", "A"),
    "10.1109/icepes.2016.7915908": ("feed-forward ANN 'along with' the differential relay gives the trip command for internal faults", "simulated (MATLAB), size n/r", "other: ANN issues the trip (AI alone; relay role n/r)",
                                    "n/r", "N", "N", "regression / performance plots", "early 'ANN + differential relay' scheme; no supervision logic described", "A"),
    "10.11591/ijai.v8.i4.pp307-316": ("ANN-based differential relay with 2nd-harmonic current as restraining input", "simulated (MATLAB), size n/r", "other: ANN replaces the restraint function", "n/r", "N", "N", "mal-operation count, operate time",
                                      "ANN + harmonic restraint in one relay; no dual-path logic", "A"),
    "10.1016/j.ijepes.2014.05.056": ("fuzzy-logic inrush stabilisation of the differential relay (successor of the 2007 ANN scheme)", "simulated", "blocking (fuzzy, not ML)", "n/r", "N", "N", "n/r",
                                     "shows the same group moved from ANN to fuzzy stabilisation; supports 'AI as restraint' being the established pattern", "A"),
    # ---- the six reproduced methods ----
    "10.1016/j.epsr.2021.107297": ("RT-BSWT energies + disturbance detector + two RBF-SVMs", "simulated", "none (stand-alone classifier with detector)", "n/r", "N", "N", "accuracy, detection time",
                                   "reproduced (Simoes 2021); covers wavelet + SVM family", "R"),
    "10.3390/en15113905": ("DWT (5 wavelets) + OMP + BA/GA selection + KNN/SVM/ANN", "lab transformer, size n/r", "none", "k-fold (unit n/r)", "N", "N", "accuracy, precision, recall, F1",
                           "reproduced (Abdusalam 2022); covers statistical-feature + shallow classifier family", "A"),
    "10.1109/tii.2019.2929744": ("accelerated CNN on raw currents", "simulated 230 kV + experimental prototype", "none", "n/r", "Y (prototype)", "N", "reliability indexes, speed",
                                 "reproduced (Afrasiabi 2020); covers CNN-on-raw-current family", "A"),
    "10.1109/access.2025.3618747": ("dual SDAE DNN: Com-DNN corrects CT saturation, Dis-DNN discriminates", "simulated 23 kV + hardware implementation", "none (stand-alone)", "n/r", "N", "N", "dependability, security",
                                    "reproduced (Key 2025); covers CT-compensation + autoencoder DNN family; uses true line currents", "A"),
    "10.3390/a17090397": ("improved wavelet feature + differential and bias current -> LSTM", "simulated with CT saturation and uncertainties", "none", "n/r", "N", "N", "accuracy",
                          "reproduced (Alhamd 2024); covers wavelet + recurrent family (closest to our classifier)", "A"),
    # ---- recent competitors 2020-2026 ----
    "10.1109/tie.2021.3109535": ("fast GRNN (GRU without reset gate) + mutual-information loss, raw data", "simulated + experimental", "none", "n/r", "Y (experimental)", "N", "speed, reliability vs GRU and 7 methods",
                                 "competitor; GRU family covered only by the same-feature GRU of Table B, FGRNN itself not reproduced", "A"),
    "10.1109/tpwrd.2021.3080927": ("signal-localised CNN on wavelet time-frequency coefficients", "simulated, three transformer systems, one model per transformer", "none", "per-transformer train/validation/test (unit n/r)",
                                   "N (each transformer trained separately)", "N", "confusion matrix vs LSTM, SVM, BPNN, 2nd-harmonic blocking", "competitor (TPWRD); CNN-on-wavelet covered by Afrasiabi + same-feature 1D-CNN", "A"),
    "10.1016/j.epsr.2023.109255": ("multi-resolution analysis + BiGRU", "simulated, size n/r", "none", "n/r", "n/r", "n/r", "n/r", "competitor in EPSR itself; wavelet + bidirectional recurrent covered by Alhamd (BiLSTM) and Table B GRU", "T"),
    "10.1049/gtd2.13112": ("VMD + CNN-BiLSTM on the differential current", "simulated 500 MVA transformer (MATLAB)", "none", "n/r", "N", "n/r", "classification accuracy",
                           "competitor (IET GTD 2024); CNN + BiLSTM partly covered (Alhamd, 1D-CNN), VMD front-end not reproduced", "A"),
    "10.1016/j.eswa.2025.128632": ("RL (PPO) early classification: the agent chooses how long a data window to use", "simulated + experimental", "none", "n/r", "Y (sim-to-experiment)", "n/r", "n/r",
                                   "competitor; variable-window / early-decision family not covered", "T"),
    "10.3390/en17040963": ("data window + stacked denoising autoencoders (internal fault during inrush)", "simulated PSCAD, Korean 154 kV substation", "none", "n/r", "N", "N", "accuracy, sensitivity, precision",
                           "predecessor of Key 2025 (same group); covered by the Key reproduction", "A"),
    "10.1049/iet-gtd.2020.0542": ("knowledge-based ANN with feature transfer (source = unsaturated V-I curve images)", "simulated + experiments", "none", "n/r", "Y (generalisation is the topic)", "N", "n/r",
                                  "generalisation of ML relays (requested citation, Z. Li et al. 2020); needs magnetising-branch voltage, not reproducible with our current-only relay", "A"),
    "10.1186/s41601-022-00273-8": ("denoising-classification CNN (CAE + CNN) on the exciting-voltage / differential-current curve", "PSCAD simulation + dynamic-model experiments", "none (protection scheme built on the CNN)", "n/r",
                                   "Y (experiments)", "N", "n/r", "generalisation-focused competitor; needs voltage; not covered", "A"),
    "10.17775/cseejpes.2020.04480": ("knowledge-based CNN (restrictive weight sparsity, adaptive sample weights) on the V-I curve", "simulated, size n/r", "none", "n/r", "n/r", "N", "n/r", "generalisation via protection knowledge; not covered", "A"),
    "10.3390/pr14030449": ("SE-CapsuleNet on time-domain fault-component features; trip after s consecutive identical decisions", "simulated", "none (confirmation counter on the AI output)", "n/r", "N", "N", "accuracy, robustness to Rf 400 ohm, 20 dB noise",
                           "2026 competitor; its consecutive-confirmation rule is close to our min-of-20 dwell", "A"),
    "10.1109/tpwrd.2009.2028800": ("optimal probabilistic neural network classifier", "simulated", "none", "n/r", "N", "N", "accuracy", "classic ML-87T reference (TPWRD)", "A"),
    "10.1016/j.asoc.2019.105975": ("composite deep learning differential protection", "n/r", "none", "n/r", "n/r", "n/r", "n/r", "same group as Afrasiabi 2020/2022; family covered", "T"),
    "10.1109/tpwrd.2015.2513778": ("boundary DWT energy criterion (deterministic)", "simulated + n/r", "none (wavelet criterion replaces harmonic restraint)", "n/a (no learning)", "N", "N", "n/r",
                                   "deterministic wavelet 87T; not benchmarked (fairness plan F8)", "T"),
    "10.1109/tpwrd.2018.2852485": ("wavelet-based internal-fault-during-inrush detection (deterministic)", "simulated", "none", "n/a", "N", "N", "n/r", "deterministic wavelet 87T; not benchmarked", "T"),
    # ---- evaluation rigour ----
    "10.1111/ecog.02881": ("methods paper: blocked / grouped cross-validation for structured data", "n/a", "n/a", "grouped (recommended)", "n/a", "n/a", "n/a", "citation for trace-grouped CV", "A"),
    "10.1016/j.patter.2023.100804": ("survey and taxonomy of leakage in ML-based science", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "citation for leakage-free protocol", "A"),
    "10.36001/phme.2024.v8i1.4125": ("shows test-training leakage from segment-level random splits in condition monitoring", "vibration data", "n/a", "window vs fault-shape split compared", "n/a", "n/r", "accuracy drop under proper split",
                                     "closest-domain evidence that window splits inflate accuracy", "A"),
    "10.15294/jte.v18i1.40675": ("ANN fault detection with leakage-prone features removed and scenario-based splitting", "simulated three-phase system", "none", "case (scenario)", "N", "n/r", "accuracy",
                                 "a power-system paper that adopts scenario splits explicitly", "A"),
    "10.1162/089976698300017197": ("McNemar and 5x2cv tests for comparing classifiers", "n/a", "n/a", "n/a", "n/a", "Y", "type-I error", "citation for paired McNemar", "A"),
    "10.1007/bf02295996": ("McNemar test for correlated proportions", "n/a", "n/a", "n/a", "n/a", "Y", "n/a", "citation for McNemar", "A"),
    "10.1080/01621459.1927.10502953": ("Wilson score interval", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "citation for Wilson intervals", "A"),
    "10.1016/j.neucom.2022.05.022": ("transfer learning (pre-trained CNN) for line fault diagnosis across line parameters", "simulated", "none", "n/r", "Y (transfer to other lines)", "n/r", "accuracy",
                                     "line-protection example of transfer tests; supports our plant-B zero-shot framing", "A"),
    "10.1109/tpwrd.2020.3035885": ("wide-area / DNN-assisted supervision of zone-3 distance relays under stressed conditions", "IEEE test systems (simulated)", "other: supervision (decision switches to a second logic under stress)", "n/r", "n/r", "n/r", "prevented trips",
                                   "line-protection analogue of AI supervising a conventional element", "A"),
    "10.1109/smartgridcomm.2019.8909810": ("autoencoder flags anomalous V/I data to block false distance-relay trips (cyber)", "simulated", "blocking (AI vetoes conventional trip)", "n/r", "N", "N", "detection rate",
                                           "line analogue: AI as a veto on a conventional trip (the mirror image of our 87T gate)", "A"),
    "10.1109/jsyst.2020.3009203": ("ML discrimination of internal faults vs transients for transformers and phase-angle regulators", "simulated (PSCAD) interconnected system", "none", "n/r", "n/r", "n/r", "accuracy", "multi-device ML protection; context", "T"),
    # ---- requested topic citations ----
    "10.1109/tpwrd.2019.2893279": ("turn-to-turn fault detection from fault-related incremental currents", "simulated + n/r", "n/a", "n/a", "N", "N", "sensitivity (% turns)", "HiZ / low-level internal faults", "T"),
    "10.1016/j.ijepes.2020.106158": ("percentage-based turn-to-turn fault algorithm implemented in a digital relay", "simulation + implementation", "n/a", "n/a", "N", "N", "n/r", "low-level internal faults (practical)", "T"),
    "10.1049/icp.2025.0483": ("incremental negative-sequence differential for turn-to-turn faults with stabilising criteria", "n/r", "n/a", "n/a", "N", "N", "n/r", "low-level internal faults, recent (DPSP 2025)", "T"),
    "10.3390/app16147073": ("low-level inter-turn fault detection algorithm for transformer differential protection", "n/r", "n/a", "n/a", "N", "N", "n/r", "low-level internal faults, 2026", "T"),
    "10.1109/ieeestd.2008.4483716": ("IEEE C37.110-2007 guide: CT application for relaying (saturation, remanence, dimensioning)", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "CT saturation and remanence (standard reference)", "T"),
    "10.1109/powertech55446.2023.10202781": ("impact of electromagnetic vs optical CTs on transformer differential protection at re-energisation", "simulated", "n/a", "n/a", "N", "N", "n/r", "CT behaviour (remanence-type effects) at re-energisation", "T"),
    "10.1109/access.2025.3609541": ("dynamic differential protection with CT-saturation estimation", "simulated", "n/a", "n/a", "N", "N", "n/r", "CT saturation, recent", "T"),
    "10.1049/ip-smt:19951953": ("sympathetic interaction between transformers caused by inrush transients", "simulation + measurement", "n/a", "n/a", "n/a", "n/a", "n/a", "sympathetic inrush (classic reference)", "T"),
    "10.1016/j.epsr.2015.12.011": ("sympathetic inrush with loaded transformers", "simulation", "n/a", "n/a", "n/a", "n/a", "n/a", "sympathetic inrush (EPSR)", "T"),
    "10.1109/ieeestd.2021.9471045": ("IEEE C37.91-2021 Guide for Protecting Power Transformers", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "operate-time / application expectations (replace the 2008 placeholder in refs.bib)", "T"),
}
NODOI = [
    ("Lin Z., Yang S., Zhang Y., Hao Z., Zhang B.: A Data-Aided Power Transformer Differential Protection without Inrush Blocking Module, arXiv:2604.01928 (posted 2026-04-02)",
     "https://arxiv.org/abs/2604.01928", "Y", "arXiv (eess.SY)", "2026", *Q["10.1109/tpwrd.2022.3230468"][:7],
     "duplicate posting of the 2023 TPWRD paper: cite the journal version, DOI 10.1109/TPWRD.2022.3230468"),
    ("Oelhaf J., Kordowich G., Bergler C., Maier A., Jaeger J., Bayer S.: EvEMTBench: An Open Benchmark for Machine Learning in Power System Protection, arXiv:2609.28149",
     "https://arxiv.org/abs/2609.28149", "Y", "arXiv (eess.SY)", "2026", "open benchmark: 4 grids 20-345 kV, 24 tasks, fixed partitions with leakage controls", "simulated EMT",
     "n/a", "case/topology-level partitions", "Y (distribution shifts, zero-shot and fine-tuned cross-grid)", "n/r", "task metrics + protection diagnostics",
     "closest evaluation-rigour peer (lines/grids); preprint, cite as such"),
    ("Holm S.: A simple sequentially rejective multiple test procedure, Scand. J. Statist. 6(2):65-70, 1979", "https://www.jstor.org/stable/4615733", "N",
     "Scandinavian Journal of Statistics", "1979", "Holm step-down correction", "n/a", "n/a", "n/a", "n/a", "Y", "n/a",
     "citation for Holm; JSTOR page blocked to the audit (no Crossref DOI): UNVERIFIED here, author to confirm on JSTOR"),
    ("Demsar J.: Statistical comparisons of classifiers over multiple data sets, J. Mach. Learn. Res. 7:1-30, 2006", "https://jmlr.org/papers/v7/demsar06a.html", "Y",
     "JMLR", "2006", "guidance on statistical tests for classifier comparison", "n/a", "n/a", "n/a", "n/a", "Y", "n/a", "optional citation for the testing strategy"),
    ("IEC 60255-187-1:2021 Measuring relays and protection equipment - Part 187-1: Functional requirements for restrained and unrestrained differential protection of motors, generators and transformers",
     "https://webstore.iec.ch/en/publication/32570", "Y", "IEC standard", "2021", "defines how operate time and other performance figures of differential functions are specified and tested", "n/a", "n/a", "n/a", "n/a", "n/a",
     "typical operate time (method of declaration)", "operate-time expectations; the standard specifies the test method, not one universal time limit (author to quote the clause)"),
    ("Ngaopitakkul A., Kunakorn A.: Internal fault classification in transformer windings using combination of DWT and back-propagation neural networks, IJCAS 4(3), 2006",
     "documents/Reference Papers (git f92ea33), not in Crossref", "N", "Int. J. Control, Automation, and Systems", "2006", "db4 DWT scale-1 + BPNN (LM)", "ATP/EMTP 200 kHz", "none", "n/r", "N", "N", "classification accuracy",
     "reproduced; bibliographic record read from the PDF only (see documents/reference_audit.md ref19) - author to confirm DOI/volume"),
]
cols = ["citation", "DOI/URL", "verified (Y/N)", "venue", "year", "method", "data (simulated / real, size)", "AI-relay interaction", "split (window / case)",
        "OOD or transfer test (Y/N)", "significance tests (Y/N)", "reported metrics", "relevance to us", "audit read"]
rows = []
for doi, q in Q.items():
    r = rec.get(doi)
    if r is None:
        raise SystemExit(f"no Crossref record saved for {doi}")
    au = r["authors"] or "(standard)"
    cit = f"{au}: {r['title']}" + (f", {r['venue']}" if r.get("venue") else "") + (f" {r['vol']}" if r.get("vol") else "") + (f", {r['page']}" if r.get("page") else "") + (f" ({r['year']})" if r.get("year") else "")
    rows.append([cit.replace("&amp;", "&"), "https://doi.org/" + doi, "Y", (r.get("venue") or r.get("type") or "").replace("&amp;", "&"), r.get("year") or "", *q[:8],
                 {"A": "abstract", "F": "full text", "R": "full text (repo spec)", "T": "title/record only"}[q[8]]])
for n in NODOI:
    rows.append(list(n[:13]) + ["record / page"])
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(cols)
    w.writerows(rows)
print(f"{len(rows)} rows -> {OUT}")
