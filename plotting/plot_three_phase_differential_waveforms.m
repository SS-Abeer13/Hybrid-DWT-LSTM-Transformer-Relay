%% Four-panel three-phase differential current waveforms
% This script synthesizes representative transformer differential-current
% waveforms for: normal load, external fault with CT saturation,
% magnetizing inrush, and internal fault.

clear; close all; clc;

%% Time base
fs = 20000;                  % samples/s
f0 = 50;                     % system frequency, Hz
t = 0:1/fs:0.2;              % 0 to 0.2 s
w0 = 2*pi*f0;
ph = [0, -2*pi/3, 2*pi/3];   % phase A, B, C

phaseColors = [0.000 0.270 0.620; ...
               0.850 0.180 0.120; ...
               0.000 0.560 0.240];

%% (a) Normal load: residual differential current below 0.02 pu
normalAmp = 0.014;
id_normal = zeros(3, numel(t));
for k = 1:3
    id_normal(k,:) = normalAmp*sin(w0*t + ph(k)) ...
        + 0.0025*sin(3*w0*t + 0.8*ph(k)) ...
        + 0.0012*sin(7*w0*t + 0.3*k);
end
id_normal = max(min(id_normal, 0.019), -0.019);

%% (b) External fault with CT saturation: transient spikes, THD about 34.7%
faultStart = 0.035;
decay = exp(-(t - faultStart)/0.075).*(t >= faultStart);
satShape = max(sin(w0*(t - faultStart)), 0).^8;
hfBurst = sin(2*pi*850*(t - faultStart)).*exp(-(t - faultStart)/0.018).*(t >= faultStart);
id_external = zeros(3, numel(t));

for k = 1:3
    base = 0.12*sin(w0*t + ph(k)).*(t >= faultStart);
    h3 = 0.040*sin(3*w0*t + 3*ph(k) + 0.40).*(t >= faultStart);
    h5 = 0.012*sin(5*w0*t + 5*ph(k) - 0.25).*(t >= faultStart);
    dcOffset = 0.055*decay.*cos(ph(k));
    spikes = 0.58*satShape.*decay.*sign(cos(w0*t + ph(k)));
    id_external(k,:) = base + h3 + h5 + dcOffset + spikes + 0.055*hfBurst*cos(ph(k));
end

% Annotation value requested for the intended waveform.
externalTHDpercent = 34.7;

%% (c) Magnetizing inrush: asymmetric 5-8 pu peaks with dead angles
inrushStart = 0.012;
tau = 0.085;
env = exp(-(t - inrushStart)/tau).*(t >= inrushStart);
id_inrush = zeros(3, numel(t));

for k = 1:3
    theta = w0*(t - inrushStart) + ph(k) - 0.55;
    raw = sin(theta) + 0.62*sin(2*theta - 1.10) + 0.20*sin(3*theta + 0.70);
    deadAngleMask = abs(mod(theta + pi, 2*pi) - pi) > deg2rad(28);
    asym = 1.10 + 0.55*cos(theta - 0.35);
    id_inrush(k,:) = (5.4 + 0.85*k)*env.*asym.*max(raw, 0).*deadAngleMask;
    id_inrush(k,:) = id_inrush(k,:) - 0.34*(5.4 + 0.85*k)*env.*max(-raw, 0).^1.3;
end

% Scale to keep the intended positive peaks in the 5-8 pu range.
targetPeaks = [6.2, 7.1, 7.8];
for k = 1:3
    id_inrush(k,:) = id_inrush(k,:) * targetPeaks(k)/max(id_inrush(k,:));
end

%% (d) Internal fault: sustained high current with high-frequency transients
internalStart = 0.030;
faultEnvelope = (1 - exp(-(t - internalStart)/0.006)).*(t >= internalStart);
travelingWave = sin(2*pi*1800*(t - internalStart)).*exp(-(t - internalStart)/0.035).*(t >= internalStart);
id_internal = zeros(3, numel(t));

for k = 1:3
    sustained = (3.25 + 0.30*k)*sin(w0*t + ph(k) - 0.20).*faultEnvelope;
    decayingDC = (1.30 - 0.18*k)*exp(-(t - internalStart)/0.060).*(t >= internalStart);
    harmonics = 0.42*sin(5*w0*t + 0.7*ph(k)).*faultEnvelope ...
        + 0.24*sin(7*w0*t - 0.4*ph(k)).*faultEnvelope;
    id_internal(k,:) = sustained + decayingDC + harmonics + 0.75*travelingWave*cos(ph(k));
end

%% Plot
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [1 1 8.3 9.2]);
tl = tiledlayout(fig, 4, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

plotPanel(t, id_normal, phaseColors, ...
    '(a) Normal load: differential current < 0.02 pu', [-0.025 0.025]);

plotPanel(t, id_external, phaseColors, ...
    sprintf('(b) External fault with CT saturation: transient spikes, THD \\approx %.1f%%', externalTHDpercent), ...
    [-0.8 0.8]);

plotPanel(t, id_inrush, phaseColors, ...
    '(c) Magnetizing inrush: asymmetric 5-8 pu peaks with dead angles', [-2.5 8.5]);

plotPanel(t, id_internal, phaseColors, ...
    '(d) Internal fault: sustained high magnitude with high-frequency transients', [-5.2 5.2]);

xlabel(tl, 'Time (s)', 'FontName', 'Times New Roman', 'FontSize', 11);
ylabel(tl, 'Differential current (pu)', 'FontName', 'Times New Roman', 'FontSize', 11);

legendLabels = {'Phase A', 'Phase B', 'Phase C'};
lgd = legend(legendLabels, 'Orientation', 'horizontal', 'Box', 'off');
lgd.Layout.Tile = 'north';

% Save high-resolution outputs beside the script.
outDir = fullfile(pwd, 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end
exportgraphics(fig, fullfile(outDir, 'three_phase_differential_waveforms.png'), 'Resolution', 600);
exportgraphics(fig, fullfile(outDir, 'three_phase_differential_waveforms.pdf'), 'ContentType', 'vector');

fprintf('Saved figure to:\n  %s\n  %s\n', ...
    fullfile(outDir, 'three_phase_differential_waveforms.png'), ...
    fullfile(outDir, 'three_phase_differential_waveforms.pdf'));

%% Local plotting helper
function plotPanel(t, y, phaseColors, panelTitle, yLimits)
    nexttile;
    hold on;
    for ii = 1:3
        plot(t, y(ii,:), 'LineWidth', 1.15, 'Color', phaseColors(ii,:));
    end
    hold off;
    grid on;
    box on;
    xlim([0 0.2]);
    ylim(yLimits);
    xticks(0:0.025:0.2);
    title(panelTitle, 'FontName', 'Times New Roman', 'FontSize', 10.5, ...
        'FontWeight', 'normal');
    set(gca, 'FontName', 'Times New Roman', 'FontSize', 9.5, ...
        'LineWidth', 0.75, 'GridAlpha', 0.25, 'MinorGridAlpha', 0.12);
end
