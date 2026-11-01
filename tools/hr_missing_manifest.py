"""D2 completeness: kept traces of the original v5 plant-A main set that have no 20 kHz re-simulation (the re-simulation flagged them as
failed: logged signals empty or shorter than 22,001 samples). All baselines are scored on the traces that exist in BOTH data sets."""
import sys
from pathlib import Path
import numpy as np
from scipy.io import loadmat
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C  # noqa: E402
meta = C.load_meta(); seen = set()
for prefix, src in C.PLANT_A_MAIN:
    for f in C.block_files(prefix):
        seen.update((src, int(i) - 1) for i in np.asarray(loadmat(f)["idx"]).ravel())
miss = sorted(k for k in meta if k not in seen)
L = [f"plant A main set: {len(meta)} kept traces, {len(miss)} without a 20 kHz re-simulation ({len(meta)-len(miss)} usable)", "source_file, 0-based index, scenario, should_trip"]
L += [f"{k[0]}, {k[1]}, {meta[k]['scenarioName']}, {meta[k]['should_trip']}" for k in miss]
(ROOT / "documents" / "baselines" / "hr_missing_traces.txt").write_text("\n".join(L), encoding="utf-8")
print(L[0])
