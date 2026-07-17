%% =========================================================================
%  plot_transformer_protection_SLD.m
%  Single-Line Diagram: 300 MVA, 230/11 kV, Yd1 Transformer Protection
%  Test System — for thesis figures
%
%  Features drawn:
%   - 230 kV HV bus  &  11 kV LV bus
%   - Inrush energization circuit breaker (HV side)
%   - HV CT  &  LV CT  with nonlinear saturation annotation
%   - Yd1 power transformer (300 MVA, 230/11 kV)
%   - Differential protection zone boundary (IEEE dashed box)
%   - 87T differential relay with CT secondary wiring
%   - Internal fault markers at 10 %, 50 %, 90 % of winding
%   - External fault on HV bus  &  external fault on LV feeder
%   - LV feeders with load symbols
%
%  Usage:  Run as a script or call plot_transformer_protection_SLD()
%  Output: SLD_300MVA_Yd1_protection.png  +  .pdf  (same folder)
%
%  Author : Abeer — Transformer Thesis, 2026
%  Tested : MATLAB R2021b+
%% =========================================================================

function plot_transformer_protection_SLD()

%% ----- Figure setup -------------------------------------------------------
hFig = figure('Name','Transformer Protection SLD', ...
              'Color','white', ...
              'Units','inches', ...
              'Position',[0.5 0.5 16 8.5]);

ax = axes(hFig, 'Position',[0.01 0.08 0.98 0.86]);
hold(ax,'on');  axis(ax,'off');  axis(ax,'equal');
set(ax,'XLim',[-0.8 15.8], 'YLim',[-3.6 7.6]);

%% ----- Colour palette (thesis-safe) ---------------------------------------
C.bus    = [0.05 0.05 0.05];   % near-black  – buses / conductors
C.wire   = [0.20 0.20 0.20];   % dark grey   – conductors
C.xfmr   = [0.05 0.25 0.55];   % steel blue  – transformer
C.ct     = [0.08 0.45 0.10];   % dark green  – CTs
C.relay  = [0.75 0.08 0.08];   % dark red    – 87T relay
C.zone   = [0.80 0.10 0.10];   % red         – diff zone boundary
C.fault  = [0.88 0.35 0.00];   % amber       – internal faults
C.faultE = [0.60 0.00 0.00];   % crimson     – external faults
C.inrush = [0.40 0.00 0.55];   % purple      – inrush CB
C.sat    = [0.50 0.00 0.50];   % purple      – CT saturation note
C.feeder = [0.30 0.30 0.30];   % med grey    – LV feeders

%% ----- Layout constants ---------------------------------------------------
Y0   = 4.5;   % main conductor height
LW_W = 2.0;   % wire linewidth
LW_B = 3.8;   % bus  linewidth

% Key x-coordinates
X_SRC   = 0.0;
X_HVBUS = 1.0;
X_SWCL  = 2.5;   % inrush CB centre
X_HVCT  = 4.0;   % HV CT centre
X_TL    = 5.4;   % transformer left edge
X_TM    = 7.0;   % transformer centre
X_TR    = 8.6;   % transformer right edge
X_LVCT  = 10.0;  % LV CT centre
X_LVBUS = 11.5;
X_FDR   = 12.2;  % feeder junction

%% ===== 1.  HV SOURCE ======================================================
draw_source(ax, X_SRC, Y0, 0.38, C.bus);
line(ax,[X_SRC+0.38 X_HVBUS],[Y0 Y0],'Color',C.wire,'LineWidth',LW_W);

%% ===== 2.  HV BUS (230 kV) ================================================
line(ax,[X_HVBUS X_HVBUS],[Y0-1.3 Y0+1.3],'Color',C.bus,'LineWidth',LW_B);
text(ax, X_HVBUS, Y0+1.65, {'230 kV','HV Bus'}, ...
    'HorizontalAlignment','center','FontSize',10, ...
    'FontWeight','bold','Color',C.bus);

% External HV fault (on bus)
draw_fault(ax, X_HVBUS+0.55, Y0, '\bfF_{ext,HV}', C.faultE, 'below');

%% ===== 3.  HV CONDUCTOR: bus → CB =========================================
line(ax,[X_HVBUS X_SWCL-0.28],[Y0 Y0],'Color',C.wire,'LineWidth',LW_W);

%% ===== 4.  INRUSH ENERGIZATION CB =========================================
draw_CB(ax, X_SWCL, Y0, C.inrush, true);   % true = closed
text(ax, X_SWCL, Y0-0.72, {'Inrush CB','(Energization)'}, ...
    'HorizontalAlignment','center','FontSize',8.5, ...
    'FontWeight','bold','Color',C.inrush);

%% ===== 5.  HV CONDUCTOR: CB → HV CT =======================================
line(ax,[X_SWCL+0.28 X_HVCT-0.32],[Y0 Y0],'Color',C.wire,'LineWidth',LW_W);

%% ===== 6.  HV CT ==========================================================
draw_CT(ax, X_HVCT, Y0, C.ct, LW_W);
text(ax, X_HVCT, Y0+0.85, {'CT_{HV}','(230 kV / 1 A)'}, ...
    'HorizontalAlignment','center','FontSize',8.5, ...
    'FontWeight','bold','Color',C.ct);
% CT saturation annotation
text(ax, X_HVCT, Y0-0.52, '\it\downarrow nonlinear sat.', ...
    'HorizontalAlignment','center','FontSize',7.5,'Color',C.sat);
% Secondary lead down to relay
line(ax,[X_HVCT X_HVCT],[Y0-0.30 Y0-1.35], ...
    'Color',C.ct,'LineWidth',1.4,'LineStyle','--');

%% ===== 7.  HV CONDUCTOR: CT → TRANSFORMER =================================
line(ax,[X_HVCT+0.32 X_TL],[Y0 Y0],'Color',C.wire,'LineWidth',LW_W);

%% ===== 8.  TRANSFORMER (Yd1, 300 MVA, 230/11 kV) ==========================
draw_transformer(ax, X_TM, Y0, C.xfmr);
text(ax, X_TM, Y0+2.25, {'300 MVA  230/11 kV  Yd1'}, ...
    'HorizontalAlignment','center','FontSize',10.5, ...
    'FontWeight','bold','Color',C.xfmr);

%% ===== 9.  INTERNAL FAULT MARKERS (10 %, 50 %, 90 %) ======================
wdg_pct  = [10  50  90];
wdg_lbl  = {'\bfF_{int}(10%)'  '\bfF_{int}(50%)'  '\bfF_{int}(90%)'};
wdg_xpos = X_TL + (wdg_pct/100)*(X_TR-X_TL);   % map % → x on winding

for k = 1:3
    draw_fault(ax, wdg_xpos(k), Y0+0.45, wdg_lbl{k}, C.fault, 'above');
end

%% ===== 10. LV CONDUCTOR: TRANSFORMER → LV CT ==============================
line(ax,[X_TR X_LVCT-0.32],[Y0 Y0],'Color',C.wire,'LineWidth',LW_W);

%% ===== 11. LV CT ==========================================================
draw_CT(ax, X_LVCT, Y0, C.ct, LW_W);
text(ax, X_LVCT, Y0+0.85, {'CT_{LV}','(11 kV / 1 A)'}, ...
    'HorizontalAlignment','center','FontSize',8.5, ...
    'FontWeight','bold','Color',C.ct);
text(ax, X_LVCT, Y0-0.52, '\it\downarrow nonlinear sat.', ...
    'HorizontalAlignment','center','FontSize',7.5,'Color',C.sat);
% Secondary lead down to relay
line(ax,[X_LVCT X_LVCT],[Y0-0.30 Y0-1.35], ...
    'Color',C.ct,'LineWidth',1.4,'LineStyle','--');

%% ===== 12. LV CONDUCTOR: LV CT → LV BUS ===================================
line(ax,[X_LVCT+0.32 X_LVBUS],[Y0 Y0],'Color',C.wire,'LineWidth',LW_W);

%% ===== 13. LV BUS (11 kV) =================================================
line(ax,[X_LVBUS X_LVBUS],[Y0-1.3 Y0+1.3],'Color',C.bus,'LineWidth',LW_B);
text(ax, X_LVBUS, Y0+1.65, {'11 kV','LV Bus'}, ...
    'HorizontalAlignment','center','FontSize',10, ...
    'FontWeight','bold','Color',C.bus);

%% ===== 14. LV FEEDERS =====================================================
draw_LV_feeders(ax, X_LVBUS, X_FDR, Y0, C.feeder, C.faultE, LW_W);

%% ===== 15. DIFFERENTIAL PROTECTION ZONE (IEEE dashed boundary) ===========
Zxl = X_HVCT - 0.55;
Zxr = X_LVCT + 0.55;
Zyb = Y0 - 2.85;
Zyt = Y0 + 2.05;
draw_zone(ax, Zxl, Zxr, Zyb, Zyt, C.zone);
text(ax, (Zxl+Zxr)/2, Zyb-0.30, 'Differential Protection Zone', ...
    'HorizontalAlignment','center','FontSize',9, ...
    'FontWeight','bold','Color',C.zone, ...
    'BackgroundColor','white','EdgeColor',C.zone,'Margin',2);

%% ===== 16. 87T DIFFERENTIAL RELAY ========================================
X_REL = X_TM;
Y_REL = Y0 - 2.15;
draw_relay_box(ax, X_REL, Y_REL, '87T', C.relay);

% CT secondary bus & wiring to relay
Y_BUS2 = Y0 - 1.35;
line(ax,[X_HVCT X_LVCT],[Y_BUS2 Y_BUS2], ...
    'Color',C.ct,'LineWidth',1.2,'LineStyle','--');
line(ax,[X_REL X_REL],[Y_BUS2 Y_REL+0.22], ...
    'Color',C.ct,'LineWidth',1.2,'LineStyle','--');

%% ===== 17. TITLE ==========================================================
title(ax, ...
    {'Single-Line Diagram — 300 MVA, 230/11 kV, Yd1 Transformer Protection Test System'; ...
     'Differential Protection (87T) | HV/LV CTs with Nonlinear Saturation | Internal & External Faults | Inrush Energization'}, ...
    'FontSize',11,'FontWeight','bold');

%% ===== 18. LEGEND =========================================================
draw_legend(ax);

hold(ax,'off');

%% ===== 19. EXPORT =========================================================
out_base = fullfile(fileparts(mfilename('fullpath')), 'SLD_300MVA_Yd1_protection');
exportgraphics(hFig, [out_base '.png'], 'Resolution', 300, 'BackgroundColor','white');
exportgraphics(hFig, [out_base '.pdf'], 'ContentType','vector',  'BackgroundColor','white');
fprintf('[SLD] Saved:\n  %s.png\n  %s.pdf\n', out_base, out_base);

end  % main function


%% =========================================================================
%%  HELPER FUNCTIONS
%% =========================================================================

% ---- AC voltage source (circle + sine symbol) ----------------------------
function draw_source(ax, xc, yc, r, col)
    th = linspace(0,2*pi,80);
    fill(ax, xc+r*cos(th), yc+r*sin(th), 'w', ...
         'EdgeColor',col,'LineWidth',2.0);
    % sine wave inside
    t  = linspace(-pi, pi, 60);
    xs = xc + 0.60*r*t/pi;
    ys = yc + 0.38*r*sin(t);
    line(ax, xs, ys, 'Color',col,'LineWidth',1.5);
end

% ---- Circuit breaker / switch --------------------------------------------
function draw_CB(ax, xc, yc, col, closed)
    hw = 0.28;   % half-width of contact gap
    r  = 0.16;   % small contact circle radius
    th = linspace(0,2*pi,50);
    % left  lead + contact circle
    line(ax,[xc-0.5 xc-hw],[yc yc],'Color',col,'LineWidth',2.2);
    fill(ax, xc-hw+r*cos(th), yc+r*sin(th), 'w','EdgeColor',col,'LineWidth',1.5);
    % right lead + contact circle
    line(ax,[xc+hw xc+0.5],[yc yc],'Color',col,'LineWidth',2.2);
    fill(ax, xc+hw+r*cos(th)*(-1), yc+r*sin(th), 'w','EdgeColor',col,'LineWidth',1.5);
    % blade
    if closed
        line(ax,[xc-hw+r xc+hw-r],[yc yc],'Color',col,'LineWidth',2.5);
    else
        line(ax,[xc-hw+r xc+hw*0.3],[yc yc+0.35],'Color',col,'LineWidth',2.5);
    end
end

% ---- Current transformer (ring on conductor) -----------------------------
function draw_CT(ax, xc, yc, col, lw)
    r  = 0.28;
    th = linspace(0,2*pi,80);
    % primary conductor through
    line(ax,[xc-0.55 xc+0.55],[yc yc],'Color',[0.2 0.2 0.2],'LineWidth',lw);
    % CT annular ring (filled white so conductor appears to pass through)
    fill(ax, xc+r*cos(th), yc+r*0.55*sin(th), 'w', ...
         'EdgeColor',col,'LineWidth',2.0);
    % polarity dot
    fill(ax, xc-0.09+0.05*cos(th), yc+0.28+0.05*sin(th), col, ...
         'EdgeColor',col,'LineWidth',0.5);
    % secondary terminal stub
    line(ax,[xc xc],[yc-0.16 yc-0.30],'Color',col,'LineWidth',1.6);
end

% ---- Yd1 Power transformer -----------------------------------------------
function draw_transformer(ax, xc, yc, col)
    r  = 0.62;   % coil circle radius
    lw = 2.5;
    dx = 0.80;   % HV coil offset from centre  (left)
                 % LV coil offset from centre  (right)
    th = linspace(0,2*pi,80);

    % ---- core (two vertical rectangles)
    cw = 0.18; ch = r*1.15;
    fill(ax,[xc-cw xc xc xc-cw xc-cw], ...
            [yc-ch yc-ch yc+ch yc+ch yc-ch], ...
        [0.85 0.90 0.95],'EdgeColor',col,'LineWidth',1.2);
    fill(ax,[xc xc+cw xc+cw xc xc], ...
            [yc-ch yc-ch yc+ch yc+ch yc-ch], ...
        [0.85 0.90 0.95],'EdgeColor',col,'LineWidth',1.2);

    % ---- HV coil (left winding, Y side)
    fill(ax, xc-dx+r*cos(th), yc+r*0.78*sin(th), [0.94 0.97 1.0], ...
         'EdgeColor',col,'LineWidth',lw);

    % ---- LV coil (right winding, d side)
    fill(ax, xc+dx+r*cos(th), yc+r*0.78*sin(th), [0.94 0.97 1.0], ...
         'EdgeColor',col,'LineWidth',lw);

    % ---- Graphic symbols inside windings (academic star/Y and delta/triangle)
    % Draw star (Y) inside left circle (HV side)
    x1 = xc - dx;
    y1 = yc;
    len = 0.24;
    line(ax, [x1 x1], [y1 y1-len], 'Color', col, 'LineWidth', 2.0);
    line(ax, [x1 x1+len*cos(pi/6)], [y1 y1+len*sin(pi/6)], 'Color', col, 'LineWidth', 2.0);
    line(ax, [x1 x1-len*cos(pi/6)], [y1 y1+len*sin(pi/6)], 'Color', col, 'LineWidth', 2.0);

    % Draw delta (triangle) inside right circle (LV side)
    x2 = xc + dx;
    y2 = yc;
    line(ax, [x2-0.24 x2 x2+0.24 x2-0.24], [y2-0.14 y2+0.28 y2-0.14 y2-0.14], 'Color', col, 'LineWidth', 2.0);

    % ---- Vector group labels below windings
    text(ax, xc-dx, yc-0.78, 'Y', 'HorizontalAlignment','center', ...
        'FontSize',11,'FontWeight','bold','Color',col);
    text(ax, xc+dx, yc-0.78, 'd1', 'HorizontalAlignment','center', ...
        'FontSize',11,'FontWeight','bold','Color',col);

    % ---- Neutral grounding on Y side
    xng = xc - dx - r + 0.02;
    draw_ground(ax, xng-0.05, yc-r*0.78, col);

    % ---- HV/LV connection stubs (connect coil to main conductor)
    line(ax,[xc-dx-r xc-dx-r-0.4],[yc yc],'Color',[0.2 0.2 0.2],'LineWidth',2.0);
    line(ax,[xc+dx+r xc+dx+r+0.4],[yc yc],'Color',[0.2 0.2 0.2],'LineWidth',2.0);
end

% ---- Grounding symbol ----------------------------------------------------
function draw_ground(ax, xc, yc, col)
    line(ax,[xc xc],[yc yc-0.22],'Color',col,'LineWidth',1.8);
    widths = [0.28 0.18 0.09];
    for k = 1:3
        yg = yc - 0.22 - (k-1)*0.11;
        line(ax,[xc-widths(k) xc+widths(k)],[yg yg],'Color',col,'LineWidth',1.8);
    end
end

% ---- Differential protection zone (dashed rectangle) --------------------
function draw_zone(ax, xl, xr, yb, yt, col)
    xs = [xl xr xr xl xl];
    ys = [yb yb yt yt yb];
    line(ax, xs, ys, 'Color',col,'LineWidth',1.8,'LineStyle','--');
end

% ---- 87T Relay box -------------------------------------------------------
function draw_relay_box(ax, xc, yc, lbl, col)
    w = 0.65; h = 0.50;
    fill(ax,[xc-w/2 xc+w/2 xc+w/2 xc-w/2 xc-w/2], ...
            [yc-h/2 yc-h/2 yc+h/2 yc+h/2 yc-h/2], ...
        [1.0 0.94 0.94], 'EdgeColor',col,'LineWidth',2.2);
    text(ax, xc, yc, lbl, 'HorizontalAlignment','center', ...
        'FontSize',12,'FontWeight','bold','Color',col);
end

% ---- Fault marker (X cross + label) -------------------------------------
function draw_fault(ax, xc, yc, lbl, col, pos)
    s = 0.14;
    line(ax,[xc-s xc+s],[yc-s yc+s],'Color',col,'LineWidth',2.4);
    line(ax,[xc-s xc+s],[yc+s yc-s],'Color',col,'LineWidth',2.4);
    switch pos
        case 'above'
            text(ax, xc, yc+s+0.30, lbl, ...
                'HorizontalAlignment','center','FontSize',8.5, ...
                'Color',col,'Interpreter','tex','VerticalAlignment','bottom');
        case 'below'
            text(ax, xc, yc-s-0.30, lbl, ...
                'HorizontalAlignment','center','FontSize',8.5, ...
                'Color',col,'Interpreter','tex','VerticalAlignment','top');
        case 'right'
            text(ax, xc+s+0.20, yc, lbl, ...
                'HorizontalAlignment','left','FontSize',8.5, ...
                'Color',col,'Interpreter','tex','VerticalAlignment','middle');
    end
end

% ---- LV feeders with loads + external LV fault ---------------------------
function draw_LV_feeders(ax, xbus, xfdr, yc, col, faultCol, lw)
    % Junction to feeder column
    line(ax,[xbus xfdr],[yc yc],'Color',col,'LineWidth',lw);

    % Feeder 1 (upper)
    y1 = yc + 0.70;
    line(ax,[xfdr xfdr],[yc y1],     'Color',col,'LineWidth',lw);
    line(ax,[xfdr xfdr+1.5],[y1 y1], 'Color',col,'LineWidth',lw);
    draw_load_symbol(ax, xfdr+1.5, y1, col);
    text(ax, xfdr+0.75, y1+0.28, 'Feeder 1','FontSize',8,'Color',col, ...
        'HorizontalAlignment','center');

    % Feeder 2 (lower) — external LV fault here
    y2 = yc - 0.70;
    line(ax,[xfdr xfdr],[yc y2],     'Color',col,'LineWidth',lw);
    line(ax,[xfdr xfdr+1.5],[y2 y2], 'Color',col,'LineWidth',lw);
    draw_load_symbol(ax, xfdr+1.5, y2, col);
    text(ax, xfdr+0.75, y2-0.30, 'Feeder 2','FontSize',8,'Color',col, ...
        'HorizontalAlignment','center');

    % External LV fault on Feeder 2
    draw_fault(ax, xfdr+0.75, y2, '\bfF_{ext,LV}', faultCol, 'above');
end

% ---- Load symbol (zigzag resistor) --------------------------------------
function draw_load_symbol(ax, xc, yc, col)
    n  = 4;                                        % number of half-cycles
    xs = xc + linspace(0, 0.45, 2*n+2);           % 10 points
    ys = yc + [0 repmat([0.18 -0.18],1,n) 0];     % 10 points
    line(ax, xs, ys, 'Color',col,'LineWidth',1.6);
end

% ---- Legend --------------------------------------------------------------
function draw_legend(ax)
    items = { ...
        [0.08 0.45 0.10], '--- CT secondary wiring (dashed)';
        [0.05 0.25 0.55], 'Transformer (Yd1)';
        [0.75 0.08 0.08], '87T Differential Relay';
        [0.80 0.10 0.10], 'Differential Protection Zone boundary';
        [0.40 0.00 0.55], 'Inrush Energization CB';
        [0.88 0.35 0.00], 'Internal Fault — 10 % / 50 % / 90 % winding';
        [0.60 0.00 0.00], 'External Fault — HV bus  /  LV feeder';
        [0.50 0.00 0.50], 'Nonlinear CT saturation model';
    };
    lx0 = -0.75;   ly0 = -0.30;   dy = 0.38;
    text(ax, lx0+0.85, ly0+0.48, 'Legend', ...
        'FontSize',9,'FontWeight','bold','Color',[0.1 0.1 0.1], ...
        'HorizontalAlignment','center');
    for k = 1:size(items,1)
        c = items{k,1};
        s = items{k,2};
        yy = ly0 - (k-1)*dy;
        line(ax,[lx0 lx0+0.65],[yy yy],'Color',c,'LineWidth',2.5);
        fill(ax, lx0+0.28+0.08*cos(linspace(0,2*pi,30)), ...
                 yy+0.08*sin(linspace(0,2*pi,30)), c,'EdgeColor',c);
        text(ax, lx0+0.80, yy, s,'FontSize',8,'Color',[0.15 0.15 0.15], ...
            'VerticalAlignment','middle');
    end
end
