"""N4 (Simoes et al.): 3 seeds x 5 folds on the plant-A common set, modes 'published' (C=500, gamma=100) and 'grid'. Native decision logic of the paper
(IF -> trip; SVM2 evolving fault -> trip; after a trip blocked). Output: runs/20261101_v5_benchmark_fair/simoes_<mode>/rows.json + summary."""
import json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C, cv, simoes2021_rtbswt_svm as S
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
metas, _ = cv.trace_index()
cv.check_folds_match_reference(metas)
E = np.load(OUT / "cache" / "simoes_E_plantA.npy", mmap_mode="r"); done = np.load(OUT / "cache" / "simoes_E_plantA_done.npy")
procs = {i: {"E": np.asarray(E[i])} for i in range(len(metas)) if done[i]}
for mode in sys.argv[1:] or ("published", "grid"):
    d = OUT / f"simoes_{mode}"; d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows = cv.run_cv(lambda s, k: S.SimoesMethod(mode), procs, metas, out_dir=d, tag="rows")
    s = C.summarise(rows)
    (d / "summary.json").write_text(json.dumps(s, indent=1, default=float))
    print(mode, "dep", s["dependability_pct"], "sec", s["security_pct"], f"{time.time()-t0:.0f}s", flush=True)
