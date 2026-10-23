"""A7b: over-excitation realised load from the LV current only; recovery-inrush check = the HV-bus fault must visibly reduce the HV current."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "hvDipRatio" not in s, "A7b already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:90]
    s = s.replace(old, new, 1)


rep("cfg.version   = 'v3-2026-10-21-A7';", "cfg.version   = 'v3-2026-10-21-A7b';")
rep(r"""    rec.loadRealisedPct = 100 * 0.5 * (pH + pL);""", r"""    rec.loadRealisedPct = 100 * 0.5 * (pH + pL);
    if strcmp(sc.kind, 'overexc'), rec.loadRealisedPct = 100 * pL; end      % HV current includes the saturated core's magnetising current""")
rep(r"""% Energisation time must ALWAYS match: this is what caught the stuck-breaker bug.""", r"""% Recovery inrush: the event is the voltage recovery, which builds over a cycle, so the sharp-edge timing test does not apply. Instead the
% HV-bus fault must visibly reduce the HV current while it is on (constant-impedance load follows the dipped voltage).
if strcmp(sc.kind, 'recovery_inrush')
    rb = mean(sqrt(mean(Ip(t >= p.tFault - 0.04 & t <= p.tFault - 0.005, :) .^ 2, 1)));
    rd = mean(sqrt(mean(Ip(t >= p.tFault + 0.012 & t <= p.faultClear - 0.005, :) .^ 2, 1)));
    hvDipRatio = rd / max(rb, eps);
    rec.timingOK = double(hvDipRatio < 0.85);
    rec.eventVisible = rec.timingOK;
end
% Energisation time must ALWAYS match: this is what caught the stuck-breaker bug.""")
p.write_text(s, encoding="utf-8")
print("A7b applied")
