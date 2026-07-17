%% plot_ablation_tornado.m
% Generates publication-grade Figure 6.9: Ablation sensitivity of
% classification accuracy to individual design choices.

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 8.2 4.8]);
ax = axes(fig, 'FontName','Times New Roman','FontSize',11);
hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

% Data
configs = {
    'Full Model (Proposed)',
    'Without Attention Layer',
    'Single LSTM Layer (64 units)',
    'Detail-Energy Features Only',
    'Approximation-Energy Only',
    'Without Normalisation',
    '2-Level DWT',
    '4-Level DWT'
};
delta_acc = [0.00, -0.71, -1.34, -0.44, -8.03, -2.87, -0.56, -0.87];

% Reverse arrays for plotting from top to bottom
configs = flip(configs);
delta_acc = flip(delta_acc);

% Horizontal bar chart
bh = barh(ax, 1:numel(configs), delta_acc, 0.6, 'FaceColor','flat', 'EdgeColor','none');

% Color negative bars red and baseline/full model blue
CData = zeros(numel(configs), 3);
for i = 1:numel(configs)
    if delta_acc(i) == 0.0
        CData(i,:) = [0.20 0.55 0.90]; % Baseline blue
    else
        CData(i,:) = [0.85 0.30 0.30]; % Negative red
    end
end
bh.CData = CData;

% Customize axes
set(ax, 'YTick', 1:numel(configs), 'YTickLabel', configs, 'FontSize', 9.5);
xlabel('Accuracy Change \Delta Acc. (percentage points)', 'FontName','Times New Roman','FontSize',12);
ylabel('Ablated Configuration', 'FontName','Times New Roman','FontSize',12);
xlim([-9.5 1.0]);

% Add numerical labels to bars
for i = 1:numel(configs)
    if delta_acc(i) == 0.0
        text(ax, 0.2, i, 'Baseline (99.27%)', 'FontName','Times New Roman','FontSize',9.5, 'FontWeight','bold', 'Color',[0.20 0.40 0.70]);
    else
        text(ax, delta_acc(i) - 0.75, i, sprintf('%.2f pp', delta_acc(i)), ...
             'FontName','Times New Roman','FontSize',9.5, 'HorizontalAlignment','center', 'VerticalAlignment','middle');
    end
end

title('Ablation Sensitivity: Impact of Architectural Choices', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'ablation_sensitivity_tornado.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
