"""Re-tune the threshold of the 6 plant-compensated checkpoints with the plateau rule (no retraining) and compare spreads.
Writes runs/20261020_multiseed_plateau/ (eval-only reports) and summary_plateau.txt."""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
SRC = {20261018: ROOT / "runs" / "20261020_v2_plant", **{s: ROOT / "runs" / "20261020_multiseed" / f"seed_{s}" for s in (11, 22, 33, 44, 55)}}
OUT = ROOT / "runs" / "20261020_multiseed_plateau"
DATA = "datasets/StressDataset_v2_20261020_005715.mat"
rows = []
for seed, src in SRC.items():
    d = OUT / f"seed_{seed}"; d.mkdir(parents=True, exist_ok=True)
    if not (d / "unique_traces_cache.npz").is_file():
        shutil.copy(src / "unique_traces_cache.npz", d / "unique_traces_cache.npz")
    tag = "existing_" + src.name
    if not (d / f"report_{tag}.json").is_file():
        subprocess.run([sys.executable, str(ROOT / "lstm_models" / "train_trace_split.py"), "--files", DATA, "--run-dir", str(d),
                        "--features", "plant", "--dep-tolerance", "2", "--threshold-mode", "plateau", "--seed", str(seed),
                        "--evaluate-only", str(src / "transformer_protection_lstm_best.pth")],
                       cwd=ROOT, check=True, stdout=open(d / "eval_log.txt", "w"), stderr=subprocess.STDOUT)
    r = json.load(open(d / f"report_{tag}.json")); t = r["test_relay"]; v = r["validation_relay"]
    old = json.load(open(src / "report_trained.json"))
    rows.append(dict(seed=seed, thr=r["threshold"], old_thr=old["threshold"], dep=t["dependability_pct"], sec=t["security_pct"],
                     missed=t["missed_trips"], false=t["false_trips"], pre=t["trips_before_fault_onset"], n_f=t["n_fault_traces"], n_h=t["n_healthy_traces"],
                     med=t["operate_time"]["median_ms"], mx=t["operate_time"]["max_ms"], w1=t["operate_time"]["within_1_cycle_pct"],
                     w2=t["operate_time"]["within_2_cycles_pct"], vdep=v["dependability_pct"], vsec=v["security_pct"],
                     old_dep=old["test_relay"]["dependability_pct"], old_sec=old["test_relay"]["security_pct"],
                     old_med=old["test_relay"]["operate_time"]["median_ms"]))
L = ["Threshold rule: plateau centre (logit) vs previous validation argmax - same 6 checkpoints, no retraining", "",
     f"{'seed':>9s} {'old thr':>8s} {'new thr':>8s} | {'dep% old/new':>13s} {'sec% old/new':>13s} {'med ms old/new':>15s} | {'miss':>4s} {'false':>5s} {'pre':>3s} {'max ms':>7s} {'<=2cyc%':>7s}"]
for r in rows:
    L.append(f"{r['seed']:9d} {r['old_thr']:8.4f} {r['thr']:8.4f} | {r['old_dep']:6.1f}/{r['dep']:5.1f} {r['old_sec']:6.1f}/{r['sec']:5.1f} {r['old_med']:7.1f}/{r['med']:6.1f} | {r['missed']:4d} {r['false']:5d} {r['pre']:3d} {r['mx']:7.1f} {r['w2']:7.1f}")
def ms(k): v = np.array([r[k] for r in rows], float); return f"{v.mean():.2f} (sd {v.std(ddof=1):.2f}) [{v.min():.2f}-{v.max():.2f}]"
lg = lambda x: np.log(np.array(x) / (1 - np.array(x)))
L += ["", f"threshold  old: sd of logit {lg([r['old_thr'] for r in rows]).std(ddof=1):.2f}  range {min(r['old_thr'] for r in rows)}-{max(r['old_thr'] for r in rows)}",
      f"threshold  new: sd of logit {lg([r['thr'] for r in rows]).std(ddof=1):.2f}  range {min(r['thr'] for r in rows)}-{max(r['thr'] for r in rows)}", "",
      f"test dependability   {ms('dep')}", f"test security        {ms('sec')}", f"median operate (ms)  {ms('med')}", f"within 1 cycle (%)   {ms('w1')}", f"within 2 cycles (%)  {ms('w2')}",
      f"max operate (ms)     {ms('mx')}", f"pooled: missed {sum(r['missed'] for r in rows)}/{sum(r['n_f'] for r in rows)}, false trips {sum(r['false'] for r in rows)}/{sum(r['n_h'] for r in rows)}, pre-fault {sum(r['pre'] for r in rows)}"]
(OUT / "summary_plateau.txt").write_text("\n".join(L), encoding="utf-8"); print("\n".join(L))
