"""Audit task B2: every number in the IMPLEMENTATION_PLAN.md entries of 2026-11-02 and 2026-11-03 (plus the 2026-11-04 00:08 entry,
which belongs to the same working day in local time) against the saved files.

Each claim = (log entry time, the number as written in the log, a function that recomputes the value from a saved file, the
number of decimals the log uses). The 'as written' strings are QUOTED from IMPLEMENTATION_PLAN.md; the comparison value is always
recomputed here from the file. A claim matches when the recomputed value rounds to the quoted value (or, for p-values, agrees to the
quoted 2 significant digits; for 'p < x' claims, when the bound holds).
Output: audit/scripts/out/log_claims.csv and .txt
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BF = ROOT / "runs" / "20261101_v5_benchmark_fair"
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
J = lambda p: json.loads((BF / p).read_text())  # noqa: E731
SEEDS = (20261021, 20261022, 20261023)
BAD_FILE = ROOT / "documents" / "baselines" / "hr_missing_traces.txt"


def bad_set():
    metas = json.loads((BF / "trace_metas_plantA.json").read_text())
    ex = set()
    for line in BAD_FILE.read_text().splitlines()[2:]:
        p = [x.strip() for x in line.split(",")]
        ex.add((p[0], int(p[1])))
    return {i for i, m in enumerate(metas) if (m["source_file"], int(m["source_index"])) in ex}


BAD = bad_set()


def rows_pct(rows, flag, drop_bad=True):
    v = [bool(r["correct"]) for r in rows if int(r["should_trip"]) == flag and not r.get("undetectable") and (not drop_bad or int(r["trace"]) not in BAD)]
    return 100 * np.mean(v)


def rowsdir(d, pat="rows_seed*_fold*.json", key=None):
    out = []
    for f in sorted((BF / d).glob(pat)):
        j = json.loads(f.read_text())
        out += j[key] if key else j
    return out


def n4(method, setname, mode, metric):
    for line in (BF / "n4_full_summary.txt").read_text().splitlines():
        p = line.split()
        if p and p[0] == method and setname in line:
            nums = [float(x) for x in re.findall(r"\|\s*([\d.]+)\s+([\d.]+)", line)[0 if mode == "native" else 1]]
            return nums[0 if metric == "dep" else 1]
    raise KeyError(method)


def full_final(method, lab, mode, flag):
    j = J(f"full/{method}/final_{lab}.json")
    return rows_pct(j[mode], flag, drop_bad=False)


def full_cv(method, mode, flag):
    return rows_pct(rowsdir(f"full/{method}", "cv_seed*_fold*.json", mode), flag)


def t5(file, ref, method, metric, field, mode="native"):
    for t in J(file)["tests"]:
        if t["reference"] == ref and t["method"] == method and t["metric"] == metric and t.get("mode", "native") == mode:
            return t[field]
    raise KeyError((ref, method, metric))


def b1(seed, model, mode, metric):
    s = J(f"b1_equal_budget/seed_{seed}/literature_benchmark_summary.json")["summaries"][model][mode]
    return s["dependability_pct" if metric == "dep" else "security_pct"]


def ref_pct(variant, flag, seeds=SEEDS, ood=False):
    rows = []
    for s in seeds:
        for k in range(1, 6):
            rows += json.loads((ROOT / "runs" / "20261029_v5_cv5_seeds" / f"seed_{s}" / f"fold{k}" / "result.json").read_text())["rows"][variant]
    return rows_pct(rows, flag)


def kh(metric, field):
    return [t for t in J("n5_statistics_keyhybrid.json") if t["metric"] == metric][0][field]


def b2t(test, metric, field):
    return [t for t in J("b2_equal_search/b2_summary.json") if t["test"] == test and t["metric"] == metric][0][field]


def b2tab(model, mode, flag):
    rows = []
    for f in sorted((BF / "b2_equal_search").glob("final_seed*_fold*.json")):
        rows += json.loads(f.read_text())[model][mode]
    return rows_pct(rows, flag)


def n6(setting, metric, field):
    return [t for t in J("n6c_tuned_harmonic.json")["tests"] if t["setting"] == setting and t["metric"] == metric][0][field]


def n8(inst, metric, field):
    return [t for t in J("n8a_instances_vs_tuned_harmonic.json") if t["instance"] == inst and t["metric"] == metric][0][field]


def lat(name, field="median"):
    for line in (BF / "latency_baselines.txt").read_text().splitlines():
        if line.startswith(name + " "):
            m = re.search(r"median\s+([\d.]+) us\s+p99\s+([\d.na]+)\s+budget\s+([\d.na]+)", line)
            return float(m.group({"median": 1, "p99": 2, "budget": 3}[field]))
    raise KeyError(name)


def n4p(method, col):
    for line in (BF / "n4_progress.txt").read_text().splitlines():
        p = line.split()
        if p and p[0] == method:
            return float(p[{"folds": 1, "dep": 2, "sec": 3, "op": 4}[col]])


def summ(d, flag):
    j = J(f"{d}/summary.json")
    return j


def sim_summary(d, key):
    j = J(f"{d}/summary.json")
    # find dependability/security anywhere at the top level
    def find(o, k):
        if isinstance(o, dict):
            if k in o:
                return o[k]
            for v in o.values():
                r = find(v, k)
                if r is not None:
                    return r
        return None
    return find(j, key)


def gj(*path):
    o = J("gated_only_ablation.json")
    for p in path:
        o = o[p]
    return o


def keyhyb_thr(kind):
    v = [float(json.loads(f.read_text())[kind]) for f in sorted((BF / "full" / "key_hybrid").glob("cv_seed*_fold*.json"))]
    return v


def auc_range(model):
    r = J("b2_equal_search/search_results.json")[model]
    a = [c["val_auc"] for c in r]
    return max(a), min(a)


def pbpath():
    return (BF / "plantB_falsetrip_paths.txt").read_text()


C = []  # (entry, quoted, value, ndp, file, note)


def add(entry, quoted, fn, file, kind="num"):
    try:
        v = fn()
    except Exception as e:  # noqa: BLE001
        v = f"ERROR {type(e).__name__}: {e}"
    C.append((entry, quoted, v, kind, file))


E = "11-02 09:16"
add(E, "Simoes published dep 59.9", lambda: rows_pct(rowsdir("simoes_published"), 1), "simoes_published/rows_*.json")
add(E, "Simoes grid dep 69.7", lambda: rows_pct(rowsdir("simoes_grid"), 1), "simoes_grid/rows_*.json")
add(E, "Simoes published sec 95.3", lambda: rows_pct(rowsdir("simoes_published"), 0), "simoes_published/rows_*.json")
add(E, "Simoes grid sec 92.2", lambda: rows_pct(rowsdir("simoes_grid"), 0), "simoes_grid/rows_*.json")
add(E, "detector mean detection at factor 100: 86.1", lambda: float(re.search(r"factor\s+100:.*\|\s+([\d.]+) %", (BF / "n2_simoes_factor.txt").read_text()).group(1)), "n2_simoes_factor.txt")
E = "11-02 09:56"
add(E, "Afrasiabi (Hajipour) dep 87.06", lambda: rows_pct(rowsdir("afrasiabi"), 1), "afrasiabi/rows_*.json")
add(E, "Afrasiabi (Hajipour) sec 89.56", lambda: rows_pct(rowsdir("afrasiabi"), 0), "afrasiabi/rows_*.json")
add(E, "Afrasiabi no stage dep 86.41", lambda: rows_pct(rowsdir("afrasiabi_nocomp"), 1), "afrasiabi_nocomp/rows_*.json")
add(E, "Afrasiabi no stage sec 88.09", lambda: rows_pct(rowsdir("afrasiabi_nocomp"), 0), "afrasiabi_nocomp/rows_*.json")
add(E, "Key dep 96.91", lambda: rows_pct(rowsdir("key"), 1), "key/rows_*.json")
add(E, "Key sec 74.86", lambda: rows_pct(rowsdir("key"), 0), "key/rows_*.json")
E = "11-02 12:27"
add(E, "Abdusalam BA+SVM dep 76.06 (13 of 15 folds)", lambda: n4p("abdusalam_ba_svm", "dep"), "n4_progress.txt (snapshot)")
add(E, "Abdusalam BA+SVM sec 99.93 (13 of 15 folds)", lambda: n4p("abdusalam_ba_svm", "sec"), "n4_progress.txt (snapshot)")
add(E, "Alhamd reduced budget dep 85.79", lambda: rows_pct(rowsdir("alhamd_reduced_budget"), 1), "alhamd_reduced_budget/rows_*.json")
add(E, "Alhamd reduced budget sec 54.91", lambda: rows_pct(rowsdir("alhamd_reduced_budget"), 0), "alhamd_reduced_budget/rows_*.json")
add(E, "Ngaopitakkul dep 27.71", lambda: rows_pct(rowsdir("ngaopitakkul"), 1), "ngaopitakkul/rows_*.json")
add(E, "Ngaopitakkul sec 99.26", lambda: rows_pct(rowsdir("ngaopitakkul"), 0), "ngaopitakkul/rows_*.json")
E = "11-02 21:55"
for m, s, md, met, q in [("simoes_grid", "CV plant A", "native", "dep", "69.68"), ("simoes_grid", "CV plant A", "native", "sec", "92.20"), ("simoes_grid", "CV plant A", "modeb", "dep", "76.84"),
                         ("simoes_grid", "CV plant A", "modeb", "sec", "72.08"), ("simoes_grid", "plantA_OOD", "native", "dep", "70.95"), ("simoes_grid", "plantA_OOD", "native", "sec", "73.83"),
                         ("simoes_grid", "plantA_OOD", "modeb", "dep", "75.00"), ("simoes_grid", "plantA_OOD", "modeb", "sec", "60.40"), ("simoes_grid", "plantB_main", "native", "dep", "83.23"),
                         ("simoes_grid", "plantB_main", "native", "sec", "89.43"), ("simoes_grid", "plantB_main", "modeb", "dep", "86.71"), ("simoes_grid", "plantB_main", "modeb", "sec", "71.73"),
                         ("abdusalam_ba_svm", "CV plant A", "native", "dep", "76.38"), ("abdusalam_ba_svm", "CV plant A", "native", "sec", "99.95"), ("abdusalam_ba_svm", "CV plant A", "modeb", "dep", "79.23"),
                         ("abdusalam_ba_svm", "CV plant A", "modeb", "sec", "92.91"), ("abdusalam_ba_svm", "plantA_OOD", "native", "dep", "83.11"), ("abdusalam_ba_svm", "plantA_OOD", "native", "sec", "93.96"),
                         ("abdusalam_ba_svm", "plantA_OOD", "modeb", "dep", "84.46"), ("abdusalam_ba_svm", "plantA_OOD", "modeb", "sec", "86.58")]:
    if s == "CV plant A":
        add(E, f"{m} {s} {md} {met} {q}", lambda m=m, md=md, met=met: full_cv(m, md, 1 if met == "dep" else 0), f"full/{m}/cv_*.json")
    else:
        add(E, f"{m} {s} {md} {met} {q}", lambda m=m, s=s, md=md, met=met: full_final(m, s, md, 1 if met == "dep" else 0), f"full/{m}/final_{s}.json")
add(E, "plant-B cache 1,289 traces; 1,278 with a 20 kHz copy", lambda: len(J("full/key/final_plantB_main.json")["native"]), "full/key/final_plantB_main.json (rows)")
add(E, "OOD plant A: 297 of 300", lambda: len(J("full/key/final_plantA_OOD.json")["native"]), "full/key/final_plantA_OOD.json (rows)")
E = "11-02 23:11"
q = {("Standalone LSTM", "standalone"): ["97.92 / 96.78", "97.04 / 94.61", "98.08 / 95.42"], ("1D-CNN", "standalone"): ["97.52 / 97.08", "96.16 / 96.63", "97.84 / 97.43"],
     ("Wavelet-GRU", "standalone"): ["98.16 / 96.83", "97.36 / 95.37", "97.44 / 94.67"], ("Wavelet-ANN", "standalone"): ["97.76 / 96.43", "96.64 / 96.28", "97.36 / 96.98"],
     ("Proposed Hybrid DWT-LSTM", "hybrid"): ["93.92 / 99.14", "94.24 / 98.69", "90.81 / 99.04"], ("1D-CNN", "hybrid"): ["93.84 / 98.84", "93.21 / 99.40", "94.16 / 99.30"],
     ("Wavelet-GRU", "hybrid"): ["93.76 / 98.89", "93.92 / 98.79", "94.00 / 98.84"]}
for (mdl, md), vals in q.items():
    for s, v in zip(SEEDS, vals):
        d, sc = v.split(" / ")
        add(E, f"B1 {mdl} {md} seed {s} dep {d}", lambda s=s, mdl=mdl, md=md: b1(s, mdl, md, "dep"), f"b1_equal_budget/seed_{s}/literature_benchmark_summary.json")
        add(E, f"B1 {mdl} {md} seed {s} sec {sc}", lambda s=s, mdl=mdl, md=md: b1(s, mdl, md, "sec"), f"b1_equal_budget/seed_{s}/literature_benchmark_summary.json")
E = "11-03 08:17"
for m, s, md, met, qv in [("key", "CV plant A", "native", "dep", "96.99"), ("key", "CV plant A", "native", "sec", "75.28"), ("key", "CV plant A", "modeb", "dep", "97.23"), ("key", "CV plant A", "modeb", "sec", "99.56"),
                          ("key", "plantA_OOD", "native", "dep", "96.62"), ("key", "plantA_OOD", "native", "sec", "78.52"), ("key", "plantA_OOD", "modeb", "dep", "97.97"), ("key", "plantA_OOD", "modeb", "sec", "95.97"),
                          ("key", "plantB_main", "native", "dep", "98.16"), ("key", "plantB_main", "native", "sec", "69.75"), ("key", "plantB_main", "modeb", "dep", "96.93"), ("key", "plantB_main", "modeb", "sec", "98.94"),
                          ("alhamd", "CV plant A", "native", "dep", "96.53"), ("alhamd", "CV plant A", "native", "sec", "82.91"), ("alhamd", "CV plant A", "modeb", "dep", "97.93"), ("alhamd", "CV plant A", "modeb", "sec", "98.17"),
                          ("alhamd", "plantA_OOD", "native", "dep", "97.30"), ("alhamd", "plantA_OOD", "native", "sec", "87.25"), ("alhamd", "plantA_OOD", "modeb", "dep", "95.27"), ("alhamd", "plantA_OOD", "modeb", "sec", "95.30"),
                          ("alhamd", "plantB_main", "native", "dep", "92.64"), ("alhamd", "plantB_main", "native", "sec", "83.75"), ("alhamd", "plantB_main", "modeb", "dep", "89.98"), ("alhamd", "plantB_main", "modeb", "sec", "96.17"),
                          ("afrasiabi", "plantB_main", "native", "sec", "75.17"), ("abdusalam_ba_svm", "plantB_main", "native", "sec", "99.74"), ("abdusalam_ba_svm", "plantB_main", "native", "dep", "71.37"),
                          ("ngaopitakkul", "plantB_main", "native", "sec", "97.62"), ("ngaopitakkul", "plantB_main", "native", "dep", "28.02"), ("afrasiabi", "plantB_main", "modeb", "sec", "99.87"),
                          ("abdusalam_ba_svm", "plantB_main", "modeb", "sec", "95.51"), ("simoes_grid", "CV plant A", "modeb", "sec", "72.1"), ("abdusalam_ba_svm", "CV plant A", "modeb", "sec", "92.9"),
                          ("afrasiabi", "CV plant A", "modeb", "dep", "87.3")]:
    if s == "CV plant A":
        add(E, f"{m} {s} {md} {met} {qv}", lambda m=m, md=md, met=met: full_cv(m, md, 1 if met == "dep" else 0), f"full/{m}/cv_*.json")
    else:
        add(E, f"{m} {s} {md} {met} {qv}", lambda m=m, s=s, md=md, met=met: full_final(m, s, md, 1 if met == "dep" else 0), f"full/{m}/final_{s}.json")
add(E, "like-for-like neural security range '95.3-99.6 %' (CV) - lower end", lambda: min(full_cv(m, "modeb", 0) for m in ("afrasiabi", "key", "alhamd")), "full/{afrasiabi,key,alhamd}/cv_*.json")
add(E, "like-for-like neural security range '95.3-99.6 %' (CV) - upper end 99.6", lambda: max(full_cv(m, "modeb", 0) for m in ("afrasiabi", "key", "alhamd")), "full/*/cv_*.json")
for nm, qv in [("afrasiabi_cnn_per_decision", "116.7"), ("key_per_sample", "37.0"), ("ngaopitakkul_per_sample", "3.3"), ("simoes_per_sample_wavelet", "7.5"), ("alhamd_per_decision", "1,809"),
               ("abdusalam_features_per_decision", "608,796")]:
    add(E, f"latency {nm} median {qv} us", lambda nm=nm: lat(nm), "latency_baselines.txt")
add(E, "Simoes SVM1 per detection 498 us", lambda: lat("simoes_svm1_per_detection"), "latency_baselines.txt")
add(E, "Hajipour per sample 0.1 us", lambda: lat("afrasiabi_hajipour_per_sample_per_signal"), "latency_baselines.txt")
for meth, met, qv, pv in [("key", "dependability", "+4.04", "1.8e-15"), ("alhamd", "dependability", "+3.58", "2.1e-12"), ("afrasiabi", "dependability", "-6.24", "<1e-45"),
                          ("abdusalam_ba_svm", "dependability", "-16.57", "<1e-45"), ("simoes_grid", "dependability", "-23.27", "<1e-45"), ("ngaopitakkul", "dependability", "-65.24", "<1e-45"),
                          ("key", "security", "-23.67", "<1e-79"), ("alhamd", "security", "-16.04", "<1e-79"), ("afrasiabi", "security", "-10.32", "<1e-79"), ("simoes_grid", "security", "-6.75", "<1e-79"),
                          ("abdusalam_ba_svm", "security", "+1.00", "1.5e-14"), ("ngaopitakkul", "security", "+0.30", "0.126")]:
    add(E, f"D-N5 hybrid vs {meth} {met} {qv} pt", lambda meth=meth, met=met: t5("n5_statistics.json", "Proposed hybrid", meth, met, "diff_pt"), "n5_statistics.json")
    add(E, f"D-N5 hybrid vs {meth} {met} p_Holm {pv}", lambda meth=meth, met=met: t5("n5_statistics.json", "Proposed hybrid", meth, met, "p_holm"), "n5_statistics.json", kind="p")
add(E, "LSTM alone vs Key dep -0.67", lambda: t5("n5_statistics.json", "LSTM alone", "key", "dependability", "diff_pt"), "n5_statistics.json")
add(E, "LSTM alone vs Key dep p_Holm 0.126", lambda: t5("n5_statistics.json", "LSTM alone", "key", "dependability", "p_holm"), "n5_statistics.json", kind="p")
add(E, "LSTM alone vs Alhamd dep -1.13", lambda: t5("n5_statistics.json", "LSTM alone", "alhamd", "dependability", "diff_pt"), "n5_statistics.json")
add(E, "LSTM alone vs Alhamd dep p_Holm 5.4e-3", lambda: t5("n5_statistics.json", "LSTM alone", "alhamd", "dependability", "p_holm"), "n5_statistics.json", kind="p")
add(E, "'No per-seed sign changes' (count of unstable tests in N5 = 0)", lambda: sum(1 for t in J("n5_statistics.json")["tests"] if not t["sign_stable"]), "n5_statistics.json", kind="int0")
for meth, k, qv in [("afrasiabi", "sec_sd", "4.39"), ("key", "sec_sd", "8.62"), ("alhamd", "sec_sd", "4.36"), ("ngaopitakkul", "dep_sd", "3.39")]:
    add(E, f"fold-model sd {meth} {k} {qv}", lambda meth=meth, k=k: J("n5_statistics.json")["fold_sd"][meth][k], "n5_statistics.json")
add(E, "pairs 3,717 fault", lambda: t5("n5_statistics.json", "Proposed hybrid", "key", "dependability", "n"), "n5_statistics.json", kind="int")
add(E, "pairs 5,910 healthy", lambda: t5("n5_statistics.json", "Proposed hybrid", "key", "security", "n"), "n5_statistics.json", kind="int")
E = "11-03 09:10"
for meth, met, qv, pv in [("key", "dependability", "+4.28", "3.9e-24"), ("key", "security", "+0.61", "1.1e-3"), ("alhamd", "dependability", "+4.98", "6.1e-36"), ("alhamd", "security", "-0.78", "1.3e-3"),
                          ("afrasiabi", "dependability", "-5.68", "5.3e-47"), ("afrasiabi", "security", "+0.69", "5.5e-6"), ("abdusalam_ba_svm", "dependability", "-13.72", "<1e-6"),
                          ("abdusalam_ba_svm", "security", "-6.04", "<1e-6"), ("simoes_grid", "dependability", "-16.12", "<1e-6"), ("simoes_grid", "security", "-26.87", "<1e-6"),
                          ("ngaopitakkul", "dependability", "-54.56", "<1e-6"), ("ngaopitakkul", "security", "-1.47", "<1e-6")]:
    add(E, f"D-N5b hybrid vs {meth} like-for-like {met} {qv}", lambda meth=meth, met=met: t5("n5_statistics_modeb.json", "Proposed hybrid", meth, met, "diff_pt", "modeb"), "n5_statistics_modeb.json")
    add(E, f"D-N5b hybrid vs {meth} like-for-like {met} p_Holm48 {pv}", lambda meth=meth, met=met: t5("n5_statistics_modeb.json", "Proposed hybrid", meth, met, "p_holm", "modeb"), "n5_statistics_modeb.json", kind="p")
for meth, met, qv, pv in [("key", "dependability", "-0.43", "0.31"), ("key", "security", "+3.99", "2.3e-49"), ("alhamd", "dependability", "+0.27", "0.36"), ("alhamd", "security", "+2.61", "3.6e-19"),
                          ("afrasiabi", "dependability", "-10.38", None), ("afrasiabi", "security", "+4.08", None)]:
    add(E, f"D-N5b LSTM alone vs {meth} like-for-like {met} {qv}", lambda meth=meth, met=met: t5("n5_statistics_modeb.json", "LSTM alone", meth, met, "diff_pt", "modeb"), "n5_statistics_modeb.json")
    if pv:
        add(E, f"D-N5b LSTM alone vs {meth} like-for-like {met} p_Holm48 {pv}", lambda meth=meth, met=met: t5("n5_statistics_modeb.json", "LSTM alone", meth, met, "p_holm", "modeb"), "n5_statistics_modeb.json", kind="p")
add(E, "native LSTM alone vs Key dep p_Holm 0.126 -> 0.252", lambda: t5("n5_statistics_modeb.json", "LSTM alone", "key", "dependability", "p_holm", "native"), "n5_statistics_modeb.json", kind="p")
pb = lambda pat: float(re.search(pat, pbpath()).group(1))  # noqa: E731
add(E, "D-diag false trips 89", lambda: pb(r"false trips (\d+) of"), "plantB_falsetrip_paths.txt", kind="int")
add(E, "D-diag healthy 764", lambda: pb(r"of (\d+) detectable"), "plantB_falsetrip_paths.txt", kind="int")
add(E, "D-diag solo 87", lambda: pb(r"solo (\d+) \("), "plantB_falsetrip_paths.txt", kind="int")
add(E, "D-diag 97.8 %", lambda: pb(r"solo \d+ \(([\d.]+) %"), "plantB_falsetrip_paths.txt")
add(E, "D-diag gate 2", lambda: pb(r"gate (\d+) \("), "plantB_falsetrip_paths.txt", kind="int")
add(E, "D-diag CTSat 62", lambda: pb(r"Stress_ExtCTSat (\d+)"), "plantB_falsetrip_paths.txt", kind="int")
add(E, "D-diag External 23", lambda: pb(r"External (\d+)"), "plantB_falsetrip_paths.txt", kind="int")
add(E, "D-diag ExtInInrush 4", lambda: pb(r"Stress_ExtInInrush (\d+)"), "plantB_falsetrip_paths.txt", kind="int")
add(E, "D-diag solo off security 99.21", lambda: pb(r"off -> .*?\"security_pct\": ([\d.]+)"), "plantB_falsetrip_paths.txt")
add(E, "D-diag solo off dependability 90.47", lambda: pb(r"off -> .*?\"dependability_pct\": ([\d.]+)"), "plantB_falsetrip_paths.txt")
add(E, "D-diag only-solo faults 11 of 493", lambda: pb(r"AI-alone path: (\d+) of"), "plantB_falsetrip_paths.txt", kind="int")
E = "11-03 09:42"
for mdl, qv in [("Wavelet-SVM", "10"), ("Wavelet-RF", "11"), ("Wavelet-ANN", "11"), ("1D-CNN", "10"), ("Wavelet-GRU", "11"), ("Proposed LSTM", "10")]:
    add(E, f"B2 unique configs {mdl} {qv}", lambda mdl=mdl: J("b2_equal_search/unique_configs.json")[mdl]["unique"], "b2_equal_search/unique_configs.json", kind="int")
for path, qv in [(("dependability", "deployed_pct"), "92.95"), (("dependability", "gated_only_pct"), "88.43"), (("dependability", "diff_pt"), "-4.52"), (("dependability", "deployed_only_correct"), "168"),
                 (("security", "gated_only_pct"), "99.42"), (("security", "diff_pt"), "+0.47"), (("security", "gated_only_correct"), "28")]:
    add(E, f"gated-only {'/'.join(path)} {qv}", lambda path=path: gj(*path), "gated_only_ablation.json", kind="int" if "correct" in path[1] else "num")
add(E, "gated-only dep p = 5e-51", lambda: gj("dependability", "p"), "gated_only_ablation.json", kind="p")
add(E, "gated-only sec p = 7e-9", lambda: gj("security", "p"), "gated_only_ablation.json", kind="p")
ga = (BF / "gated_only_ablation.txt").read_text()
add(E, "OOD deployed 97.99", lambda: float(re.search(r"AI-alone path: \{\"dependability_pct\": ([\d.]+)", ga).group(1)), "gated_only_ablation.txt")
add(E, "OOD deployed 96.00", lambda: float(re.search(r"AI-alone path: \{.*?\"security_pct\": ([\d.]+)", ga).group(1)), "gated_only_ablation.txt")
add(E, "OOD gated-only 94.63", lambda: float(re.search(r"87T gate\): \{\"dependability_pct\": ([\d.]+)", ga).group(1)), "gated_only_ablation.txt")
add(E, "OOD gated-only 98.67", lambda: float(re.search(r"87T gate\): \{.*?\"security_pct\": ([\d.]+)", ga).group(1)), "gated_only_ablation.txt")
add(E, "'OOD 3.4 pt'", lambda: float(re.search(r"AI-alone path: \{\"dependability_pct\": ([\d.]+)", ga).group(1)) - float(re.search(r"87T gate\): \{\"dependability_pct\": ([\d.]+)", ga).group(1)), "gated_only_ablation.txt")
E = "11-03 13:47"
for met, fld, qv in [("dependability", "key_hybrid_pct", "94.11"), ("security", "key_hybrid_pct", "99.86"), ("dependability", "diff_pt", "+1.16"), ("security", "diff_pt", "+0.91"),
                     ("dependability", "hybrid_only_correct", "68"), ("dependability", "keyhybrid_only_correct", "111"), ("security", "hybrid_only_correct", "8"), ("security", "keyhybrid_only_correct", "62")]:
    add(E, f"Key hybrid {met} {fld} {qv}", lambda met=met, fld=fld: kh(met, fld), "n5_statistics_keyhybrid.json", kind="int" if "only" in fld else "num")
add(E, "Key hybrid dep p = 1.6e-3", lambda: kh("dependability", "p"), "n5_statistics_keyhybrid.json", kind="p")
add(E, "Key hybrid dep p_Holm50 = 9.7e-3", lambda: kh("dependability", "p_holm50"), "n5_statistics_keyhybrid.json", kind="p")
add(E, "Key hybrid sec p_Holm50 = 2.4e-10", lambda: kh("security", "p_holm50"), "n5_statistics_keyhybrid.json", kind="p")
for i, qv in enumerate(["-0.16", "0.00", "+3.63"]):
    add(E, f"Key hybrid dep per-seed {qv}", lambda i=i: list(kh("dependability", "per_seed_diff_pt").values())[i], "n5_statistics_keyhybrid.json")
for i, qv in enumerate(["+0.66", "+1.12", "+0.96"]):
    add(E, f"Key hybrid sec per-seed {qv}", lambda i=i: list(kh("security", "per_seed_diff_pt").values())[i], "n5_statistics_keyhybrid.json")
add(E, "Key hybrid AI thresholds range 0.15-0.7 (min)", lambda: min(keyhyb_thr("thr")), "full/key_hybrid/cv_*.json")
add(E, "Key hybrid AI thresholds range 0.15-0.7 (max)", lambda: max(keyhyb_thr("thr")), "full/key_hybrid/cv_*.json")
add(E, "Key hybrid solo thresholds 0.9-0.95 (min)", lambda: min(keyhyb_thr("solo")), "full/key_hybrid/cv_*.json")
add(E, "Key hybrid solo thresholds 0.9-0.95 (max)", lambda: max(keyhyb_thr("solo")), "full/key_hybrid/cv_*.json")
add(E, "Key hybrid OOD 97.97", lambda: full_final("key_hybrid", "plantA_OOD", "hybrid", 1), "full/key_hybrid/final_plantA_OOD.json")
add(E, "Key hybrid OOD 95.30", lambda: full_final("key_hybrid", "plantA_OOD", "hybrid", 0), "full/key_hybrid/final_plantA_OOD.json")
add(E, "Key hybrid plant B 95.50", lambda: full_final("key_hybrid", "plantB_main", "hybrid", 1), "full/key_hybrid/final_plantB_main.json")
add(E, "Key hybrid plant B 99.87", lambda: full_final("key_hybrid", "plantB_main", "hybrid", 0), "full/key_hybrid/final_plantB_main.json")
for mdl, b, w in [("Wavelet-SVM", "0.99300", "0.97045"), ("Wavelet-RF", "0.99870", "0.99607"), ("Wavelet-ANN", "0.99897", "0.99786"), ("1D-CNN", "0.99925", "0.99806"), ("Wavelet-GRU", "0.99888", "0.99766"), ("Proposed LSTM", "0.99899", "0.99691")]:
    add(E, f"B2 search {mdl} best AUC {b}", lambda mdl=mdl: auc_range(mdl)[0], "b2_equal_search/search_results.json")
    add(E, f"B2 search {mdl} worst AUC {w}", lambda mdl=mdl: auc_range(mdl)[1], "b2_equal_search/search_results.json")
add(E, "chosen LSTM hidden 128", lambda: J("b2_equal_search/chosen_configs.json")["Proposed LSTM"]["hidden"], "b2_equal_search/chosen_configs.json", kind="int")
E = "11-03 17:53"
for mdl, sa, hy in [("Wavelet-SVM", "90.93 / 90.41", "87.01 / 97.73"), ("Wavelet-RF", "97.07 / 95.45", "93.49 / 99.49"), ("Wavelet-ANN", "97.69 / 97.14", "94.92 / 99.20"),
                    ("1D-CNN", "97.96 / 97.28", "95.75 / 99.02"), ("Wavelet-GRU", "98.01 / 97.28", "95.59 / 98.82"), ("Proposed LSTM", "98.44 / 97.26", "93.60 / 99.10")]:
    for md, v in (("standalone", sa), ("hybrid", hy)):
        d, s_ = v.split(" / ")
        add(E, f"Table B {mdl} {md} dep {d}", lambda mdl=mdl, md=md: b2tab(mdl, md, 1), "b2_equal_search/final_*.json")
        add(E, f"Table B {mdl} {md} sec {s_}", lambda mdl=mdl, md=md: b2tab(mdl, md, 0), "b2_equal_search/final_*.json")
add(E, "deployed LSTM standalone 97.66", lambda: ref_pct("LSTM alone", 1), "runs/20261029_v5_cv5_seeds/*/result.json")
add(E, "deployed LSTM standalone 95.57", lambda: ref_pct("LSTM alone", 0), "runs/20261029_v5_cv5_seeds/*/result.json")
add(E, "deployed hybrid 92.95", lambda: ref_pct("Hybrid + AI-alone path", 1), "runs/20261029_v5_cv5_seeds/*/result.json")
add(E, "deployed hybrid 98.95", lambda: ref_pct("Hybrid + AI-alone path", 0), "runs/20261029_v5_cv5_seeds/*/result.json")
TL, TD = "tuned LSTM hybrid vs deployed hybrid (reference = deployed)", "hybrid vs deployed hybrid (reference = deployed)"
for test, met, fld, qv in [(TL, "dependability", "diff_pt", "+0.65"), (TL, "security", "diff_pt", "+0.15"), (TL, "dependability", "p_holm", "0.79"), (TL, "security", "p_holm", "1.0"),
                           ("1D-CNN " + TD, "dependability", "diff_pt", "+2.80"), ("1D-CNN " + TD, "dependability", "p_holm", "1.3e-17"), ("1D-CNN " + TD, "security", "diff_pt", "+0.07"),
                           ("Wavelet-GRU " + TD, "dependability", "diff_pt", "+2.64"), ("Wavelet-GRU " + TD, "dependability", "p_holm", "5.4e-15"), ("Wavelet-GRU " + TD, "security", "diff_pt", "-0.14"),
                           ("Wavelet-ANN " + TD, "dependability", "diff_pt", "+1.96"), ("Wavelet-ANN " + TD, "dependability", "p_holm", "3.4e-8"), ("Wavelet-ANN " + TD, "security", "diff_pt", "+0.25"),
                           ("Wavelet-RF " + TD, "dependability", "diff_pt", "+0.54"), ("Wavelet-RF " + TD, "security", "diff_pt", "+0.54"), ("Wavelet-RF " + TD, "security", "p_holm", "4.5e-3"),
                           ("Wavelet-SVM " + TD, "dependability", "diff_pt", "-5.95"), ("Wavelet-SVM " + TD, "security", "diff_pt", "-1.22")]:
    add(E, f"B2 stats {test[:40]} {met} {fld} {qv}", lambda test=test, met=met, fld=fld: b2t(test, met, fld), "b2_equal_search/b2_summary.json", kind="p" if fld == "p_holm" else "num")
add(E, "Holm over all 22", lambda: len(J("b2_equal_search/b2_summary.json")), "b2_equal_search/b2_summary.json", kind="int")
E = "11-03 23:41"
la = (BF / "latency_alhamd_trained.txt").read_text()
add(E, "Alhamd fold-1 config median 1,166 us", lambda: float(re.search(r"seed20261021_fold1.*?median (\d+) us", la).group(1)), "latency_alhamd_trained.txt", kind="int")
add(E, "Alhamd fold-1 p99 1,747 us", lambda: float(re.search(r"seed20261021_fold1.*?p99 (\d+) us", la).group(1)), "latency_alhamd_trained.txt", kind="int")
add(E, "Alhamd final median 1,169 us", lambda: float(re.search(r"final_model.*?median (\d+) us", la).group(1)), "latency_alhamd_trained.txt", kind="int")
add(E, "Alhamd final p99 1,674 us", lambda: float(re.search(r"final_model.*?p99 (\d+) us", la).group(1)), "latency_alhamd_trained.txt", kind="int")
add(E, "Alhamd largest 1,799 us", lambda: float(re.search(r"largest.*?median (\d+) us", la).group(1)), "latency_alhamd_trained.txt", kind="int")
add(E, "N6c chosen 0.2/0.2/0.25 in 9 folds", lambda: sum(1 for c in J("n6c_tuned_harmonic.json")["chosen"] if c["setting"] == [0.2, 0.2, 0.25]), "n6c_tuned_harmonic.json", kind="int")
add(E, "N6c chosen 0.2/0.15/0.25 in 6 folds", lambda: sum(1 for c in J("n6c_tuned_harmonic.json")["chosen"] if c["setting"] == [0.2, 0.15, 0.25]), "n6c_tuned_harmonic.json", kind="int")
for st, met, fld, qv in [("textbook 0.30/0.15/0.35", "dependability", "harmonic", "85.96"), ("textbook 0.30/0.15/0.35", "security", "harmonic", "99.39"),
                         ("tuned on validation", "dependability", "harmonic", "91.18"), ("tuned on validation", "security", "harmonic", "99.07"),
                         ("tuned on validation", "dependability", "diff_pt", "-1.78"), ("tuned on validation", "dependability", "hybrid_only", "138"), ("tuned on validation", "dependability", "harmonic_only", "72"),
                         ("tuned on validation", "dependability", "p_holm4", "1.9e-5"), ("tuned on validation", "security", "diff_pt", "+0.12"), ("tuned on validation", "security", "hybrid_only", "47"),
                         ("tuned on validation", "security", "harmonic_only", "54"), ("tuned on validation", "security", "p_holm4", "0.55"), ("textbook 0.30/0.15/0.35", "dependability", "diff_pt", "-6.99"),
                         ("textbook 0.30/0.15/0.35", "security", "diff_pt", "+0.44"), ("textbook 0.30/0.15/0.35", "dependability", "p_holm4", "5.8e-69"), ("textbook 0.30/0.15/0.35", "security", "p_holm4", "1.2e-2")]:
    add(E, f"N6c {st[:8]} {met} {fld} {qv}", lambda st=st, met=met, fld=fld: n6(st, met, fld), "n6c_tuned_harmonic.json", kind="p" if "holm" in fld else ("int" if "only" in fld else "num"))
for i, qv in enumerate(["-2.66", "-2.82", "+0.16"]):
    add(E, f"N6c tuned dep per-seed {qv}", lambda i=i: list(n6("tuned on validation", "dependability", "per_seed").values())[i], "n6c_tuned_harmonic.json")
add(E, "N6c 'reproduces the earlier 85.93 / 99.40' (dep)", lambda: float(re.search(r"Harmonic 87T per-phase\s+([\d.]+)", (ROOT / "runs/20261101_v5_common_set/summary.txt").read_text()).group(1)), "runs/20261101_v5_common_set/summary.txt")
add(E, "H6c 'gain from tuning +5.2 pt'", lambda: n6("tuned on validation", "dependability", "harmonic") - n6("textbook 0.30/0.15/0.35", "dependability", "harmonic"), "n6c_tuned_harmonic.json")
n6t = (BF / "n6c_tuned_harmonic.txt").read_text()
add(E, "Internal_HiZ n = 459", lambda: float(re.search(r"Internal_HiZ \(n=(\d+)\)", n6t).group(1)), "n6c_tuned_harmonic.txt", kind="int")
add(E, "HiZ hybrid 65.4", lambda: float(re.search(r"Internal_HiZ \(n=\d+\): hybrid ([\d.]+)", n6t).group(1)), "n6c_tuned_harmonic.txt")
add(E, "HiZ tuned 62.1", lambda: float(re.search(r"Internal_HiZ .*?tuned harmonic ([\d.]+)", n6t).group(1)), "n6c_tuned_harmonic.txt")
add(E, "HiZ textbook 51.0", lambda: float(re.search(r"Internal_HiZ .*?textbook harmonic ([\d.]+)", n6t).group(1)), "n6c_tuned_harmonic.txt")
add(E, "other internal n = 3,258", lambda: float(re.search(r"other internal faults \(n=(\d+)\)", n6t).group(1)), "n6c_tuned_harmonic.txt", kind="int")
add(E, "other hybrid 96.8 / tuned 95.3 / textbook 90.9 (hybrid)", lambda: float(re.search(r"other internal faults \(n=\d+\): hybrid ([\d.]+)", n6t).group(1)), "n6c_tuned_harmonic.txt")
E = "11-04 00:08"
for inst, qv, pv in [("1D-CNN", "+4.57", "3.0e-37"), ("Wavelet-GRU", "+4.41", "3.3e-31"), ("Wavelet-ANN", "+3.74", "2.4e-27"), ("Key (claim-C run)", "+2.93", "1.0e-18"), ("LSTM (tuned, B2)", "+2.42", "1.3e-7"), ("Wavelet-RF", "+2.31", "4.3e-13")]:
    add(E, f"N8a {inst} dep {qv}", lambda inst=inst: n8(inst, "dependability", "diff_pt"), "n8a_instances_vs_tuned_harmonic.json")
    add(E, f"N8a {inst} dep p_Holm16 {pv}", lambda inst=inst: n8(inst, "dependability", "p_holm16"), "n8a_instances_vs_tuned_harmonic.json", kind="p")
for inst, qv in [("Key (claim-C run)", "+0.80"), ("Wavelet-RF", "+0.42"), ("1D-CNN", "-0.05"), ("Wavelet-GRU", "-0.25"), ("Wavelet-ANN", "+0.14"), ("LSTM (tuned, B2)", "+0.03")]:
    add(E, f"N8a {inst} sec {qv}", lambda inst=inst: n8(inst, "security", "diff_pt"), "n8a_instances_vs_tuned_harmonic.json")


def quoted_number(q):
    m = re.findall(r"[<]?[+-]?\d[\d,]*\.?\d*(?:e-?\d+)?", q.split(" ")[-1] if not q.endswith("'") else q)
    return m[-1] if m else None


def check(quoted, v, kind):
    if isinstance(v, str):
        return "ERROR", v
    nums = re.findall(r"<?[+-]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?", quoted.replace("'", ""))
    tok = (nums[-1] if nums else "nan").replace(",", "") if kind != "int0" else "0"
    if "range" in quoted and "lower end" in quoted:
        tok = "95.3"
    if "range" in quoted and "upper end" in quoted:
        tok = "99.6"
    if "per-seed" in quoted or "pt'" in quoted:
        pass
    if "'OOD 3.4 pt'" in quoted:
        tok = "3.4"
    if "+5.2 pt" in quoted:
        tok = "5.2"
    if "0.15-0.7 (min)" in quoted:
        tok = "0.15"
    if "0.15-0.7 (max)" in quoted:
        tok = "0.7"
    if "0.9-0.95 (min)" in quoted:
        tok = "0.9"
    if "0.9-0.95 (max)" in quoted:
        tok = "0.95"
    if "1,289" in quoted:
        tok = "1278"
    if "297 of 300" in quoted:
        tok = "297"
    if "13 of 15" in quoted:
        tok = nums[0]
    if "reproduces" in quoted:
        tok = "85.93"
    if "(hybrid)" in quoted:
        tok = "96.8"
    if "11 of 493" in quoted:
        tok = "11"
    if "0.126 -> 0.252" in quoted:
        tok = "0.252"
    if "in 9 folds" in quoted:
        tok = "9"
    if "in 6 folds" in quoted:
        tok = "6"
    if "n = 459" in quoted:
        tok = "459"
    if "3,258" in quoted:
        tok = "3258"
    if "hidden 128" in quoted:
        tok = "128"
    if "over all 22" in quoted:
        tok = "22"
    if kind == "p":
        if tok.startswith("<"):
            return ("Y" if v < float(tok[1:]) else "N"), f"{v:.3e}"
        q = float(tok)
        # quoted to 1-2 significant digits: accept rounding of the mantissa
        if q == 0:
            return ("Y" if v == 0 else "N"), f"{v:.3e}"
        sig = len(re.sub(r"[^0-9]", "", tok.split("e")[0]).lstrip("0")) or 1
        ok = float(f"{v:.{max(sig - 1, 0)}e}") == float(f"{q:.{max(sig - 1, 0)}e}") or abs(v - q) / q < 0.051
        return ("Y" if ok else "N"), f"{v:.3e}"
    if kind in ("int", "int0"):
        return ("Y" if int(round(v)) == int(float(tok)) else "N"), f"{v}"
    q = float(tok)
    nd = len(tok.split(".")[1]) if "." in tok else 0
    ok = round(v, nd) == round(q, nd) or abs(round(v, nd) - q) < 10 ** (-nd) * 0.51
    return ("Y" if ok else "N"), f"{v:.4f}"


rows, L = [], []
for entry, quoted, v, kind, f in C:
    ok, shown = check(quoted, v, kind)
    rows.append({"log entry": f"2026-{entry}", "claim (quoted from the log)": quoted, "file": f, "recomputed": shown, "match": ok})
with open(OUT / "log_claims.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
n_n = [r for r in rows if r["match"] != "Y"]
L.append(f"{len(rows)} claims checked; {len(rows) - len(n_n)} match; {len(n_n)} do not match or error")
for r in n_n:
    L.append(f"  NO: {r['log entry']} | {r['claim (quoted from the log)']} | {r['file']} | recomputed {r['recomputed']}")
(OUT / "log_claims.txt").write_text("\n".join(L))
print("\n".join(L))
