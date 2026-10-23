"""Repeat the plant-compensated training/evaluation over several seeds (each seed = new by-trace split + new init).

    python lstm_models/run_multiseed.py            # seeds below, sequential, resumable (skips finished runs)
    python lstm_models/run_multiseed.py --aggregate-only

Output: runs/20261020_multiseed/seed_<n>/ (report_trained.json ...) and runs/20261020_multiseed/summary.json / summary.txt.
The existing run runs/20261020_v2_plant (seed 20261018) is included in the summary as one more repetition.
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "20261020_multiseed_v3"
DATA = "datasets/StressDataset_v2_20261020_005715.mat"
SEEDS = [11, 22, 33, 44, 55]
BASE = ROOT / "runs" / "20261020_v3_87tfix"


def run_one(seed: int) -> None:
    d = OUT / f"seed_{seed}"
    if (d / "report_trained.json").is_file():
        print(f"seed {seed}: done, skipping", flush=True)
        return
    d.mkdir(parents=True, exist_ok=True)
    cache = d / "unique_traces_cache.npz"
    if not cache.is_file():
        shutil.copy(BASE / "unique_traces_cache.npz", cache)      # same plant features, saves the rebuild
    cmd = [sys.executable, str(ROOT / "lstm_models" / "train_trace_split.py"), "--files", DATA, "--run-dir", str(d),
           "--features", "plant", "--dep-tolerance", "2", "--seed", str(seed)]
    print("running:", " ".join(cmd), flush=True)
    with open(d / "train_log.txt", "w") as log:
        subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)


def load(d: Path) -> dict:
    r = json.load(open(d / "report_trained.json"))
    t = r["test_relay"]
    return {"run": d.name, "seed": r["config"].get("seed"), "threshold": r["threshold"],
            "auc": r["test_window_metrics"].get("auc", r["test_window_metrics"].get("roc_auc")),
            "dep": t["dependability_pct"], "sec": t["security_pct"], "missed": t["missed_trips"],
            "false": t["false_trips"], "pre": t["trips_before_fault_onset"],
            "n_fault": t["n_fault_traces"], "n_healthy": t["n_healthy_traces"],
            "med_ms": t["operate_time"].get("median_ms"), "p90_ms": t["operate_time"].get("p90_ms"),
            "max_ms": t["operate_time"].get("max_ms"), "w1": t["operate_time"].get("within_1_cycle_pct"),
            "w2": t["operate_time"].get("within_2_cycles_pct"),
            "cat": {k: v["correct_pct"] for k, v in t["by_category"].items()}}


def aggregate() -> None:
    dirs = [BASE] + [OUT / f"seed_{s}" for s in SEEDS if (OUT / f"seed_{s}" / "report_trained.json").is_file()]
    rows = [load(d) for d in dirs]
    lines = [f"Repeated by-trace splits, plant-compensated features, dwell 20 ({len(rows)} runs)", ""]
    lines.append(f"{'run':22s} {'seed':>10s} {'thr':>7s} {'dep%':>6s} {'sec%':>6s} {'miss':>4s} {'false':>5s} {'pre':>3s} {'med ms':>7s} {'max ms':>7s} {'<=1cyc%':>7s} {'<=2cyc%':>7s}")
    for r in rows:
        lines.append(f"{r['run']:22s} {str(r['seed']):>10s} {r['threshold']:7.4f} {r['dep']:6.1f} {r['sec']:6.1f} {r['missed']:4d} {r['false']:5d} {r['pre']:3d} "
                     f"{r['med_ms']:7.1f} {r['max_ms']:7.1f} {r['w1']:7.1f} {r['w2']:7.1f}")
    def ms(k):
        v = np.array([r[k] for r in rows], float)
        return v.mean(), v.std(ddof=1) if len(v) > 1 else 0.0, v.min(), v.max()
    lines += ["", f"{'metric':12s} {'mean':>8s} {'sd':>7s} {'min':>8s} {'max':>8s}"]
    for k, n in [("dep", "dependability%"), ("sec", "security%"), ("med_ms", "median ms"), ("max_ms", "max ms"), ("w1", "<=1 cycle%"), ("w2", "<=2 cycles%")]:
        a, s, lo, hi = ms(k)
        lines.append(f"{n:14s} {a:8.2f} {s:7.2f} {lo:8.2f} {hi:8.2f}")
    tot_f = sum(r["missed"] for r in rows); tot_ff = sum(r["n_fault"] for r in rows)
    tot_h = sum(r["false"] for r in rows); tot_hh = sum(r["n_healthy"] for r in rows)
    lines += ["", f"Pooled over runs: missed {tot_f}/{tot_ff} faults, false trips {tot_h}/{tot_hh} healthy, pre-fault trips {sum(r['pre'] for r in rows)}",
              "(test sets overlap between runs: pooled counts are not independent samples)", "", "Per-category correct % (mean over runs, min):"]
    cats = sorted({c for r in rows for c in r["cat"]})
    for c in cats:
        v = [r["cat"][c] for r in rows if c in r["cat"]]
        lines.append(f"  {c:22s} mean {np.mean(v):6.1f}  min {np.min(v):6.1f}  (n runs {len(v)})")
    (OUT / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--aggregate-only", action="store_true"); a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not a.aggregate_only:
        for s in SEEDS:
            run_one(s)
    aggregate()
