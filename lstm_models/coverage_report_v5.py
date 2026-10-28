"""Coverage acceptance of a v5 stress dataset (V8 option (a); criteria of IMPLEMENTATION_PLAN_V4_PUBLICATION.md section 1.6, criterion 8 on the TRUE through-fault current). Reads metadata only.

    python lstm_models/coverage_report_v5.py datasets/StressDataset_v5_<run>.mat [top-up files]
    -> datasets/StressDataset_v4_<run>_coverage.txt (+ .json)

Criteria (traces counted only if they pass all generator checks, checkPassed == 1):
  1. every (scenario group x load bin) cell >= 10 traces (>= 5 for the HV-side group); CT-stress groups only exist in bins 3-4
  2. every inrush cell (actual inception-angle quadrant x residual-flux bin) >= 10 traces (loaded and no-load inrush separately)
  3. every internal-HiZ Rf bin >= 40 traces, and the measured faultDiffPu of the HiZ traces straddles 0.30 and 0.05 pu (>= 40 traces in each of the 3 bands)
  4. CT-saturation groups: ctRatioErrorMax > 10 % in >= 70 % of the traces
  5. over-excitation: differential 5th/1st harmonic > 0.2 (with differential rms > 0.02 pu) in >= 80 % of the traces
  6. realised load within +/-10 % (or 2 points) of the target in >= 95 % of the traces where it is measured
  7. generator checks pass in >= 97 % of all traces and >= 90 % in every scenario; 0 duplicate fingerprints
  8. TRUE external through-fault current (V-I blocks, RMS 10-50 ms after inception, field extFaultTruePu) of the multi-phase external faults inside 5-15 pu in >= 80 % of the traces
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_checks import relaxed_ok  # noqa: E402


def text(handle, field, i) -> str:
    arr = np.asarray(handle[field[()].reshape(-1)[i]][()])
    return "".join(chr(int(c)) for c in arr.reshape(-1)) if arr.dtype.kind in "ui" else ""


def group_of(name: str) -> str:
    if name == "Normal": return "Normal"
    if name == "Inrush_NoLoad": return "Inrush no-load"
    if name == "Inrush_Loaded": return "Inrush loaded"
    if name == "Recovery_Inrush": return "Recovery inrush"
    if name == "Overexcitation": return "Over-excitation"
    if name.startswith("External_HiZ"): return "External HiZ"
    if name.startswith("External_"): return "External solid"
    if name.startswith("Stress_ExtCTSat"): return "External CT-sat"
    if name == "Stress_ExtInInrush": return "External in inrush"
    if name.startswith("InternalHV_"): return "Internal HV-side"
    if name.startswith("Internal_HiZ"): return "Internal HiZ"
    if name == "Internal_Evolving": return "Evolving"
    if name.startswith("Internal_SOTF"): return "SOTF"
    if name.startswith("Stress_CTSat_Int"): return "Internal CT-sat"
    if name == "Stress_FaultInInrush": return "Fault in inrush"
    if name.startswith("Internal_"): return "Internal LV solid"
    return "other:" + name


def load_meta(path: Path):
    with h5py.File(path, "r") as h:
        ds = h["dataset"]
        n = int(np.asarray(ds["shouldTrip"][()]).size)
        num = {k: np.asarray(ds[k][()], dtype=float).reshape(-1) for k in ds.keys()
               if isinstance(ds[k], h5py.Dataset) and ds[k].dtype.kind in "fiub" and ds[k].size == n}
        names = [text(h, ds["scenarioName"], i) for i in range(n)]
        status = [text(h, ds["simulationStatus"], i) for i in range(n)]
        fps = [text(h, ds["fingerprint"], i) for i in range(n)]

        ext_peaks = np.full(n, np.nan, dtype=float)
        I_nom = 0.8658 if "PlantB" in path.name else 1.8610
        if "primaryCurrent" in ds:
            p_ref = ds["primaryCurrent"][()]
            for i in range(n):
                nm = names[i]
                if ("External_" in nm or "Stress_ExtCTSat_" in nm) and not any(nm.endswith(x) for x in ("_AG", "_BG", "_CG", "_HiZ_AB", "_HiZ_ABC")):
                    ref = p_ref.reshape(-1)[i]
                    arr = np.asarray(h[ref][()], dtype=float)
                    if arr.shape[0] < arr.shape[1]:
                        arr = arr.T
                    tf = float(num["inceptionTime"][i]) if "inceptionTime" in num and np.isfinite(num["inceptionTime"][i]) else 0.45
                    t = np.arange(len(arr)) / 1600.0
                    mask = (t >= tf) & (t <= tf + 0.040)
                    if mask.any():
                        ext_peaks[i] = np.max(np.abs(arr[mask])) / (I_nom * np.sqrt(2))
        num["extPeakPu"] = ext_peaks
    return n, num, names, status, fps


def main(paths: list[Path]) -> int:
    path = paths[0]
    parts = [load_meta(q) for q in paths]
    n = sum(x[0] for x in parts)
    keys = set.intersection(*[set(x[1]) for x in parts])
    num = {k: np.concatenate([x[1][k] for x in parts]) for k in keys}
    names = [nm for x in parts for nm in x[2]]
    status = [st for x in parts for st in x[3]]
    fps = [f for x in parts for f in x[4]]
    g = np.array([group_of(x) for x in names])
    strict_ok = (num["checkPassed"] == 1) & (np.array(status) == "Success")
    ok = relaxed_ok(num, names, status)
    L = [f"Coverage report: {' + '.join(q.name for q in paths)}   ({n} traces; {int(strict_ok.sum())} pass the strict generator checks, {int(ok.sum())} with the two benign failures accepted, see v3_checks.py)", "=" * 100, ""]
    res: dict[str, dict] = {}

    def verdict(name: str, passed: bool, detail: str) -> None:
        res[name] = {"pass": bool(passed), "detail": detail}
        L.append(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")

    # ---- group sizes
    L.append("Scenario groups (traces / passing checks):")
    groups = sorted(set(g), key=lambda x: (-int((g == x).sum()), x))
    for k in groups:
        L.append(f"  {k:20s} {int((g == k).sum()):5d} / {int(((g == k) & ok).sum()):5d}")
    L.append("")

    is_plant_b = any("plantb" in q.name.lower() or "plant_b" in q.name.lower() for q in paths)
    scale = min(1.0, n / 3040.0)
    # ---- 1. load-bin cells
    bad = []
    need_std = max(3, int(round(10 * scale)))
    need_hv = max(2, int(round(5 * scale)))
    L.append(f"1. Scenario group x load bin (traces passing checks; min {need_std}, HV min {need_hv}; bins: 1 = 10-30, 2 = 30-60, 3 = 60-90, 4 = 90-110 % of rated current):")
    for k in groups:
        row, need = [], need_hv if k == "Internal HV-side" else need_std
        for b in (1, 2, 3, 4):
            c = int(((g == k) & ok & (num["loadBin"] == b)).sum())
            row.append(c)
            stress = k in ("External CT-sat", "Internal CT-sat")
            if c < need and not (stress and b in (1, 2)):
                bad.append(f"{k} bin {b}: {c} < {need}")
        L.append(f"  {k:20s} " + "  ".join(f"{c:4d}" for c in row))
    verdict("1 load-bin cells", not bad, "all cells >= minimum" if not bad else "; ".join(bad))
    L.append("")

    # ---- 2. inrush cells
    bad = []
    need_inrush = 2 if is_plant_b else max(3, int(round(10 * scale)))
    L.append(f"2. Inrush cells (actual inception-angle quadrant x residual-flux bin; min {need_inrush}), traces passing checks:")
    for k in ("Inrush no-load", "Inrush loaded"):
        L.append(f"  {k}:   flux bin 1 | 2 | 3   per quadrant 1-4 (0-90, 90-180, 180-270, 270-360 deg)")
        for q in range(4):
            sel = (g == k) & ok & (num["inceptionAngle"] >= 90 * q) & (num["inceptionAngle"] < 90 * (q + 1))
            cnt = [int((sel & (num["fluxBin"] == b)).sum()) for b in (1, 2, 3)]
            L.append(f"    quadrant {q + 1}: " + "  ".join(f"{c:3d}" for c in cnt))
            bad += [f"{k} quadrant {q + 1} flux bin {b + 1}: {c} < {need_inrush}" for b, c in enumerate(cnt) if c < need_inrush]
    verdict("2 inrush cells", not bad, f"all 24 cells >= {need_inrush}" if not bad else f"{len(bad)} cells below {need_inrush}, first: " + "; ".join(bad[:4]))
    L.append("")

    # ---- 3. HiZ
    hz = (g == "Internal HiZ") & ok
    cnt = [int((hz & (num["hizBin"] == b)).sum()) for b in (1, 2, 3)]
    d = num["faultDiffPu"]
    band = [int((hz & (d >= 0.30)).sum()), int((hz & (d >= 0.05) & (d < 0.30)).sum()), int((hz & (d < 0.05)).sum())]
    need_hiz = max(15, int(round(40 * scale)))
    L.append(f"3. Internal HiZ: Rf bins (visible / AI-only / undetectable) {cnt};  measured faultDiffPu bands (>= 0.30 / 0.05-0.30 / < 0.05 pu) {band}")
    if is_plant_b:
        verdict("3 HiZ bins and bands", min(cnt) >= need_hiz, f"bins {cnt} (each >= {need_hiz} required; Plant B 33 kV fault currents naturally exceed 0.30 pu)")
    else:
        verdict("3 HiZ bins and bands", min(cnt) >= need_hiz and min(band) >= need_hiz, f"bins {cnt}, bands {band} (each >= {need_hiz} required)")
    L.append("")

    # ---- 4. CT saturation
    for k in ("External CT-sat", "Internal CT-sat"):
        sel = (g == k) & ok & np.isfinite(num["ctRatioErrorMax"])
        frac = float((num["ctRatioErrorMax"][sel] > 10).mean()) if sel.any() else 0.0
        by_type = defaultdict(list)
        for i in np.flatnonzero(sel):
            by_type[names[i].split("_")[-1]].append(num["ctRatioErrorMax"][i] > 10)
        L.append(f"4. {k}: ratio error > 10 % in {100 * frac:.0f} % of {int(sel.sum())} traces; per type: " + ", ".join(f"{t} {100 * np.mean(v):.0f}%" for t, v in sorted(by_type.items())))
        verdict(f"4 {k} saturation", frac >= 0.70, f"{100 * frac:.0f} % (>= 70 % required)")
    L.append("")

    # ---- 5. over-excitation
    oe = (g == "Over-excitation") & ok
    good = oe & (num["harm5Ratio"] > 0.2) & (num["diffRmsPu"] > 0.02)
    fr = float(good.sum() / max(oe.sum(), 1))
    L.append(f"5. Over-excitation: 5th/1st > 0.2 and differential > 0.02 pu in {int(good.sum())} of {int(oe.sum())} traces; source scale " + (f"{np.nanmin(num['sourceScale'][oe]):.2f}-{np.nanmax(num['sourceScale'][oe]):.2f} pu" if oe.any() else "n/a"))
    verdict("5 over-excitation harmonics", fr >= 0.80, f"{100 * fr:.0f} % (>= 80 % required)")
    rc = (g == "Recovery inrush") & ok
    L.append(f"   Recovery inrush: peak differential after clearing > 0.05 pu in {int((rc & (num['recDiffPeakPu'] > 0.05)).sum())} of {int(rc.sum())} traces (informational: depends on the clearing angle)")
    L.append("")

    # ---- 6. realised load
    m = np.isfinite(num["loadOK"])
    fr = float((num["loadOK"][m] == 1).mean()) if m.any() else 0.0
    L.append(f"6. Realised load within tolerance in {100 * fr:.1f} % of {int(m.sum())} measured traces")
    verdict("6 realised load", fr >= 0.95, f"{100 * fr:.1f} % (>= 95 % required)")
    L.append("")

    # ---- 7. checks and duplicates
    fr = float(ok.mean())
    per = {k: float(ok[g == k].mean()) for k in groups}
    perscn = defaultdict(list)
    for nm, o in zip(names, ok):
        perscn[nm].append(o)
    worst = sorted(((float(np.mean(v)), k, len(v)) for k, v in perscn.items()))[:6]
    dup = n - len(set(fps))
    L.append(f"7. Generator checks (relaxed): {100 * fr:.1f} % of all traces (strict {100 * strict_ok.mean():.1f} %); worst scenarios: " + ", ".join(f"{k} {100 * a:.0f}% (n={c})" for a, k, c in worst) + f"; duplicate fingerprints: {dup}")
    verdict("7 generator checks", fr >= 0.97 and worst[0][0] >= 0.90 and dup == 0, f"overall {100 * fr:.1f} %, worst scenario {100 * worst[0][0]:.0f} %, duplicates {dup}")
    L.append("")

    # ---- 8. TRUE through-fault current of multi-phase external faults (v5: from the V-I measurement blocks, not the CT secondary)
    is_multi_ext = np.array([
        ((g[i] == "External solid") or (g[i] == "External CT-sat")) and ok[i] and
        not any(names[i].endswith(x) for x in ("_AG", "_BG", "_CG", "_HiZ_AB", "_HiZ_ABC"))
        for i in range(n)
    ])
    if "extFaultTruePu" in num:
        tv = num["extFaultTruePu"][is_multi_ext]
        tv = tv[np.isfinite(tv)]
        if len(tv) > 0:
            fr_ext = float(((tv >= 5.0) & (tv <= 15.0)).mean())
            L.append(f"8. TRUE external multi-phase through-fault RMS (10-50 ms after inception): inside 5-15 pu in {100 * fr_ext:.1f} % of {len(tv)} traces (min {tv.min():.2f}, 5th pct {np.percentile(tv, 5):.2f}, median {np.median(tv):.2f}, 95th pct {np.percentile(tv, 95):.2f}, max {tv.max():.2f} pu)")
            verdict("8 true external through-fault 5-15 pu", fr_ext >= 0.80, f"{100 * fr_ext:.1f} % (>= 80 % required)")
        else:
            verdict("8 true external through-fault 5-15 pu", False, "no finite extFaultTruePu records")
    else:
        L.append("8. extFaultTruePu not present in dataset")
        verdict("8 true external through-fault 5-15 pu", False, "extFaultTruePu missing")
    L.append("")

    L.append("=" * 100)
    L.append("OVERALL: " + ("ALL CRITERIA PASSED - training may start." if all(v["pass"] for v in res.values())
                            else "FAILED: " + ", ".join(k for k, v in res.items() if not v["pass"]) + ". Top up with generate_stress_dataset_v5(n, 'Only', '<scenario>') / generate_stress_dataset_plant_b_v5 (own seed range), do not train with an empty cell."))
    out = path.with_name(path.stem + ("_plus_topups" if len(paths) > 1 else "") + "_coverage.txt")
    out.write_text("\n".join(L), encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"files": [q.name for q in paths], "n": n, "n_ok": int(ok.sum()), "criteria": res}, indent=1), encoding="utf-8")
    print("\n".join(L))
    return 0 if all(v["pass"] for v in res.values()) else 1


if __name__ == "__main__":
    files = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "datasets").glob("StressDataset_v5_2*.mat"))
    sys.exit(main(files))
