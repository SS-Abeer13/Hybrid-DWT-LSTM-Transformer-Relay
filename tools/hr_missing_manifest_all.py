"""N1a: traces of the original data sets (plant A main, plant A OOD, plant B main, plant B OOD) without a 20 kHz re-simulation, per scenario group.
Uses all traces of the original files (before the generator checks / de-duplication of the training pipeline)."""
import sys, re, collections
from pathlib import Path
import h5py, numpy as np
from scipy.io import loadmat
ROOT = Path(__file__).resolve().parent.parent
HR = ROOT / "datasets" / "hr"
SETS = {
 "plantA_main": [("StressDataset_v5HR_20261028_162333", "StressDataset_v5_20261028_162333.mat"), ("StressDataset_v5HROnly_20261028_232627", "StressDataset_v5Only_20261028_232627.mat"), ("StressDataset_v5HROnly_20261028_233305", "StressDataset_v5Only_20261028_233305.mat"), ("StressDataset_v5HROnly_20261028_234041", "StressDataset_v5Only_20261028_234041.mat"), ("StressDataset_v5HROnly_20261029_111722", "StressDataset_v5Only_20261029_111722.mat")],
 "plantA_OOD": [("StressDataset_v5HROOD_20261028_205712", "StressDataset_v5OOD_20261028_205712.mat")],
 "plantB_main": [("StressDataset_PlantBv5HR_20261028_212041", "StressDataset_PlantBv5_20261028_212041.mat"), ("StressDataset_PlantBv5HROnly_20261029_111005", "StressDataset_PlantBv5Only_20261029_111005.mat"), ("StressDataset_PlantBv5HROnly_20261029_111251", "StressDataset_PlantBv5Only_20261029_111251.mat")],
 "plantB_OOD": [("StressDataset_PlantBv5HROOD_20261029_010052", "StressDataset_PlantBv5OOD_20261029_010052.mat")],
}
def names(path):
    with h5py.File(path) as f:
        d = f["dataset"]["scenarioName"]
        return ["".join(chr(c) for c in np.array(f[r[0]]).ravel()) for r in d[:, 0:1]] if d.shape[1] == 1 else ["".join(chr(c) for c in np.array(f[r]).ravel()) for r in d[0]]
L = []
for label, runs in SETS.items():
    tot = miss = 0; bad = collections.Counter(); allc = collections.Counter(); lines = []
    for prefix, src in runs:
        nm = names(ROOT / "datasets" / src)
        have = set()
        for f in HR.glob(prefix + "_blk*.mat"):
            have.update(int(i) - 1 for i in np.asarray(loadmat(f)["idx"]).ravel())
        for i, n in enumerate(nm):
            allc[n] += 1; tot += 1
            if i not in have:
                miss += 1; bad[n] += 1; lines.append(f"  {src} index {i} {n}")
    L.append(f"{label}: {tot} original traces, {miss} without a 20 kHz copy ({100*miss/tot:.2f} %)")
    fam = lambda n: re.sub(r"_(HiZ_)?[ABCG]+$", lambda m: "_HiZ" if m.group(1) else "", n)  # noqa: E731
    fa, fb = collections.Counter(), collections.Counter()
    for n, c in allc.items():
        fa[fam(n)] += c; fb[fam(n)] += bad.get(n, 0)
    L.append("  by scenario family (phase suffix removed):")
    for n in sorted(fa, key=lambda n: -fb[n] / fa[n]):
        if fb[n]:
            L.append(f"    [family] {n:26s} {fb[n]}/{fa[n]} ({100*fb[n]/fa[n]:.1f} %)")
    for n, c in sorted(bad.items(), key=lambda x: -x[1] / allc[x[0]]):
        L.append(f"    {n:28s} {c}/{allc[n]} ({100*c/allc[n]:.1f} %)")
    L += lines
(ROOT / "documents" / "baselines" / "hr_missing_all.txt").write_text("\n".join(L), encoding="utf-8")
print("\n".join(l for l in L if not l.startswith("  ") or l.startswith("    ")))
