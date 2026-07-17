%% plot_ct_saturation.m
% Generates publication-grade Figure 3.3: Current transformer equivalent
% circuit and saturation-induced secondary distortion.

clear; close all; clc;

% Figure setup (Times New Roman, wide position)
fig = figure('Color','w','Units','inches','Position',[1 1 11.5 5.0]);

%% Subplot 1: Schematic of CT Equivalent Circuit (drawn with vector blocks)
ax1 = subplot(1,2,1);
hold(ax1, 'on'); axis(ax1, 'equal'); axis(ax1, 'off');
xlim(ax1, [0 10]); ylim(ax1, [0 6]);

% Draw Primary Source Path
line(ax1, [0 1.5], [4.5 4.5], 'Color','k', 'LineWidth', 1.8);
line(ax1, [1.5 2.5], [4.5 4.5], 'Color','k', 'LineWidth', 1.8);
% Primary Source Winding Symbol (little loops or rectangle)
rectangle(ax1, 'Position', [2.0 4.1 1.0 0.8], 'FaceColor', [0.95 0.95 0.95], 'EdgeColor', 'k', 'LineWidth', 1.5);
text(ax1, 2.5, 4.5, 'N_p', 'FontName','Times New Roman','FontSize',10, 'HorizontalAlignment','center');

% Secondary Winding (parallel to primary)
rectangle(ax1, 'Position', [4.0 4.1 1.0 0.8], 'FaceColor', [0.95 0.95 0.95], 'EdgeColor', 'k', 'LineWidth', 1.5);
text(ax1, 4.5, 4.5, 'N_s', 'FontName','Times New Roman','FontSize',10, 'HorizontalAlignment','center');

% Core dashed lines (coupling)
line(ax1, [3.4 3.4], [3.8 5.2], 'Color',[0.5 0.5 0.5], 'LineWidth', 1.5, 'LineStyle','--');
line(ax1, [3.6 3.6], [3.8 5.2], 'Color',[0.5 0.5 0.5], 'LineWidth', 1.5, 'LineStyle','--');

% Secondary resistance & leakage branch
rectangle(ax1, 'Position', [5.8 4.2 1.2 0.6], 'FaceColor', [0.9 0.9 0.9], 'EdgeColor', 'k', 'LineWidth', 1.5);
text(ax1, 6.4, 4.5, 'R_s + jX_s', 'FontName','Times New Roman','FontSize',9, 'HorizontalAlignment','center');

% Magnetizing Branch (downwards)
line(ax1, [5.3 5.3], [4.5 3.3], 'Color','k', 'LineWidth', 1.5);
rectangle(ax1, 'Position', [4.8 2.3 1.0 1.0], 'FaceColor', [0.95 0.92 0.92], 'EdgeColor', 'r', 'LineWidth', 1.5);
text(ax1, 5.3, 2.8, {'Nonlinear', 'Z_m (B-H)'}, 'FontName','Times New Roman','FontSize',8.5, 'Color','r', 'HorizontalAlignment','center');
line(ax1, [5.3 5.3], [2.3 1.5], 'Color','k', 'LineWidth', 1.5);

% Burden Branch (downwards at the end)
line(ax1, [7.8 7.8], [4.5 3.3], 'Color','k', 'LineWidth', 1.5);
rectangle(ax1, 'Position', [7.3 2.3 1.0 1.0], 'FaceColor', [0.92 0.95 0.98], 'EdgeColor', 'b', 'LineWidth', 1.5);
text(ax1, 7.8, 2.8, {'Burden', 'Z_b'}, 'FontName','Times New Roman','FontSize',9, 'Color','b', 'HorizontalAlignment','center');
line(ax1, [7.8 7.8], [2.3 1.5], 'Color','k', 'LineWidth', 1.5);

% Bottom connection wire
line(ax1, [4.5 7.8], [1.5 1.5], 'Color','k', 'LineWidth', 1.5);
line(ax1, [4.5 4.5], [1.5 4.1], 'Color','k', 'LineWidth', 1.5);

% Connect top wire
line(ax1, [5.0 5.8], [4.5 4.5], 'Color','k', 'LineWidth', 1.5);
line(ax1, [7.0 7.8], [4.5 4.5], 'Color','k', 'LineWidth', 1.5);

% Current arrows
text(ax1, 1.0, 4.9, 'i_{primary} (I_p)', 'FontName','Times New Roman','FontSize',9.5, 'Color','k');
text(ax1, 5.6, 2.8, 'i_m', 'FontName','Times New Roman','FontSize',9.5, 'Color','r');
text(ax1, 8.2, 4.8, 'i_{secondary} (I_s)', 'FontName','Times New Roman','FontSize',9.5, 'Color','b');

title(ax1, '(a) CT Equivalent Electrical Circuit', 'FontName','Times New Roman','FontSize',12,'FontWeight','bold');

%% Subplot 2: Saturation Secondary Waveforms
ax2 = subplot(1,2,2);
hold(ax2, 'on'); grid(ax2, 'on'); box(ax2, 'on');
set(ax2, 'FontName','Times New Roman','FontSize',11);

% Time Base (50Hz)
t = 0:0.0001:0.06;
w = 2*pi*50;

% Primary current with decaying DC offset: I_p = sin(wt) + 1.2*exp(-t/0.02)
i_primary = 2.5 * sin(w*t) + 3.0 * exp(-t/0.018);

% Secondary Current with saturation clipping: when integral of voltage (flux) exceeds threshold
flux = zeros(size(t));
i_sec = zeros(size(t));
flux_limit = 0.006;
f = 0;

for k = 1:numel(t)
    f = f + i_primary(k) * 0.0001; % simple integration
    flux(k) = f;
    
    % Saturated clipping
    if f > flux_limit
        i_sec(k) = 0.1 * i_primary(k); % severely clipped secondary current
    elseif f < -flux_limit
        i_sec(k) = 0.1 * i_primary(k);
    else
        i_sec(k) = i_primary(k); % linear secondary current
    end
end

% Plot Primary vs Distorted Secondary
plot(ax2, t*1000, i_primary, 'k--', 'LineWidth', 1.2, 'DisplayName','Ideal Secondary I_p / CTR');
plot(ax2, t*1000, i_sec, 'b-', 'LineWidth', 1.8, 'DisplayName','Saturated Secondary I_s');

% Annotate saturation
text(ax2, 11, 0.4, {'Severe Saturation', 'Clipping'}, 'FontName','Times New Roman','FontSize',9.5, 'Color','b', 'HorizontalAlignment','center');
text(ax2, 28, 4.0, {'DC Offset', 'Saturation Winding'}, 'FontName','Times New Roman','FontSize',9.5, 'Color','k');

legend(ax2, 'Location','northeast', 'FontSize',9.5);
xlabel(ax2, 'Time (ms)', 'FontName','Times New Roman','FontSize',12);
ylabel(ax2, 'Current (pu)', 'FontName','Times New Roman','FontSize',12);
xlim(ax2, [0 60]);
ylim(ax2, [-3.5 6.0]);
title(ax2, '(b) CT Secondary Current Distortion', 'FontName','Times New Roman','FontSize',12,'FontWeight','bold');

% Main Title
sgtitle(fig, 'CT Equivalent Circuit Model & Saturation Waveforms', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'ct_saturation_characteristic.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
