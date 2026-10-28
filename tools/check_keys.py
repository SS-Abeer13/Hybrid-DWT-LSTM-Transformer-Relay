import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "runs/20261027_v4_cv5_seeds/seed_20261021/fold1/result.json") as fp:
    d = json.load(fp)
h = d["summary"]["variants"]["Hybrid + AI-alone path"]
print("Keys in summary.variants:", list(h.keys()))
for k, v in h.items():
    if not isinstance(v, (list, dict)):
        print(f"  {k}: {v}")
