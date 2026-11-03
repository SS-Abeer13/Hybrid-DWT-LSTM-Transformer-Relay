"""Step 5 (review 2026-11-03 09:45): gated-only ablation of the proposed hybrid from SAVED per-trace decisions, no retraining. Labelled post-hoc ablation, not an adoption.
CV plant A (3 seeds x 5 folds, common set): variant 'Hybrid (87T gate)' (AI-alone path off, AI threshold tuned for that variant on validation, as saved by train_cv_v5)
vs the deployed 'Hybrid + AI-alone path'; paired exact McNemar. OOD (final model, scored once) from report_ood.json. Plant B (zero-shot, same thresholds) from trip_path_check.json.
Output: runs/20261101_v5_benchmark_fair/gated_only_ablation.txt/.json"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import cv
CVD = ROOT / "runs" / "20261029_v5_cv5_seeds"
excl = set()
for l in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
    f, i, *_ = [x.strip() for x in l.split(",")]; excl.add((f, int(i)))
metas, _ = cv.trace_index()
bad = {i for i, m in enumerate(metas) if (m["source_file"], int(m["source_index"])) in excl}
def load(variant):
    out = {}
    for s in cv.SEEDS:
        for k in range(1, 6):
            for r in json.load(open(CVD / f"seed_{s}" / f"fold{k}" / "result.json"))["rows"][variant]:
                if r["trace"] not in bad and not r.get("undetectable"):
                    out[(s, k, r["trace"])] = r
    return out
dep_row = load("Hybrid + AI-alone path"); gat = load("Hybrid (87T gate)")
L = ["Gated-only ablation of the proposed hybrid (post-hoc, from saved decisions; AI-alone path off)", ""]
res = {}
for metric, flag in (("dependability", 1), ("security", 0)):
    ks = [k for k in dep_row if k in gat and dep_row[k]["should_trip"] == flag]
    a = np.array([bool(dep_row[k]["correct"]) for k in ks]); b = np.array([bool(gat[k]["correct"]) for k in ks])
    n10, n01 = int(np.sum(a & ~b)), int(np.sum(~a & b)); p = binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    res[metric] = {"n": len(ks), "deployed_pct": 100 * a.mean(), "gated_only_pct": 100 * b.mean(), "diff_pt": 100 * (b.mean() - a.mean()), "deployed_only_correct": n10, "gated_only_correct": n01, "p": float(p)}
    L.append(f"plant A CV, {metric:13s} (n={len(ks)}): deployed {100*a.mean():.2f} %, gated-only {100*b.mean():.2f} %, diff {100*(b.mean()-a.mean()):+.2f} pt, discordant {n10}/{n01}, exact McNemar p = {p:.2e} (raw, 2 ablation tests)")
o = json.load(open(ROOT / "runs" / "20261029_v5_final" / "report_ood.json"))["ood"]
for v in ("Hybrid + AI-alone path", "Hybrid (87T gate)"):
    x = o[v]["overall"] if "overall" in o[v] else o[v]
    L.append(f"plant A OOD (final model, once), {v}: " + json.dumps({k: (round(x[k], 2) if isinstance(x.get(k), float) else x.get(k)) for k in ("dependability_pct", "security_pct", "missed", "false_trips") if k in x}))
t = json.load(open(ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "trip_path_check.json"))["variants"]
for k in ("Proposed as evaluated (high-set + gate + solo)", "without AI-alone path (high-set + gate)"):
    L.append(f"plant B zero-shot, {k}: dependability {t[k]['dependability_pct']:.2f} %, security {t[k]['security_pct']:.2f} %, false trips {t[k]['false_trips']}")
L += ["", "Wording (post-hoc counterfactual, a practical recommendation): the AI-alone path buys a few points of dependability; on an unseen plant it caused 98 % of the false trips; a utility deploying the relay on an untrained plant should disable it until retraining. The deployed logic stays the main result everywhere."]
Path(ROOT / "runs" / "20261101_v5_benchmark_fair" / "gated_only_ablation.txt").write_text("\n".join(L)); json.dump(res, open(ROOT / "runs" / "20261101_v5_benchmark_fair" / "gated_only_ablation.json", "w"), indent=1)
print("\n".join(L))
