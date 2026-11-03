"""D-lat: Alhamd latency with the configuration actually trained (spec budget: per-fold 12-configuration search), not the largest of the search space.
The per-fold chosen configurations were not stored by run_full_eval.py, so the two fits that matter are repeated here (seed 20261021 fold 1 and the final-model split;
same seeds, GPU) and the configuration each search selects is timed: features of the 5 new samples + BiLSTM on 60 x 48, single thread CPU, 500 timed calls, budget 1,667 us.
Output: runs/20261101_v5_benchmark_fair/latency_alhamd_trained.txt/.json   (run on an idle machine; fits first, timing last)"""
import json, sys, time, warnings
from pathlib import Path
import numpy as np, torch
from sklearn.model_selection import train_test_split
warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models")); sys.path.insert(0, str(ROOT / "tools"))
import run_full_eval as RF
from baselines import cv, alhamd2024_wavelet_lstm as AL
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
metas, pos = cv.trace_index()
m0 = RF.FACTORY["alhamd"](0, "A")
procs = RF.cv_procs("alhamd", m0, metas, pos)
items = lambda ids: [{"id": i, "meta": metas[i], "proc": procs[i]} for i in ids if i in procs]
chosen = {}
seed = cv.SEEDS[0]
k, tr, va, te = next(iter(cv.folds(metas, seed)))
m = AL.AlhamdMethod("A", seed=seed + k); m.fit(items(tr), items(va), seed + k)
chosen["seed20261021_fold1"] = {"cfg": {k_: (v if not isinstance(v, (np.floating, np.integer)) else v.item()) for k_, v in m.cfg.items()}, "search": [x for x in m.log if "final" not in x]}
names = np.array([x["scenarioName"] for x in metas]); trainable = [i for i in range(len(metas)) if not metas[i]["undetectable"] and i in procs]
st = names[trainable].copy()
for c, n_c in zip(*np.unique(st, return_counts=True)):
    if n_c < 4: st[st == c] = "_small"
tr2, va2 = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=seed)
m2 = AL.AlhamdMethod("A", seed=seed); m2.fit(items(sorted(tr2.tolist())), items(sorted(va2.tolist())), seed)
chosen["final_model"] = {"cfg": {k_: (v if not isinstance(v, (np.floating, np.integer)) else v.item()) for k_, v in m2.cfg.items()}, "search": [x for x in m2.log if "final" not in x]}
del procs; torch.set_num_threads(1)
rng = np.random.RandomState(0); newx = rng.randn(16, 3).astype(float); seg = torch.from_numpy(rng.randn(1, 60, 48).astype(np.float32))
def timeit(cfg, n=500, warm=50):
    net = AL.BiLSTM(int(cfg["hidden"]), int(cfg["layers"]), float(cfg["dropout"])).eval()
    def f():
        for p in range(3): AL.rtbswt_both(newx[:, p])
        with torch.no_grad(): net(seg)
    for _ in range(warm): f()
    t = np.empty(n)
    for i in range(n):
        a = time.perf_counter_ns(); f(); t[i] = (time.perf_counter_ns() - a) / 1e3
    return {"median_us": float(np.median(t)), "p99_us": float(np.percentile(t, 99)), "budget_us": AL.STEP / AL.FS * 1e6}
res = {k_: {**v, "latency": timeit(v["cfg"])} for k_, v in chosen.items()}
res["largest_search_space_config (earlier measurement)"] = {"cfg": {"hidden": 128, "layers": 2, "dropout": 0.1}, "latency": timeit({"hidden": 128, "layers": 2, "dropout": 0.1})}
L = ["Alhamd et al. latency per decision (single thread CPU, features of 5 new samples + BiLSTM 60x48), budget 1,667 us"]
for k_, v in res.items():
    L.append(f"{k_:52s} {v['cfg']}  median {v['latency']['median_us']:.0f} us, p99 {v['latency']['p99_us']:.0f} us -> " + ("real-time" if v['latency']['median_us'] <= v['latency']['budget_us'] else "NOT real-time in this implementation"))
(OUT / "latency_alhamd_trained.json").write_text(json.dumps(res, indent=1, default=str)); (OUT / "latency_alhamd_trained.txt").write_text("\n".join(L)); print("\n".join(L))
