"""Feature windows of the Abdusalam et al. reproduction for every common-set plant-A trace, computed once in parallel (features do not depend on the fold).
Output: runs/20261101_v5_benchmark_fair/cache/abdusalam_feats.pkl  {trace position: {window end: 288 features}}; auto-resumable per chunk."""
import pickle, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C, cv, abdusalam2022_dwt_omp_ga as A

def jobs(pos, metas, done):
    for tr in C.iter_hr(C.PLANT_A_MAIN):
        tid = pos[(tr["src"], tr["index"])]
        if tid in done:
            continue
        p = A.prepare(tr)
        yield tid, metas[tid], p["d"], p["picked"]

if __name__ == "__main__":
    out = ROOT / "runs" / "20261101_v5_benchmark_fair" / "cache" / "abdusalam_feats.pkl"
    metas, pos = cv.trace_index()
    cache = pickle.load(open(out, "rb")) if out.exists() else {}
    print("already", len(cache), flush=True)
    t0 = time.time()
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 8) as pool:
        for n, (tid, fc) in enumerate(pool.imap_unordered(A.compute_trace_features, jobs(pos, metas, set(cache)), chunksize=4), 1):
            cache[tid] = fc
            if n % 200 == 0:
                pickle.dump(cache, open(out, "wb")); print(n, len(cache), f"{time.time()-t0:.0f}s", flush=True)
    pickle.dump(cache, open(out, "wb")); print("done", len(cache), f"{time.time()-t0:.0f}s")
