"""D-N8b: abstract DRAFT (claim-C framing) with every number read from a saved file.

Wording = the text in paper_epsr/abstract_draft_N8b.txt (author-approved wording, IMPLEMENTATION_PLAN.md 2026-11-04 00:13); here every
number is filled in by this script and registered with its source file, so the abstract cannot drift from the results.
Output: paper_epsr/ABSTRACT_DRAFT.md (abstract + number-to-source map + automatic checks). Not inserted into main.tex.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import cv  # noqa: E402

BASE = ROOT / "runs" / "20261101_v5_benchmark_fair"
OUT = ROOT / "paper_epsr" / "ABSTRACT_DRAFT.md"
BANNED = ("best", "superior", "state of the art", "state-of-the-art", "outperforms all")
SRC: list[tuple[str, str, str]] = []  # (printed number, what it is, source)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def num(value, fmt: str, what: str, src: Path | str, suffix: str = "") -> str:
    s = format(value, fmt) + suffix
    SRC.append((s, what, src if isinstance(src, str) else rel(src)))
    return s


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ sources
f_plA, f_plB = ROOT / "simulations" / "plant_v5_checks_A.txt", ROOT / "simulations" / "plant_v5_checks_B.txt"
mva_A = int(re.search(r"S = (\d+) MVA", f_plA.read_text()).group(1))
mva_B = int(re.search(r"S = (\d+) MVA", f_plB.read_text()).group(1))

f_miss = ROOT / "documents" / "baselines" / "hr_missing_traces.txt"
m = re.match(r"plant A main set: (\d+) kept traces, (\d+) without", f_miss.read_text().splitlines()[0])
n_traces = int(m.group(1)) - int(m.group(2))

f_n5 = BASE / "n5_statistics.json"
n5 = jload(f_n5)
dep = {t["method"]: t["method_pct"] for t in n5["tests"] if t["reference"] == "Proposed hybrid" and t["metric"] == "dependability"}
sec = {t["method"]: t["method_pct"] for t in n5["tests"] if t["reference"] == "Proposed hybrid" and t["metric"] == "security"}
deployed = {t["metric"]: t["ref_pct"] for t in n5["tests"] if t["reference"] == "Proposed hybrid"}
n_methods = len(dep)
n_folds = len({(f.name) for f in (BASE / "key").glob("rows_seed*_fold*.json")}) // len(cv.SEEDS)
n_seeds = len(cv.SEEDS)
NAMES = {"key": "Key et al.", "alhamd": "Alhamd et al.", "abdusalam_ba_svm": "Abdusalam et al.", "afrasiabi": "Afrasiabi et al.",
         "simoes_grid": "Simões et al.", "ngaopitakkul": "Ngaopitakkul and Kunakorn"}
by_dep = sorted(dep, key=lambda k: -dep[k])
most_secure = max(sec, key=lambda k: sec[k])

# pre-registered joint criterion (BENCHMARK_FAIRNESS_PLAN.md, 2026-11-04 00:10, decision 2): >= 93 % dependability and >= 98.8 % security
f_plan = ROOT / "BENCHMARK_FAIRNESS_PLAN.md"
crit = re.search(r"only family of methods with ≥ (\d+) % dependability and ≥ ([\d.]+) % security", f_plan.read_text(encoding="utf-8"))
c_dep, c_sec = float(crit.group(1)), float(crit.group(2))
none_native_meets = not any(dep[k] >= c_dep and sec[k] >= c_sec for k in dep)

f_n8 = BASE / "n8a_instances_vs_tuned_harmonic.json"
n8 = jload(f_n8)
d8 = [t for t in n8 if t["metric"] == "dependability"]
s8 = [t for t in n8 if t["metric"] == "security"]
n_inst = len(d8)
th_dep, th_sec = d8[0]["tuned_harmonic_pct"], s8[0]["tuned_harmonic_pct"]
n_sig_dep = sum(t["p_holm16"] < 0.05 and t["diff_pt"] > 0 for t in d8)
holm_n = len(n8) + len(jload(BASE / "n6c_tuned_harmonic.json")["tests"])

f_uniq = BASE / "b2_equal_search" / "unique_configs.json"
drawn = {v["drawn"] for v in jload(f_uniq).values()}
assert len(drawn) == 1
drawn = drawn.pop()

f_zs = ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "zero_shot_summary.json"
zs = jload(f_zs)["Proposed"]
f_tpc = ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "trip_path_check.json"
tpc = jload(f_tpc)
f_kb = BASE / "full" / "key_hybrid" / "final_plantB_main.json"
kb = [r for r in jload(f_kb)["hybrid"] if not r["undetectable"]]
kb_sec = 100 * np.mean([r["correct"] for r in kb if not r["should_trip"]])

f_n6t = BASE / "n6c_tuned_harmonic.txt"
hiz = re.search(r"Internal_HiZ \(n=(\d+)\): hybrid ([\d.]+), tuned harmonic ([\d.]+)", f_n6t.read_text())

f_b2 = BASE / "b2_equal_search" / "b2_summary.json"
svm = {t["metric"]: t["other_pct"] for t in jload(f_b2) if t["test"].startswith("Wavelet-SVM hybrid vs deployed")}

# ------------------------------------------------------------------------------------------------ abstract (approved wording)
title = "A model-agnostic dual-path supervisory logic for transformer differential protection, evaluated with a leak-free benchmark of six reproduced methods"
inst_names = "1D-CNN, GRU, ANN, Key's network, RF, LSTM"
A = (
    "Published learning-based transformer differential relays are rarely compared under the same data, folds and decision logic. "
    f"We evaluate on simulated {num(mva_A, 'd', 'plant A rating', f_plA, ' MVA')} and {num(mva_B, 'd', 'plant B rating', f_plB, ' MVA')} plants with trace-grouped cross-validation "
    f"({num(n_seeds, 'd', 'number of seeds', 'lstm_models/baselines/cv.py (cv.SEEDS)')} seeds x {num(n_folds, 'd', 'folds per seed', rel(BASE / 'key') + '/rows_seed*_fold*.json (file count)')} folds, "
    f"{num(n_traces, ',d', 'plant-A common-set traces (kept minus missing 20 kHz re-simulation)', f_miss)} traces) and re-implement "
    f"{['zero','one','two','three','four','five','six','seven'][n_methods]} published methods, trained on our data at each paper's own sampling rate. "
    f"Natively, none of the {['zero','one','two','three','four','five','six','seven'][n_methods]} reaches {num(c_dep, '.0f', 'joint criterion, dependability (pre-registered)', f_plan, ' %')} dependability and "
    f"{num(c_sec, '.1f', 'joint criterion, security (pre-registered)', f_plan, ' %')} security together: the two most dependable ({NAMES[by_dep[0]]}, {NAMES[by_dep[1]]}) reach "
    f"{num(dep[by_dep[0]], '.1f', f'{by_dep[0]} native CV dependability', f_n5, ' %')} and {num(dep[by_dep[1]], '.1f', f'{by_dep[1]} native CV dependability', f_n5, ' %')} at only "
    f"{num(sec[by_dep[0]], '.1f', f'{by_dep[0]} native CV security', f_n5, ' %')} and {num(sec[by_dep[1]], '.1f', f'{by_dep[1]} native CV security', f_n5, ' %')} security, "
    f"and the most secure ({NAMES[most_secure]}) reaches {num(dep[most_secure], '.1f', f'{most_secure} native CV dependability', f_n5, ' %')} dependability. "
    "We then study a dual-path supervisory logic (87T vote, confirmed classifier output, AI-alone path, high-set) with interchangeable classifiers. "
    f"In hybrid mode, {['zero','one','two','three','four','five','six','seven'][n_inst]} instances ({inst_names}; equal {num(drawn, 'd', 'configurations drawn per model (B2)', f_uniq)}-configuration search, equal training budget) give "
    f"{num(min(t['instance_pct'] for t in d8), '.1f', 'lowest instance dependability (hybrid, CV)', f_n8)}-{num(max(t['instance_pct'] for t in d8), '.1f', 'highest instance dependability (hybrid, CV)', f_n8, ' %')} dependability and "
    f"{num(min(t['instance_pct'] for t in s8), '.1f', 'lowest instance security (hybrid, CV)', f_n8)}-{num(max(t['instance_pct'] for t in s8), '.1f', 'highest instance security (hybrid, CV)', f_n8, ' %')} security, "
    f"and the deployed LSTM instance used in our Simulink closed loop gives {num(deployed['dependability'], '.1f', 'deployed hybrid CV dependability', f_n5, ' %')} and "
    f"{num(deployed['security'], '.1f', 'deployed hybrid CV security', f_n5, ' %')}. "
    f"All {['zero','one','two','three','four','five','six','seven'][n_inst]} are significantly more dependable than a validation-tuned harmonic-restrained 87T "
    f"({num(th_dep, '.1f', 'tuned harmonic 87T CV dependability', f_n8, ' %')} / {num(th_sec, '.1f', 'tuned harmonic 87T CV security', f_n8, ' %')}) by "
    f"{num(min(t['diff_pt'] for t in d8), '.1f', 'smallest instance minus tuned-harmonic dependability difference', f_n8)}-{num(max(t['diff_pt'] for t in d8), '.1f', 'largest instance minus tuned-harmonic dependability difference', f_n8)} percentage points "
    f"(Holm-corrected, post-hoc), with security within {num(min(t['diff_pt'] for t in s8), '+.1f', 'smallest security difference', f_n8)} to {num(max(t['diff_pt'] for t in s8), '+.1f', 'largest security difference', f_n8)} points. "
    f"Transfer to an unseen plant depends on the classifier: zero-shot security on the {num(mva_B, 'd', 'plant B rating', f_plB, ' MVA')} plant is "
    f"{num(kb_sec, '.1f', 'Key hybrid plant-B zero-shot security', f_kb, ' %')} with Key's network but {num(zs['security_pct'], '.1f', 'deployed hybrid plant-B zero-shot security', f_zs, ' %')} with the deployed LSTM, "
    f"whose AI-alone path caused {num(tpc['false_trip_first_path']['solo'], 'd', 'plant-B false trips first fired by the AI-alone path', f_tpc)} of "
    f"{num(tpc['variants']['Proposed as evaluated (high-set + gate + solo)']['false_trips'], 'd', 'plant-B false trips, deployed hybrid', f_tpc)} false trips. "
    f"High-impedance faults remain the limit: about {num(float(hiz.group(2)), '.0f', 'Internal_HiZ dependability, deployed hybrid (CV)', f_n6t, ' %')} dependability for the hybrid and "
    f"{num(float(hiz.group(3)), '.0f', 'Internal_HiZ dependability, tuned harmonic 87T (CV)', f_n6t, ' %')} for the tuned conventional relay. "
    f"Only a kernel SVM is clearly worse ({num(svm['dependability'], '.1f', 'SVM hybrid (tuned, B2) CV dependability', f_b2, ' %')} / {num(svm['security'], '.1f', 'SVM hybrid (tuned, B2) CV security', f_b2, ' %')}). "
    "Among the other classifiers the choice is not decisive; the supervisory logic and the evaluation protocol are the contribution."
)

# ------------------------------------------------------------------------------------------------ checks
checks = [
    ("no banned word in title or abstract", not any(re.search(rf"\b{re.escape(b)}\b", (title + ' ' + A).lower()) for b in BANNED)),
    (f"no native reproduction meets {c_dep:.0f} % / {c_sec} % (claim restricted to native mode)", none_native_meets),
    (f"every instance significantly more dependable than the tuned harmonic 87T (Holm-{holm_n}): {n_sig_dep} of {n_inst}", n_sig_dep == n_inst),
    ("no instance significantly less secure than the tuned harmonic 87T", not any(t["p_holm16"] < 0.05 and t["diff_pt"] < 0 for t in s8)),
    ("range quoted over ALL instances (min and max), not the top instance only", True),
    (f"Internal_HiZ limitation present (n = {hiz.group(1)})", "High-impedance" in A),
]
words = len(A.split())

L = ["# Abstract draft (D-N8b) — NOT final, not in main.tex", "",
     "Generated by `tools/build_abstract_draft_n8b.py`; do not edit by hand (re-run the script). Every number below is read from a saved result file; "
     "the map after the abstract lists each one with its source. Wording = `paper_epsr/abstract_draft_N8b.txt` (approved by the author, "
     "IMPLEMENTATION_PLAN.md entry 2026-11-04 00:13). The paper body is **not** rewritten until the author approves this file.", "",
     "## Title (draft)", "", title, "", "## Abstract (draft)", "", A, "", f"*{words} words.* EPSR's abstract limit is to be checked against the final template; trimming changes wording only, never numbers.", "",
     "## Number-to-source map", "", "| # | Number as printed | What it is | Source file |", "|---|---|---|---|"]
for i, (s, what, src) in enumerate(SRC, 1):
    L.append(f"| {i} | {s} | {what} | `{src}` |")
L += ["", "## Automatic checks", ""] + [f"- [{'x' if ok else ' '}] {c}" for c, ok in checks]
L += ["", "## Labels that must travel with these numbers", "",
      f"- The instance-vs-tuned-harmonic range is **post-hoc** (D-N8a, added after N6c), Holm over {holm_n} tests; cite it only as a range over all {n_inst} instances.",
      f"- Security differences vs the tuned harmonic 87T are not significant for {sum(t['p_holm16'] >= 0.05 for t in s8)} of {n_inst} instances; their per-seed signs change for "
      f"{sum(not t['sign_stable'] for t in s8)} of {n_inst} (`unstable`).",
      "- \"Model-agnostic\" refers to the supervisory logic as a whole; the 87T gate is not presented as what makes a classifier secure (see the 2026-11-04 00:08 log entry).",
      "- The deployed LSTM is \"the deployed instance used in the Simulink closed loop\", not the headline."]
OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
if not all(ok for _, ok in checks):
    sys.exit("a check failed — see the file")
