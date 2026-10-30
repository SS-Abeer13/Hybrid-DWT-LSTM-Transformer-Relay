"""Writes paper_epsr/generated/results_macros.tex (every number used in the paper text) from the saved result files, and copies the generated tables.
No number is typed by hand.   python tools/build_paper_macros_v5.py
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "runs"
TAG = "20261029_v5"
OUT = ROOT / "paper_epsr" / "generated"
OUT.mkdir(parents=True, exist_ok=True)


def J(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


cv = J(R / f"{TAG}_cv5_seeds" / "summary.json")
st = J(R / f"{TAG}_stats" / "stats.json")
hm = J(R / f"{TAG}_harmonic87t" / "summary.json")
ood = J(R / f"{TAG}_final" / "report_ood.json")["ood"]["Hybrid + AI-alone path"]
zs = J(R / f"{TAG}_plant_b_zeroshot" / "zero_shot_summary.json")
cp = J(R / f"{TAG}_cross_plant" / "cross_plant_summary.json")
lo = J(R / f"{TAG}_leave_one_out" / "leave_one_out_summary.json")
e1 = J(R / f"{TAG}_e1_harmonic_gate" / "e1_summary.json")
tp = J(R / f"{TAG}_plant_b_zeroshot" / "trip_path_check.json")
lat = J(R / f"{TAG}_latency" / "latency.json")
latc = J(R / f"{TAG}_latency" / "latency_c.json")
fin = R / f"{TAG}_final"
M: dict[str, str] = {}


def put(name: str, val, fmt: str = "{:.2f}") -> None:
    M[name] = fmt.format(val) if not isinstance(val, str) else val


pool = cv["pooled"]
H = pool["Hybrid + AI-alone path"]
for key, tag in (("87T alone", "Ta"), ("LSTM alone", "Lstm"), ("Hybrid (87T gate)", "Gate"), ("Hybrid + AI-alone path", "Hyb")):
    put(f"cv{tag}Dep", pool[key]["dependability_pct"]); put(f"cv{tag}Sec", pool[key]["security_pct"])
    put(f"cv{tag}Missed", pool[key]["missed"], "{:d}"); put(f"cv{tag}False", pool[key]["false_trips"], "{:d}")
    put(f"cv{tag}Med", pool[key]["operate"]["median_ms"], "{:.1f}")
hv = hm["variants"]["per_phase"]["main_pooled"]
put("cvHarmDep", hv["dependability_pct"]); put("cvHarmSec", hv["security_pct"])
put("cvNfold", cv["n_fold_models"], "{:d}"); put("cvNseed", len(cv["seeds"]), "{:d}")
put("cvNeval", (H["n_fault"] + H["n_healthy"]) // len(cv["seeds"]), "{:d}")
put("cvNfault", H["n_fault"] // len(cv["seeds"]), "{:d}"); put("cvNhealthy", H["n_healthy"] // len(cv["seeds"]), "{:d}")
sd = st["multi_seed_fold_models"]["Hybrid + AI-alone path"]
put("cvHybDepSD", sd["dependability"]["std"]); put("cvHybSecSD", sd["security"]["std"])
cats = H["by_category"]
put("catHiz", cats["Internal HiZ"]["correct_pct"], "{:.1f}"); put("catExtInrush", cats["External in inrush"]["correct_pct"], "{:.1f}")
put("catSotf", cats["SOTF"]["correct_pct"], "{:.1f}"); put("catLvSolid", cats["Internal LV solid"]["correct_pct"], "{:.1f}")
put("catNcat", len(cats), "{:d}")
for nm, key in (("U", "proposed_vs_unrestrained_87t"), ("P", "proposed_vs_harmonic_87t_per_phase")):
    mc = st["mcnemar"][key]
    for met, mn in (("dependability", "Dep"), ("security", "Sec")):
        put(f"mc{nm}{mn}Wins", mc[met]["table"]["n10_A_wins_B_fails"], "{:d}"); put(f"mc{nm}{mn}Loss", mc[met]["table"]["n01_A_fails_B_wins"], "{:d}")
        put(f"mc{nm}{mn}P", mc[met]["p_value"], "{:.2g}"); put(f"mc{nm}{mn}N", mc[met]["n_traces"], "{:d}")
        put(f"mc{nm}{mn}Prop", mc[met]["accuracy_A_pct"]); put(f"mc{nm}{mn}Base", mc[met]["accuracy_B_pct"])
o = ood
put("oodDep", o["overall"]["dependability_pct"], "{:.1f}"); put("oodSec", o["overall"]["security_pct"], "{:.1f}")
put("oodN", o["overall"]["n_fault"] + o["overall"]["n_healthy"], "{:d}")
put("oodMed", o["overall"]["operate"]["median_ms"], "{:.1f}"); put("oodFalse", o["overall"]["false_trips"], "{:d}"); put("oodMissed", o["overall"]["missed"], "{:d}")
for b in range(1, 6):
    put(f"oodBlock{'ABCDE'[b - 1]}Dep", o["blocks"][str(b)]["dependability_pct"], "{:.1f}"); put(f"oodBlock{'ABCDE'[b - 1]}Sec", o["blocks"][str(b)]["security_pct"], "{:.1f}")
put("thrAi", (fin / "decision_threshold.txt").read_text().split()[0], "{}"); put("thrSolo", (fin / "decision_solo_threshold.txt").read_text().split()[0], "{}")
put("dwellN", (fin / "decision_dwell.txt").read_text().split()[0], "{}")
# plant B
for k, tag in (("Proposed", "Prop"), ("Harmonic 87T", "Harm"), ("87T alone", "Ta"), ("LSTM alone", "Lstm")):
    put(f"zs{tag}Dep", zs[k]["dependability_pct"]); put(f"zs{tag}Sec", zs[k]["security_pct"])
    put(f"zs{tag}False", zs[k]["false_trips"], "{:d}"); put(f"zs{tag}Missed", zs[k]["missed_trips"], "{:d}")
put("zsNfault", zs["Proposed"]["n_fault"], "{:d}"); put("zsNhealthy", zs["Proposed"]["n_healthy"], "{:d}")
put("cpDep", cp["overall"]["dependability_pct"]); put("cpSec", cp["overall"]["security_pct"])
put("cpADep", cp["plant_a_subset"]["dependability_pct"]); put("cpASec", cp["plant_a_subset"]["security_pct"])
put("cpBDep", cp["plant_b_subset"]["dependability_pct"]); put("cpBSec", cp["plant_b_subset"]["security_pct"])
put("looABDep", lo["train_a_test_b"]["dependability_pct"]); put("looABSec", lo["train_a_test_b"]["security_pct"])
put("looBADep", lo["train_b_test_a"]["dependability_pct"]); put("looBASec", lo["train_b_test_a"]["security_pct"])
v = tp["variants"]
put("tpFalseAll", v["Proposed as evaluated (high-set + gate + solo)"]["false_trips"], "{:d}")
put("tpFalseSolo", tp["false_trip_first_path"].get("solo", 0), "{:d}")
put("tpNoSoloDep", v["without AI-alone path (high-set + gate)"]["dependability_pct"]); put("tpNoSoloSec", v["without AI-alone path (high-set + gate)"]["security_pct"])
put("tpHighsetDep", v["high-set only"]["dependability_pct"], "{:.1f}")
put("tpSoloOnlyFaults", tp["faults_tripped_only_by_solo"], "{:d}")
extc = sum(n for c, d in tp["false_trips_by_category"].items() if c.startswith("External") or c.startswith("Stress_Ext") for k, n in d.items() if not k.startswith("_"))
put("tpFalseExt", extc, "{:d}")
# E1
put("eOneDep", e1["cv"]["e1"]["dependability_pct"]); put("eOneSec", e1["cv"]["e1"]["security_pct"])
put("eOneOodSec", e1["ood"]["e1"]["security_pct"], "{:.1f}")
put("eOneDepWins", e1["cv"]["paired_vs_reference"]["dependability"]["a_wins"], "{:d}"); put("eOneDepLoss", e1["cv"]["paired_vs_reference"]["dependability"]["b_wins"], "{:d}")
put("eOneDepP", e1["cv"]["paired_vs_reference"]["dependability"]["p_value"], "{:.2g}")
# closed loop
mir = J(fin / "d4" / "mirror.json")
agree = tot = simok = mirok = nfail = 0
dts = []
for lab in ("main", "ood"):
    Rr = list(np.atleast_1d(loadmat(ROOT / "simulations" / f"test_hybrid_relay_d5{lab}_results.mat", squeeze_me=True, struct_as_record=False)["R"]))
    sim = {int(str(r.name).split("#")[-1]): r for r in Rr}
    nfail += sum(1 for r in Rr if not bool(r.passed))
    for m in mir[lab]:
        s_ = sim[int(m["index"])]
        agree += int(bool(m["tripped"]) == bool(s_.tripped)); tot += 1
        simok += int(bool(s_.tripped) == bool(m["should_trip"])); mirok += int(bool(m["tripped"]) == bool(m["should_trip"]))
        if m["tripped"] and s_.tripped:
            dts.append(abs((float(s_.tripTime) - float(m["trip_time_s"])) * 1000.0))
put("clAgree", agree, "{:d}"); put("clTotal", tot, "{:d}"); put("clSimOk", simok, "{:d}"); put("clMirOk", mirok, "{:d}")
put("clDtMed", float(np.median(dts))); put("clDtMax", float(np.max(dts))); put("clNfail", nfail, "{:d}")
pbt = (ROOT / "simulations" / "test_hybrid_relay_plant_b_results.txt").read_text(encoding="utf-8")
pm = re.search(r"Passed (\d+) / (\d+)", pbt)
put("clBPass", pm.group(1), "{}"); put("clBTotal", pm.group(2), "{}")
# latency and size
co, cc = lat["combined_relay_pipeline"], latc["combined_relay_pipeline"]
put("latOnnxMed", co["median_us"], "{:.1f}"); put("latOnnxPnn", co["p99_us"], "{:.1f}"); put("latCMed", cc["median_us"], "{:.1f}"); put("latCPnn", cc["p99_us"], "{:.1f}"); put("latCMax", cc["max_us"], "{:.1f}")
put("latPeriod", 625, "{}")
macs_t = 4 * 64 * (12 + 64) + 4 * 64 * (64 + 64)    # LSTM layer 0 (12 inputs) and layer 1 (64 inputs), per time step
put("netMacs", 32 * macs_t / 1e6, "{:.2f}"); put("netParams", J(R / f"{TAG}_literature_benchmark" / "literature_benchmark_summary.json")["metadata"]["Standalone LSTM"]["params"], "{:d}")
# datasets
for tagname, f in (("A", "StressDataset_v5_20261028_162333_plus_topups_coverage.json"), ("B", "StressDataset_PlantBv5_20261028_212041_plus_topups_coverage.json")):
    put(f"dsMain{tagname}", J(ROOT / "datasets" / f)["n"], "{:d}")
# plant checks
def tf(pl: str, idx: int = 0) -> str:
    t = (ROOT / "simulations" / f"plant_v5_checks_{pl}.txt").read_text(encoding="utf-8")
    return re.findall(r"TRUE RMS steady ([\d.]+) pu", t)[idx]
put("tfA", tf("A"), "{}"); put("tfB", tf("B"), "{}")

# literature table for the paper (no typed citations; models are cited in the text)
lit = J(R / f"{TAG}_literature_benchmark" / "literature_benchmark_summary.json")
order = ["Conventional 87T", "Wavelet-SVM", "Wavelet-ANN", "Wavelet-RF", "1D-CNN", "Wavelet-GRU", "Standalone LSTM", "Proposed Hybrid DWT-LSTM"]
rows = []
for m in order:
    sm = lit["summaries"][m]
    for mode, lab in (("standalone", "direct trip"), ("hybrid", "in the dual-path relay")):
        if mode in sm:
            q = sm[mode]
            par = lit["metadata"][m]["params"]
            rows.append(f"{m} & {lab} & {par:,} & {q['dependability_pct']:.2f} & {q['security_pct']:.2f} & {q['operate']['median_ms']:.1f} & {q['false_trips']}\\\\".replace(",", "{,}") if par else f"{m} & {lab} & --- & {q['dependability_pct']:.2f} & {q['security_pct']:.2f} & {q['operate']['median_ms']:.1f} & {q['false_trips']}\\\\")
head = [r"\begin{tabular}{@{}llrrrrr@{}}\toprule", r"Model & Mode & Parameters & Dep.\,(\%) & Sec.\,(\%) & Median $T_{op}$ (ms) & False trips\\ \midrule"]
(OUT / "table_lit_paper.tex").write_text(chr(10).join(head + rows + [r"\bottomrule", r"\end{tabular}"]), encoding="utf-8")
(OUT / "results_macros.tex").write_text("% generated by tools/build_paper_macros_v5.py - do not edit\n" + "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(M.items())) + "\n", encoding="utf-8")
for t in ("table_6_1_ablation", "table_6_2_categories", "table_6_3_statistical_tests", "table_6_4_ood", "table_6_5_closed_loop", "table_6_6_latency", "table_6_8_plant_b_generalization", "table_literature_benchmark"):
    src = ROOT / "latex_source" / "latex" / f"{t}.tex"
    if src.is_file():
        shutil.copy(src, OUT / f"{t}.tex")
print(len(M), "macros written;", len(list(OUT.glob("table_*.tex"))), "tables copied")
