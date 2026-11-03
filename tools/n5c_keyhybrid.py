"""Holm-50 statistics of the claim-C evaluation 'hybrid with Key' (review 2026-11-03 09:45; H6 logged before): exact McNemar vs the proposed hybrid on the same
(seed, fold, trace) pairs, dependability and security, Holm over 50 tests = the 48 of n5_statistics_modeb.json + these 2. Plus OOD and plant B (single final model, descriptive,
Wilson 95 % intervals). Output: runs/20261101_v5_benchmark_fair/n5_statistics_keyhybrid.txt/.json"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models")); sys.path.insert(0, str(ROOT / "tools"))
from baselines import cv, common as C
import n5_statistics as N5
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
ref = N5.load_ref("Hybrid + AI-alone path")
kh = {}
for f in sorted((OUT / "full" / "key_hybrid").glob("cv_seed*_fold*.json")):
    for r in json.loads(f.read_text())["hybrid"]:
        kh[(r["seed"], r["fold"], r["trace"])] = r
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)
tests = []
for metric, flag in (("dependability", 1), ("security", 0)):
    ks = [k for k in kh if k in ref and not kh[k]["undetectable"] and kh[k]["should_trip"] == flag]
    a = np.array([bool(ref[k]["correct"]) for k in ks]); b = np.array([bool(kh[k]["correct"]) for k in ks])
    n10, n01, p = N5.mcnemar(a, b)
    ps = {s: float(100 * (b[[i for i, k in enumerate(ks) if k[0] == s]].mean() - a[[i for i, k in enumerate(ks) if k[0] == s]].mean())) for s in cv.SEEDS}
    tests.append({"metric": metric, "n": len(ks), "hybrid_pct": 100 * a.mean(), "key_hybrid_pct": 100 * b.mean(), "diff_pt": 100 * (b.mean() - a.mean()), "hybrid_only_correct": n10, "keyhybrid_only_correct": n01, "p": p, "per_seed_diff_pt": ps})
prior = [t["p"] for t in json.loads((OUT / "n5_statistics_modeb.json").read_text())["tests"]]
adj = N5.holm(np.array(prior + [t["p"] for t in tests]))
for t, q in zip(tests, adj[len(prior):]):
    t["p_holm50"] = float(q)
L = [f"Hybrid with Key vs proposed hybrid, plant-A CV (3 seeds x 5 folds, common set), exact McNemar, Holm over {len(prior)+2} tests; per-seed difference in the last column"]
for t in tests:
    L.append(f"{t['metric']:13s} n={t['n']}: proposed {t['hybrid_pct']:.2f} %, with Key {t['key_hybrid_pct']:.2f} %, diff {t['diff_pt']:+.2f} pt, discordant {t['hybrid_only_correct']}/{t['keyhybrid_only_correct']}, p = {t['p']:.2e}, p_Holm50 = {t['p_holm50']:.2e}" + (" *" if t["p_holm50"] < 0.05 else "") + "  seeds " + " ".join(f"{v:+.2f}" for v in t["per_seed_diff_pt"].values()))
dep, sec = [], []
for s in cv.SEEDS:
    for k in range(1, 6):
        r = [x for kk, x in kh.items() if kk[0] == s and kk[1] == k and not x["undetectable"]]
        dep.append(100 * np.mean([x["correct"] for x in r if x["should_trip"]])); sec.append(100 * np.mean([x["correct"] for x in r if not x["should_trip"]]))
L.append(f"fold-model mean +- sd (15): dependability {np.mean(dep):.2f} +- {np.std(dep, ddof=1):.2f} (min {min(dep):.1f}), security {np.mean(sec):.2f} +- {np.std(sec, ddof=1):.2f} (min {min(sec):.1f})")
L.append(f"H6 check: dependability >= 93 %: {np.mean(dep) >= 93}; security >= 99 %: {np.mean(sec) >= 99}")
for lab in ("plantA_OOD", "plantB_main"):
    j = json.loads((OUT / "full" / "key_hybrid" / f"final_{lab}.json").read_text())
    rows = [r for r in j["hybrid"] if not r["undetectable"]]
    f_ = [r for r in rows if r["should_trip"]]; h_ = [r for r in rows if not r["should_trip"]]
    kf, kh_ = sum(r["correct"] for r in f_), sum(r["correct"] for r in h_)
    lo1, hi1 = wilson(kf, len(f_)); lo2, hi2 = wilson(kh_, len(h_))
    L.append(f"{lab} (final model, descriptive; thresholds AI {j['thr']}, solo {j['solo']}): dependability {100*kf/len(f_):.2f} % [{lo1:.1f}, {hi1:.1f}] (n={len(f_)}), security {100*kh_/len(h_):.2f} % [{lo2:.1f}, {hi2:.1f}] (n={len(h_)})"
             + (f"; false-trip first path {j['paths']['false_trips']}, fault first path {j['paths']['faults']}" if "paths" in j else "")
             + (" | gated-only counterfactual: " + str({k: round(v, 2) if isinstance(v, float) else v for k, v in C.summarise(j['gated_only']).items() if k in ('dependability_pct', 'security_pct', 'false_trips')}) if "gated_only" in j else ""))
L.append("proposed hybrid, for reference (final model): OOD 97.99 / 96.00; plant B zero-shot 92.70 / 88.35")
(OUT / "n5_statistics_keyhybrid.txt").write_text("\n".join(L)); (OUT / "n5_statistics_keyhybrid.json").write_text(json.dumps(tests, indent=1)); print("\n".join(L))
