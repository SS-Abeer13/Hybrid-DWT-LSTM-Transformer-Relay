"""Step A6 patch of generate_stress_dataset_v3.m: over-excitation and recovery-inrush scenarios (sympathetic inrush is skipped by author decision)."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "recovery_inrush" not in s, "A6 patch already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:80]
    s = s.replace(old, new, 1)


rep("cfg.version   = 'v3-2026-10-21-A5';", "cfg.version   = 'v3-2026-10-21-A6';")

# --- 6th fault block: HV-bus (external, upstream of the HV breaker and CTs) fault for recovery inrush
rep(r"""findBlock(model, 'External_Fault'), findBlock(model, 'Internal_Fault_HV')}, ...""",
    r"""findBlock(model, 'External_Fault'), findBlock(model, 'Internal_Fault_HV'), findBlock(model, 'External_Fault_HV')}, ...""")
rep(r"""findBlock(model, 'Step4'), findBlock(model, 'Step_HV')});   % 5 = HV-side internal (A5)""",
    r"""findBlock(model, 'Step4'), findBlock(model, 'Step_HV'), findBlock(model, 'Step_ExtHV')});   % 5 = HV-side internal (A5), 6 = HV-bus external (A6)""")

# --- fault reset: restore external control and default switching times on every block
rep(r"""    setp(f.blk, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01');""",
    r"""    setp(f.blk, 'External', 'on', 'SwitchTimes', '[0.05 1]', 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01');""")

# --- scenario handling
rep(r"""    case 'internal_hv'                                  % fault on the 230 kV winding terminals, inside the HV CT zone (A5)""",
    r"""    case 'overexc'                                      % healthy, source voltage 1.15-1.45 pu from t = 0 (core saturates above ~1.25 pu): 5th harmonic
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
    case 'recovery_inrush'                              % 3-phase fault on the 230 kV bus (outside the CT zone), cleared by its own switching times
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        setp(B.fault(6).blk, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'off', 'FaultResistance', sprintf('%.6g', p.Rf), ...
            'External', 'off', 'SwitchTimes', sprintf('[%.6f %.6f]', p.tFault, p.faultClear));
    case 'internal_hv'                                  % fault on the 230 kV winding terminals, inside the HV CT zone (A5)""")

# --- parameter draws
rep(r"""switch sc.kind
    case {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext'}
        p.tFault = 0.30 + 0.45 * rand();""", r"""p.faultClear = NaN;
if strcmp(sc.kind, 'overexc'), p.srcScale = 1.15 + 0.30 * rand(); end          % 1.15-1.45 pu (OOD: 1.50-1.60 in A7)
switch sc.kind
    case 'recovery_inrush'
        p.tFault = 0.30 + 0.15 * rand();                                        % HV-bus fault starts ...
        p.faultClear = p.tFault + 0.040 + 0.060 * rand();                       % ... and clears 40-100 ms later (clearing angle random)
    case {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext'}
        p.tFault = 0.30 + 0.45 * rand();""")
rep(r"""if isnan(p.tFault), p.tEvent = p.tEnergise; else, p.tEvent = p.tFault; end
if strcmp(sc.kind, 'normal'), p.tEvent = NaN; end""", r"""if isnan(p.tFault), p.tEvent = p.tEnergise; else, p.tEvent = p.tFault; end
if any(strcmp(sc.kind, {'normal', 'overexc'})), p.tEvent = NaN; end
if strcmp(sc.kind, 'recovery_inrush'), p.tEvent = p.faultClear; end              % the interesting event is the voltage recovery""")
# Rf for recovery: 0.05-0.3 ohm (HV-bus voltage dip 0.14-0.6 pu); the scenario row carries RfLo/RfHi

# --- store the clearing time and new measures
rep(r"""D.faultTime2(i) = p.tFault2;""", r"""D.faultTime2(i) = p.tFault2; if strcmp(sc.kind, 'recovery_inrush'), D.faultTime2(i) = p.faultClear; end""")
rep(r"""'ctRatioErrorMax', NaN, 'fingerprint', '',""", r"""'ctRatioErrorMax', NaN, 'harm5Ratio', NaN, 'diffRmsPu', NaN, 'recDiffPeakPu', NaN, 'recH2', NaN, 'fingerprint', '',""")
rep(r"""'ctRatioErrorMax', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});""", r"""'ctRatioErrorMax', 'harm5Ratio', 'diffRmsPu', 'recDiffPeakPu', 'recH2', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});""")
rep(r"""'ctRatioErrorMax', 'checkPassed', 'loadKnob', 'ctBurden'}""", r"""'ctRatioErrorMax', 'harm5Ratio', 'diffRmsPu', 'recDiffPeakPu', 'recH2', 'checkPassed', 'loadKnob', 'ctBurden'}""")

# --- measures (differential = plant-compensated d = Is - Ip*M)
rep(r"""% duplicate waveform?""", r"""% harmonic signatures of the plant-compensated differential d = Is - Ip*M (the LSTM input): over-excitation (5th) and recovery inrush (2nd)
Mpl = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
dpl = Is - Ip * Mpl;
dft = @(i0) abs(fft(dpl(i0:i0 + 31, :), [], 1));                  % 32-point DFT: bin 2 = 50 Hz, 3 = 100 Hz, 6 = 250 Hz
if strcmp(sc.kind, 'overexc')
    i0 = round(0.60 * fs) + 1; F = dft(i0);
    rec.harm5Ratio = mean(F(6, :) ./ max(F(2, :), 1e-4));
    rec.diffRmsPu = mean(sqrt(mean(dpl(i0:i0 + 31, :) .^ 2, 1))) / cfg.Inom(1);
elseif strcmp(sc.kind, 'recovery_inrush')
    best = 0; h2 = NaN;
    for i0 = round((p.faultClear + 0.005) * fs):2:min(round((p.faultClear + 0.15) * fs), size(dpl, 1) - 32)
        r = mean(sqrt(mean(dpl(i0:i0 + 31, :) .^ 2, 1))) / cfg.Inom(1);
        if r > best, best = r; F = dft(i0); h2 = mean(F(3, :) ./ max(F(2, :), 1e-4)); end
    end
    rec.recDiffPeakPu = best; rec.recH2 = h2;
end

% duplicate waveform?""")
# no 'faultDiffPu' for the HV-bus fault (it is outside the zone), realised-load window and target scale with the source voltage
rep(r"""    if ~isnan(p.tFault)
        rmsWin = @(t1, t2)""", r"""    if ~isnan(p.tFault) && ~strcmp(sc.kind, 'recovery_inrush')
        rmsWin = @(t1, t2)""")
rep(r"""elseif strcmp(sc.kind, 'normal')
    loadWin = t > 0.12 & t < 1.0;""", r"""elseif any(strcmp(sc.kind, {'normal', 'overexc'}))
    loadWin = t > 0.12 & t < 1.0;
elseif strcmp(sc.kind, 'recovery_inrush')
    loadWin = t > 0.12 & t < 0.28;""")
rep(r"""    target = 100 * p.loadPu;
    rec.loadOK""", r"""    target = 100 * p.loadPu * p.srcScale;                         % constant-impedance load: current follows the source voltage
    rec.loadOK""")

# --- healthy window for the noise check: over-excitation is periodic like Normal
rep(r"""if strcmp(sc.kind, 'normal'), healthy = t > 0.12 & t < 1.0; end""", r"""if any(strcmp(sc.kind, {'normal', 'overexc'})), healthy = t > 0.12 & t < 1.0; end""")

# --- scenario rows
rep(r"""f = {'name','zone','kind','fA','fB','fC','fG','RfLo','RfHi','shouldTrip','weight'};
ST = cell2struct(rows, f, 2).';""", r"""rows(end + 1, :) = {'Overexcitation',  'Overexc', 'overexc',         0, 0, 0, 0, 0,    0,   false, 4};
rows(end + 1, :) = {'Recovery_Inrush', 'Inrush',  'recovery_inrush', 1, 1, 1, 0, 0.05, 0.3, false, 3};
f = {'name','zone','kind','fA','fB','fC','fG','RfLo','RfHi','shouldTrip','weight'};
ST = cell2struct(rows, f, 2).';""")

# --- progress line shows the new signature; self-test cases
rep(r"""'Stress_CTSat_Int_AB', 'InternalHV_AG', 'InternalHV_AB'};""", r"""'Stress_CTSat_Int_AB', 'InternalHV_AG', 'InternalHV_AB', 'Overexcitation', 'Recovery_Inrush'};""")
p.write_text(s, encoding="utf-8")
print("A6 patch applied")
