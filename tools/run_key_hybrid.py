"""Claim-C extra evaluation (BENCHMARK_FAIRNESS_PLAN.md, D-N5b decision table, row 1): "hybrid with Key".

The identical dual-path logic of the proposed hybrid (lstm_models/train_trace_split.relay_report via benchmark_literature_models.rows_for / tune_variant:
87T vote AND confirmed classifier output >= AI_Threshold, OR confirmed output >= AI_Solo_Threshold, OR high-set; dwell 20 windows of the relay's 1,600 Hz;
plateau-rule thresholds tuned on the fold's validation traces). Only the classifier output changes: the Key et al. Dis-DNN internal-fault probability (3.2 kHz stream,
retrained per fold exactly as in the Key run of run_full_eval.py: same seeds, 12-configuration budget) is sampled at the relay's decision instants.
usage: run_key_hybrid.py cv <seed index 0-2> | final       Output: runs/20261101_v5_benchmark_fair/full/key_hybrid/
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "lstm_models"))
import run_b2_search as B2  # noqa: E402  (trace loading + T globals)
import benchmark_literature_models as B  # noqa: E402
import train_trace_split as T  # noqa: E402
import run_full_eval as RF  # noqa: E402
from baselines import common as C  # noqa: E402
from baselines import cv  # noqa: E402
from baselines import key2025_comdnn_disdnn as KE  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

OUT = ROOT / "runs" / "20261101_v5_benchmark_fair" / "full" / "key_hybrid"
DWT_ROWS = 32


def window_probs(key_stream, n_samples: int) -> np.ndarray:
    """Key probability stream (times in s, scores) -> one value per relay window (decision sample ds / 1,600 Hz, latest Key decision at or before it)."""
    times, p = key_stream
    n_w = (n_samples - DWT_ROWS) - T.SEQ + 1
    ds = np.arange(n_w) + T.SEQ - 1 + T.DWT_WINDOW
    idx = np.searchsorted(times, ds / C.FS_RELAY, side="right") - 1
    out = np.where(idx >= 0, p[np.clip(idx, 0, len(p) - 1)], 0.0)
    return out.astype(np.float32)


def run_rows(m, traces_cache, ids_to_proc, thr_ids, test_ids):
    """ids: positions in traces_cache; ids_to_proc: position -> proc."""
    probs = {i: window_probs(m.score_stream(ids_to_proc[i]), len(traces_cache[i]["vote87"])) for i in set(thr_ids) | set(test_ids)}
    thr, solo = B.tune_variant(traces_cache, thr_ids, probs, "Hybrid + AI-alone path")
    rows = B.rows_for(traces_cache, test_ids, probs, "Hybrid + AI-alone path", thr, solo)
    return rows, thr, solo


def main():
    mode = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    traces = B2.load_traces()
    metas, pos = cv.trace_index()
    m0 = RF.FACTORY["key"](0, "A")
    if mode == "cv":
        seed = cv.SEEDS[int(sys.argv[2])]
        procs = RF.cv_procs("key", m0, metas, pos)
        for k, tr, va, te in cv.folds(metas, seed):
            f = OUT / f"cv_seed{seed}_fold{k}.json"
            if f.is_file():
                continue
            t0 = time.time()
            ok = lambda ids: [i for i in ids if i in procs]  # noqa: E731
            m = RF.FACTORY["key"](seed + k, "A")
            m.fit([{"id": i, "meta": metas[i], "proc": procs[i]} for i in ok(tr)], [{"id": i, "meta": metas[i], "proc": procs[i]} for i in ok(va)], seed + k)
            rows, thr, solo = run_rows(m, traces, procs, ok(va), ok(te))
            for r in rows:
                r["seed"], r["fold"] = seed, k
            f.write_text(json.dumps({"hybrid": rows, "thr": thr, "solo": solo}, default=float))
            s = C.summarise(rows)
            print(f"seed {seed} fold {k}: hybrid with Key {s['dependability_pct']:.1f}/{s['security_pct']:.1f} (AI {thr}, solo {solo}) {time.time()-t0:.0f}s", flush=True)
        return
    # final model + OOD (once) + plant B (zero-shot, thresholds frozen from the final validation split)
    procs = RF.cv_procs("key", m0, metas, pos)
    names = np.array([x["scenarioName"] for x in metas])
    trainable = [i for i in range(len(metas)) if not metas[i]["undetectable"] and i in procs]
    st = names[trainable].copy()
    for c, n_c in zip(*np.unique(st, return_counts=True)):
        if n_c < 4:
            st[st == c] = "_small"
    tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=cv.SEEDS[0])
    tr, va = sorted(tr.tolist()), sorted(va.tolist())
    m = RF.FACTORY["key"](cv.SEEDS[0], "A")
    m.fit([{"id": i, "meta": metas[i], "proc": procs[i]} for i in tr], [{"id": i, "meta": metas[i], "proc": procs[i]} for i in va], cv.SEEDS[0])
    probs_va = {i: window_probs(m.score_stream(procs[i]), len(traces[i]["vote87"])) for i in va}
    thr, solo = B.tune_variant(traces, va, probs_va, "Hybrid + AI-alone path")
    print(f"final model fitted; thresholds AI {thr}, solo {solo}", flush=True)
    for label, runs, cache, plant in (("plantA_OOD", C.PLANT_A_OOD, C.CACHE_A_OOD, "A"), ("plantB_main", C.PLANT_B_MAIN, C.CACHE_B_MAIN, "B")):
        f = OUT / f"final_{label}.json"
        if f.is_file():
            continue
        tc = [t for t in np.load(cache, allow_pickle=True)["traces"]]
        for t in tc:
            t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < B.MIN_FAULT_PU)
        lookup = {(t["source_file"], int(t["source_index"])): i for i, t in enumerate(tc)}
        mP = RF.FACTORY["key"](cv.SEEDS[0], plant)
        ids, pr = [], {}
        for tr_ in C.iter_hr(runs, cache):
            i = lookup[(tr_["meta"]["source_file"], int(tr_["meta"]["source_index"]))]
            ids.append(i); pr[i] = mP.prepare(tr_)
        probs = {i: window_probs(m.score_stream(pr[i]), len(tc[i]["vote87"])) for i in ids}
        rows = B.rows_for(tc, sorted(ids), probs, "Hybrid + AI-alone path", thr, solo)
        # which path trips first (per-path counts of the false trips, same logic as tools/plantb_trip_path_v5.py): high-set / 87T-gated classifier / classifier-alone (solo)
        paths = {"false_trips": {"highset": 0, "gate": 0, "solo": 0}, "faults": {"highset": 0, "gate": 0, "solo": 0}}
        for r in rows:
            i = r["trace"]; t = tc[i]
            if not r["tripped"] or r["undetectable"]:
                continue
            hs = int(np.argmax(t["highset"])) if np.asarray(t["highset"]).any() else None
            g = T.relay_decision(probs[i], thr, t["vote87"], None, None)
            first = "highset" if (hs is not None and r["trip_sample"] == hs and (g < 0 or hs <= g)) else ("gate" if g >= 0 and r["trip_sample"] == g else "solo")
            paths["faults" if r["should_trip"] else "false_trips"][first] += 1
        gated = B.rows_for(tc, sorted(ids), probs, "Hybrid (87T gate)", thr, None)       # counterfactual: AI-alone path off, same AI threshold
        f.write_text(json.dumps({"hybrid": rows, "thr": thr, "solo": solo, "paths": paths, "gated_only": gated}, default=float))
        print(label, "paths", paths, flush=True)
        s = C.summarise(rows)
        print(f"{label}: {len(ids)} traces | hybrid with Key {s['dependability_pct']:.1f}/{s['security_pct']:.1f}", flush=True)


if __name__ == "__main__":
    main()
