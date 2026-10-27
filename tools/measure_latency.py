"""Measured Latency Benchmark for Transformer Differential Protection Relay.

Phase 4.1 of IMPLEMENTATION_PLAN_V4_PUBLICATION.md:
- Python / ONNX Runtime, single thread (intra_op_num_threads=1), one window per call (the streaming relay case).
- Feature extraction (DWT + FFT) and inference timed SEPARATELY and COMBINED.
- 100 warm-up calls, then 10,000 timed calls using high-resolution time.perf_counter_ns().
- Reports: median, p90, p95, p99, max, and mean latency in microseconds.
- Compares against real-time sampling deadline (625 us at 1,600 Hz).
- Records CPU model, clock, OS, Python, and ONNX Runtime versions.
- Saves results to runs/<date>_latency/latency.json and latency.txt.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pywt
import torch

ROOT = Path(__file__).resolve().parent.parent


def get_cpu_info() -> str:
    """Detect CPU model across platforms."""
    try:
        import subprocess
        if platform.system() == "Windows":
            out = subprocess.check_output("powershell -NoProfile -Command \"(Get-CimInstance Win32_Processor).Name\"", shell=True).decode()
            line = out.strip()
            if line:
                return line
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"


def benchmark_latency(onnx_path: Path, output_dir: Path, n_warmup: int = 100, n_calls: int = 10000):
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("REAL-TIME LATENCY MEASUREMENT BENCHMARK (Phase 4.1)")
    print("=" * 80)
    print(f"ONNX Model: {onnx_path}")
    print(f"Iterations: {n_warmup} warm-up, {n_calls} timed runs")

    # 1. Setup single-threaded ONNX Runtime session
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    opts.inter_op_num_threads = 1
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(str(onnx_path), sess_options=opts, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    print(f"Session Provider: CPUExecutionProvider (single-threaded)")
    print(f"Input Name: '{input_name}', Shape: {input_shape}")

    # Generate realistic inputs
    win_samples = np.random.randn(3, 32).astype(np.float64)  # 3-phase, 32 samples
    feat_seq = np.random.randn(1, 32, 12).astype(np.float32) # [1, 32, 12] sequence

    # 2. Benchmark Feature Extraction (DWT + FFT) Separately
    print("\nWarming up Feature Extraction (DWT + FFT)...", flush=True)
    for _ in range(n_warmup):
        a2, d2, d1 = pywt.wavedec(win_samples, "db4", mode="symmetric", level=2, axis=-1)
        f1 = np.log1p((d1 ** 2).sum(-1))
        f2 = np.log1p((d2 ** 2).sum(-1))
        f3 = np.log1p((a2 ** 2).sum(-1))
        spec = np.abs(np.fft.fft(win_samples, axis=-1))
        f4 = np.minimum(spec[..., 2] / (spec[..., 1] + 1e-4), 2.0)
        _ = np.concatenate([f1, f2, f3, f4])

    print(f"Timing {n_calls} Feature Extraction calls...", flush=True)
    dwt_times_ns = np.zeros(n_calls, dtype=np.int64)
    for i in range(n_calls):
        t0 = time.perf_counter_ns()
        a2, d2, d1 = pywt.wavedec(win_samples, "db4", mode="symmetric", level=2, axis=-1)
        f1 = np.log1p((d1 ** 2).sum(-1))
        f2 = np.log1p((d2 ** 2).sum(-1))
        f3 = np.log1p((a2 ** 2).sum(-1))
        spec = np.abs(np.fft.fft(win_samples, axis=-1))
        f4 = np.minimum(spec[..., 2] / (spec[..., 1] + 1e-4), 2.0)
        _ = np.concatenate([f1, f2, f3, f4])
        t1 = time.perf_counter_ns()
        dwt_times_ns[i] = t1 - t0

    # 3. Benchmark ONNX Runtime Model Inference Separately
    print("Warming up ONNX Runtime Inference...", flush=True)
    for _ in range(n_warmup):
        _ = session.run(None, {input_name: feat_seq})

    print(f"Timing {n_calls} ONNX Inference calls...", flush=True)
    onnx_times_ns = np.zeros(n_calls, dtype=np.int64)
    for i in range(n_calls):
        t0 = time.perf_counter_ns()
        _ = session.run(None, {input_name: feat_seq})
        t1 = time.perf_counter_ns()
        onnx_times_ns[i] = t1 - t0

    # 4. Benchmark Combined End-to-End Relay Step
    print("Warming up End-to-End Pipeline (Features + Inference + Threshold)...", flush=True)
    dwell_cnt = 0
    thr = 0.5
    for _ in range(n_warmup):
        a2, d2, d1 = pywt.wavedec(win_samples, "db4", mode="symmetric", level=2, axis=-1)
        f1 = np.log1p((d1 ** 2).sum(-1))
        f2 = np.log1p((d2 ** 2).sum(-1))
        f3 = np.log1p((a2 ** 2).sum(-1))
        spec = np.abs(np.fft.fft(win_samples, axis=-1))
        f4 = np.minimum(spec[..., 2] / (spec[..., 1] + 1e-4), 2.0)
        feats = np.concatenate([f1, f2, f3, f4]).astype(np.float32)
        feat_seq[0, :-1, :] = feat_seq[0, 1:, :]
        feat_seq[0, -1, :] = feats
        prob = session.run(None, {input_name: feat_seq})[0][0]
        if prob > thr:
            dwell_cnt += 1
        else:
            dwell_cnt = 0
        trip = dwell_cnt >= 20

    print(f"Timing {n_calls} End-to-End Pipeline calls...", flush=True)
    combined_times_ns = np.zeros(n_calls, dtype=np.int64)
    for i in range(n_calls):
        t0 = time.perf_counter_ns()
        a2, d2, d1 = pywt.wavedec(win_samples, "db4", mode="symmetric", level=2, axis=-1)
        f1 = np.log1p((d1 ** 2).sum(-1))
        f2 = np.log1p((d2 ** 2).sum(-1))
        f3 = np.log1p((a2 ** 2).sum(-1))
        spec = np.abs(np.fft.fft(win_samples, axis=-1))
        f4 = np.minimum(spec[..., 2] / (spec[..., 1] + 1e-4), 2.0)
        feats = np.concatenate([f1, f2, f3, f4]).astype(np.float32)
        feat_seq[0, :-1, :] = feat_seq[0, 1:, :]
        feat_seq[0, -1, :] = feats
        prob = session.run(None, {input_name: feat_seq})[0][0]
        if prob > thr:
            dwell_cnt += 1
        else:
            dwell_cnt = 0
        trip = dwell_cnt >= 20
        t1 = time.perf_counter_ns()
        combined_times_ns[i] = t1 - t0

    # 5. Compute Statistics in Microseconds
    def stats(arr_ns: np.ndarray) -> dict:
        arr_us = arr_ns / 1000.0
        return {
            "mean_us": float(np.mean(arr_us)),
            "std_us": float(np.std(arr_us)),
            "median_us": float(np.median(arr_us)),
            "p90_us": float(np.percentile(arr_us, 90)),
            "p95_us": float(np.percentile(arr_us, 95)),
            "p99_us": float(np.percentile(arr_us, 99)),
            "max_us": float(np.max(arr_us)),
            "min_us": float(np.min(arr_us)),
        }

    st_dwt = stats(dwt_times_ns)
    st_onnx = stats(onnx_times_ns)
    st_comb = stats(combined_times_ns)

    sample_period_us = 1e6 / 1600.0  # 625 us
    cpu_budget_utilization_pct = (st_comb["median_us"] / sample_period_us) * 100.0

    metadata = {
        "timestamp": datetime.datetime.now().isoformat(),
        "cpu_model": get_cpu_info(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
        "onnxruntime_version": ort.__version__,
        "sample_rate_hz": 1600,
        "sample_period_us": sample_period_us,
        "n_warmup": n_warmup,
        "n_timed_calls": n_calls,
    }

    results = {
        "metadata": metadata,
        "feature_extraction_dwt_fft": st_dwt,
        "onnx_inference": st_onnx,
        "combined_relay_pipeline": st_comb,
        "budget_analysis": {
            "sampling_interval_us": sample_period_us,
            "pipeline_median_us": st_comb["median_us"],
            "pipeline_p99_us": st_comb["p99_us"],
            "cpu_time_utilization_pct": cpu_budget_utilization_pct,
            "real_time_margin_pct": 100.0 - cpu_budget_utilization_pct,
            "verdict_real_time_capable": st_comb["p99_us"] < sample_period_us,
        },
    }

    # Format text report
    L = [
        "=" * 80,
        "MEASURED LATENCY BENCHMARK REPORT (TRANSFORMER RELAY v4)",
        "=" * 80,
        f"Timestamp:          {metadata['timestamp']}",
        f"Host CPU:           {metadata['cpu_model']}",
        f"Operating System:   {metadata['os']}",
        f"Software Stack:     Python {metadata['python_version']}, PyTorch {metadata['torch_version']}, ONNX Runtime {metadata['onnxruntime_version']}",
        f"Execution Model:    Single thread (intra_op_num_threads=1, ORT_SEQUENTIAL), streaming 1 window/call",
        f"Timed Iterations:   {n_calls} calls (following {n_warmup} warm-up calls)",
        "",
        "LATENCY BREAKDOWN (Microseconds, us):",
        f"{'Subsystem':32s} {'Median':>9s} {'Mean':>9s} {'p90':>9s} {'p99':>9s} {'Max':>9s}",
        "-" * 80,
        f"{'1. Feature Extraction (DWT+FFT)':32s} {st_dwt['median_us']:9.1f} {st_dwt['mean_us']:9.1f} {st_dwt['p90_us']:9.1f} {st_dwt['p99_us']:9.1f} {st_dwt['max_us']:9.1f}",
        f"{'2. LSTM ONNX Inference':32s} {st_onnx['median_us']:9.1f} {st_onnx['mean_us']:9.1f} {st_onnx['p90_us']:9.1f} {st_onnx['p99_us']:9.1f} {st_onnx['max_us']:9.1f}",
        f"{'3. Total Combined Pipeline':32s} {st_comb['median_us']:9.1f} {st_comb['mean_us']:9.1f} {st_comb['p90_us']:9.1f} {st_comb['p99_us']:9.1f} {st_comb['max_us']:9.1f}",
        "-" * 80,
        "",
        "REAL-TIME FEASIBILITY ASSESSMENT:",
        f"   Relay Sampling Frequency:       1,600 Hz (32 samples/cycle at 50 Hz)",
        f"   Available Time Budget per Step: {sample_period_us:.1f} us",
        f"   Measured Pipeline Latency (p50):{st_comb['median_us']:.1f} us ({cpu_budget_utilization_pct:.1f}% CPU core load)",
        f"   Measured Pipeline Latency (p99):{st_comb['p99_us']:.1f} us",
        f"   Processing Safety Margin:       {100.0 - cpu_budget_utilization_pct:.1f}% idle headroom per sample interval",
        f"   Real-time Feasibility Verdict:  {'PASS (Well within 625 us real-time budget)' if results['budget_analysis']['verdict_real_time_capable'] else 'FAIL'}",
        "=" * 80,
    ]

    (output_dir / "latency.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (output_dir / "latency.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)
    print(f"\nSaved latency benchmarks to:\n  {output_dir / 'latency.json'}\n  {output_dir / 'latency.txt'}")


def main():
    parser = argparse.ArgumentParser(description="Measure Latency for Transformer Relay")
    parser.add_argument("--onnx", default="lstm_models/wt_lstm_relay.onnx", help="Path to ONNX model")
    parser.add_argument("--output-dir", default="runs/latency_benchmark", help="Output directory")
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--calls", type=int, default=10000)
    args = parser.parse_args()

    onnx_file = Path(args.onnx) if Path(args.onnx).is_absolute() else ROOT / args.onnx
    out_dir = Path(args.output_dir) if Path(args.output_dir).is_absolute() else ROOT / args.output_dir
    benchmark_latency(onnx_file, out_dir, args.warmup, args.calls)


if __name__ == "__main__":
    main()
