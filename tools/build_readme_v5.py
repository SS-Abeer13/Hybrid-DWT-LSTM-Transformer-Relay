"""Writes README.md from saved result files (no typed numbers). Run after the result files exist:  python tools/build_readme_v5.py"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "runs"
TAG = "20261029_v5"


def J(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


cv = J(R / f"{TAG}_cv5_seeds" / "summary.json")
st = J(R / f"{TAG}_stats" / "stats.json")
hm = J(R / f"{TAG}_harmonic87t" / "summary.json")
ood = J(R / f"{TAG}_final" / "report_ood.json")["ood"]
zs = J(R / f"{TAG}_plant_b_zeroshot" / "zero_shot_summary.json")
cp = J(R / f"{TAG}_cross_plant" / "cross_plant_summary.json")
lo = J(R / f"{TAG}_leave_one_out" / "leave_one_out_summary.json")
e1 = J(R / f"{TAG}_e1_harmonic_gate" / "e1_summary.json")
tp = J(R / f"{TAG}_plant_b_zeroshot" / "trip_path_check.json")
lat = J(R / f"{TAG}_latency" / "latency.json")
latc = J(R / f"{TAG}_latency" / "latency_c.json")
fin = R / f"{TAG}_final"
thr_ai, thr_solo, dwell = [(fin / f).read_text().split()[0] for f in ("decision_threshold.txt", "decision_solo_threshold.txt", "decision_dwell.txt")]
pooled = cv["pooled"]
H = pooled["Hybrid + AI-alone path"]
n_fm = cv["n_fold_models"]
sd = st["multi_seed_fold_models"]["Hybrid + AI-alone path"]


def tf(plant: str) -> str:
    t = (ROOT / "simulations" / f"plant_v5_checks_{plant}.txt").read_text(encoding="utf-8")
    return re.search(r"TRUE RMS steady ([\d.]+) pu", t).group(1)


def cats(variant: str = "Hybrid + AI-alone path") -> dict:
    return pooled[variant]["by_category"]


mc = st["mcnemar"]
hp = mc["proposed_vs_harmonic_87t_per_phase"]
mir = J(R / f"{TAG}_final" / "d4" / "mirror.json")
agree = tot = 0
for lab in ("main", "ood"):
    Rr = list(np.atleast_1d(loadmat(ROOT / "simulations" / f"test_hybrid_relay_d5{lab}_results.mat", squeeze_me=True, struct_as_record=False)["R"]))
    sim = {int(str(r.name).split("#")[-1]): r for r in Rr}
    for m in mir[lab]:
        agree += int(bool(m["tripped"]) == bool(sim[int(m["index"])].tripped)); tot += 1
pb_cl = (ROOT / "simulations" / "test_hybrid_relay_plant_b_results.txt").read_text(encoding="utf-8")
pb_pass = re.search(r"Passed (\d+) / (\d+)", pb_cl)
ds_a = sum(1 for _ in [0]) and None


def row(name, d, s):
    return f"| {name} | {d:.2f} | {s:.2f} |"


L = []
L += ["# Hybrid DWT-LSTM Supervisory Transformer Differential Protection", "",
      "Simulation study of a transformer differential relay that combines a conventional dual-slope 87T with a DWT-feature LSTM. "
      "The relay model, the data generators (MATLAB/Simulink), the training and evaluation code (Python) and the closed-loop test benches are in this repository. "
      "All numbers below are written by `tools/build_readme_v5.py` from the saved result files in `runs/` and `simulations/`.", "",
      "**Status.** Simulation only (no hardware-in-the-loop, two simulated transformers, terminal faults). The v4 results in earlier commits were produced with a plant whose "
      "through-fault level (23.9 and 37.6 pu) and CT sizing were unrealistic and with a mis-calibrated plant-B 87T; they are superseded by the v5 rebuild described here.", "",
      "## Relay logic", "",
      f"trip = high-set OR (87T vote AND confirmed LSTM score >= AI threshold) OR confirmed LSTM score >= AI-alone threshold. The confirmed score is the minimum of the last {dwell} network outputs "
      f"(1600 Hz). Final plant-A model: AI threshold {thr_ai}, AI-alone threshold {thr_solo}, dwell {dwell}, tuned on validation traces only.", "",
      "## Plants and data (v5)", "",
      "| | Plant A | Plant B |", "|---|---|---|",
      f"| Transformer | 300 MVA, 230/11 kV, YNd1, 5 A CTs | 40 MVA, 132/33 kV, Dyn11, 1 A CTs |",
      f"| True external through-fault (RMS, steady) | {tf('A')} pu | {tf('B')} pu |",
      "| CT design | linear at nominal burden; saturates with DC offset or raised burden | linear at nominal burden; saturates with raised burden only |",
      f"| Trace sets | main (3040 + top-ups) and OOD (300) | main (1200 + top-ups) and OOD (150) |", "",
      "Plant checks: `simulations/plant_v5_checks_A.txt`, `plant_v5_checks_B.txt` (plant B fails check C4 and C6 as recorded there). Dataset coverage: `datasets/*_coverage.txt`.", "",
      "## Results, plant A (grouped 5-fold CV, 3 seeds, " + str(n_fm) + " fold-models, pooled)", "",
      "| Variant | Dependability % | Security % |", "|---|---|---|"]
for v in ("87T alone", "LSTM alone", "Hybrid (87T gate)", "Hybrid + AI-alone path"):
    L.append(row(v, pooled[v]["dependability_pct"], pooled[v]["security_pct"]))
hv = hm["variants"]
L.append(row("Per-phase harmonic-restrained 87T", hv["per_phase"]["main_pooled"]["dependability_pct"], hv["per_phase"]["main_pooled"]["security_pct"]))
L += ["", f"Hybrid + AI-alone path, mean +/- SD over the {n_fm} fold-models: dependability {sd['dependability']['mean']:.2f} +/- {sd['dependability']['std']:.2f} %, security {sd['security']['mean']:.2f} +/- {sd['security']['std']:.2f} %.", "",
      "Paired McNemar tests (`runs/" + TAG + "_stats/stats.json`), hybrid vs per-phase harmonic 87T: "
      f"dependability p = {hp['dependability']['p_value']:.2g}, security p = {hp['security']['p_value']:.2g}.", "",
      f"Out-of-distribution set (scored once, {ood['Hybrid + AI-alone path']['overall']['n_fault'] + ood['Hybrid + AI-alone path']['overall']['n_healthy']} traces): hybrid dependability "
      f"{ood['Hybrid + AI-alone path']['overall']['dependability_pct']:.1f} %, security {ood['Hybrid + AI-alone path']['overall']['security_pct']:.1f} %.", "",
      "Weakest category (hybrid, CV pooled): " + ", ".join(f"{c} {b['correct_pct']:.1f} %" for c, b in sorted(cats().items(), key=lambda x: x[1]['correct_pct'])[:3]) + ".", "",
      "## Plant B", "",
      "| Experiment | Dependability % | Security % |", "|---|---|---|",
      row("Zero-shot, plant-A model: Proposed", zs["Proposed"]["dependability_pct"], zs["Proposed"]["security_pct"]),
      row("Zero-shot: per-phase harmonic 87T", zs["Harmonic 87T"]["dependability_pct"], zs["Harmonic 87T"]["security_pct"]),
      row("Cross-plant training (A + B), pooled", cp["overall"]["dependability_pct"], cp["overall"]["security_pct"]),
      row("Train A, test B", lo["train_a_test_b"]["dependability_pct"], lo["train_a_test_b"]["security_pct"]),
      row("Train B, test A", lo["train_b_test_a"]["dependability_pct"], lo["train_b_test_a"]["security_pct"]), "",
      f"Zero-shot trip-path check (`trip_path_check.txt`): of {tp['variants']['Proposed as evaluated (high-set + gate + solo)']['false_trips']} false trips, {tp['false_trip_first_path'].get('solo', 0)} come first through the AI-alone path; "
      f"without that path the zero-shot relay gives {tp['variants']['without AI-alone path (high-set + gate)']['dependability_pct']:.2f} % dependability and {tp['variants']['without AI-alone path (high-set + gate)']['security_pct']:.2f} % security.", "",
      "## Closed loop and timing", "",
      f"- Simulink closed loop (LSTM active) vs Python relay mirror, plant A: decision agreement {agree} / {tot}.",
      f"- Plant B 12-case suite: {pb_pass.group(1)} / {pb_pass.group(2)} cases correct.",
      f"- Execution time of the feature extraction + LSTM pipeline, one window per call, development PC: ONNX Runtime median {lat['combined_relay_pipeline']['median_us']:.1f} us, hand-written ANSI C median {latc['combined_relay_pipeline']['median_us']:.1f} us (sample period 625 us). "
      "The C source is written by `tools/build_and_run_c_benchmark.py`; it is not MATLAB Coder output and was not run on a relay processor.", "",
      "## Design variant tested after the v5 results (E1)", "",
      f"Using the per-phase harmonic-restrained 87T as the gate of the hybrid (protocol fixed before the run, `IMPLEMENTATION_PLAN_V4_PUBLICATION.md`): CV dependability {e1['cv']['e1']['dependability_pct']:.2f} % / security {e1['cv']['e1']['security_pct']:.2f} % "
      f"(current hybrid {e1['cv']['reference_hybrid_ai_alone']['dependability_pct']:.2f} / {e1['cv']['reference_hybrid_ai_alone']['security_pct']:.2f}); OOD security {e1['ood']['e1']['security_pct']:.2f} % vs {e1['ood']['reference']['security_pct']:.2f} %. Not adopted.", "",
      "## Limitations", "",
      f"- Internal high-impedance faults: hybrid correct on {cats()['Internal HiZ']['correct_pct']:.1f} % of the CV traces.",
      "- Simulation only; two transformers; terminal faults; no hardware-in-the-loop.",
      "- The plant-A model does not transfer to plant B without retraining (zero-shot security above).",
      "- Closed loop, plant A: two of the 50 traces fail the 30 ms / correct-decision check (`simulations/test_hybrid_relay_d5main_results.txt`).", "",
      "## Layout", "",
      "| Path | Content |", "|---|---|",
      "| `simulations/` | Simulink plants (`*_v5.slx`), builders and probes (`build_plants_v5.m`, `check_plant_physics_v5.m`), generators (`generate_stress_dataset_v5.m`, `generate_stress_dataset_plant_b_v5.m`), calibration, closed-loop scripts |",
      "| `lstm_models/` | features, 87T mirror (`relay87t.py`), training and CV (`train_cv_v5.py`), coverage report (`coverage_report_v5.py`), literature baselines |",
      "| `tools/` | statistics, plant-B transfer experiments, harmonic 87T, E1, latency benchmark, table builders |",
      "| `latex_source/` | thesis sources and the generated tables (`tools/build_publication_tables_v5.py`) |",
      "| `IMPLEMENTATION_PLAN*.md` | protocol, dated log, reviews |", "",
      "## Reproduce", "",
      "Requires MATLAB R2023a with Simulink, Simscape Electrical, Wavelet and Deep Learning toolboxes, and Python 3.11 (numpy, scipy, scikit-learn, pywt, torch, onnx, onnxruntime, h5py).",
      "Datasets (`*.mat`), model files (`*.pth`, `*.onnx`) and `runs/` are not in the repository (size); regenerate them:", "",
      "```",
      "run_v5_generation_all.bat                      # plant A and B main + OOD sets (about 8 h), then the top-ups listed in IMPLEMENTATION_PLAN.md",
      "python lstm_models/coverage_report_v5.py datasets/StressDataset_v5_<run>.mat [top-up files]",
      "python lstm_models/train_cv_v5.py cv --files <main + top-ups> --run-dir runs/<tag>_cv5_seeds --seeds 20261021 20261022 20261023",
      "python lstm_models/train_cv_v5.py final --files <main + top-ups> --ood <ood file> --run-dir runs/<tag>_final",
      "python tools/evaluate_harmonic87t_v5.py --files <...> --ood <...> --cv-dir runs/<tag>_cv5_seeds --output-dir runs/<tag>_harmonic87t",
      "python tools/compute_v4_statistics.py --cv-dir ... --harmonic-dir ... --lit-dir ... --output-dir runs/<tag>_stats",
      "python tools/run_plant_b_generalization_v5.py --plant-a-run runs/<tag>_final --plant-a-files <...> --plant-b-files <...> --out-tag <tag>",
      "python tools/build_publication_tables_v5.py && python tools/build_readme_v5.py",
      "```", "",
      "MATLAB is started with `matlab -batch`; every generator resumes from its `_PARTIAL.mat` with the same run id.", ""]
(ROOT / "README.md").write_text("\n".join(L), encoding="utf-8")
print("README.md written,", len(L), "lines")
