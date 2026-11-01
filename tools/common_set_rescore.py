"""N1b: re-score the proposed relay and the 87T baselines on the common set (traces that exist in the original AND the 20 kHz data sets), from saved
per-trace rows only (no retraining). Output: runs/20261101_v5_common_set/summary.json / .txt"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "20261101_v5_common_set"
cv = ROOT / "runs" / "20261029_v5_cv5_seeds"
cache = np.load(cv / "traces_cache.npz", allow_pickle=True)["traces"]
key = [(t["source_file"], int(t["source_index"])) for t in cache]
miss = set()
for l in (ROOT / "documents" / "baselines" / "hr_missing_traces.txt").read_text().splitlines()[2:]:
    f, i, *_ = [x.strip() for x in l.split(",")]
    miss.add((f, int(i)))
excl = np.array([k in miss for k in key])
VAR = ["Hybrid + AI-alone path", "LSTM alone", "87T alone"]


def score(rows):
    head = [r for r in rows if not r.get("undetectable")]
    f = [r["correct"] for r in head if r["should_trip"]]; h = [r["correct"] for r in head if not r["should_trip"]]
    return 100 * np.mean(f), 100 * np.mean(h), len(f), len(h)


res, L = {}, [f"Common set vs full set (plant A main, CV x 3 seeds x 5 folds); {int(excl.sum())} of {len(key)} kept traces excluded", f"{'variant':26s} {'full dep':>9s} {'common dep':>11s} {'delta':>7s} | {'full sec':>9s} {'common sec':>11s} {'delta':>7s}  (mean over 3 seeds of pooled folds)"]
for v in VAR:
    A, B = [], []
    for sd in sorted(p for p in cv.glob("seed_*")):
        rows = [r for k in range(1, 6) for r in json.load(open(sd / f"fold{k}" / "result.json"))["rows"][v]]
        A.append(score(rows)); B.append(score([r for r in rows if not excl[r["trace"]]]))
    a, b = np.mean(A, 0), np.mean(B, 0)
    res[v] = {"full": a.tolist(), "common": b.tolist(), "per_seed_full": [list(x) for x in A], "per_seed_common": [list(x) for x in B]}
    L.append(f"{v:26s} {a[0]:9.2f} {b[0]:11.2f} {b[0]-a[0]:+7.2f} | {a[1]:9.2f} {b[1]:11.2f} {b[1]-a[1]:+7.2f}")
hm = json.load(open(ROOT / "runs" / "20261029_v5_harmonic87t" / "summary.json"))["variants"]["per_phase"]["rows"]
idx2 = {i: t for i, t in enumerate(cache)}
a = score([dict(r, correct=bool(r["tripped"] and not r.get("early")) if r["should_trip"] else not r["tripped"]) for r in hm if not r.get("undetectable")])
b = score([dict(r, correct=bool(r["tripped"] and not r.get("early")) if r["should_trip"] else not r["tripped"]) for r in hm if not r.get("undetectable") and key[r["trace_idx"]] not in miss]) if all(r["trace_idx"] < len(key) for r in hm) else None
if b is not None:
    L.append(f"{'Harmonic 87T per-phase':26s} {a[0]:9.2f} {b[0]:11.2f} {b[0]-a[0]:+7.2f} | {a[1]:9.2f} {b[1]:11.2f} {b[1]-a[1]:+7.2f}  (single pass over all traces)")
    res["harmonic_per_phase"] = {"full": list(a), "common": list(b)}
OUT.joinpath("summary.json").write_text(json.dumps(res, indent=1)); OUT.joinpath("summary.txt").write_text("\n".join(L))
print("\n".join(L))
