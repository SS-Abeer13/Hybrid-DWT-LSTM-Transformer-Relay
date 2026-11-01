"""Compute the Simoes et al. RT-BSWT differential energies (12.8 kHz) once for every common-set plant-A trace and store them as a memory-mapped array
(position in the CV trace list -> E). Auto-resumable. Output: runs/20261101_v5_benchmark_fair/cache/simoes_E_plantA.npy + _done.npy"""
import sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import common as C, cv, simoes2021_rtbswt_svm as S
OUT = ROOT / "runs" / "20261101_v5_benchmark_fair" / "cache"
metas, pos = cv.trace_index()
first = next(C.iter_hr(C.PLANT_A_MAIN))
E0 = S.energies(first["Ip"], first["Is"])
shape = (len(metas),) + E0.shape
f, fd = OUT / "simoes_E_plantA.npy", OUT / "simoes_E_plantA_done.npy"
if f.exists():
    arr = np.lib.format.open_memmap(f, mode="r+"); done = np.load(fd)
else:
    arr = np.lib.format.open_memmap(f, mode="w+", dtype=np.float32, shape=shape); done = np.zeros(len(metas), bool)
print("shape", shape, "already", int(done.sum()), flush=True)
t0 = time.time(); n = 0
for tr in C.iter_hr(C.PLANT_A_MAIN):
    i = pos[(tr["src"], tr["index"])]
    if done[i]:
        continue
    arr[i] = S.energies(tr["Ip"], tr["Is"]).astype(np.float32); done[i] = True; n += 1
    if n % 100 == 0:
        arr.flush(); np.save(fd, done); print(n, int(done.sum()), f"{time.time()-t0:.0f}s", flush=True)
arr.flush(); np.save(fd, done); print("done", int(done.sum()), f"{time.time()-t0:.0f}s")
