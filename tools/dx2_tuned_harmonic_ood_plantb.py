"""D-X2 (post-hoc; hypothesis H-X2 and rule logged before running): the harmonic-restrained 87T tuned on the EXTENDED grid, scored on the plant-A OOD set and on plant B
zero-shot, with the setting FROZEN from the plant-A final model's validation split (85/15 split of the detectable plant-A traces, seed 20261021, as for every other final
model). Same plateau rule and 125-setting grid as the extended N6c; the setting is chosen once and never retuned on OOD or plant B.
The textbook setting is scored on the same traces as a consistency check against the earlier harmonic-87T results (OOD 93.96 / 88.67, plant B 94.12 / 98.95).
Output: runs/20261101_v5_benchmark_fair/dx2_tuned_harmonic_ood_plantb.txt / .json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.argv = [sys.argv[0], "extended"]            # the n6c module reads its grid from argv
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
sys.path.insert(0, str(ROOT / "tools"))
import n6c_tuned_harmonic as N6  # noqa: E402
import relay87t as R  # noqa: E402
import run_plant_b_generalization_v5 as G  # noqa: E402
from baselines import common as C, cv  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from stress_dataset import FS, load_traces  # noqa: E402

OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"


def precompute(t, plant):
    p, s = t["primary"], t["secondary"]
    a = R.analyse(p, s, plant=plant)
    cfg = R.get_plant_config(plant)
    hv = (p / cfg["i_nom"]) @ cfg["m_hv"].T
    lv = (s / cfg["i_nom"]) @ cfg["m_lv"].T
    win = np.lib.stride_tricks.sliding_window_view(lv - hv, N6.W, axis=0)
    spec = np.abs(np.fft.fft(win, axis=-1))
    fund = spec[..., 1] + 1e-4
    return {"idr": a["idiff_rms"], "irr": a["irest_rms"], "k2": spec[..., 2] / fund, "k5": spec[..., 5] / fund, "n": len(p)}


def load_set(files, plant, cache):
    meta = C.load_meta(cache)        # detectability exactly as defined for every other method (cache of the generator checks)
    seen, items = set(), []
    for f in files:
        for t in load_traces(ROOT / "datasets" / f):
            onset = int(round(t["inceptionTime"] * FS)) if t["should_trip"] else -1
            md = meta.get((t["source_file"], int(t["source_index"])))
            if md is None:
                continue
            items.append({"pc": precompute(t, plant), "onset": onset, "should_trip": bool(t["should_trip"]),
                          "undetectable": bool(md["undetectable"]), "src": (t["source_file"], int(t["source_index"])), "scenario": t["scenarioName"]})
    return items


def score(items, setting):
    rows = []
    for k, it in enumerate(items):
        ts = N6.decide(it["pc"], setting)
        tripped = ts >= 0
        early = bool(it["should_trip"] and tripped and ts < it["onset"])
        rows.append({"idx": k, "should_trip": int(it["should_trip"]), "undetectable": it["undetectable"], "correct": bool((it["should_trip"] and tripped and not early) or (not it["should_trip"] and not tripped)), "src": it["src"], "scenario": it["scenario"]})
    return rows


def ds(rows):
    f = [r["correct"] for r in rows if r["should_trip"] and not r["undetectable"]]
    h = [r["correct"] for r in rows if not r["should_trip"] and not r["undetectable"]]
    return 100 * np.mean(f), 100 * np.mean(h), len(f), len(h)


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def failed_hr() -> set:
    out = set()
    for line in (ROOT / "documents" / "baselines" / "hr_missing_all.txt").read_text().splitlines():
        if line.startswith("  ") and " index " in line:
            a = line.split()
            out.add((a[0], int(a[2])))
    return out


def main() -> None:
    # 1. frozen setting from the plant-A final model's validation split (same recipe as run_full_eval / run_key_hybrid)
    metas, pos = cv.trace_index()
    excl = set()
    for line in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
        f, i, *_ = [x.strip() for x in line.split(",")]
        excl.add((f, int(i)))
    ok = {i for i, m in enumerate(metas) if (m["source_file"], int(m["source_index"])) not in excl}
    names = np.array([m["scenarioName"] for m in metas])
    trainable = [i for i in range(len(metas)) if not metas[i]["undetectable"] and i in ok]
    st = names[trainable].copy()
    for c, n_c in zip(*np.unique(st, return_counts=True)):
        if n_c < 4:
            st[st == c] = "_small"
    tr, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=cv.SEEDS[0])
    va = set(va.tolist())
    items_va = {}
    for _, src in C.PLANT_A_MAIN:
        for t in load_traces(ROOT / "datasets" / src):
            key = (t["source_file"], int(t["source_index"]))
            if key in pos and pos[key] in va and pos[key] not in items_va:
                i = pos[key]
                items_va[i] = {"pc": N6.precompute(t), "onset": int(round(t["inceptionTime"] * FS)) if t["should_trip"] else -1, "should_trip": bool(t["should_trip"]), "undetectable": False}
    vs = {}
    for g in N6.GRID:
        rows = N6.rows_for(items_va, sorted(items_va), g)
        vs[g] = N6.dep_sec(rows)
    g = N6.choose(vs)
    setting = [N6.PICK[g[0]], N6.K2[g[1]], N6.K5[g[2]]]
    L = [f"Tuned harmonic 87T (extended grid, post-hoc), setting FROZEN from the plant-A final model's validation split ({len(items_va)} validation traces): pickup {setting[0]} pu, k2 {setting[1]}, k5 {setting[2]} (validation dependability / security {vs[g][0]:.2f} / {vs[g][1]:.2f})",
         "scored once on OOD and plant B; nothing retuned there", ""]
    res = {"setting": setting, "validation": vs[g]}
    skip = failed_hr()
    for label, files, plant, cache in (("plantA_OOD", ["StressDataset_v5OOD_20261028_205712.mat"], "A", C.CACHE_A_OOD),
                                ("plantB_main", ["StressDataset_PlantBv5_20261028_212041.mat", "StressDataset_PlantBv5Only_20261029_111005.mat", "StressDataset_PlantBv5Only_20261029_111251.mat"], "B", C.CACHE_B_MAIN)):
        items = load_set(files, plant, cache)
        r_t, r_x = score(items, g), score(items, N6.TEXTBOOK)
        for name, rows in (("tuned, extended grid (frozen)", r_t), ("textbook 0.30 / 0.15 / 0.35 (consistency check)", r_x)):
            d, s, nf, nh = ds(rows)
            lo1, hi1 = wilson(round(d * nf / 100), nf); lo2, hi2 = wilson(round(s * nh / 100), nh)
            sub = [r for r in rows if r["src"] not in skip]
            d2, s2, nf2, nh2 = ds(sub)
            L.append(f"{label:12s} {name:50s} dependability {d:.2f} % [{lo1:.1f}, {hi1:.1f}] (n={nf}), security {s:.2f} % [{lo2:.1f}, {hi2:.1f}] (n={nh}) | on the traces that exist at 20 kHz: {d2:.2f} / {s2:.2f} (n={nf2}+{nh2})")
            res[f"{label}|{name}"] = {"dep": d, "sec": s, "n_fault": nf, "n_healthy": nh, "dep_20k": d2, "sec_20k": s2, "false_trips": int(sum(1 for r in rows if not r["should_trip"] and not r["undetectable"] and not r["correct"]))}
    sec_b = res["plantB_main|tuned, extended grid (frozen)"]["sec"]
    L += ["", f"H-X2 check: plant-B security {sec_b:.2f} % -> " + ("meets" if sec_b >= 98 else "does NOT meet") + " the pre-set 98 % line (rule applied in the log)"]
    (OUT / "dx2_tuned_harmonic_ood_plantb.txt").write_text("\n".join(L)); (OUT / "dx2_tuned_harmonic_ood_plantb.json").write_text(json.dumps(res, indent=1, default=float))
    print("\n".join(L))


if __name__ == "__main__":
    main()
