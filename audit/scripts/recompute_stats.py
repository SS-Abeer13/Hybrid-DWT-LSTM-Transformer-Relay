"""Independent audit recomputation (task B1).

Re-derives, from the per-trace JSON files only, the dependability / security values, the McNemar discordant counts,
the exact two-sided McNemar p-values and the Holm-adjusted p-values reported in
  runs/20261101_v5_benchmark_fair/n5_statistics.json            (24 tests)
  runs/20261101_v5_benchmark_fair/n5_statistics_modeb.json      (48 tests)
  runs/20261101_v5_benchmark_fair/n5_statistics_keyhybrid.json  (2 tests, Holm over 50)
  runs/20261101_v5_benchmark_fair/n6c_tuned_harmonic.json       (4 tests)
  runs/20261101_v5_benchmark_fair/n8a_instances_vs_tuned_harmonic.json (12 tests, Holm over 16)
  runs/20261101_v5_benchmark_fair/b2_equal_search/b2_summary.json (22 tests)
  runs/20261101_v5_benchmark_fair/gated_only_ablation.json      (2 tests, raw p)

Written for the audit; it does NOT import tools/ or lstm_models/ (independent code path):
  * pairing is done by an explicit (seed, fold, trace) key, and each pair is checked for the same scenario name and label;
  * the exact McNemar p-value uses scipy.stats.binomtest; Holm uses statsmodels.stats.multitest.multipletests(method="holm");
  * the common set is rebuilt from documents/baselines/hr_missing_traces.txt and runs/.../trace_metas_plantA.json.
Output: audit/scripts/out/recompute_stats.json and recompute_stats.txt (printed too).
Usage: python audit/scripts/recompute_stats.py   (from the repo root)
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[2]
BF = ROOT / "runs" / "20261101_v5_benchmark_fair"
CVD = ROOT / "runs" / "20261029_v5_cv5_seeds"
OUTD = Path(__file__).resolve().parent / "out"
OUTD.mkdir(exist_ok=True)
SEEDS = (20261021, 20261022, 20261023)
METHODS = ["simoes_grid", "afrasiabi", "key", "alhamd", "abdusalam_ba_svm", "ngaopitakkul"]
TOL_PT = 0.01
LOG: list[str] = []
MISMATCH: list[str] = []
WARN: list[str] = []


def log(s=""):
    LOG.append(s)
    print(s)


# ----------------------------------------------------------------------------------------------- loaders
def load_ref(variant):
    out, scen = {}, {}
    for s in SEEDS:
        for k in range(1, 6):
            rows = json.loads((CVD / f"seed_{s}" / f"fold{k}" / "result.json").read_text())["rows"][variant]
            for r in rows:
                key = (s, k, int(r["trace"]))
                if key in out:
                    WARN.append(f"duplicate key {key} in reference {variant}")
                out[key] = r
    return out


def load_full(name, mode):
    out = {}
    for f in sorted((BF / "full" / name).glob("cv_seed*_fold*.json")):
        for r in json.loads(f.read_text())[mode]:
            key = (int(r["seed"]), int(r["fold"]), int(r["trace"]))
            if key in out:
                WARN.append(f"duplicate key {key} in full/{name} {mode}")
            out[key] = r
    return out


def load_b2():
    out = {}
    for f in sorted((BF / "b2_equal_search").glob("final_seed*_fold*.json")):
        j = json.loads(f.read_text())
        for name, v in j.items():
            for mode in ("standalone", "hybrid"):
                d = out.setdefault(name, {}).setdefault(mode, {})
                for r in v[mode]:
                    d[(int(r["seed"]), int(r["fold"]), int(r["trace"]))] = r
    return out


def common_set_bad():
    metas = json.loads((BF / "trace_metas_plantA.json").read_text())
    excl = set()
    for line in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
        p = [x.strip() for x in line.split(",")]
        if len(p) >= 2 and p[1].lstrip("-").isdigit():
            excl.add((p[0], int(p[1])))
    bad = {i for i, m in enumerate(metas) if (m["source_file"], int(m["source_index"])) in excl}
    return metas, bad


METAS, BAD = common_set_bad()


def undetectable_meta(i):
    m = METAS[i]
    fp = m.get("fault_pu")
    return bool(m["should_trip"] and fp is not None and np.isfinite(fp) and fp < 0.05)


# ----------------------------------------------------------------------------------------------- tests
def paired(ref, oth, flag, drop_bad=False):
    """Keys present in both, same label, detectable in BOTH files, label == flag."""
    ks = []
    for key in sorted(set(ref) & set(oth)):
        a, b = ref[key], oth[key]
        if drop_bad and key[2] in BAD:
            continue
        if int(a["should_trip"]) != int(b["should_trip"]):
            MISMATCH.append(f"label differs for {key}")
            continue
        sa, sb = a.get("scenario"), b.get("scenario")
        if sa is not None and sb is not None and sa != sb:
            MISMATCH.append(f"scenario differs for {key}: {sa} vs {sb}")
        if a.get("undetectable") or b.get("undetectable"):
            continue
        if int(a["should_trip"]) == flag:
            ks.append(key)
    return ks


def mcn(ref, oth, ks):
    a = np.array([bool(ref[k]["correct"]) for k in ks])
    b = np.array([bool(oth[k]["correct"]) for k in ks])
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p = binomtest(n10, n10 + n01, 0.5, alternative="two-sided").pvalue if n10 + n01 else 1.0
    ps = {}
    for s in SEEDS:
        m = np.array([k[0] == s for k in ks])
        ps[s] = 100 * (b[m].mean() - a[m].mean()) if m.any() else None
    return dict(n=len(ks), ref_pct=100 * a.mean(), oth_pct=100 * b.mean(), diff=100 * (b.mean() - a.mean()), n10=n10, n01=n01, p=float(p), per_seed=ps)


def holm(ps):
    return multipletests(np.asarray(ps, float), method="holm")[1]


def cmp_test(label, mine, saved, fields):
    """fields: list of (my_key, saved_key, kind) kind in pt|int|p."""
    bad = []
    for mk, sk, kind in fields:
        if sk not in saved:
            continue
        x, y = mine[mk], saved[sk]
        if kind == "pt" and abs(x - y) > TOL_PT:
            bad.append(f"{sk}: recomputed {x:.4f} vs saved {y:.4f}")
        if kind == "int" and int(x) != int(y):
            bad.append(f"{sk}: recomputed {x} vs saved {y}")
        if kind == "p":
            if not (np.isclose(x, y, rtol=1e-6, atol=1e-300) or (x < 1e-300 and y < 1e-300)):
                bad.append(f"{sk}: recomputed {x:.6e} vs saved {y:.6e}")
            elif (x < 0.05) != (y < 0.05):
                bad.append(f"{sk}: significance flips")
    status = "OK" if not bad else "MISMATCH: " + "; ".join(bad)
    if bad:
        MISMATCH.append(f"{label}: " + "; ".join(bad))
    return status


STD_FIELDS = [("n", "n", "int"), ("ref_pct", "ref_pct", "pt"), ("oth_pct", "method_pct", "pt"), ("diff", "diff_pt", "pt"),
              ("n10", "n_ref_only_correct", "int"), ("n01", "n_method_only_correct", "int"), ("p", "p", "p"), ("p_holm", "p_holm", "p")]


def family_n5(modes, saved_file):
    refs = {"Proposed hybrid": load_ref("Hybrid + AI-alone path"), "LSTM alone": load_ref("LSTM alone")}
    mine = []
    for mode in modes:
        for m in METHODS:
            rows = load_full(m, mode)
            for rn, ref in refs.items():
                for metric, flag in (("dependability", 1), ("security", 0)):
                    t = mcn(ref, rows, paired(ref, rows, flag))
                    t.update(mode=mode, method=m, reference=rn, metric=metric)
                    mine.append(t)
    for t, q in zip(mine, holm([t["p"] for t in mine])):
        t["p_holm"] = float(q)
    saved = json.loads((BF / saved_file).read_text())["tests"]
    log(f"\n== {saved_file}: {len(mine)} recomputed tests, {len(saved)} saved tests (Holm family size recomputed = {len(mine)})")
    if len(saved) != len(mine):
        MISMATCH.append(f"{saved_file}: family size {len(saved)} saved vs {len(mine)} recomputed")
    for t in mine:
        s = [x for x in saved if x["method"] == t["method"] and x["reference"] == t["reference"] and x["metric"] == t["metric"] and x.get("mode", "native") == t["mode"]]
        st = cmp_test(f"{saved_file} {t['reference']} {t['mode']} {t['method']} {t['metric']}", t, s[0], STD_FIELDS) if s else "NOT IN SAVED FILE"
        log(f"  {t['reference']:15s} {t['mode']:6s} {t['method']:17s} {t['metric']:13s} n={t['n']:4d} {t['ref_pct']:6.2f} {t['oth_pct']:6.2f} {t['diff']:+7.2f} "
            f"{t['n10']:5d}/{t['n01']:<5d} p={t['p']:.3e} pH={t['p_holm']:.3e}  {st}")
    return mine


def keyhybrid(prior):
    ref = load_ref("Hybrid + AI-alone path")
    kh = load_full("key_hybrid", "hybrid")
    mine = []
    for metric, flag in (("dependability", 1), ("security", 0)):
        t = mcn(ref, kh, paired(ref, kh, flag)); t["metric"] = metric; mine.append(t)
    adj = holm([t["p"] for t in prior] + [t["p"] for t in mine])
    for t, q in zip(mine, adj[len(prior):]):
        t["p_holm"] = float(q)
    saved = json.loads((BF / "n5_statistics_keyhybrid.json").read_text())
    log(f"\n== n5_statistics_keyhybrid.json: Holm family = {len(prior)} + {len(mine)} = {len(prior) + len(mine)}")
    for t in mine:
        s = [x for x in saved if x["metric"] == t["metric"]][0]
        st = cmp_test(f"keyhybrid {t['metric']}", t, s, [("n", "n", "int"), ("ref_pct", "hybrid_pct", "pt"), ("oth_pct", "key_hybrid_pct", "pt"), ("diff", "diff_pt", "pt"),
                                                         ("n10", "hybrid_only_correct", "int"), ("n01", "keyhybrid_only_correct", "int"), ("p", "p", "p"), ("p_holm", "p_holm50", "p")])
        log(f"  {t['metric']:13s} n={t['n']} {t['ref_pct']:.2f} -> {t['oth_pct']:.2f} ({t['diff']:+.2f}) {t['n10']}/{t['n01']} p={t['p']:.3e} pH50={t['p_holm']:.3e} "
            f"seeds {[round(v, 2) for v in t['per_seed'].values()]}  {st}")
    # fold-model sd
    dep, sec = [], []
    for s in SEEDS:
        for k in range(1, 6):
            r = [x for kk, x in kh.items() if kk[0] == s and kk[1] == k and not x["undetectable"]]
            dep.append(100 * np.mean([x["correct"] for x in r if x["should_trip"]])); sec.append(100 * np.mean([x["correct"] for x in r if not x["should_trip"]]))
    log(f"  fold-model mean+-sd: dep {np.mean(dep):.2f} +- {np.std(dep, ddof=1):.2f} (min {min(dep):.1f}); sec {np.mean(sec):.2f} +- {np.std(sec, ddof=1):.2f} (min {min(sec):.1f})")
    log(f"  Key-hybrid rows contain {len(kh)} (seed, fold, trace) keys; traces outside the common set: {sum(1 for k in kh if k[2] in BAD)}")
    for lab in ("plantA_OOD", "plantB_main"):
        j = json.loads((BF / "full" / "key_hybrid" / f"final_{lab}.json").read_text())
        rows = [r for r in j["hybrid"] if not r["undetectable"]]
        f_ = [r["correct"] for r in rows if r["should_trip"]]; h_ = [r["correct"] for r in rows if not r["should_trip"]]
        log(f"  {lab}: dep {100*np.mean(f_):.2f} (n={len(f_)}), sec {100*np.mean(h_):.2f} (n={len(h_)})")
    return mine


def n6c():
    rows = json.loads((BF / "n6c_tuned_rows.json").read_text())
    tuned = {tuple(r["key"]): r for r in rows["tuned"]}
    text = {tuple(r["key"]): r for r in rows["textbook"]}
    ref = load_ref("Hybrid + AI-alone path")
    mine = []
    for name, d in (("textbook 0.30/0.15/0.35", text), ("tuned on validation", tuned)):
        for metric, flag in (("dependability", 1), ("security", 0)):
            t = mcn(ref, d, paired(ref, d, flag)); t.update(setting=name, metric=metric); mine.append(t)
    for t, q in zip(mine, holm([t["p"] for t in mine])):
        t["p_holm"] = float(q)
    saved = json.loads((BF / "n6c_tuned_harmonic.json").read_text())["tests"]
    log(f"\n== n6c_tuned_harmonic.json: Holm family = {len(mine)}")
    for t in mine:
        s = [x for x in saved if x["setting"] == t["setting"] and x["metric"] == t["metric"]][0]
        st = cmp_test(f"n6c {t['setting']} {t['metric']}", t, s, [("n", "n", "int"), ("ref_pct", "hybrid", "pt"), ("oth_pct", "harmonic", "pt"), ("diff", "diff_pt", "pt"),
                                                                 ("n10", "hybrid_only", "int"), ("n01", "harmonic_only", "int"), ("p", "p", "p"), ("p_holm", "p_holm4", "p")])
        log(f"  {t['setting']:24s} {t['metric']:13s} n={t['n']} {t['ref_pct']:.2f} {t['oth_pct']:.2f} {t['diff']:+.2f} {t['n10']}/{t['n01']} p={t['p']:.3e} pH4={t['p_holm']:.3e} {st}")
    # HiZ family
    for g in ("Internal_HiZ", "other"):
        def dep(d):
            v = [bool(d[k]["correct"]) for k in tuned if k in ref and k in d and d[k]["should_trip"] and not d[k].get("undetectable") and not ref[k].get("undetectable")
                 and (METAS[k[2]]["scenarioName"].startswith("Internal_HiZ") == (g == "Internal_HiZ"))]
            return 100 * np.mean(v), len(v)
        log(f"  dependability {g}: hybrid {dep(ref)[0]:.1f} (n={dep(ref)[1]}), tuned harmonic {dep(tuned)[0]:.1f}, textbook {dep(text)[0]:.1f}")
    return mine, tuned


def n8a(n6c_tests, tuned):
    b2 = load_b2()
    inst = {}
    for name in ("1D-CNN", "Wavelet-GRU", "Wavelet-ANN", "Wavelet-RF", "Proposed LSTM"):
        inst[name] = {k: v for k, v in b2[name]["hybrid"].items() if k[2] not in BAD}
    inst["Key (claim-C run)"] = load_full("key_hybrid", "hybrid")
    order = ["1D-CNN", "Wavelet-GRU", "Wavelet-ANN", "Key (claim-C run)", "Wavelet-RF", "Proposed LSTM"]
    mine = []
    for name in order:
        for metric, flag in (("dependability", 1), ("security", 0)):
            t = mcn(tuned, inst[name], paired(tuned, inst[name], flag)); t.update(instance=name, metric=metric); mine.append(t)
    adj = holm([t["p"] for t in mine] + [t["p"] for t in n6c_tests])
    for t, q in zip(mine, adj[:len(mine)]):
        t["p_holm"] = float(q)
    saved = json.loads((BF / "n8a_instances_vs_tuned_harmonic.json").read_text())
    log(f"\n== n8a_instances_vs_tuned_harmonic.json: Holm family = {len(mine)} + {len(n6c_tests)} = {len(mine) + len(n6c_tests)}")
    for t in mine:
        nm = "LSTM (tuned, B2)" if t["instance"] == "Proposed LSTM" else t["instance"]
        s = [x for x in saved if x["instance"] == nm and x["metric"] == t["metric"]][0]
        st = cmp_test(f"n8a {nm} {t['metric']}", t, s, [("n", "n", "int"), ("ref_pct", "tuned_harmonic_pct", "pt"), ("oth_pct", "instance_pct", "pt"), ("diff", "diff_pt", "pt"),
                                                       ("n10", "harmonic_only", "int"), ("n01", "instance_only", "int"), ("p", "p", "p"), ("p_holm", "p_holm16", "p")])
        log(f"  {nm:18s} {t['metric']:13s} n={t['n']} {t['ref_pct']:.2f} {t['oth_pct']:.2f} {t['diff']:+.2f} {t['n10']}/{t['n01']} p={t['p']:.3e} pH16={t['p_holm']:.3e} {st}")
    return mine, b2


def b2fam(b2):
    deployed = load_ref("Hybrid + AI-alone path")
    names = ["Wavelet-SVM", "Wavelet-RF", "Wavelet-ANN", "1D-CNN", "Wavelet-GRU", "Proposed LSTM"]
    hyb = {n: {k: v for k, v in b2[n]["hybrid"].items() if k[2] not in BAD and not v.get("undetectable")} for n in names}
    sa = {n: {k: v for k, v in b2[n]["standalone"].items() if k[2] not in BAD and not v.get("undetectable")} for n in names}
    log("\n== b2_summary: Table B values recomputed (common set)")
    for n in names:
        f = lambda d, fl: 100 * np.mean([bool(r["correct"]) for r in d.values() if int(r["should_trip"]) == fl])  # noqa: E731
        log(f"  {n:14s} standalone {f(sa[n],1):6.2f} / {f(sa[n],0):6.2f}   hybrid {f(hyb[n],1):6.2f} / {f(hyb[n],0):6.2f}")
    tests = []
    for n in names[:-1]:
        for metric, flag in (("dependability", 1), ("security", 0)):
            t = mcn(hyb["Proposed LSTM"], hyb[n], paired(hyb["Proposed LSTM"], hyb[n], flag)); t.update(test=f"{n} hybrid vs tuned LSTM hybrid", metric=metric); tests.append(t)
    for metric, flag in (("dependability", 1), ("security", 0)):
        t = mcn(deployed, hyb["Proposed LSTM"], paired(deployed, hyb["Proposed LSTM"], flag)); t.update(test="tuned LSTM hybrid vs deployed hybrid (reference = deployed)", metric=metric); tests.append(t)
    for n in names[:-1]:
        for metric, flag in (("dependability", 1), ("security", 0)):
            t = mcn(deployed, hyb[n], paired(deployed, hyb[n], flag)); t.update(test=f"{n} hybrid vs deployed hybrid (reference = deployed)", metric=metric); tests.append(t)
    for t, q in zip(tests, holm([t["p"] for t in tests])):
        t["p_holm"] = float(q)
    planned = tests[:12]
    for t, q in zip(planned, holm([t["p"] for t in planned])):
        t["p_holm_planned12"] = float(q)
    saved = json.loads((BF / "b2_equal_search" / "b2_summary.json").read_text())
    log(f"  Holm family = {len(tests)} (12 planned + {len(tests) - 12} post-hoc); saved {len(saved)}")
    for t in tests:
        s = [x for x in saved if x["test"] == t["test"] and x["metric"] == t["metric"]][0]
        st = cmp_test(f"b2 {t['test']} {t['metric']}", t, s, [("n", "n", "int"), ("ref_pct", "ref_pct", "pt"), ("oth_pct", "other_pct", "pt"), ("diff", "diff_pt", "pt"),
                                                            ("n10", "ref_only", "int"), ("n01", "other_only", "int"), ("p", "p", "p"), ("p_holm", "p_holm", "p")])
        extra = f" pH12={t['p_holm_planned12']:.2e}" if "p_holm_planned12" in t else ""
        log(f"  {t['test'][:58]:58s} {t['metric'][:3]} n={t['n']} {t['diff']:+.2f} {t['n10']}/{t['n01']} pH22={t['p_holm']:.2e}{extra} {st}")
    return tests


def gated():
    dep = load_ref("Hybrid + AI-alone path"); g = load_ref("Hybrid (87T gate)")
    bad_drop = lambda d: {k: v for k, v in d.items() if k[2] not in BAD}  # noqa: E731
    saved = json.loads((BF / "gated_only_ablation.json").read_text())
    log("\n== gated_only_ablation (common set = drop traces without a 20 kHz copy)")
    for metric, flag in (("dependability", 1), ("security", 0)):
        a, b = bad_drop(dep), bad_drop(g)
        t = mcn(a, b, paired(a, b, flag))
        log(f"  {metric:13s} n={t['n']} {t['ref_pct']:.2f} -> {t['oth_pct']:.2f} ({t['diff']:+.2f}) {t['n10']}/{t['n01']} p={t['p']:.3e}")
    log("  saved: " + json.dumps(saved)[:600])


def ref_common_check():
    """The 'proposed hybrid' reference numbers are quoted on the common set (92.95 / 98.95). Verify, and check the fold test sets are identical across methods."""
    ref = load_ref("Hybrid + AI-alone path")
    sets = {"ref": {k for k in ref}}
    for m in METHODS + ["key_hybrid"]:
        sets[m] = set(load_full(m, "hybrid" if m == "key_hybrid" else "native"))
    b2 = load_b2()
    for n in b2:
        sets["b2:" + n] = set(b2[n]["hybrid"])
    log("== fold/trace set consistency")
    for name, s in sets.items():
        only_ref = len(sets["ref"] - s); only_m = len(s - sets["ref"])
        log(f"  {name:22s} keys {len(s):5d}  in ref not here {only_ref:4d}  here not in ref {only_m:3d}")
        if only_m:
            MISMATCH.append(f"{name}: {only_m} (seed, fold, trace) keys not in the proposed model's folds")
    # traces dropped from reproductions: are they exactly the BAD set?
    miss = {k[2] for k in sets["ref"] - sets["key"]}
    log(f"  traces in ref but not in reproductions: {len(miss)} unique; equal to the hr_missing set: {miss == BAD}; |BAD| = {len(BAD)}")
    for fl, lab in ((1, "dependability"), (0, "security")):
        v = [bool(r["correct"]) for k, r in ref.items() if k[2] not in BAD and not r["undetectable"] and int(r["should_trip"]) == fl]
        v_all = [bool(r["correct"]) for k, r in ref.items() if not r["undetectable"] and int(r["should_trip"]) == fl]
        log(f"  proposed hybrid {lab}: common set {100*np.mean(v):.2f} (n={len(v)}), all traces {100*np.mean(v_all):.2f} (n={len(v_all)})")
    # undetectable flags agree with the metadata file?
    dis = sum(1 for k, r in ref.items() if bool(r["undetectable"]) != undetectable_meta(k[2]))
    log(f"  undetectable flag in result.json vs metadata (fault_pu < 0.05): {dis} disagreements")
    # per-seed fold sizes
    c = Counter((k[0], k[1]) for k in ref)
    log(f"  test traces per (seed, fold): min {min(c.values())}, max {max(c.values())}, total per seed {[sum(v for kk, v in c.items() if kk[0] == s) for s in SEEDS]}")


if __name__ == "__main__":
    ref_common_check()
    native = family_n5(("native",), "n5_statistics.json")
    both = family_n5(("native", "modeb"), "n5_statistics_modeb.json")
    keyhybrid(both)
    n6, tuned = n6c()
    _, b2 = n8a(n6, tuned)
    b2fam(b2)
    gated()
    log("\n== SUMMARY")
    log(f"mismatches > {TOL_PT} pt or in p / counts / family size: {len(MISMATCH)}")
    for m in MISMATCH:
        log("  - " + m)
    log(f"warnings: {len(WARN)}")
    for w in WARN[:20]:
        log("  - " + w)
    (OUTD / "recompute_stats.txt").write_text("\n".join(LOG))
