"""Step A7 patch of generate_stress_dataset_v3.m: plan quotas, stratified sampling (load bin, angle, residual flux, HiZ bin), source strength,
frequency deviation, OOD set. Every anchor is asserted; the patch refuses to run twice."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "balancedBin" not in s, "A7 patch already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:90]
    s = s.replace(old, new, 1)


def replace_function(name, new_text):
    """Replace the whole local function `name` (from 'function ... name(' up to the next top-level 'function' or comment banner)."""
    global s
    a = s.index("function ", s.index("function ") if False else 0) if False else None  # unused
    start = s.index("\nfunction ")  # placeholder, replaced below
    import re
    m = re.search(r"\nfunction [^\n]*\b" + name + r"\(", s)
    assert m, "function not found: " + name
    start = m.start() + 1
    nxt = re.search(r"\n(?:% =+\n|function )", s[start + 10:])
    end = start + 10 + nxt.start() + 1
    s = s[:start] + new_text + "\n" + s[end:]


rep("cfg.version   = 'v3-2026-10-21-A6';", "cfg.version   = 'v3-2026-10-21-A7';")

# ---------------------------------------------------------------- scenario table with the plan quotas (weights = trace counts for N = 3040)
replace_function("scenarioTable", r"""function ST = scenarioTable()
% name | zone | kind | fA fB fC fG | RfLo RfHi (ohm) | shouldTrip | weight      (weights = trace counts for N = 3040, IMPLEMENTATION_PLAN_V3.md 1.2)
% PHYSICS: the transformer is Y (ungrounded) / Delta; the LV internal fault blocks sit on the 11 kV DELTA terminals, the HV-side ones
% (InternalHV_*) on the 230 kV winding terminals. Single-line-to-ground current on the delta side returns through the grounded-Y LOAD neutral
% and grows with load. Internal HiZ Rf comes from the sensitivity sweep (hiz_bins.json), 3 bins: 87T-visible / AI-only / undetectable.
ft = {'AG' [1 0 0 1]; 'BG' [0 1 0 1]; 'CG' [0 0 1 1]; 'AB' [1 1 0 0]; 'BC' [0 1 1 0]; 'AC' [1 0 1 0]; ...
      'ABG' [1 1 0 1]; 'BCG' [0 1 1 1]; 'ACG' [1 0 1 1]; 'ABC' [1 1 1 0]; 'ABCG' [1 1 1 1]};
rows = {
 'Normal'               'Normal'   'normal'          0 0 0 0  0     0     false 303
 'Inrush_NoLoad'        'Inrush'   'inrush_noload'   0 0 0 0  0     0     false 200
 'Inrush_Loaded'        'Inrush'   'inrush_loaded'   0 0 0 0  0     0     false 120
 'Recovery_Inrush'      'Inrush'   'recovery_inrush' 1 1 1 0  0.05  0.3   false  80
 'Overexcitation'       'Overexc'  'overexc'         0 0 0 0  0     0     false 150
 'Internal_Evolving'    'Internal' 'evolving'        1 1 0 0  0.01  0.5   true   80
 'Internal_SOTF_AB'     'Internal' 'sotf'            1 1 0 0  0.01  2     true   40
 'Internal_SOTF_ABC'    'Internal' 'sotf'            1 1 1 0  0.01  2     true   40
 'External_HiZ_AB'      'External' 'external'        1 1 0 0  1     25    false  30
 'External_HiZ_ABC'     'External' 'external'        1 1 1 0  1     25    false  30
 'Stress_FaultInInrush' 'Internal' 'fault_in_inrush' 1 1 0 1  0.01  1     true  120
 'Stress_ExtInInrush'   'Inrush'   'ext_in_inrush'   1 1 0 0  0.01  5     false 100
};
for q = 1:size(ft, 1)
    v = ft{q, 2};
    rows(end + 1, :) = {['Internal_' ft{q, 1}],            'Internal', 'internal',      v(1), v(2), v(3), v(4), 0.01,  2,    true,  46}; %#ok<AGROW>
    rows(end + 1, :) = {['InternalHV_' ft{q, 1}],          'Internal', 'internal_hv',   v(1), v(2), v(3), v(4), 0.01,  2,    true,  18}; %#ok<AGROW>
    rows(end + 1, :) = {['External_' ft{q, 1}],            'External', 'external',      v(1), v(2), v(3), v(4), 0.01,  5,    false, 40}; %#ok<AGROW>
    rows(end + 1, :) = {['Stress_ExtCTSat_' ft{q, 1}],     'External', 'ct_stress_ext', v(1), v(2), v(3), v(4), 0.001, 0.05, false, 22}; %#ok<AGROW>
    rows(end + 1, :) = {['Stress_CTSat_Int_' ft{q, 1}],    'Internal', 'ct_stress_int', v(1), v(2), v(3), v(4), 0.01,  0.1,  true,  11}; %#ok<AGROW>
end
hz = {'AB' [1 1 0 0]; 'BC' [0 1 1 0]; 'AC' [1 0 1 0]; 'ABC' [1 1 1 0]; 'AG' [1 0 0 1]};      % 5 HiZ types x 48 (3 Rf bins x 16)
for q = 1:size(hz, 1)
    v = hz{q, 2};
    rows(end + 1, :) = {['Internal_HiZ_' hz{q, 1}], 'Internal', 'internal', v(1), v(2), v(3), v(4), 1, 25, true, 48}; %#ok<AGROW>
end
f = {'name','zone','kind','fA','fB','fC','fG','RfLo','RfHi','shouldTrip','weight'};
ST = cell2struct(rows, f, 2).';
for i = 1:numel(ST)
    t = ''; L = 'ABCG'; v = [ST(i).fA ST(i).fB ST(i).fC ST(i).fG];
    for q = 1:4, if v(q), t = [t L(q)]; end, end %#ok<AGROW>
    if isempty(t), t = 'None'; end
    ST(i).faultTag = t;
end
end
""")

# ---------------------------------------------------------------- stratified parameter draws (+ OOD blocks)
replace_function("drawParameters", r"""function p = drawParameters(sc, seed, ctx)
% ctx: struct('hiz', hiz_bins, 'seed0', base seed, 'within', i, 'n', n, 'block', OOD block 0-5, 'sid', scenario id).
%  within > 0 : STRATIFIED draws - each bin of a dimension (load bin, inception-angle class, residual-flux bin, HiZ bin) appears floor/ceil(n/K) times
%               over the n traces of the scenario, in an independent random order per dimension (balancedBin); inside a bin the draw is uniform.
%  within = 0 : plain random draws (self-test and the OOD set).
rng(seed, 'twister');
stress = startsWith(sc.kind, 'ct_stress');
ood = ctx.block;                                       % 0 = main set, 1-5 = OOD block
p.pf = 0.80 + 0.20 * rand();                           % 0.80-1.00 lagging
% --- load, % of RATED current: 4 bins 10-30 / 30-60 / 60-90 / 90-110 (stress: 60-85 / 85-110)
if stress, edges = [60 85 110]; else, edges = [10 30 60 90 110]; end
K = numel(edges) - 1; lb = bin(ctx, 1, K);
loadPct = edges(lb) + diff(edges([lb lb + 1])) * rand();
p.loadBin = lb + 2 * stress;                           % stress traces use the two upper bins (3 and 4)
if ood == 1, if rand() < 0.5, loadPct = 1 + 9 * rand(); p.loadBin = 0; else, loadPct = 110 + 20 * rand(); p.loadBin = 5; end, end   % OOD: 1-10 / 110-130 %
p.loadPu = loadPct / 100;                              % per unit of rated CURRENT (not of the load knob)
p.loadKnob = load_knob_for(loadPct, p.pf);             % ActivePower = knob*300 MVA*pf (calibrate_load.m)
p.srcScale = 0.95 + 0.10 * rand();
% --- noise (% of rated CT secondary current) and CT gain mismatch
lo = 0.05; hi = 1.0; if stress, lo = 1; hi = 3; end
p.noisePct = 10 ^ (log10(lo) + (log10(hi) - log10(lo)) * rand());
mm = 0.02; if stress, mm = 0.05; end
if ood == 5, p.noisePct = 4 + 2 * rand(); mm = 0.08; end                       % OOD: 5 % noise, +/-8 % mismatch
% --- CT burden (x 1 ohm): stress 4-10 x, other traces 1-3 x (probe_ct_stress.m); OOD 12-16 x
if stress, p.ctBurden = 10 ^ (log10(4) + log10(2.5) * rand()); else, p.ctBurden = 1 + 2 * rand(); end
if ood == 3, p.ctBurden = 12 + 4 * rand(); end
p.ctGain = 1 + (2 * rand(1, 6) - 1) * mm;
p.noiseSeeds = randi([1 2^31 - 2], 1, 6);
% --- source strength (series Z scale 0.5-2 x, log-uniform; OOD 3 x) and frequency (49.8-50.2 Hz; OOD +/-0.5 Hz)
p.srcZScale = 2 ^ (2 * rand() - 1);
p.freq = 49.8 + 0.4 * rand();
if ood == 2, p.srcZScale = 3 * (0.9 + 0.2 * rand()); p.freq = 50 + sign(rand() - 0.5) * (0.5 + 0.05 * (2 * rand() - 1)); end
if ood == 2 && p.freq == 50, p.freq = 50.5; end
% --- fault resistance
p.hizBin = 0;
if startsWith(sc.name, 'Internal_HiZ_')
    p.hizBin = bin(ctx, 4, 3);                         % 1 = 87T-visible, 2 = AI-only, 3 = below the detect limit (hiz_bins.json)
    bn = ctx.hiz.(sc.name(numel('Internal_HiZ_') + 1:end)).bins;
    r = {bn.visible, bn.ai_only, bn.undetect}; r = sort(r{p.hizBin}(:)');
    p.Rf = 10 ^ (log10(r(1)) + (log10(r(2)) - log10(r(1))) * rand());
elseif sc.RfHi > sc.RfLo
    p.Rf = 10 ^ (log10(sc.RfLo) + (log10(sc.RfHi) - log10(sc.RfLo)) * rand());
else
    p.Rf = sc.RfLo;
end
% --- timing
p.tEnergise = 0; p.tFault = NaN; p.tFault2 = NaN; p.faultClear = NaN;
switch sc.kind
    case 'recovery_inrush'
        p.tFault = 0.30 + 0.15 * rand();                                        % HV-bus fault starts ...
        p.faultClear = p.tFault + 0.040 + 0.060 * rand();                       % ... and clears 40-100 ms later
    case {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext'}
        p.tFault = 0.30 + 0.45 * rand();
    case 'evolving'
        p.tFault = 0.30 + 0.35 * rand();
        p.tFault2 = p.tFault + 0.02 + 0.08 * rand();
    case {'inrush_noload', 'inrush_loaded'}
        p.tEnergise = 0.10 + 0.60 * rand();
    case 'sotf'
        p.tEnergise = 0.20 + 0.50 * rand();
        p.tFault = p.tEnergise;                        % fault already present when energised
    case {'fault_in_inrush', 'ext_in_inrush'}
        p.tEnergise = 0.10 + 0.40 * rand();
        p.tFault = p.tEnergise + 0.02 + 0.28 * rand();
end
if isnan(p.tFault), p.tEvent = p.tEnergise; else, p.tEvent = p.tFault; end
if any(strcmp(sc.kind, {'normal', 'overexc'})), p.tEvent = NaN; end
if strcmp(sc.kind, 'recovery_inrush'), p.tEvent = p.faultClear; end              % the interesting event is the voltage recovery
% --- over-excitation level: 1.15-1.45 pu (core saturates above ~1.2 pu); OOD 1.50-1.60 pu
if strcmp(sc.kind, 'overexc'), p.srcScale = 1.15 + 0.30 * rand(); if ood == 4, p.srcScale = 1.50 + 0.10 * rand(); end, end
% --- point on wave: inception / closing / clearing angle class (4 quadrants + 'worst case' = within 10 deg of 0 or 90 deg), then the source phase
p.angleBin = 0;
if isnan(p.tEvent)
    p.srcPhase = 360 * rand();
else
    p.angleBin = bin(ctx, 2, 5);
    if p.angleBin <= 4
        ang = 90 * (p.angleBin - 1) + 90 * rand();
    else
        ang = mod(90 * randi(2) - 90 + 20 * (rand() - 0.5), 360);                % around 0 or 90 deg
    end
    p.srcPhase = mod(ang - 360 * p.freq * p.tEvent, 360);                          % so that the angle AT the event is `ang`
end
% --- residual flux (inrush-type scenarios): bin of the largest component, 3 fluxes summing to zero; OOD 0.9 pu
p.fluxBin = 0;
if any(strcmp(sc.kind, {'inrush_noload', 'inrush_loaded', 'sotf', 'fault_in_inrush', 'ext_in_inrush'}))
    p.fluxBin = bin(ctx, 3, 3);
    fe = [0 0.27 0.53 0.80]; target = fe([p.fluxBin p.fluxBin + 1]); if ood == 4, target = [0.85 0.95]; end
    for tries = 1:5000
        f12 = -1 + 2 * rand(1, 2); fl = [f12, -sum(f12)];
        if ood == 4, fl = [0.9, -0.45, -0.45]; fl = fl(randperm(3)) * sign(rand() - 0.5); end
        m = max(abs(fl));
        if m >= target(1) && m < target(2) && m <= 1.0, break; end
        if tries == 5000, fl = fl / max(m, eps) * mean(target); end
    end
    p.residualFlux = fl;
else
    flux = -0.8 + 1.6 * rand(1, 2); p.residualFlux = [flux, -sum(flux)];
end
p.inceptionAngle = NaN; if ~isnan(p.tEvent), p.inceptionAngle = mod(p.srcPhase + 360 * p.freq * p.tEvent, 360); end
p.oodBlock = ood;
end

function b = bin(ctx, dim, K)
% Stratum 1..K for dimension `dim`: balanced over the n traces of the scenario (random order), or uniform random when within = 0.
if ctx.within <= 0 || ctx.n <= 0
    b = randi(K); return;
end
b = balancedBin(ctx.seed0, ctx.sid, dim, ctx.within, ctx.n, K);
end

function b = balancedBin(seed0, sid, dim, within, n, K)
% Every bin 1..K appears floor(n/K) or ceil(n/K) times over within = 1..n; the order is an independent random permutation per (scenario, dimension).
rs = RandStream('twister', 'Seed', mod(seed0 * 7919 + sid * 104729 + dim * 1299709, 2 ^ 32 - 1));
perm = randperm(rs, n);
b = mod(perm(within) - 1, K) + 1;
end

function ctx = makeCtx(cfg, sc, within, n, block)
ctx = struct('hiz', cfg.hizBins, 'seed0', cfg.seed, 'within', within, 'n', n, 'block', block, 'sid', sum(double(sc.name) .* (1:numel(sc.name))));
end
""")

# ---------------------------------------------------------------- locate / prepare: source impedance block
rep("B.priV  = findBlock(model, 'Primary_side');", "B.srcZ  = findBlock(model, 'Three-Phase Series RLC Branch');   % source impedance (0.1 ohm + 1 mH), scaled per trace (A7)\nB.priV  = findBlock(model, 'Primary_side');")
rep("""cfg.blwnStd = sqrt(0.1 / str2double(get_param(B.blwn, 'Ts')));""", """cfg.srcZ0 = [str2double(get_param(B.srcZ, 'Resistance')), str2double(get_param(B.srcZ, 'Inductance'))];
assert(abs(cfg.srcZ0(1) - 0.1) < 1e-9 && abs(cfg.srcZ0(2) - 1e-3) < 1e-12, 'GenV3:SrcZ', 'unexpected source impedance %s / %s', get_param(B.srcZ, 'Resistance'), get_param(B.srcZ, 'Inductance'));
cfg.hizBins = jsondecode(fileread(fullfile(thisDir, 'hiz_bins.json')));            % A4: Rf bins of the internal HiZ faults
cfg.blwnStd = sqrt(0.1 / str2double(get_param(B.blwn, 'Ts')));""")

# ---------------------------------------------------------------- apply: frequency and source strength
rep(r"""for k = 1:3
    setp(B.vs{k}, 'Amplitude', amp, 'Phase', sprintf('%.6g', p.srcPhase + ph0(k)));
end""", r"""for k = 1:3
    setp(B.vs{k}, 'Amplitude', amp, 'Phase', sprintf('%.6g', p.srcPhase + ph0(k)), 'Frequency', sprintf('%.6g', p.freq));
end
setp(B.srcZ, 'Resistance', sprintf('%.6g', cfg.srcZ0(1) * p.srcZScale), 'Inductance', sprintf('%.6g', cfg.srcZ0(2) * p.srcZScale));""")

# ---------------------------------------------------------------- the noise check must allow the cycle-difference residual of a load current at f != 50 Hz
rep(r"""    rec.noiseOK = double(rec.noiseMeasured > 0.5 * rec.noiseExpected && rec.noiseMeasured < 2 * rec.noiseExpected + 0.01);""",
    r"""    resid = 2 * abs(sin(pi * p.freq * 32 / fs)) * sqrt(mean(seg(:) .^ 2));      % |x(t) - x(t - 20 ms)| of a periodic component at f != 50 Hz
    rec.noiseOK = double(rec.noiseMeasured > 0.5 * rec.noiseExpected && rec.noiseMeasured < 2 * rec.noiseExpected + 0.01 + resid);""")

# ---------------------------------------------------------------- storage of the new fields
rep(r"""'loadKnob', 'ctBurden'}""", r"""'loadKnob', 'ctBurden', 'loadBin', 'angleBin', 'fluxBin', 'hizBin', 'sourceZScale', 'frequencyHz', 'oodBlock'}""")
rep(r"""D.ctBurden(i) = p.ctBurden;""", r"""D.ctBurden(i) = p.ctBurden;
D.loadBin(i) = p.loadBin; D.angleBin(i) = p.angleBin; D.fluxBin(i) = p.fluxBin; D.hizBin(i) = p.hizBin;
D.sourceZScale(i) = p.srcZScale; D.frequencyHz(i) = p.freq; D.oodBlock(i) = p.oodBlock;""")

# ---------------------------------------------------------------- main: plan (incl. OOD) and per-sample context
rep(r"""weights = [ST.weight];
counts = max(1, round(nSamplesNum * weights / sum(weights)));
counts(1) = counts(1) + (nSamplesNum - sum(counts));
N = sum(counts);
plan = repelem(1:numel(ST), counts);
""", r"""weights = [ST.weight];
counts = max(1, round(nSamplesNum * weights / sum(weights)));
counts(1) = counts(1) + (nSamplesNum - sum(counts));
N = sum(counts);
plan = repelem(1:numel(ST), counts);
blockOf = zeros(1, N);
if strcmp(opts.Set, 'OOD')
    [plan, blockOf, counts, ST] = oodPlan(ST);          % 5 blocks x 60 traces (30 healthy + 30 faults); nSamples is ignored
    N = numel(plan);
end
firstOf = [1, cumsum(counts(1:end - 1)) + 1];
""")
rep(r"""    p = drawParameters(sc, cfg.seed + idx);
    p.sampleSeed = cfg.seed + idx;""", r"""    within = idx - firstOf(plan(idx)) + 1;
    if strcmp(opts.Set, 'OOD'), within = 0; end                      % OOD: plain random draws inside the block ranges
    p = drawParameters(sc, cfg.seed + idx, makeCtx(cfg, sc, within, counts(plan(idx)), blockOf(idx)));
    p.sampleSeed = cfg.seed + idx;""")
rep(r"""    p = drawParameters(sc, cfg.seed + 900000 + i); p.sampleSeed = cfg.seed + 900000 + i;""",
    r"""    p = drawParameters(sc, cfg.seed + 900000 + i, makeCtx(cfg, sc, 0, 0, 0)); p.sampleSeed = cfg.seed + 900000 + i;""")

# ---------------------------------------------------------------- OOD plan
rep(r"""% =====================================================================================
% Model configuration (every write is read back)""", r"""function [plan, blockOf, counts, ST] = oodPlan(ST)
% OOD set (IMPLEMENTATION_PLAN_V3.md 1.3): 5 blocks x 60 traces, half healthy and half faults. Ranges per block are applied in drawParameters.
%   1 extreme load (1-10 %, 110-130 % rated)   2 weak source 3 x + frequency 49.5 / 50.5 Hz   3 CT burden 12-16 x
%   4 over-excitation 1.50-1.60 pu + residual flux 0.9 pu   5 noise 5 % + CT mismatch +/-8 %
L = {
 1, {'Normal' 8; 'External_ABC' 8; 'External_AB' 7; 'Inrush_Loaded' 7}, {'Internal_AB' 8; 'Internal_ABC' 8; 'InternalHV_AB' 7; 'Internal_AG' 7}
 2, {'Normal' 10; 'External_ABC' 10; 'Inrush_Loaded' 10}, {'Internal_AB' 10; 'Internal_ABC' 10; 'InternalHV_AG' 10}
 3, {'Stress_ExtCTSat_ABC' 10; 'Stress_ExtCTSat_AB' 10; 'Stress_ExtCTSat_AG' 10}, {'Stress_CTSat_Int_AB' 10; 'Stress_CTSat_Int_ABC' 10; 'Stress_CTSat_Int_AG' 10}
 4, {'Overexcitation' 12; 'Inrush_NoLoad' 6; 'Inrush_Loaded' 6; 'Recovery_Inrush' 6}, {'Internal_AB' 10; 'Internal_SOTF_AB' 10; 'Stress_FaultInInrush' 10}
 5, {'Normal' 10; 'External_ABC' 10; 'Inrush_Loaded' 10}, {'Internal_AB' 10; 'Internal_ABC' 10; 'InternalHV_AB' 10}};
names = {ST.name}; plan = []; blockOf = [];
for r = 1:size(L, 1)
    for g = 2:3
        for q = 1:size(L{r, g}, 1)
            ix = find(strcmp(names, L{r, g}{q, 1}));
            assert(isscalar(ix), 'GenV3:OOD', 'OOD scenario %s not in the scenario table', L{r, g}{q, 1});
            plan = [plan, repmat(ix, 1, L{r, g}{q, 2})]; %#ok<AGROW>
            blockOf = [blockOf, repmat(L{r, 1}, 1, L{r, g}{q, 2})]; %#ok<AGROW>
        end
    end
end
counts = histcounts(plan, 0.5:1:numel(ST) + 0.5);
end

% =====================================================================================
% Model configuration (every write is read back)""")
p.write_text(s, encoding="utf-8")
print("A7 patch applied")
