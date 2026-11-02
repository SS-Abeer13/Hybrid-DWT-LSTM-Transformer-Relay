"""D-N4 latency of the six reproductions, same methodology as tools/measure_latency.py (single thread, one decision per call, warm-up then timed calls,
time.perf_counter_ns, development PC, CPU only). Per method the cost of ONE decision at the method's own rate is measured and compared with the budget
(time between decisions). Networks use the LARGEST architecture of the method's search space with random weights (an upper bound; the chosen configuration of a
fold is not stored); SVM / feature costs use real data. Run on an idle machine. Output: runs/20261101_v5_benchmark_fair/latency_baselines.json / .txt"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import torch

warnings.simplefilter("ignore")
torch.set_num_threads(1)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
from baselines import abdusalam2022_dwt_omp_ga as AB  # noqa: E402
from baselines import afrasiabi2020_acnn as AF  # noqa: E402
from baselines import alhamd2024_wavelet_lstm as AL  # noqa: E402
from baselines import common as C  # noqa: E402
from baselines import hajipour2015_ct_comp as HJ  # noqa: E402
from baselines import key2025_comdnn_disdnn as KE  # noqa: E402
from baselines import ngaopitakkul2006_dwt_bpnn as NG  # noqa: E402
from baselines import simoes2021_rtbswt_svm as SI  # noqa: E402

OUT = ROOT / "runs" / "20261101_v5_benchmark_fair"


def timeit(fn, n=2000, warm=100):
    for _ in range(warm):
        fn()
    t = np.empty(n)
    for i in range(n):
        a = time.perf_counter_ns(); fn(); t[i] = (time.perf_counter_ns() - a) / 1e3
    return {"median_us": float(np.median(t)), "p99_us": float(np.percentile(t, 99)), "max_us": float(t.max()), "n": n}


def main():
    res = {}
    rng = np.random.RandomState(0)
    # ---- Afrasiabi: ACNN per decision (every 7 samples at 5.6 kHz = 1,250 us); Hajipour stage per sample
    net = AF.ACNN().eval()
    x = torch.from_numpy(rng.randn(1, 3, 7, 8).astype(np.float32)) if False else None
    w = rng.randn(3, 56).astype(np.float32)

    def acnn():
        xx = AF.window(w.T.copy(), 55) if False else (w / max(float(np.abs(w).max()), 1e-9))
        with torch.no_grad():
            return torch.sigmoid(net(torch.from_numpy(np.ascontiguousarray(xx, dtype=np.float32))[None])).item()
    res["afrasiabi_cnn_per_decision"] = {**timeit(acnn), "budget_us": AF.STEP / AF.FS * 1e6}
    sig = (np.sin(2 * np.pi * 50 * np.arange(4000) / 4000) * 8).astype(float)
    cp = HJ.ct_params("A", 1.0)
    t0 = time.perf_counter(); HJ.dsc(sig, 4000.0, cp); dt = time.perf_counter() - t0
    res["afrasiabi_hajipour_per_sample_per_signal"] = {"median_us": dt / 4000 * 1e6, "budget_us": 1e6 / 4000, "note": "1 s of a saturating-free 8 A signal; six signals per sample"}
    # ---- Key: per sample, Com-DNN on the six signals (batch 6) + Dis-DNN (192 inputs), largest search-space sizes
    com = KE.ComDNN(64).eval(); dis = KE.DisDNN(64, 32).eval() if hasattr(KE, "DisDNN") else None
    xc = torch.from_numpy(rng.randn(6, 64).astype(np.float32)); xd = torch.from_numpy(rng.randn(1, 192).astype(np.float32))

    def key():
        with torch.no_grad():
            com(xc); dis(xd)
    res["key_per_sample"] = {**timeit(key), "budget_us": 1e6 / KE.FS}
    # ---- Alhamd: per decision (5 samples at 3 kHz = 1,667 us): features of the new samples + BiLSTM on 60 x 48, largest config (hidden 128, 2 layers)
    bl = AL.BiLSTM(128, 2, 0.1).eval()
    seg = torch.from_numpy(rng.randn(1, 60, 48).astype(np.float32))
    newx = rng.randn(16, 3).astype(float)

    def alh():
        for p in range(3):
            AL.rtbswt_both(newx[:, p])
        with torch.no_grad():
            bl(seg)
    res["alhamd_per_decision"] = {**timeit(alh, 500), "budget_us": AL.STEP / AL.FS * 1e6}
    # ---- Ngaopitakkul: per sample at 20 kHz (decimated coefficient every second sample): db4 FIR on four channels; per detection: network
    buf = rng.randn(4, 8)
    h = NG.pywt.Wavelet("db4").dec_hi

    def ng_sample():
        c = (buf * np.array(h)).sum(1) ** 2
        return c.max() >= 5.0 * 1e-6
    res["ngaopitakkul_per_sample"] = {**timeit(ng_sample, 20000), "budget_us": 1e6 / NG.FS}
    p = rng.randn(4 * 12 + 12 + 12 * 11 + 11 + 11 * 8 + 8) * 0.3
    xin = rng.rand(1, 4)
    res["ngaopitakkul_per_detection_network"] = timeit(lambda: NG.forward(p, xin, 12, 11), 5000)
    # ---- Abdusalam: per decision window (every 25 samples at 10 kHz = 2,500 us), features on a real window
    d = (np.sin(2 * np.pi * 50 * np.arange(200) / 10000)[:, None] * np.array([1.0, 0.5, 0.2])[None]).astype(np.float32) + 0.01 * rng.randn(200, 3).astype(np.float32)
    res["abdusalam_features_per_decision"] = {**timeit(lambda: AB.window_features(d), 30, 3), "budget_us": AB.STEP / AB.FS * 1e6}
    # ---- Simoes: per sample (12.8 kHz = 78.1 us): RT-BSWT coefficients and energies of the 8 signals, here the vectorised numpy form of one sample; per detection: SVM 1 (32 features)
    Hm = np.array(SI.H)
    ring = rng.randn(8, 8)

    def si_sample():
        w_ = np.stack([ring[:, :SI.L] @ Hm for _ in range(SI.L)], 1)
        return (w_ ** 2).sum(1)
    res["simoes_per_sample_wavelet"] = {**timeit(si_sample, 20000), "budget_us": 1e6 / SI.FS}
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.svm import SVC
    X = rng.rand(1500, 32); y = rng.choice(["EF", "IF", "EN"], 1500)
    svm = OneVsRestClassifier(SVC(kernel="rbf", C=500.0, gamma=100.0)).fit(X, y)
    x1 = rng.rand(1, 32)
    res["simoes_svm1_per_detection"] = {**timeit(lambda: svm.predict(x1), 500), "n_support_total": int(sum(e.support_vectors_.shape[0] for e in svm.estimators_)),
                                        "note": "random 1,500-event training set (worst case for the support-vector count)"}
    L = ["Measured latency of the reproductions (single thread, CPU, Python/PyTorch/NumPy, one decision per call; architectures at the largest search-space size, random weights)"]
    for k, v in res.items():
        L.append(f"{k:44s} median {v['median_us']:10.1f} us  p99 {v.get('p99_us', float('nan')):10.1f}  budget {v.get('budget_us', float('nan')):9.1f} us  " + ("PASS" if v.get("budget_us") and v["median_us"] <= v["budget_us"] else ("-" if not v.get("budget_us") else "NOT real-time in this implementation")))
    (OUT / "latency_baselines.json").write_text(json.dumps(res, indent=1)); (OUT / "latency_baselines.txt").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
