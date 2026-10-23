"""Step A5 patch of generate_stress_dataset_v3.m: HV-side internal faults ('internal_hv' kind) using the new Internal_Fault_HV block."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "internal_hv" not in s, "A5 patch already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:80]
    s = s.replace(old, new, 1)


rep("cfg.version   = 'v3-2026-10-21-A3b';", "cfg.version   = 'v3-2026-10-21-A5';")

# 5th fault block: HV-side internal fault (added by add_hv_internal_fault.m)
rep("""B.fault = struct('blk', {findBlock(model, 'Internal_Fault1'), findBlock(model, 'Internal_Fault2'), ...
                         findBlock(model, 'Internal_Fault3'), findBlock(model, 'External_Fault')}, ...
                 'step', {findBlock(model, 'Step3'), findBlock(model, 'Step_Evolve2'), ...
                          findBlock(model, 'Step_Evolve3'), findBlock(model, 'Step4')});""",
    """B.fault = struct('blk', {findBlock(model, 'Internal_Fault1'), findBlock(model, 'Internal_Fault2'), ...
                         findBlock(model, 'Internal_Fault3'), findBlock(model, 'External_Fault'), findBlock(model, 'Internal_Fault_HV')}, ...
                 'step', {findBlock(model, 'Step3'), findBlock(model, 'Step_Evolve2'), ...
                          findBlock(model, 'Step_Evolve3'), findBlock(model, 'Step4'), findBlock(model, 'Step_HV')});   % 5 = HV-side internal (A5)""")

# scenario handling
rep("""    case {'internal', 'ct_stress_int'}
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);""",
    """    case {'internal', 'ct_stress_int'}
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case 'internal_hv'                                  % fault on the 230 kV winding terminals, inside the HV CT zone (A5)
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 5, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);""")
rep("""    case {'internal', 'external', 'ct_stress_int', 'ct_stress_ext'}
        p.tFault = 0.30 + 0.45 * rand();""", """    case {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext'}
        p.tFault = 0.30 + 0.45 * rand();""")

# scenario rows: HV-side internal faults, all 11 types (weights placeholder until A7)
rep("""for q = 1:size(ft, 1)
    v = ft{q, 2};""", """for q = 1:size(ft, 1)
    v = ft{q, 2};
    rows(end + 1, :) = {['InternalHV_' ft{q, 1}], 'Internal', 'internal_hv', v(1), v(2), v(3), v(4), 0.01, 2, true, 1}; %#ok<AGROW>""")

# self-test: one HV-side case
rep("'Stress_ExtCTSat_ABC', 'Stress_ExtCTSat_AG', 'Stress_CTSat_Int_AB'};", "'Stress_ExtCTSat_ABC', 'Stress_ExtCTSat_AG', 'Stress_CTSat_Int_AB', 'InternalHV_AG', 'InternalHV_AB'};")
p.write_text(s, encoding="utf-8")
print("A5 patch applied")
