"""Table E (paper-v1): operate time per method and fault class, median / 90th percentile, from operate_ms in the saved per-trace rows.

Operate time = trip time minus the applied fault time (verified on the waveform by the generator check), correctly tripped detectable fault
traces only, pooled over 3 seeds x 5 folds on the common set. No new run: every value comes from tools/paper_data.py (saved rows).
Output: paper_epsr/generated/paper/table_E_operate.tex (manuscript: native reproductions, conventional relays, instances, ablation),
paper_epsr/generated/table_E_operate_full.tex (supplement: also the like-for-like rows) and paper_epsr/generated/operate_times.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_data as P  # noqa: E402

OUT = P.ROOT / "paper_epsr" / "generated"
CLASSES = [("All faults", None), ("Solid LV / HV", {"Internal LV solid", "Internal HV-side"}), ("CT saturation", {"Internal CT-sat"}),
           ("In inrush", {"Fault in inrush"}), ("SOTF", {"SOTF"}), ("High impedance", {"Internal HiZ"})]


def stats(x: np.ndarray) -> dict:
    return {"n": int(len(x)), "median_ms": float(np.median(x)) if len(x) else None, "p90_ms": float(np.percentile(x, 90)) if len(x) else None}


def cell(s: dict) -> str:
    return "--" if not s["n"] else f"{s['median_ms']:.1f} / {s['p90_ms']:.1f}"


def main() -> None:
    M = {}
    for name, v in P.all_methods().items():
        if name == "Harmonic 87T, textbook":      # no operate times saved for the n6c re-runs: use the single pass
            M["Harmonic 87T, textbook (single pass)"] = ("Conventional relay", P.harmonic_textbook_single_pass())
        elif name != "Harmonic 87T, tuned":
            M[name] = v
    res = {name: {"group": g, **{c: stats(P.operate_times(rows, cats)) for c, cats in CLASSES}} for name, (g, rows) in M.items()}
    (OUT / "operate_times.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    present_classes = sorted({r["category"] for _, rows in M.values() for r in rows if r["should_trip"]})
    other = [c for c in present_classes if not any(cats and c in cats for _, cats in CLASSES)]

    def table(groups: tuple[str, ...], label: str, caption_extra: str) -> list[str]:
        L = [r"\begin{table*}[t]\centering",
             r"\caption{Operate time (ms) per method and fault class: median / 90th percentile over correctly tripped fault traces, plant-A CV pooled over "
             + f"{len(P.SEEDS)} seeds $\\times$ 5 folds, common set{caption_extra}." + r"}\label{" + label + "}",
             r"\scriptsize\setlength{\tabcolsep}{4pt}",
             r"\begin{tabular}{@{}ll" + "c" * len(CLASSES) + r"r@{}}\toprule",
             "Group & Method & " + " & ".join(c for c, _ in CLASSES) + r" & $n$ (all) \\ \midrule"]
        last = None
        for name, r in res.items():
            if r["group"] not in groups:
                continue
            if last is not None and r["group"] != last:
                L.append(r"\addlinespace")
            L.append(f"{r['group'] if r['group'] != last else ''} & {name.replace(' (native)', '').replace(' (like-for-like)', ', like-for-like').replace('õ', '{\\~o}')} & " + " & ".join(cell(r[c]) for c, _ in CLASSES) + f" & {r['All faults']['n']:,}".replace(",", "{,}") + r" \\")
            last = r["group"]
        L += [r"\bottomrule\end{tabular}",
              r"\vspace{3pt}\par\raggedright\scriptsize\textit{Notes.} Operate time = trip time minus the applied fault time (verified on the waveform by the generator check); "
              r"counts are (seed, fold, trace) decisions, so each trace appears up to three times; descriptive, no test. Reproductions run at their own sampling rates and decide once per detector firing (Sim\~oes, Ngaopitakkul) or per window; "
              r"the harmonic 87T row is a single pass over all traces with textbook settings (no operate times were saved for the tuned settings). "
              + ("Evolving faults are counted only in `All faults'. " if "Evolving" in other else "")
              + r"`--' = no correctly tripped trace in the class.",
              r"\end{table*}"]
        return L

    (OUT / "paper").mkdir(parents=True, exist_ok=True)
    main_groups = ("Reproduction (native)", "Conventional relay", "Dual-path instance", "Ablation")
    (OUT / "paper" / "table_E_operate.tex").write_text("\n".join(table(main_groups, "tab:pE_operate", "")), encoding="utf-8")
    (OUT / "table_E_operate_full.tex").write_text("\n".join(table(P.GROUPS, "tab:E_operate_full", ", including the like-for-like rows")), encoding="utf-8")
    print("operate-time table written;", len(res), "methods")


if __name__ == "__main__":
    main()
