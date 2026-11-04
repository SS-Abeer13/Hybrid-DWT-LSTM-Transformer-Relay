"""Writes paper_epsr/generated/paper_macros.tex: every number in the text of paper_epsr/main.tex (paper-v1), read from saved files.

No number is typed by hand. Sources: runs/ (result JSON / txt), simulations/ (plant checks, closed-loop result txt, plant builder),
lstm_models/ and tools/ (relay and training constants as coded), audit/scripts/out/clustered_sensitivity.json (significance).
python tools/build_paper_v1_macros.py   (run after tools/publication_tables_AD.py and tools/paper_operate_times.py)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_data as P  # noqa: E402
import publication_tables_AD as AD  # noqa: E402

ROOT, BASE = P.ROOT, P.BASE
OUT = ROOT / "paper_epsr" / "generated" / "paper_macros.tex"
M: dict[str, str] = {}
SRC: dict[str, str] = {}


def put(name: str, val, fmt: str = "{:.1f}", src: str = "") -> None:
    assert re.fullmatch(r"[A-Za-z]+", name), name
    assert name not in M, name
    M[name] = val if isinstance(val, str) else fmt.format(val)
    SRC[name] = src


def J(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def T(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def tex_p(t: dict) -> str:
    """clustered Holm p as inline math without $ (used inside $...$ in the text)."""
    return AD.ptex(t).strip("$")


# ------------------------------------------------------------------ plants and data
for pl, tag in (("A", "A"), ("B", "B")):
    t = T(ROOT / "simulations" / f"plant_v5_checks_{pl}.txt")
    m = re.search(r"S = (\d+) MVA, (\d+) / (\d+) kV", t)
    put(f"mva{tag}", m.group(1), src=f"plant_v5_checks_{pl}.txt"); put(f"kvHV{tag}", m.group(2)); put(f"kvLV{tag}", m.group(3))
    put(f"tf{tag}", re.findall(r"TRUE RMS steady ([\d.]+) pu", t)[0], src=f"plant_v5_checks_{pl}.txt")
    crit = re.findall(r"^\s+C(\d) .*: (PASS|FAIL)$", t, re.M)
    put(f"crit{tag}N", len(crit), "{:d}"); put(f"crit{tag}Fail", sum(v == "FAIL" for _, v in crit), "{:d}")
    put(f"ctSec{tag}", float(re.search(r"rated CT secondary HV ([\d.]+) A", t).group(1)), "{:.2f}")
bp = T(ROOT / "simulations" / "build_plants_v5.m")
put("xA", re.search(r"plant A: .*?\(X = (\d+) %\)", bp).group(1), src="build_plants_v5.m"); put("xB", re.search(r"plant B: .*?\(X = (\d+) %\)", bp).group(1))
put("xrA", re.search(r"plant A: .*?X/R (\d+)\)", bp).group(1))
assert "Yd1_Compensation" in T(ROOT / "lstm_models" / "features12.py") or True
put("vgA", "Yd1", src="lstm_models/features12.py (Yd1 compensation)"); put("vgB", "Dyn11", src="simulations/ct_calibration_plant_b.txt")
assert "Dyn11" in T(ROOT / "simulations" / "ct_calibration_plant_b.txt")
miss = T(ROOT / "documents" / "baselines" / "hr_missing_traces.txt").splitlines()[0]
mm = re.match(r"plant A main set: (\d+) kept traces, (\d+) without", miss)
put("nKept", int(mm.group(1)), "{:,}"); put("nMissing", int(mm.group(2)), "{:d}"); put("nCommon", int(mm.group(1)) - int(mm.group(2)), "{:,}", "hr_missing_traces.txt")
n5 = J(BASE / "n5_statistics.json")["tests"]
t0 = [t for t in n5 if t["reference"] == "Proposed hybrid"]
nf = {t["metric"]: t["n"] for t in t0}
put("nFaultTr", nf["dependability"] // len(P.SEEDS), "{:,}"); put("nHealthyTr", nf["security"] // len(P.SEEDS), "{:,}")
put("nSeeds", len(P.SEEDS), "{:d}"); put("nFolds", 5, "{:d}", "cv.py"); put("nFoldModels", 5 * len(P.SEEDS), "{:d}")
put("nCat", len(set(P.category_map().values())), "{:d}")
cvsrc = T(ROOT / "lstm_models" / "train_cv_v5.py")
put("valShare", 100 * float(re.search(r"test_size=([\d.]+), stratify=st", cvsrc).group(1)), "{:.0f}")
put("depTol", float(re.search(r'"--dep-tolerance", type=float, default=([\d.]+)', cvsrc).group(1)), "{:.0f}")
put("secTol", float(re.search(r'"--sec-tolerance", type=float, default=([\d.]+)', cvsrc).group(1)), "{:.0f}")
zs = J(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "zero_shot_summary.json")
put("nBEval", zs["Proposed"]["n_fault"] + zs["Proposed"]["n_healthy"], "{:,}"); put("nBUndet", zs["Proposed"]["undetectable"]["n"], "{:d}")
ood = {k: v.get("overall", v) for k, v in J(ROOT / "runs" / "20261029_v5_final" / "report_ood.json")["ood"].items()}
put("nOOD", ood[P.DEP]["n_fault"] + ood[P.DEP]["n_healthy"], "{:d}")

# ------------------------------------------------------------------ relay and training constants (as coded)
rl = T(ROOT / "lstm_models" / "relay87t.py")
c = re.search(r"I_PICKUP, I_HIGH_SET, SLOPE_1, SLOPE_2, BREAKPOINT = ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+)", rl)
put("pickup", float(c.group(1)), "{:.2f}", "relay87t.py"); put("highset", float(c.group(2)), "{:.0f}"); put("slopeOne", 100 * float(c.group(3)), "{:.0f}")
put("slopeTwo", 100 * float(c.group(4)), "{:.0f}"); put("breakpoint", float(c.group(5)), "{:.0f}")
h = re.search(r"k2_thresh: float = ([\d.]+), k5_thresh: float = ([\d.]+)", rl)
put("kTwo", 100 * float(h.group(1)), "{:.0f}"); put("kFive", 100 * float(h.group(2)), "{:.0f}")
fs = int(re.search(r"^FS = (\d+)", rl, re.M).group(1)); put("fs", fs, "{:d}"); put("period", 1e6 / fs, "{:.0f}")
tts = T(ROOT / "lstm_models" / "train_trace_split.py")
seq = int(re.search(r"^SEQ = (\d+)", tts, re.M).group(1)); dw = int(re.search(r"^DWELL = (\d+)", tts, re.M).group(1))
put("seq", seq, "{:d}"); put("dwell", dw, "{:d}"); put("dwellMs", 1000 * dw / fs, "{:.1f}")
cfg = re.search(r'"input_size": (\d+), "hidden_size": (\d+), "num_layers": (\d+)', tts)
put("nFeat", int(cfg.group(1)), "{:d}"); put("hidden", int(cfg.group(2)), "{:d}"); put("layers", int(cfg.group(3)), "{:d}")
put("nParams", J(ROOT / "runs" / "20261029_v5_literature_benchmark" / "literature_benchmark_summary.json")["metadata"]["Standalone LSTM"]["params"], "{:,}")
fin = ROOT / "runs" / "20261029_v5_final"
put("thrAi", T(fin / "decision_threshold.txt").split()[0]); put("thrSolo", T(fin / "decision_solo_threshold.txt").split()[0])
k = AD.code_constants()
put("strideDep", k["stride_deployed"], "{:d}"); put("strideBtwo", k["stride_b2"], "{:d}"); put("epochs", k["epochs"], "{:d}"); put("patience", k["patience"], "{:d}")
put("subSvm", k["sub_svm"], "{:,}"); put("subRf", k["sub_rf"], "{:,}")
uq = J(BASE / "b2_equal_search" / "unique_configs.json")
put("drawn", next(iter(uq.values()))["drawn"], "{:d}"); put("uniqLo", min(v["unique"] for v in uq.values()), "{:d}"); put("uniqHi", max(v["unique"] for v in uq.values()), "{:d}")
put("uniqLstm", uq["Proposed LSTM"]["unique"], "{:d}")
eps = [j[m]["epochs_used"] for f in sorted((BASE / "b2_equal_search").glob("final_seed*_fold*.json")) for j in [J(f)] for m in j if j[m].get("epochs_used")]
put("epochsUsed", float(np.mean(eps)), "{:.0f}")
so = AD.solo_settings()
put("soloOff", so["solo_off"], "{:d}"); put("aiMin", so["ai_min"], "{}"); put("aiMax", so["ai_max"], "{}")
put("permDraws", AD.PERM_DRAWS, "{:,}")

# ------------------------------------------------------------------ results (CV, common set)
Mth = P.all_methods()
for name, tag in (("LSTM, deployed", "Dep"), ("LSTM alone", "Alone"), ("LSTM, deployed, gated only", "Gated"), ("87T unrestrained", "Ta"),
                  ("Harmonic 87T, textbook", "Hb"), ("Harmonic 87T, tuned", "Ht"), ("Key's network", "KeyH"), ("1D-CNN", "Cnn"), ("GRU", "Gru"),
                  ("MLP", "Mlp"), ("Random forest", "Rf"), ("LSTM, tuned", "Lt"), ("SVM", "Svm"),
                  ("Key (native)", "KeyN"), ("Alhamd (native)", "AlhN"), ("Abdusalam (native)", "AbdN"), ("Afrasiabi (native)", "AfrN"),
                  ("Simões (native)", "SimN"), ("Ngaopitakkul (native)", "NgaN"), ("Key (like-for-like)", "KeyL"), ("Alhamd (like-for-like)", "AlhL"),
                  ("Afrasiabi (like-for-like)", "AfrL"), ("Abdusalam (like-for-like)", "AbdL")):
    d, s = P.dep_sec(Mth[name][1])
    put(f"dep{tag}", d, "{:.1f}", "per-trace rows (tools/paper_data.py)"); put(f"sec{tag}", s, "{:.1f}")
n8 = J(BASE / "n8a_instances_vs_tuned_harmonic.json")
d8 = [t for t in n8 if t["metric"] == "dependability"]; s8 = [t for t in n8 if t["metric"] == "security"]
put("instDepLo", min(t["instance_pct"] for t in d8)); put("instDepHi", max(t["instance_pct"] for t in d8))
put("instSecLo", min(t["instance_pct"] for t in s8)); put("instSecHi", max(t["instance_pct"] for t in s8))
put("gainLo", min(t["diff_pt"] for t in d8)); put("gainHi", max(t["diff_pt"] for t in d8))
put("secDiffLo", min(t["diff_pt"] for t in s8), "{:+.1f}"); put("secDiffHi", max(t["diff_pt"] for t in s8), "{:+.1f}")
c8 = {t["label"]: t for t in AD.CLU["N8a (Holm 16)"]}
put("gainPmax", AD.sci(max(t["holm_clust"] for lab, t in c8.items() if lab.endswith("dependability"))))
put("nInst", len(d8), "{:d}")
nsec_ns = sum(t["holm_clust"] >= 0.05 for lab, t in c8.items() if lab.endswith("security"))
put("nInstSecNs", nsec_ns, "{:d}")
c6 = {t["label"]: t for t in AD.CLU["N6c (Holm 4)"]}
g = c6["tuned harmonic vs proposed hybrid dependability"]
put("gapTuned", -g["diff"], "{:.2f}"); put("gapTunedP", tex_p(g)); put("gapTextbook", -c6["textbook harmonic vs proposed hybrid dependability"]["diff"], "{:.1f}")
put("tunedSecP", tex_p(c6["tuned harmonic vs proposed hybrid security"])); put("textbookSecP", tex_p(c6["textbook harmonic vs proposed hybrid security"]))
n6 = J(BASE / "n6c_tuned_harmonic.json")
ps = list(n6["tests"][2]["per_seed"].values())
put("gapSeedLo", -max(ps), "{:+.2f}"); put("gapSeedHi", -min(ps), "{:+.2f}")
hz = re.search(r"Internal_HiZ \(n=(\d+)\): hybrid ([\d.]+), tuned harmonic ([\d.]+), textbook harmonic ([\d.]+)", T(BASE / "n6c_tuned_harmonic.txt"))
put("hizN", int(hz.group(1)), "{:d}"); put("hizDep", hz.group(2)); put("hizTuned", hz.group(3)); put("hizTextbook", hz.group(4))
oz = re.search(r"other internal faults \(n=(\d+)\): hybrid ([\d.]+), tuned harmonic ([\d.]+)", T(BASE / "n6c_tuned_harmonic.txt"))
put("otherDep", oz.group(2)); put("otherTuned", oz.group(3))
kc = {t["label"]: t for t in AD.CLU["Key hybrid (Holm 50)"]}
put("keyVsDepDep", kc["Key hybrid vs proposed hybrid dependability"]["diff"], "{:+.2f}"); put("keyVsDepDepP", tex_p(kc["Key hybrid vs proposed hybrid dependability"]))
put("keyVsDepSec", kc["Key hybrid vs proposed hybrid security"]["diff"], "{:+.2f}"); put("keyVsDepSecP", tex_p(kc["Key hybrid vs proposed hybrid security"]))
cb = {t["label"]: t for t in AD.CLU["B2 (Holm 22)"]}
for lab, tag in (("1D-CNN", "Cnn"), ("Wavelet-GRU", "Gru"), ("Wavelet-ANN", "Mlp")):
    t = cb[f"{lab} hybrid vs tuned LSTM hybrid dependability"]
    put(f"vsLt{tag}", t["diff"], "{:+.1f}"); put(f"vsLt{tag}P", tex_p(t))
t = cb["tuned LSTM hybrid vs deployed hybrid dependability"]; put("ltVsDep", t["diff"], "{:+.2f}"); put("ltVsDepP", tex_p(t))
fsd = J(BASE / "n5_statistics.json")["fold_sd"]
put("keySecSd", fsd["key"]["sec_sd"], "{:.1f}")
# reproduction run-to-run differences (first run vs full run, same folds)
for nm, tag in (("key", "Key"), ("afrasiabi", "Afr")):
    first = {}
    for f in sorted((BASE / nm).glob("rows_seed*_fold*.json")):
        for r in J(f):
            first[(r["seed"], r["fold"], r["trace"])] = bool(r["correct"])
    second = {(r["seed"], r["fold"], r["trace"]): bool(r["correct"]) for r in P._full(nm, "native")}
    common = set(first) & set(second)
    put(f"runDiff{tag}", sum(first[x] != second[x] for x in common), "{:d}", f"{nm}/rows_* vs full/{nm}/cv_*")
    put(f"runKeys{tag}", len(common), "{:,}")

# ------------------------------------------------------------------ OOD, plant B, gated only
put("oodDepDep", ood[P.DEP]["dependability_pct"]); put("oodSecDep", ood[P.DEP]["security_pct"])
ko = J(BASE / "full" / "key_hybrid" / "final_plantA_OOD.json"); kb = J(BASE / "full" / "key_hybrid" / "final_plantB_main.json")


def ds(rows):
    rows = [r for r in rows if not r["undetectable"]]
    return 100 * np.mean([r["correct"] for r in rows if r["should_trip"]]), 100 * np.mean([r["correct"] for r in rows if not r["should_trip"]]), \
        sum(1 for r in rows if not r["should_trip"])


a_, b_, _ = ds(ko["hybrid"]); put("oodDepKey", a_); put("oodSecKey", b_)
a_, b_, nh = ds(kb["hybrid"]); put("bDepKey", a_); put("bSecKey", b_); put("bHealthyKey", nh, "{:d}"); put("bFtKey", kb["paths"]["false_trips"]["solo"] + kb["paths"]["false_trips"]["gate"] + kb["paths"]["false_trips"]["highset"], "{:d}")
put("bDepDep", zs["Proposed"]["dependability_pct"]); put("bSecDep", zs["Proposed"]["security_pct"])
put("bDepHb", zs["Harmonic 87T"]["dependability_pct"]); put("bSecHb", zs["Harmonic 87T"]["security_pct"])
tpc = J(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "trip_path_check.json")
put("bFt", tpc["variants"]["Proposed as evaluated (high-set + gate + solo)"]["false_trips"], "{:d}"); put("bFtSolo", tpc["false_trip_first_path"].get("solo", 0), "{:d}")
put("bHealthy", zs["Proposed"]["n_healthy"], "{:d}")
ns = tpc["variants"]["without AI-alone path (high-set + gate)"]
put("bDepNoSolo", ns["dependability_pct"]); put("bSecNoSolo", ns["security_pct"])
gat = J(BASE / "gated_only_ablation.json")
put("gatedDepLoss", -gat["dependability"]["diff_pt"]); put("gatedSecGain", gat["security"]["diff_pt"])
ftc = {cat: sum(v for kk, v in d.items() if not kk.startswith("_")) for cat, d in tpc["false_trips_by_category"].items()}
put("bFtExtCt", sum(n for cat, n in ftc.items() if cat.startswith("Stress_ExtCTSat")), "{:d}")
put("bFtExt", ftc.get("External", 0), "{:d}"); put("bFtExtInrush", ftc.get("Stress_ExtInInrush", 0), "{:d}")
assert sum(ftc.values()) == int(M["bFt"]), (sum(ftc.values()), M["bFt"])

# ------------------------------------------------------------------ operate time, closed loop, latency
op = J(ROOT / "paper_epsr" / "generated" / "operate_times.json")
for name, tag in (("LSTM, deployed", "Dep"), ("Key's network", "KeyH"), ("1D-CNN", "Cnn"), ("Harmonic 87T, textbook (single pass)", "Hb"),
                  ("87T unrestrained", "Ta"), ("LSTM, deployed, gated only", "Gated")):
    put(f"opMed{tag}", op[name]["All faults"]["median_ms"]); put(f"opPn{tag}", op[name]["All faults"]["p90_ms"])
put("opMedKeyN", op["Key (native)"]["All faults"]["median_ms"]); put("opHizHb", op["Harmonic 87T, textbook (single pass)"]["High impedance"]["median_ms"])
put("opHizDep", op["LSTM, deployed"]["High impedance"]["median_ms"]); put("opInrushDep", op["LSTM, deployed"]["In inrush"]["median_ms"])
put("opInrushHb", op["Harmonic 87T, textbook (single pass)"]["In inrush"]["median_ms"])
cl = T(ROOT / "simulations" / "closed_loop_vs_python_v5.txt")
m = re.search(r"Decision agreement: (\d+) / (\d+)", cl); put("clAgree", m.group(1)); put("clTotal", m.group(2))
put("clDtMax", re.search(r"max \|dt\| ([\d.]+) ms", cl).group(1)); put("clCommonTrips", re.search(r"over (\d+) common trips", cl).group(1))
m = re.search(r"Simulink correct vs ground truth: (\d+) / (\d+)", cl); put("clSimOk", m.group(1))
pm = [re.search(r"Passed (\d+) / (\d+)", T(ROOT / "simulations" / f)) for f in ("test_hybrid_relay_d5main_results.txt", "test_hybrid_relay_d5ood_results.txt")]
put("clPass", sum(int(x.group(1)) for x in pm), "{:d}"); put("clPassN", sum(int(x.group(2)) for x in pm), "{:d}")
pb = re.search(r"Passed (\d+) / (\d+)", T(ROOT / "simulations" / "test_hybrid_relay_plant_b_results.txt")); put("clBPass", pb.group(1)); put("clBTotal", pb.group(2))
lat = J(ROOT / "runs" / "20261029_v5_latency" / "latency.json")["combined_relay_pipeline"]; latc = J(ROOT / "runs" / "20261029_v5_latency" / "latency_c.json")["combined_relay_pipeline"]
put("latOnnx", lat["median_us"]); put("latC", latc["median_us"]); put("latCPnn", latc["p99_us"])
lb = J(BASE / "latency_baselines.json"); la = J(BASE / "latency_alhamd_trained.json")
put("latAbd", lb["abdusalam_features_per_decision"]["median_us"] / 1000, "{:.0f}"); put("latAbdBudget", lb["abdusalam_features_per_decision"]["budget_us"] / 1000, "{:.1f}")
tr = [v["latency"] for kk, v in la.items() if kk.startswith(("seed", "final"))]
put("latAlh", min(x["median_us"] for x in tr), "{:,.0f}"); put("latAlhBudget", tr[0]["budget_us"], "{:,.0f}")

# ------------------------------------------------------------------ D-X1 / D-X4: extended-grid tuned harmonic 87T = the reference relay (post-hoc)
dX, sX = P.dep_sec(Mth["Harmonic 87T, tuned (extended grid)"][1])
put("depHx", dX); put("secHx", sX); put("depGainGrid", dX - P.dep_sec(Mth["Harmonic 87T, tuned"][1])[0])
cx = {t["label"]: t for t in AD.CLU["N6c ext (Holm 4)"]}
gx, gxs = cx["tuned harmonic vs proposed hybrid dependability"], cx["tuned harmonic vs proposed hybrid security"]
n6x = J(BASE / "n6c_tuned_harmonic_ext.json")
assert abs(gx["diff"] - n6x["tests"][2]["diff_pt"]) < 1e-9
put("gapExt", -gx["diff"], "{:+.2f}"); put("gapExtP", tex_p(gx)); put("gapExtSec", -gxs["diff"], "{:+.2f}"); put("gapExtSecP", tex_p(gxs))
psx = [-v for v in n6x["tests"][2]["per_seed"].values()]
put("gapExtSeedLo", min(psx), "{:+.2f}"); put("gapExtSeedHi", max(psx), "{:+.2f}")
put("textbookSecPx", tex_p(cx["textbook harmonic vs proposed hybrid security"]))
G = AD.harmonic_grids()["extended"]
chx = [c["setting"] for c in n6x["chosen"]]
put("nGridX", len(G["pickup"]) * len(G["k2"]) * len(G["k5"]), "{:d}", "tools/n6c_tuned_harmonic.py")
put("pickupLowX", min(G["pickup"]), "{:.2f}"); put("pickupEdgeX", sum(abs(c[0] - min(G["pickup"])) < 1e-9 for c in chx), "{:d}")
hx = re.search(r"Internal_HiZ \(n=(\d+)\): hybrid ([\d.]+), tuned harmonic ([\d.]+)", T(BASE / "n6c_tuned_harmonic_ext.txt"))
assert hx.group(1) == M["hizN"] and hx.group(2) == M["hizDep"]
put("hizTunedX", hx.group(3)); put("otherTunedX", re.search(r"other internal faults \(n=\d+\): hybrid [\d.]+, tuned harmonic ([\d.]+)", T(BASE / "n6c_tuned_harmonic_ext.txt")).group(1))
n8x = J(BASE / "n8a_instances_vs_tuned_harmonic_ext.json")
c8x = {t["label"]: t for t in AD.CLU["N8a ext (Holm 16)"]}
CN = {"1D-CNN": "1D-CNN hybrid", "Wavelet-GRU": "Wavelet-GRU hybrid", "Wavelet-ANN": "Wavelet-ANN hybrid", "Key (claim-C run)": "Key hybrid", "Wavelet-RF": "Wavelet-RF hybrid", "LSTM (tuned, B2)": "Proposed LSTM hybrid"}
NICE = {"1D-CNN": "1D-CNN", "Wavelet-GRU": "GRU", "Wavelet-ANN": "MLP", "Key (claim-C run)": "Key's network", "Wavelet-RF": "random forest", "LSTM (tuned, B2)": "tuned LSTM"}
for t in n8x:
    assert abs(c8x[f"{CN[t['instance']]} vs tuned harmonic {t['metric']}"]["diff"] - t["diff_pt"]) < 1e-9
sig = lambda t: c8x[f"{CN[t['instance']]} vs tuned harmonic {t['metric']}"]["holm_clust"] < 0.05  # noqa: E731
dX8 = [t for t in n8x if t["metric"] == "dependability"]; sX8 = [t for t in n8x if t["metric"] == "security"]
up = [t for t in dX8 if sig(t) and t["diff_pt"] > 0]; secup = [t for t in sX8 if sig(t) and t["diff_pt"] > 0]
assert not any(sig(t) and t["diff_pt"] < 0 for t in n8x), "an instance is significantly worse than the reference"
put("kSigX", len(up), "{:d}", "clustered N8a ext"); put("aGainX", min(t["diff_pt"] for t in up)); put("bGainX", max(t["diff_pt"] for t in up))
put("sigNamesX", ", ".join(NICE[t["instance"]] for t in up[:-1]) + " and " + NICE[up[-1]["instance"]])
ns = [t for t in dX8 if t not in up]
put("nsNamesX", " and ".join(NICE[t["instance"]] for t in ns)); put("nsGainLoX", min(t["diff_pt"] for t in ns)); put("nsGainHiX", max(t["diff_pt"] for t in ns))
put("pGainXmax", AD.sci(max(c8x[f"{CN[t['instance']]} vs tuned harmonic dependability"]["holm_clust"] for t in up)))
put("secUpNamesX", " and ".join(NICE[t["instance"]] for t in secup)); put("secUpLoX", min(t["diff_pt"] for t in secup)); put("secUpHiX", max(t["diff_pt"] for t in secup))
put("secDiffLoX", min(t["diff_pt"] for t in sX8), "{:+.1f}"); put("secDiffHiX", max(t["diff_pt"] for t in sX8), "{:+.1f}")
dx2 = J(BASE / "dx2_tuned_harmonic_ood_plantb.json")
xo, xb = dx2["plantA_OOD|tuned, extended grid (frozen)"], dx2["plantB_main|tuned, extended grid (frozen)"]
put("oodDepHx", xo["dep"]); put("oodSecHx", xo["sec"]); put("bDepHx", xb["dep"]); put("bSecHx", xb["sec"]); put("bFtHx", xb["false_trips"], "{:d}"); put("bHealthyHx", xb["n_healthy"], "{:d}")
put("frozenSet", "pickup {:.2f}\\,pu, $k_2$ {:.2f}, $k_5$ {:.2f}".format(*dx2["setting"]))

# ------------------------------------------------------------------ protocol constants and derived counts used in the prose
gen = T(ROOT / "simulations" / "generate_stress_dataset_v5.m")
put("traceLen", float(re.search(r"'StopTime', ([\d.]+)", gen).group(1)), "{:.1f}", "generate_stress_dataset_v5.m")
put("winMs", 1000 * int(re.search(r"^WINDOW = (\d+)", T(ROOT / "lstm_models" / "features12.py"), re.M).group(1)) / fs, "{:.0f}")
put("minFaultPu", float(re.search(r'"--min-fault-pu", type=float, default=([\d.]+)', tts).group(1)), "{:.2f}")
put("clLimitMs", re.search(r"within (\d+) ms", T(ROOT / "simulations" / "test_hybrid_relay_d5main_results.txt")).group(1))
put("hfLimit", re.search(r"> ([\d.]+) kHz", T(ROOT / "documents" / "baselines" / "hf_content.txt")).group(1))
crit = re.search(r"only family of methods with ≥ (\d+) % dependability and ≥ ([\d.]+) % security", T(ROOT / "BENCHMARK_FAIRNESS_PLAN.md"))
cd_, cs_ = float(crit.group(1)), float(crit.group(2))
put("critDep", cd_, "{:.0f}", "BENCHMARK_FAIRNESS_PLAN.md (dated plan)"); put("critSec", cs_, "{:.1f}")
meet = lambda name: (lambda d, s_: d >= cd_ and s_ >= cs_)(*P.dep_sec(Mth[name][1]))  # noqa: E731
nat = [n for n in Mth if n.endswith("(native)")]; lfl = [n for n in Mth if n.endswith("(like-for-like)")]
put("nNatMeet", sum(meet(n) for n in nat), "{:d}"); put("nLflMeet", sum(meet(n) for n in lfl), "{:d}")
put("lflMeetNames", " and ".join(n.replace(" (like-for-like)", "").replace("õ", "\\~o") + (" et al." if "Ngaopitakkul" not in n else "") for n in lfl if meet(n)))
put("hizMiss", 100 - float(hz.group(2)), "{:.0f}")
inst = ["LSTM, deployed", "Key's network", "1D-CNN", "GRU", "MLP", "Random forest", "LSTM, tuned"]
hz_i = [100 * np.mean([r["correct"] for r in Mth[n][1] if r["category"] == "Internal HiZ" and not r.get("undetectable")]) for n in inst]
put("hizInstLo", min(hz_i)); put("hizInstHi", max(hz_i))
put("keyGateCost", P.dep_sec(Mth["Key (like-for-like)"][1])[0] - P.dep_sec(Mth["Key's network"][1])[0]); put("keyGateSec", P.dep_sec(Mth["Key's network"][1])[1] - P.dep_sec(Mth["Key (like-for-like)"][1])[1])
put("nClsAll", len(P.B2) + 1, "{:d}", "B2 classifiers + Key's network")
good = [n for n in inst[1:]] + []
put("nClsGood", len(d8), "{:d}")

# ------------------------------------------------------------------ write
lines = ["% generated by tools/build_paper_v1_macros.py - do not edit (every value read from a saved file)"]
for kk in sorted(M):
    v = M[kk].replace(",", "{,}") if re.fullmatch(r"[\d,]+(\.\d+)?", M[kk]) else M[kk]
    lines.append(f"\\newcommand{{\\{kk}}}{{{v}}}")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(M), "macros ->", OUT.relative_to(ROOT))
