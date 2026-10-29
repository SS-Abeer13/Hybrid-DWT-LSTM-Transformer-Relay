"""E1 (IMPLEMENTATION_PLAN_V4_PUBLICATION.md, protocol fixed 2026-10-30 before the run): hybrid relay whose 87T gate is the per-phase
harmonic-restrained 87T instead of the unrestrained one. No retraining: saved fold models and the saved final model; thresholds tuned on the
models' own validation traces by the existing plateau rules, with the harmonic gate in place. One variant, one attempt.

    python tools/e1_harmonic_gate_v5.py
Outputs: runs/20261029_v5_e1_harmonic_gate/{e1_summary.json, e1_summary.txt}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.stats import chi2
from sklearn.model_selection import StratifiedKFold, train_test_split

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lstm_models"))
sys.path.insert(0, str(ROOT / "tools"))
import relay87t  # noqa: E402
import stress_dataset  # noqa: E402
import train_cv_v5 as C  # noqa: E402
import train_trace_split as T  # noqa: E402
import run_plant_b_generalization_v5 as G  # noqa: E402

TAG = "20261029_v5"
CV = ROOT / "runs" / f"{TAG}_cv5_seeds"
FINAL = ROOT / "runs" / f"{TAG}_final"
OUT = ROOT / "runs" / f"{TAG}_e1_harmonic_gate"
SEEDS = [20261021, 20261022, 20261023]
FILES_A = ["datasets/StressDataset_v5_20261028_162333.mat", "datasets/StressDataset_v5Only_20261028_232627.mat",
           "datasets/StressDataset_v5Only_20261028_233305.mat", "datasets/StressDataset_v5Only_20261028_234041.mat",
           "datasets/StressDataset_v5Only_20261029_111722.mat"]
FILES_OOD = ["datasets/StressDataset_v5OOD_20261028_205712.mat"]
FILES_B = ["datasets/StressDataset_PlantBv5_20261028_212041.mat", "datasets/StressDataset_PlantBv5Only_20261029_111005.mat",
           "datasets/StressDataset_PlantBv5Only_20261029_111251.mat"]
VAR = "Hybrid + AI-alone path"      # the relay logic of this variant; the gate signals are swapped to the harmonic ones


def load_model(path: Path) -> torch.nn.Module:
    ck = torch.load(path, map_location="cpu", weights_only=False)
    c = ck["config"]
    m = T.TransformerProtectionLSTM(int(c["input_size"]), int(c["hidden_size"]), int(c["num_layers"]), float(c["dropout"]), bool(c["bidirectional"]))
    m.load_state_dict(ck["model_state_dict"])
    return m.eval()


def harmonic_signals(files: list[str], plant: str = "A") -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """fingerprint -> (per-phase harmonic 87T vote, high-set), from the raw currents."""
    out = {}
    for f in files:
        for t in stress_dataset.load_traces(ROOT / f):
            if t["fingerprint"] in out:
                continue
            h = relay87t.analyse_harmonic(t["primary"], t["secondary"], plant=plant, mode="per_phase")
            out[t["fingerprint"]] = (h["vote"], h["highset"])
    return out


def swap_gate(traces: list[dict], sig: dict) -> None:
    for t in traces:
        t["vote87_unres"], t["highset_unres"] = t["vote87"], t["highset"]
        t["vote87"], t["highset"] = sig[t["fingerprint"]]


def restore_gate(traces: list[dict]) -> None:
    for t in traces:
        t["vote87"], t["highset"] = t["vote87_unres"], t["highset_unres"]


def mcnemar(a_ok: np.ndarray, b_ok: np.ndarray) -> dict:
    n10 = int(np.sum(a_ok & ~b_ok)); n01 = int(np.sum(~a_ok & b_ok))
    stat = (abs(n10 - n01) - 1) ** 2 / (n10 + n01) if (n10 + n01) else 0.0
    return {"a_wins": n10, "b_wins": n01, "chi2": float(stat), "p_value": float(chi2.sf(stat, 1)) if (n10 + n01) else 1.0}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    args = type("A", (), {"files": FILES_A, "dwell": 20, "dep_tolerance": 2.0, "sec_tolerance": 1.0, "limit": 0})()
    traces = C.load_traces(args, CV / "traces_cache.npz")
    fin_fp = [t['fingerprint'] for t in np.load(FINAL / 'traces_cache_main.npz', allow_pickle=True)['traces']]
    assert [t['fingerprint'] for t in traces] == fin_fp, 'CV cache and final cache differ in order'
    sig = harmonic_signals(FILES_A)
    swap_gate(traces, sig)
    device = torch.device("cpu")

    # ------------------------------------------------------------------ (1) CV, 15 fold-models (splits rebuilt exactly as train_cv_v5.py)
    names = np.array([t["scenarioName"] for t in traces]); idx = np.arange(len(traces))
    strat = names.copy()
    for c_, n_ in zip(*np.unique(names, return_counts=True)):
        if n_ < 5:
            strat[names == c_] = "_small"
    rows_e1, rows_ref, settings = [], [], []
    for seed in SEEDS:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for k, (tr_all, te) in enumerate(skf.split(idx, strat), 1):
            trainable = [i for i in tr_all if not traces[i]["undetectable"]]
            st = strat[trainable].copy()
            for c_, n_ in zip(*np.unique(st, return_counts=True)):
                if n_ < 4:
                    st[st == c_] = "_small"
            if (st == "_small").sum() == 1:
                st[st == "_small"] = st[0]
            _, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=seed + k)
            va_ids, te_ids = sorted(va.tolist()), sorted(te.tolist())
            model = load_model(CV / f"seed_{seed}" / f"fold{k}" / "transformer_protection_lstm_best.pth")
            probs = {i: T.stream_probs(model, traces[i]["features"], device) for i in sorted(set(va_ids) | set(te_ids))}
            thr, solo = C.tune_variant(traces, va_ids, probs, VAR)
            rows = C.rows_for(traces, te_ids, probs, VAR, thr, solo)
            for r in rows:
                r["seed"], r["fold"] = seed, k
            C.annotate(rows, traces)
            rows_e1 += rows
            settings.append({"seed": seed, "fold": k, "ai_threshold": thr, "solo_threshold": solo})
            ref = json.loads((CV / f"seed_{seed}" / f"fold{k}" / "result.json").read_text(encoding="utf-8"))["rows"][VAR]
            rows_ref += ref
            print(f"seed {seed} fold {k}: thr {thr:.4f} solo {solo}", flush=True)
    s_e1, s_ref = C.summarise(rows_e1), C.summarise(rows_ref)

    # paired comparison, matched on (seed, fold, trace)
    key = lambda r: (r["seed"], r["fold"], r["trace"])  # noqa: E731
    ref_by = {key(r): r for r in rows_ref}
    pair = [(r, ref_by[key(r)]) for r in rows_e1 if key(r) in ref_by and not r.get("undetectable")]
    assert len(pair) == len([r for r in rows_e1 if not r.get("undetectable")]), "pairing incomplete"
    cmp = {}
    for nm, want in (("dependability", True), ("security", False)):
        sel = [(a, b) for a, b in pair if bool(a["should_trip"]) == want]
        cmp[nm] = {"n": len(sel), "e1_correct_pct": 100 * float(np.mean([a["correct"] for a, _ in sel])), "ref_correct_pct": 100 * float(np.mean([b["correct"] for _, b in sel])),
                   **mcnemar(np.array([a["correct"] for a, _ in sel]), np.array([b["correct"] for _, b in sel]))}
    hh = json.loads((ROOT / "runs" / f"{TAG}_harmonic87t" / "summary.json").read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ (2) final model: thresholds on its validation traces; OOD scored once
    trainable = [i for i in range(len(traces)) if not traces[i]["undetectable"]]
    nm_ = np.array([traces[i]["scenarioName"] for i in trainable]); st = nm_.copy()
    for c_, n_ in zip(*np.unique(st, return_counts=True)):
        if n_ < 4:
            st[st == c_] = "_small"
    _, va = train_test_split(np.array(trainable), test_size=0.15, stratify=st, random_state=20261021)
    va_ids = sorted(va.tolist())
    fmodel = load_model(FINAL / "transformer_protection_lstm_best.pth")
    probs = {i: T.stream_probs(fmodel, traces[i]["features"], device) for i in va_ids}
    thr_f, solo_f = C.tune_variant(traces, va_ids, probs, VAR)
    restore_gate(traces)

    args_o = type("A", (), {"files": FILES_OOD, "dwell": 20, "dep_tolerance": 2.0, "sec_tolerance": 1.0, "limit": 0})()
    ood = C.load_traces(args_o, FINAL / "traces_cache_ood.npz")
    swap_gate(ood, harmonic_signals(FILES_OOD))
    oprobs = {i: T.stream_probs(fmodel, ood[i]["features"], device) for i in range(len(ood))}
    orows = C.rows_for(ood, list(range(len(ood))), oprobs, VAR, thr_f, solo_f)
    C.annotate(orows, ood)
    for r, t in zip(orows, [ood[r["trace"]] for r in orows]):
        r["ood_block"] = int(t.get("oodBlock", 0))
    s_ood = C.summarise(orows)
    ood_ref = json.loads((FINAL / "report_ood.json").read_text(encoding="utf-8"))["ood"][VAR]["overall"]
    blocks = {b: C.summarise([r for r in orows if r["ood_block"] == b]) for b in range(1, 6)}

    # ------------------------------------------------------------------ (3) plant B zero-shot, plant-A final model, thresholds frozen from (2)
    tb = G.load_dataset_traces([ROOT / f for f in FILES_B])
    for t in tb:
        t["vote87"], t["highset"] = t["vote87_harm"], t["highset_harm"]
    G.PLANT_A_DWELL = 20
    pb = G.compute_model_probs(fmodel, tb, device)
    zb = G.evaluate_relay_on_traces(tb, pb, thr_f, solo_f, variant="Proposed")
    zb.pop("rows", None)
    zs_ref = json.loads((ROOT / "runs" / f"{TAG}_plant_b_zeroshot" / "zero_shot_summary.json").read_text(encoding="utf-8"))

    res = {
        "protocol": "IMPLEMENTATION_PLAN_V4_PUBLICATION.md, E1 protocol (fixed 2026-10-30)",
        "cv": {"e1": s_e1, "reference_hybrid_ai_alone": s_ref, "paired_vs_reference": cmp, "thresholds_per_fold": settings},
        "final": {"ai_threshold": thr_f, "solo_threshold": solo_f},
        "ood": {"e1": s_ood, "reference": ood_ref, "blocks_e1": blocks},
        "plant_b_zero_shot": {"e1": zb, "reference_proposed": {k: zs_ref["Proposed"][k] for k in ("dependability_pct", "security_pct", "missed_trips", "false_trips")},
                              "reference_harmonic_87t": {k: zs_ref["Harmonic 87T"][k] for k in ("dependability_pct", "security_pct", "missed_trips", "false_trips")}},
    }
    (OUT / "e1_summary.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")

    def line(name, s):
        o = s["operate"]
        return f"{name:44s} dep {s['dependability_pct']:6.2f} %  sec {s['security_pct']:6.2f} %  missed {s['missed']:4d}  false {s['false_trips']:4d}  pre {s['pre_fault_trips']:3d}  median {o['median_ms']:.1f} ms"
    L = ["E1: hybrid with the per-phase harmonic-restrained 87T as gate (protocol fixed before the run; no retraining)", "",
         "(1) CV, 15 fold-models pooled (undetectable faults excluded):",
         "  " + line("Hybrid + AI-alone path (unrestrained gate)", s_ref),
         "  " + line("Hybrid, harmonic gate (E1)", s_e1),
         f"  per-phase harmonic 87T alone (summary of {TAG}_harmonic87t, main CV pooled): see that summary.",
         "  paired McNemar, E1 vs reference hybrid, matched on (seed, fold, trace):"]
    for nm, c_ in cmp.items():
        L.append(f"    {nm:14s} n={c_['n']}  E1 {c_['e1_correct_pct']:.2f} %  ref {c_['ref_correct_pct']:.2f} %  E1 wins {c_['a_wins']}  ref wins {c_['b_wins']}  chi2 {c_['chi2']:.2f}  p {c_['p_value']:.3g}")
    L += ["", f"(2) Final model, thresholds tuned on its validation traces with the harmonic gate: AI {thr_f:.4f}, solo {solo_f}", "  OOD (scored once):",
          "    reference hybrid: dep %.1f %% sec %.1f %%" % (ood_ref["dependability_pct"], ood_ref["security_pct"]),
          "    " + line("E1", s_ood)]
    for b, sb in blocks.items():
        L.append(f"      block {b}: dep {sb['dependability_pct']:.1f} % ({sb['n_fault']})  sec {sb['security_pct']:.1f} % ({sb['n_healthy']})")
    L += ["", "(3) Plant B zero-shot (plant-A final model; the thresholds of (2) frozen):",
          f"    reference Proposed       : dep {zs_ref['Proposed']['dependability_pct']:.2f} %  sec {zs_ref['Proposed']['security_pct']:.2f} %  false trips {zs_ref['Proposed']['false_trips']}",
          f"    reference harmonic 87T   : dep {zs_ref['Harmonic 87T']['dependability_pct']:.2f} %  sec {zs_ref['Harmonic 87T']['security_pct']:.2f} %  false trips {zs_ref['Harmonic 87T']['false_trips']}",
          f"    E1 hybrid, harmonic gate : dep {zb['dependability_pct']:.2f} %  sec {zb['security_pct']:.2f} %  false trips {zb['false_trips']}  missed {zb['missed_trips']}"]
    (OUT / "e1_summary.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
