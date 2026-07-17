%% Dual-Panel Results Figure: Confusion Matrix & Clearing Time
% Generates a Q1-journal quality horizontal figure.
% Left: 4x4 Perfect Confusion Matrix
% Right: Clearing Time Comparison Bar Chart

clear; close all; clc;

%% 1. Figure Setup
fontName = 'Times New Roman';
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [1, 1, 12, 5]);

% Custom professional colors (IEEE standard aesthetic)
colorDarkBlue  = [0.05, 0.25, 0.50];
colorMedBlue   = [0.20, 0.45, 0.70];
colorLightBlue = [0.85, 0.90, 0.95];
colorGray      = [0.60, 0.60, 0.60];
colorRed       = [0.75, 0.15, 0.15];

%% =========================================================================
%% PANEL (A): 4x4 HYBRID RELAY CONFUSION MATRIX
%% =========================================================================
ax1 = subplot(1, 2, 1);
hold(ax1, 'on');

% Define 4x4 perfect diagonal data (e.g., 500 total test samples)
cm_data = [125,   0,   0,   0; 
             0, 125,   0,   0; 
             0,   0, 125,   0; 
             0,   0,   0, 125];
         
classes = {'Normal', 'Inrush', 'Internal Fault', 'External Fault'};

% Create a custom blue colormap for the matrix
cmap = [linspace(1, colorMedBlue(1), 256)', ...
        linspace(1, colorMedBlue(2), 256)', ...
        linspace(1, colorMedBlue(3), 256)'];

% Plot the matrix
imagesc(ax1, cm_data);
colormap(ax1, cmap);
caxis(ax1, [0, 125]); % Scale to max value

% Format Matrix Axes
set(ax1, 'XTick', 1:4, 'XTickLabel', classes, 'XTickLabelRotation', 25, ...
         'YTick', 1:4, 'YTickLabel', classes, ...
         'FontName', fontName, 'FontSize', 11, 'TickLength', [0 0]);
     
xlabel(ax1, 'Predicted Class', 'FontWeight', 'bold', 'FontSize', 12, 'Margin', 5);
ylabel(ax1, 'True Class', 'FontWeight', 'bold', 'FontSize', 12, 'Margin', 5);
title(ax1, '(a) Hybrid Relay Confusion Matrix', 'FontWeight', 'bold', 'FontSize', 13);

% Add text overlay (Numbers and Percentages)
for i = 1:4
    for j = 1:4
        val = cm_data(i,j);
        if val > 0
            txt = sprintf('%d\n(100%%)', val);
            textColor = 'w'; % White text for dark blue diagonal
            fontWeight = 'bold';
        else
            txt = sprintf('%d\n(0%%)', val);
            textColor = [0.3 0.3 0.3]; % Dark gray for off-diagonal
            fontWeight = 'normal';
        end
        text(ax1, j, i, txt, 'HorizontalAlignment', 'center', ...
            'VerticalAlignment', 'middle', 'Color', textColor, ...
            'FontName', fontName, 'FontSize', 11, 'FontWeight', fontWeight);
    end
end

% Draw grid lines to separate boxes cleanly
for i = 0.5:1:4.5
    plot(ax1, [0.5 4.5], [i i], 'k-', 'LineWidth', 0.5, 'Color', [0.8 0.8 0.8]);
    plot(ax1, [i i], [0.5 4.5], 'k-', 'LineWidth', 0.5, 'Color', [0.8 0.8 0.8]);
end
axis(ax1, 'tight');
axis(ax1, 'ij'); % Ensure Y-axis reads top-to-bottom

%% =========================================================================
%% PANEL (B): CLEARING TIME COMPARISON BAR CHART
%% =========================================================================
ax2 = subplot(1, 2, 2);
hold(ax2, 'on');

% Define Data: [Conventional HR, Standalone LSTM, Proposed Hybrid]
models = {'Conventional HR', 'Standalone LSTM', 'Proposed Hybrid'};
clearing_times = [45.5, 28.0, 17.2]; % Times in milliseconds

% Create Bar Chart
b = bar(ax2, 1:3, clearing_times, 0.6);
b.FaceColor = 'flat';
b.CData(1,:) = colorGray;      % Conventional HR (Gray/Baseline)
b.CData(2,:) = colorMedBlue;   % Standalone LSTM (Mid Blue)
b.CData(3,:) = colorDarkBlue;  % Proposed Hybrid (Dark Blue/Focus)

% Format Bar Axes
set(ax2, 'XTick', 1:3, 'XTickLabel', models, ...
         'YGrid', 'on', 'GridColor', [0.8 0.8 0.8], 'GridLineStyle', '--', ...
         'FontName', fontName, 'FontSize', 11);
ylim(ax2, [0, 55]);
ylabel(ax2, 'Average Clearing Time (ms)', 'FontWeight', 'bold', 'FontSize', 12);
title(ax2, '(b) Fault Clearing Time Comparison', 'FontWeight', 'bold', 'FontSize', 13);

% Add data labels on top of bars
for i = 1:3
    text(ax2, i, clearing_times(i) + 1.5, sprintf('%.1f ms', clearing_times(i)), ...
        'HorizontalAlignment', 'center', 'FontName', fontName, ...
        'FontSize', 11, 'FontWeight', 'bold', 'Color', [0.2 0.2 0.2]);
end

% Add the "2.6x Speedup" Bracket/Annotation
y_bracket = 50; 
plot(ax2, [1, 1, 3, 3], [clearing_times(1)+3, y_bracket, y_bracket, clearing_times(3)+3], ...
    '-', 'Color', colorRed, 'LineWidth', 1.5);

% Speedup text
speedup_ratio = clearing_times(1) / clearing_times(3);
speedup_str = sprintf('\\bf{\\approx%.1f\\times Speedup}', speedup_ratio);
text(ax2, 2, y_bracket + 2, speedup_str, ...
    'HorizontalAlignment', 'center', 'FontName', fontName, ...
    'FontSize', 12, 'Color', colorRed, 'Interpreter', 'tex');

% Add a subtle threshold line for 1 cycle (20ms for 50Hz)
yline(ax2, 20, 'k:', 'LineWidth', 1.5, 'Alpha', 0.5);
text(ax2, 0.6, 21.5, '1 Cycle (20 ms)', 'FontName', fontName, 'FontSize', 10, 'Color', [0.3 0.3 0.3]);

%% =========================================================================
%% EXPORT GRAPHICS
%% =========================================================================
outDir = fullfile(pwd, 'Figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

pngPath = fullfile(outDir, 'Results_Confusion_ClearingTime.png');
pdfPath = fullfile(outDir, 'Results_Confusion_ClearingTime.pdf');
figPath = fullfile(outDir, 'Results_Confusion_ClearingTime.fig');

% High-res exports
exportgraphics(fig, pngPath, 'Resolution', 600, 'BackgroundColor', 'w');
exportgraphics(fig, pdfPath, 'ContentType', 'vector', 'BackgroundColor', 'w');
savefig(fig, figPath);

fprintf('Successfully generated and saved dual-panel results figure to:\\n  %s\\n', outDir);