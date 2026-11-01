"""D3 (BENCHMARK_FAIRNESS_PLAN.md): do the 20 kHz re-simulated traces, decimated to the relay's 1,600 Hz, reproduce the original traces?

For a stratified sample of plant-A main-set traces that exist in both data sets, the CT secondaries Ip, Is of the 20 kHz run are sampled at the
relay's instants (zero-order hold: sample floor(k * 12.5)), pushed through the same Python chain as the relay mirror (differential, 12 features,
87T vote and high-set) and through the proposed final model with its saved thresholds (hybrid + AI-alone path, dwell). The decisions are compared with those
of the original trace (cached features of the same final-model run). Noise realisations differ (noise sample time 100 us -> 25 us), so identical
waveforms are not expected; the criterion is the plan's: same events and identical trip / no-trip decisions on >= 99 % of the traces.
Output: documents/baselines/d3_equivalence.txt / .json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
import features12 as F  # noqa: E402
import relay87t  # noqa: E402
import train_cv_v3 as CV  # noqa: E402
import train_trace_split as T  # noqa: E402
from baselines import common as C  # noqa: E402
from v3_checks import relaxed_ok_trace  # noqa: E402

RUN = ROOT / "runs" / "20261029_v5_final"
PER_SCENARIO = 6


def main() -> None:
    ai = float((RUN / "decision_threshold.txt").read_text().strip())
    solo = float((RUN / "decision_solo_threshold.txt").read_text().strip())
    dwell = int((RUN / "decision_dwell.txt").read_text().strip())
    ckpt = torch.load(RUN / "transformer_protection_lstm_best.pth", map_location="cpu", weights_only=False)
    cfg = ckpt["config"]
    model = T.TransformerProtectionLSTM(int(cfg["input_size"]), int(cfg["hidden_size"]), int(cfg["num_layers"]), float(cfg["dropout"]), bool(cfg["bidirectional"]))
    model.load_state_dict(ckpt["model_state_dict"]); model.eval()
    CV.configure(type("A", (), {"dwell": dwell, "dep_tolerance": 2.0, "sec_tolerance": 1.0, "limit": 0})())

    orig = [t for t in np.load(RUN / "traces_cache_main.npz", allow_pickle=True)["traces"] if "checkPassed" not in t or relaxed_ok_trace(t)]
    for t in orig:
        t["undetectable"] = False
    key = {(t["source_file"], int(t["source_index"])): i for i, t in enumerate(orig)}

    taken = defaultdict(int)
    pairs = []      # (original trace dict, HR-derived trace dict)
    for tr in C.iter_hr(C.PLANT_A_MAIN):
        i = key.get((tr["src"], tr["index"]))
        if i is None:
            continue
        name = orig[i]["scenarioName"]
        if taken[name] >= PER_SCENARIO:
            continue
        taken[name] += 1
        k = np.floor(np.arange(1761) * 12.5).astype(int)
        ip, is_ = tr["Ip"][k].astype(np.float64), tr["Is"][k].astype(np.float64)
        d = F.plant_compensated_diff(ip, is_, plant="A")
        a = relay87t.analyse(ip, is_, plant="A")
        t2 = dict(orig[i])
        t2["features"], t2["vote87"], t2["highset"] = F.trace_features(d), a["vote"], a["highset"]
        pairs.append((orig[i], t2))
    n = len(pairs)
    print("pairs", n)
    both = [p[0] for p in pairs] + [p[1] for p in pairs]
    probs = {i: T.stream_probs(model, both[i]["features"], torch.device("cpu")) for i in range(len(both))}
    rows = CV.rows_for(both, list(range(len(both))), probs, "Hybrid + AI-alone path", ai, solo)
    by = {r["trace"]: r for r in rows}
    same, dt, diff = 0, [], []
    for j in range(n):
        a, b = by[j], by[n + j]
        ok = bool(a["tripped"]) == bool(b["tripped"])
        same += ok
        if a["tripped"] and b["tripped"]:
            dt.append((b["trip_sample"] - a["trip_sample"]) / 1.6)
        if not ok:
            diff.append({"scenario": pairs[j][0]["scenarioName"], "should_trip": bool(a["should_trip"]), "orig_tripped": bool(a["tripped"]), "hr_tripped": bool(b["tripped"])})
    L = [f"D3 equivalence, plant A main set, {n} traces ({PER_SCENARIO} per scenario), final model thresholds AI {ai} / solo {solo} / dwell {dwell}",
         f"identical trip / no-trip decision: {same}/{n} = {100*same/n:.2f} %  (criterion >= 99 %)",
         f"trip-time difference HR - original on traces tripping in both (ms): median {np.median(dt):.3f}, p5 {np.percentile(dt,5):.3f}, p95 {np.percentile(dt,95):.3f}, n={len(dt)}" if dt else "no common trips",
         f"discordant traces: {len(diff)}"] + [f"  {d}" for d in diff]
    (ROOT / "documents" / "baselines" / "d3_equivalence.txt").write_text("\n".join(L), encoding="utf-8")
    (ROOT / "documents" / "baselines" / "d3_equivalence.json").write_text(json.dumps({"n": n, "same": same, "discordant": diff}, indent=1), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
