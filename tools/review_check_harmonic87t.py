"""Review re-check (2026-10-26): conventional 87T variants scored with the SAME relay mirror as train_cv_v3 '87T alone'.
Run from the project root:  python tools/review_check_harmonic87t.py
Reproduces the unrestrained baseline exactly (79.62 % / 52.96 %, 881 false trips) and scores three harmonic-restraint variants:
  as_coded     = relay87t.analyse_harmonic (cross_block=True): ANY phase with k2>15 % or k5>35 % blocks, incl. phases carrying ~no current
  cross_active = cross-blocking only from phases whose differential RMS exceeds the pickup
  per_phase    = each phase's vote is restrained by its own k2/k5 (common practice)
Thresholds k2 15 %, k5 35 %; 87T vote taken as in train_cv_v3 (first vote after the window fills, plus high-set).
"""
import sys, numpy as np
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LM = str(ROOT / "lstm_models")
sys.path.insert(0, LM)
import train_trace_split as T, relay87t as R
from stress_dataset import load_traces, FS
from v3_checks import relaxed_ok_trace
D = str(ROOT / "datasets") + "/"
files = ["StressDataset_v3_20261021_021053.mat","StressDataset_v3Only_topup_inrush_loaded.mat","StressDataset_v3Only_topup_overexc.mat"]
W = R.W
def harmonic(primary, secondary, mode):
    res = R.analyse(primary, secondary)
    hv = (primary / R.I_NOM) @ R.M_PLANT.T; lv = secondary / R.I_NOM
    d = lv - hv
    blk = np.zeros((len(d), 3), bool)
    win = np.lib.stride_tricks.sliding_window_view(d, W, axis=0)
    spec = np.abs(np.fft.fft(win, axis=-1)); fund = spec[..., 1] + 1e-4
    k2 = spec[..., 2] / fund; k5 = spec[..., 5] / fund
    ph = (k2 > .15) | (k5 > .35)                       # per phase [T-W+1,3]
    idr = res["idiff_rms"]
    hv_ = (primary / R.I_NOM) @ R.M_PLANT.T
    irr = res["irest_rms"]
    dyn = np.where(irr <= R.BREAKPOINT, R.SLOPE_1*irr, R.SLOPE_2*(irr-R.BREAKPOINT)+R.SLOPE_1*R.BREAKPOINT)
    with np.errstate(invalid="ignore"):
        vph = (idr > R.I_PICKUP) & (idr > dyn)          # per-phase vote
    vph = np.nan_to_num(vph).astype(bool)
    full = np.zeros((len(d), 3), bool); full[W-1:] = ph
    if mode == "as_coded":            # thesis/F: implementation: any phase blocks, incl. phases with ~0 current
        b = full.any(1); v = vph.any(1) & ~b
    elif mode == "cross_active":      # cross-block only from phases above pickup
        act = np.nan_to_num(idr > R.I_PICKUP).astype(bool)
        b = (full & act).any(1); v = vph.any(1) & ~b
    elif mode == "per_phase":         # each phase restrained by its own harmonics
        v = (vph & ~full).any(1)
    return v | res["highset"], res["highset"]
traces = {}
for f in files:
    for t in load_traces(__import__("pathlib").Path(D + f)):
        if t["fingerprint"] in traces: continue
        if "checkPassed" in t and not relaxed_ok_trace(t): continue
        t["onset"] = int(round(t["inceptionTime"]*FS)) if t["should_trip"] else -1
        t["category"] = T.category(t["scenarioName"])
        t["fault_pu"] = R.fault_rise_pu(t["primary"], t["secondary"], t["onset"]) if t["onset"] >= 0 else np.nan
        t["undet"] = bool(t["should_trip"] and np.isfinite(t["fault_pu"]) and t["fault_pu"] < 0.05)
        traces[t["fingerprint"]] = t
traces = list(traces.values())
print("traces", len(traces), "undetectable", sum(t["undet"] for t in traces))
T.SOLO_THR = None; T.GATE87T = True
def run(name, getvote, dwell):
    T.DWELL = dwell
    rows = []
    for i, t in enumerate(traces):
        v, hs = getvote(t)
        n = len(t["primary"]) - 32 - T.SEQ + 1
        trip = T.relay_decision(np.ones(n, np.float32), 0.5, v, hs, None)
        tripped = trip >= 0; early = t["should_trip"] and tripped and trip < t["onset"]
        rows.append((t, tripped, early))
    f = [r for r in rows if r[0]["should_trip"] and not r[0]["undet"]]; h = [r for r in rows if not r[0]["should_trip"]]
    dep = 100*np.mean([tr and not e for _, tr, e in f]); sec = 100*np.mean([not tr for _, tr, _ in h])
    fa = sum(tr for _, tr, _ in h)
    cats = defaultdict(list)
    for t, tr, e in rows:
        if t["undet"]: continue
        cats[t["category"]].append((tr and not e) if t["should_trip"] else (not tr))
    print(f"{name:34s} dwell {dwell:2d}: dep {dep:6.2f} (n={len(f)})  sec {sec:6.2f} (n={len(h)})  false {fa}")
    return cats
c0 = run("unrestrained (current baseline)", lambda t: (R.analyse(t["primary"], t["secondary"])["vote"], R.analyse(t["primary"], t["secondary"])["highset"]), 20)
for mode in ("as_coded", "cross_active", "per_phase"):
    for dw in (20,):
        cats = run("harmonic " + mode, lambda t, m=mode: harmonic(t["primary"], t["secondary"], m), dw)
        print("   ", "  ".join(f"{k}:{100*np.mean(v):.0f}" for k, v in sorted(cats.items())))
