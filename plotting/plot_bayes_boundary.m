%% plot_bayes_boundary.m
% Generates publication-grade Figure 3.4: Conceptual feature-space separation
% of the four event classes with cost-asymmetric decision boundaries.

clear; close all; clc;
rng(42, 'twister'); % Seed for identical clusters

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 7.5 5.5]);
ax = axes(fig, 'FontName','Times New Roman','FontSize',11);
hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

% Generate Synthetic Clusters representing Wavelet approximation/detail energy (log pu^2)
N_pts = 120;

% Normal: near zero (very low energy)
normal_x = -6.0 + 0.3 * randn(N_pts, 1);
normal_y = -6.0 + 0.3 * randn(N_pts, 1);

% Inrush: high approximation, low detail
inrush_x = -2.8 + 0.4 * randn(N_pts, 1);
inrush_y = -5.2 + 0.4 * randn(N_pts, 1);

% External: medium approximation, medium detail
external_x = -3.2 + 0.45 * randn(N_pts, 1);
external_y = -4.0 + 0.45 * randn(N_pts, 1);

% Internal: high detail, high approximation
internal_x = -1.8 + 0.5 * randn(N_pts, 1);
internal_y = -2.2 + 0.5 * randn(N_pts, 1);

% Plot Clusters
h_norm = scatter(normal_x, normal_y, 25, [0.4 0.78 0.4], 'filled', 'DisplayName', 'Normal Steady-State');
h_inru = scatter(inrush_x, inrush_y, 25, [0.98 0.72 0.2], 'filled', 'DisplayName', 'Magnetizing Inrush');
h_ext  = scatter(external_x, external_y, 25, [0.3 0.58 0.9], 'filled', 'DisplayName', 'External Fault (CT Saturation)');
h_int  = scatter(internal_x, internal_y, 25, [0.9 0.3 0.3], 'filled', 'DisplayName', 'Internal Winding Fault');

% Draw Cost-Symmetric (Standard Bayes) Boundary
x_bound = -5.0:0.1:0.0;
y_standard = -3.5 + 0.5 * (x_bound + 3.0);
h_std = plot(x_bound, y_standard, 'k--', 'LineWidth', 1.2, 'DisplayName', 'Standard Bayes Boundary (Symmetric Cost)');

% Draw Dependability-Biased (Cost-Asymmetric) shifted Boundary
% The boundary is shifted downwards to expand the Internal Fault (Trip) region,
% ensuring that no internal fault is missed (zero false negatives / 100% dependability!).
y_biased = -4.2 + 0.5 * (x_bound + 3.0);
h_bias = plot(x_bound, y_biased, 'r-', 'LineWidth', 2.0, 'DisplayName', 'Dependability-Biased Boundary (\lambda_{FN} \gg \lambda_{FP})');

% Annotate shift
annotation('arrow', [0.48 0.52], [0.55 0.43], 'Color', 'r', 'LineWidth', 1.5);
text(-3.4, -3.85, 'Dependability-Biased Shift', 'FontName','Times New Roman','FontSize',9.5, 'Color','r', 'FontWeight','bold', 'Rotation', 21);

% Region Text Labels
text(-5.0, -5.5, 'Normal', 'FontName','Times New Roman','FontSize',10.5, 'FontWeight','bold', 'Color',[0.2 0.5 0.2]);
text(-1.5, -4.5, 'Inrush', 'FontName','Times New Roman','FontSize',10.5, 'FontWeight','bold', 'Color',[0.7 0.4 0.1]);
text(-4.2, -3.2, 'External Fault', 'FontName','Times New Roman','FontSize',10.5, 'FontWeight','bold', 'Color',[0.1 0.3 0.6]);
text(-1.5, -1.8, {'Internal Fault', '(Expanded Trip Zone)'}, 'FontName','Times New Roman','FontSize',11, 'FontWeight','bold', 'Color',[0.7 0.1 0.1], 'HorizontalAlignment','center');

% Labels and Limits
xlabel('Approximation-Energy Feature log_{10}(E_A)  (pu^2)', 'FontName','Times New Roman','FontSize',12);
ylabel('Detail-Energy Feature log_{10}(E_D)  (pu^2)', 'FontName','Times New Roman','FontSize',12);
xlim([-7.0 0.0]);
ylim([-7.0 0.0]);

legend([h_norm, h_inru, h_ext, h_int, h_std, h_bias], 'Location', 'northwest', 'FontSize', 8.5, 'Interpreter', 'none');
title('Conceptual 2D Feature-Space separation & Decision Boundaries', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'bayes_decision_boundary.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);
