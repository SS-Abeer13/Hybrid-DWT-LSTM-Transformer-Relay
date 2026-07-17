%% plot_twostep_architecture.m
% Generates publication-grade Figure 5.1: Two-step development and
% deployment architecture (MATLAB/Simulink <-> PyTorch <-> ONNX).

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 12.0 4.0]);
ax = axes(fig);
hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
xlim(ax, [0 12]); ylim(ax, [0 4]);

fontName = 'Times New Roman';

%% Node definitions
% x, y, width, height, color, title, subtitle
nodes = {
    0.2, 1.2, 2.0, 1.6, [0.94 0.94 0.94], 'Step 1a: Physical Modeling', {'MATLAB/Simulink', 'Transient power simulation', 'Data generation'};
    2.7, 1.2, 2.0, 1.6, [0.90 0.90 0.90], 'Step 1b: Signal Processing', {'DWT coefficient extraction', 'Wavelet energies', 'Z-score normalization'};
    5.2, 1.2, 2.0, 1.6, [0.86 0.86 0.86], 'Step 2a: LSTM Intelligence', {'PyTorch network training', 'Dropout & Attention pooling', 'Hyperparameter HPO'};
    7.7, 1.2, 2.0, 1.6, [0.82 0.82 0.82], 'Step 2b: Model Export', {'ONNX format (Opset 14)', 'Graph optimization', 'Compacted 56,898 params'};
    10.2, 1.2, 1.6, 1.6, [0.88 0.94 0.88], 'Step 3: Relaying', {'Simulink deployment', 'Predict block integration', '13.1 ms clearing time'}
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
    rectangle(ax, 'Position', [x y w h], 'Curvature', [0.15 0.15], 'FaceColor', col, 'EdgeColor', [0.16 0.16 0.16], 'LineWidth', 1.5);
    
    % Draw Title
    text(ax, x + w/2, y + h - 0.3, lbl_title, 'FontName', fontName, 'FontSize', 9.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
    
    % Draw Subtitle
    text(ax, x + w/2, y + h/2 - 0.15, lbl_sub, 'FontName', fontName, 'FontSize', 8, 'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
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
title('End-to-End Two-Step DWT-LSTM Development and Deployment Framework', 'FontName', fontName, 'FontSize', 13, 'FontWeight', 'bold');

% Save output
outPath = fullfile(pwd, 'figures', 'two_step_development_architecture.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
