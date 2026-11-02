"""N4: 3 seeds x 5 folds on the plant-A common set for the Afrasiabi (with / without Hajipour compensation) and Key reproductions, native decision logic.
usage: run_nn_cv.py <afrasiabi|afrasiabi_nocomp|key> [seed_index ...]    output: runs/20261101_v5_benchmark_fair/<name>/rows_seed*_fold*.json (auto-resume per fold)"""
import json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C, cv
from baselines import afrasiabi2020_acnn as A, key2025_comdnn_disdnn as K, ngaopitakkul2006_dwt_bpnn as N, alhamd2024_wavelet_lstm as H
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
name = sys.argv[1]
seeds = [cv.SEEDS[int(i)] for i in sys.argv[2:]] or cv.SEEDS
metas, pos = cv.trace_index()
cv.check_folds_match_reference(metas)
make = {"afrasiabi": lambda s, k: A.AcnnMethod("A", compensate=True), "afrasiabi_nocomp": lambda s, k: A.AcnnMethod("A", compensate=False),
        "key": lambda s, k: K.KeyMethod("A", n_configs=12), "ngaopitakkul": lambda s, k: N.NgaopitakkulMethod("A", seed=s + k), "alhamd": lambda s, k: H.AlhamdMethod("A", seed=s + k)}[name]
m0 = make(0, 0)
cache = OUT / "cache" / f"{name}_procs.npz"
t0 = time.time()
procs = {}
for tr in C.iter_hr(C.PLANT_A_MAIN):
    procs[pos[(tr["src"], tr["index"])]] = m0.prepare(tr)
print(f"prepared {len(procs)} traces in {time.time()-t0:.0f}s", flush=True)
d = OUT / name; d.mkdir(parents=True, exist_ok=True)
rows = cv.run_cv(make, procs, metas, seeds=seeds, out_dir=d, tag="rows", log=lambda s: print(s, flush=True))
s = C.summarise(rows)
(d / f"summary_{'_'.join(map(str, seeds))}.json").write_text(json.dumps(s, indent=1, default=float))
print(name, "dep", s["dependability_pct"], "sec", s["security_pct"], flush=True)
