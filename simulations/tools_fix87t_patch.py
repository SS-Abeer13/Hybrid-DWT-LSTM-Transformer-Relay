from pathlib import Path
p = Path(__file__).resolve().parent / "fix_87t_compensation.m"
s = p.read_text(encoding="utf-8")
def rep(a, b):
    global s
    assert a in s, a[:60]
    s = s.replace(a, b)
rep("""% Plant facts (read from the model, confirmed on healthy traces):
%   * Step_down_Transformer 300 MVA, 230 kV Y / 11 kV Delta (D1)  -> rated line currents 753.06 A / 15745.9 A.
%   * CT 'CT 2000/5' windings [5*(1/400) V : 5 V]       -> 400:1       -> HV rated secondary 1.8827 A.
%     CT 'CT 92000/5' windings [5*(11/92000) V : 5 V]   -> 8363.6:1    -> LV rated secondary 1.8827 A
%     (the chart assumed 18400:1 = 92000/5 and a base of 0.8557 A: wrong by 2.2x on the LV side).
""", """% Plant facts (ground truth from the V-I measurement blocks, simulations/probe_ct_truth.m, 2026-10-21):
%   * Step_down_Transformer 300 MVA, 230 kV Y / 11 kV Delta (D1)  -> rated line currents 753.06 A / 15745.9 A.
%   * The CT subsystems behave as HV 809.6:1 and LV 16925:1 (2.024 x their winding-voltage ratios 400:1 and 92000/11:1; true line
%     current / CT-secondary current measured at two loads, spread < 0.05 %). Rated CT-secondary current = 0.9302 A on BOTH sides.
%     (History: the original chart assumed HV 400:1 -> 1.883 A and LV 18400:1 -> 0.8557 A; the first correction on 2026-10-20 used
%     1.8827 A / 1.8827 A from the winding voltages, which was still 2.024 x too large.)
""")
rep("'    % 3. CT ratios exactly as modelled: HV 400:1, LV winding voltages 5*(11/92000) : 5 -> 92000/11 = 8363.6:1', ...",
    "'    % 3. EFFECTIVE CT ratios measured against the true line currents (2.024 x the winding-voltage ratios 400 and 92000/11)', ...")
rep("'    CT_Ratio_HV = 2000 / 5;', ...", "'    CT_Ratio_HV = 809.6;', ...")
rep("'    CT_Ratio_LV = 92000 / 11;', ...", "'    CT_Ratio_LV = 16925;', ...")
rep("'    % 4. Rated secondary currents = 1.0 pu bases (1.8827 A on both sides)', ...", "'    % 4. Rated secondary currents = 1.0 pu bases (0.9302 A on both sides)', ...")
rep("S = 300e6; Ihv = S/(sqrt(3)*230e3)/(2000/5); Ilv = S/(sqrt(3)*11e3)/(92000/11);\nassert(abs(Ihv - 1.8827) < 1e-3 && abs(Ilv - 1.8827) < 1e-3, 'bases are not 1.8827 A');",
    "S = 300e6; Ihv = S/(sqrt(3)*230e3)/809.6; Ilv = S/(sqrt(3)*11e3)/16925;\nassert(abs(Ihv - 0.9302) < 1e-3 && abs(Ilv - 0.9302) < 1e-3, 'bases are not 0.9302 A');")
p.write_text(s, encoding="utf-8")
print("patched")
