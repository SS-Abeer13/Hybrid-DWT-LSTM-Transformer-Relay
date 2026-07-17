%% Horizontal flowchart: Hybrid adaptive transformer differential protection
% Academic thesis-ready swimlane diagram based on the DWT-LSTM + deterministic
% supervision framework described in the thesis.

clear; close all; clc;

%% Canvas
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [0.35 0.35 16.2 8.3]);
ax = axes(fig, 'Position', [0.035 0.055 0.93 0.88]);
hold(ax, 'on');
axis(ax, 'off');
xlim(ax, [0 100]);
ylim(ax, [0 60]);

fontName = 'Times New Roman';

%% Academic grayscale palette
P.bg1 = [0.94 0.94 0.94];
P.bg2 = [0.90 0.90 0.90];
P.bg3 = [0.86 0.86 0.86];
P.bg4 = [0.82 0.82 0.82];
P.border = [0.16 0.16 0.16];
P.arrow = [0.10 0.10 0.10];
P.start = [0.96 0.96 0.96];
P.process = [0.98 0.98 0.98];
P.ai = [0.93 0.93 0.93];
P.security = [0.90 0.90 0.90];
P.decision = [0.88 0.88 0.88];
P.trip = [0.84 0.84 0.84];
P.block = [0.92 0.92 0.92];
P.latch = [0.86 0.86 0.86];

%% Phase swimlanes
drawGroup(ax, [1.0 45.0 75.5 12.0], 'Phase 1: Measurement & Signal Conditioning', P.bg1, P.border, fontName);
drawGroup(ax, [1.0 27.7 89.8 12.8], 'Phase 2: Proposed WT-Energy-LSTM Intelligence Framework', P.bg2, P.border, fontName);
drawGroup(ax, [1.0 13.6 49.2 11.4], 'Phase 3: Deterministic Hardwired Supervision', P.bg3, P.border, fontName);
drawGroup(ax, [52.0 7.2 45.8 17.8], 'Phase 4: Output Actuation & Latching', P.bg4, P.border, fontName);

%% Phase 1: measurement path
A = node(ax, 3.0, 48.3, 8.5, 4.9, P.start, 'START', 'Measurement', fontName, P.border, 'ellipse');
B = node(ax, 13.3, 48.3, 8.8, 4.9, P.process, 'CT Interface', 'Anti-aliasing', fontName, P.border, 'rect');
C = node(ax, 23.8, 48.3, 8.8, 4.9, P.process, 'ADC Sampling', 'Time sync', fontName, P.border, 'rect');
D = node(ax, 34.3, 48.3, 8.9, 4.9, P.process, 'Preprocessing', 'Digital filtering', fontName, P.border, 'rect');
E = node(ax, 44.9, 48.3, 9.8, 4.9, P.process, 'Vector Compensation', 'Ratio correction', fontName, P.border, 'rect');
F = node(ax, 56.5, 48.3, 8.8, 4.9, P.process, 'Differential Core', 'Idiff / Irest engine', fontName, P.border, 'rect');
G = node(ax, 67.0, 51.2, 7.9, 4.2, P.process, 'Compute Idiff', 'Idiff abc[n]', fontName, P.border, 'rect');
H = node(ax, 67.0, 45.8, 7.9, 4.2, P.process, 'Compute Irest', 'Irest[n]', fontName, P.border, 'rect');

arrow(ax, rightMid(A), leftMid(B), 'iHV abc, iLV abc', P.arrow, fontName);
arrow(ax, rightMid(B), leftMid(C), 'conditioned', P.arrow, fontName);
arrow(ax, rightMid(C), leftMid(D), 'sampled vectors', P.arrow, fontName);
arrow(ax, rightMid(D), leftMid(E), 'normalized', P.arrow, fontName);
arrow(ax, rightMid(E), leftMid(F), 'phase aligned', P.arrow, fontName);
drawSmoothArrowPath(ax, [rightMid(F); 66.0 50.75; 66.0 53.3; leftMid(G)], 'Idiff abc[n]', P.arrow, fontName);
drawSmoothArrowPath(ax, [rightMid(F); 66.0 50.75; 66.0 47.9; leftMid(H)], 'Irest[n]', P.arrow, fontName);

%% Phase 2: WT-energy-LSTM pipeline
W0 = node(ax, 3.8, 31.7, 8.8, 5.0, P.ai, 'Sliding Window', 'Moving data sequence', fontName, P.border, 'rect');
W1 = node(ax, 15.0, 31.7, 10.2, 5.0, P.ai, 'Discrete Wavelet Transform', 'db4 multi-level decomposition', fontName, P.border, 'rect');
W2 = node(ax, 27.6, 31.7, 9.6, 5.0, P.ai, 'Feature Refinery', 'Spectral energy extraction', fontName, P.border, 'rect');
W3 = node(ax, 39.5, 31.7, 9.7, 5.0, P.ai, 'Feature Sequence Builder', 'Xt = [B x T x F]', fontName, P.border, 'rect');
N1 = node(ax, 51.5, 31.7, 9.3, 5.0, P.ai, 'Stateful LSTM Core', 'Hidden-state progression', fontName, P.border, 'rect');
N2 = node(ax, 63.0, 31.7, 9.7, 5.0, P.ai, 'Dense / Score Output', 'Fault probability Yhat', fontName, P.border, 'rect');
J = node(ax, 75.2, 31.7, 10.0, 5.0, P.decision, 'Trip Decision', 'Latching logic', fontName, P.border, 'rect');

drawSmoothArrowPath(ax, [bottomMid(G); 70.95 42.2; 8.2 42.2; topMid(W0)], ...
    '3-phase Idiff waveforms', P.arrow, fontName);
arrow(ax, rightMid(W0), leftMid(W1), 'Idiff abc[w]', P.arrow, fontName);
arrow(ax, rightMid(W1), leftMid(W2), 'D1...D5, A5', P.arrow, fontName);
arrow(ax, rightMid(W2), leftMid(W3), 'EV abc', P.arrow, fontName);
arrow(ax, rightMid(W3), leftMid(N1), 'ordered tensor', P.arrow, fontName);
arrow(ax, rightMid(N1), leftMid(N2), 'hidden map', P.arrow, fontName);
arrow(ax, rightMid(N2), leftMid(J), 'Yhat 0...1', P.arrow, fontName);

%% Phase 3: deterministic supervision
S1 = node(ax, 4.2, 16.2, 12.5, 4.7, P.security, 'Security Supervision Engine', 'Idiff, Irest, waveform derivatives', fontName, P.border, 'rect');
S2 = node(ax, 25.4, 16.2, 15.8, 4.7, P.security, 'External Fault / Deep CT Saturation', 'Transient stability logic', fontName, P.border, 'rect');

drawSmoothArrowPath(ax, [bottomMid(G); 70.95 44.0; 92.0 44.0; 92.0 26.4; 10.45 26.4; topMid(S1)], ...
    'Idiff[n], d(Idiff)/dt', P.arrow, fontName);
drawSmoothArrowPath(ax, [bottomMid(H); 70.95 43.0; 95.0 43.0; 95.0 25.4; 14.8 25.4; 14.8 20.9], ...
    'Irest magnitude', P.arrow, fontName);
arrow(ax, rightMid(S1), leftMid(S2), 'morphological analysis', P.arrow, fontName);
drawSmoothArrowPath(ax, [rightMid(S2); 50.8 18.55; 50.8 25.9; 79.8 25.9; bottomMid(J)], ...
    'BLOCK = 0/1', P.arrow, fontName);

%% Phase 4: actuation
K = node(ax, 55.2, 14.0, 9.0, 6.0, P.decision, 'Dual-Key AND Gate', 'Decision matrix', fontName, P.border, 'diamond');
L = node(ax, 68.2, 18.6, 9.5, 4.7, P.trip, 'Operate Pickup & Timer', 'High-speed clearance', fontName, P.border, 'rect');
M = node(ax, 68.2, 9.6, 9.5, 4.7, P.block, 'Restrain / Suppress Trip', 'NO_TRIP status', fontName, P.border, 'rect');
T = node(ax, 80.0, 18.6, 6.8, 4.7, P.trip, 'Trip Output', 'TRIP ASSERT', fontName, P.border, 'rect');
U = node(ax, 89.0, 18.6, 7.0, 4.7, P.latch, 'S-R Latch', 'Anti-pumping', fontName, P.border, 'rect');
V = node(ax, 88.8, 8.4, 7.5, 4.7, P.start, 'END', 'SOE / logs', fontName, P.border, 'ellipse');

drawArrowPathWithLabelAt(ax, [bottomMid(J); 80.2 26.9; 59.7 26.9; topMid(K)], ...
    'Yhat, BLOCK, Idiff, Irest', P.arrow, fontName, [69.95 27.65]);
drawSmoothArrowPath(ax, [diamondRight(K); 66.0 17.0; 66.0 20.95; leftMid(L)], ...
    'Yhat >= 0.85 and BLOCK = 0', P.arrow, fontName);
drawSmoothArrowPath(ax, [diamondBottom(K); 59.7 11.95; leftMid(M)], ...
    'else / fail-safe', P.arrow, fontName);
arrow(ax, rightMid(L), leftMid(T), 'TRIP_CMD', P.arrow, fontName);
arrow(ax, rightMid(T), leftMid(U), 'binary contact', P.arrow, fontName);
drawSmoothArrowPath(ax, [bottomMid(U); 92.5 15.0; topMid(V)], 'logs, SOE records', P.arrow, fontName);
drawSmoothArrowPath(ax, [rightMid(M); 86.8 11.95; 86.8 10.75; leftMid(V)], 'status only', P.arrow, fontName);

%% Title and thesis verification note
text(ax, 50, 58.7, 'Hybrid Adaptive Transformer Differential Protection Framework', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, 'FontWeight', 'bold', ...
    'FontSize', 15.5, 'Color', [0.08 0.09 0.10]);
text(ax, 50, 2.3, ...
    'Verified against thesis: db4 DWT energy features, LSTM classifier, differential/restraint supervision, CT saturation stability logic, and hybrid Veto/AND trip decision.', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, 'FontSize', 9.0, ...
    'Color', [0.25 0.25 0.25], 'Interpreter', 'none');

%% Save outputs
outDir = fullfile(pwd, 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

pngPath = fullfile(outDir, 'hybrid_protection_framework_flowchart.png');
pdfPath = fullfile(outDir, 'hybrid_protection_framework_flowchart.pdf');
figPath = fullfile(outDir, 'hybrid_protection_framework_flowchart.fig');

exportgraphics(fig, pngPath, 'Resolution', 600);
exportgraphics(fig, pdfPath, 'ContentType', 'vector');
savefig(fig, figPath);

fprintf('Saved hybrid protection framework flowchart to:\n  %s\n  %s\n  %s\n', pngPath, pdfPath, figPath);

%% Local helpers
function h = node(ax, x, y, w, hgt, color, titleText, bodyText, fontName, borderColor, shape)
    if strcmp(shape, 'ellipse')
        rectangle(ax, 'Position', [x y w hgt], 'Curvature', [1 1], ...
            'FaceColor', color, 'EdgeColor', borderColor, 'LineWidth', 1.1);
    elseif strcmp(shape, 'diamond')
        xp = [x+w/2 x+w x+w/2 x];
        yp = [y+hgt y+hgt/2 y y+hgt/2];
        patch(ax, xp, yp, color, 'EdgeColor', borderColor, 'LineWidth', 1.1);
    else
        rectangle(ax, 'Position', [x y w hgt], 'Curvature', 0.06, ...
            'FaceColor', color, 'EdgeColor', borderColor, 'LineWidth', 1.0);
    end
    text(ax, x+w/2, y+hgt*0.64, titleText, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'FontName', fontName, 'FontWeight', 'bold', 'FontSize', 7.5, ...
        'Color', [0.07 0.08 0.09], 'Interpreter', 'none');
    if ~isempty(bodyText)
        text(ax, x+w/2, y+hgt*0.34, bodyText, ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
            'FontName', fontName, 'FontSize', 6.5, ...
            'Color', [0.19 0.20 0.21], 'Interpreter', 'none');
    end
    h = struct('x', x, 'y', y, 'w', w, 'h', hgt);
end

function drawGroup(ax, pos, label, color, borderColor, fontName)
    rectangle(ax, 'Position', pos, 'Curvature', 0.025, ...
        'FaceColor', color, 'EdgeColor', borderColor, 'LineWidth', 1.0);
    text(ax, pos(1)+0.8, pos(2)+pos(4)-1.20, label, ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', fontName, 'FontWeight', 'bold', 'FontSize', 8.9, ...
        'Color', [0.08 0.10 0.12], 'Interpreter', 'none');
end

function arrow(ax, p1, p2, label, color, fontName)
    drawArrowPath(ax, [p1; p2], label, color, fontName);
end

function arrowElbow(ax, p1, pMid, p2, label, color, fontName)
    drawArrowPath(ax, [p1; pMid; p2], label, color, fontName);
end

function drawSmoothArrowPath(ax, pts, label, color, fontName)
    % Keep routed connectors as exact polylines so arrow tips remain docked
    % to the target block edge in exported PDF/PNG outputs.
    drawArrowPath(ax, pts, label, color, fontName);
end

function drawArrowPath(ax, pts, label, color, fontName)
    plot(ax, pts(:,1), pts(:,2), '-', 'Color', color, 'LineWidth', 0.85);
    addArrowHead(ax, pts(end-1,:), pts(end,:), color);
    if ~isempty(label)
        idx = max(1, floor(size(pts,1)/2));
        p = (pts(idx,:) + pts(idx+1,:))/2;
        text(ax, p(1), p(2)+0.75, label, ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
            'FontName', fontName, 'FontSize', 5.3, 'Color', [0.20 0.20 0.20], ...
            'BackgroundColor', [1 1 1], 'Margin', 0.6, 'Interpreter', 'none');
    end
end

function drawArrowPathWithLabelAt(ax, pts, label, color, fontName, labelPos)
    plot(ax, pts(:,1), pts(:,2), '-', 'Color', color, 'LineWidth', 0.85);
    addArrowHead(ax, pts(end-1,:), pts(end,:), color);
    if ~isempty(label)
        text(ax, labelPos(1), labelPos(2), label, ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
            'FontName', fontName, 'FontSize', 5.3, 'Color', [0.20 0.20 0.20], ...
            'BackgroundColor', [1 1 1], 'Margin', 0.6, 'Interpreter', 'none');
    end
end

function addArrowHead(ax, p1, p2, color)
    v = p2 - p1;
    if norm(v) < 1e-6
        return;
    end
    v = v / norm(v);
    n = [-v(2) v(1)];
    len = 0.95;
    wid = 0.42;
    tip = p2;
    base = p2 - len*v;
    tri = [tip; base + wid*n; base - wid*n];
    patch(ax, tri(:,1), tri(:,2), color, 'EdgeColor', color);
end

function p = leftMid(n), p = [n.x, n.y+n.h/2]; end
function p = rightMid(n), p = [n.x+n.w, n.y+n.h/2]; end
function p = topMid(n), p = [n.x+n.w/2, n.y+n.h]; end
function p = bottomMid(n), p = [n.x+n.w/2, n.y]; end
function p = diamondRight(n), p = [n.x+n.w, n.y+n.h/2]; end
function p = diamondBottom(n), p = [n.x+n.w/2, n.y]; end
