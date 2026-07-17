%% plot_percentage_restraint_slope.m
% Generates publication-grade Figure 3.1: Dual-Slope Percentage Restraint
% operate/restrain characteristic of the differential relay.

clear; close all; clc;

% Figure setup (Times New Roman, single column width)
fig = figure('Color','w','Units','inches','Position',[1 1 7.0 5.2]);
ax = axes(fig, 'FontName','Times New Roman','FontSize',11);
hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

% Parameters
I_pickup = 0.30;  % Minimum pickup current (A)
I_knee1  = 3.0;   % First knee point (A)
S1       = 0.25;  % Slope 1 (25%)
S2       = 0.60;  % Slope 2 (60%)

% Compute Operating Boundary
Ir = 0:0.01:6.5;
Id_thresh = zeros(size(Ir));

for i = 1:numel(Ir)
    if Ir(i) < I_pickup
        Id_thresh(i) = I_pickup;
    elseif Ir(i) < I_knee1
        Id_thresh(i) = I_pickup + S1 * (Ir(i) - I_pickup);
    else
        Id_thresh(i) = I_pickup + S1 * (I_knee1 - I_pickup) + S2 * (Ir(i) - I_knee1);
    end
end

% Shading regions
fill_x = [0, Ir, 6.5, 0];
fill_y = [7.0, Id_thresh, 7.0, 7.0];
h_op = fill(fill_x, fill_y, [1.0 0.92 0.92], 'EdgeColor','none', 'DisplayName','Operate Region (Trip)');

fill_x2 = [0, Ir, 6.5, 6.5, 0];
fill_y2 = [0, Id_thresh, Id_thresh(end), 0, 0];
h_rest = fill(fill_x2, fill_y2, [0.92 0.98 0.92], 'EdgeColor','none', 'DisplayName','Restrain Region (Block)');

% Plot Boundary Line
h_bound = plot(Ir, Id_thresh, 'k-', 'LineWidth', 2.0, 'DisplayName','Operating Boundary');

% Plot Knee Points and settings
plot(I_pickup, I_pickup, 'ko', 'MarkerFaceColor','k', 'MarkerSize',6);
plot(I_knee1, Id_thresh(Ir == I_knee1), 'ko', 'MarkerFaceColor','k', 'MarkerSize',6);

% Annotate settings
text(I_pickup + 0.1, I_pickup - 0.1, 'I_{pickup} = 0.30 A', 'FontName','Times New Roman','FontSize',9.5);
text(I_knee1 - 0.6, Id_thresh(Ir == I_knee1) + 0.25, {'Knee Point', '(I_{rest} = 3.0 A)'}, ...
     'FontName','Times New Roman','FontSize',9.5, 'HorizontalAlignment','center');

% Slopes
text(1.1, 0.55, 'Slope 1 = 25%', 'FontName','Times New Roman','FontSize',10, 'Rotation',13);
text(4.2, 1.65, 'Slope 2 = 60%', 'FontName','Times New Roman','FontSize',10, 'Rotation',31);

% Region Text Labels
text(2.0, 4.0, {'OPERATE REGION', '(Internal Faults)'}, 'FontName','Times New Roman','FontSize',12, ...
     'FontWeight','bold','Color',[0.6 0.1 0.1], 'HorizontalAlignment','center');
text(4.0, 0.6, {'RESTRAIN REGION', '(Normal Load / External Through-Faults)'}, 'FontName','Times New Roman','FontSize',11, ...
     'FontWeight','bold','Color',[0.1 0.5 0.1], 'HorizontalAlignment','center');

% Labels and Limits
xlabel('Restraint Current I_r = (|I_{HV}| + |I_{LV}|)/2  (A)', 'FontName','Times New Roman','FontSize',12);
ylabel('Differential Current I_d = |I_{HV} + I_{LV}|  (A)', 'FontName','Times New Roman','FontSize',12);
xlim([0 6.0]);
ylim([0 5.0]);

% Title
title('Dual-Slope Percentage Restraint Operating Characteristic', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'restraint_slope_characteristic.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
