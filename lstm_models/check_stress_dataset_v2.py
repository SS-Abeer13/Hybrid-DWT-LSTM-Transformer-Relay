"""Inspect a StressDataset_v2_*.mat file: were the scenario parameters really applied?

Prints per-scenario counts and check pass rates, duplicate waveforms, parameter ranges
(load, noise, Rf, timing), timing errors, fault detectability (faultDiffPu) and writes
an overview plot (one random trace per scenario) next to the file.

    python lstm_models/check_stress_dataset_v2.py datasets/StressDataset_v2_<run>.mat
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from stress_dataset import load_traces


def main() -> None:
    path = Path(sys.argv[1])
    T = load_traces(path)
    n = len(T)
    print(f"{path.name}: {n} traces loaded")

    fps = Counter(t["fingerprint"] for t in T)
    dup = sum(c - 1 for c in fps.values() if c > 1)
    print(f"Unique waveforms: {len(fps)} / {n}   (duplicates: {dup})")

    by = defaultdict(list)
    for t in T:
        by[t["scenarioName"]].append(t)
    print(f"\n{'scenario':24s} {'n':>4s} {'checks':>7s} {'timing':>7s} {'unseen':>6s} {'|dt| ms':>8s} {'load %':>11s} {'Rf ohm':>13s} {'diff pu':>13s}")
    for name in sorted(by):
        g = by[name]
        f = lambda k: np.array([t.get(k, np.nan) for t in g], float)  # noqa: E731
        chk, tim, vis = f("checkPassed"), f("timingOK"), f("eventVisible")
        dt = np.abs(f("eventDetected") - np.where(np.isfinite(f("inceptionTime")), f("inceptionTime"), f("energisationTime"))) * 1e3
        rng = lambda v, fmt: (f"{np.nanmin(v):{fmt}}-{np.nanmax(v):{fmt}}" if np.isfinite(v).any() else "-")  # noqa: E731
        print(f"{name:24s} {len(g):4d} {np.nanmean(chk == 1) * 100:6.0f}% {np.nanmean(tim == 1) * 100:6.0f}% "
              f"{int(np.sum(vis == 0)):6d} {np.nanmax(dt) if np.isfinite(dt).any() else float('nan'):8.1f} "
              f"{rng(100 * f('loadPu'), '.0f'):>11s} {rng(f('faultResistance'), '.2g'):>13s} {rng(f('faultDiffPu'), '.2f'):>13s}")

    allf = lambda k: np.array([t.get(k, np.nan) for t in T], float)  # noqa: E731
    print(f"\nChecks passed: {np.nanmean(allf('checkPassed') == 1) * 100:.1f}%  | timing failures: {int(np.sum(allf('timingOK') == 0))}"
          f"  | noise check failures: {int(np.sum(allf('noiseOK') == 0))}")
    print(f"Noise: {np.nanmin(allf('noisePct')):.2f}-{np.nanmax(allf('noisePct')):.2f} % rated | "
          f"measured/expected median {np.nanmedian(allf('noiseMeasured') / allf('noiseExpected')):.2f}")
    trip = allf("faultDiffPu")[np.array([t["should_trip"] for t in T]) == 1]
    print(f"Internal faults below 0.05 pu differential (physically undetectable): {int(np.sum(trip < 0.05))} / {np.isfinite(trip).sum()}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        names = sorted(by)
        fig, axes = plt.subplots(len(names), 1, figsize=(11, 1.5 * len(names)), sharex=True)
        rnd = np.random.default_rng(0)
        for ax, name in zip(np.atleast_1d(axes), names):
            t = by[name][rnd.integers(len(by[name]))]
            d = t["primary"] - t["secondary"]
            ax.plot(np.arange(len(d)) / 1600, d, lw=0.5)
            for k, c in (("inceptionTime", "r"), ("energisationTime", "g")):
                if np.isfinite(t.get(k, np.nan)) and t.get(k, 0) > 0:
                    ax.axvline(t[k], color=c, ls="--", lw=0.8)
            ax.set_title(f"{name}  load {100 * t.get('loadPu', np.nan):.0f}%  Rf {t.get('faultResistance', np.nan):.3g}  "
                         f"check {t.get('checkPassed', np.nan):.0f}", fontsize=7)
        plt.tight_layout()
        out = path.with_name(path.stem + "_overview.png")
        plt.savefig(out, dpi=70)
        print(f"Overview plot: {out}  (red = fault time, green = energisation)")
    except Exception as exc:  # plotting is optional
        print(f"(plot skipped: {exc})")


if __name__ == "__main__":
    main()
