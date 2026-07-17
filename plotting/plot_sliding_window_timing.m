%% plot_sliding_window_timing.m
% Generates publication-grade Figure 5.4: Dual sliding-window timing:
% half-cycle DWT window and full-cycle LSTM buffer.

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 9.0 4.8]);
ax = axes(fig, 'FontName','Times New Roman','FontSize',11);
hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

% Draw continuous signal sine wave
t = 0:0.05:40; % ms
y = sin(2*pi*50*t/1000) + 0.15*sin(3*2*pi*50*t/1000);
plot(ax, t, y, 'Color', [0.6 0.6 0.6], 'LineWidth', 1.0);

% Highlight sliding windows at t = 25 ms
% Window 1: DWT (16 samples, 10 ms, e.g. from 15 to 25 ms)
fill_x1 = [15 25 25 15];
fill_y1 = [-1.3 -1.3 1.3 1.3];
fill(ax, fill_x1, fill_y1, [0.85 0.92 1.0], 'FaceAlpha', 0.5, 'EdgeColor', 'b', 'LineWidth', 1.5, 'LineStyle','--', 'DisplayName','DWT Sliding Window (16 samples, 10 ms)');

% Window 2: LSTM Buffer (32 steps, 20 ms, e.g. from 5 to 25 ms)
fill_x2 = [5 25 25 5];
fill_y2 = [-1.4 -1.4 1.4 1.4];
fill(ax, fill_x2, fill_y2, [1.0 0.95 0.85], 'FaceAlpha', 0.3, 'EdgeColor', [0.85 0.5 0.1], 'LineWidth', 1.5, 'DisplayName','LSTM Buffer (32 steps, 20 ms)');

% Annotate update cadence
% Draw tick marks every 0.625 ms around t = 25 ms
for step = 0:8
    x_tick = 25 - step * 0.625;
    line(ax, [x_tick x_tick], [-0.1 0.1], 'Color','r', 'LineWidth',1.2);
end
text(ax, 23.5, -0.4, {'Update Cadence', '\Delta t = 0.625 ms'}, 'FontName','Times New Roman','FontSize',9, 'Color','r', 'HorizontalAlignment','center');

% Annotate current time
xline(ax, 25, 'k-', 'LineWidth', 1.8);
text(ax, 25, 1.5, 'Current instant t_0', 'FontName','Times New Roman','FontSize',9.5, 'FontWeight','bold', 'HorizontalAlignment','center');

% Labels and Limits
xlabel('Time (ms)', 'FontName','Times New Roman','FontSize',12);
ylabel('Differential Current Wave (pu)', 'FontName','Times New Roman','FontSize',12);
xlim([0 35]);
ylim([-1.6 1.7]);

legend(ax, 'Location','southwest', 'FontSize',9.5);
title('Dual Sliding-Window Temporal Buffering Cadence', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'dual_sliding_window_timing.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
