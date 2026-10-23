"""Option 2 (AI-alone trip path): re-evaluate the 6 corrected-87T checkpoints with a validation-tuned solo threshold (no retraining).
Writes runs/20261020_multiseed_v3_solo/ and summary_solo.txt (compares with the gated-only hybrid in runs/20261020_multiseed_v3)."""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
SRC = {20261018: ROOT / "runs" / "20261020_v3_87tfix", **{s: ROOT / "runs" / "20261020_multiseed_v3" / f"seed_{s}" for s in (11, 22, 33, 44, 55)}}
OUT = ROOT / "runs" / "20261020_multiseed_v3_solo"
DATA = "datasets/StressDataset_v2_20261020_005715.mat"
rows = []
for seed, src in SRC.items():
    d = OUT / f"seed_{seed}"; d.mkdir(parents=True, exist_ok=True)
    if not (d / "unique_traces_cache.npz").is_file():
        shutil.copy(src / "unique_traces_cache.npz", d / "unique_traces_cache.npz")
    tag = "existing_" + src.name
    if not (d / f"report_{tag}.json").is_file():
        subprocess.run([sys.executable, str(ROOT / "lstm_models" / "train_trace_split.py"), "--files", DATA, "--run-dir", str(d), "--features", "plant",
                        "--dep-tolerance", "2", "--solo", "--seed", str(seed), "--write-settings",
                        "--evaluate-only", str(src / "transformer_protection_lstm_best.pth")],
                       cwd=ROOT, check=True, stdout=open(d / "eval_log.txt", "w"), stderr=subprocess.STDOUT)
    r = json.load(open(d / f"report_{tag}.json")); t = r["test_relay"]; v = r["validation_relay"]
    g = json.load(open(src / "report_trained.json"))["test_relay"]
    rows.append(dict(seed=seed, thr=r["threshold"], solo=r["solo_threshold"], dep=t["dependability_pct"], sec=t["security_pct"], missed=t["missed_trips"],
                     false=t["false_trips"], pre=t["trips_before_fault_onset"], n_f=t["n_fault_traces"], n_h=t["n_healthy_traces"], med=t["operate_time"]["median_ms"],
                     mx=t["operate_time"]["max_ms"], w1=t["operate_time"]["within_1_cycle_pct"], w2=t["operate_time"]["within_2_cycles_pct"],
                     gdep=g["dependability_pct"], gsec=g["security_pct"], gmed=g["operate_time"]["median_ms"],
                     cat={k: x["correct_pct"] for k, x in t["by_category"].items()}, gcat={k: x["correct_pct"] for k, x in g["by_category"].items()}))
L = ["Option 2: 87T-gated LSTM + AI-alone trip (solo threshold tuned on validation); same 6 checkpoints, corrected 87T", "",
     f"{'seed':>9s} {'thr':>6s} {'solo':>7s} | {'dep% gated/solo':>16s} {'sec% gated/solo':>16s} {'med ms g/s':>11s} | {'miss':>4s} {'false':>5s} {'pre':>3s} {'max ms':>7s} {'<=1cyc':>6s} {'<=2cyc':>6s}"]
for r in rows:
    L.append(f"{r['seed']:9d} {r['thr']:6.3f} {str(r['solo']):>7s} | {r['gdep']:7.1f}/{r['dep']:6.1f} {r['gsec']:8.1f}/{r['sec']:6.1f} {r['gmed']:5.1f}/{r['med']:5.1f} | {r['missed']:4d} {r['false']:5d} {r['pre']:3d} {r['mx']:7.1f} {r['w1']:6.1f} {r['w2']:6.1f}")
def ms(k): v = np.array([r[k] for r in rows], float); return f"{v.mean():.2f} (sd {v.std(ddof=1):.2f}) [{v.min():.2f}-{v.max():.2f}]"
L += ["", f"dependability  gated-only {np.mean([r['gdep'] for r in rows]):.1f}  ->  solo {ms('dep')}", f"security       gated-only {np.mean([r['gsec'] for r in rows]):.1f}  ->  solo {ms('sec')}",
      f"median operate (ms) {ms('med')}", f"within 1 cycle (%) {ms('w1')}", f"within 2 cycles (%) {ms('w2')}", f"max operate (ms) {ms('mx')}",
      f"pooled: missed {sum(r['missed'] for r in rows)}/{sum(r['n_f'] for r in rows)}, false trips {sum(r['false'] for r in rows)}/{sum(r['n_h'] for r in rows)}, pre-fault {sum(r['pre'] for r in rows)}", "",
      "Per-category correct % (mean over runs): gated-only -> solo"]
for c in sorted({k for r in rows for k in r["cat"]}):
    L.append(f"  {c:22s} {np.mean([r['gcat'][c] for r in rows if c in r['gcat']]):6.1f} -> {np.mean([r['cat'][c] for r in rows if c in r['cat']]):6.1f}   (min solo {np.min([r['cat'][c] for r in rows if c in r['cat']]):.1f})")
(OUT / "summary_solo.txt").write_text("\n".join(L), encoding="utf-8"); print("\n".join(L))
