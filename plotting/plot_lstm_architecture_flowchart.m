%% Horizontal LSTM network architecture flowchart
% Thesis-ready diagram for the DWT-LSTM classifier architecture.

clear; close all; clc;

%% Figure setup
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [0.5 0.5 13.2 3.8]);
ax = axes(fig);
hold(ax, 'on');
axis(ax, 'off');
xlim(ax, [0 13.2]);
ylim(ax, [0 3.8]);

fontName = 'Times New Roman';

%% Grayscale colors
cInput = [0.96 0.96 0.96];
cLstm = [0.90 0.90 0.90];
cDrop = [0.84 0.84 0.84];
cAttn = [0.78 0.78 0.78];
cDense = [0.88 0.88 0.88];
cOut = [0.82 0.82 0.82];
cBorder = [0.16 0.16 0.16];
cArrow = [0.10 0.10 0.10];

%% Node definitions
nodes = {
    0.25, 1.55, 1.10, 0.82, cInput, 'Input', '[B, 32, 6]';
    1.70, 1.45, 1.25, 1.02, cLstm, 'LSTM 1', '128 units\newlinereturn sequences';
    3.28, 1.55, 1.05, 0.82, cDrop, 'Dropout', 'p = 0.3';
    4.68, 1.45, 1.25, 1.02, cLstm, 'LSTM 2', '64 units\newlinereturn sequences';
    6.26, 1.55, 1.05, 0.82, cDrop, 'Dropout', 'p = 0.3';
    7.66, 1.35, 1.52, 1.22, cAttn, 'Global Temporal\newlineAttention', 'weighted sum\newlineacross 32 steps';
    9.58, 1.55, 1.12, 0.82, cDense, 'Dense', '32 units, ReLU';
    11.08, 1.55, 1.22, 0.82, cOut, 'Output', '4 units, softmax';
};

%% Draw nodes and arrows
for i = 1:size(nodes, 1)
    drawNode(ax, nodes{i,1}, nodes{i,2}, nodes{i,3}, nodes{i,4}, ...
        nodes{i,5}, nodes{i,6}, nodes{i,7}, fontName, cBorder);
end

for i = 1:size(nodes, 1)-1
    x1 = nodes{i,1} + nodes{i,3};
    y1 = nodes{i,2} + nodes{i,4}/2;
    x2 = nodes{i+1,1};
    y2 = nodes{i+1,2} + nodes{i+1,4}/2;
    drawArrow(ax, x1 + 0.08, y1, x2 - 0.08, y2, cArrow);
end

%% Title and parameter count
text(ax, 6.6, 3.35, 'LSTM Network Architecture for Transformer Differential Protection', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, ...
    'FontWeight', 'bold', 'FontSize', 15, 'Color', [0.08 0.08 0.08]);

text(ax, 6.6, 0.72, 'Total trainable parameters: 125,476', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, ...
    'FontWeight', 'bold', 'FontSize', 12, 'Color', [0.12 0.12 0.12]);

text(ax, 6.6, 0.38, ...
    'Sequence length = 32 time steps; feature vector = 6 DWT energy features per step', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, ...
    'FontSize', 10, 'Color', [0.30 0.30 0.30]);

%% Save outputs
outDir = fullfile(pwd, 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

pngPath = fullfile(outDir, 'lstm_network_architecture_flowchart.png');
pdfPath = fullfile(outDir, 'lstm_network_architecture_flowchart.pdf');
figPath = fullfile(outDir, 'lstm_network_architecture_flowchart.fig');

exportgraphics(fig, pngPath, 'Resolution', 600);
exportgraphics(fig, pdfPath, 'ContentType', 'vector');
savefig(fig, figPath);

fprintf('Saved LSTM architecture flowchart to:\n  %s\n  %s\n  %s\n', pngPath, pdfPath, figPath);

%% Local helpers
function drawNode(ax, x, y, w, h, faceColor, titleText, bodyText, fontName, borderColor)
    rectangle(ax, 'Position', [x y w h], 'Curvature', 0.08, ...
        'FaceColor', faceColor, 'EdgeColor', borderColor, 'LineWidth', 1.15);
    text(ax, x + w/2, y + h*0.63, titleText, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'FontName', fontName, 'FontWeight', 'bold', 'FontSize', 10.5, ...
        'Color', [0.08 0.08 0.08], 'Interpreter', 'tex');
    text(ax, x + w/2, y + h*0.32, bodyText, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'FontName', fontName, 'FontSize', 9.3, ...
        'Color', [0.18 0.18 0.18], 'Interpreter', 'tex');
end

function drawArrow(ax, x1, y1, x2, y2, color)
    annotation(ax.Parent, 'arrow', ...
        xDataToNorm(ax, [x1 x2]), yDataToNorm(ax, [y1 y2]), ...
        'Color', color, 'LineWidth', 1.15, 'HeadLength', 7, 'HeadWidth', 7);
end

function xn = xDataToNorm(ax, x)
    axPos = ax.Position;
    xLim = ax.XLim;
    xn = axPos(1) + (x - xLim(1))/(xLim(2) - xLim(1))*axPos(3);
end

function yn = yDataToNorm(ax, y)
    axPos = ax.Position;
    yLim = ax.YLim;
    yn = axPos(2) + (y - yLim(1))/(yLim(2) - yLim(1))*axPos(4);
end
