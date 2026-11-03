"""D-N8a (post-hoc, added after N6c): each instance of the dual-path architecture (tuned CNN, GRU, ANN, RF, tuned LSTM from B2, and Key from the claim-C run) vs the
validation-tuned harmonic 87T, exact McNemar on (seed, fold, trace), dependability and security. Holm over 16 tests = these 12 + the 4 of N6c (textbook and tuned
harmonic vs the deployed hybrid). Output: runs/20261101_v5_benchmark_fair/n8a_instances_vs_tuned_harmonic.txt/.json"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models")); sys.path.insert(0, str(ROOT / "tools"))
from baselines import cv
import n5_statistics as N5
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
rows = json.loads((OUT / "n6c_tuned_rows.json").read_text())
tuned = {tuple(r["key"]): r for r in rows["tuned"]}
excl = set()
for l in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
    f, i, *_ = [x.strip() for x in l.split(",")]; excl.add((f, int(i)))
metas, _ = cv.trace_index()
bad = {i for i, m in enumerate(metas) if (m["source_file"], int(m["source_index"])) in excl}
inst = {}
for name in ("Wavelet-ANN", "1D-CNN", "Wavelet-GRU", "Wavelet-RF", "Proposed LSTM"):
    inst[name if name != "Proposed LSTM" else "LSTM (tuned, B2)"] = {}
for f in sorted((OUT / "b2_equal_search").glob("final_seed*_fold*.json")):
    j = json.loads(f.read_text())
    for name in ("Wavelet-ANN", "1D-CNN", "Wavelet-GRU", "Wavelet-RF", "Proposed LSTM"):
        for r in j[name]["hybrid"]:
            if r["trace"] not in bad:
                inst[name if name != "Proposed LSTM" else "LSTM (tuned, B2)"][(r["seed"], r["fold"], r["trace"])] = r
inst["Key (claim-C run)"] = {}
for f in sorted((OUT / "full" / "key_hybrid").glob("cv_seed*_fold*.json")):
    for r in json.loads(f.read_text())["hybrid"]:
        inst["Key (claim-C run)"][(r["seed"], r["fold"], r["trace"])] = r
order = ["1D-CNN", "Wavelet-GRU", "Wavelet-ANN", "Key (claim-C run)", "Wavelet-RF", "LSTM (tuned, B2)"]
tests = []
for name in order:
    for metric, flag in (("dependability", 1), ("security", 0)):
        ks = [k for k in inst[name] if k in tuned and not tuned[k]["undetectable"] and not inst[name][k].get("undetectable") and tuned[k]["should_trip"] == flag]
        a = np.array([bool(tuned[k]["correct"]) for k in ks]); b = np.array([bool(inst[name][k]["correct"]) for k in ks])
        n10, n01, p = N5.mcnemar(a, b)
        per_seed = {s: float(100 * (b[[i for i, k in enumerate(ks) if k[0] == s]].mean() - a[[i for i, k in enumerate(ks) if k[0] == s]].mean())) for s in cv.SEEDS}
        tests.append({"instance": name, "metric": metric, "n": len(ks), "tuned_harmonic_pct": 100 * a.mean(), "instance_pct": 100 * b.mean(), "diff_pt": 100 * (b.mean() - a.mean()),
                      "harmonic_only": n10, "instance_only": n01, "p": p, "per_seed": per_seed})
n6c = json.loads((OUT / "n6c_tuned_harmonic.json").read_text())["tests"]
p_all = [t["p"] for t in tests] + [t["p"] for t in n6c]
adj = N5.holm(np.array(p_all))
for t, q in zip(tests, adj[:len(tests)]):
    t["p_holm16"] = float(q)
    ds = list(t["per_seed"].values()); t["sign_stable"] = all(v > 0 for v in ds) or all(v < 0 for v in ds) or all(v == 0 for v in ds)
L = ["POST-HOC (added after N6c): architecture instances (hybrid mode) vs the validation-tuned harmonic 87T (91.18 / 99.07 on this set), exact McNemar on (seed, fold, trace), Holm over 16 tests (12 here + 4 of N6c)",
     f"{'instance':20s} {'metric':13s} {'n':>5s} {'harm %':>7s} {'inst %':>7s} {'diff pt':>8s} {'harm-only':>9s} {'inst-only':>9s} {'p':>9s} {'p_Holm16':>9s}  per-seed"]
for t in tests:
    L.append(f"{t['instance']:20s} {t['metric']:13s} {t['n']:5d} {t['tuned_harmonic_pct']:7.2f} {t['instance_pct']:7.2f} {t['diff_pt']:+8.2f} {t['harmonic_only']:9d} {t['instance_only']:9d} {t['p']:9.2e} {t['p_holm16']:9.2e}"
             + (" *" if t["p_holm16"] < 0.05 else "") + "  " + " ".join(f"{v:+.2f}" for v in t["per_seed"].values()) + ("" if t["sign_stable"] else "  unstable"))
dep = [t for t in tests if t["metric"] == "dependability"]; sec = [t for t in tests if t["metric"] == "security"]
sig_up = [t for t in dep if t["p_holm16"] < 0.05 and t["diff_pt"] > 0]
L += ["", f"dependability: {len(sig_up)} of {len(dep)} instances significantly higher than the tuned harmonic 87T after Holm-16; range of the differences over all {len(dep)} instances {min(t['diff_pt'] for t in dep):+.2f} to {max(t['diff_pt'] for t in dep):+.2f} pt; "
      f"over the significant ones {min(t['diff_pt'] for t in sig_up):+.2f} to {max(t['diff_pt'] for t in sig_up):+.2f} pt" if sig_up else "no instance significantly higher",
      f"security: instances significantly different from the tuned harmonic 87T: " + (", ".join(f"{t['instance']} {t['diff_pt']:+.2f} pt" for t in sec if t["p_holm16"] < 0.05) or "none") + f"; range of the differences {min(t['diff_pt'] for t in sec):+.2f} to {max(t['diff_pt'] for t in sec):+.2f} pt"]
(OUT / "n8a_instances_vs_tuned_harmonic.txt").write_text("\n".join(L)); (OUT / "n8a_instances_vs_tuned_harmonic.json").write_text(json.dumps(tests, indent=1)); print("\n".join(L))
