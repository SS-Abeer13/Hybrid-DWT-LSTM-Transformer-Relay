%% plot_flop_share.m
% Generates publication-grade Figure 5.7: Per-inference computational cost
% distribution across pipeline stages.

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 7.5 4.5]);
ax = axes(fig, 'FontName','Times New Roman','FontSize',11);
hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

% Data
stages = {'DWT Front End', 'LSTM Layer 1 (128)', 'LSTM Layer 2 (64)', 'Temporal Attention', 'Dense & Softmax'};
flops = [1350, 856064, 425984, 24576, 2116]; % actual multiply-accumulates/FLOPs
pct = flops / sum(flops) * 100;

% Create horizontal bar
bh = barh(ax, 1:5, pct, 0.65, 'FaceColor',[0.4 0.58 0.9], 'EdgeColor','none');

% Customize Y ticks
set(ax, 'YTick', 1:5, 'YTickLabel', stages, 'FontSize', 10);
xlabel('Computational Cost Share (%)', 'FontName','Times New Roman','FontSize',12);
ylabel('Pipeline Stage', 'FontName','Times New Roman','FontSize',12);
xlim([0 100]);

% Add numerical labels to bars
for i = 1:5
    text(ax, pct(i) + 1.5, i, sprintf('%.2f%%  (%s FLOPs)', pct(i), format_flops(flops(i))), ...
         'FontName','Times New Roman','FontSize',9.5, 'VerticalAlignment','middle');
end

title('Per-Inference Computational Complexity Budget Share', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'computational_cost_distribution.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);

function str = format_flops(f)
    if f < 1000
        str = sprintf('%d', f);
    elseif f < 1000000
        str = sprintf('%.1f k', f/1000);
    else
        str = sprintf('%.2f M', f/1000000);
    end
end
