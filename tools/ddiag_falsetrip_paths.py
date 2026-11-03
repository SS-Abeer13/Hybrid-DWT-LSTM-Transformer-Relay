"""D-diag: through which path do the plant-B false trips of the deployed hybrid (plant-A final model, AI 0.995, solo 0.998, dwell 20, nothing retuned) come?
Reads the script-written runs/20261029_v5_plant_b_zeroshot/trip_path_check.json (tools/plantb_trip_path_v5.py). Output: runs/20261101_v5_benchmark_fair/plantB_falsetrip_paths.txt"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "runs" / "20261029_v5_plant_b_zeroshot" / "trip_path_check.json").read_text())
v = d["variants"]; k_full = "Proposed as evaluated (high-set + gate + solo)"; k_ng = "without AI-alone path (high-set + gate)"
full, nosolo = v[k_full], v[k_ng]
ft = d["false_trip_first_path"]; n_ft = sum(ft.values())
cats = d["false_trips_by_category"]
fam = {}
for c, p in cats.items():
    f = "Stress_ExtCTSat" if c.startswith("Stress_ExtCTSat") else c
    fam[f] = fam.get(f, 0) + sum(x for kk, x in p.items() if not kk.startswith("_"))
L = ["Plant B zero-shot, deployed hybrid (thresholds frozen from plant A: AI %s, solo %s, dwell %s); source: trip_path_check.json" % (d["thresholds"]["ai"], d["thresholds"]["solo"], d["thresholds"]["dwell"]),
     f"as evaluated: false trips {n_ft} of 764 detectable healthy traces; first path that fired: " + ", ".join(f"{k} {x} ({100*x/n_ft:.1f} %)" for k, x in ft.items()) + ", high-set 0",
     f"traces where both the gated path and the AI-alone path fired: {d['false_trips_with_gate_and_solo_both']}",
     f"false trips by family: " + ", ".join(f"{k} {x}" for k, x in sorted(fam.items(), key=lambda t: -t[1])),
     "counterfactual (same traces, same thresholds): switch the AI-alone (solo) path off -> " + json.dumps({k: full_ if False else nosolo[k] for k, full_ in [(kk, 0) for kk in nosolo]}, default=str),
     f"   as evaluated: {json.dumps(full, default=str)}",
     f"faults tripped ONLY by the AI-alone path: {d['faults_tripped_only_by_solo']} of 493 ({100*d['faults_tripped_only_by_solo']/493:.1f} %)",
     "", "Reading: the plant-B security loss comes from the AI-alone (solo) path, not from the 87T-gated path. Per the decision table this goes into the limitations as 'the solo path is the transfer weakness'; the solo threshold is NOT changed (that would be tuning on plant B)."]
(ROOT / "runs" / "20261101_v5_benchmark_fair" / "plantB_falsetrip_paths.txt").write_text("\n".join(L), encoding="utf-8"); print("\n".join(L))
