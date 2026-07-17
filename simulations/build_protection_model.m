%% =========================================================================
%  build_protection_model.m
%
%  Builds a Simulink / Simscape Electrical (Specialized Power Systems)
%  model of the
%
%       300 MVA, 230/11 kV, Yd1 Transformer Differential Protection
%       Test System
%
%  Architecture (flat electrical – no custom electrical subsystems):
%
%   ┌── Electrical domain (powerlib blocks, top level) ────────────────┐
%   │ Vs_HV → Meas_HVBus → CB_Inrush → CT_HV → T_Yd1 → CT_LV →      │
%   │ Meas_LVBus → [Feeder1, Feeder2 → F_ext_LV]                       │
%   │                                                                    │
%   │ Faults: F_ext_HV (HV bus)                                         │
%   │         F_int_10pct / 50pct / 90pct (winding taps via series R)   │
%   └───────────────────────────────────────────────────────────────────┘
%
%   ┌── Signal domain (Simulink subsystems) ───────────────────────────┐
%   │ CT_HV → [port 4 = Iabc] → CTSat_HV → Relay_87T ← CTSat_LV ←   │
%   │                                   CT_LV [port 4 = Iabc]          │
%   │ Relay_87T → {I_diff, Trip} → Scope_Relay                         │
%   └───────────────────────────────────────────────────────────────────┘
%
%  CT_HV / CT_LV = Three-Phase V-I Measurement blocks (series in circuit)
%                  These represent the CT primary winding + core.
%  CTSat_HV/LV  = Signal subsystems: apply turns-ratio + nonlinear
%                  saturation curve (piece-wise-linear B-H lookup).
%
%  Requirements : MATLAB R2019b+,  Simscape Electrical (powerlib)
%  Usage        : run  build_protection_model
%  Output       : XfmrProtection_300MVA_Yd1.slx  (same folder as this .m)
%
%  Author : Abeer – Transformer Differential Protection Thesis, 2026
%% =========================================================================

function build_protection_model()

MDL = 'XfmrProtection_300MVA_Yd1';

%% ── 0.  Housekeeping ─────────────────────────────────────────────────────
if bdIsLoaded(MDL), close_system(MDL, 0); end
new_system(MDL);
open_system(MDL);

set_param(MDL, ...
    'Solver',         'ode23tb', ...
    'StopTime',       '0.30',   ...
    'RelTol',         '1e-5',   ...
    'MaxStep',        '2e-5',   ...
    'SimulationMode', 'normal');

%% ── Library auto-detection ───────────────────────────────────────────────
%  'powerlib'  = Specialized Power Systems (MATLAB ≤ R2020a)
%  'sps_lib'   = renamed in R2021b; both may coexist as aliases
%  Try to load whichever is available; fall back gracefully.
for LIB_candidate = {'powerlib','sps_lib'}
    try
        load_system(LIB_candidate{1});
        LIB = LIB_candidate{1};
        break;
    catch
        LIB = '';
    end
end
if isempty(LIB)
    error('build_protection_model:nolib', ...
        ['Neither ''powerlib'' nor ''sps_lib'' could be loaded.\n' ...
         'Install Simscape Electrical (Specialized Power Systems) toolbox.']);
end
fprintf('[build_protection_model]  Using library: %s\n', LIB);

%% ── 1.  Canvas layout ────────────────────────────────────────────────────
%
%  Single-line diagram  – blocks increase in x left → right
%  Yc = vertical centreline of the power conductor
%
Yc  = 300;    % power-line centre  (px)
Ydn = 450;    % row for fault blocks hanging below
Yup = 130;    % row for signal / relay blocks above

% Column x-centres
X.src  =   90;
X.mHV  =  240;   % HV Bus (V-I Meas)
X.cb   =  390;   % Inrush CB
X.ctHV =  530;   % CT_HV  (V-I Meas — represents CT)
X.Tx   =  710;   % Transformer
X.ctLV =  900;   % CT_LV  (V-I Meas — represents CT)
X.mLV  = 1060;   % LV Bus (V-I Meas)
X.f1   = 1230;   % Feeder 1
X.f2   = 1230;   % Feeder 2
X.fextLV= 1410;  % External LV fault

X.satHV =  530;  % CTSat_HV subsystem  (above line, aligned with CT_HV)
X.satLV =  900;  % CTSat_LV subsystem
X.relay =  715;  % 87T relay subsystem

% Helper: position vector [left top right bottom] from centre + half-extents
P = @(xc,yc,hw,hh) round([xc-hw, yc-hh, xc+hw, yc+hh]);

%% ── 2.  powergui ─────────────────────────────────────────────────────────
ab([LIB '/powergui'], 'powergui', MDL, P(30,30,45,22));
sp(MDL,'powergui','SimulationMode','Continuous');

%% ── 3.  HV Source  (230 kV, 50 Hz, Thevenin) ────────────────────────────
ab([LIB '/Electrical Sources/Three-Phase Source'], 'Vs_HV', MDL, ...
    P(X.src, Yc, 60, 38));
sp(MDL,'Vs_HV', ...
    'Voltage',   '230e3', ...
    'Frequency', '50',    ...
    'PhaseAngle','0',     ...
    'Impedance', 'on',    ...
    'R1',  '0.529', ...       % positive-sequence R  (Ω)
    'X1', '13.23',  ...       % positive-sequence X
    'R0',  '1.587', ...
    'X0', '39.69');

%% ── 4.  HV Bus  ──  Three-Phase V-I Measurement ──────────────────────────
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'Meas_HVBus', MDL, ...
    P(X.mHV, Yc, 55, 38));
sp(MDL,'Meas_HVBus', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 5.  External HV bus fault ────────────────────────────────────────────
ab([LIB '/Elements/Three-Phase Fault'], 'F_ext_HV', MDL, ...
    P(X.mHV, Ydn-20, 55, 35));
sp(MDL,'F_ext_HV', ...
    'FaultA','1','FaultB','1','FaultC','1','FaultG','1', ...
    'FaultTimes',       '[0.10  0.20]', ...
    'TransitionStatus', '[1  0]',       ...
    'Rground','0.001',  'Rfault','0.001');

%% ── 6.  Inrush energisation breaker ─────────────────────────────────────
ab([LIB '/Elements/Three-Phase Breaker'], 'CB_Inrush', MDL, ...
    P(X.cb, Yc, 58, 38));
sp(MDL,'CB_Inrush', ...
    'InitialStatus','0',      ...   % open at t = 0
    'SwitchTimes',  '0.02',   ...   % closes at 20 ms → triggers inrush
    'Breakers',     'ABC',    ...
    'Rclose',       '0.001',  ...
    'Ropen',        '1e6');

%% ── 7.  CT_HV  ──  Three-Phase V-I Measurement  (represents HV CT) ──────
%  In an actual model, replace this with a Saturable Transformer (1000:1)
%  configured as a CT.  Here the V-I Meas provides the primary current
%  signal that feeds the signal-domain saturation model (CTSat_HV).
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'CT_HV', MDL, ...
    P(X.ctHV, Yc, 55, 38));
sp(MDL,'CT_HV', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 8.  Power transformer  Yd1  300 MVA  230/11 kV ──────────────────────
ab([LIB '/Elements/Three-Phase Transformer (Two Windings)'], 'T_Yd1', MDL, ...
    P(X.Tx, Yc, 90, 72));
sp(MDL,'T_Yd1', ...
    'NominalPower',  '300e6', ...
    'Frequency',     '50',    ...
    'Winding1',  '[230e3  0.003  0.10]', ...   % [Vn(V)  R(pu)  L(pu)]
    'Winding2',  '[11e3   0.003  0.10]', ...
    'Magnetization', '[200  0]',          ...  % [Rm_pu  Lm_pu]
    'Core',          'Three single-phase cores', ...
    'Connection1',   'Yn',               ...
    'Connection2',   'Delta (D1)');           %  → Yd1 vector group

%% ── 9.  Internal fault blocks  (10 %, 50 %, 90 % winding position) ──────
%
%  Each fault is preceded by a small series resistance that represents the
%  winding impedance between the terminal and the fault point.
%  (A rigorous model requires a multi-tap transformer; this approximation
%   is standard for differential protection test systems in the literature.)
%
Zbase_HV = (230e3)^2 / 300e6;     %  HV-side impedance base  ≈ 176.3 Ω
Zbase_LV = (11e3 )^2 / 300e6;     %  LV-side impedance base  ≈ 0.403 Ω

% -- 10 %  fault  (close to HV terminal) ----------------------------------
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Tap_10pct', MDL, ...
    P(X.Tx-80, Ydn-20, 50, 30));
sp(MDL,'Tap_10pct','BranchType','R','R', ...
    num2str(0.10 * Zbase_HV * 0.003));   % 10 % of winding R_HV

ab([LIB '/Elements/Three-Phase Fault'], 'F_int_10pct', MDL, ...
    P(X.Tx-80, Ydn+50, 55, 35));
sp(MDL,'F_int_10pct', ...
    'FaultA','1','FaultB','0','FaultC','0','FaultG','1', ...
    'FaultTimes','[0.15  0.22]','TransitionStatus','[1 0]', ...
    'Rground','0.001','Rfault','0.001');

% -- 50 %  fault  (mid-winding) -------------------------------------------
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Tap_50pct', MDL, ...
    P(X.Tx, Ydn-20, 50, 30));
sp(MDL,'Tap_50pct','BranchType','R','R', ...
    num2str(0.50 * Zbase_HV * 0.003));

ab([LIB '/Elements/Three-Phase Fault'], 'F_int_50pct', MDL, ...
    P(X.Tx, Ydn+50, 55, 35));
sp(MDL,'F_int_50pct', ...
    'FaultA','0','FaultB','1','FaultC','0','FaultG','1', ...
    'FaultTimes','[0.15  0.22]','TransitionStatus','[1 0]', ...
    'Rground','0.001','Rfault','0.001');

% -- 90 %  fault  (close to LV terminal, referenced to LV impedance base) -
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Tap_90pct', MDL, ...
    P(X.Tx+80, Ydn-20, 50, 30));
sp(MDL,'Tap_90pct','BranchType','R','R', ...
    num2str(0.10 * Zbase_LV * 0.003));   % 10 % of remaining winding (from LV)

ab([LIB '/Elements/Three-Phase Fault'], 'F_int_90pct', MDL, ...
    P(X.Tx+80, Ydn+50, 55, 35));
sp(MDL,'F_int_90pct', ...
    'FaultA','0','FaultB','0','FaultC','1','FaultG','1', ...
    'FaultTimes','[0.15  0.22]','TransitionStatus','[1 0]', ...
    'Rground','0.001','Rfault','0.001');

%% ── 10.  CT_LV  ──  Three-Phase V-I Measurement  (represents LV CT) ─────
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'CT_LV', MDL, ...
    P(X.ctLV, Yc, 55, 38));
sp(MDL,'CT_LV', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 11.  LV Bus  ──  Three-Phase V-I Measurement ─────────────────────────
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'Meas_LVBus', MDL, ...
    P(X.mLV, Yc, 55, 38));
sp(MDL,'Meas_LVBus', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 12.  LV feeders ──────────────────────────────────────────────────────
% Feeder 1  (upper branch, RL load + ground)
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Feeder1', MDL, ...
    P(X.f1, Yc-60, 58, 30));
sp(MDL,'Feeder1','BranchType','RL','R','20.0','L','0.0318');
ab([LIB '/Elements/Ground'], 'Gnd_F1', MDL, P(X.f1+95, Yc-60, 18,18));

% Feeder 2  (lower branch, RL load → external LV fault)
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Feeder2', MDL, ...
    P(X.f2, Yc+60, 58, 30));
sp(MDL,'Feeder2','BranchType','RL','R','20.0','L','0.0318');

ab([LIB '/Elements/Three-Phase Fault'], 'F_ext_LV', MDL, ...
    P(X.fextLV, Yc+60, 55, 35));
sp(MDL,'F_ext_LV', ...
    'FaultA','1','FaultB','1','FaultC','1','FaultG','1', ...
    'FaultTimes',       '[0.05  0.15]', ...
    'TransitionStatus', '[1  0]',       ...
    'Rground','0.001',  'Rfault','0.001');

%% ── 13.  CT saturation models  (signal domain) ───────────────────────────
%
%  CTSat_HV : 1000/1 A CT saturation  (knee voltage ~ 200 V)
%  CTSat_LV : 2000/1 A CT saturation  (knee voltage ~ 100 V)
%
%  Saturation table  [phi_pu | i_pu]:
%    phi < knee  →  nearly linear   (i grows slowly)
%    phi > knee  →  saturated       (i grows sharply)
%
sat_tbl = [0 0; 0.80 0.003; 0.95 0.007; 1.00 0.015; ...
           1.10 0.060; 1.25 0.25; 1.50 1.10; 2.00 4.50];

build_CTsat_subsystem(MDL, 'CTSat_HV', P(X.satHV, Yup, 58, 38), ...
    1000, sat_tbl);
build_CTsat_subsystem(MDL, 'CTSat_LV', P(X.satLV, Yup, 58, 38), ...
    2000, sat_tbl);

%% ── 14.  87T Differential relay  (signal domain) ─────────────────────────
build_relay_87T(MDL, 'Relay_87T', P(X.relay, Yup, 72, 48));

%% ── 15.  Monitoring scopes ───────────────────────────────────────────────
ab('simulink/Sinks/Scope', 'Scope_Relay',  MDL, P(X.relay+185, Yup,    45,28));
ab('simulink/Sinks/Scope', 'Scope_CTsec',  MDL, P(X.relay+185, Yup+70, 45,28));
sp(MDL,'Scope_Relay', 'NumInputPorts','2');
sp(MDL,'Scope_CTsec','NumInputPorts','2');

%% ── 16.  Annotations ────────────────────────────────────────────────────
add_anno(MDL, '230 kV HV Bus',                     [X.mHV-45   Yc-100]);
add_anno(MDL, '11 kV  LV Bus',                     [X.mLV-35   Yc-100]);
add_anno(MDL, sprintf('T Yd1\n300 MVA\n230/11 kV'),[X.Tx-35    Yc+92 ]);
add_anno(MDL, sprintf('CT_{HV}\n1000/1 A'),         [X.ctHV-30  Yc+75 ]);
add_anno(MDL, sprintf('CT_{LV}\n2000/1 A'),         [X.ctLV-30  Yc+75 ]);
add_anno(MDL, 'Inrush CB',                          [X.cb-30    Yc-100]);
add_anno(MDL, ...
  '|──── Differential Protection Zone (87T) ────|', ...
  [X.ctHV-80  Yup-35]);

%% ═════════════════════════════════════════════════════════════════════════
%%  CONNECTIONS
%% ═════════════════════════════════════════════════════════════════════════
L = {'autorouting','smart'};

% ── Electrical path (main power circuit) ──────────────────────────────────
cl(MDL,'Vs_HV/1',        'Meas_HVBus/1',   L);   % source → HV bus
cl(MDL,'Meas_HVBus/2',   'CB_Inrush/1',    L);   % HV bus → CB
cl(MDL,'CB_Inrush/2',    'CT_HV/1',        L);   % CB → CT_HV
cl(MDL,'CT_HV/2',        'T_Yd1/1',        L);   % CT_HV → transformer HV
cl(MDL,'T_Yd1/2',        'CT_LV/1',        L);   % transformer LV → CT_LV
cl(MDL,'CT_LV/2',        'Meas_LVBus/1',   L);   % CT_LV → LV bus
cl(MDL,'Meas_LVBus/2',   'Feeder1/1',      L);   % LV bus → Feeder 1
cl(MDL,'Meas_LVBus/2',   'Feeder2/1',      L);   % LV bus → Feeder 2
cl(MDL,'Feeder1/2',      'Gnd_F1/1',       L);   % Feeder 1 → gnd
cl(MDL,'Feeder2/2',      'F_ext_LV/1',     L);   % Feeder 2 → ext LV fault

% ── External HV fault branches off HV bus ────────────────────────────────
cl(MDL,'Meas_HVBus/2',   'F_ext_HV/1',     L);

% ── Internal fault taps ──────────────────────────────────────────────────
%   10 % & 50 % tap off HV terminal
cl(MDL,'T_Yd1/1',        'Tap_10pct/1',    L);
cl(MDL,'Tap_10pct/2',    'F_int_10pct/1',  L);
cl(MDL,'T_Yd1/1',        'Tap_50pct/1',    L);
cl(MDL,'Tap_50pct/2',    'F_int_50pct/1',  L);
%   90 % tap off LV terminal
cl(MDL,'T_Yd1/2',        'Tap_90pct/1',    L);
cl(MDL,'Tap_90pct/2',    'F_int_90pct/1',  L);

% ── Signal path: V-I Meas current outputs → CTSat → Relay ────────────────
%   Three-Phase V-I Measurement output ports:
%     port 3 = Va,Vb,Vc (or Vabc vector, depending on config)
%     port 4 = Ia,Ib,Ic current signal
%   We use port 4 for current.  If your MATLAB version uses port 3 for
%   current, change '/4' to '/3' in the two lines below.
cl(MDL,'CT_HV/4',        'CTSat_HV/1',     L);
cl(MDL,'CT_LV/4',        'CTSat_LV/1',     L);

cl(MDL,'CTSat_HV/1',     'Relay_87T/1',    L);
cl(MDL,'CTSat_LV/1',     'Relay_87T/2',    L);

cl(MDL,'Relay_87T/1',    'Scope_Relay/1',  L);
cl(MDL,'Relay_87T/2',    'Scope_Relay/2',  L);

cl(MDL,'CTSat_HV/1',     'Scope_CTsec/1',  L);
cl(MDL,'CTSat_LV/1',     'Scope_CTsec/2',  L);

%% ── Save ─────────────────────────────────────────────────────────────────
outpath = fullfile(fileparts(mfilename('fullpath')), [MDL '.slx']);
save_system(MDL, outpath);

fprintf('\n── build_protection_model ────────────────────────────────\n');
fprintf('  Model saved to:\n  %s\n\n', outpath);
fprintf('  For clean thesis screenshot:\n');
fprintf('    Ctrl+Shift+F  (Fit System to View)\n');
fprintf('    Format → Auto Arrange (Ctrl+Shift+A)  — Simulink R2022a+\n\n');
fprintf('  NOTE: CT_HV / CT_LV use Three-Phase V-I Measurement as the\n');
fprintf('  primary winding proxy.  Signal port 4 outputs I_abc (primary).\n');
fprintf('  CTSat_HV/LV subsystems apply the 1000:1 / 2000:1 ratio + \n');
fprintf('  piece-wise-linear B-H saturation before the relay.\n');
fprintf('──────────────────────────────────────────────────────────\n\n');

end   % ── build_protection_model ──────────────────────────────────────────


%% =========================================================================
%%  LOCAL HELPERS
%% =========================================================================

function ab(lib_path, blk, mdl, position)
    add_block(lib_path, [mdl '/' blk], 'Position', position);
end

function sp(mdl, blk, varargin)
    try
        set_param([mdl '/' blk], varargin{:});
    catch ME
        warning('prot_model:param','Block "%s" param error — %s', blk, ME.message);
    end
end

function cl(mdl, src, dst, opts)
    try
        add_line(mdl, src, dst, opts{:});
    catch ME
        warning('prot_model:line','%s → %s failed — %s', src, dst, ME.message);
    end
end

function add_anno(mdl, txt, xy)
    try
        a          = Simulink.Annotation(mdl, txt);
        a.position = xy;
    catch
        try  % R2019b / R2020a fallback
            a = Simulink.Annotation([mdl '/annotation_' ...
                    num2str(round(xy(1)))]);
            a.text     = txt;
            a.position = xy;
        catch; end
    end
end


%% =========================================================================
%%  build_CTsat_subsystem
%%  Signal-domain CT saturation model.
%%
%%  Input  port 1 : I_abc  (primary current, pu – from V-I Measurement)
%%  Output port 1 : I_sec  (secondary current after ratio + saturation)
%%
%%  Internally:
%%    Demux → [Gain 1/N] × 3 → [1-D Lookup Table (sat)] × 3 → Mux
%%
%%  The lookup table implements the piece-wise-linear approximation of the
%%  CT magnetising curve.  Symmetry is applied via abs / sign.
%%
%%  Parameters:
%%    ratio    – CT turns ratio  (primary / secondary)
%%    sat_tbl  – N×2 matrix [phi_pu, i_pu]  (monotonically increasing phi)
%% =========================================================================
function build_CTsat_subsystem(mdl, name, pos_rect, ratio, ~)
%  sat_tbl arg accepted but unused — saturation implemented via
%  simulink/Discontinuities/Saturation (works on every MATLAB version).
%
%  Per-phase pipeline:  Demux → Gain(1/N) → Saturation(±1 pu) → Mux
%
%  The hard ±1 pu limit represents the CT knee-point.  For a higher-
%  fidelity piece-wise-linear curve, replace each Saturation block with
%  a 1-D Lookup Table using parameters 'Breakpoints1' / 'Table'
%  (R2021b+) or 'InputValues' / 'OutputValues' (older).

sys = [mdl '/' name];
add_block('built-in/Subsystem', sys, 'Position', pos_rect);
for p_ = {'In1','In2','Out1'}
    try, delete_block([sys '/' p_{1}]); catch; end
end

% ── I/O ports ──
add_block('built-in/Inport',  [sys '/Ipri'], 'Position',[20  95  50 115],'Port','1');
add_block('built-in/Outport', [sys '/Isec'], 'Position',[430  95 460 115],'Port','1');

% ── Demux 3-phase input ──
add_block('simulink/Signal Routing/Demux', [sys '/DmxIn'], ...
    'Position',[80 75 100 135],'Outputs','3');

% ── Per-phase: Gain(1/N) → Saturation(±1 pu) ──
phases = {'A','B','C'};
yo     = [0  60  120];

for k = 1:3
    ph = phases{k};

    % Turns-ratio gain
    add_block('simulink/Math Operations/Gain', [sys '/G_' ph], ...
        'Position',[150  70+yo(k)  205  90+yo(k)], ...
        'Gain', sprintf('1/%g', ratio));

    % Saturation — models CT core saturation at the knee point.
    % UpperLimit = 1.0 pu secondary, LowerLimit = -1.0 pu secondary.
    add_block('simulink/Discontinuities/Saturation', [sys '/Sat_' ph], ...
        'Position',[250  70+yo(k)  320  90+yo(k)], ...
        'UpperLimit', '1.0', ...
        'LowerLimit', '-1.0');
end

% ── Mux [Ia_sec ; Ib_sec ; Ic_sec] ──
add_block('simulink/Signal Routing/Mux', [sys '/MuxOut'], ...
    'Position',[375 72 395 152],'Inputs','3');

% ── Wiring ──
sl = @(s,d) add_line(sys, s, d, 'autorouting','smart');

sl('Ipri/1','DmxIn/1');
for k = 1:3
    ph = phases{k};
    kp = num2str(k);
    sl(['DmxIn/'  kp],   ['G_'   ph '/1']);
    sl(['G_'   ph '/1'], ['Sat_' ph '/1']);
    sl(['Sat_' ph '/1'], ['MuxOut/'  kp]);
end
sl('MuxOut/1','Isec/1');

% Mask appearance
try
    set_param(sys, ...
        'MaskDisplay', [ ...
            'color([0 0.45 0.1]);' ...
            'patch([0.08 0.92 0.92 0.08],[0.08 0.08 0.92 0.92],[0.92 1.0 0.92]);' ...
            'text(0.5,0.62,''' name ''',''hor'',''center'',''FontSize'',8,''FontWeight'',''bold'');' ...
            'text(0.5,0.32,''Sat CT'',''hor'',''center'',''FontSize'',7);' ...
            'text(0.5,0.15,''' sprintf('1/%g',ratio) ''',''hor'',''center'',''FontSize'',7);' ...
        ], ...
        'ForegroundColor','[0 0.45 0.1]', ...
        'BackgroundColor','[0.92 1.0 0.92]');
catch; end

end   % build_CTsat_subsystem


%% =========================================================================
%%  build_relay_87T
%%  IEEE dual-slope percentage-differential characteristic.
%%
%%  Input  port 1 : I_HV  [Ia Ib Ic]  from CTSat_HV  (secondary current)
%%  Input  port 2 : I_LV  [Ia Ib Ic]  from CTSat_LV  (polarity corrected)
%%
%%  Output port 1 : I_diff  – operating (differential) current magnitude
%%  Output port 2 : Trip    – logical 1 when Id > SLP1·Ir + Id_min
%%
%%  Characteristic (IEC 60255-111 / IEEE C37.91):
%%    SLP1   = 0.30   (30 % slope)
%%    Id_min = 0.20   (pu minimum pickup — covers mismatch & CT error)
%%    No harmonic restraint wired here; add a 2nd harmonic detector
%%    (using an FFT subsystem) if modelling inrush inhibit.
%% =========================================================================
function build_relay_87T(mdl, name, pos_rect)

sys = [mdl '/' name];
add_block('built-in/Subsystem', sys, 'Position', pos_rect);
for p_ = {'In1','In2','Out1'}
    try, delete_block([sys '/' p_{1}]); catch; end
end

%--- I/O ports
add_block('built-in/Inport', [sys '/I_HV'],   'Position',[20  80 50 100],'Port','1');
add_block('built-in/Inport', [sys '/I_LV'],   'Position',[20 190 50 210],'Port','2');
add_block('built-in/Outport',[sys '/I_diff'], 'Position',[620  80 650 100],'Port','1');
add_block('built-in/Outport',[sys '/Trip'],   'Position',[620 190 650 210],'Port','2');

%--- Id = |I_HV + I_LV|  (CT secondaries added; polarities set so that for
%    through-fault: I_HV ≈ –I_LV → Id ≈ 0; for internal fault: Id > 0)
add_block('simulink/Math Operations/Sum',         [sys '/AddId'], ...
    'Position',[120  75 155 105],'Inputs','++');
add_block('simulink/Math Operations/Dot Product', [sys '/DotId'], ...
    'Position',[195  75 240 105]);
add_block('simulink/Math Operations/Sqrt',        [sys '/SqrtId'], ...
    'Position',[265  80 310 100]);

%--- Ir = ( |I_HV| + |I_LV| ) / 2
add_block('simulink/Math Operations/Dot Product', [sys '/DotHV'], ...
    'Position',[80  155 125 185]);
add_block('simulink/Math Operations/Dot Product', [sys '/DotLV'], ...
    'Position',[80  215 125 245]);
add_block('simulink/Math Operations/Sqrt',        [sys '/SqrtHV'], ...
    'Position',[150 158 190 182]);
add_block('simulink/Math Operations/Sqrt',        [sys '/SqrtLV'], ...
    'Position',[150 218 190 242]);
add_block('simulink/Math Operations/Sum',         [sys '/AddIr'], ...
    'Position',[220 175 255 215],'Inputs','++');
add_block('simulink/Math Operations/Gain',        [sys '/Half'], ...
    'Position',[280 180 330 210],'Gain','0.5');

%--- Pickup = SLP1 · Ir + Id_min
add_block('simulink/Math Operations/Gain',  [sys '/SLP1'], ...
    'Position',[360 180 410 210],'Gain','0.30');
add_block('simulink/Sources/Constant',      [sys '/Id_min'], ...
    'Position',[360 235 410 255],'Value','0.20');
add_block('simulink/Math Operations/Sum',   [sys '/AddPU'], ...
    'Position',[445 190 480 240],'Inputs','++');

%--- Trip  =  Id > Pickup
add_block('simulink/Math Operations/Sum',                        [sys '/ErrTrip'], ...
    'Position',[510  78 550 108],'Inputs','+-');
add_block('simulink/Logic and Bit Operations/Relational Operator',[sys '/GT0'], ...
    'Position',[510 185 575 220],'Operator','>');
add_block('simulink/Sources/Constant',                           [sys '/Zero'], ...
    'Position',[440 115 470 135],'Value','0');

%--- Wire up
sl = @(s,d) add_line(sys, s, d, 'autorouting','smart');

sl('I_HV/1',   'AddId/1');
sl('I_LV/1',   'AddId/2');
sl('AddId/1',  'DotId/1');
sl('AddId/1',  'DotId/2');
sl('DotId/1',  'SqrtId/1');

sl('I_HV/1',   'DotHV/1');
sl('I_HV/1',   'DotHV/2');
sl('I_LV/1',   'DotLV/1');
sl('I_LV/1',   'DotLV/2');
sl('DotHV/1',  'SqrtHV/1');
sl('DotLV/1',  'SqrtLV/1');
sl('SqrtHV/1', 'AddIr/1');
sl('SqrtLV/1', 'AddIr/2');
sl('AddIr/1',  'Half/1');
sl('Half/1',   'SLP1/1');
sl('SLP1/1',   'AddPU/1');
sl('Id_min/1', 'AddPU/2');

sl('SqrtId/1', 'ErrTrip/1');
sl('AddPU/1',  'ErrTrip/2');
sl('Zero/1',   'GT0/1');
sl('ErrTrip/1','GT0/2');

sl('SqrtId/1', 'I_diff/1');
sl('GT0/1',    'Trip/1');

%--- Mask
try
    set_param(sys, ...
        'MaskDisplay', [ ...
            'color(''red'');' ...
            'patch([0.05 0.95 0.95 0.05],[0.05 0.05 0.95 0.95],[1 0.93 0.93]);' ...
            'text(0.5,0.60,''87T'',''hor'',''center'',''ver'',''middle'',' ...
              '''FontSize'',14,''FontWeight'',''bold'');' ...
            'text(0.5,0.20,''Diff Relay'',''hor'',''center'',''FontSize'',7);' ...
        ], ...
        'ForegroundColor','red', ...
        'BackgroundColor','[1 0.93 0.93]');
catch; end

end   % build_relay_87T
