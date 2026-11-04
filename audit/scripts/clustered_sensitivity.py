"""Audit sensitivity analysis (existing data only, no new experiment).

The reported McNemar tests pool the 3 CV repetitions: every trace appears once per seed, so the 3,717 fault / 5,910 healthy
'pairs' are ~1,239 / ~1,970 traces counted three times. The pairs are not independent, which can make p-values too small.
This script re-tests every reported comparison two ways that respect the clustering:
  (a) trace-clustered sign-flip permutation test: per trace, d_i = mean over seeds of (other correct - reference correct);
      statistic = sum(d_i); 200,000 random sign flips (two-sided, add-one correction); when no permutation reaches the observed
      value, a normal approximation of the same statistic is also given;
  (b) seed-1-only exact McNemar (each trace exactly once; seed 20261021 only).
Holm is then re-applied inside the SAME families as reported (24, 48, 50, 4, 16, 22; D-X1 adds the extended-grid 4 and 16). The output lists every test whose
'significant after Holm' verdict changes.
Output: audit/scripts/out/clustered_sensitivity.txt / .json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recompute_stats as R  # noqa: E402

RNG = np.random.default_rng(20261103)
NPERM = 200_000


def clustered(ref, oth, ks):
    by = defaultdict(list)
    for k in ks:
        by[k[2]].append(int(bool(oth[k]["correct"])) - int(bool(ref[k]["correct"])))
    d = np.array([np.mean(v) for v in by.values()])
    d = d[d != 0]
    if len(d) == 0:
        return 1.0, 1.0, 0
    obs = abs(d.sum())
    cnt = 0
    for _ in range(NPERM // 10000):
        s = RNG.choice([-1.0, 1.0], size=(10000, len(d)))
        cnt += int((np.abs(s @ d) >= obs - 1e-12).sum())
    p_perm = (cnt + 1) / (NPERM + 1)
    z = obs / np.sqrt((d ** 2).sum())
    return float(p_perm), float(2 * norm.sf(z)), len(d)


def seed1(ref, oth, ks):
    ks = [k for k in ks if k[0] == R.SEEDS[0]]
    a = np.array([bool(ref[k]["correct"]) for k in ks]); b = np.array([bool(oth[k]["correct"]) for k in ks])
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    return float(binomtest(n10, n10 + n01, 0.5).pvalue) if n10 + n01 else 1.0, n10, n01, len(ks)


def run_family(name, comparisons, extra_prior=None):
    """comparisons: list of (label, ref_rows, other_rows, flag, reported_p_holm)."""
    out = []
    for lab, ref, oth, flag, rep in comparisons:
        ks = R.paired(ref, oth, flag)
        t = R.mcn(ref, oth, ks)
        pp, pz, ntr = clustered(ref, oth, ks)
        p1, a, b, n1 = seed1(ref, oth, ks)
        out.append(dict(label=lab, diff=t["diff"], p_pooled=t["p"], p_clust=max(pp, pz) if pp <= 1.0 / NPERM * 2 else pp, p_perm=pp, p_normal=pz,
                        n_discordant_traces=ntr, p_seed1=p1, seed1_disc=(a, b), n_seed1=n1, reported_p_holm=rep))
    prior_c = [x["p_clust"] for x in (extra_prior or [])]
    prior_1 = [x["p_seed1"] for x in (extra_prior or [])]
    prior_p = [x["p_pooled"] for x in (extra_prior or [])]
    hp = R.holm(prior_p + [x["p_pooled"] for x in out])[len(prior_p):]
    hc = R.holm(prior_c + [x["p_clust"] for x in out])[len(prior_c):]
    h1 = R.holm(prior_1 + [x["p_seed1"] for x in out])[len(prior_1):]
    for x, a, b, c in zip(out, hp, hc, h1):
        x["holm_pooled"], x["holm_clust"], x["holm_seed1"] = float(a), float(b), float(c)
    return out


def fmt(fam, rows):
    L = [f"\n== {fam} (Holm family size {len(rows)}{'' if fam != 'Key hybrid (Holm 50)' else ' new + 48 prior'})",
         f"{'comparison':66s} {'diff':>7s} {'pH pooled':>10s} {'pH clust':>10s} {'pH seed1':>10s}  verdict change"]
    for x in rows:
        sig = [x["holm_pooled"] < .05, x["holm_clust"] < .05, x["holm_seed1"] < .05]
        ch = "" if len(set(sig)) == 1 else ("CLUSTERED FLIPS" if sig[0] != sig[1] else "") + (" SEED-1 FLIPS" if sig[0] != sig[2] else "")
        L.append(f"{x['label'][:66]:66s} {x['diff']:+7.2f} {x['holm_pooled']:10.2e} {x['holm_clust']:10.2e} {x['holm_seed1']:10.2e}  {ch}")
    return L


def main():
    refs = {"Proposed hybrid": R.load_ref("Hybrid + AI-alone path"), "LSTM alone": R.load_ref("LSTM alone")}
    fams, L = {}, ["Trace-clustered sensitivity of the reported McNemar tests (audit; existing data only). 'pH' = Holm-adjusted within the reported family.",
                   f"clustered = sign-flip permutation over traces ({NPERM} draws; floor {1/NPERM:.1e}, when no permutation reaches the observed value the floor itself is used, i.e. conservative); seed1 = exact McNemar on seed 20261021 only"]
    comps = []
    for mode in ("native", "modeb"):
        for m in R.METHODS:
            rows = R.load_full(m, mode)
            for rn, ref in refs.items():
                for metric, flag in (("dependability", 1), ("security", 0)):
                    comps.append((f"{rn} vs {m} [{mode}] {metric}", ref, rows, flag, None))
    fams["N5 native (Holm 24)"] = run_family("n5", comps[:24])
    fams["N5b native + like-for-like (Holm 48)"] = run_family("n5b", comps)
    kh = R.load_full("key_hybrid", "hybrid")
    fams["Key hybrid (Holm 50)"] = run_family("kh", [(f"Key hybrid vs proposed hybrid {m}", refs["Proposed hybrid"], kh, f, None) for m, f in (("dependability", 1), ("security", 0))],
                                              extra_prior=fams["N5b native + like-for-like (Holm 48)"])
    rows = json.loads((R.BF / "n6c_tuned_rows.json").read_text())
    tuned = {tuple(r["key"]): r for r in rows["tuned"]}; text = {tuple(r["key"]): r for r in rows["textbook"]}
    n6 = [(f"{nm} harmonic vs proposed hybrid {m}", refs["Proposed hybrid"], d, f, None) for nm, d in (("textbook", text), ("tuned", tuned)) for m, f in (("dependability", 1), ("security", 0))]
    fams["N6c (Holm 4)"] = run_family("n6c", n6)
    b2 = R.load_b2()
    inst = {n: {k: v for k, v in b2[n]["hybrid"].items() if k[2] not in R.BAD} for n in ("1D-CNN", "Wavelet-GRU", "Wavelet-ANN", "Wavelet-RF", "Proposed LSTM", "Wavelet-SVM")}
    inst["Key"] = kh
    n8 = [(f"{n} hybrid vs tuned harmonic {m}", tuned, inst[n], f, None) for n in ("1D-CNN", "Wavelet-GRU", "Wavelet-ANN", "Key", "Wavelet-RF", "Proposed LSTM") for m, f in (("dependability", 1), ("security", 0))]
    n8r = run_family("n8a", n8, extra_prior=None)
    # Holm 16 = 12 + the 4 N6c tests: recompute jointly
    allc = R.holm([x["p_clust"] for x in n8r] + [x["p_clust"] for x in fams["N6c (Holm 4)"]])
    all1 = R.holm([x["p_seed1"] for x in n8r] + [x["p_seed1"] for x in fams["N6c (Holm 4)"]])
    allp = R.holm([x["p_pooled"] for x in n8r] + [x["p_pooled"] for x in fams["N6c (Holm 4)"]])
    for x, a, b, c in zip(n8r, allp, allc, all1):
        x["holm_pooled"], x["holm_clust"], x["holm_seed1"] = float(a), float(b), float(c)
    fams["N8a (Holm 16)"] = n8r
    b2c = []
    for n in ("Wavelet-SVM", "Wavelet-RF", "Wavelet-ANN", "1D-CNN", "Wavelet-GRU"):
        for m, f in (("dependability", 1), ("security", 0)):
            b2c.append((f"{n} hybrid vs tuned LSTM hybrid {m}", inst["Proposed LSTM"], inst[n], f, None))
    for m, f in (("dependability", 1), ("security", 0)):
        b2c.append((f"tuned LSTM hybrid vs deployed hybrid {m}", refs["Proposed hybrid"], inst["Proposed LSTM"], f, None))
    for n in ("Wavelet-SVM", "Wavelet-RF", "Wavelet-ANN", "1D-CNN", "Wavelet-GRU"):
        for m, f in (("dependability", 1), ("security", 0)):
            b2c.append((f"{n} hybrid vs deployed hybrid {m}", refs["Proposed hybrid"], inst[n], f, None))
    fams["B2 (Holm 22)"] = run_family("b2", b2c)
    # D-X1 (2026-11-04): the same tests against the EXTENDED-grid tuned harmonic 87T (post-hoc; n6c_tuned_rows_ext.json).
    # Appended after every earlier family, so the shared RNG stream - and every earlier result - is unchanged.
    rows_x = json.loads((R.BF / "n6c_tuned_rows_ext.json").read_text())
    tuned_x = {tuple(r["key"]): r for r in rows_x["tuned"]}; text_x = {tuple(r["key"]): r for r in rows_x["textbook"]}
    n6x = [(f"{nm} harmonic vs proposed hybrid {m}", refs["Proposed hybrid"], d, f, None) for nm, d in (("textbook", text_x), ("tuned", tuned_x)) for m, f in (("dependability", 1), ("security", 0))]
    fams["N6c ext (Holm 4)"] = run_family("n6c_ext", n6x)
    n8x = [(f"{n} hybrid vs tuned harmonic {m}", tuned_x, inst[n], f, None) for n in ("1D-CNN", "Wavelet-GRU", "Wavelet-ANN", "Key", "Wavelet-RF", "Proposed LSTM") for m, f in (("dependability", 1), ("security", 0))]
    n8xr = run_family("n8a_ext", n8x, extra_prior=None)
    allc = R.holm([x["p_clust"] for x in n8xr] + [x["p_clust"] for x in fams["N6c ext (Holm 4)"]])
    all1 = R.holm([x["p_seed1"] for x in n8xr] + [x["p_seed1"] for x in fams["N6c ext (Holm 4)"]])
    allp = R.holm([x["p_pooled"] for x in n8xr] + [x["p_pooled"] for x in fams["N6c ext (Holm 4)"]])
    for x, a, b, c in zip(n8xr, allp, allc, all1):
        x["holm_pooled"], x["holm_clust"], x["holm_seed1"] = float(a), float(b), float(c)
    fams["N8a ext (Holm 16)"] = n8xr
    flips = []
    for fam, rows in fams.items():
        L += fmt(fam, rows)
        for x in rows:
            if (x["holm_pooled"] < .05) != (x["holm_clust"] < .05) or (x["holm_pooled"] < .05) != (x["holm_seed1"] < .05):
                flips.append(f"{fam}: {x['label']} diff {x['diff']:+.2f}: pooled pH {x['holm_pooled']:.2e}, clustered pH {x['holm_clust']:.2e}, seed-1 pH {x['holm_seed1']:.2e}")
    L += ["", "== Verdict changes (significant after Holm: pooled vs clustered or seed-1 only)"] + ["  - " + f for f in flips] + [f"  total {len(flips)}"]
    out = Path(__file__).resolve().parent / "out"
    (out / "clustered_sensitivity.txt").write_text("\n".join(L))
    (out / "clustered_sensitivity.json").write_text(json.dumps({k: [{kk: vv for kk, vv in x.items()} for x in v] for k, v in fams.items()}, indent=1, default=float))
    print("\n".join(L))


if __name__ == "__main__":
    main()
