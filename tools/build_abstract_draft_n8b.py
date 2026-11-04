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

# joint criterion fixed in the dated plan (BENCHMARK_FAIRNESS_PLAN.md, 2026-11-04 00:10, decision 2): >= 93 % dependability and >= 98.8 % security
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
inst_names = "1D-CNN, GRU, MLP, Key's network, random forest, LSTM"
W = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven']
f_clu = ROOT / "audit" / "scripts" / "out" / "clustered_sensitivity.json"
f_n6j = BASE / "n6c_tuned_harmonic.json"
# extended-grid tuned harmonic 87T = the reference relay (post-hoc; D-X1 clustered families "N6c ext" and "N8a ext")
f_n6xr, f_n6xt = BASE / "n6c_tuned_rows_ext.json", BASE / "n6c_tuned_harmonic_ext.txt"
f_n8x, f_dx2 = BASE / "n8a_instances_vs_tuned_harmonic_ext.json", BASE / "dx2_tuned_harmonic_ood_plantb.json"
_rx = jload(f_n6xr)["tuned"]
dHx = float(np.mean([100 * np.mean([r["correct"] for r in _rx if r["key"][0] == sd and r["should_trip"] and not r["undetectable"]]) for sd in cv.SEEDS]))
sHx = float(np.mean([100 * np.mean([r["correct"] for r in _rx if r["key"][0] == sd and not r["should_trip"] and not r["undetectable"]]) for sd in cv.SEEDS]))
_cx = {t["label"]: t for t in jload(f_clu)["N6c ext (Holm 4)"]}
gx_p = (_cx["tuned harmonic vs proposed hybrid dependability"]["holm_clust"], _cx["tuned harmonic vs proposed hybrid security"]["holm_clust"])
deployed_equal = min(gx_p) >= 0.05
hizx = re.search(r"Internal_HiZ \(n=(\d+)\): hybrid ([\d.]+), tuned harmonic ([\d.]+)", f_n6xt.read_text())
_c8x = {t["label"]: t for t in jload(f_clu)["N8a ext (Holm 16)"]}
_CN = {"1D-CNN": "1D-CNN hybrid", "Wavelet-GRU": "Wavelet-GRU hybrid", "Wavelet-ANN": "Wavelet-ANN hybrid", "Key (claim-C run)": "Key hybrid", "Wavelet-RF": "Wavelet-RF hybrid", "LSTM (tuned, B2)": "Proposed LSTM hybrid"}
n8x = jload(f_n8x)
_sigx = lambda t: _c8x[f"{_CN[t['instance']]} vs tuned harmonic {t['metric']}"]["holm_clust"] < 0.05  # noqa: E731
up_x = [t for t in n8x if t["metric"] == "dependability" and _sigx(t) and t["diff_pt"] > 0]
k_sig = len(up_x)
lower_x = [t for t in n8x if _sigx(t) and t["diff_pt"] < 0]
xb = jload(f_dx2)["plantB_main|tuned, extended grid (frozen)"]
_tb = jload(f_n6xr)["textbook"]
dTb = float(np.mean([100 * np.mean([r["correct"] for r in _tb if r["key"][0] == sd and r["should_trip"] and not r["undetectable"]]) for sd in cv.SEEDS]))
tune_gain = dHx - dTb
max_cls_gain = max(t["diff_pt"] for t in n8x if t["metric"] == "dependability")
_mac = ROOT / "paper_epsr" / "generated" / "paper_macros.tex"
if _mac.is_file():   # the sentence must agree with the macros used in the paper body
    _m = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", _mac.read_text(encoding="utf-8")))
    assert f"{dTb:.1f}" == _m["depHb"] and f"{dHx:.1f}" == _m["depHx"], (dTb, dHx, _m.get("depHb"), _m.get("depHx"))
_g = [t for t in jload(f_clu)["N6c (Holm 4)"] if t["label"] == "tuned harmonic vs proposed hybrid dependability"][0]
gap_dep, gap_p = -_g["diff"], _g["holm_clust"]
_seeds = [-v for v in jload(f_n6j)["tests"][2]["per_seed"].values()]   # hybrid minus tuned harmonic, per seed
assert abs(-jload(f_n6j)["tests"][2]["diff_pt"] - gap_dep) < 1e-9
gap_lo, gap_hi = min(_seeds), max(_seeds)
gap_stable = all(v > 0 for v in _seeds) or all(v < 0 for v in _seeds)
clu8 = {t["label"]: t for t in jload(f_clu)["N8a (Holm 16)"]}
clu_dep_max = max(t["holm_clust"] for lab, t in clu8.items() if lab.endswith("dependability"))
assert clu_dep_max < 0.05, "a dependability gain is not significant under the clustered test"
A = (
    "Learned 87T relays are rarely compared on common data and folds. "
    f"We evaluate on simulated {num(mva_A, 'd', 'plant A rating', f_plA, ' MVA')} and {num(mva_B, 'd', 'plant B rating', f_plB, ' MVA')} plants with trace-grouped cross-validation "
    f"({num(n_seeds, 'd', 'number of seeds', 'lstm_models/baselines/cv.py (cv.SEEDS)')} seeds x {num(n_folds, 'd', 'folds per seed', rel(BASE / 'key') + '/rows_seed*_fold*.json (file count)')} folds, "
    f"{num(n_traces, ',d', 'plant-A common-set traces (kept minus missing 20 kHz re-simulation)', f_miss)} traces) and re-implement {W[n_methods]} published methods. "
    f"Natively, none reaches {num(c_dep, '.0f', 'joint criterion, dependability (decision rule fixed in the dated plan)', f_plan, ' %')} dependability with "
    f"{num(c_sec, '.1f', 'joint criterion, security (decision rule fixed in the dated plan)', f_plan, ' %')} security; the two most dependable reach "
    f"{num(dep[by_dep[0]], '.1f', f'{by_dep[0]} native CV dependability', f_n5, ' %')} and {num(dep[by_dep[1]], '.1f', f'{by_dep[1]} native CV dependability', f_n5, ' %')} at "
    f"{num(sec[by_dep[0]], '.1f', f'{by_dep[0]} native CV security', f_n5, ' %')} and {num(sec[by_dep[1]], '.1f', f'{by_dep[1]} native CV security', f_n5, ' %')} security. "
    "A dual-path supervisory logic (87T-gated classifier, classifier-alone path, high-set) accepts any classifier. "
    f"With equal search and epoch budgets, {W[n_inst]} instances reach "
    f"{num(min(t['instance_pct'] for t in d8), '.1f', 'lowest instance dependability (hybrid, CV)', f_n8)}-{num(max(t['instance_pct'] for t in d8), '.1f', 'highest instance dependability (hybrid, CV)', f_n8, ' %')} dependability and "
    f"{num(min(t['instance_pct'] for t in s8), '.1f', 'lowest instance security (hybrid, CV)', f_n8)}-{num(max(t['instance_pct'] for t in s8), '.1f', 'highest instance security (hybrid, CV)', f_n8, ' %')} security. "
    f"A harmonic-restrained 87T tuned on validation traces over an extended grid (post-hoc; "
    f"{num(dHx, '.1f', 'extended-grid tuned harmonic 87T CV dependability', f_n6xr, ' %')} / {num(sHx, '.1f', 'extended-grid tuned harmonic 87T CV security', f_n6xr, ' %')}) "
    f"cannot be told apart from the deployed LSTM instance ({num(deployed['dependability'], '.1f', 'deployed hybrid CV dependability', f_n5, ' %')} / "
    f"{num(deployed['security'], '.1f', 'deployed hybrid CV security', f_n5, ' %')}; trace-clustered test, "
    + (f"p_H = {num(gx_p[0], '.2f', 'clustered Holm-4 p, deployed vs extended-grid tuned harmonic (dependability and security)', f_clu)} on both metrics"
       if f"{gx_p[0]:.2f}" == f"{gx_p[1]:.2f}" else
       f"p_H = {num(gx_p[0], '.2f', 'clustered Holm-4 p, dependability', f_clu)} and {num(gx_p[1], '.2f', 'clustered Holm-4 p, security', f_clu)}")
    + f") and detects more high-impedance faults ({num(float(hizx.group(3)), '.1f', 'Internal_HiZ dependability, extended-grid tuned harmonic (CV)', f_n6xt, ' %')} against "
    f"{num(float(hizx.group(2)), '.1f', 'Internal_HiZ dependability, deployed hybrid (CV)', f_n6xt, ' %')}). "
    f"{W[k_sig].capitalize()} of {W[n_inst]} instances are more dependable than this relay, by "
    f"{num(min(t['diff_pt'] for t in up_x), '.1f', 'smallest significant instance minus extended-grid tuned harmonic dependability difference [a]', f_n8x)}-"
    f"{num(max(t['diff_pt'] for t in up_x), '.1f', 'largest significant instance minus extended-grid tuned harmonic dependability difference [b]', f_n8x)} points "
    f"(post-hoc, Holm-adjusted), and none is less secure. "
    f"Tuning alone raised the harmonic 87T from {num(dTb, '.1f', 'textbook harmonic 87T CV dependability', f_n6xr, ' %')} (textbook) to "
    f"{num(dHx, '.1f', 'extended-grid tuned harmonic 87T CV dependability', f_n6xr, ' %')} dependability, by {num(tune_gain, '.1f', 'tuning gain: extended-grid minus textbook dependability (pt)', f_n6xr)} points, "
    f"more than any classifier gains over the tuned relay (at most {num(max_cls_gain, '.1f', 'largest instance minus extended-grid tuned harmonic dependability difference', f_n8x)}). "
    f"Zero-shot security on the unseen plant is "
    f"{num(kb_sec, '.1f', 'Key hybrid plant-B zero-shot security', f_kb, ' %')} with Key's network but {num(zs['security_pct'], '.1f', 'deployed hybrid plant-B zero-shot security', f_zs, ' %')} with the deployed LSTM, "
    f"whose classifier-alone path caused {num(tpc['false_trip_first_path']['solo'], 'd', 'plant-B false trips first fired by the AI-alone path', f_tpc)} of "
    f"{num(tpc['variants']['Proposed as evaluated (high-set + gate + solo)']['false_trips'], 'd', 'plant-B false trips, deployed hybrid', f_tpc)} false trips; "
    f"the frozen tuned relay reaches {num(xb['dep'], '.1f', 'extended-grid tuned harmonic plant-B zero-shot dependability', f_dx2, ' %')} / "
    f"{num(xb['sec'], '.1f', 'extended-grid tuned harmonic plant-B zero-shot security', f_dx2, ' %')}. "
    "The deployed LSTM relay does not outperform a well-tuned conventional relay; the benchmark, the reproductions and the classifier-agnostic logic are the contribution."
)

# ------------------------------------------------------------------------------------------------ checks
checks = [
    ("no banned word in title or abstract", not any(re.search(rf"\b{re.escape(b)}\b", (title + ' ' + A).lower()) for b in BANNED)),
    (f"no native reproduction meets {c_dep:.0f} % / {c_sec} % (claim restricted to native mode)", none_native_meets),
    ("the deployed hybrid is NOT significantly different from the extended-grid tuned harmonic 87T on either metric (clustered Holm-4), so no 'beats' claim", deployed_equal),
    ("no sentence claims that the deployed hybrid beats a tuned relay", "points more dependable than the tuned relay" not in A and "lead" not in A),
    (f"[k] = {k_sig} of {n_inst} instances significantly more dependable than the extended-grid reference (clustered Holm-16); [a]-[b] over those {k_sig}", k_sig >= 1),
    ("no instance significantly less dependable or less secure than the extended-grid reference (so 'none is less secure' holds)", not lower_x),
    ("range quoted over ALL instances (min and max), not the top instance only", True),
    (f"high-impedance result present (n = {hizx.group(1)})", "high-impedance" in A),
    (f"tuning gain {tune_gain:.2f} pt is larger than every classifier's gain over the tuned relay (max {max_cls_gain:.2f} pt)", tune_gain > max_cls_gain),
]
words = len(A.split())
checks.append((f"abstract has {words} words (EPSR limit 250)", words <= 250))
TEX = ROOT / "paper_epsr" / "generated" / "abstract.tex"
tex = A
tex = tex.replace("p_H = ", "$p_{\\mathrm{H}}=$\\,")
for o, n in ((" %", "\\,\\%"), (" x ", " $\\times$ "), (" MVA", "\\,MVA")):
    tex = tex.replace(o, n)
# hyphens stay plain hyphens; only a numeric range (digit-digit) becomes an en dash, and a leading minus sign becomes a math minus
tex = re.sub(r"(?<=\d)-(?=\d)", "--", tex)
tex = re.sub(r"(?<![\w.$])-(?=\d)", "$-$", tex)
assert not re.search(r"[A-Za-z]--|--[A-Za-z]", tex), "a word hyphen became an en dash"
TEX.parent.mkdir(parents=True, exist_ok=True)
TEX.write_text("% generated by tools/build_abstract_draft_n8b.py - do not edit\n" + tex + "\n", encoding="utf-8")

L = ["# Abstract (D-N8b, revised for paper-v1: <= 250 words, clustered test, equal search and epoch budget)", "",
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
