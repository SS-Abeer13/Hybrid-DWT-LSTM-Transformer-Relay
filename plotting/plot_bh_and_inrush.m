%% plot_bh_and_inrush.m
% Generates publication-grade Figure 3.2: Core B-H saturation curve
% alongside the resulting magnetizing inrush current waveform.

clear; close all; clc;

% Figure setup (Times New Roman, wide position)
fig = figure('Color','w','Units','inches','Position',[1 1 11.5 5.0]);

%% Subplot 1: B-H Curve
ax1 = subplot(1,2,1);
hold(ax1, 'on'); grid(ax1, 'on'); box(ax1, 'on');
set(ax1, 'FontName','Times New Roman','FontSize',11);

% Simulated B-H data using arctan/tanh modeling
H = -100:0.1:100;
B = 1.6 * tanh(H/15) + 0.002 * H;

% Draw curve
plot(ax1, H, B, 'k-', 'LineWidth', 2.0);

% Highlight regions
% Knee Point
plot(ax1, 20, B(H == 20), 'ko', 'MarkerFaceColor','k', 'MarkerSize', 6);
text(ax1, 20, B(H == 20) + 0.15, 'Knee Point', 'FontName','Times New Roman','FontSize',9.5, 'HorizontalAlignment','center');

% Linear region
x_lin = [-15 15];
y_lin = 1.6*tanh(x_lin/15) + 0.002*x_lin;
plot(ax1, x_lin, y_lin, 'b--', 'LineWidth', 1.0);
text(ax1, -12, -0.6, 'Linear Region', 'FontName','Times New Roman','FontSize',9.5, 'Color','b');

% Saturation region
text(ax1, 60, 1.45, {'Saturation Region', '(d\phi/di \rightarrow 0)'}, 'FontName','Times New Roman','FontSize',9.5, 'Color',[0.5 0.1 0.1], 'HorizontalAlignment','center');

% Labels and Limits
xlabel(ax1, 'Magnetic Field Intensity H (A-turns/m)', 'FontName','Times New Roman','FontSize',12);
ylabel(ax1, 'Magnetic Flux Density B (T)', 'FontName','Times New Roman','FontSize',12);
xlim(ax1, [-80 80]);
ylim(ax1, [-2.0 2.0]);
title(ax1, '(a) Core B-H Magnetization Curve', 'FontName','Times New Roman','FontSize',12,'FontWeight','bold');

%% Subplot 2: Asymmetric Inrush Waveform
ax2 = subplot(1,2,2);
hold(ax2, 'on'); grid(ax2, 'on'); box(ax2, 'on');
set(ax2, 'FontName','Times New Roman','FontSize',11);

% Time base (2.5 cycles of 50Hz)
t = 0:0.0001:0.05;
w = 2*pi*50;

% Asymmetric inrush current wave equation: rich in 2nd harmonics
i_inrush = 6.0 * (sin(w*t - pi/2) + exp(-t/0.015)) .* (sin(w*t - pi/2) + exp(-t/0.015) > 0.1);

% Plot inrush
plot(ax2, t*1000, i_inrush, 'k-', 'LineWidth', 1.8);

% Highlight 2nd harmonic and dead-angles
plot(ax2, [10 20], [0 0], 'r-', 'LineWidth', 3.0);
text(ax2, 15, 0.4, 'Dead-Angle Block', 'FontName','Times New Roman','FontSize',9.5, 'Color','r', 'HorizontalAlignment','center');
text(ax2, 28, 4.0, {'High Peak', '(Unidirectional offset)'}, 'FontName','Times New Roman','FontSize',9.5, 'Color',[0.6 0.1 0.1], 'HorizontalAlignment','center');

% Labels and Limits
xlabel(ax2, 'Time (ms)', 'FontName','Times New Roman','FontSize',12);
ylabel(ax2, 'Inrush Current i(t)  (pu)', 'FontName','Times New Roman','FontSize',12);
xlim(ax2, [0 50]);
ylim(ax2, [-1.0 7.0]);
title(ax2, '(b) Asymmetric Magnetizing Inrush Waveform', 'FontName','Times New Roman','FontSize',12,'FontWeight','bold');

% Main Title
sgtitle(fig, 'Nonlinear Magnetization & Inrush Waveform Generation', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'bh_and_inrush_characteristic.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
