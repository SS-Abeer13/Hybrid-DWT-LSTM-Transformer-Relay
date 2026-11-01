"""N2: Simoes detector factor chosen by the pre-set rule on the validation traces of every CV fold (3 seeds x 5 folds), grid {5,10,15,20,30,50,100}.
Output: runs/20261101_v5_benchmark_fair/n2_simoes_factor.json / .txt"""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import cv, simoes2021_rtbswt_svm as S
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
metas, _ = cv.trace_index()
E = np.load(OUT / "cache" / "simoes_E_plantA.npy", mmap_mode="r"); done = np.load(OUT / "cache" / "simoes_E_plantA_done.npy")
res = []
for seed in cv.SEEDS:
    for k, tr, va, te in cv.folds(metas, seed):
        val = [{"meta": metas[i], "proc": {"E": np.asarray(E[i])}} for i in va if done[i]]
        f, rep = S.SimoesMethod.select_factor(val)
        res.append({"seed": seed, "fold": k, "n_val": len(val), **rep})
        print(seed, k, f, rep["flag"], flush=True)
(OUT / "n2_simoes_factor.json").write_text(json.dumps(res, indent=1, default=float))
L = [f"N2 Simoes detector factor, rule on validation traces per fold; {len(res)} fold-models", "chosen factor counts: " + str(dict(Counter(r["chosen"] for r in res))), "flags: " + str(dict(Counter(r["flag"] for r in res))), "",
     "mean over folds per factor: spurious firings per Normal/over-excitation trace | event detection rate (fault, inrush, external traces)"]
for f in S.FACTORS:
    sp = np.mean([r["grid"][str(f)]["spurious_per_trace"] if str(f) in r["grid"] else r["grid"][f]["spurious_per_trace"] for r in res])
    dr = np.mean([r["grid"][str(f)]["detection_rate"] if str(f) in r["grid"] else r["grid"][f]["detection_rate"] for r in res])
    L.append(f"  factor {f:5.0f}: {sp:7.2f} | {100*dr:5.1f} %")
(OUT / "n2_simoes_factor.txt").write_text("\n".join(L)); print("\n".join(L))
