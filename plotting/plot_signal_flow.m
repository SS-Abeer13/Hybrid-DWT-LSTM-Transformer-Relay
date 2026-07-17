%% plot_signal_flow.m
% Generates publication-grade Figure 5.3: End-to-end seven-stage signal flow
% of the proposed protection scheme.

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 12.5 3.5]);
ax = axes(fig);
hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
xlim(ax, [0 12.5]); ylim(ax, [0 3.5]);

fontName = 'Times New Roman';

%% Node definitions
% x, y, width, height, color, title, subtitle
nodes = {
    0.2, 0.9, 1.4, 1.7, [0.96 0.96 0.96], 'Stage 1: CT', {'CT secondary current', '3-phase sampling'};
    1.9, 0.9, 1.4, 1.7, [0.92 0.92 0.92], 'Stage 2: MU', {'IEC 61850-9-2', 'Conditioning & AWGN'};
    3.6, 0.9, 1.4, 1.7, [0.88 0.88 0.88], 'Stage 3: DWT', {'16-sample window', '6 energy features'};
    5.3, 0.9, 1.4, 1.7, [0.84 0.84 0.84], 'Stage 4: Buffer', {'32-step full-cycle', 'time-series buffer'};
    7.0, 0.9, 1.4, 1.7, [0.80 0.80 0.80], 'Stage 5: LSTM', {'Sigmoid confidence', 'classification'};
    8.7, 0.9, 1.4, 1.7, [0.76 0.76 0.76], 'Stage 6: Veto', {'Parallel 87T Restraint', 'AND handshake veto'};
    10.4, 0.9, 1.8, 1.7, [0.94 0.88 0.88], 'Stage 7: Breaker', {'Winding trip latch', 'Sub-cycle trip coil', '13.1 ms clearing time'}
};

%% Draw nodes
for i = 1:size(nodes, 1)
    x = nodes{i,1};
    y = nodes{i,2};
    w = nodes{i,3};
    h = nodes{i,4};
    col = nodes{i,5};
    lbl_title = nodes{i,6};
    lbl_sub = nodes{i,7};
    
    % Draw rounded rectangle
    rectangle(ax, 'Position', [x y w h], 'Curvature', [0.12 0.12], 'FaceColor', col, 'EdgeColor', [0.16 0.16 0.16], 'LineWidth', 1.5);
    
    % Draw Title
    text(ax, x + w/2, y + h - 0.3, lbl_title, 'FontName', fontName, 'FontSize', 9, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
    
    % Draw Subtitle
    text(ax, x + w/2, y + h/2 - 0.15, lbl_sub, 'FontName', fontName, 'FontSize', 7.5, 'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
end

%% Draw arrows
for i = 1:size(nodes, 1)-1
    x1 = nodes{i,1} + nodes{i,3};
    y1 = nodes{i,2} + nodes{i,4}/2;
    x2 = nodes{i+1,1};
    y2 = nodes{i+1,2} + nodes{i+1,4}/2;
    
    % Draw line
    line(ax, [x1+0.05 x2-0.05], [y1 y1], 'Color', [0.1 0.1 0.1], 'LineWidth', 1.5);
    % Draw arrow head
    plot(ax, x2-0.05, y1, 'k>', 'MarkerFaceColor', 'k', 'MarkerSize', 6);
end

% Title
title('End-to-End Seven-Stage Protective Signal-Flow Pipeline', 'FontName', fontName, 'FontSize', 13, 'FontWeight', 'bold');

% Save output
outPath = fullfile(pwd, 'figures', 'proposed_protection_signal_flow.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
