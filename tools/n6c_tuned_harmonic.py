"""N6c: validation-tuned harmonic-restrained 87T (per-phase), BENCHMARK_FAIRNESS_PLAN.md B4 / N6c.

Grid pickup {0.2, 0.3, 0.4} pu x k2 {0.12, 0.15, 0.20} x k5 {0.25, 0.35} (18 settings). Per fold (3 seeds x 5 folds, the same folds as every other model) the setting is
chosen on the fold's VALIDATION traces by the plateau rule: keep the settings whose validation security is within 1 pt of the best, take the best dependability D* among
them, keep those within 2 pt of D*, and return the member of that plateau closest to its centroid in grid-index space (ties: higher dependability, then the textbook
setting). The textbook setting (0.30 / 0.15 / 0.35) is reported next to it. The 1,600 Hz CT secondaries come from the original datasets; the trip logic is the relay
mirror's (high-set OR vote for 20 consecutive windows, as in evaluate_harmonic87t_v5.py).
Output: runs/20261101_v5_benchmark_fair/n6c_tuned_harmonic.txt / .json
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
sys.path.insert(0, str(ROOT / "tools"))
import relay87t as R  # noqa: E402
import train_trace_split as T  # noqa: E402
from stress_dataset import load_traces  # noqa: E402
from baselines import common as C, cv  # noqa: E402
import n5_statistics as N5  # noqa: E402

OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"
EXT = len(sys.argv) > 1 and sys.argv[1] == "extended"      # post-hoc extension of the grid (plan entry of the grid-edge check); the original run is the default
if EXT:
    PICK, K2, K5 = (0.10, 0.15, 0.20, 0.30, 0.40), (0.12, 0.15, 0.20, 0.25, 0.30), (0.15, 0.20, 0.25, 0.35, 0.45)
else:
    PICK, K2, K5 = (0.2, 0.3, 0.4), (0.12, 0.15, 0.20), (0.25, 0.35)
SUF = "_ext" if EXT else ""
GRID = list(itertools.product(range(len(PICK)), range(len(K2)), range(len(K5))))
TEXTBOOK = (PICK.index(0.30), K2.index(0.15), K5.index(0.35))
W = 32


def precompute(t):
    p, s = t["primary"], t["secondary"]
    a = R.analyse(p, s)
    cfg = R.get_plant_config("A")
    hv = (p / cfg["i_nom"]) @ cfg["m_hv"].T
    lv = (s / cfg["i_nom"]) @ cfg["m_lv"].T
    diff = lv - hv
    win = np.lib.stride_tricks.sliding_window_view(diff, W, axis=0)
    spec = np.abs(np.fft.fft(win, axis=-1))
    fund = spec[..., 1] + 1e-4
    return {"idr": a["idiff_rms"], "irr": a["irest_rms"], "k2": spec[..., 2] / fund, "k5": spec[..., 5] / fund, "n": len(p)}


def decide(pc, setting):
    pk, k2, k5 = PICK[setting[0]], K2[setting[1]], K5[setting[2]]
    idr, irr = pc["idr"], pc["irr"]
    dyn = np.where(irr <= R.BREAKPOINT, R.SLOPE_1 * irr, R.SLOPE_2 * (irr - R.BREAKPOINT) + R.SLOPE_1 * R.BREAKPOINT)
    with np.errstate(invalid="ignore"):
        vph = np.nan_to_num((idr > pk) & (idr > dyn)).astype(bool)
        hs = np.nan_to_num(idr > R.I_HIGH_SET).astype(bool).any(1)
    blocked = np.zeros(vph.shape, bool)
    blocked[W - 1:] = (pc["k2"] > k2) | (pc["k5"] > k5)
    vote = ((vph & ~blocked).any(1)) | hs
    n_w = pc["n"] - 32 - T.SEQ + 1
    T.DWELL = 20
    return T.relay_decision(np.ones(n_w, np.float32), 0.5, vote, hs, None)


def rows_for(items, ids, setting):
    out = {}
    for i in ids:
        it = items[i]
        ts = decide(it["pc"], setting)
        tripped = ts >= 0
        early = bool(it["should_trip"] and tripped and ts < it["onset"])
        out[i] = {"trace": i, "should_trip": int(it["should_trip"]), "undetectable": it["undetectable"], "tripped": tripped,
                  "correct": bool((it["should_trip"] and tripped and not early) or (not it["should_trip"] and not tripped))}
    return out


def dep_sec(rows):
    f = [r["correct"] for r in rows.values() if r["should_trip"] and not r["undetectable"]]
    h = [r["correct"] for r in rows.values() if not r["should_trip"] and not r["undetectable"]]
    return 100 * np.mean(f), 100 * np.mean(h)


def choose(val_scores):
    best_sec = max(v[1] for v in val_scores.values())
    a = {g: v for g, v in val_scores.items() if v[1] >= best_sec - 1.0}
    dstar = max(v[0] for v in a.values())
    plat = [g for g, v in a.items() if v[0] >= dstar - 2.0]
    cen = np.mean(np.array(plat), axis=0)
    return min(plat, key=lambda g: (float(np.linalg.norm(np.array(g) - cen)), -val_scores[g][0], g != TEXTBOOK))


def main():
    metas, pos = cv.trace_index()
    items = {}
    for _, src in C.PLANT_A_MAIN:
        for t in load_traces(ROOT / "datasets" / src):
            key = (t["source_file"], int(t["source_index"]))
            if key in pos and pos[key] not in items:
                i = pos[key]
                items[i] = {"pc": precompute(t), "onset": int(round(t["inceptionTime"] * C.FS_RELAY)) if t["should_trip"] else -1,
                            "should_trip": bool(t["should_trip"]), "undetectable": bool(metas[i]["undetectable"])}
    excl = set()
    for line in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
        f, i, *_ = [x.strip() for x in line.split(",")]
        excl.add((f, int(i)))
    ok = {i for i in items if (metas[i]["source_file"], int(metas[i]["source_index"])) not in excl}
    print(f"{len(items)} traces precomputed, {len(ok)} on the common set", flush=True)
    allrows = {g: rows_for(items, sorted(ok), g) for g in GRID}
    tuned_rows, text_rows, chosen = {}, {}, []
    for seed in cv.SEEDS:
        for k, tr, va, te in cv.folds(metas, seed):
            vs = {g: dep_sec({i: allrows[g][i] for i in va if i in ok and not items[i]["undetectable"]}) for g in GRID}
            g = choose(vs)
            chosen.append({"seed": seed, "fold": k, "setting": [PICK[g[0]], K2[g[1]], K5[g[2]]], "val": vs[g]})
            for i in te:
                if i in ok:
                    tuned_rows[(seed, k, i)] = dict(allrows[g][i], seed=seed, fold=k)
                    text_rows[(seed, k, i)] = dict(allrows[TEXTBOOK][i], seed=seed, fold=k)
    ref = N5.load_ref("Hybrid + AI-alone path")
    counts = {}
    for c in chosen:
        counts[str(c["setting"])] = counts.get(str(c["setting"]), 0) + 1
    edge = {name: (sum(1 for c in chosen if c["setting"][i] == grid_vals[0]), sum(1 for c in chosen if c["setting"][i] == grid_vals[-1]))
            for i, (name, grid_vals) in enumerate((("pickup", PICK), ("k2", K2), ("k5", K5)))}
    L = ["Validation-tuned harmonic 87T (per-phase) vs textbook settings, plant-A CV (3 seeds x 5 folds, common set)" + (" - EXTENDED GRID (post-hoc)" if EXT else ""),
         "chosen at the lower / upper edge of the grid (of 15 fold-models): " + ", ".join(f"{k} {lo} / {hi}" for k, (lo, hi) in edge.items()),
         "chosen settings (pickup, k2, k5) over the 15 fold-models: " + str(counts)]
    tests = []
    for name, rows in (("textbook 0.30/0.15/0.35", text_rows), ("tuned on validation", tuned_rows)):
        for metric, flag in (("dependability", 1), ("security", 0)):
            ks = [k for k in rows if k in ref and not rows[k]["undetectable"] and rows[k]["should_trip"] == flag]
            a = np.array([bool(ref[k]["correct"]) for k in ks])
            b = np.array([bool(rows[k]["correct"]) for k in ks])
            n10, n01, p = N5.mcnemar(a, b)
            per_seed = {s: float(100 * (b[[i for i, k in enumerate(ks) if k[0] == s]].mean() - a[[i for i, k in enumerate(ks) if k[0] == s]].mean())) for s in cv.SEEDS}
            tests.append({"setting": name, "metric": metric, "n": len(ks), "hybrid": 100 * a.mean(), "harmonic": 100 * b.mean(), "diff_pt": 100 * (b.mean() - a.mean()),
                          "hybrid_only": n10, "harmonic_only": n01, "p": p, "per_seed": per_seed})
    adj = N5.holm(np.array([t["p"] for t in tests]))
    for t, q in zip(tests, adj):
        t["p_holm4"] = float(q)
        L.append(f"harmonic 87T {t['setting']:24s} {t['metric']:13s} n={t['n']}: hybrid {t['hybrid']:.2f} harmonic {t['harmonic']:.2f} diff {t['diff_pt']:+.2f} pt "
                 f"discordant {t['hybrid_only']}/{t['harmonic_only']} p_Holm4 {q:.2e}" + (" *" if q < 0.05 else "") + "  seeds " + " ".join(f"{v:+.2f}" for v in t["per_seed"].values()))
    def fam(i):
        return "Internal_HiZ" if metas[i]["scenarioName"].startswith("Internal_HiZ") else "other internal faults"

    def dep_of(rows, g):
        v = [bool(rows[k]["correct"]) for k in rows if k in ref and rows[k]["should_trip"] and not rows[k]["undetectable"] and fam(k[2]) == g]
        return 100 * np.mean(v), len(v)

    for g in ("Internal_HiZ", "other internal faults"):
        (hy, n) = dep_of({k: ref[k] for k in tuned_rows if k in ref}, g)
        L.append(f"dependability, {g} (n={n}): hybrid {hy:.1f}, tuned harmonic {dep_of(tuned_rows, g)[0]:.1f}, textbook harmonic {dep_of(text_rows, g)[0]:.1f}")
    rows_dump = {"tuned": [dict(v, key=list(k)) for k, v in tuned_rows.items()], "textbook": [dict(v, key=list(k)) for k, v in text_rows.items()]}
    (OUT / f"n6c_tuned_rows{SUF}.json").write_text(json.dumps(rows_dump, default=float))
    (OUT / f"n6c_tuned_harmonic{SUF}.txt").write_text("\n".join(L))
    (OUT / f"n6c_tuned_harmonic{SUF}.json").write_text(json.dumps({"chosen": chosen, "tests": tests}, indent=1, default=float))
    print("\n".join(L))


if __name__ == "__main__":
    main()
