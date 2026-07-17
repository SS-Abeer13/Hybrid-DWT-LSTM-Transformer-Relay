%% Side-by-side comparison: conventional 87T relay vs hybrid DWT-LSTM model
% Thesis-ready before/after figure with noisy differential-current traces,
% relay decisions, and reported benchmark metrics.

clear; close all; clc;
rng(87, 'twister');

%% Time base and style
fs = 20000;                  % samples/s
f0 = 50;                     % system frequency, Hz
t = 0:1/fs:0.2;              % 0 to 0.2 s
w0 = 2*pi*f0;
ph = [0, -2*pi/3, 2*pi/3];   % phase A, B, C

phaseColors = [0.000 0.270 0.620; ...
               0.850 0.180 0.120; ...
               0.000 0.560 0.240];
tripColor = [0.80 0.12 0.10];
blockColor = [0.00 0.45 0.22];
alarmColor = [0.88 0.45 0.05];

%% Generate stressed external-fault / inrush-like disturbance
eventStart = 0.035;
decay = exp(-(t - eventStart)/0.075).*(t >= eventStart);
satShape = max(sin(w0*(t - eventStart)), 0).^8;
hfBurst = sin(2*pi*850*(t - eventStart)).*exp(-(t - eventStart)/0.018).*(t >= eventStart);
remanence = 0.95*exp(-(t - eventStart)/0.10).*(t >= eventStart);
thermalNoiseSigma = 0.006;   % small broadband thermal noise floor, pu
targetSnrDb = 20;            % worst thesis noise case retained in Fig. 6.12/Table 6.12

id_stress_clean = zeros(3, numel(t));
for k = 1:3
    base = 0.13*sin(w0*t + ph(k)).*(t >= eventStart);
    h3 = 0.046*sin(3*w0*t + 3*ph(k) + 0.40).*(t >= eventStart);
    h5 = 0.017*sin(5*w0*t + 5*ph(k) - 0.25).*(t >= eventStart);
    ctOffset = 0.11*remanence*cos(ph(k));
    satSpikes = 0.78*satShape.*decay.*sign(cos(w0*t + ph(k)));
    id_stress_clean(k,:) = base + h3 + h5 + ctOffset + satSpikes + 0.07*hfBurst*cos(ph(k));
end

id_stress_noisy = addThermalAndAwgn(id_stress_clean, thermalNoiseSigma, targetSnrDb);

%% Generate internal fault retained as dependable trip after model integration
internalStart = 0.045;
faultEnvelope = (1 - exp(-(t - internalStart)/0.006)).*(t >= internalStart);
travelingWave = sin(2*pi*1800*(t - internalStart)).*exp(-(t - internalStart)/0.035).*(t >= internalStart);
id_internal_clean = zeros(3, numel(t));

for k = 1:3
    sustained = (3.15 + 0.35*k)*sin(w0*t + ph(k) - 0.20).*faultEnvelope;
    decayingDC = (1.20 - 0.15*k)*exp(-(t - internalStart)/0.060).*(t >= internalStart);
    harmonics = 0.40*sin(5*w0*t + 0.7*ph(k)).*faultEnvelope ...
        + 0.22*sin(7*w0*t - 0.4*ph(k)).*faultEnvelope;
    id_internal_clean(k,:) = sustained + decayingDC + harmonics + 0.72*travelingWave*cos(ph(k));
end

id_internal_noisy = addThermalAndAwgn(id_internal_clean, thermalNoiseSigma, 30);

%% Thesis benchmark metrics
methods = {'Standalone 87T'; 'Optimized 87T'; 'Proposed Hybrid'};
accuracy = [95.83; 96.67; 100.00];
dependability = [96.25; 97.08; 100.00];
security = [95.63; 96.46; 100.00];
falseNeg = [18; 14; 0];
falsePos = [62; 51; 0];
timeMs = [0.1; 0.1; 12.1];

snrLevels = [Inf 60 50 40 30 20];
noiseOverallAccuracy = [99.27 99.27 99.17 99.06 98.65 97.08];

%% Plot figure
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [0.7 0.7 11.2 7.2]);
tl = tiledlayout(fig, 3, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

ax1 = nexttile(1);
plotWaveforms(ax1, t, id_stress_noisy, phaseColors, [-1.05 1.05]);
title(ax1, 'Before: conventional standalone 87T', 'FontName', 'Times New Roman', ...
    'FontWeight', 'bold', 'FontSize', 11);
subtitle(ax1, 'CT saturation + ±95% remanence + thermal noise + 20 dB SNR', ...
    'FontName', 'Times New Roman', 'FontSize', 9);
addDecisionBand(ax1, 0.060, 0.160, tripColor, 'TRIP', 'False trip during external/noisy transient');

ax2 = nexttile(2);
plotWaveforms(ax2, t, id_stress_noisy, phaseColors, [-1.05 1.05]);
title(ax2, 'After: hybrid adaptive 87T + DWT-LSTM supervisor', 'FontName', 'Times New Roman', ...
    'FontWeight', 'bold', 'FontSize', 11);
subtitle(ax2, 'Same disturbance: DWT-LSTM veto/security layer identifies non-internal event', ...
    'FontName', 'Times New Roman', 'FontSize', 9);
addDecisionBand(ax2, 0.060, 0.160, blockColor, 'BLOCK', 'False trip vetoed');

ax3 = nexttile(3);
plotWaveforms(ax3, t, id_internal_noisy, phaseColors, [-5.2 5.2]);
title(ax3, 'Internal fault: conventional 87T pickup', 'FontName', 'Times New Roman', ...
    'FontWeight', 'normal', 'FontSize', 10.5);
addDecisionBand(ax3, 0.055, 0.165, tripColor, 'TRIP', 'High differential current');

ax4 = nexttile(4);
plotWaveforms(ax4, t, id_internal_noisy, phaseColors, [-5.2 5.2]);
title(ax4, 'Internal fault: hybrid dependability retained', 'FontName', 'Times New Roman', ...
    'FontWeight', 'normal', 'FontSize', 10.5);
addDecisionBand(ax4, 0.055, 0.165, tripColor, 'TRIP', '87T and LSTM agree');

ax5 = nexttile(5);
plotNoiseRobustness(ax5, snrLevels, noiseOverallAccuracy, alarmColor);

ax6 = nexttile(6);
drawMetricTable(ax6, methods, accuracy, dependability, security, falseNeg, falsePos, timeMs);

xlabel(tl, 'Time (s)', 'FontName', 'Times New Roman', 'FontSize', 11);
ylabel(tl, 'Differential current (pu)', 'FontName', 'Times New Roman', 'FontSize', 11);

lgd = legend(ax1, {'Phase A', 'Phase B', 'Phase C'}, 'Orientation', 'horizontal', 'Box', 'off');
lgd.Layout.Tile = 'north';

annotation(fig, 'textbox', [0.08 0.008 0.86 0.04], 'String', ...
    'Benchmark values are thesis-reported results: standalone 87T vs optimized 87T vs proposed hybrid relay. Noise robustness uses clean-to-20 dB SNR stress cases.', ...
    'EdgeColor', 'none', 'HorizontalAlignment', 'center', ...
    'FontName', 'Times New Roman', 'FontSize', 8.5, 'Color', [0.20 0.20 0.20]);

%% Save outputs
outDir = fullfile(pwd, 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

pngPath = fullfile(outDir, 'before_after_87t_hybrid_comparison.png');
pdfPath = fullfile(outDir, 'before_after_87t_hybrid_comparison.pdf');
figPath = fullfile(outDir, 'before_after_87t_hybrid_comparison.fig');

exportgraphics(fig, pngPath, 'Resolution', 600);
exportgraphics(fig, pdfPath, 'ContentType', 'vector');
savefig(fig, figPath);

fprintf('Saved before/after comparison to:\n  %s\n  %s\n  %s\n', pngPath, pdfPath, figPath);

%% Local helpers
function yNoisy = addThermalAndAwgn(yClean, thermalSigma, snrDb)
    thermal = thermalSigma*randn(size(yClean));
    yThermal = yClean + thermal;
    signalPower = mean(yClean(:).^2);
    noisePower = signalPower/(10^(snrDb/10));
    awgnNoise = sqrt(noisePower)*randn(size(yClean));
    yNoisy = yThermal + awgnNoise;
end

function plotWaveforms(ax, t, y, phaseColors, yLimits)
    axes(ax);
    hold(ax, 'on');
    for ii = 1:3
        plot(ax, t, y(ii,:), 'LineWidth', 1.05, 'Color', phaseColors(ii,:));
    end
    hold(ax, 'off');
    grid(ax, 'on');
    box(ax, 'on');
    xlim(ax, [0 0.2]);
    ylim(ax, yLimits);
    xticks(ax, 0:0.05:0.2);
    set(ax, 'FontName', 'Times New Roman', 'FontSize', 9.5, ...
        'LineWidth', 0.75, 'GridAlpha', 0.25, 'MinorGridAlpha', 0.12);
end

function addDecisionBand(ax, x1, x2, color, decision, detail)
    yl = ylim(ax);
    y1 = yl(1) + 0.04*range(yl);
    y2 = yl(1) + 0.21*range(yl);
    patch(ax, [x1 x2 x2 x1], [y1 y1 y2 y2], color, ...
        'FaceAlpha', 0.13, 'EdgeColor', color, 'LineWidth', 0.8);
    text(ax, (x1+x2)/2, y1 + 0.62*(y2-y1), decision, ...
        'HorizontalAlignment', 'center', 'FontName', 'Times New Roman', ...
        'FontSize', 11, 'FontWeight', 'bold', 'Color', color);
    text(ax, (x1+x2)/2, y1 + 0.24*(y2-y1), detail, ...
        'HorizontalAlignment', 'center', 'FontName', 'Times New Roman', ...
        'FontSize', 8.5, 'Color', color);
end

function plotNoiseRobustness(ax, snrLevels, overallAcc, lineColor)
    snrPlot = snrLevels;
    snrPlot(isinf(snrPlot)) = 70;
    plot(ax, snrPlot, overallAcc, '-o', 'LineWidth', 1.25, ...
        'Color', lineColor, 'MarkerFaceColor', lineColor, 'MarkerSize', 4.5);
    grid(ax, 'on');
    box(ax, 'on');
    xlim(ax, [18 72]);
    ylim(ax, [96.5 100.1]);
    xticks(ax, [20 30 40 50 60 70]);
    xticklabels(ax, {'20', '30', '40', '50', '60', 'Clean'});
    xlabel(ax, 'SNR stress level (dB)', 'FontName', 'Times New Roman', 'FontSize', 9.5);
    ylabel(ax, 'Overall accuracy (%)', 'FontName', 'Times New Roman', 'FontSize', 9.5);
    title(ax, 'Noise robustness of proposed model', 'FontName', 'Times New Roman', ...
        'FontWeight', 'normal', 'FontSize', 10.5);
    text(ax, 20, 97.08, '  97.08% at 20 dB SNR', 'FontName', 'Times New Roman', ...
        'FontSize', 8.8, 'Color', lineColor, 'VerticalAlignment', 'bottom');
    set(ax, 'FontName', 'Times New Roman', 'FontSize', 9.5, ...
        'LineWidth', 0.75, 'GridAlpha', 0.25);
end

function drawMetricTable(ax, methods, accuracy, dependability, security, falseNeg, falsePos, timeMs)
    axis(ax, 'off');
    title(ax, 'Relay performance benchmark', 'FontName', 'Times New Roman', ...
        'FontWeight', 'normal', 'FontSize', 10.5);

    headers = {'Method', 'Acc.', 'Dep.', 'Sec.', 'FN', 'FP', 'Time'};
    rows = cell(numel(methods), numel(headers));
    for ii = 1:numel(methods)
        rows{ii,1} = methods{ii};
        rows{ii,2} = sprintf('%.2f%%', accuracy(ii));
        rows{ii,3} = sprintf('%.2f%%', dependability(ii));
        rows{ii,4} = sprintf('%.2f%%', security(ii));
        rows{ii,5} = sprintf('%d', falseNeg(ii));
        rows{ii,6} = sprintf('%d', falsePos(ii));
        rows{ii,7} = sprintf('%.1f ms', timeMs(ii));
    end

    x = [0.02 0.36 0.48 0.60 0.72 0.80 0.88];
    yTop = 0.82;
    rowH = 0.19;
    colW = [0.33 0.11 0.11 0.11 0.07 0.07 0.10];

    rectangle(ax, 'Position', [0.01 yTop-0.045 0.97 0.13], ...
        'FaceColor', [0.92 0.94 0.97], 'EdgeColor', [0.45 0.48 0.52]);
    for jj = 1:numel(headers)
        text(ax, x(jj), yTop+0.02, headers{jj}, 'FontName', 'Times New Roman', ...
            'FontSize', 8.8, 'FontWeight', 'bold', 'HorizontalAlignment', 'left');
    end

    for ii = 1:size(rows,1)
        y = yTop - ii*rowH;
        if ii == 3
            fillColor = [0.90 0.97 0.92];
        else
            fillColor = [1 1 1];
        end
        rectangle(ax, 'Position', [0.01 y-0.045 0.97 0.13], ...
            'FaceColor', fillColor, 'EdgeColor', [0.78 0.80 0.83]);
        for jj = 1:numel(headers)
            if jj == 1
                fontWeight = 'bold';
            else
                fontWeight = 'normal';
            end
            text(ax, x(jj), y+0.02, rows{ii,jj}, 'FontName', 'Times New Roman', ...
                'FontSize', 8.6, 'FontWeight', fontWeight, 'HorizontalAlignment', 'left');
        end
    end

    text(ax, 0.02, 0.08, 'Hybrid result: zero false negatives and zero false trips on thesis validation set.', ...
        'FontName', 'Times New Roman', 'FontSize', 8.8, 'Color', [0.00 0.35 0.18]);
    xlim(ax, [0 1]);
    ylim(ax, [0 1]);
end
