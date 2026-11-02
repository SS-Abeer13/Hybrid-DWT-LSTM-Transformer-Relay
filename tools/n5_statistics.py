"""D-N5: paired McNemar tests (exact, two-sided) on (seed, fold, trace), the proposed hybrid and LSTM alone against each reproduction's native decisions,
dependability (fault traces) and security (healthy traces) separately, pooled over the 3 seeds, Holm correction over ALL tests in the table, plus per-seed
differences (sign stability) and fold-model sd. Undetectable faults and the 30 traces without a 20 kHz copy are excluded (common set).
Output: runs/20261101_v5_benchmark_fair/n5_statistics.json / .txt"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import cv  # noqa: E402

OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
CVD = ROOT / "runs" / "20261029_v5_cv5_seeds"
METHODS = ["simoes_grid", "afrasiabi", "key", "alhamd", "abdusalam_ba_svm", "ngaopitakkul"]
REF = {"Proposed hybrid": "Hybrid + AI-alone path", "LSTM alone": "LSTM alone"}


def load_ref(variant):
    out = {}
    for seed in cv.SEEDS:
        for k in range(1, 6):
            for r in json.load(open(CVD / f"seed_{seed}" / f"fold{k}" / "result.json"))["rows"][variant]:
                out[(seed, k, r["trace"])] = r
    return out


def load_method(name, mode="native"):
    out = {}
    for f in sorted((OUT / "full" / name).glob("cv_seed*_fold*.json")):
        for r in json.loads(f.read_text())[mode]:
            out[(r["seed"], r["fold"], r["trace"])] = r
    return out


def mcnemar(a, b):
    """a, b: boolean correctness arrays (paired). Exact two-sided p; n10 = ref right & other wrong, n01 = ref wrong & other right."""
    n10, n01 = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    return n10, n01, float(p)


def holm(ps):
    order = np.argsort(ps)
    adj, run = np.zeros(len(ps)), 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(ps) - rank) * ps[i]); adj[i] = min(1.0, run)
    return adj


def main():
    refs = {n: load_ref(v) for n, v in REF.items()}
    tests = []
    for m in METHODS:
        rows = load_method(m)
        if not rows:
            continue
        for rn, ref in refs.items():
            keys = [k for k in rows if k in ref and not rows[k]["undetectable"]]
            for metric, flag in (("dependability", 1), ("security", 0)):
                ks = [k for k in keys if rows[k]["should_trip"] == flag]
                a = np.array([bool(ref[k]["correct"]) for k in ks]); b = np.array([bool(rows[k]["correct"]) for k in ks])
                n10, n01, p = mcnemar(a, b)
                per_seed = {}
                for s in cv.SEEDS:
                    sk = [i for i, k in enumerate(ks) if k[0] == s]
                    per_seed[s] = float(100 * (b[sk].mean() - a[sk].mean())) if sk else None
                tests.append({"method": m, "reference": rn, "metric": metric, "n": len(ks), "ref_pct": float(100 * a.mean()), "method_pct": float(100 * b.mean()),
                              "diff_pt": float(100 * (b.mean() - a.mean())), "n_ref_only_correct": n10, "n_method_only_correct": n01, "p": p, "per_seed_diff_pt": per_seed})
    adj = holm(np.array([t["p"] for t in tests]))
    for t, q in zip(tests, adj):
        t["p_holm"] = float(q)
        ds = [v for v in t["per_seed_diff_pt"].values() if v is not None]
        t["sign_stable"] = bool(all(v > 0 for v in ds) or all(v < 0 for v in ds) or all(v == 0 for v in ds))
    # fold-model sd of the methods
    sd = {}
    for m in METHODS:
        rows = load_method(m)
        if not rows:
            continue
        deps, secs = [], []
        for s in cv.SEEDS:
            for k in range(1, 6):
                r = [x for kk, x in rows.items() if kk[0] == s and kk[1] == k and not x["undetectable"]]
                f = [x["correct"] for x in r if x["should_trip"]]; h = [x["correct"] for x in r if not x["should_trip"]]
                if f and h:
                    deps.append(100 * np.mean(f)); secs.append(100 * np.mean(h))
        sd[m] = {"n_fold_models": len(deps), "dep_mean": float(np.mean(deps)), "dep_sd": float(np.std(deps, ddof=1)), "sec_mean": float(np.mean(secs)), "sec_sd": float(np.std(secs, ddof=1))}
    L = ["Paired exact McNemar tests on (seed, fold, trace), plant-A common set, native decisions; Holm correction over all %d tests; * = p_Holm < 0.05; 'unstable' = per-seed difference changes sign" % len(tests),
         f"{'reference':16s} {'method':18s} {'metric':14s} {'n':>5s} {'ref %':>7s} {'meth %':>7s} {'diff pt':>8s} {'ref-only':>8s} {'meth-only':>9s} {'p':>9s} {'p_Holm':>9s}"]
    for t in tests:
        L.append(f"{t['reference']:16s} {t['method']:18s} {t['metric']:14s} {t['n']:5d} {t['ref_pct']:7.2f} {t['method_pct']:7.2f} {t['diff_pt']:+8.2f} {t['n_ref_only_correct']:8d} {t['n_method_only_correct']:9d} {t['p']:9.2e} {t['p_holm']:9.2e}"
                 + (" *" if t["p_holm"] < 0.05 else "") + ("" if t["sign_stable"] else " unstable"))
    L += ["", "fold-model mean +- sd (15 fold-models per method)"] + [f"{m:18s} dep {v['dep_mean']:.2f} +- {v['dep_sd']:.2f}   sec {v['sec_mean']:.2f} +- {v['sec_sd']:.2f}" + ("   (sd > 3 pt: report the range)" if max(v["dep_sd"], v["sec_sd"]) > 3 else "") for m, v in sd.items()]
    (OUT / "n5_statistics.json").write_text(json.dumps({"tests": tests, "fold_sd": sd}, indent=1)); (OUT / "n5_statistics.txt").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
