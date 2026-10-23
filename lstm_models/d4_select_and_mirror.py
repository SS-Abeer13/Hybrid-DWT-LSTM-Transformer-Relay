"""Step D4 helper.
  select : choose 25 OOD traces + 25 held-out validation traces of the FINAL model (main set only, no top-ups); write the index lists (1-based dataset numbers).
  mirror : Python relay mirror (final model, thresholds from runs/20261022_v3_final) on those traces -> d4_mirror.json
  compare: Simulink closed-loop results (test_hybrid_relay_d4main_results.mat / d4ood) vs the mirror -> simulations/closed_loop_vs_python_v3.txt

    python lstm_models/d4_select_and_mirror.py select|mirror|compare
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.io import loadmat
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_cv_v3 as C  # noqa: E402
import train_trace_split as T  # noqa: E402
from v3_checks import relaxed_ok_trace  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "runs" / "20261022_v3_final"
MAIN_NAME = "StressDataset_v3_20261021_021053.mat"
SEED = 20261021
OUT = ROOT / "runs" / "20261022_v3_final" / "d4"


def kept(cache: Path):
    return [t for t in np.load(cache, allow_pickle=True)["traces"] if "checkPassed" not in t or relaxed_ok_trace(t)]


def final_validation_ids(traces) -> list[int]:
    """Re-create the validation split of cmd_final (same code, same seed)."""
    for t in traces:
        t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < C.MIN_FAULT_PU)
    names = np.array([C.group_of(t["scenarioName"]) if False else t["scenarioName"] for t in traces])
    trainable = [i for i, t in enumerate(traces) if not t["undetectable"]]
    st = names[trainable].copy()
    for c, n_c in zip(*np.unique(st, return_counts=True)):
        if n_c < 4:
            st[st == c] = "_small"
    _, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=SEED)
    return sorted(va.tolist())


def select() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    rs = np.random.RandomState(20261022)
    main = kept(ROOT / "runs" / "20261021_v3data_baseline" / "traces_cache_main.npz")
    va = final_validation_ids(main)
    cand = [i for i in va if main[i]["source_file"] == MAIN_NAME]
    pick = sorted(rs.choice(cand, size=25, replace=False).tolist())
    main_idx = [int(main[i]["source_index"]) + 1 for i in pick]
    ood = kept(RUN / "traces_cache_ood.npz")
    po = sorted(rs.choice(len(ood), size=25, replace=False).tolist())
    ood_idx = [int(ood[i]["source_index"]) + 1 for i in po]
    sel = {"main": main_idx, "ood": ood_idx}
    (OUT / "indices.json").write_text(json.dumps(sel), encoding="utf-8")
    print("main (final-validation) indices:", main_idx)
    print("OOD indices:", ood_idx)
    return sel


def mirror() -> None:
    sel = json.loads((OUT / "indices.json").read_text(encoding="utf-8"))
    ai = float((RUN / "decision_threshold.txt").read_text().strip()); solo = float((RUN / "decision_solo_threshold.txt").read_text().strip())
    ckpt = torch.load(RUN / "transformer_protection_lstm_best.pth", map_location="cpu", weights_only=False)
    cfg = ckpt["config"]
    model = T.TransformerProtectionLSTM(int(cfg["input_size"]), int(cfg["hidden_size"]), int(cfg["num_layers"]), float(cfg["dropout"]), bool(cfg["bidirectional"]))
    model.load_state_dict(ckpt["model_state_dict"]); model.eval()
    ns = type("A", (), {"dwell": 20, "dep_tolerance": 2.0, "sec_tolerance": 1.0, "limit": 0})()
    C.configure(ns)
    res = {}
    for label, cache, key in (("main", ROOT / "runs" / "20261021_v3data_baseline" / "traces_cache_main.npz", "main"), ("ood", RUN / "traces_cache_ood.npz", "ood")):
        traces = kept(cache)
        by_src = {(t["source_file"], int(t["source_index"]) + 1): i for i, t in enumerate(traces)}
        want = [(MAIN_NAME if label == "main" else next(t["source_file"] for t in traces), k) for k in sel[key]]
        ids = [by_src[w] for w in want]
        for t in traces:
            t["undetectable"] = False
        probs = {i: T.stream_probs(model, traces[i]["features"], torch.device("cpu")) for i in ids}
        rows = C.rows_for(traces, ids, probs, "Hybrid + AI-alone path", ai, solo)
        res[label] = [{"index": traces[r["trace"]]["source_index"] + 1, "scenario": traces[r["trace"]]["scenarioName"], "should_trip": r["should_trip"], "tripped": r["tripped"],
                       "trip_time_s": (r["trip_sample"] / 1600.0) if r["tripped"] else None, "onset_s": r["onset_sample"] / 1600.0 if r["onset_sample"] >= 0 else None} for r in rows]
    (OUT / "mirror.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("mirror written:", {k: len(v) for k, v in res.items()})


def compare() -> None:
    mir = json.loads((OUT / "mirror.json").read_text(encoding="utf-8"))
    L = ["Simulink closed loop (LSTM active, saved model) vs Python relay mirror (final model, AI 0.99, solo 0.998, dwell 20) on 50 traces: 25 held-out validation traces of the final model + 25 OOD traces", ""]
    agree, tot, dts, rows_all = 0, 0, [], []
    for label in ("main", "ood"):
        R = []
        for f in sorted((ROOT / "simulations").glob(f"test_hybrid_relay_d4{label}*_results.mat")):
            R += list(np.atleast_1d(loadmat(f, squeeze_me=True, struct_as_record=False)["R"]))
        sim = {int(str(r.name).split("#")[-1]): r for r in R}
        for m in mir[label]:
            r = sim.get(m["index"])
            if r is None:
                continue
            tot += 1
            same = bool(r.tripped) == bool(m["tripped"])
            agree += same
            dt = None
            if same and m["tripped"]:
                dt = 1000 * (float(r.tripTime) - m["trip_time_s"]); dts.append(dt)
            rows_all.append((label, m["index"], m["scenario"], "TRIP" if m["tripped"] else "block", "TRIP" if r.tripped else "block", dt, bool(m["should_trip"])))
    L.append(f"{'set':5s} {'#':>5s} {'scenario':26s} {'mirror':7s} {'simulink':8s} {'dt ms':>7s}")
    for lab, i, sc, a, b, dt, st in rows_all:
        L.append(f"{lab:5s} {i:5d} {sc:26s} {a:7s} {b:8s} {('%.1f' % dt) if dt is not None else '-':>7s}{'' if a == b else '   <-- DISAGREE'}")
    L.append("")
    L.append(f"Decision agreement: {agree} / {tot} = {100 * agree / max(tot, 1):.1f} %  (criterion >= 98 %)")
    if dts:
        d = np.array(dts)
        L.append(f"Trip-time difference Simulink - mirror over {len(d)} common trips: median {np.median(d):.2f} ms, mean {d.mean():.2f}, p95 {np.percentile(np.abs(d), 95):.2f}, max |dt| {np.abs(d).max():.2f} ms  (criterion median <= 2 ms)")
    L.append(f"Simulink correct vs ground truth: {sum(1 for r in rows_all if (r[4] == 'TRIP') == r[6])} / {tot}; mirror correct: {sum(1 for r in rows_all if (r[3] == 'TRIP') == r[6])} / {tot}")
    (ROOT / "simulations" / "closed_loop_vs_python_v3.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    {"select": select, "mirror": mirror, "compare": compare}[sys.argv[1]]()
