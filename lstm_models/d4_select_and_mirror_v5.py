"""Phase 2.4 - Closed-loop vs Python Relay Mirror Parity (v5).
  select : choose 25 OOD traces + 25 held-out validation traces of the FINAL model (main set only); write 1-based indices to indices.json.
  mirror : Python relay mirror (final model, thresholds from runs/20261029_v5_final) on those traces -> mirror.json
  compare: Simulink closed-loop results (test_hybrid_relay_d5main_results.mat / d5ood) vs the mirror -> simulations/closed_loop_vs_python_v5.txt

    python lstm_models/d4_select_and_mirror_v5.py select|mirror|compare
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
RUN = ROOT / "runs" / "20261029_v5_final"
MAIN_NAME = "StressDataset_v5_20261028_162333.mat"
SEED = 20261021
OUT = RUN / "d4"


def kept(cache: Path):
    return [t for t in np.load(cache, allow_pickle=True)["traces"] if "checkPassed" not in t or relaxed_ok_trace(t)]


def final_validation_ids(traces) -> list[int]:
    """Re-create the validation split of cmd_final (same code, same seed)."""
    for t in traces:
        t["undetectable"] = bool(t["should_trip"] and np.isfinite(t.get("fault_pu", np.nan)) and t["fault_pu"] < C.MIN_FAULT_PU)
    names = np.array([t["scenarioName"] for t in traces])
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
    main = kept(RUN / "traces_cache_main.npz")
    va = final_validation_ids(main)
    cand = [i for i in va if main[i]["source_file"] == MAIN_NAME]
    pick = sorted(rs.choice(cand, size=25, replace=False).tolist())
    main_idx = [int(main[i]["source_index"]) + 1 for i in pick]

    ood = kept(RUN / "traces_cache_ood.npz")
    po = sorted(rs.choice(len(ood), size=25, replace=False).tolist())
    ood_idx = [int(ood[i]["source_index"]) + 1 for i in po]

    sel = {"main": main_idx, "ood": ood_idx}
    (OUT / "indices.json").write_text(json.dumps(sel, indent=2), encoding="utf-8")
    print("main (final-validation) indices (25):", main_idx)
    print("OOD indices (25):", ood_idx)
    return sel


def mirror() -> None:
    sel = json.loads((OUT / "indices.json").read_text(encoding="utf-8"))
    ai = float((RUN / "decision_threshold.txt").read_text().strip())
    solo = float((RUN / "decision_solo_threshold.txt").read_text().strip())
    dwell = int((RUN / "decision_dwell.txt").read_text().strip()) if (RUN / "decision_dwell.txt").is_file() else 20

    ckpt = torch.load(RUN / "transformer_protection_lstm_best.pth", map_location="cpu", weights_only=False)
    cfg = ckpt["config"]
    model = T.TransformerProtectionLSTM(int(cfg["input_size"]), int(cfg["hidden_size"]), int(cfg["num_layers"]), float(cfg["dropout"]), bool(cfg["bidirectional"]))
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    ns = type("A", (), {"dwell": dwell, "dep_tolerance": 2.0, "sec_tolerance": 1.0, "limit": 0})()
    C.configure(ns)
    res = {}
    for label, cache, key in (("main", RUN / "traces_cache_main.npz", "main"), ("ood", RUN / "traces_cache_ood.npz", "ood")):
        traces = kept(cache)
        by_src = {(t["source_file"], int(t["source_index"]) + 1): i for i, t in enumerate(traces)}
        want = [(MAIN_NAME if label == "main" else next(t["source_file"] for t in traces), k) for k in sel[key]]
        ids = [by_src[w] for w in want]
        for t in traces:
            t["undetectable"] = False
        probs = {i: T.stream_probs(model, traces[i]["features"], torch.device("cpu")) for i in ids}
        rows = C.rows_for(traces, ids, probs, "Hybrid + AI-alone path", ai, solo)
        res[label] = [
            {
                "index": traces[r["trace"]]["source_index"] + 1,
                "scenario": traces[r["trace"]]["scenarioName"],
                "should_trip": r["should_trip"],
                "tripped": r["tripped"],
                "trip_time_s": (r["trip_sample"] / 1600.0) if r["tripped"] else None,
                "onset_s": r["onset_sample"] / 1600.0 if r["onset_sample"] >= 0 else None,
            }
            for r in rows
        ]
    (OUT / "mirror.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("mirror written:", {k: len(v) for k, v in res.items()})


def compare() -> None:
    mir = json.loads((OUT / "mirror.json").read_text(encoding="utf-8"))
    ai = (RUN / "decision_threshold.txt").read_text().strip()
    solo = (RUN / "decision_solo_threshold.txt").read_text().strip()
    dwell = (RUN / "decision_dwell.txt").read_text().strip() if (RUN / "decision_dwell.txt").is_file() else "20"

    L = [
        f"Simulink closed loop (LSTM active, saved model v5) vs Python relay mirror (final model, AI {ai}, solo {solo}, dwell {dwell}) on 50 traces: 25 held-out validation traces of the final model + 25 OOD traces",
        "",
        f"{'set':10s} {'#':5s} {'scenario':26s} {'mirror':8s} {'simulink':10s} {'dt ms':>8s}",
    ]
    agree, tot, dts, rows_all = 0, 0, [], []
    for label in ("main", "ood"):
        f = ROOT / "simulations" / f"test_hybrid_relay_d5{label}_results.mat"
        R = list(np.atleast_1d(loadmat(f, squeeze_me=True, struct_as_record=False)["R"]))
        sim = {int(str(r.name).split("#")[-1]): r for r in R}

        for m in mir[label]:
            idx = int(m["index"])
            assert idx in sim, f"trace #{idx} ({label}) missing from Simulink results"
            s = sim[idx]
            m_trip = bool(m["tripped"])
            s_trip = bool(s.tripped)
            dt = None
            if m_trip and s_trip:
                dt = (float(s.tripTime) - float(m["trip_time_s"])) * 1000.0
                dts.append(dt)
            ok = m_trip == s_trip
            agree += int(ok)
            tot += 1
            dt_str = f"{dt:+.1f}" if dt is not None else "-"
            L.append(f"{label:10s} {idx:5d} {m['scenario']:26s} {('TRIP' if m_trip else 'block'):8s} {('TRIP' if s_trip else 'block'):10s} {dt_str:>8s}")
            rows_all.append((label, idx, m["scenario"], m["should_trip"], m_trip, s_trip, dt))

    dts = np.array(dts) if dts else np.array([0.0])
    med_dt = float(np.median(np.abs(dts)))
    mean_dt = float(np.mean(dts))
    p95_dt = float(np.percentile(np.abs(dts), 95))
    max_dt = float(np.max(np.abs(dts)))

    pct_agree = 100.0 * agree / tot
    L.append("")
    L.append(f"Decision agreement: {agree} / {tot} = {pct_agree:.1f} %  (criterion >= 98 %)")
    L.append(f"Trip-time difference Simulink - mirror over {len(dts)} common trips: median {med_dt:.2f} ms, mean {mean_dt:.2f}, p95 {p95_dt:.2f}, max |dt| {max_dt:.2f} ms  (criterion median <= 2 ms)")

    sim_correct = sum(1 for r in rows_all if r[3] == r[5])
    mir_correct = sum(1 for r in rows_all if r[3] == r[4])
    L.append(f"Simulink correct vs ground truth: {sim_correct} / {tot}; mirror correct: {mir_correct} / {tot}")

    txt = "\n".join(L) + "\n"
    out_file = ROOT / "simulations" / "closed_loop_vs_python_v5.txt"
    out_file.write_text(txt, encoding="utf-8")
    print(txt)

    assert pct_agree >= 98.0, f"Decision agreement {pct_agree:.1f}% < 98%"
    assert med_dt <= 2.0, f"Median |dt| {med_dt:.2f} ms > 2.0 ms"
    print("PARITY CRITERIA PASSED: >=98% agreement and median |dt| <= 2 ms.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "select"
    if cmd == "select":
        select()
    elif cmd == "mirror":
        mirror()
    elif cmd == "compare":
        compare()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
