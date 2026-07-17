clc% =========================================================================
% VisualiseDatasets.m  —  Comprehensive diagnostic suite
% =========================================================================
% Searches pwd and pwd/Datasets/ for:
%   TransformerProtection_Dataset_*.mat   (mixed batch)
%   InrushDataset_*.mat                   (inrush batch)
% Merges all found files and produces four figures:
%   Fig 1 — Dataset Composition        (12 panels)
%   Fig 2 — Parameter Space Coverage   (12 panels)
%   Fig 3 — Statistical Verification   (12 panels)
%   Fig 4 — Representative Waveforms   (12 panels)
% Saves all figures as PNG in figures/academic_plots/
% =========================================================================
clear; clc; close all;

SAVE_FIGS  = true;
SEARCH_SUB = 'datasets';
FS         = 1600;   % sampling frequency (Hz) — matches FeatureExtractor

fprintf('╔══════════════════════════════════════════════════════════════╗\n');
fprintf('║         DATASET VISUALISATION & VERIFICATION  v2            ║\n');
fprintf('╚══════════════════════════════════════════════════════════════╝\n\n');

% ── 1. Find files ─────────────────────────────────────────────────────────
searchPaths = {pwd, fullfile(pwd,SEARCH_SUB)};
patterns    = {'TransformerProtection_Dataset_*.mat','InrushDataset_*.mat'};
srcLabel    = {'Mixed','Inrush'};
allFiles    = struct('path',{},'type',{});
for sp = 1:numel(searchPaths)
    for pt = 1:numel(patterns)
        found = dir(fullfile(searchPaths{sp},patterns{pt}));
        for fi = 1:numel(found)
            allFiles(end+1).path = fullfile(found(fi).folder,found(fi).name);
            allFiles(end  ).type = srcLabel{pt};
        end
    end
end
if isempty(allFiles)
    error('No dataset files found. Run from the folder containing your .mat files.');
end
fprintf('Found %d file(s):\n',numel(allFiles));
for fi=1:numel(allFiles), fprintf('  [%s]  %s\n',allFiles(fi).type,allFiles(fi).path); end

% ── 2. Load & merge ───────────────────────────────────────────────────────
M = loadMerge(allFiles);
N = M.N;
fprintf('\nTotal samples: %d\n\n',N);

% ── 3. Console report ─────────────────────────────────────────────────────
printReport(M,N);

% ── 4. figures ────────────────────────────────────────────────────────────
ts   = datestr(now,'yyyymmdd_HHMMSS');
fig1 = figComposition(M,N);
fig2 = figParameterCoverage(M,N,FS);
fig3 = figStatVerification(M,N);
fig4 = figWaveforms(M,N,FS);

if SAVE_FIGS
    % Resolve output directory to figures/academic_plots relative to the script location
    scriptDir = fileparts(mfilename('fullpath'));
    outDir = fullfile(scriptDir, '..', 'figures', 'academic_plots');
    if ~exist(outDir, 'dir'), mkdir(outDir); end
    
    names  = {'12_Dataset_Composition.png', ...
              '13_Parameter_Space_Coverage.png', ...
              '14_Statistical_Verification.png', ...
              '15_Representative_Waveforms.png'};
    figs   = {fig1,fig2,fig3,fig4};
    for k = 1:4
        fname = fullfile(outDir,names{k});
        exportgraphics(figs{k},fname,'Resolution',300);
        fprintf('Saved: %s\n',fname);
    end
end

% =========================================================================
%  LOAD & MERGE
% =========================================================================
function M = loadMerge(allFiles)
    cF = {'zone','faultType','simulationStatus','ctMismatch',...
          'primaryCurrent','secondaryCurrent','diffCurrent','tripSignal'};
    nF = {'faultResistance','inceptionAngle','inceptionTime',...
          'shouldTrip','noiseLevel'};
    for f=cF, M.(f{1})={}; end
    for f=nF, M.(f{1})=[]; end
    M.sourceFile={}; M.sourceType={}; M.N=0;

    for fi=1:numel(allFiles)
        fprintf('  Loading %s ... ',allFiles(fi).path);
        try
            raw = load(allFiles(fi).path,'dataset');
            ds  = raw.dataset;
        catch ME
            fprintf('FAILED: %s\n',ME.message); continue;
        end
        n = inferN(ds);
        fprintf('%d samples\n',n);
        if n==0, continue; end

        for f=cF
            fn=f{1};
            if isfield(ds,fn) && iscell(ds.(fn)) && numel(ds.(fn))==n
                M.(fn)=[M.(fn); ds.(fn)(:)];
            else
                M.(fn)=[M.(fn); repmat({''},n,1)];
            end
        end
        for f=nF
            fn=f{1};
            if isfield(ds,fn)
                v=double(ds.(fn)); v=v(:);
                if numel(v)==n, M.(fn)=[M.(fn);v];
                else,           M.(fn)=[M.(fn);zeros(n,1)]; end
            else
                M.(fn)=[M.(fn);zeros(n,1)];
            end
        end
        M.sourceFile=[M.sourceFile; repmat({allFiles(fi).path},n,1)];
        M.sourceType=[M.sourceType; repmat({allFiles(fi).type},n,1)];
        M.N=M.N+n;
    end
    M.shouldTrip=logical(M.shouldTrip);
    M.inceptionAngle=double(M.inceptionAngle);
    empty=cellfun(@isempty,M.zone); M.zone(empty)={'Unknown'};
    empty=cellfun(@isempty,M.faultType); M.faultType(empty)={'None'};
end

function n = inferN(ds)
    probes={'zone','faultType','shouldTrip','noiseLevel','primaryCurrent'};
    n=0;
    for k=1:numel(probes)
        if isfield(ds,probes{k})
            v=ds.(probes{k});
            n=max(n,numel(v));
        end
    end
end

% =========================================================================
%  CONSOLE REPORT
% =========================================================================
function printReport(M,N)
    fprintf('══════════════════════════════════════════════════════════════\n');
    fprintf('  VERIFICATION REPORT\n');
    fprintf('══════════════════════════════════════════════════════════════\n');

    % Source
    fprintf('\n── Source breakdown ──\n');
    [uT,~,icT]=unique(M.sourceType);
    for k=1:numel(uT)
        n_k=sum(icT==k);
        fprintf('  %-8s: %4d  (%.1f%%)\n',uT{k},n_k,n_k/N*100);
    end

    % Zone
    fprintf('\n── Zone distribution ──\n');
    zones={'Normal','Inrush','Internal','External','Unknown'};
    for z=zones
        n_z=sum(strcmp(M.zone,z{1}));
        if n_z==0, continue; end
        nT=sum(strcmp(M.zone,z{1})&M.shouldTrip);
        fprintf('  %-10s: %4d  (%5.1f%%)  trip=%d  (%.1f%%)\n',...
                z{1},n_z,n_z/N*100,nT,nT/n_z*100);
    end

    % Fault types
    fprintf('\n── Fault type counts ──\n');
    [uFT,~,icFT]=unique(M.faultType);
    cFT=accumarray(icFT,1);
    [cFTs,si]=sort(cFT,'descend');
    for k=1:numel(uFT)
        fprintf('  %-8s: %4d  (%.1f%%)\n',uFT{si(k)},cFTs(k),cFTs(k)/N*100);
    end

    % Trip rates
    fprintf('\n── Trip rate per zone ──\n');
    exp_trip={'Normal',0;'Inrush',0;'Internal',1;'External',0};
    for r=1:4
        mask=strcmp(M.zone,exp_trip{r,1});
        n_z=sum(mask);
        if n_z==0, continue; end
        rate=sum(M.shouldTrip(mask))/n_z;
        ok=abs(rate-exp_trip{r,2})<0.02;
        fprintf('  %-10s  actual=%.4f  expected=%.0f  %s\n',...
                exp_trip{r,1},rate,exp_trip{r,2},sel(ok,'✓','⚠'));
    end

    % Angle uniformity
    fprintf('\n── Inception angle χ²(7) test ──\n');
    for z={'Internal','External','Inrush'}
        mask=strcmp(M.zone,z{1})&M.inceptionAngle>0;
        ang=M.inceptionAngle(mask);
        if numel(ang)<16, continue; end
        obs=histcounts(ang,0:45:360);
        eu=numel(ang)/8*ones(1,8);
        chi2v=sum((obs-eu).^2./eu);
        pv=1-chi2cdf(chi2v,7);
        fprintf('  %-10s  χ²=%.2f  p=%.3f  %s\n',z{1},chi2v,pv,...
                sel(pv>0.05,'(uniform ✓)','(non-uniform ⚠)'));
    end

    % K-S on Rf
    fprintf('\n── Rf log-uniform K-S test ──\n');
    for z={'Internal','External'}
        mask=strcmp(M.zone,z{1})&M.faultResistance>0.01;
        Rf=M.faultResistance(mask);
        if numel(Rf)<10, continue; end
        logR=log10(Rf);
        U=(logR-min(logR))/(max(logR)-min(logR)+eps);
        Us=sort(U(:));
        [~,pkv]=kstest(U,'CDF',[Us,Us]);
        fprintf('  %-10s  K-S p=%.3f  %s\n',z{1},pkv,...
                sel(pkv>0.05,'(log-uniform ✓)','(non-uniform ⚠)'));
    end

    % Class balance
    nT=sum(M.shouldTrip); nNT=N-nT;
    fprintf('\n── Class balance ──\n');
    fprintf('  Trip     : %4d  (%.1f%%)\n',nT,nT/N*100);
    fprintf('  No-Trip  : %4d  (%.1f%%)\n',nNT,nNT/N*100);
    fprintf('  Ratio    : %.2f  →  pos_weight = %.4f\n',...
            max(nT,nNT)/max(min(nT,nNT),1), nNT/max(nT,1));

    % Success
    nS=sum(strcmp(M.simulationStatus,'Success'));
    fprintf('\n── Simulation success ──\n');
    fprintf('  Success : %4d  (%.1f%%)\n',nS,nS/N*100);
    fprintf('  Failed  : %4d  (%.1f%%)\n',N-nS,(N-nS)/N*100);
    fprintf('══════════════════════════════════════════════════════════════\n\n');
end

% =========================================================================
%  FIGURE 1 — DATASET COMPOSITION  (4×3 grid)
% =========================================================================
function fig = figComposition(M,N)
    ZC = zoneColorMap();
    zones = {'Normal','Inrush','Internal','External'};
    zCnt  = cellfun(@(z)sum(strcmp(M.zone,z)),zones);
    pres  = zCnt>0;

    fig = figure('Name','Fig1 Dataset Composition','NumberTitle','off',...
                 'Position',[30 30 1500 980],'Color','w');

    % ── 1: Zone pie ───────────────────────────────────────────────────────
    ax=subplot(4,4,1);
    zPresPie = zones(pres);
    cmat=cell2mat(cellfun(@(z)ZC(z),zPresPie(:),'UniformOutput',false));
    pie(ax,zCnt(pres),zPresPie); colormap(ax,cmat);
    title(ax,'Zone Distribution','FontWeight','bold','FontSize',10);

    % ── 2: Trip balance ───────────────────────────────────────────────────
    ax=subplot(4,4,2);
    nT=sum(M.shouldTrip); nNT=N-nT;
    bh=bar(ax,[nNT nT],'FaceColor','flat');
    bh.CData=[0.35 0.75 0.35;0.88 0.28 0.28];
    set(ax,'XTickLabel',{'No-Trip','Trip'},'FontSize',9);
    ylabel(ax,'Count'); title(ax,'Trip Label Balance','FontWeight','bold','FontSize',10);
    for k=1:2
        vals=[nNT nT];
        text(k,vals(k)+N*0.01,sprintf('%d\n(%.1f%%)',vals(k),vals(k)/N*100),...
             'HorizontalAlignment','center','FontSize',8,'Parent',ax);
    end
    text(0.5,0.03,sprintf('pos\\_weight=%.3f',nNT/max(nT,1)),...
         'Units','normalized','FontSize',8,'Color',[0.2 0.2 0.6],'Parent',ax);

    % ── 3: Source file breakdown ──────────────────────────────────────────
    ax=subplot(4,4,3);
    [uSrc,~,icS]=unique(M.sourceType);
    sCnt=accumarray(icS,1);
    srcCols=[0.40 0.65 0.90;0.98 0.72 0.20;0.55 0.80 0.55;0.80 0.55 0.80];
    bh2=bar(ax,sCnt,'FaceColor','flat'); bh2.CData=srcCols(1:numel(uSrc),:);
    set(ax,'XTickLabel',uSrc,'FontSize',9);
    ylabel(ax,'Count'); title(ax,'Source Type','FontWeight','bold','FontSize',10);
    for k=1:numel(uSrc)
        text(k,sCnt(k)+N*0.005,sprintf('%.1f%%',sCnt(k)/N*100),...
             'HorizontalAlignment','center','FontSize',8,'Parent',ax);
    end

    % ── 4: Simulation success per zone ────────────────────────────────────
    ax=subplot(4,4,4);
    zPres=zones(pres);
    sr=zeros(1,sum(pres));
    for zi=1:sum(pres)
        mask=strcmp(M.zone,zPres{zi});
        n_z=sum(mask);
        if n_z==0, continue; end
        sr(zi)=sum(strcmp(M.simulationStatus(mask),'Success'))/n_z*100;
    end
    bh3=bar(ax,sr,'FaceColor','flat');
    cd3=cell2mat(cellfun(@(z)ZC(z),zPres(:),'UniformOutput',false));
    bh3.CData=cd3; ylim(ax,[0 106]); ylabel(ax,'Success (%)');
    set(ax,'XTickLabel',zPres,'FontSize',9);
    yline(ax,100,'--r','LineWidth',1.2);
    title(ax,'Sim Success Rate / Zone','FontWeight','bold','FontSize',10);
    for zi=1:sum(pres)
        text(zi,sr(zi)+0.5,sprintf('%.1f%%',sr(zi)),...
             'HorizontalAlignment','center','FontSize',8,'Parent',ax);
    end

    % ── 5: Fault type bar (sorted, all types) ─────────────────────────────
    ax=subplot(4,4,[5 9]);
    [uFT,~,icFT]=unique(M.faultType);
    cFT=accumarray(icFT,1);
    [cFTs,si]=sort(cFT,'descend'); uFTs=uFT(si);
    barh(ax,cFTs,'FaceColor',[0.40 0.62 0.88],'EdgeColor','none');
    set(ax,'YTick',1:numel(uFTs),'YTickLabel',uFTs,'FontSize',9,'YDir','reverse');
    xlabel(ax,'Count'); title(ax,'Fault Type Distribution (all)','FontWeight','bold','FontSize',10);
    for k=1:numel(uFTs)
        text(cFTs(k)+0.5,k,sprintf('%d  (%.1f%%)',cFTs(k),cFTs(k)/N*100),...
             'VerticalAlignment','middle','FontSize',7.5,'Parent',ax);
    end
    grid(ax,'on');

    % ── 6: Per-zone stacked trip/no-trip ──────────────────────────────────
    ax=subplot(4,4,6);
    tZ  = cellfun(@(z)sum(strcmp(M.zone,z)& M.shouldTrip), zones(pres));
    ntZ = cellfun(@(z)sum(strcmp(M.zone,z)&~M.shouldTrip), zones(pres));
    bh4=bar(ax,[ntZ;tZ]','stacked');
    bh4(1).FaceColor=[0.35 0.75 0.35]; bh4(2).FaceColor=[0.88 0.28 0.28];
    set(ax,'XTickLabel',zPres,'XTickLabelRotation',20,'FontSize',9);
    legend(ax,{'No-Trip','Trip'},'Location','northwest','FontSize',8);
    title(ax,'Trip/No-Trip per Zone','FontWeight','bold','FontSize',10);

    % ── 7: Internal fault type pie ────────────────────────────────────────
    ax=subplot(4,4,7);
    intMask=strcmp(M.zone,'Internal');
    if any(intMask)
        [uIF,~,icIF]=unique(M.faultType(intMask));
        cIF=accumarray(icIF,1);
        [cIFs,sii]=sort(cIF,'descend');
        pie(ax,cIFs,uIF(sii));
        colormap(ax,lines(numel(cIFs)));
    end
    title(ax,'Internal Fault Sub-types','FontWeight','bold','FontSize',10);

    % ── 8: External fault type pie ────────────────────────────────────────
    ax=subplot(4,4,8);
    extMask=strcmp(M.zone,'External');
    if any(extMask)
        [uEF,~,icEF]=unique(M.faultType(extMask));
        cEF=accumarray(icEF,1);
        [cEFs,sii]=sort(cEF,'descend');
        pie(ax,cEFs,uEF(sii));
        colormap(ax,cool(numel(cEFs)));
    end
    title(ax,'External Fault Sub-types','FontWeight','bold','FontSize',10);

    % ── 9: Fault type × zone grouped bar ──────────────────────────────────
    ax=subplot(4,4,[10 11]);
    faultOnly={'AG','BG','CG','AB','BC','CA','ABG','BCG','CAG','ABC'};
    zones4={'Normal','Inrush','Internal','External'};
    gdata=zeros(numel(faultOnly),4);
    for fi2=1:numel(faultOnly)
        for zi=1:4
            gdata(fi2,zi)=sum(strcmp(M.faultType,faultOnly{fi2})&strcmp(M.zone,zones4{zi}));
        end
    end
    bar(ax,gdata,'stacked');
    cols4=cell2mat(cellfun(@(z)ZC(z),zones4(:),'UniformOutput',false));
    ax.Children(1).FaceColor=cols4(4,:);
    ax.Children(2).FaceColor=cols4(3,:);
    ax.Children(3).FaceColor=cols4(2,:);
    ax.Children(4).FaceColor=cols4(1,:);
    set(ax,'XTick',1:numel(faultOnly),'XTickLabel',faultOnly,'FontSize',9);
    legend(ax,fliplr(zones4),'Location','northeast','FontSize',8);
    ylabel(ax,'Count'); title(ax,'Fault Type × Zone (stacked)','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 10: Trip rate per fault type (bar) ───────────────────────────────
    ax=subplot(4,4,12);
    tripRF=zeros(1,numel(uFT));
    for k=1:numel(uFT)
        mask=strcmp(M.faultType,uFT{k});
        n_k=sum(mask);
        if n_k>0, tripRF(k)=sum(M.shouldTrip(mask))/n_k; end
    end
    [~,si2]=sort(tripRF,'descend');
    barh(ax,tripRF(si2),'FaceColor','flat',...
         'CData',repmat([0.85 0.40 0.40],numel(uFT),1));
    set(ax,'YTick',1:numel(uFT),'YTickLabel',uFT(si2),'FontSize',8);
    xlabel(ax,'Trip Rate'); xlim(ax,[0 1.15]);
    title(ax,'Trip Rate / Fault Type','FontWeight','bold','FontSize',10);
    xline(ax,0.5,'--k'); grid(ax,'on');

    % ── 11: Zone proportions donut (text summary) ─────────────────────────
    ax=subplot(4,4,[13 14]);
    znames=zones(pres); zcounts=zCnt(pres);
    theta1=0;
    hold(ax,'on'); axis(ax,'equal'); axis(ax,'off');
    cmat2=cell2mat(cellfun(@(z)ZC(z),znames(:),'UniformOutput',false));
    for k=1:numel(znames)
        theta2=theta1+zcounts(k)/N*2*pi;
        th=linspace(theta1,theta2,60);
        xo=[cos(th) 0]; yo=[sin(th) 0];
        xi=0.45*[cos(th) 0]; yi=0.45*[sin(th) 0];
        fill(ax,[xo fliplr(xi)],[yo fliplr(yi)],cmat2(k,:),'EdgeColor','w','LineWidth',1.5);
        mid=(theta1+theta2)/2;
        r=0.7; text(r*cos(mid),r*sin(mid),...
            sprintf('%s\n%d (%.1f%%)',znames{k},zcounts(k),zcounts(k)/N*100),...
            'HorizontalAlignment','center','FontSize',9,'FontWeight','bold','Parent',ax);
        theta1=theta2;
    end
    hold(ax,'off');
    title(ax,'Zone Proportions (donut)','FontWeight','bold','FontSize',10);

    % ── 12: Key stats text box ────────────────────────────────────────────
    ax=subplot(4,4,[15 16]);
    axis(ax,'off');
    nS2=sum(strcmp(M.simulationStatus,'Success'));
    txt={sprintf('N = %d total samples',N),...
         sprintf('Success rate: %.1f%%',nS2/N*100),...
         sprintf('Trip (Internal): %d  (%.1f%%)',sum(M.shouldTrip),sum(M.shouldTrip)/N*100),...
         sprintf('No-Trip: %d  (%.1f%%)',N-sum(M.shouldTrip),(N-sum(M.shouldTrip))/N*100),...
         sprintf('pos\\_weight (BCELoss): %.4f',  (N-sum(M.shouldTrip))/max(sum(M.shouldTrip),1)),...
         sprintf('Unique fault types: %d',numel(uFT)),...
         sprintf('Rf range: [%.3g, %.3g] Ω',min(M.faultResistance(M.faultResistance>0)),max(M.faultResistance)),...
         sprintf('Noise range: [%.3g, %.3g]',min(M.noiseLevel(M.noiseLevel>0)),max(M.noiseLevel)),...
         sprintf('Inception angle: [%d, %d]°',round(min(M.inceptionAngle(M.inceptionAngle>0))),round(max(M.inceptionAngle)))};
    text(0.05,0.95,txt,'Units','normalized','VerticalAlignment','top',...
         'FontSize',10,'FontName','Courier',...
         'BackgroundColor',[0.95 0.95 1.0],'EdgeColor',[0.7 0.7 0.9],...
         'Parent',ax);
    title(ax,'Dataset Summary','FontWeight','bold','FontSize',10);

    sgtitle(fig,sprintf('Dataset Composition  |  N = %d',N),...
            'FontSize',14,'FontWeight','bold');
end

% =========================================================================
%  FIGURE 2 — PARAMETER SPACE COVERAGE  (4×3 grid)
% =========================================================================
function fig = figParameterCoverage(M,N,FS)
    ZC=zoneColorMap();
    zones={'Normal','Inrush','Internal','External'};

    fig=figure('Name','Fig2 Parameter Space Coverage','NumberTitle','off',...
               'Position',[50 20 1500 980],'Color','w');

    % ── 1: Rf histogram — Internal (log scale) ────────────────────────────
    ax=subplot(4,3,1);
    Rf_int=M.faultResistance(strcmp(M.zone,'Internal')&M.faultResistance>0.005);
    if ~isempty(Rf_int)
        edges=logspace(log10(0.005),log10(max(Rf_int)*1.2+0.1),45);
        histogram(ax,Rf_int,edges,'FaceColor',[0.88 0.28 0.28],'EdgeColor','none');
        set(ax,'XScale','log'); grid(ax,'on');
        xline(ax,2,'--k','LineWidth',1.5,'Label','2 Ω','LabelHorizontalAlignment','right','FontSize',8);
        xline(ax,20,'--b','LineWidth',1.5,'Label','20 Ω','LabelHorizontalAlignment','right','FontSize',8);
        xlabel(ax,'Rf (Ω)'); ylabel(ax,'Count');
        title(ax,'Rf — Internal Faults','FontWeight','bold','FontSize',10);
        text(0.02,0.93,sprintf('n=%d\nmed=%.2g Ω\nmax=%.2g Ω',...
             numel(Rf_int),median(Rf_int),max(Rf_int)),...
             'Units','normalized','FontSize',7.5,'BackgroundColor',[1 1 1 0.7],'Parent',ax);
    end

    % ── 2: Rf histogram — External (log scale) ────────────────────────────
    ax=subplot(4,3,2);
    Rf_ext=M.faultResistance(strcmp(M.zone,'External')&M.faultResistance>0.005);
    if ~isempty(Rf_ext)
        edges2=logspace(log10(0.005),log10(max(Rf_ext)*1.2+0.1),40);
        histogram(ax,Rf_ext,edges2,'FaceColor',[0.28 0.55 0.88],'EdgeColor','none');
        set(ax,'XScale','log'); grid(ax,'on');
        xlabel(ax,'Rf (Ω)'); ylabel(ax,'Count');
        title(ax,'Rf — External Faults','FontWeight','bold','FontSize',10);
        text(0.02,0.93,sprintf('n=%d\nmed=%.2g Ω\nmax=%.2g Ω',...
             numel(Rf_ext),median(Rf_ext),max(Rf_ext)),...
             'Units','normalized','FontSize',7.5,'BackgroundColor',[1 1 1 0.7],'Parent',ax);
    end

    % ── 3: Rf CDF overlay (Internal vs External) ─────────────────────────
    ax=subplot(4,3,3);
    hold(ax,'on');
    for zl={'Internal','External'}
        Rf_z=sort(M.faultResistance(strcmp(M.zone,zl{1})&M.faultResistance>0.005));
        if isempty(Rf_z), continue; end
        cdf=(1:numel(Rf_z))/numel(Rf_z);
        semilogx(ax,Rf_z,cdf,'LineWidth',2,'Color',ZC(zl{1}),'DisplayName',zl{1});
    end
    hold(ax,'off');
    legend(ax,'Location','southeast','FontSize',9);
    xlabel(ax,'Rf (Ω)'); ylabel(ax,'CDF');
    title(ax,'Rf CDF: Internal vs External','FontWeight','bold','FontSize',10);
    grid(ax,'on'); xline(ax,2,'--k'); xline(ax,20,'--b');

    % ── 4: Inception angle polar — internal faults ────────────────────────
    ax=subplot(4,3,4);
    fltMask=(strcmp(M.zone,'Internal')|strcmp(M.zone,'External'))&M.inceptionAngle>0;
    ang=M.inceptionAngle(fltMask);
    if numel(ang)>5
        pax=polaraxes(fig,'Position',get(ax,'Position')); delete(ax);
        polarhistogram(pax,deg2rad(ang),24,'FaceColor',[0.98 0.65 0.20],...
                       'EdgeColor','w','LineWidth',0.5,'FaceAlpha',0.85);
        title(pax,'Inception Angle — Faults','FontWeight','bold','FontSize',10);
        % Uniformity annotation
        obs=histcounts(ang,0:45:360); eu=numel(ang)/8*ones(1,8);
        chi2v=sum((obs-eu).^2./eu); pv=1-chi2cdf(chi2v,7);
        text(0,1.15,sprintf('χ²(7)=%.1f  p=%.2f',chi2v,pv),...
             'Units','normalized','HorizontalAlignment','center',...
             'FontSize',8,'Parent',pax);
    end

    % ── 5: Inception angle polar — inrush ────────────────────────────────
    ax=subplot(4,3,5);
    irMask=strcmp(M.zone,'Inrush')&M.inceptionAngle>0;
    irAng=M.inceptionAngle(irMask);
    if numel(irAng)>5
        pax2=polaraxes(fig,'Position',get(ax,'Position')); delete(ax);
        polarhistogram(pax2,deg2rad(irAng),24,'FaceColor',[0.35 0.75 0.35],...
                       'EdgeColor','w','LineWidth',0.5,'FaceAlpha',0.85);
        title(pax2,'Energisation Angle — Inrush','FontWeight','bold','FontSize',10);
        obs=histcounts(irAng,0:45:360); eu=numel(irAng)/8*ones(1,8);
        chi2v=sum((obs-eu).^2./eu); pv=1-chi2cdf(chi2v,7);
        text(0,1.15,sprintf('χ²(7)=%.1f  p=%.2f',chi2v,pv),...
             'Units','normalized','HorizontalAlignment','center',...
             'FontSize',8,'Parent',pax2);
    end

    % ── 6: Inception angle per fault type (violin-style) ─────────────────
    ax=subplot(4,3,6);
    fTypes={'AG','BG','CG','ABG','BCG','CAG','AB','BC','CA','ABC'};
    hold(ax,'on');
    for k=1:numel(fTypes)
        ang_ft=M.inceptionAngle(strcmp(M.faultType,fTypes{k})&M.inceptionAngle>0);
        if isempty(ang_ft), continue; end
        scatter(ax,k*ones(size(ang_ft)),ang_ft,8,[0.6 0.6 0.9],'filled',...
                'MarkerFaceAlpha',0.3);
        plot(ax,[k-0.35 k+0.35],[median(ang_ft) median(ang_ft)],...
             'k-','LineWidth',2);
        q=quantile(ang_ft,[0.25 0.75]);
        plot(ax,[k k],[q(1) q(2)],'k-','LineWidth',1);
    end
    hold(ax,'off');
    set(ax,'XTick',1:numel(fTypes),'XTickLabel',fTypes,'XTickLabelRotation',40,'FontSize',8);
    ylabel(ax,'Inception Angle (°)'); ylim(ax,[-10 380]);
    yticks(ax,0:90:360); yline(ax,0,'--k','Alpha',0.3); yline(ax,360,'--k','Alpha',0.3);
    title(ax,'Angle Distribution per Fault Type','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 7: Noise level distribution (overlapping histograms) ──────────────
    ax=subplot(4,3,7);
    hold(ax,'on');
    for z=zones
        mask=strcmp(M.zone,z{1})&M.noiseLevel>0;
        if sum(mask)<2, continue; end
        histogram(ax,M.noiseLevel(mask),25,'FaceColor',ZC(z{1}),...
                  'EdgeColor','none','FaceAlpha',0.55,'DisplayName',z{1});
    end
    hold(ax,'off');
    legend(ax,'Location','northeast','FontSize',8);
    xlabel(ax,'Noise Level (fraction)'); ylabel(ax,'Count');
    title(ax,'Noise Level by Zone','FontWeight','bold','FontSize',10);
    grid(ax,'on');
    xline(ax,0.05,'--r','LineWidth',1.2,'Label','5%','FontSize',8);

    % ── 8: Noise level CDF by zone ────────────────────────────────────────
    ax=subplot(4,3,8);
    hold(ax,'on');
    for z=zones
        mask=strcmp(M.zone,z{1})&M.noiseLevel>0;
        if sum(mask)<2, continue; end
        nl=sort(M.noiseLevel(mask));
        cdf=(1:sum(mask))/sum(mask);
        plot(ax,nl,cdf,'LineWidth',2,'Color',ZC(z{1}),'DisplayName',z{1});
        % Mark median
        med_nl=median(nl);
        plot(ax,med_nl,0.5,'o','Color',ZC(z{1}),'MarkerSize',6,'MarkerFaceColor',ZC(z{1}));
    end
    hold(ax,'off');
    legend(ax,'Location','southeast','FontSize',8);
    xlabel(ax,'Noise Level'); ylabel(ax,'CDF');
    title(ax,'Noise Level CDF by Zone','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 9: CT mismatch boxplot per channel ───────────────────────────────
    ax=subplot(4,3,9);
    validCT=M.ctMismatch(~cellfun(@isempty,M.ctMismatch));
    if numel(validCT)>5
        CTmat=cell2mat(cellfun(@(x)x(:),validCT(:).','UniformOutput',false));
        if size(CTmat,1)>=6
            boxplot(ax,CTmat(1:6,:)','Labels',{'CH1','CH2','CH3','CH4','CH5','CH6'},...
                    'Colors',[0.35 0.65 0.85],'Widths',0.6);
            yline(ax,1.0,'--k','LineWidth',1.5,'Label','Unity gain');
            ylabel(ax,'Gain Mismatch');
            title(ax,'CT Mismatch per Channel','FontWeight','bold','FontSize',10);
            grid(ax,'on');
            % Add mean ± std annotation
            mu=mean(CTmat(1:6,:),2); sg=std(CTmat(1:6,:),0,2);
            for ch=1:6
                text(ch,max(CTmat(ch,:))+0.002,...
                     sprintf('μ=%.3f\nσ=%.4f',mu(ch),sg(ch)),...
                     'HorizontalAlignment','center','FontSize',6.5,'Parent',ax);
            end
        end
    end

    % ── 10: Rf × inception angle scatter (Internal, by fault type) ───────
    ax=subplot(4,3,10);
    intSc=strcmp(M.zone,'Internal')&M.faultResistance>0.005;
    Rf_sc=M.faultResistance(intSc);
    ang_sc=M.inceptionAngle(intSc);
    ft_sc=M.faultType(intSc);
    [uFT2,~,icFT2]=unique(ft_sc);
    cmap10=lines(numel(uFT2));
    hold(ax,'on');
    for k=1:numel(uFT2)
        sel=icFT2==k;
        scatter(ax,ang_sc(sel),log10(Rf_sc(sel)+0.001),12,cmap10(k,:),...
                'filled','MarkerFaceAlpha',0.5,'DisplayName',uFT2{k});
    end
    hold(ax,'off');
    legend(ax,'Location','northwest','FontSize',7,'NumColumns',2);
    xlabel(ax,'Inception Angle (°)'); ylabel(ax,'log_{10}(Rf)');
    xticks(ax,0:90:360);
    title(ax,'Rf vs Angle (Internal, by type)','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 11: Noise level vs Rf scatter ─────────────────────────────────────
    ax=subplot(4,3,11);
    hold(ax,'on');
    for z=zones
        mask=strcmp(M.zone,z{1})&M.noiseLevel>0;
        if sum(mask)<2, continue; end
        scatter(ax,log10(M.faultResistance(mask)+0.001),M.noiseLevel(mask),...
                8,ZC(z{1}),'filled','MarkerFaceAlpha',0.35,'DisplayName',z{1});
    end
    hold(ax,'off');
    legend(ax,'Location','northeast','FontSize',8);
    xlabel(ax,'log_{10}(Rf+0.001)'); ylabel(ax,'Noise Level');
    title(ax,'Noise vs Rf (by zone)','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 12: Inception time histogram by zone ─────────────────────────────
    ax=subplot(4,3,12);
    hold(ax,'on');
    for z=zones
        mask=strcmp(M.zone,z{1})&M.inceptionTime>0&M.inceptionTime<1.5;
        if sum(mask)<2, continue; end
        histogram(ax,M.inceptionTime(mask),30,'FaceColor',ZC(z{1}),...
                  'EdgeColor','none','FaceAlpha',0.55,'DisplayName',z{1});
    end
    hold(ax,'off');
    legend(ax,'Location','northeast','FontSize',8);
    xlabel(ax,'Inception / Energisation Time (s)'); ylabel(ax,'Count');
    title(ax,'Fault/Energisation Time','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    sgtitle(fig,'Parameter Space Coverage','FontSize',14,'FontWeight','bold');
end

% =========================================================================
%  FIGURE 3 — STATISTICAL VERIFICATION  (4×3 grid)
% =========================================================================
function fig = figStatVerification(M,N)
    ZC=zoneColorMap();
    zones={'Normal','Inrush','Internal','External'};

    fig=figure('Name','Fig3 Statistical Verification','NumberTitle','off',...
               'Position',[70 10 1500 980],'Color','w');

    % ── 1+2: Trip rate per fault type + 95% CI ───────────────────────────
    ax=subplot(4,3,[1 2]);
    [uFT,~,icFT]=unique(M.faultType);
    nFT=numel(uFT);
    tr=zeros(1,nFT); tci=zeros(1,nFT); tcnt=zeros(1,nFT);
    for k=1:nFT
        mask=icFT==k; n_k=sum(mask); tcnt(k)=n_k;
        p=sum(M.shouldTrip(mask))/max(n_k,1);
        tr(k)=p; tci(k)=1.96*sqrt(p*(1-p)/max(n_k,1));
    end
    [~,si]=sort(tr,'descend');
    x=1:nFT;
    bar(ax,tr(si),'FaceColor',[0.85 0.38 0.38],'EdgeColor','none'); hold(ax,'on');
    errorbar(ax,x,tr(si),tci(si),'k.','LineWidth',1.2,'CapSize',4);
    % Annotate count
    for k=1:nFT
        text(k,min(tr(si(k))+tci(si(k))+0.05,1.08),...
             sprintf('n=%d',tcnt(si(k))),'HorizontalAlignment','center',...
             'FontSize',7,'Parent',ax,'Color',[0.3 0.3 0.3]);
    end
    hold(ax,'off');
    set(ax,'XTick',x,'XTickLabel',uFT(si),'XTickLabelRotation',40,'FontSize',9);
    ylabel(ax,'Trip Rate'); ylim(ax,[-0.05 1.20]);
    yline(ax,0.5,'--k','Alpha',0.4);
    title(ax,'Trip Rate per Fault Type (± 95% CI)','FontWeight','bold','FontSize',11);
    grid(ax,'on');

    % ── 3: Trip rate per zone + CI + expected ────────────────────────────
    ax=subplot(4,3,3);
    trZ=zeros(1,4); tciZ=zeros(1,4); expT=[0 0 1 0];
    for zi=1:4
        mask=strcmp(M.zone,zones{zi}); n_z=sum(mask);
        if n_z==0, continue; end
        p=sum(M.shouldTrip(mask))/n_z;
        trZ(zi)=p; tciZ(zi)=1.96*sqrt(p*(1-p)/max(n_z,1));
    end
    bar(ax,trZ,'FaceColor',[0.85 0.38 0.38],'EdgeColor','none'); hold(ax,'on');
    errorbar(ax,1:4,trZ,tciZ,'k.','LineWidth',1.5,'CapSize',5);
    scatter(ax,1:4,expT,60,'kv','filled','DisplayName','Expected');
    hold(ax,'off');
    set(ax,'XTick',1:4,'XTickLabel',zones,'FontSize',9);
    ylabel(ax,'Trip Rate'); ylim(ax,[-0.08 1.15]);
    legend(ax,{'Measured','95% CI','Expected'},'Location','north','FontSize',8);
    title(ax,'Trip Rate per Zone','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 4: Chi-squared angle uniformity per zone ─────────────────────────
    ax=subplot(4,3,4);
    chi2V=zeros(1,4); pvChi=zeros(1,4); hasChi=false(1,4);
    for zi=1:4
        ang=M.inceptionAngle(strcmp(M.zone,zones{zi})&M.inceptionAngle>0);
        if numel(ang)<16, continue; end
        hasChi(zi)=true;
        obs=histcounts(ang,0:45:360); eu=numel(ang)/8*ones(1,8);
        chi2V(zi)=sum((obs-eu).^2./eu);
        pvChi(zi)=1-chi2cdf(chi2V(zi),7);
    end
    bhc=bar(ax,chi2V(hasChi),'FaceColor','flat');
    cd_c=repmat([0.45 0.78 0.45],sum(hasChi),1);
    cd_c(pvChi(hasChi)<0.05,:)=repmat([0.90 0.38 0.38],sum(pvChi(hasChi)<0.05),1);
    bhc.CData=cd_c;
    yline(ax,chi2inv(0.95,7),'--r','LineWidth',1.5,...
          'Label','α=0.05  (χ²=14.1)','FontSize',8);
    set(ax,'XTick',1:sum(hasChi),'XTickLabel',zones(hasChi),'FontSize',9);
    ylabel(ax,'χ²(7) statistic');
    title(ax,'Angle Uniformity χ²(7) Test','FontWeight','bold','FontSize',10);
    for k=1:sum(hasChi)
        vv=chi2V(hasChi); pp=pvChi(hasChi);
        text(k,vv(k)+0.3,sprintf('p=%.3f',pp(k)),...
             'HorizontalAlignment','center','FontSize',8,'Parent',ax);
    end
    grid(ax,'on');

    % ── 5: K-S Rf log-uniform per zone ───────────────────────────────────
    ax=subplot(4,3,5);
    ksP=zeros(1,4); hasKS=false(1,4);
    for zi=1:4
        Rf_z=M.faultResistance(strcmp(M.zone,zones{zi})&M.faultResistance>0.01);
        if numel(Rf_z)<10, continue; end
        hasKS(zi)=true;
        logR=log10(Rf_z);
        U=(logR-min(logR))/(max(logR)-min(logR)+eps);
        Us=sort(U(:));
        [~,ksP(zi)]=kstest(U,'CDF',[Us,Us]);
    end
    bhk=bar(ax,ksP(hasKS),'FaceColor','flat');
    cd_k=repmat([0.40 0.65 0.90],sum(hasKS),1);
    cd_k(ksP(hasKS)<0.05,:)=repmat([0.90 0.38 0.38],sum(ksP(hasKS)<0.05),1);
    bhk.CData=cd_k;
    yline(ax,0.05,'--r','LineWidth',1.5,'Label','p=0.05','FontSize',8);
    set(ax,'XTick',1:sum(hasKS),'XTickLabel',zones(hasKS),'FontSize',9);
    ylabel(ax,'K-S p-value'); ylim(ax,[0 1.05]);
    title(ax,'Rf Log-Uniform K-S Test','FontWeight','bold','FontSize',10);
    for k=1:sum(hasKS)
        pv2=ksP(hasKS);
        text(k,min(pv2(k)+0.03,0.98),sprintf('%.3f',pv2(k)),...
             'HorizontalAlignment','center','FontSize',8,'Parent',ax);
    end
    grid(ax,'on');

    % ── 6: Zone × fault-type trip rate heatmap ───────────────────────────
    ax=subplot(4,3,[6 9]);
    [uFT2,~,icFT2]=unique(M.faultType);
    nFT2=numel(uFT2);
    heatD=nan(4,nFT2);
    for zi=1:4
        for ti=1:nFT2
            mask=strcmp(M.zone,zones{zi})&icFT2==ti;
            n_m=sum(mask);
            if n_m>0, heatD(zi,ti)=sum(M.shouldTrip(mask))/n_m; end
        end
    end
    imagesc(ax,heatD); colormap(ax,redblueMap(256)); caxis(ax,[0 1]);
    cb=colorbar(ax); cb.Label.String='Trip Rate'; cb.FontSize=8;
    set(ax,'XTick',1:nFT2,'XTickLabel',uFT2,'XTickLabelRotation',45,...
           'YTick',1:4,'YTickLabel',zones,'FontSize',9);
    title(ax,'Trip Rate Heat-map  (Zone × Fault Type)','FontWeight','bold','FontSize',11);
    for zi=1:4
        for ti=1:nFT2
            if ~isnan(heatD(zi,ti))
                text(ti,zi,sprintf('%.2f',heatD(zi,ti)),...
                     'HorizontalAlignment','center','FontSize',8,...
                     'Color',sel(heatD(zi,ti)>0.5,'w','k'),'Parent',ax);
            end
        end
    end

    % ── 7: Sample count sufficiency (≥30 per class) ──────────────────────
    ax=subplot(4,3,7);
    [uFT3,~,icFT3]=unique(M.faultType);
    cFT3=accumarray(icFT3,1);
    [cFT3s,si3]=sort(cFT3,'descend');
    cols_suf=repmat([0.40 0.75 0.40],numel(uFT3),1);
    cols_suf(cFT3s<30,:)=repmat([0.90 0.38 0.38],sum(cFT3s<30),1);
    bhS=barh(ax,cFT3s,'FaceColor','flat'); bhS.CData=cols_suf;
    set(ax,'YTick',1:numel(uFT3),'YTickLabel',uFT3(si3),'FontSize',8);
    xlabel(ax,'Count'); xline(ax,30,'--r','LineWidth',1.5,'Label','n=30 minimum','FontSize',8);
    title(ax,'Sample Sufficiency per Fault Type','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 8: Noise level × zone confidence intervals ────────────────────────
    ax=subplot(4,3,8);
    hold(ax,'on');
    for zi=1:4
        mask=strcmp(M.zone,zones{zi})&M.noiseLevel>0;
        nl=M.noiseLevel(mask);
        if numel(nl)<2, continue; end
        mn=mean(nl); sg=std(nl); se=sg/sqrt(numel(nl));
        bar(ax,zi,mn,'FaceColor',ZC(zones{zi}),'EdgeColor','none','BarWidth',0.5);
        errorbar(ax,zi,mn,1.96*se,'k.','LineWidth',1.5,'CapSize',6);
        text(zi,mn+1.96*se+0.001,sprintf('μ=%.4f\nσ=%.4f',mn,sg),...
             'HorizontalAlignment','center','FontSize',7.5,'Parent',ax);
    end
    hold(ax,'off');
    set(ax,'XTick',1:4,'XTickLabel',zones,'FontSize',9);
    ylabel(ax,'Noise Level'); ylim(ax,[0 max(M.noiseLevel)*1.3+0.002]);
    title(ax,'Noise Level Mean ± 95% CI per Zone','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    % ── 10: Rf box per fault type (internal only) ─────────────────────────
    ax=subplot(4,3,10);
    fTypes={'AG','BG','CG','ABG','BCG','CAG','AB','BC','CA','ABC'};
    grpData={}; grpLabels={};
    for k=1:numel(fTypes)
        mask=strcmp(M.zone,'Internal')&strcmp(M.faultType,fTypes{k})&M.faultResistance>0.005;
        Rf_k=M.faultResistance(mask);
        if numel(Rf_k)>=3
            grpData{end+1}=log10(Rf_k);  %#ok
            grpLabels{end+1}=fTypes{k};  %#ok
        end
    end
    if ~isempty(grpData)
        allVals=cell2mat(cellfun(@(x)x(:),grpData(:),'UniformOutput',false));
        grpIdx=cell2mat(arrayfun(@(k)k*ones(numel(grpData{k}),1),(1:numel(grpData))','UniformOutput',false));
        boxplot(ax,allVals,grpIdx,'Labels',grpLabels,'Colors',[0.88 0.28 0.28],...
                'Whisker',1.5);
        ylabel(ax,'log_{10}(Rf)'); xlabel(ax,'Fault Type');
        title(ax,'Rf Distribution per Internal Fault Type','FontWeight','bold','FontSize',10);
        grid(ax,'on');
    end

    % ── 11: Class balance with recommended training weight ────────────────
    ax=subplot(4,3,11);
    nT=sum(M.shouldTrip); nNT=N-nT;
    bh11=barh(ax,[nNT nT],'FaceColor','flat');
    bh11.CData=[0.35 0.75 0.35;0.88 0.28 0.28];
    set(ax,'YTick',[1 2],'YTickLabel',{'No-Trip','Trip'},'FontSize',10);
    xlabel(ax,'Sample Count');
    title(ax,'Binary Class Balance','FontWeight','bold','FontSize',10);
    text(max(nNT,nT)*0.55,1,sprintf('N=%d  (%.1f%%)',nNT,nNT/N*100),...
         'VerticalAlignment','middle','FontSize',9,'Parent',ax);
    text(max(nNT,nT)*0.55,2,sprintf('N=%d  (%.1f%%)',nT,nT/N*100),...
         'VerticalAlignment','middle','FontSize',9,'Parent',ax);
    text(0.05,0.05,sprintf('pos\\_weight = %.4f',nNT/max(nT,1)),...
         'Units','normalized','FontSize',10,'FontWeight','bold',...
         'Color',[0.18 0.18 0.60],'Parent',ax);
    grid(ax,'on');

    % ── 12: Inception angle histogram per zone (line plot) ────────────────
    ax=subplot(4,3,12);
    hold(ax,'on');
    for z=zones
        ang=M.inceptionAngle(strcmp(M.zone,z{1})&M.inceptionAngle>0);
        if numel(ang)<4, continue; end
        [c,e]=histcounts(ang,0:20:360);
        centres=(e(1:end-1)+e(2:end))/2;
        plot(ax,centres,c,'LineWidth',2,'Color',ZC(z{1}),'DisplayName',z{1});
    end
    % Ideal uniform line
    totalAng=sum(M.inceptionAngle>0);
    yline(ax,totalAng/18,'--k','LineWidth',1,'Label','Ideal uniform','FontSize',7);
    hold(ax,'off');
    legend(ax,'Location','northwest','FontSize',8);
    xlabel(ax,'Inception Angle (°)'); ylabel(ax,'Count');
    xlim(ax,[0 360]); xticks(ax,0:90:360);
    title(ax,'Angle Distribution per Zone (20° bins)','FontWeight','bold','FontSize',10);
    grid(ax,'on');

    sgtitle(fig,sprintf('Statistical Verification  |  N = %d',N),...
            'FontSize',14,'FontWeight','bold');
end

% =========================================================================
%  FIGURE 4 — REPRESENTATIVE WAVEFORMS  (6 rows × 2 cols)
% =========================================================================
function fig = figWaveforms(M,N,FS)
    fig=figure('Name','Fig4 Representative Waveforms','NumberTitle','off',...
               'Position',[90 10 1400 1100],'Color','w');

    categories={
        'Normal',   'Normal',  'None',  'Normal Operation (shouldTrip=false)';
        'Inrush',   'Inrush',  'None',  'Magnetizing Inrush (shouldTrip=false)';
        'Internal', 'Internal','AG',    'Internal A-G Fault (shouldTrip=true)';
        'Internal', 'Internal','ABC',   'Internal 3-Phase Fault (shouldTrip=true)';
        'External', 'External','AG',    'External A-G Fault (shouldTrip=false)';
        'External', 'External','ABC',   'External 3-Phase Fault (shouldTrip=false)';
    };

    phCols=[0.85 0.15 0.15; 0.10 0.50 0.10; 0.10 0.20 0.88];  % R G B phases

    for row=1:6
        zone_r=categories{row,2};
        ft_r  =categories{row,3};
        label =categories{row,4};

        % Find a successful sample matching this category
        mask=strcmp(M.zone,zone_r) & strcmp(M.faultType,ft_r) & ...
             strcmp(M.simulationStatus,'Success');
        idx=find(mask,1,'first');

        % ── Left col: Primary current (3-phase) ───────────────────────────
        ax=subplot(6,2,2*row-1);
        if ~isempty(idx) && ~isempty(M.primaryCurrent{idx})
            Ip=double(M.primaryCurrent{idx});
            if ismatrix(Ip) && size(Ip,2)>=3
                t_s=(0:size(Ip,1)-1)/FS;
                hold(ax,'on');
                for ph=1:3
                    plot(ax,t_s,Ip(:,ph),'Color',phCols(ph,:),'LineWidth',1.2);
                end
                hold(ax,'off');
                legend(ax,{'I_A','I_B','I_C'},'Location','northeast',...
                       'FontSize',7,'Orientation','horizontal');
            else
                text(0.5,0.5,'waveform not 3-col','HorizontalAlignment','center',...
                     'Units','normalized','Parent',ax);
            end
        else
            text(0.5,0.5,'No data','HorizontalAlignment','center',...
                 'Units','normalized','Parent',ax);
        end
        xlabel(ax,'Time (s)'); ylabel(ax,'Current (pu)');
        title(ax,sprintf('%s — Primary I_{abc}',label),'FontSize',9,'FontWeight','bold');
        grid(ax,'on'); box(ax,'on');

        % ── Right col: Secondary current ─────────────────────────────────
        ax=subplot(6,2,2*row);
        if ~isempty(idx) && ~isempty(M.secondaryCurrent{idx})
            Is=double(M.secondaryCurrent{idx});
            if ismatrix(Is) && size(Is,2)>=3
                t_s=(0:size(Is,1)-1)/FS;
                hold(ax,'on');
                for ph=1:3
                    plot(ax,t_s,Is(:,ph),'Color',phCols(ph,:),'LineWidth',1.2);
                end
                hold(ax,'off');
                legend(ax,{'I_A','I_B','I_C'},'Location','northeast',...
                       'FontSize',7,'Orientation','horizontal');
            else
                text(0.5,0.5,'waveform not 3-col','HorizontalAlignment','center',...
                     'Units','normalized','Parent',ax);
            end
        else
            text(0.5,0.5,'No data','HorizontalAlignment','center',...
                 'Units','normalized','Parent',ax);
        end
        xlabel(ax,'Time (s)'); ylabel(ax,'Current (pu)');
        title(ax,sprintf('%s — Secondary I_{abc}',label),'FontSize',9,'FontWeight','bold');
        grid(ax,'on'); box(ax,'on');
    end

    sgtitle(fig,'Representative 3-Phase Waveforms by Scenario Category',...
            'FontSize',13,'FontWeight','bold');
end

% =========================================================================
%  UTILITIES
% =========================================================================
function ZC = zoneColorMap()
    ZC=containers.Map(...
        {'Normal','Inrush','Internal','External','Unknown'},...
        {[0.30 0.72 0.30],[0.96 0.70 0.18],[0.86 0.25 0.25],[0.25 0.52 0.86],[0.65 0.65 0.65]});
end

function cmap = redblueMap(n)
    h=floor(n/2);
    r1=linspace(0.10,1,h)'; g1=linspace(0.18,1,h)'; b1=ones(h,1);
    r2=ones(n-h,1); g2=linspace(1,0.18,n-h)'; b2=linspace(1,0.10,n-h)';
    cmap=[[r1;r2] [g1;g2] [b1;b2]];
end

function r = sel(cond,a,b)
    if cond, r=a; else, r=b; end
end
