"""D-B2 results: Table B 'tuned with equal budget' (3 seeds x 5 folds, common set, stride 4, 25 epochs / patience 5) and paired exact McNemar tests on (seed, fold, trace):
each model's HYBRID vs the tuned LSTM hybrid, and the tuned LSTM hybrid vs the deployed hybrid; dependability and security separately, Holm over all 12 tests.
Output: runs/20261101_v5_benchmark_fair/b2_equal_search/b2_summary.txt/.json"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models")); sys.path.insert(0, str(ROOT / "tools"))
from baselines import cv
import n5_statistics as N5
D = ROOT / "runs" / "20261101_v5_benchmark_fair" / "b2_equal_search"
excl = set()
for l in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
    f, i, *_ = [x.strip() for x in l.split(",")]; excl.add((f, int(i)))
metas, _ = cv.trace_index()
bad = {i for i, m in enumerate(metas) if (m["source_file"], int(m["source_index"])) in excl}
files = sorted(D.glob("final_seed*_fold*.json"))
names = ["Wavelet-SVM", "Wavelet-RF", "Wavelet-ANN", "1D-CNN", "Wavelet-GRU", "Proposed LSTM"]
rows = {n: {"standalone": {}, "hybrid": {}} for n in names}; ep = {n: [] for n in names}
for f in files:
    j = json.loads(f.read_text())
    for n in names:
        if n not in j:
            continue
        for mode in ("standalone", "hybrid"):
            for r in j[n][mode]:
                if r["trace"] not in bad and not r.get("undetectable"):
                    rows[n][mode][(r["seed"], r["fold"], r["trace"])] = r
        if j[n]["epochs_used"] is not None:
            ep[n].append(j[n]["epochs_used"])
deployed = N5.load_ref("Hybrid + AI-alone path"); deployed_sa = N5.load_ref("LSTM alone")
def pct(rs, flag):
    v = [bool(r["correct"]) for r in rs.values() if r["should_trip"] == flag]
    return 100 * np.mean(v) if v else float("nan")
L = [f"Table B, tuned with equal budget ({len(files)} fold-models per model; common set)", f"{'model':16s} {'standalone dep/sec':>20s} {'hybrid dep/sec':>16s} {'epochs':>7s}  chosen configuration"]
best = json.loads((D / "chosen_configs.json").read_text())
for n in names:
    L.append(f"{n:16s} {pct(rows[n]['standalone'],1):9.2f} / {pct(rows[n]['standalone'],0):6.2f}   {pct(rows[n]['hybrid'],1):7.2f} / {pct(rows[n]['hybrid'],0):6.2f} {np.mean(ep[n]) if ep[n] else float('nan'):7.1f}  {best[n]}")
L.append(f"{'deployed LSTM':16s} {pct({k: v for k, v in deployed_sa.items() if (k in rows['Proposed LSTM']['standalone'])},1):9.2f} / {pct({k: v for k, v in deployed_sa.items() if (k in rows['Proposed LSTM']['standalone'])},0):6.2f}   {pct({k: v for k, v in deployed.items() if (k in rows['Proposed LSTM']['hybrid'])},1):7.2f} / {pct({k: v for k, v in deployed.items() if (k in rows['Proposed LSTM']['hybrid'])},0):6.2f}  (default configuration, stride 4, from the CV)")
tests = []
def test(label, a_rows, b_rows):
    for metric, flag in (("dependability", 1), ("security", 0)):
        ks = [k for k in b_rows if k in a_rows and b_rows[k]["should_trip"] == flag and not b_rows[k].get("undetectable") and not a_rows[k].get("undetectable")]
        a = np.array([bool(a_rows[k]["correct"]) for k in ks]); b = np.array([bool(b_rows[k]["correct"]) for k in ks])
        n10, n01, p = N5.mcnemar(a, b)
        ps = {s: float(100 * (b[[i for i, k in enumerate(ks) if k[0] == s]].mean() - a[[i for i, k in enumerate(ks) if k[0] == s]].mean())) for s in cv.SEEDS}
        tests.append({"test": label, "metric": metric, "n": len(ks), "ref_pct": 100 * a.mean(), "other_pct": 100 * b.mean(), "diff_pt": 100 * (b.mean() - a.mean()), "ref_only": n10, "other_only": n01, "p": p, "per_seed": ps})
for n in names[:-1]:
    test(f"{n} hybrid vs tuned LSTM hybrid", rows["Proposed LSTM"]["hybrid"], rows[n]["hybrid"])
test("tuned LSTM hybrid vs deployed hybrid (reference = deployed)", deployed, rows["Proposed LSTM"]["hybrid"])
for n in names[:-1]:   # added after seeing the first 12 tests: every tuned hybrid vs the DEPLOYED proposed hybrid (the comparison the claim is about)
    test(f"{n} hybrid vs deployed hybrid (reference = deployed)", deployed, rows[n]["hybrid"])
adj = N5.holm(np.array([t["p"] for t in tests]))
L += ["", f"paired exact McNemar, Holm over {len(tests)} tests (diff = other minus reference, pt)"]
for t, q in zip(tests, adj):
    t["p_holm"] = float(q)
    ds = list(t["per_seed"].values()); t["sign_stable"] = all(v > 0 for v in ds) or all(v < 0 for v in ds) or all(v == 0 for v in ds)
    L.append(f"{t['test']:62s} {t['metric']:13s} n={t['n']} ref {t['ref_pct']:.2f} other {t['other_pct']:.2f} diff {t['diff_pt']:+.2f} discordant {t['ref_only']}/{t['other_only']} p_Holm {q:.2e}" + (" *" if q < 0.05 else "") + ("" if t["sign_stable"] else " unstable"))
(D / "b2_summary.txt").write_text("\n".join(L)); (D / "b2_summary.json").write_text(json.dumps(tests, indent=1)); print("\n".join(L))
