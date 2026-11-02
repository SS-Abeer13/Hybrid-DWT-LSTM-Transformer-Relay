"""D-N4: native AND like-for-like (mode b) results of one reproduction, in one pass over the fitted models.

usage: run_full_eval.py <method> [cv|final|both]
  cv    3 seeds x 5 folds on the plant-A common set (same folds as the proposed model): native rows + mode-b rows per fold, threshold tuned on the fold's validation traces
  final one model on 85 % of the detectable plant-A traces (stratified, seed 20261021: the recipe of the proposed final model), 15 % validation -> threshold; scored ONCE on
        the plant-A OOD set and on the plant-B main set (zero-shot: logic and threshold frozen)
Output: runs/20261101_v5_benchmark_fair/full/<method>/{cv_seed*_fold*.json, final_<set>.json}   (auto-resume per fold)
"""
from __future__ import annotations

import json
import pickle
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from sklearn.model_selection import train_test_split  # noqa: E402

from baselines import abdusalam2022_dwt_omp_ga as AB  # noqa: E402
from baselines import afrasiabi2020_acnn as AF  # noqa: E402
from baselines import alhamd2024_wavelet_lstm as AL  # noqa: E402
from baselines import common as C  # noqa: E402
from baselines import cv, modeb  # noqa: E402
from baselines import key2025_comdnn_disdnn as KE  # noqa: E402
from baselines import ngaopitakkul2006_dwt_bpnn as NG  # noqa: E402
from baselines import simoes2021_rtbswt_svm as SI  # noqa: E402

OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
FACTORY = {
    "simoes_grid": lambda s, plant: SI.SimoesMethod("grid", plant),
    "simoes_published": lambda s, plant: SI.SimoesMethod("published", plant),
    "afrasiabi": lambda s, plant: AF.AcnnMethod(plant, compensate=True),
    "afrasiabi_nocomp": lambda s, plant: AF.AcnnMethod(plant, compensate=False),
    "key": lambda s, plant: KE.KeyMethod(plant, n_configs=12),
    "ngaopitakkul": lambda s, plant: NG.NgaopitakkulMethod(plant, seed=s),
    "abdusalam_ba_svm": lambda s, plant: AB.AbdusalamMethod("BA", "SVM", plant=plant, seed=s),
    "alhamd": lambda s, plant: AL.AlhamdMethod(plant, seed=s),
}


def hs_key(meta):
    return (meta["source_file"], int(meta["source_index"]))


def cv_procs(name, m0, metas, pos):
    procs = {}
    if name.startswith("simoes"):
        E = np.load(OUT / "cache" / "simoes_E_plantA.npy", mmap_mode="r"); done = np.load(OUT / "cache" / "simoes_E_plantA_done.npy")
        return {i: {"E": np.asarray(E[i])} for i in range(len(metas)) if done[i]}
    feats = pickle.load(open(OUT / "cache" / "abdusalam_feats.pkl", "rb")) if name.startswith("abdusalam") else None
    for tr in C.iter_hr(C.PLANT_A_MAIN):
        tid = pos[(tr["src"], tr["index"])]
        procs[tid] = m0.prepare(tr)
        if feats is not None:
            procs[tid]["fc"] = feats.get(tid, {})
    return procs


def set_items(name, runs, cache, plant, seed):
    """Prepared evaluation items of an external set (OOD plant A, plant B main)."""
    meta = C.load_meta(cache)
    hs = C.load_highset_times(cache)
    mP = FACTORY[name](seed, plant)
    items = []
    for tr in C.iter_hr(runs, cache):
        md = tr["meta"]
        items.append({"id": len(items), "meta": md, "proc": mP.prepare(tr), "hs": hs.get((md["source_file"], int(md["source_index"])))})
    if name.startswith("abdusalam"):
        from multiprocessing import Pool
        jobs = [(i["id"], i["meta"], i["proc"]["d"], i["proc"]["picked"]) for i in items]
        with Pool(8) as pool:
            for tid, fc in pool.imap_unordered(AB.compute_decision_features, jobs, chunksize=4):
                items[tid]["proc"]["fc"] = fc
    return items


def evaluate(m, tr_items, thr):
    nat, mb = [], []
    for it in tr_items:
        t_nat = m.trip_time(it["proc"])
        times, scores = m.score_stream(it["proc"])
        t_b = modeb.trip_time(times, scores, thr, m.STEP_S, m.EVENT_BASED, it["hs"])
        nat.append(C.score_row(it["meta"], t_nat, it["id"]))
        mb.append(C.score_row(it["meta"], t_b, it["id"]))
    return nat, mb


def val_streams(m, va_items):
    return [{"id": it["id"], "meta": it["meta"], "stream": m.score_stream(it["proc"]), "step": m.STEP_S, "event": m.EVENT_BASED, "hs": it["hs"]} for it in va_items]


def main():
    name = sys.argv[1]
    stage = sys.argv[2] if len(sys.argv) > 2 else "both"
    d = OUT / "full" / name
    d.mkdir(parents=True, exist_ok=True)
    metas, pos = cv.trace_index()
    cv.check_folds_match_reference(metas)
    hs_main = C.load_highset_times(C.CACHE_A_MAIN)
    m0 = FACTORY[name](0, "A")
    t0 = time.time()
    procs = cv_procs(name, m0, metas, pos)
    print(f"prepared {len(procs)} traces in {time.time()-t0:.0f}s", flush=True)
    items = lambda ids: [{"id": i, "meta": metas[i], "proc": procs[i], "hs": hs_main.get(hs_key(metas[i]))} for i in ids if i in procs]  # noqa: E731

    if stage in ("cv", "both"):
        for seed in cv.SEEDS:
            for k, tr, va, te in cv.folds(metas, seed):
                f = d / f"cv_seed{seed}_fold{k}.json"
                if f.is_file():
                    print(f"seed {seed} fold {k}: cached", flush=True)
                    continue
                t1 = time.time()
                m = FACTORY[name](seed + k, "A")
                m.fit(items(tr), items(va), seed + k)
                thr, table = modeb.tune(val_streams(m, items(va)))
                nat, mb = evaluate(m, items(te), thr)
                for r in nat + mb:
                    r["seed"], r["fold"] = seed, k
                sn, sb = C.summarise(nat), C.summarise(mb)
                f.write_text(json.dumps({"native": nat, "modeb": mb, "thr": thr, "val_table": table}, default=float))
                print(f"seed {seed} fold {k}: native {sn['dependability_pct']:.1f}/{sn['security_pct']:.1f} | mode b (thr {thr}) {sb['dependability_pct']:.1f}/{sb['security_pct']:.1f} | {time.time()-t1:.0f}s", flush=True)

    if stage in ("final", "both"):
        # final model: 85 / 15 split of the detectable traces (recipe of the proposed final model)
        names = np.array([m_["scenarioName"] for m_ in metas])
        trainable = [i for i in range(len(metas)) if not metas[i]["undetectable"] and i in procs]
        st = names[trainable].copy()
        for c, n_c in zip(*np.unique(st, return_counts=True)):
            if n_c < 4:
                st[st == c] = "_small"
        tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=cv.SEEDS[0])
        m = FACTORY[name](cv.SEEDS[0], "A")
        m.fit(items(sorted(tr.tolist())), items(sorted(va.tolist())), cv.SEEDS[0])
        thr, table = modeb.tune(val_streams(m, items(sorted(va.tolist()))))
        print(f"final model fitted; mode-b threshold {thr}", flush=True)
        for label, runs, cache, plant in (("plantA_OOD", C.PLANT_A_OOD, C.CACHE_A_OOD, "A"), ("plantB_main", C.PLANT_B_MAIN, C.CACHE_B_MAIN, "B")):
            f = d / f"final_{label}.json"
            if f.is_file():
                continue
            its = set_items(name, runs, cache, plant, cv.SEEDS[0])
            nat, mb = evaluate(m, its, thr)
            sn, sb = C.summarise(nat), C.summarise(mb)
            f.write_text(json.dumps({"native": nat, "modeb": mb, "thr": thr, "val_table": table}, default=float))
            print(f"{label}: {len(its)} traces | native {sn['dependability_pct']:.1f}/{sn['security_pct']:.1f} | mode b {sb['dependability_pct']:.1f}/{sb['security_pct']:.1f}", flush=True)


if __name__ == "__main__":
    main()
