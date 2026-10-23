function knob = load_knob_for(pctRated, pf, cal)
%LOAD_KNOB_FOR Load-knob value that realises a target load in % of RATED current at power factor pf (calibrate_load.m table).
%   knob = load_knob_for(60, 0.9)   % -> ActivePower = knob*300e6*pf, InductivePower = knob*300e6*sqrt(1-pf^2)
% Monotone (pchip) interpolation of knob vs realised % on each calibrated power factor, then linear in pf.
% Targets below the first table point extrapolate linearly through the origin; above the last point (136 %) it errors.
if nargin < 3, c = relay_config(); cal = c.LOAD_KNOB_PER_RATED; end
assert(isscalar(pctRated) && pctRated > 0, 'target load must be a positive scalar (%% of rated)');
k = zeros(1, numel(cal.pf));
for j = 1:numel(cal.pf)
    x = cal.pctRated(j, :); y = cal.knob;
    assert(pctRated <= x(end) + 1e-9, 'load_knob_for: %.1f %% of rated is above the reachable maximum %.1f %% (pf %.2f)', pctRated, x(end), cal.pf(j));
    if pctRated < x(1)
        k(j) = y(1) * pctRated / x(1);
    else
        k(j) = interp1(x, y, pctRated, 'pchip');
    end
end
pf = min(max(pf, cal.pf(1)), cal.pf(end));
knob = interp1(cal.pf, k, pf, 'linear');
end
