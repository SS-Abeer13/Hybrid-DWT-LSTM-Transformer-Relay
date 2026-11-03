"""Cross-validation harness shared by the faithful reproductions: the SAME folds, seeds and inner validation split as lstm_models/train_cv_v5.py
(StratifiedKFold on the scenario names of the cached trace list, train_test_split 15 % of the trainable training traces with random_state seed + fold),
so that every method sees exactly the traces of the proposed relay and the rows can be paired on (seed, fold, trace).

A method is any object with:
    prepare(tr_hr)  -> proc            (heavy per-trace processing of the 20 kHz data; cacheable)
    fit(items_train, items_val, seed)  (items = list of dicts {"meta", "proc"})
    trip_time(proc) -> seconds or None (native decision logic)
Rows are produced with common.score_row; 'trace' is the index in the cached trace list (same as train_cv_v5 rows).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split

from . import common as C

SEEDS = (20261021, 20261022, 20261023)


def trace_index() -> tuple[list[dict], dict]:
    """The cached trace list of the CV (same order as train_cv_v5) and a map (source file, source index) -> position."""
    if not C.CACHE_A_MAIN.is_file():      # the 250 MB feature cache is not on GitHub: use the light metadata file written from it
        z = json.loads((C.ROOT / "runs" / "20261101_v5_benchmark_fair" / "trace_metas_plantA.json").read_text(encoding="utf-8"))
    else:
        z = np.load(C.CACHE_A_MAIN, allow_pickle=True)["traces"]
    metas = []
    for t in z:
        m = {k: v for k, v in t.items() if k not in ("features", "vote87", "highset")}
        m["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < C.MIN_FAULT_PU)
        m["onset_time"] = (t["onset"] / C.FS_RELAY) if t["onset"] >= 0 else None
        metas.append(m)
    pos = {(m["source_file"], int(m["source_index"])): i for i, m in enumerate(metas)}
    return metas, pos


def folds(metas: list[dict], seed: int, n_folds: int = 5):
    """Yield (fold k, train ids, val ids, test ids) exactly as run_single_seed_cv builds them."""
    names = np.array([m["scenarioName"] for m in metas])
    idx = np.arange(len(metas))
    strat = names.copy()
    for c, n in zip(*np.unique(names, return_counts=True)):
        if n < n_folds:
            strat[names == c] = "_small"
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    for k, (tr_all, te) in enumerate(skf.split(idx, strat), 1):
        trainable = [i for i in tr_all if not metas[i]["undetectable"]]
        st = strat[trainable].copy()
        for c, n_c in zip(*np.unique(st, return_counts=True)):
            if n_c < 4:
                st[st == c] = "_small"
        if (st == "_small").sum() == 1:
            st[st == "_small"] = st[0]
        tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=seed + k)
        yield k, sorted(tr.tolist()), sorted(va.tolist()), sorted(te.tolist())


def check_folds_match_reference(metas: list[dict], seed: int = SEEDS[0], run: str = "runs/20261029_v5_cv5_seeds") -> None:
    """The test ids of every fold must equal the 'trace' ids of the saved result rows of the proposed model (guards against any drift)."""
    root = C.ROOT / run / f"seed_{seed}"
    for k, tr, va, te in folds(metas, seed):
        ref = json.loads((root / f"fold{k}" / "result.json").read_text(encoding="utf-8"))["rows"]["Hybrid + AI-alone path"]
        assert sorted(r["trace"] for r in ref) == te, f"fold {k}: test ids differ from the saved result"


def run_cv(make_method, procs: dict[int, object], metas: list[dict], seeds=SEEDS, out_dir: Path | None = None, tag: str = "method",
           log=print) -> list[dict]:
    """procs: position -> proc (from method.prepare). make_method(seed, fold) -> fresh method object. Returns all rows (with seed and fold)."""
    rows: list[dict] = []
    for seed in seeds:
        for k, tr, va, te in folds(metas, seed):
            f_out = None if out_dir is None else out_dir / f"{tag}_seed{seed}_fold{k}.json"
            if f_out is not None and f_out.is_file():
                rows += json.loads(f_out.read_text(encoding="utf-8"))
                log(f"seed {seed} fold {k}: cached")
                continue
            t0 = time.time()
            m = make_method(seed, k)
            items = lambda ids: [{"meta": metas[i], "proc": procs[i], "id": i} for i in ids if i in procs]  # noqa: E731
            m.fit(items(tr), items(va), seed + k)
            fold_rows = []
            for i in te:
                if i not in procs:
                    continue
                r = C.score_row(metas[i], m.trip_time(procs[i]), i)
                r["seed"], r["fold"] = seed, k
                fold_rows.append(r)
            s = C.summarise(fold_rows)
            log(f"seed {seed} fold {k}: {len(fold_rows)} test traces | dep {s['dependability_pct']:.1f} % sec {s['security_pct']:.1f} % | {time.time() - t0:.0f} s")
            rows += fold_rows
            if f_out is not None:
                f_out.parent.mkdir(parents=True, exist_ok=True)
                f_out.write_text(json.dumps(fold_rows, default=float), encoding="utf-8")
    return rows
