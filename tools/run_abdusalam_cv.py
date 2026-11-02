"""N4 (Abdusalam et al.): 3 seeds x 5 folds on the plant-A common set; variants BA+SVM (main row), BA+KNN, BA+ANN, GA+SVM, GA+KNN, GA+ANN, native logic.
Window features come from runs/.../cache/abdusalam_feats.pkl (tools/cache_abdusalam_feats.py). Output: runs/20261101_v5_benchmark_fair/abdusalam_<sel>_<clf>/"""
import json, pickle, sys, time, warnings
from pathlib import Path
import numpy as np
warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C, cv, abdusalam2022_dwt_omp_ga as A
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
metas, pos = cv.trace_index()
cv.check_folds_match_reference(metas)
feats = pickle.load(open(OUT / "cache" / "abdusalam_feats.pkl", "rb"))
procs = {}
for tr in C.iter_hr(C.PLANT_A_MAIN):
    p = A.prepare(tr); tid = pos[(tr["src"], tr["index"])]
    p["fc"] = feats.get(tid, {}); procs[tid] = p
print("prepared", len(procs), flush=True)
variants = [v.split("_") for v in (sys.argv[1:] or ["BA_SVM", "BA_KNN", "BA_ANN", "GA_SVM", "GA_KNN", "GA_ANN"])]
for sel, clf in variants:
    d = OUT / f"abdusalam_{sel.lower()}_{clf.lower()}"; d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows = cv.run_cv(lambda s, k: A.AbdusalamMethod(sel, clf, seed=s + k), procs, metas, out_dir=d, tag="rows", log=lambda s: print(sel, clf, s, flush=True))
    s = C.summarise(rows)
    print(sel, clf, "dep", s["dependability_pct"], "sec", s["security_pct"], f"{time.time()-t0:.0f}s", flush=True)
