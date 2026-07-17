%% plot_wavelet_filterbank.m
% Generates publication-grade Figure 5.5: db4 mother wavelet and the
% five-level dyadic filter-bank decomposition tree.

clear; close all; clc;

% Figure setup (Times New Roman, wider position to fit 5 levels)
fig = figure('Color','w','Units','inches','Position',[0.5 0.5 14 6.5]);

%% Subplot 1: db4 Scaling and Wavelet Functions
ax1 = subplot(1,2,1);
hold(ax1, 'on'); grid(ax1, 'on'); box(ax1, 'on');
set(ax1, 'FontName','Times New Roman','FontSize',11);

t_phi = linspace(0, 7, 500);
phi = sin(pi*t_phi/7) + 0.4*sin(2*pi*t_phi/7) - 0.2*sin(3*pi*t_phi/7) + 0.08*sin(4*pi*t_phi/7);
phi(t_phi < 0 | t_phi > 7) = 0;
phi = 1.35 * (phi - min(phi)) / (max(phi) - min(phi)) - 0.2;

t_psi = linspace(0, 7, 500);
psi = cos(pi*t_psi/3.5) - 0.85*sin(2*pi*t_psi/3.5) + 0.35*cos(3*pi*t_psi/3.5) - 0.15*sin(4*pi*t_psi/3.5);
psi(t_psi < 0 | t_psi > 7) = 0;
psi = 1.8 * psi / max(abs(psi));

plot(ax1, t_phi, phi, 'b-', 'LineWidth', 1.8, 'DisplayName','Scaling function \phi(t)');
plot(ax1, t_psi, psi, 'r-', 'LineWidth', 1.8, 'DisplayName','Wavelet function \psi(t)');

xlabel(ax1, 'Time t', 'FontName','Times New Roman','FontSize',12);
ylabel(ax1, 'Amplitude', 'FontName','Times New Roman','FontSize',12);
xlim(ax1, [0 7]);
ylim(ax1, [-1.5 1.5]);
legend(ax1, 'Location','northeast', 'FontSize',9.5);
title(ax1, '(a) db4 Scaling & Wavelet Functions', 'FontName','Times New Roman','FontSize',12,'FontWeight','bold');

% Add text table for features
strFeatures = {
    'Features Extracted per Level (x5)',
    'E: Wavelet energy \Sigma |cD_j[k]|^2',
    'H: Shannon entropy of normalised band',
    '\sigma: Standard deviation of coefficients',
    'M: Maximum amplitude (transient peak)',
    'MAD: Mean absolute deviation',
    'K: Kurtosis (heavy-tail detector)',
    'Sk: Skewness of band distribution',
    '',
    'Total: 7 stats \times 5 levels +',
    '2 inst. (I_{diff}, I_{rest}) = 37-dim/window'
};
text(ax1, 0.2, -1.0, strFeatures, 'FontName','Times New Roman', 'FontSize', 10, 'EdgeColor', 'k', 'BackgroundColor', 'w');

%% Subplot 2: Dyadic Filter-Bank Decomposition Tree (5 Levels)
ax2 = subplot(1,2,2);
hold(ax2, 'on'); axis(ax2, 'equal'); axis(ax2, 'off');
% Adjust x and y limits for 5 levels
xlim(ax2, [0 15]); ylim(ax2, [0 11]);

% Initial input
rectangle(ax2, 'Position', [0.0 9.1 1.2 0.8], 'FaceColor', [0.96 0.96 0.96], 'EdgeColor', 'k', 'LineWidth', 1.5);
text(ax2, 0.6, 9.5, 'Input x[n]', 'FontName','Times New Roman','FontSize',10, 'HorizontalAlignment','center');
line(ax2, [1.2 1.6], [9.5 9.5], 'Color','k', 'LineWidth', 1.5);

% We loop 5 levels
x_start = 1.6;
y_cur = 9.5;
y_drop = 1.8; % vertical drop for next lowpass

freq_bands = {
    '2500 - 5000 Hz',
    '1250 - 2500 Hz',
    '625 - 1250 Hz',
    '312 - 625 Hz',
    '156 - 312 Hz'
};

for lvl = 1:5
    % Vertical split
    y_hi = y_cur + 0.8;
    y_lo = y_cur - y_drop;
    line(ax2, [x_start x_start], [y_lo y_hi], 'Color','k', 'LineWidth', 1.5);
    line(ax2, [x_start x_start+0.4], [y_hi y_hi], 'Color','k', 'LineWidth', 1.5);
    line(ax2, [x_start x_start+0.4], [y_lo y_lo], 'Color','k', 'LineWidth', 1.5);
    
    % High-pass branch
    rectangle(ax2, 'Position', [x_start+0.4 y_hi-0.4 1.2 0.8], 'FaceColor', [0.92 0.92 0.92], 'EdgeColor', 'k', 'LineWidth', 1.5);
    text(ax2, x_start+1.0, y_hi, {'HPF', 'g[n]'}, 'FontName','Times New Roman','FontSize',8, 'HorizontalAlignment','center');
    line(ax2, [x_start+1.6 x_start+2.0], [y_hi y_hi], 'Color','k', 'LineWidth', 1.5);
    
    rectangle(ax2, 'Position', [x_start+2.0 y_hi-0.4 0.8 0.8], 'FaceColor', [0.85 0.95 0.85], 'EdgeColor', 'k', 'LineWidth', 1.5);
    text(ax2, x_start+2.4, y_hi, '\downarrow 2', 'FontName','Times New Roman','FontSize',11, 'HorizontalAlignment','center');
    line(ax2, [x_start+2.8 x_start+3.5], [y_hi y_hi], 'Color','k', 'LineWidth', 1.5);
    
    text(ax2, x_start+3.6, y_hi, sprintf('cD_%d[n]', lvl), 'FontName','Times New Roman','FontSize',10, 'FontWeight','bold', 'Color','r');
    text(ax2, x_start+3.6, y_hi-0.4, freq_bands{lvl}, 'FontName','Times New Roman','FontSize',9, 'Color',[0.3 0.3 0.3]);
    
    % Low-pass branch
    rectangle(ax2, 'Position', [x_start+0.4 y_lo-0.4 1.2 0.8], 'FaceColor', [0.92 0.92 0.92], 'EdgeColor', 'k', 'LineWidth', 1.5);
    text(ax2, x_start+1.0, y_lo, {'LPF', 'h[n]'}, 'FontName','Times New Roman','FontSize',8, 'HorizontalAlignment','center');
    line(ax2, [x_start+1.6 x_start+2.0], [y_lo y_lo], 'Color','k', 'LineWidth', 1.5);
    
    rectangle(ax2, 'Position', [x_start+2.0 y_lo-0.4 0.8 0.8], 'FaceColor', [0.85 0.95 0.85], 'EdgeColor', 'k', 'LineWidth', 1.5);
    text(ax2, x_start+2.4, y_lo, '\downarrow 2', 'FontName','Times New Roman','FontSize',11, 'HorizontalAlignment','center');
    
    if lvl == 5
        % Final approx output
        line(ax2, [x_start+2.8 x_start+3.5], [y_lo y_lo], 'Color','k', 'LineWidth', 1.5);
        text(ax2, x_start+3.6, y_lo, sprintf('cA_%d[n]', lvl), 'FontName','Times New Roman','FontSize',10, 'FontWeight','bold', 'Color','b');
        text(ax2, x_start+3.6, y_lo-0.4, '0 - 156 Hz', 'FontName','Times New Roman','FontSize',9, 'Color',[0.3 0.3 0.3]);
    else
        % Connect to next level
        line(ax2, [x_start+2.8 x_start+3.2], [y_lo y_lo], 'Color','k', 'LineWidth', 1.5);
        x_start = x_start + 3.2;
        y_cur = y_lo;
    end
end

% Base text info
strInfo = {
    'L = 5 decomposition',
    'Window: 20 ms',
    'fs = 10 kHz (200 pts)'
};
text(ax2, 0.5, 2.0, strInfo, 'FontName','Times New Roman', 'FontSize', 11, 'EdgeColor', 'k', 'BackgroundColor', 'w');

title(ax2, '(b) 5-Level Dyadic Filter Bank Decomposition Tree', 'FontName','Times New Roman','FontSize',12,'FontWeight','bold');

% Main Title
sgtitle(fig, 'db4 Wavelet Analysis & Dyadic Decomposition Scheme', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
if ~exist('figures', 'dir')
    mkdir('figures');
end
outPath = fullfile(pwd, 'figures', 'db4_wavelet_filterbank.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
