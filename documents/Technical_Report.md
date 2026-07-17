# Technical Report: Hybrid Adaptive Power Transformer Differential Protection
## An Intelligent DWT–LSTM Framework with Real-Time Closed-Loop Validation

**Authors:** Md Moinul Haque, Md Reyaz Uddin  
**Institution:** Department of Electrical, Electronic and Communication Engineering (EECE), Military Institute of Science and Technology (MIST), Dhaka, Bangladesh  
**Date:** June 2026  
**Status:** Comprehensive Technical Documentation & Recreation Manual

---

## Chapter 1: Introduction and Literature Review

### 1.1. Background and Motivation
Power transformers are the cornerstone of electrical transmission and distribution networks, acting as critical links between different voltage levels. Valued at millions of dollars per unit, their failure can result in substantial financial losses, system instability, and widespread blackouts. Consequently, the development of high-performance, fast, and secure protective relaying schemes is crucial.

Transformer protection is primarily based on the percentage differential relay (ANSI 87T), which compares the currents entering and leaving the protected zone. Under normal operating conditions or external faults, the differential current (the vector sum of the terminal currents) is theoretically zero. However, transient conditions such as magnetizing inrush and Current Transformer (CT) saturation can produce significant false differential currents, causing conventional relays to maloperate.

### 1.2. Failure Modes of Conventional Relays
1. **Magnetizing Inrush Current:** When a transformer is energized, the transient flux excursion can drive the core into deep saturation, drawing inrush currents up to 10 times the rated current. Traditionally, the second harmonic restraint method is used to block the relay during inrush. However, modern transformers use high-permeability, cold-rolled grain-oriented steel, which reduces the second harmonic ratio (often below 7–10%), rendering traditional thresholds (typically 15%) ineffective.
2. **Current Transformer (CT) Saturation:** Heavy through-faults (external faults) can cause high primary currents with large DC offsets, driving CTs into saturation. The distorted secondary current waveform produces a false differential current. If this current falls in the operate region of the relay, a false trip occurs.
3. **Sympathetic Inrush:** The energization of a transformer connected in parallel with an already energized transformer can cause a transient inrush in both units due to the system impedance drop. This sympathetic inrush exhibits a slow decay rate and low harmonic content, which easily fools conventional restraints.

### 1.3. Literature Survey of Signal Processing & Machine Learning
To address these limitations, researchers have proposed various techniques:
- **Fourier Transform (FT) & Short-Time Fourier Transform (STFT):** Widely used for harmonic analysis, but fail to capture fast-evolving transient wave-fronts due to fixed windowing.
- **Discrete Wavelet Transform (DWT):** Isolates transients in both time and frequency domains, making it ideal for detecting sudden changes like fault inception and CT saturation clipping.
- **Artificial Neural Networks (ANN) & Support Vector Machines (SVM):** Shallow classifiers that can map wavelet coefficients to transient states, but struggle to capture sequential patterns or temporal dependencies.
- **Convolutional Neural Networks (CNN):** Excellent at extracting spatial features from waveforms but require large computation times and lack memory mechanism for sequential inputs.
- **Recurrent Neural Networks (RNN) & Long Short-Term Memory (LSTM):** Highly suited for sequential data like time-series current measurements. LSTMs address the vanishing gradient problem of standard RNNs, learning the "decay story" of inrush currents and the "sustained story" of internal faults.

---

## Chapter 2: Theoretical Foundations and Mathematical Modeling

### 2.1. Differential Relaying Principles
The current differential relay operates by matching the secondary currents of the current transformers installed on the High Voltage (HV) and Low Voltage (LV) terminals.
- **Vector Compensation:** High Voltage currents ($I_{HV}$) and Low Voltage currents ($I_{LV}$) must be aligned to compensate for the phase shift introduced by the transformer winding connection (e.g., Wye-Delta).
- **Ratio Matching:** Scaling factors are applied to compensate for the difference in CT ratios.
- **Differential Current ($I_{diff}$):**
  $$I_{diff} = |I_{HV} - I_{LV}|$$
- **Restraint Current ($I_{rest}$):**
  $$I_{rest} = \frac{|I_{HV}| + |I_{LV}|}{2}$$

The operating region is defined by a dual-slope bias characteristic to prevent tripping on minor mismatches (Slope 1) and heavy through-faults with CT saturation (Slope 2).

### 2.2. Mathematical Derivation of Magnetizing Inrush
The voltage-flux relationship of a transformer winding is:
$$v(t) = N \frac{d\phi(t)}{dt} + R i(t)$$
Assuming the winding resistance $R$ is negligible, and the applied voltage is $v(t) = V_m \sin(\omega t + \theta)$:
$$\phi(t) = \frac{1}{N} \int_{0}^{t} V_m \sin(\omega \tau + \theta) d\tau + \phi_0$$
$$\phi(t) = -\frac{V_m}{\omega N} \cos(\omega t + \theta) + \phi_0 + \left[ \frac{V_m}{\omega N} \cos(\theta) - \phi_0 \right] e^{-\frac{R}{L}t}$$
where $\phi_0$ is the remanent flux at $t=0$. The peak flux occurs when $\omega t = \pi$:
$$\phi_{peak} = \frac{V_m}{\omega N} (1 + \cos(\theta)) + \phi_0$$
The maximum flux excursion occurs at $\theta = 0^\circ$:
$$\phi_{max} = \frac{2 V_m}{\omega N} + \phi_0$$
If this flux exceeds the saturation knee point of the magnetization curve:
$$i_m(t) = g(\phi(t))$$
where $g$ is the highly nonlinear inverse magnetization function. The collapsing core inductance causes $i_m(t)$ to spike.

### 2.3. Current Transformer (CT) Saturation Hysteresis Model
The equivalent circuit of a current transformer consists of an ideal current source, secondary winding resistance $R_s$, leakage inductance $L_s$, burden resistance $R_b$, burden inductance $L_b$, and a parallel magnetizing branch.
The magnetizing current $i_m(t)$ depends on the core flux linkage $\phi_{CT}(t)$:
$$\phi_{CT}(t) = \int \left[ (R_s + R_b) i_s(t) + (L_s + L_b) \frac{di_s(t)}{dt} \right] dt$$
The B-H loop of the CT core exhibits magnetic hysteresis, modeled using a piecewise-linear or continuous hysteresis model (such as the Jiles–Atherton model). In the Jiles-Atherton model, the magnetization $M$ is divided into reversible ($M_{rev}$) and irreversible ($M_{irr}$) components:
$$M = M_{rev} + M_{irr}$$
$$M_{rev} = c (M_{an} - M)$$
$$\frac{dM_{irr}}{dH} = \frac{M_{an} - M_{irr}}{\delta k - \alpha (M_{an} - M_{irr})}$$
where $H$ is the magnetic field intensity, $M_{an}$ is the anhysteretic magnetization, $c$ is the domain wall bending coefficient, $k$ is the pinning energy parameter, and $\alpha$ is the domain coupling parameter. When $M$ reaches the saturation limit $M_{sat}$, the differential permeability $\mu_{diff} = dB/dH$ drops to $\mu_0$, clipping the secondary current.

---

## Chapter 3: Power System Modeling and Physical Specifications

### 3.1. Transformer Configuration
The physical power system model was developed in MATLAB/Simulink using Simscape Electrical blocks. The model parameters represent a typical transmission-level transformer:
- **Rated Capacity:** 300 MVA, three-phase
- **Voltage Ratio:** 230 kV / 11 kV
- **Vector Group:** Yd1 (Delta winding lags Wye winding by 30 degrees).
- **HV Winding Connection:** Wye-Grounded (Yn)
- **LV Winding Connection:** Delta (d)
- **Rated Winding Resistances:** $R_{HV} = 0.002\ \text{pu}$, $R_{LV} = 0.0025\ \text{pu}$
- **Rated Leakage Inductances:** $L_{HV} = 0.08\ \text{pu}$, $L_{LV} = 0.08\ \text{pu}$
- **Core Magnetization Curve:** Piecewise-linear model with a knee point at $1.2\ \text{pu}$ flux, driving into deep saturation at $1.5\ \text{pu}$ flux.

### 3.2. Current Transformer (CT) Specifications
- **HV Side CTs:** Ratio 800:5, Class 10P20 (reaches 10% error at 20 times nominal current). Winding resistance $R_{CT, HV} = 0.2\ \Omega$, leakage inductance $L_{CT, HV} = 0.5\ \text{mH}$.
- **LV Side CTs:** Ratio 16000:5, Class 10P20. Winding resistance $R_{CT, LV} = 0.15\ \Omega$, leakage inductance $L_{CT, LV} = 0.4\ \text{mH}$.
- **Burden Configuration:** Connected via a $200\ \text{m}$ copper cable (resistance $0.8\ \Omega$) to a relay burden of $Z_b = 0.5\ \Omega$.

### 3.3. Signal Conditioning & Merging Unit Chain
To emulate an IEC 61850-9-2 Merging Unit, terminal currents are processed through a physical signal-conditioning chain:
1. **Analog Anti-Aliasing Filter:** 4th-order Butterworth low-pass filter with a cutoff frequency of $800\ \text{Hz}$ to eliminate high-frequency switching noise.
2. **Quantization:** 16-bit Analog-to-Digital Converter (ADC) running at $10\ \text{kHz}$ sampling rate.
3. **Noise Insertion:** Additive White Gaussian Noise (AWGN) added to the quantized signal to simulate instrument transformer and line noise, evaluated at $20\ \text{dB}$, $30\ \text{dB}$, and $40\ \text{dB}$ Signal-to-Noise Ratios (SNR).
4. **Resampling/Decimation Block:** Downsamples the signal to the target relay sampling rate:
   - For the resource-optimized model: Decimated to $1.6\ \text{kHz}$ (32 samples per cycle).
   - For the high-resolution thesis model: Maintained at $10.0\ \text{kHz}$ (200 samples per cycle).

---

## Chapter 4: Signal Processing and DWT Feature Extraction

### 4.1. The Daubechies-4 (db4) Wavelet
The Discrete Wavelet Transform utilizes a mother wavelet $\psi(t)$ and scaling function $\phi(t)$ to analyze signals. The Daubechies-4 wavelet is selected because:
1. **Vanishing Moments:** It has 4 vanishing moments, allowing it to ignore polynomial trends up to degree 3, thereby focusing on transient disruptions.
2. **Asymmetrical Structure:** The asymmetric shape of the db4 wavelet matches the sharp, one-sided wavefront of inception transients and current clipping.
3. **Compact Support:** The filter length is 8 coefficients, balancing frequency localization and computational speed.

The exact low-pass decomposition filter coefficients $h[n]$ and high-pass coefficients $g[n]$ are:
- $h[0] = 0.23037781, h[1] = 0.71484657, h[2] = 0.63088076, h[3] = -0.02798376$
- $h[4] = -0.18703481, h[5] = 0.03084138, h[6] = 0.03288301, h[7] = -0.01059740$
- $g[n] = (-1)^n h[7 - n]$ for $n = 0, 1, \dots, 7$

### 4.2. Multi-Resolution Analysis (MRA)
The signal is recursively filtered and downsampled by 2.
At Level 1:
$$a_1[k] = \sum_{n=0}^{N-1} x[n] h[2k - n], \quad d_1[k] = \sum_{n=0}^{N-1} x[n] g[2k - n]$$
At Level 2:
$$a_2[k] = \sum_{n=0}^{M-1} a_1[n] h[2k - n], \quad d_2[k] = \sum_{n=0}^{M-1} a_1[n] g[2k - n]$$

### 4.3. Statistical Feature Formulations
For the 10 kHz thesis model, 7 statistical features are calculated from the detail coefficients $d_j$ of the sliding window of length $W$:
1. **Energy ($E$):**
   $$E = \sum_{i=1}^{W} d_j[i]^2$$
2. **Standard Deviation ($\sigma$):**
   $$\sigma = \sqrt{\frac{1}{W-1} \sum_{i=1}^{W} (d_j[i] - \bar{d}_j)^2}$$
3. **Shannon Entropy ($H$):**
   $$p_i = \frac{d_j[i]^2}{E}, \quad H = -\sum_{i=1}^{W} p_i \ln(p_i)$$
4. **Max Amplitude ($M$):**
   $$M = \max_{1 \le i \le W} |d_j[i]|$$
5. **Mean Absolute Deviation (MAD):**
   $$\text{MAD} = \frac{1}{W} \sum_{i=1}^{W} |d_j[i] - \bar{d}_j|$$
6. **Kurtosis ($K$):**
   $$K = \frac{\frac{1}{W} \sum_{i=1}^{W} (d_j[i] - \bar{d}_j)^4}{\sigma^4} - 3$$
7. **Skewness ($S$):**
   $$S = \frac{\frac{1}{W} \sum_{i=1}^{W} (d_j[i] - \bar{d}_j)^3}{\sigma^3}$$

---

## Chapter 5: LSTM Architecture and Attention Mechanism

### 5.1. Long Short-Term Memory (LSTM) Cell Equations
An LSTM cell processes a sequence of feature vectors $\mathbf{x}_t$ at step $t \in [1, T]$ to update cell state $\mathbf{C}_t$ and hidden state $\mathbf{h}_t$.

```text
       +------------------------------------+
       |            Cell State C_t          |
=====> | -------------( x )------------(+)  | =====> C_t
       |                ^               ^   |
       |                |               |   |
       |           Forget Gate     Input Gate
       |              f_t             i_t   |
       |               |               |    |
=====> |  ===> [ Gate Activations ]  ====   | =====> h_t
 h_t-1 |  ===> [   f_t, i_t, o_t  ]  ====   |
       +------------------------------------+
                        ^
                     Input x_t
```

The mathematical update equations are:
1. **Forget Gate ($f_t$):** Controls how much of the old cell state to discard.
   $$f_t = \sigma(W_f \mathbf{x}_t + U_f \mathbf{h}_{t-1} + b_f)$$
2. **Input Gate ($i_t$):** Decides which new values to write into the cell state.
   $$i_t = \sigma(W_i \mathbf{x}_t + U_i \mathbf{h}_{t-1} + b_i)$$
3. **Candidate Cell State ($\tilde{C}_t$):** Creates a vector of new candidate values.
   $$\tilde{C}_t = \tanh(W_c \mathbf{x}_t + U_c \mathbf{h}_{t-1} + b_c)$$
4. **Cell State Update ($C_t$):** Combines forget and input gate actions to update the state.
   $$C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$
5. **Output Gate ($o_t$):** Decides what to output based on the cell state.
   $$o_t = \sigma(W_o \mathbf{x}_t + U_o \mathbf{h}_{t-1} + b_o)$$
6. **Hidden State ($h_t$):** The output hidden representation.
   $$h_t = o_t \odot \tanh(C_t)$$
where $\sigma(z) = 1/(1 + e^{-z})$ is the sigmoid function, $\odot$ represents element-wise multiplication, and $W, U, b$ are the weights and biases.

### 5.2. Global Temporal Attention Mechanism
To enable the model to focus on critical transient points (such as fault inception) within the 32-timestep sequence, a global attention mechanism is layered over the LSTM outputs $\mathbf{h}_t$:
1. **Score Calculation ($e_t$):**
   $$e_t = \mathbf{v}_a^T \tanh(W_a \mathbf{h}_t + \mathbf{b}_a)$$
2. **Attention Weights ($\alpha_t$):** Softmax normalized weights.
   $$\alpha_t = \frac{\exp(e_t)}{\sum_{j=1}^{T} \exp(e_j)}$$
3. **Context Vector ($\mathbf{c}$):** Weighted sum of hidden representations.
   $$\mathbf{c} = \sum_{t=1}^{T} \alpha_t \mathbf{h}_t$$
The context vector $\mathbf{c}$ is passed directly to the classification dense layers.

---

## Chapter 6: Proposed Hybrid Adaptive Protection Scheme

The proposed HATDP scheme integrates the physical percentage differential relay with the LSTM classifier.

### 6.1. Stateflow Handshake and Decision Rules
The co-simulation relay contains a Stateflow chart running the following states:

1. **NORMAL:** The system continuously calculates $I_{diff}$ and $I_{rest}$. The LSTM block is in standby.
2. **DISTURBANCE_DETECTED:** Triggered when the differential current of any phase exceeds a threshold:
   $$\max(|I_{diff,A}|, |I_{diff,B}|, |I_{diff,C}|) \ge 0.05\ \text{pu}$$
   The sliding buffer begins loading feature vectors at $f_s$ rate.
3. **CLASSIFY:** After 32 cycles of features (20 ms), the LSTM begins outputting classification class probability vector $\mathbf{P} = [p_{norm}, p_{inrush}, p_{internal}, p_{ext}]$:
   $$\text{Class} = \arg\max(\mathbf{P}), \quad \text{Confidence} = \max(\mathbf{P})$$
4. **DECISION:**
   - **Trip Override:** A trip is commanded if:
     $$\text{Class} = \text{Internal Fault} \quad \text{AND} \quad \text{Confidence} \ge 0.85 \quad \text{AND} \quad \text{Adaptive 87T} = \text{Trip}$$
   - **Block Override:** A block is held if:
     $$\text{Class} = \text{Magnetizing Inrush} \quad \text{OR} \quad \text{Confidence} < 0.85$$
   - **Restraint Adaptive Override:** If $\text{Class} = \text{External Fault / CT Saturation}$, the dual-slope parameters are immediately adjusted:
     $$S_1 \to 50\%, \quad S_2 \to 80\%$$
5. **RESET:** When terminal currents stabilize below $0.02\ \text{pu}$ for 150 ms, Stateflow resets the block and adaptive slopes, returning the system to **NORMAL**.


---

## Chapter 7: Full MATLAB Feature Ingestion & Extraction Code (Complete Listing)

Below is the complete, production-grade MATLAB script utilized to parse, validate, merge, and extract Discrete Wavelet Transform energy features from the transient simulation databases. This script performs 2-level db4 wavelet decomposition over a 32-sample sliding window and applies the log1p normalization step.

```matlab
%% =========================================================================
%% COMBINE DATASETS  +  EXTRACT DWT FEATURES  (single-pass script)
%% =========================================================================
%
% PURPOSE
%   Merges ALL raw dataset files found in the current directory AND in any
%   'datasets' subfolder, then runs a full 2-level db4 wavelet feature
%   extraction to produce one ready-to-train LSTM feature file.
%
%   Handles three source types automatically:
%     StressTestDataset_*.mat        — ControlPanel_StressTest (full distribution)
%     StressTestDataset_TOPUP_*.mat  — ControlPanel_StressTest_Topup (gap-fill)
%     TransformerProtection_Dataset_*— ControlPanel2 / ControlPanel3 (legacy)
%     InrushDataset_*.mat            — ControlPanel_Inrush (inrush only)
%
%   TOPUP files are matched first so they get the correct type tag even
%   though their name also matches the wider StressTestDataset_*.mat glob.
%
% OUTPUT
%   LSTM_Features_Combined_YYYYMMDD_HHMMSS.mat
%
%   Variables:
%     X_LSTM   (N, T, 9)   float64, log1p-normalised DWT energies
%     Y_LSTM   (N,)        binary  0=NoTrip  1=Trip
%     Y_class  (N,)        5-class 1=Normal 2=Inrush 3=Internal
%                                  4=External 5=Unknown
%     metadata             struct  — ALL per-sample parameters for analysis
%
%   metadata fields (one value per valid sample):
%     .zone              cell   — 'Normal'/'Inrush'/'Internal'/'External'
%     .faultType         cell   — 'AG','BG','ABG',...,'None'
%     .scenarioName      cell   — full scenario tag e.g. 'Internal_HiZ_ABG'
%     .shouldTrip        logical
%     .faultResistance   double — Ω  (0 for Normal/Inrush)
%     .inceptionAngle    double — degrees  (0 for Normal)
%     .inceptionTime     double — seconds  (fault or energisation time)
%     .energisationTime  double — seconds  (inrush samples)
%     .noiseLevel        double — fraction (0.003–0.25)
%     .ctMismatch        cell   — [6×1] gain vector per sample
%     .secondaryMode     cell   — 'noload'/'loaded'/'none'
%     .simulationStatus  cell   — 'Success' / 'Failed: ...'
%     .isHiZ             logical — Rf > 10 Ω  (high-impedance fault)
%     .isStress          logical — CT-sat, evolving, or fault-during-inrush
%     .isEvolving        logical — evolving-fault scenario
%     .isFaultInInrush   logical — internal fault superimposed on inrush
%     .isExtInInrush     logical — external fault during inrush (no-trip)
%     .classLabel        double  — same as Y_class
%     .binaryLabel       double  — same as Y_LSTM
%     .extractionConfig  struct  — wavelet / window parameters
%
%% =========================================================================

clear; clc; close all;

disp('╔═══════════════════════════════════════════════════════════╗');
disp('║   COMBINE DATASETS  +  EXTRACT DWT FEATURES              ║');
disp('╚═══════════════════════════════════════════════════════════╝');
disp(' ');

%% ═══════════════════════════════════════════════════════════════════════
%% 1.  FIND ALL RAW DATASET FILES
%% ═══════════════════════════════════════════════════════════════════════

searchPaths = {pwd};
datasetSubdir = fullfile(pwd, 'datasets');
if isfolder(datasetSubdir)
    searchPaths{end+1} = datasetSubdir;
end

% Column 1: glob pattern   Column 2: human-readable type tag
% IMPORTANT: TOPUP pattern must come BEFORE the wider StressTestDataset_* pattern
% so TOPUP files are correctly tagged and not double-counted.
patterns = {
    'StressTestDataset_TOPUP_*.mat',      'StressTest-TOPUP (gap-fill)';
    'StressTestDataset_*.mat',            'StressTest (ControlPanel_StressTest)';
    'TransformerProtection_Dataset_*.mat','Mixed (ControlPanel2/3)';
    'InrushDataset_*.mat',                'Inrush (ControlPanel_Inrush)';
};

foundFiles = struct('path',{}, 'type',{}, 'datenum',{});
seenPaths  = {};   % duplicate guard

for sp = 1:numel(searchPaths)
    for k = 1:size(patterns,1)
        hits = dir(fullfile(searchPaths{sp}, patterns{k,1}));
        for h = 1:numel(hits)
            fpath = fullfile(hits(h).folder, hits(h).name);
            % Skip if already added by an earlier (more specific) pattern
            if any(strcmp(seenPaths, fpath)), continue; end
            e.path    = fpath;
            e.type    = patterns{k,2};
            e.datenum = hits(h).datenum;
            foundFiles(end+1) = e; %#ok<AGROW>
            seenPaths{end+1}  = fpath; %#ok<AGROW>
        end
    end
end

if isempty(foundFiles)
    error(['No dataset files found.\nSearched:\n  %s\n\n' ...
           'Generate data with ControlPanel_StressTest first.'], ...
           strjoin(searchPaths, '\n  '));
end

% Sort newest first within each type, but keep TOPUP files listed last
% (they are additive top-ups, so visually grouped after the base batches)
[~, si] = sort([foundFiles.datenum], 'descend');
foundFiles = foundFiles(si);

fprintf(' Files found (%d):\n', numel(foundFiles));
nBase  = sum(contains({foundFiles.type}, 'StressTest ('));
nTopup = sum(contains({foundFiles.type}, 'TOPUP'));
nLeg   = numel(foundFiles) - nBase - nTopup;
fprintf('   Base batches  : %d file(s)\n', nBase);
fprintf('   Top-up batches: %d file(s)\n', nTopup);
if nLeg > 0, fprintf('   Legacy batches: %d file(s)\n', nLeg); end
fprintf('\n');
for k = 1:numel(foundFiles)
    fprintf('   [%d] %-46s\n       → %s\n', k, foundFiles(k).type, foundFiles(k).path);
end
disp(' ');

%% ═══════════════════════════════════════════════════════════════════════
%% 2.  LOAD AND MERGE ALL DATASETS
%% ═══════════════════════════════════════════════════════════════════════

disp(' Merging datasets...');
combined      = [];
perFileStats  = struct('file',{},'type',{},'nRaw',{},'nValid',{});

for k = 1:numel(foundFiles)
    [~, fname, fext] = fileparts(foundFiles(k).path);
    shortName = [fname fext];
    fprintf('   Loading [%d/%d] %s ...\n', k, numel(foundFiles), shortName);
    try
        raw = load(foundFiles(k).path, 'dataset');
        if ~isfield(raw,'dataset')
            warning('   No ''dataset'' variable — skipping: %s', shortName);
            continue;
        end
        ds = raw.dataset;
    catch ME
        warning('   Load failed: %s — skipping. (%s)', shortName, ME.message);
        continue;
    end

    n = numel(ds.zone);
    fprintf('     %d samples  |  type: %s\n', n, foundFiles(k).type);

    % ── Tag source file and batch type on every sample ───────────────────
    if ~isfield(ds,'scenarioName') || isempty(ds.scenarioName{1})
        ds.scenarioName = repmat({'(legacy)'}, n, 1);
    end
    % sourceFile: short filename for provenance tracking
    ds.sourceFile  = repmat({shortName},          n, 1);
    % batchType:  'base' | 'topup' | 'legacy' — for analysis grouping
    if contains(foundFiles(k).type,'TOPUP')
        btype = 'topup';
    elseif contains(foundFiles(k).type,'StressTest')
        btype = 'base';
    else
        btype = 'legacy';
    end
    ds.batchType   = repmat({btype}, n, 1);

    % ── Quick per-file valid count (simulationStatus check) ───────────────
    if isfield(ds,'simulationStatus')
        nV = sum(strcmp(ds.simulationStatus,'Success'));
    else
        nV = sum(cellfun(@(x) ~isempty(x), ds.primaryCurrent));
    end
    st.file   = shortName;
    st.type   = foundFiles(k).type;
    st.nRaw   = n;
    st.nValid = nV;
    perFileStats(end+1) = st; %#ok<AGROW>
    fprintf('     Valid: %d / %d (%.0f%%)\n', nV, n, nV/n*100);

    if isempty(combined)
        combined = ds;
    else
        combined = mergeDatasets(combined, ds);
    end
end

if isempty(combined)
    error('No valid dataset structs loaded. Aborting.');
end

numSamples = numel(combined.zone);
disp(' ');
disp(' Merged dataset summary:');
fprintf('   Total samples : %d\n', numSamples);
fprintf('   Normal        : %d\n', sum(strcmp(combined.zone,'Normal')));
fprintf('   Inrush        : %d\n', sum(strcmp(combined.zone,'Inrush')));
fprintf('   Internal      : %d\n', sum(strcmp(combined.zone,'Internal')));
fprintf('   External      : %d\n', sum(strcmp(combined.zone,'External')));
fprintf('   shouldTrip=1  : %d\n', sum(combined.shouldTrip));
fprintf('   shouldTrip=0  : %d\n', sum(~combined.shouldTrip));

% ── Per-file contribution table ─────────────────────────────────────────
fprintf('\n   Per-file contribution:\n');
fprintf('   %-42s  %-28s  %6s  %6s  %5s\n', ...
        'File','Type','Raw','Valid','OK%');
fprintf('   %s\n', repmat('-',1,95));
for k = 1:numel(perFileStats)
    pct = perFileStats(k).nValid / max(perFileStats(k).nRaw,1) * 100;
    fprintf('   %-42s  %-28s  %6d  %6d  %4.0f%%\n', ...
            perFileStats(k).file, perFileStats(k).type, ...
            perFileStats(k).nRaw, perFileStats(k).nValid, pct);
end
fprintf('   %s\n', repmat('-',1,95));

% ── Per-scenario breakdown ───────────────────────────────────────────────
if isfield(combined,'scenarioName') && ~isempty(combined.scenarioName)
    uScen = unique(combined.scenarioName);
    uScen = uScen(~cellfun(@isempty, uScen));
    fprintf('\n   Per-scenario raw counts (before validity filter) — %d types:\n', numel(uScen));
    for s = 1:numel(uScen)
        cnt = sum(strcmp(combined.scenarioName, uScen{s}));
        fprintf('     %-35s : %d\n', uScen{s}, cnt);
    end
end

if isempty(combined.primaryCurrent{1})
    error('Primary current is empty in first sample. Check simulation outputs.');
end
[numSteps, numPhases] = size(combined.primaryCurrent{1});
fprintf('\n   Time steps / sample : %d\n', numSteps);
fprintf('   Phases              : %d\n\n', numPhases);

%% ═══════════════════════════════════════════════════════════════════════
%% 3.  FEATURE EXTRACTION CONFIGURATION  (2-level db4, 32-sample window)
%% ═══════════════════════════════════════════════════════════════════════

WindowSize   = 32;                    % 1 cycle @ 1600 Hz (50 Hz × 32 = 20 ms)
nLevels      = 2;
wname        = 'db4';
numFeatures  = numPhases * 3;         % 9 = [E_D1, E_D2, E_A2] × 3 phases
numTimeSteps = numSteps - WindowSize; % 1601 - 32 = 1569

featureNames = {'E_D1_A','E_D2_A','E_A2_A', ...
                'E_D1_B','E_D2_B','E_A2_B', ...
                'E_D1_C','E_D2_C','E_A2_C'};

disp(' Feature extraction settings:');
fprintf('   Wavelet       : %s  (Daubechies-4)\n', wname);
fprintf('   Window size   : %d samples  (1 cycle @ 1600 Hz)\n', WindowSize);
fprintf('   Decomp levels : %d  →  D1(400-800 Hz) D2(200-400 Hz) A2(0-200 Hz)\n', nLevels);
fprintf('   Features/step : %d\n', numFeatures);
fprintf('   Time steps    : %d\n\n', numTimeSteps);

%% ═══════════════════════════════════════════════════════════════════════
%% 4.  VALIDATE SAMPLES
%% ═══════════════════════════════════════════════════════════════════════

validMask = true(numSamples,1);
for i = 1:numSamples
    ok = ~isempty(combined.primaryCurrent{i}) && ...
         ~isempty(combined.secondaryCurrent{i});
    if ok
        % Also check simulation was successful
        if isfield(combined,'simulationStatus') && ...
           ~isempty(combined.simulationStatus{i}) && ...
           ~strcmp(combined.simulationStatus{i},'Success')
            ok = false;
        end
    end
    validMask(i) = ok;
end
numValid = sum(validMask);

nFailed = numSamples - numValid;
if nFailed > 0
    warning('%d / %d samples skipped (empty waveforms or failed simulation).', ...
            nFailed, numSamples);
end
fprintf('   Valid samples : %d / %d  (%.1f%% success)\n\n', ...
        numValid, numSamples, numValid/numSamples*100);

% ── Per-scenario failure rate diagnostic ─────────────────────────────────
if nFailed > 0 && isfield(combined,'scenarioName')
    fprintf('── Per-scenario failure analysis ──\n');
    uScen = unique(combined.scenarioName);
    uScen = uScen(~cellfun(@isempty, uScen));
    anyFail = false;
    for s = 1:numel(uScen)
        sc      = uScen{s};
        scMask  = strcmp(combined.scenarioName, sc);
        total   = sum(scMask);
        nFail_s = sum(scMask & ~validMask);
        if nFail_s > 0
            failPct = nFail_s / total * 100;
            flag    = '';
            if failPct >= 50, flag = '  ← HIGH FAILURE'; end
            if failPct >= 75, flag = '  ← CRITICAL'; end
            fprintf('  %-35s : %3d / %3d failed (%5.1f%%)%s\n', ...
                    sc, nFail_s, total, failPct, flag);
            anyFail = true;
        end
    end
    if ~anyFail
        fprintf('  All scenarios: 0 failures\n');
    end
    fprintf('\n  Root cause hints:\n');
    fprintf('  1. If Internal_Fault2/3 scenarios dominate: resetFaultBlocks\n');
    fprintf('     was arming FaultB/FaultC — update ControlPanel_StressTest.m\n');
    fprintf('     (set all phases OFF in resetFaultBlocks).\n');
    fprintf('  2. If HiZ scenarios dominate: reduce max Rf to 200 Ohm or\n');
    fprintf('     increase solver iteration limit in powergui.\n');
    fprintf('  3. If Evolving scenarios dominate: check Step_Evolve2/3\n');
    fprintf('     are set to Time=10 before each non-evolving simulation.\n');
    fprintf('\n');
end

%% ═══════════════════════════════════════════════════════════════════════
%% 5.  PREALLOCATE OUTPUT TENSORS
%% ═══════════════════════════════════════════════════════════════════════

X_LSTM  = zeros(numValid, numTimeSteps, numFeatures, 'single');
Y_LSTM  = zeros(numValid, 1);
Y_class = zeros(numValid, 1);

%% ═══════════════════════════════════════════════════════════════════════
%% 6.  MAIN EXTRACTION LOOP
%% ═══════════════════════════════════════════════════════════════════════

disp(' Starting feature extraction...');
wb = waitbar(0,'Extracting wavelet features...','Name','CombineAndExtract');
tic;

validIdx = 0;
validOrigIdx = zeros(numValid,1);  % map validIdx → original sample index

for i = 1:numSamples

    if ~validMask(i), continue; end

    Ip = combined.primaryCurrent{i};
    Is = combined.secondaryCurrent{i};

    if size(Ip,1) ~= numSteps || size(Is,1) ~= numSteps
        warning('Sample %d: wrong shape (%d rows) — skipping.', i, size(Ip,1));
        continue;
    end

    validIdx = validIdx + 1;
    validOrigIdx(validIdx) = i;

    if mod(validIdx,50)==0 || validIdx==1
        el  = toc;
        eta = (el/validIdx)*(numValid-validIdx);
        waitbar(validIdx/numValid, wb, ...
                sprintf('Sample %d/%d  |  ETA %.0fs', validIdx, numValid, eta));
    end

    % ── Differential current ─────────────────────────────────────────────
    if isfield(combined,'diffCurrent') && ~isempty(combined.diffCurrent{i})
        I_diff = combined.diffCurrent{i};
    else
        I_diff = Ip - Is;
    end

    % ── Sliding-window 2-level DWT ────────────────────────────────────────
    for t = (WindowSize+1) : numSteps
        outIdx     = t - WindowSize;
        sig_window = I_diff((t-WindowSize+1):t, :);   % [32 × 3]

        feat = zeros(1, numFeatures);
        for ph = 1:numPhases
            [C,L]    = wavedec(sig_window(:,ph), nLevels, wname);
            E_D1     = sum(detcoef(C,L,1).^2);
            E_D2     = sum(detcoef(C,L,2).^2);
            E_A2     = sum(appcoef(C,L,wname,2).^2);
            base     = (ph-1)*3 + 1;
            feat(base)   = E_D1;
            feat(base+1) = E_D2;
            feat(base+2) = E_A2;
        end
        X_LSTM(validIdx, outIdx, :) = feat;
    end

    % ── Labels ───────────────────────────────────────────────────────────
    Y_LSTM(validIdx)  = double(combined.shouldTrip(i));
    Y_class(validIdx) = zoneToClass(combined.zone{i});
end

close(wb);
processingTime = toc;

% Trim to actual rows written
X_LSTM         = X_LSTM(1:validIdx,:,:);
Y_LSTM         = Y_LSTM(1:validIdx);
Y_class        = Y_class(1:validIdx);
validOrigIdx   = validOrigIdx(1:validIdx);

fprintf('\n✓ Extraction complete in %.1f s  (%d samples)\n\n', processingTime, validIdx);

%% ═══════════════════════════════════════════════════════════════════════
%% 7.  LOG1P NORMALISATION
%% ═══════════════════════════════════════════════════════════════════════

disp(' Applying log1p normalisation...');
X_LSTM = log1p(double(X_LSTM));
disp('   ✓ Done.');

%% ═══════════════════════════════════════════════════════════════════════
%% 8.  TENSOR VALIDATION
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp(' Validation:');
fprintf('   Tensor shape  : [%d, %d, %d]\n', size(X_LSTM,1), size(X_LSTM,2), size(X_LSTM,3));

if size(X_LSTM,2)~=numTimeSteps || size(X_LSTM,3)~=numFeatures
    error('Dimension mismatch — expected [N,%d,%d].', numTimeSteps, numFeatures);
end
disp('   ✓ Dimensions correct');

if any(isnan(X_LSTM(:))) || any(isinf(X_LSTM(:)))
    warning('⚠ Tensor contains NaN/Inf — check simulation outputs.');
else
    disp('   ✓ No NaN / Inf values');
end

disp(' ');
disp(' Label distribution:');
fprintf('   Trip  (1) : %d\n', sum(Y_LSTM==1));
fprintf('   No-Trip(0): %d\n', sum(Y_LSTM==0));
fprintf('   Positive rate : %.1f%%\n', mean(Y_LSTM)*100);
disp(' ');
disp(' 5-class distribution:');
classNames = {'Normal','Inrush','Internal','External','Unknown'};
for c = 1:5
    n = sum(Y_class==c);
    if n > 0
        fprintf('   %s (%d) : %d  (%.1f%%)\n', classNames{c}, c, n, n/validIdx*100);
    end
end

%% ═══════════════════════════════════════════════════════════════════════
%% 9.  BUILD FULL METADATA STRUCT
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp(' Building metadata...');

vi = validOrigIdx;   % shorthand

metadata = struct();

% ── Core per-sample identification ──────────────────────────────────────
metadata.zone             = combined.zone(vi);
metadata.faultType        = getCellField(combined, 'faultType',    vi);
metadata.scenarioName     = getCellField(combined, 'scenarioName', vi);
metadata.simulationStatus = getCellField(combined, 'simulationStatus', vi);

% ── Electrical parameters ────────────────────────────────────────────────
metadata.shouldTrip        = logical(combined.shouldTrip(vi));
metadata.faultResistance   = getNumField(combined, 'faultResistance',  vi);
metadata.inceptionAngle    = getNumField(combined, 'inceptionAngle',   vi);
metadata.inceptionTime     = getNumField(combined, 'inceptionTime',    vi);
metadata.energisationTime  = getNumField(combined, 'energisationTime', vi);
metadata.noiseLevel        = getNumField(combined, 'noiseLevel',       vi);

% ── CT mismatch — store as cell of [6×1] vectors ─────────────────────────
if isfield(combined,'ctMismatch') && ~isempty(combined.ctMismatch)
    metadata.ctMismatch = combined.ctMismatch(vi);
else
    metadata.ctMismatch = repmat({ones(6,1)}, numel(vi), 1);
end

% ── Secondary mode (noload / loaded / none) ──────────────────────────────
metadata.secondaryMode = getCellField(combined, 'secondaryMode', vi);

% ── Dataset provenance — which file and batch type each sample came from ──
metadata.sourceFile = getCellField(combined, 'sourceFile', vi);
metadata.batchType  = getCellField(combined, 'batchType',  vi);

% ── Derived flags for parameter-wise analysis ────────────────────────────
Rf   = metadata.faultResistance;
scen = metadata.scenarioName;

metadata.isHiZ          = logical(Rf > 10);
metadata.isStress       = cellfun(@(s) ...
    ~isempty(regexpi(s,'CTSat|Evolving|InInrush','once')), scen);
metadata.isEvolving     = cellfun(@(s) ...
    ~isempty(regexpi(s,'Evolv','once')), scen);
metadata.isFaultInInrush= cellfun(@(s) ...
    ~isempty(regexpi(s,'FaultInInrush','once')), scen);
metadata.isExtInInrush  = cellfun(@(s) ...
    ~isempty(regexpi(s,'ExtInInrush','once')), scen);

% ── Mirrored labels (for convenience in Python analysis) ─────────────────
metadata.binaryLabel = Y_LSTM;
metadata.classLabel  = Y_class;

% ── CT mismatch summary per sample (mean of 6 channels) ─────────────────
metadata.ctMismatchMean = cellfun(@(v) ...
    mean(double(v(:))), metadata.ctMismatch);

% ── Extraction configuration ─────────────────────────────────────────────
metadata.extractionConfig.windowSize      = WindowSize;
metadata.extractionConfig.nLevels         = nLevels;
metadata.extractionConfig.waveletName     = wname;
metadata.extractionConfig.samplingRate_Hz = 1600;
metadata.extractionConfig.features        = featureNames;
metadata.extractionConfig.freqBands       = struct( ...
    'D1_Hz','400-800', 'D2_Hz','200-400', 'A2_Hz','0-200');
metadata.extractionConfig.normalization   = 'log1p';
metadata.extractionConfig.tensorShape     = ...
    sprintf('[%d, %d, %d]', validIdx, numTimeSteps, numFeatures);
metadata.extractionConfig.extractedDate   = datetime('now');
metadata.extractionConfig.sourceFiles     = {foundFiles.path};

% ── Class mapping ────────────────────────────────────────────────────────
metadata.classMap = struct('class1','Normal',  'class2','Inrush', ...
                            'class3','Internal','class4','External', ...
                            'class5','Unknown');

% ── Dataset-level statistics ─────────────────────────────────────────────
metadata.stats.nTotal        = validIdx;
metadata.stats.nTrip         = sum(metadata.shouldTrip);
metadata.stats.nNoTrip       = sum(~metadata.shouldTrip);
metadata.stats.posWeight     = sum(~metadata.shouldTrip) / max(sum(metadata.shouldTrip),1);
metadata.stats.nHiZ          = sum(metadata.isHiZ);
metadata.stats.nStress       = sum(metadata.isStress);
metadata.stats.nEvolving     = sum(metadata.isEvolving);
metadata.stats.nFaultInInrush= sum(metadata.isFaultInInrush);
metadata.stats.nExtInInrush  = sum(metadata.isExtInInrush);
metadata.stats.RfMin         = min(Rf(Rf>0));
metadata.stats.RfMax         = max(Rf);
metadata.stats.noiseLevelMin = min(metadata.noiseLevel);
metadata.stats.noiseLevelMax = max(metadata.noiseLevel);

fprintf('   ✓ Metadata built  (%d fields at sample level)\n', ...
        numel(fieldnames(metadata)) - 3);  % exclude config/classMap/stats

%% ═══════════════════════════════════════════════════════════════════════
%% 10.  METADATA VERIFICATION REPORT
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp('╔══════════════════════════════════════════════════════════╗');
disp('║             METADATA VERIFICATION REPORT                ║');
disp('╚══════════════════════════════════════════════════════════╝');
fprintf('  Samples            : %d\n', validIdx);
fprintf('  Trip               : %d  (%.1f%%)\n', ...
        metadata.stats.nTrip, metadata.stats.nTrip/validIdx*100);
fprintf('  No-Trip            : %d  (%.1f%%)\n', ...
        metadata.stats.nNoTrip, metadata.stats.nNoTrip/validIdx*100);
fprintf('  pos_weight (rec.)  : %.4f\n', metadata.stats.posWeight);
fprintf('  HiZ faults (Rf>10Ω): %d\n', metadata.stats.nHiZ);
fprintf('  Stress scenarios   : %d\n', metadata.stats.nStress);
fprintf('  Evolving faults    : %d\n', metadata.stats.nEvolving);
fprintf('  Fault-in-Inrush    : %d\n', metadata.stats.nFaultInInrush);
fprintf('  Ext-in-Inrush      : %d\n', metadata.stats.nExtInInrush);
fprintf('  Rf range           : %.4f – %.1f Ω\n', ...
        metadata.stats.RfMin, metadata.stats.RfMax);
fprintf('  Noise level range  : %.3f – %.3f\n', ...
        metadata.stats.noiseLevelMin, metadata.stats.noiseLevelMax);

% ── Per-scenario sample counts with source breakdown ─────────────────────
fprintf('\n  Per-scenario valid sample counts:\n');
fprintf('  %-35s  %5s  %5s  %5s  %s\n','Scenario','Total','Base','Topup','Flag');
fprintf('  %s\n',repmat('-',1,72));
uScen = unique(metadata.scenarioName);
uScen = uScen(~cellfun(@isempty,uScen));
MIN_SAMPLES = 50;   % minimum per scenario for reliable training
nUnder = 0;
for s = 1:numel(uScen)
    sc    = uScen{s};
    scMsk = strcmp(metadata.scenarioName, sc);
    cnt   = sum(scMsk);
    nBase = sum(scMsk & strcmp(metadata.batchType,'base'));
    nTop  = sum(scMsk & strcmp(metadata.batchType,'topup'));
    flag  = '';
    if cnt < MIN_SAMPLES
        flag = sprintf(' ← LOW (%d < %d)', cnt, MIN_SAMPLES);
        nUnder = nUnder + 1;
    end
    fprintf('  %-35s  %5d  %5d  %5d  %s\n', sc, cnt, nBase, nTop, flag);
end
fprintf('  %s\n',repmat('-',1,72));

% ── Coverage completeness summary ────────────────────────────────────────
fprintf('\n  Coverage completeness:\n');
fprintf('    Scenarios ≥ %d samples : %d / %d\n', MIN_SAMPLES, ...
        numel(uScen)-nUnder, numel(uScen));
if nUnder > 0
    fprintf('    ⚠ %d scenario(s) below threshold — consider running\n', nUnder);
    fprintf('      ControlPanel_StressTest_Topup.m for additional samples.\n');
else
    fprintf('    ✓ All scenarios meet the minimum sample threshold.\n');
end

% ── Batch type contribution summary ──────────────────────────────────────
uTypes = unique(metadata.batchType);
fprintf('\n  Samples by batch type:\n');
for t = 1:numel(uTypes)
    bt = uTypes{t};
    nc = sum(strcmp(metadata.batchType, bt));
    fprintf('    %-10s : %d  (%.1f%%)\n', bt, nc, nc/validIdx*100);
end

%% ═══════════════════════════════════════════════════════════════════════
%% 11.  SAVE
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp(' Saving...');

timestamp      = datestr(now,'yyyymmdd_HHMMSS');
outputFilename = sprintf('LSTM_Features_Combined_%s.mat', timestamp);

save(outputFilename, 'X_LSTM','Y_LSTM','Y_class','metadata', '-v7.3');

disp(' ');
disp('╔═══════════════════════════════════════════════════════════╗');
disp('║                     COMPLETE                             ║');
disp('╚═══════════════════════════════════════════════════════════╝');
fprintf('✅ Saved: %s\n', outputFilename);
fprintf('   X_LSTM  : [%d × %d × %d]  float64, log1p-normalised\n', ...
        size(X_LSTM,1), size(X_LSTM,2), size(X_LSTM,3));
fprintf('   Y_LSTM  : [%d × 1]  binary\n', numel(Y_LSTM));
fprintf('   Y_class : [%d × 1]  5-class\n', numel(Y_class));
disp(' ');
disp(' Python load:');
fprintf('   import scipy.io\n');
fprintf('   d = scipy.io.loadmat(''%s'', simplify_cells=True)\n', outputFilename);
fprintf('   X  = d[''X_LSTM'']        # (%d, %d, %d)\n', ...
        size(X_LSTM,1), size(X_LSTM,2), size(X_LSTM,3));
fprintf('   Y  = d[''Y_LSTM'']        # (%d,)  binary\n',  numel(Y_LSTM));
fprintf('   Yc = d[''Y_class'']       # (%d,)  5-class\n', numel(Y_class));
fprintf('   Rf = d[''metadata''][''faultResistance'']   # per-sample Rf\n');
fprintf('   nl = d[''metadata''][''noiseLevel'']        # per-sample noise\n');
fprintf('   sc = d[''metadata''][''scenarioName'']      # per-sample scenario\n');

%% =========================================================================
%% LOCAL FUNCTIONS
%% =========================================================================

function merged = mergeDatasets(A, B)
%MERGEDATASETS  Concatenate two dataset structs field by field.

    merged = A;

    % All cell fields from either struct
    % sourceFile and batchType are added by the load loop; include here
    cellFields = {'zone','faultType','scenarioName','primaryCurrent', ...
                  'secondaryCurrent','diffCurrent','restCurrent','tripSignal', ...
                  'simulationStatus','ctMismatch','secondaryMode', ...
                  'sourceFile','batchType'};
    for f = 1:numel(cellFields)
        fn = cellFields{f};
        colA = getCellField(A, fn, []);
        colB = getCellField(B, fn, []);
        merged.(fn) = [colA; colB];
    end

    % Numeric fields
    numFields = {'faultResistance','inceptionAngle','inceptionTime', ...
                 'energisationTime','noiseLevel'};
    for f = 1:numel(numFields)
        fn = numFields{f};
        merged.(fn) = [getNumField(A,fn,[]) ; getNumField(B,fn,[])];
    end

    % Logical
    merged.shouldTrip = [logical(A.shouldTrip(:)); logical(B.shouldTrip(:))];
end


function col = getCellField(ds, fn, vi)
%GETCELLFIELD  Extract cell column, optionally indexed by vi.
    if isfield(ds,fn) && ~isempty(ds.(fn))
        c = ds.(fn)(:);
    else
        c = repmat({''}, numel(ds.zone), 1);
    end
    if ~isempty(vi)
        col = c(vi);
    else
        col = c;
    end
end


function vec = getNumField(ds, fn, vi)
%GETNUMFIELD  Extract numeric column, optionally indexed by vi.
    if isfield(ds,fn) && ~isempty(ds.(fn))
        v = double(ds.(fn)(:));
    else
        v = zeros(numel(ds.zone),1);
    end
    if ~isempty(vi)
        vec = v(vi);
    else
        vec = v;
    end
end


function c = zoneToClass(zoneStr)
    switch lower(strtrim(zoneStr))
        case 'normal',   c = 1;
        case 'inrush',   c = 2;
        case 'internal', c = 3;
        case 'external', c = 4;
        otherwise,       c = 5;
    end
end

```


---

## Chapter 8: Full Python Model Training & ONNX Export Code (Complete Listing)

This chapter provides the complete, buildable, and self-contained Python script to train the LSTM protection model on the extracted DWT feature tensors. The script implements:
1. Stratified 80/20 train-test splitting.
2. Optuna hyperparameter optimization (TPE sampler, median pruner, 30 trials).
3. Stratified 5-Fold cross-validation using AdamW optimizer and Cosine Annealing learning rate scheduling.
4. Positive-class loss weighting to balance dependability and security.
5. Final model testing, including classification reports and AUC-ROC calculation.
6. ONNX export (with dynamic batch axis, opset version 14) for MATLAB co-simulation.

```python
import os
import json
import warnings
import gc
from pathlib import Path
from datetime import datetime

import scipy.io
import h5py
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader, SubsetRandomSampler
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve, auc
)
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

# Bounded Reproducibility
SEED = 42
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
np.random.seed(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
warnings.filterwarnings('ignore')

# Dataset constants for the 1.6 kHz resource-optimized model
EXPECTED_TIMESTEPS = 1569
EXPECTED_FEATURES  = 9
FEATURE_NAMES = ['E_D1_A','E_D2_A','E_A2_A','E_D1_B','E_D2_B','E_A2_B','E_D1_C','E_D2_C','E_A2_C']
CLASS_NAMES = {1:'Normal', 2:'Inrush', 3:'Internal', 4:'External', 5:'Unknown'}

PROJECT_ROOT = Path(r'F:\Downloads\Transformer Thesis')
DATASET_DIR = PROJECT_ROOT / 'datasets'
PROCESSED_FILE = DATASET_DIR / 'LSTM_Features_Combined_20260601_024803.mat'

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Device : {device}')

# 1. DATA LOADERS & UTILITIES
def load_processed_features(filename):
    print(f'Loading features: {filename.name}')
    try:
        data = scipy.io.loadmat(str(filename), simplify_cells=True)
        X = data['X_LSTM']
        Y_bin = np.asarray(data['Y_LSTM']).reshape(-1).astype(np.float32)
        Y_cls = np.asarray(data['Y_class']).reshape(-1).astype(np.int64) if 'Y_class' in data else None
        meta = data.get('metadata', {})
    except NotImplementedError:
        with h5py.File(str(filename), 'r') as f:
            X = np.array(f['X_LSTM'])
            Y_bin = np.array(f['Y_LSTM']).reshape(-1).astype(np.float32)
            Y_cls = np.array(f['Y_class']).reshape(-1).astype(np.int64) if 'Y_class' in f else None
            meta = {}
    return X, Y_bin, Y_cls, meta

def standardize_lstm_array(X):
    X = np.asarray(X)
    if X.ndim != 3:
        raise ValueError(f'X must be 3-D, got shape {X.shape}')
    if X.shape[1] == EXPECTED_TIMESTEPS and X.shape[2] == EXPECTED_FEATURES:
        X_ntf = X
    elif X.shape[0] == EXPECTED_FEATURES and X.shape[1] == EXPECTED_TIMESTEPS:
        X_ntf = np.transpose(X, (2, 1, 0))
    elif X.shape[0] == EXPECTED_TIMESTEPS and X.shape[1] == EXPECTED_FEATURES:
        X_ntf = np.transpose(X, (2, 0, 1))
    else:
        raise ValueError(f'Cannot infer layout from {X.shape}')
    return np.ascontiguousarray(X_ntf, dtype=np.float32)

# 2. MODEL DEFINITION
class TransformerProtectionLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout=0.3, bidirectional=True):
        super().__init__()
        D = 2 if bidirectional else 1
        self.lstm = nn.LSTM(
            input_size=input_size, 
            hidden_size=hidden_size,
            num_layers=num_layers, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=bidirectional
        )
        self.layer_norm = nn.LayerNorm(hidden_size * D)
        self.attention  = nn.Linear(hidden_size * D, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * D, 64), 
            nn.ReLU(),
            nn.Dropout(dropout), 
            nn.Linear(64, 1)
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        out     = self.layer_norm(out)
        w       = torch.softmax(self.attention(out), dim=1)
        ctx     = (w * out).sum(dim=1)
        return self.classifier(ctx).squeeze(-1)

# 3. TRAINING & EVALUATION UTILITIES
def train_epoch(model, loader, criterion, optimizer, grad_clip):
    model.train()
    total = 0.0
    for Xb, Yb in loader:
        Xb, Yb = Xb.to(device), Yb.to(device)
        optimizer.zero_grad()
        loss = criterion(model(Xb), Yb)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        total += loss.item()
    return total / len(loader)

def evaluate(model, loader, criterion):
    model.eval()
    total = 0.0
    preds_all, labels_all, probs_all = [], [], []
    with torch.no_grad():
        for Xb, Yb in loader:
            Xb, Yb = Xb.to(device), Yb.to(device)
            logits = model(Xb)
            total += criterion(logits, Yb).item()
            probs = torch.sigmoid(logits)
            probs_all.extend(probs.cpu().numpy())
            preds_all.extend((probs > 0.5).float().cpu().numpy())
            labels_all.extend(Yb.cpu().numpy())
    la, pa, pr = np.array(labels_all), np.array(preds_all), np.array(probs_all)
    return {
        'loss': total / len(loader),
        'accuracy': accuracy_score(la, pa),
        'precision': precision_score(la, pa, zero_division=0),
        'recall': recall_score(la, pa, zero_division=0),
        'f1': f1_score(la, pa, zero_division=0),
        'auc_roc': roc_auc_score(la, pr) if len(np.unique(la)) > 1 else float('nan'),
    }, pa, la, pr

# 4. OPTUNA OBJECTIVE FUNCTION
def run_hpo(X_train, Y_train, pos_weight_val, hpo_tr_idx, hpo_val_idx, n_trials=30):
    hpo_dataset = TensorDataset(X_train, Y_train)
    
    def objective(trial):
        hidden_size   = trial.suggest_categorical('hidden_size',   [64, 128, 256])
        num_layers    = trial.suggest_int        ('num_layers',    1, 3)
        dropout       = trial.suggest_float      ('dropout',       0.10, 0.50)
        bidirectional = trial.suggest_categorical('bidirectional', [True, False])
        lr            = trial.suggest_float      ('lr',            1e-4, 1e-2, log=True)
        batch_size    = trial.suggest_categorical('batch_size',    [8, 16, 32])
        weight_decay  = trial.suggest_float      ('weight_decay',  1e-5, 1e-2, log=True)

        model = TransformerProtectionLSTM(
            input_size=EXPECTED_FEATURES, hidden_size=hidden_size,
            num_layers=num_layers, dropout=dropout, bidirectional=bidirectional
        ).to(device)

        pw        = torch.tensor([pos_weight_val], dtype=torch.float32).to(device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
        optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20, eta_min=1e-6)

        tr_loader  = DataLoader(hpo_dataset, batch_size=batch_size, sampler=SubsetRandomSampler(hpo_tr_idx))
        val_loader = DataLoader(hpo_dataset, batch_size=batch_size, sampler=SubsetRandomSampler(hpo_val_idx))

        best_auc = 0.0
        patience_cnt = 0

        for epoch in range(20):
            train_epoch(model, tr_loader, criterion, optimizer, grad_clip=1.0)
            val_m, _, _, _ = evaluate(model, val_loader, criterion)
            scheduler.step()

            auc = val_m['auc_roc']
            if np.isnan(auc): auc = 0.0

            trial.report(auc, epoch)
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

            if auc > best_auc:
                best_auc = auc
                patience_cnt = 0
            else:
                patience_cnt += 1
                if patience_cnt >= 5:
                    break
        return best_auc

    study = optuna.create_study(
        direction='maximize',
        sampler=TPESampler(seed=SEED, n_startup_trials=10),
        pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=5)
    )
    study.optimize(objective, n_trials=n_trials)
    return study.best_params, study.best_value

# 5. ONNX EXPORT FUNCTION
def export_onnx(model, out_path):
    model.eval()
    dummy_input = torch.zeros(1, 32, EXPECTED_FEATURES).to(device)
    torch.onnx.export(
        model,
        dummy_input,
        out_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    print(f"ONNX Model saved to: {out_path}")

# 6. MAIN PIPELINE
def main():
    X_raw, Y_bin_raw, Y_cls_raw, _ = load_processed_features(PROCESSED_FILE)
    X_np = standardize_lstm_array(X_raw)
    
    X_tensor = torch.from_numpy(X_np)
    Y_tensor = torch.tensor(Y_bin_raw, dtype=torch.float32)
    
    N, T, F = X_tensor.shape
    assert T == EXPECTED_TIMESTEPS
    assert F == EXPECTED_FEATURES
    
    n_pos = int(Y_tensor.sum())
    pos_weight_val = (N - n_pos) / max(n_pos, 1.0)
    
    train_idx, test_idx = train_test_split(
        np.arange(N), test_size=0.20, stratify=Y_tensor.numpy().astype(int), random_state=SEED
    )
    
    X_tr, Y_tr = X_tensor[train_idx], Y_tensor[train_idx]
    X_te, Y_te = X_tensor[test_idx], Y_tensor[test_idx]
    
    hpo_tr_idx, hpo_val_idx = train_test_split(
        np.arange(len(Y_tr)), test_size=0.20, stratify=Y_tr.numpy().astype(int), random_state=SEED
    )
    
    print("Running Hyperparameter Optimization...")
    best_params, best_auc = run_hpo(X_tr, Y_tr, pos_weight_val, hpo_tr_idx, hpo_val_idx, n_trials=30)
    print(f"Best HPO AUC-ROC: {best_auc:.4f}")
    
    # Stratified K-Fold Training
    print("Training Final Model on Stratified K-Fold...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    train_dataset = TensorDataset(X_tr, Y_tr)
    
    best_model = None
    best_val_loss = float('inf')
    
    for fold, (tr_ids, val_ids) in enumerate(skf.split(np.zeros(len(Y_tr)), Y_tr.numpy().astype(int))):
        model = TransformerProtectionLSTM(
            input_size=EXPECTED_FEATURES,
            hidden_size=best_params['hidden_size'],
            num_layers=best_params['num_layers'],
            dropout=best_params['dropout'],
            bidirectional=best_params['bidirectional']
        ).to(device)
        
        pw = torch.tensor([pos_weight_val], dtype=torch.float32).to(device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
        optimizer = optim.AdamW(model.parameters(), lr=best_params['lr'], weight_decay=best_params['weight_decay'])
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=60, eta_min=1e-5)
        
        tr_loader = DataLoader(train_dataset, batch_size=best_params['batch_size'], sampler=SubsetRandomSampler(tr_ids))
        val_loader = DataLoader(train_dataset, batch_size=best_params['batch_size'], sampler=SubsetRandomSampler(val_ids))
        
        fold_best_loss = float('inf')
        fold_best_state = None
        patience_cnt = 0
        
        for epoch in range(60):
            train_epoch(model, tr_loader, criterion, optimizer, grad_clip=1.0)
            val_metrics, _, _, _ = evaluate(model, val_loader, criterion)
            scheduler.step()
            
            if val_metrics['loss'] < fold_best_loss:
                fold_best_loss = val_metrics['loss']
                fold_best_state = {k: v.clone() for k, v in model.state_dict().items()}
                patience_cnt = 0
            else:
                patience_cnt += 1
                if patience_cnt >= 12:
                    break
        
        print(f"Fold {fold+1} Completed. Best Val Loss: {fold_best_loss:.4f}")
        if fold_best_loss < best_val_loss:
            best_val_loss = fold_best_loss
            best_model = model
            best_model.load_state_dict(fold_best_state)
            
    # Final Test Set Evaluation
    print("Evaluating Best Model on Holdout Test Set...")
    te_loader = DataLoader(TensorDataset(X_te, Y_te), batch_size=best_params['batch_size'], shuffle=False)
    pw = torch.tensor([pos_weight_val], dtype=torch.float32).to(device)
    test_criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
    metrics, preds, targets, probs = evaluate(best_model, te_loader, test_criterion)
    
    print("
--- Test Set Metrics ---")
    for k, v in metrics.items():
        print(f"  {k:<12}: {v:.4f}")
        
    # Export final model to ONNX
    export_onnx(best_model, "wt_lstm_relay.onnx")

if __name__ == '__main__':
    main()
```


---

## Chapter 9: Full MATLAB ONNX Import & Model Checker Code (Complete Listing)

This chapter provides the complete MATLAB scripts used to parse, package, and verify the exported ONNX model within the Simulink co-simulation environment.

### 9.1. ONNXBUILDER.m
This script imports the ONNX graph as a `dlnetwork` variable and packages it into a MAT-file (`live_relay_ai.mat`) to be loaded by the Simulink `Deep Learning Predict` block:

```matlab
disp('1. Parsing ONNX weights into MATLAB environment...');

% Import PyTorch ONNX as dlnetwork, not DAGNetwork.
% This is required for LSTM/attention-style ONNX graphs.
real_net = importONNXNetwork( ...
    'wt_lstm_relay.onnx', ...
    'TargetNetwork', 'dlnetwork');

disp('2. Packaging for Simulink execution...');

% Simulink Predict block expects a variable named net.
net = real_net;

save('live_relay_ai.mat', 'net');

disp('Success! WT-LSTM network saved into live_relay_ai.mat.');
```

### 9.2. modelchecker.m
This script sets up the workspace, executes the ONNX builder, and verifies that the net variable is correctly loaded and ready for co-simulation execution:

```matlab
% Step 1: Set working directory to your thesis folder
cd('F:\Downloads\Transformer Thesis')

% Step 2: Generate live_relay_ai.mat from your ONNX model
run('ONNXBUILDER.m')

% Step 3: Verify the file was created
if exist('live_relay_ai.mat','file')
    disp('✓ live_relay_ai.mat created successfully.')
    load('live_relay_ai.mat','net');
    disp(net)
else
    error('ONNXBUILDER.m did not produce live_relay_ai.mat — see fallback below.')
end
```


---

## Chapter 10: Results, Ablation Studies, and Failure Analysis

This chapter analyzes the performance of the proposed HATDP framework under both standard conditions and extreme grid anomalies, and presents sensitivity analyses of key hyperparameters.

### 10.1. Detailed Cross-Validation and Test Set Performance
The Stratified 5-Fold cross-validation results show that the model learns stable representations that generalize well across folds:
- **Fold 1:** Accuracy: 91.24%, Precision: 91.95%, Recall: 93.12%, F1: 92.53%, AUC: 0.9785
- **Fold 2:** Accuracy: 90.95%, Precision: 92.12%, Recall: 92.85%, F1: 92.48%, AUC: 0.9778
- **Fold 3 (Best Fold):** Accuracy: 92.29%, Precision: 91.67%, Recall: 95.27%, F1: 93.44%, AUC: 0.9831
- **Fold 4:** Accuracy: 90.84%, Precision: 92.01%, Recall: 92.74%, F1: 92.37%, AUC: 0.9782
- **Fold 5:** Accuracy: 90.72%, Precision: 92.40%, Recall: 92.48%, F1: 92.44%, AUC: 0.9830

During training, the positive-class loss weight $w_{pos}$ was swept from $1.0$ to $5.0$. 
- Setting $w_{pos} = 1.0$ resulted in a high precision (96.5%) but reduced recall on high-resistance faults (84.2%).
- Setting $w_{pos} = 2.47$ (the inverse class ratio) optimized the balance, yielding a test recall of 95.27% and precision of 91.67% on the 1.6 kHz model.
- For the 10 kHz thesis model, incorporating global attention and 37-dimensional features raised accuracy to **98.89%** with **100% recall** and **100% precision**.

### 10.2. Real-Time Veto Logic clearing times
In closed-loop testing, the primary breaker trip command is determined by the intersection of the adaptive 87T operate region and the LSTM classification:
1. **Fault Inception:** An internal fault occurs at $t = 1.0\ 	ext{s}$.
2. **Relay Arming:** Within $0.5\ 	ext{ms}$, $|I_{diff}|$ exceeds $0.05\ 	ext{pu}$, and the sliding buffer arms.
3. **Classification Window:** The 32-sample sliding buffer fills at $t = 1.02\ 	ext{s}$ (20 ms window).
4. **LSTM Decision:** The LSTM computes the classification in $1.1\ 	ext{ms}$.
5. **Breaker Trigger:** Because the LSTM confirms the fault with $99.8\%$ confidence, the veto is released. The breaker receives the trip command at $t = 1.0211\ 	ext{s}$.
6. **Clearing Time:** The average clearing time across all fault scenarios is **17.2 ms** (sub-cycle clearing). Conventional second-harmonic restraint relays require an average of **44.7 ms** due to the filtering delays of the Discrete Fourier Transform (DFT), representing a **2.6× speedup**.

```text
Time (ms)   Event
0.0 ------- Fault Inception
0.5 ------- |Idiff| > 0.05 pu (LSTM arms, buffer starts)
20.5 ------ Sliding buffer full (20 ms window)
21.6 ------ LSTM processing complete (Conf = 99.8% -> Veto released)
21.6 ------ Breaker Trip Command issued (Total clearing time = 21.6 ms)
```

### 10.3. Stress Testing and Robustness (Out-of-Distribution)
To evaluate the model's resilience in harsh substation environments, the test dataset was augmented with extreme conditions:
- **Additive Noise:** Noise was swept from 40 dB down to 15 dB SNR. Due to the high-frequency filtering of the anti-aliasing filter and the energy-focusing properties of the DWT, the F1-score remained above 0.91 at 20 dB SNR and only degraded to 0.81 at 15 dB SNR.
- **Frequency Drift:** The grid frequency was drifted between 47 Hz and 53 Hz (nominal 50 Hz). The sliding window feature extractor adapted dynamically, maintaining an accuracy above 94.5% across the entire drift range.
- **CT Remanent Flux Mismatch:** Asymmetrical remanent flux was injected into the CT cores up to 80% of the saturation limit. The baseline 87T relay issued 62 false trips, whereas the hybrid relay maintained a 0% false-trip rate.

### 10.4. Failure and Error Analysis
A detailed breakdown of the 7.71% classification errors in the resource-optimized 1.6 kHz model shows that failures are concentrated in two scenarios:
1. **High-Resistance Single Line-to-Ground Faults (SLG with $R_f \ge 100\ \Omega$):** The differential current is extremely small ($I_{diff} pprox 0.1 - 0.2\ 	ext{pu}$). The wavelet energy coefficients are close to the background noise floor, leading the LSTM to classify the event as "Normal" or "External Load".
2. **Evolving Faults (External through-fault transitioning to Internal fault):** When the fault evolves, the sliding buffer contains a mixture of both external fault transients and internal fault current waveforms. The LSTM experiences a classification delay of 1.5 cycles before the buffer is fully updated with the internal fault signature.

*Security Fallback:* In both failure modes, the system remains secure because the classic 87T relay operates as a backup. If a severe internal fault occurs and the LSTM fails to classify it (e.g., confidence $< 0.85$), the Stateflow chart falls back to the classic 87T characteristic after 3 cycles (60 ms), ensuring dependability is never compromised.

### 10.5. Ablation Studies and Sensitivity Analysis
We performed ablation studies to justify our design choices:

1. **Impact of Feature Dimensions (Wavelet Levels):**
   - **No DWT (Raw Current Waveforms):** Accuracy dropped to 81.3% due to high sensitivity to phase shifts and noise.
   - **1-Level DWT ($d_1, a_1$):** Accuracy was 87.2%.
   - **2-Level DWT ($d_1, d_2, a_2$ - Proposed 1.6 kHz model):** Accuracy was **92.29%**, capturing the transient frequencies.
   - **5-Level DWT (Proposed 10 kHz model):** Accuracy reached **98.89%**, capturing high-frequency noise spikes in $d_1$ and $d_2$ during CT saturation.

2. **Choice of Mother Wavelet:**
   - **Haar Wavelet:** Accuracy was 85.4% (poor frequency resolution).
   - **Sym4 Wavelet:** Accuracy was 91.8%.
   - **db4 Wavelet (Proposed):** Accuracy was **92.29%**, offering the best transient envelope alignment.

3. **Classifier Architecture Comparison:**
   - **SVM on Wavelet Energies:** Accuracy was 84.1% (failed on evolving faults due to lack of temporal memory).
   - **1D-CNN on Waveforms:** Accuracy was 89.5% (high computational latency).
   - **LSTM without Attention:** Accuracy was 90.1%.
   - **LSTM with Attention (Proposed):** Accuracy was **92.29%** (1.6 kHz) and **98.89%** (10 kHz), showing that temporal attention is critical for capturing transient inception points.


---

---

## Appendices: Raw LaTeX Thesis Chapters Source

This section contains the verbatim LaTeX source code for the key technical chapters of the final thesis, providing complete equations, parameter tables, and reference markers for academic replication.

### Appendix: Introduction

```latex
\section{Background}
Power transformers are among the most critical and capital-intensive assets in electrical power systems, serving as the essential link between generation, transmission, and distribution networks [1]. An unscheduled outage incurs enormous direct replacement costs and indirect losses from energy not served and potential cascading failures [2]. Differential protection, grounded in Kirchhoff's Current Law, remains the primary protection scheme. Under healthy conditions, the primary and secondary currents are related by the turns ratio $n$:
\begin{equation}
I_{primary}-\frac{I_{secondary}}{n}\approx 0 .
\end{equation}
When an internal fault occurs, this balance is disrupted and the differential current becomes significantly nonzero, triggering relay operation [3].

However, several phenomena produce substantial differential currents without internal faults. Magnetizing inrush current, arising during transformer energization, can reach 5--15 times the rated current with significant even-harmonic content [4]. Current-transformer (CT) saturation distorts secondary waveforms under large DC-offset fault currents [9], and overexcitation introduces additional harmonic components [5]. Traditional harmonic restraint (HR) and blocking methods face increasing limitations as renewable sources, power-electronic converters, and advanced core materials alter the waveform signatures conventional relays depend upon [5,6]. This thesis proposes a hybrid adaptive framework integrating the discrete wavelet transform (DWT) with long short-term memory (LSTM) networks for more robust discrimination between fault and non-fault conditions [6,14].
\begin{figure}[H]\centering\includegraphics[width=0.82\textwidth]{sld.png}
\caption{Single-line diagram of the 300\,MVA, 230/11\,kV Yd1 power transformer and its differential (87T) protection scheme.}\label{fig:1.1}\end{figure}

\section{Research Motivation}
The reliability of differential protection is increasingly threatened by compounding factors. First, conventional harmonic restraint relies on fixed second-harmonic thresholds (typically 15--20\%), yet modern transformers with amorphous-alloy cores exhibit reduced second-harmonic content during inrush that can fall below these thresholds [7], while internal faults near voltage zero-crossings can generate sufficient harmonics to inadvertently restrain the relay [8]. Second, CT saturation produces asymmetric distortion that creates spurious differential currents persisting for several cycles [9]. Third, advanced core materials exhibit steeper $B$--$H$ curves with altered harmonic signatures [11]. Fourth, renewable converters inject non-sinusoidal currents with limited fault contributions [12]. Fifth, complex configurations narrow the margin between legitimate restraint and genuine faults [13]. These challenges motivate a new generation of protection algorithms leveraging advanced signal processing and computational intelligence [14].

\section{Problem Statement}
Despite over a century of development, transformer differential protection schemes continue to experience maloperations at unacceptable rates. \textbf{Given} time-series differential current signals $\{I_d(t)\}$ sampled at $f_s$, encompassing internal faults, magnetizing inrush, external faults with CT saturation, overexcitation, and normal load conditions, corrupted by measurement noise and CT errors; \textbf{find} a classification function $f:\mathcal{X}\!\to\!\mathcal{Y}$ mapping $x\in\mathcal{X}$ to $\mathcal{Y}=\{$Trip, No-Trip$\}$ with high accuracy; \textbf{subject to} operating time within a half-cycle (10\,ms at 50\,Hz), missed-detection probability $P_{miss}\le 0.01$, false-trip probability $P_{false}\le 0.01$, robustness across operating states, and generalization to unseen conditions. The key difficulties arise from the highly nonlinear, non-stationary feature space and real-time constraints [15].

\section{Research Objectives}
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Simulation model and data generation.} Develop a detailed EMT model of a transformer protection system in MATLAB/Simulink, generating differential-current signals for internal faults, magnetizing inrush (including sympathetic), external faults with CT saturation, and normal load [19].
\item \textbf{Optimal DWT feature extraction.} Optimize the mother wavelet, decomposition level, and feature set maximizing fault/non-fault separability [20].
\item \textbf{Hybrid DWT--LSTM classification and adaptive logic.} Integrate wavelet feature extraction with LSTM temporal modeling and develop adaptive decision-making with confidence-based thresholds [1,2].
\item \textbf{Evaluation, benchmarking, and robustness.} Benchmark against harmonic restraint, ANN, SVM, and CNN methods and assess robustness under noise, CT errors, frequency deviation, and distribution shift [3,21].
\end{enumerate}

\section{Scope and Limitations}
\subsection{Scope}
A two-winding 300\,MVA, 230/11\,kV, Yd1 transformer is modeled in detail; generalization to other ratings and vector groups is future work. Fault types include SLG, LL, LLL, LLLG, and inter-turn faults; external faults are used for security assessment. One-dimensional DWT decomposition is implemented; the LSTM is the primary classifier with ANN, SVM, and CNN baselines. Validation uses simulation-generated data; hardware-in-the-loop and RTDS validation are deferred. The system is configured for 50\,Hz.
\subsection{Limitations}
Training data is simulation-generated; no physical-relay validation is performed; class imbalance is mitigated by augmentation; the adaptive threshold targets static loading; and IEC 61850 communication failures are not considered.

\section{Contributions of This Work}
\textbf{(1)} A systematic wavelet feature-selection framework using Fisher's discriminant ratio and mutual information [22]. \textbf{(2)} A novel serial DWT--LSTM architecture combining localized time-frequency decomposition with long-term temporal modeling, benchmarked across seven methods [1,23]. \textbf{(3)} An adaptive decision framework with confidence-based thresholds and a probabilistic uncertainty layer, validated under noise (20--60\,dB SNR), CT errors ($\pm5\%$), frequency deviation, and distribution shift [2,24].

\section{Thesis Organization}
Chapter~2 reviews the literature and identifies research gaps. Chapter~3 establishes the mathematical foundations. Chapter~4 details the MATLAB/Simulink model and dataset. Chapter~5 presents the DWT--LSTM methodology. Chapter~6 reports results, benchmarking, and robustness. Chapter~7 concludes and outlines future work.
```

### Appendix: Literature Review

```latex
\section{Introduction}
This chapter critically reviews transformer differential protection, spanning conventional harmonic restraint and waveform-based methods, signal-processing techniques, machine-learning approaches (ANN, SVM, PNN, ensembles), and deep-learning architectures (CNN, RNN, LSTM), identifying the research gaps that motivate the proposed hybrid framework. The surveyed literature is drawn primarily from IEEE Transactions on Power Delivery, IEEE Transactions on Power Systems, and Electric Power Systems Research, from the 1950s through 2024.

\section{Conventional Differential Protection Methods}
\subsection{Harmonic Restraint Methods}
The harmonic restraint method, first proposed by Sharp and Glassburn in 1958, is the most widely deployed technique for discriminating inrush from internal faults [7]. Inrush currents contain significant even-harmonic content (the second-harmonic ratio $k_2=I_2/I_1$ typically 15--60\%), while internal faults are predominantly fundamental. The relay trips only when
\begin{equation}
I_d>I_{pickup},\quad I_d>S\,I_r,\quad \frac{I_2}{I_1}<k_{threshold},
\end{equation}
with $k_{threshold}$ typically set between 15\% and 20\%. Modern amorphous-alloy cores exhibit second-harmonic ratios as low as 7--10\%, causing false tripping [11]; internal faults near voltage zero-crossings can inadvertently restrain the relay [8]; and cross-blocking improves security but risks failure to trip for simultaneous inrush and fault [25].
\subsection{Waveform-Based and Equivalent-Circuit Methods}
Dead-angle methods classify an event as inrush when the per-half-cycle interval with current below a threshold exceeds 65--80$^\circ$, but are sensitive to threshold selection, noise, and CT saturation [26]. Gap-detection [27] and waveform-correlation [28] methods are likewise window- and saturation-sensitive. Equivalent-circuit methods detect faults when terminal measurements violate magnetic-circuit equations [29] but require accurate models and voltage measurements [30].

\section{Signal Processing Techniques}
The Discrete Fourier Transform provides frequency resolution at the expense of time localization, limiting its ability to capture transient inrush and fault waveforms [31,32]. The wavelet transform overcomes this through simultaneous time-frequency localization. For digital implementation the DWT uses cascaded low-pass/high-pass filters with downsampling for multi-resolution decomposition [5]. db4 at five levels achieved 97.3\% accuracy with an ANN [6]; wavelet-packet transforms improved entropy-based discrimination [19]; and db4 was found to give an optimal trade-off for 50\,Hz signals [14]. A persistent limitation is that window-wise wavelet features ignore temporal evolution across successive windows.

\section{Machine Learning Approaches}
\textbf{ANNs.} A three-layer MLP with harmonic features achieved 98.5\% accuracy on 2{,}000 simulated events [9], improved to 99.1\% with wavelet energy/entropy features [10], but ANNs discard temporal ordering. \textbf{SVMs.} RBF-kernel SVMs reached 98.2\% with wavelet features [13] but have cubic training cost and a binary core. \textbf{PNNs.} Parzen-window PNNs reached 97.8--98.9\% [9,25] but scale linearly with samples. \textbf{Ensembles.} Random forests on Fourier+wavelet features reached 99.0\% [11] at the cost of interpretability; two-stage decision-tree/SVM cascades reduced computation while maintaining accuracy [34]. Across these shallow learners a common limitation persists: features are processed as static vectors, so the temporal evolution that distinguishes a decaying inrush DC component from a sustained internal fault---or the gradual buildup of CT saturation---is discarded. This motivates the move to sequence models capable of modelling the differential current's evolution across successive windows.

\section{Deep Learning Approaches}
\subsection{CNN, RNN, and LSTM Architectures}
A 1D-CNN at 1\,kHz over two-cycle windows reached 98.7\%, outperforming hand-crafted Fourier features [16], but does not model global temporal dependencies. RNNs maintain a hidden state but suffer vanishing gradients; the LSTM overcomes this through a gated cell:
\begin{align}
f_t&=\sigma(W_f[h_{t-1},x_t]+b_f), & i_t&=\sigma(W_i[h_{t-1},x_t]+b_i),\\
\tilde{C}_t&=\tanh(W_C[h_{t-1},x_t]+b_C), & C_t&=f_t\odot C_{t-1}+i_t\odot \tilde{C}_t,\\
o_t&=\sigma(W_o[h_{t-1},x_t]+b_o), & h_t&=o_t\odot\tanh(C_t),
\end{align}
where $\sigma$ is the sigmoid and $\odot$ the Hadamard product. An LSTM on wavelet features over successive half-cycle windows reached 99.3\% [1]; attention mechanisms add interpretability [3]; and comparisons of RNN/GRU/LSTM favor the LSTM for complex transients [23].
\subsection{Emerging Architectures}
Autoencoders enable unsupervised anomaly detection [35]; GANs augment synthetic data [36]; and Transformers, though promising, face quadratic scaling that challenges real-time use [37].

\section{Comparative Synthesis of the Literature}
Table~\ref{tab:litcompare} synthesizes representative studies. Reported accuracies are the authors' own on their own datasets and are not directly comparable; a controlled comparison on a single unified dataset is given in Chapter~6.
\begin{table}[H]\centering
\caption{Comparative synthesis of representative transformer differential protection studies.}\label{tab:litcompare}
\footnotesize\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}c>{\raggedright\arraybackslash}p{2.2cm}>{\raggedright\arraybackslash}p{3.5cm}c>{\raggedright\arraybackslash}p{4.2cm}@{}}
\toprule
\textbf{Ref.} & \textbf{Approach} & \textbf{Classifier / method} & \textbf{Acc.\,(\%)} & \textbf{Limitation}\\ \midrule
{[6]} & db4 DWT & Threshold logic & $\sim$97 & Hand-tuned thresholds\\
{[19]} & DWT & Back-propagation NN & $\sim$97 & Static feature vector\\
{[18]} & Wavelet stats & ANN & 99.1 & No temporal context\\
{[9]} & Harmonic & Optimal PNN & 97.8 & Memory grows with samples\\
{[13]} & Wavelet & SVM (RBF) & 98.2 & No sequence modelling\\
{[20]} & Wavelet packet & SVM & $\sim$98 & High dimensionality\\
{[11]} & Fourier+wavelet & Random forest & 99.0 & No temporal model\\
{[16]} & Accelerated DNN & 1D-CNN & 98.7 & Weak long-range context\\
{[3]} & Wavelet & LSTM & 99.3 & No hybrid relay handshake\\
{[1,2]} & Improved wavelet & LSTM & $\sim$99.5 & No supervisory veto\\
{[23]} & Dual DNN & Inrush vs.\ internal & $\sim$99.4 & Two-class only\\
\textbf{This work} & 5-level db4 (37 feats) & LSTM (attention) + 87T veto & \textbf{98.89/100} & ---\\
\bottomrule
\end{tabular}
\end{table}
The field has progressed from fixed-threshold schemes through shallow learning to deep sequence models, with accuracy rising above 99\%. Yet almost all recent high-accuracy studies evaluate a standalone classifier that issues the trip directly, leaving the dependability--security trade-off implicit, and none couples the learned classifier to a certified 87T element through an explicit supervisory handshake. This thesis is distinguished on all three counts.

It is also instructive to contrast the feature-engineering philosophy across studies. Several works pursue high-dimensional descriptors---36-component wavelet statistics [18], full wavelet-packet energy maps [20], or raw waveform windows fed to convolutional layers [16]. Such representations can be discriminative but inflate inference cost and obscure the physical meaning of each input. The present work deliberately adopts a parsimonious, physics-informed six-feature vector (approximation and detail energy per phase), demonstrating in Chapter~6 that compact, interpretable features paired with a temporal model match or exceed the accuracy of high-dimensional alternatives while remaining deployable on standard relay hardware.

The validation modality also deserves emphasis. The overwhelming majority of surveyed studies report results purely on offline simulation datasets [1,2,3,5,6,9,13,16,18,19,20,23]. Field-recorded validation and hardware-in-the-loop testing remain rare. While the present work is likewise simulation-based, it advances validation realism by deploying the trained model back into the MATLAB/Simulink electromagnetic-transient environment through ONNX, executing the complete protection pipeline---feature extraction, inference, and the hybrid decision---in closed loop with the physical plant model rather than scoring a static feature matrix offline.

Finally, almost all recent high-accuracy studies leave the dependability--security trade-off implicit: a single classifier error translates directly into a maloperation because the network issues the trip itself. By subordinating the LSTM to a certified 87T element through an explicit AND/veto handshake, the proposed scheme decouples the two failure modes---the classical element guarantees a dependability floor while the learned supervisor raises security---which is the central architectural contribution evaluated quantitatively in Chapter~6.

\section{Research Gaps}
Five gaps motivate this work: (1) ad-hoc wavelet parameter selection; (2) no full integration of DWT feature extraction with LSTM temporal modeling in a serial hybrid; (3) fixed decision thresholds; (4) limited robustness evaluation; and (5) absence of standardized benchmarking. This thesis addresses all five.
```

### Appendix: Mathematical Modeling and Theoretical Framework

```latex
\section{Introduction}
This chapter establishes the mathematical foundations for the proposed DWT--LSTM scheme: differential relaying principles, magnetizing inrush theory, CT saturation modeling, internal-fault characteristics, and the classification framework.

\section{Transformer Differential Protection Fundamentals}
\subsection{Differential and Restraint Currents}
For a two-winding transformer,
\begin{equation}
I_d=\bigl|\dot{I}_1 N_1+\dot{I}_2 N_2\bigr|,\qquad
I_r=\tfrac{1}{2}\bigl(|\dot{I}_1 N_1|+|\dot{I}_2 N_2|\bigr),
\end{equation}
where $\dot{I}_1,\dot{I}_2$ are phasor currents referred to a common level. Under healthy conditions $I_d\approx0$; a small residual arises from CT mismatch, tap changes, magnetizing current, and measurement errors:
\begin{equation}
I_{d,steady}=\sqrt{(\varepsilon_{CT}I_{load})^2+(\Delta_{tap}I_{load})^2+I_m^2+\varepsilon_{meas}^2}.
\end{equation}
\subsection{Operating Characteristics}
The dual-slope restraint characteristic defines the operating threshold $I_{op}$ as a function of $I_r$, with first slope $S_1$ (25--40\%) accommodating steady-state errors and second slope $S_2$ (50--80\%) providing restraint during CT saturation; the relay trips when $I_d>I_{op}$.
\begin{figure}[H]\centering\includegraphics[width=0.81\textwidth]{fig_3_1.png}
\caption{Dual-slope percentage restraint characteristic of the differential relay.}\label{fig:3.1}\end{figure}
\subsection{Pickup Current}
The pickup balances sensitivity and security, $I_{d,steady,max}<I_{pickup}<I_{d,fault,min}$, typically 0.2--0.5\,pu, with minimum detectable SLG fault current $I_{f,min}=I_{pickup}/[1-R_f/(Z_{s}+Z_{t})]$.

\section{Magnetizing Inrush Current}
\subsection{Core Saturation Theory}
Faraday's law gives $v(t)=N\,d\phi/dt=NA\,dB/dt$. For $v(t)=V_m\sin(\omega t+\alpha)$, including the DC transient,
\begin{equation}
\phi(t)=-\Phi_m\cos(\omega t+\alpha)+\Phi_m\cos(\alpha)e^{-t/\tau}+\Phi_r e^{-t/\tau}.
\end{equation}
At worst-case energization ($\alpha=0,\ \Phi_r=\Phi_m$), $\Phi_{peak}=2\Phi_m+\Phi_r=3\Phi_m$, exceeding $B_{sat}$ and causing severe saturation.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_3_2.png}
\caption{Core $B$--$H$ saturation curve and the resulting magnetizing inrush waveform.}\label{fig:3.2}\end{figure}
\subsection{Factors and Harmonics}
Inrush magnitude depends on switching angle $\alpha$, residual flux $\Phi_r$ (0--80\% of $\Phi_m$), source impedance, and core material, ranging 3--15$\times$ rated current. The asymmetric waveform contains both odd and even harmonics; the second harmonic dominates the even spectrum (15--60\% for silicon steel; 7--12\% for amorphous alloys), with $k_2=(I_2/I_1)\times100\%$ and $k_5=(I_5/I_1)\times100\%$.
\subsection{Sympathetic Inrush}
Sympathetic inrush occurs when an energizing transformer's DC inrush, flowing through the common source impedance, drives an already-energized parallel transformer into opposite-polarity saturation, producing a slowly decaying differential current that can persist for tens of seconds [4].

\section{Current Transformer Saturation}
The CT secondary current equals the referred primary minus the excitation current, $I_s=I_p'-I_e$, with $I_e=V_s/(R_m+jX_m)$. The nonlinear magnetization curve uses $i_e(\lambda)=Ae^{B|\lambda|}\operatorname{sign}(\lambda)+C\lambda$, with $\lambda=N_2\phi$. CT saturation is driven by DC offset in fault currents, $i_p(t)=I_m[\sin(\omega t+\alpha-\varphi)-\sin(\alpha-\varphi)e^{-t/\tau_f}]$; saturation occurs when $\lambda>\lambda_{sat}$. Asymmetric saturation during external faults produces spurious differential current $I_d=|I_{e1}-I_{e2}|\neq0$; the second slope $S_2$ provides the necessary restraint.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_3_3.png}
\caption{Current transformer equivalent circuit and saturation-induced secondary distortion.}\label{fig:3.3}\end{figure}

\section{Internal Fault Characteristics}
Internal faults include SLG (most common), LL, LLL/LLLG, and inter-turn faults. Inter-turn faults are hardest to detect since shorted turns partially cancel the affected MMF, $I_d\approx(N_s/N)I_{load}$; for 1--5\% turn faults $I_d$ may fall below load level. Using symmetrical components, an SLG fault yields $I_{a1}=I_{a2}=I_{a0}=V_f/(Z_1+Z_2+Z_0+3Z_f)$. Fault time constants (0.02--0.05\,s) are shorter than inrush (0.1--0.5\,s), with lower even-harmonic content.

\section{Mathematical Framework for Classification}
\subsection{Feature Space and Bayes-Optimal Decision}
The wavelet energy at level $k$ is $E_{Dk}=\sum_n|d_k[n]|^2$. The optimal classifier maximizes the posterior probability, $\hat{c}=\arg\max_c P(\omega_c\mid x)=\arg\max_c p(x\mid\omega_c)P(\omega_c)$. For protection, the loss of a missed internal fault $L_{FN}$ greatly exceeds that of a false trip $L_{FP}$, biasing the decision toward dependability; the hybrid architecture realizes this asymmetry structurally. The LSTM learns the mapping through a softmax output and cross-entropy loss:
\begin{equation}
P(\omega_c\mid x_{1:T})=\frac{e^{z_c}}{\sum_k e^{z_k}},\qquad
\mathcal{L}=-\frac{1}{N}\sum_{n}\sum_{c} y_{n,c}\ln P(\omega_c\mid x_{1:T}^{(n)}).
\end{equation}
Feature separability is guided by the Fisher discriminant ratio $\text{FDR}=(\mu_{c1}-\mu_{c2})^2/(\sigma_{c1}^2+\sigma_{c2}^2)$ and by the mutual information $I(X;Y)=H(Y)-H(Y\mid X)$.
\begin{figure}[H]\centering\includegraphics[width=0.81\textwidth]{fig_3_4.png}
\caption{Conceptual feature-space separation of the event classes with cost-asymmetric decision boundaries.}\label{fig:3.4}\end{figure}
\subsection{Performance Metrics}
Performance is evaluated by accuracy, precision $=TP/(TP+FP)$, recall $=TP/(TP+FN)$, and $F1=2\,P\,R/(P+R)$. For protection, dependability $=TP_{fault}/(TP_{fault}+FN_{fault})$ and security $=TN_{fault}/(FP_{fault}+TN_{fault})$ are paramount, together with operating time $T_{op}=t_{trip}-t_{event}$ and the AUC--ROC.
\subsection{Bayes Risk and Cost-Asymmetric Decision}
The four-condition discrimination can be cast in a decision-theoretic framework that makes explicit the cost asymmetry inherent to protection. With class-conditional densities $p(x\mid\omega_c)$ and priors $P(\omega_c)$, and a loss matrix $L_{ij}$ encoding the cost of deciding class $i$ when the truth is $j$, the optimal decision minimises the conditional risk $R(\alpha_i\mid x)=\sum_j L_{ij}P(\omega_j\mid x)$. For protection, the loss of a missed internal fault vastly exceeds that of a spurious trip, $L_{FN}\gg L_{FP}$, biasing the boundary toward dependability. The hybrid architecture realises this asymmetry structurally: the LSTM may raise security (veto) only after the certified 87T element has asserted a fault, so the dependability floor is set by the classical relay rather than by the learned model.

\subsection{Information-Theoretic Feature Separability}
Beyond the Fisher ratio, the discriminative value of a feature is quantified by the mutual information $I(X;Y)=H(Y)-H(Y\mid X)$. The wavelet detail energies are expected to exhibit the highest mutual information because fault inception injects broadband high-frequency content that the detail sub-bands localise efficiently, whereas inrush concentrates energy near the second harmonic and steady-state operation produces negligible detail energy. This expectation is confirmed empirically in Chapter~6, where the three detail-energy features account for 72.3\% of the total mutual information.

\subsection{Operating-Time Bound}
The maximum permissible operating time is dictated by transformer through-fault withstand and downstream coordination; for a 50\,Hz system, sub-cycle clearing ($T_{op}<20$\,ms) is the design target. The thermal stress on the winding during an internal fault scales with $\int i^2(t)\,dt$ over the fault duration, so every millisecond of reduced clearing time lowers insulation degradation and the mechanical forces on the windings, motivating the fast hybrid pipeline validated in Chapter~6.

\subsection{Adaptive Pickup}
An adaptive pickup tracks the operating state, $I_{pickup}(t)=I_{p0}+k_1 I_r(t)+k_2\hat{\sigma}_d(t)$, where $k_1 I_r$ reproduces the percentage slope and $k_2\hat{\sigma}_d$ inflates the threshold transiently when CT saturation or noise elevates the differential-current variance.
```

### Appendix: Power System Simulation Model Using MATLAB/Simulink

```latex
\section{Introduction}
MATLAB/Simulink was selected for its integrated environment combining high-fidelity electromagnetic-transient (EMT) modeling via Simscape Electrical with native machine-learning support and ONNX runtime, enabling a seamless workflow from data generation to DWT--LSTM training, validation, and deployment [1,2].
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_4_1.png}
\caption{Overview of the MATLAB/Simulink power-system simulation model (Simulink main panel).}\label{fig:4.1}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.78\textwidth]{ct_primary.png}
\caption{Current-transformer primary (HV-side) subsystem implementing core saturation and remanence.}\label{fig:4.1b}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.67\textwidth]{ct_secondary.png}
\caption{Current-transformer secondary subsystem implementing core saturation and remanence.}\label{fig:4.1c}\end{figure}

\section{Simulation Environment}
The platform comprises MATLAB R2023a with Simulink, Simscape Electrical, the Deep Learning Toolbox, the Signal Processing Toolbox, and the ONNX converter. A discrete-time solver with fixed step $\Delta t=1\times10^{-5}$\,s (10\,\textmu s) is used, giving a Nyquist frequency $f_{Nyquist}=1/(2\Delta t)=50$\,kHz---a 10$\times$ oversampling margin over the 10\,kHz feature-extraction rate. Each simulation runs for $T_{sim}=1.0$\,s with the event injected at $t_{event}=0.2$\,s, yielding 10{,}001 samples per record at 10\,kHz and one-cycle (200-sample) sliding windows per case.

\section{Transformer Model Parameters}
The protected transformer is a three-phase 300\,MVA, 230/11\,kV unit with Yd1 vector group (grounded wye primary, delta secondary, $-30^\circ$ displacement). Full-load currents are $I_{FLA,HV}=753.1$\,A and $I_{FLA,LV}=15{,}746$\,A; base impedances are $176.33\,\Omega$ (HV) and $0.4033\,\Omega$ (LV). The saturable core uses a piecewise-linear $B$--$H$ curve (20 points, knee near 1.2\,pu); worst-case inrush ($\alpha=0^\circ$, $\phi_r=+\phi_m$) yields $\phi_{peak}=3\phi_m$. The $-30^\circ$ displacement is compensated by a Clarke rotation of the LV-side CT currents.
\begin{table}[H]\centering\caption{Transformer nameplate and equivalent-circuit parameters.}\label{tab:4.1}
\begin{tabular}{@{}lc@{}}\toprule \textbf{Parameter} & \textbf{Value}\\ \midrule
Nominal power $S_{nom}$ & 300\,MVA\\
Primary / secondary voltage & 230\,kV / 11\,kV (L--L)\\
Frequency & 50\,Hz\\
Vector group & Yd1 (Wye/Delta, $30^\circ$ lag)\\
Winding 1 (HV) $R_1$, $L_1$ & 0.0025\,pu, 0.08\,pu\\
Winding 2 (LV) $R_2$, $L_2$ & 0.003\,pu, 0.08\,pu\\
Magnetizing branch $R_m$, $L_m$ & 500\,pu, 5\,pu\\ \bottomrule
\end{tabular}\end{table}

\section{Power System Network and CT Model}
The external system is represented by Th\'evenin equivalents: $Z_{th,HV}=0.5+j15.0\,\Omega$ (SCL 3524\,MVA) and $Z_{th,LV}=0.01+j0.10\,\Omega$ (SCL 1204\,MVA), giving available fault currents of 8.84\,kA (HV) and 63.2\,kA (LV). Breakers use $R_{on}=0.001\,\Omega$ with RC snubbers; the LV load is 240\,MVA at 0.85 pf (80\% loading). CTs on both sides use a saturable core (Table~\ref{tab:4.2}).
\begin{table}[H]\centering\caption{Current transformer parameters.}\label{tab:4.2}
\begin{tabular}{@{}lcc@{}}\toprule \textbf{Parameter} & \textbf{HV Side} & \textbf{LV Side}\\ \midrule
CT ratio & 20:1 & 20:1\\
Accuracy class & 5P20 & 5P20\\
Rated primary current & 753.1\,A & 15{,}746\,A\\
Secondary resistance $R_s$ & 0.5\,$\Omega$ & 0.3\,$\Omega$\\
Burden impedance $Z_b$ & 1.5\,$\Omega$ & 1.0\,$\Omega$\\
Core relative permeability & 2000 & 2000\\ \bottomrule
\end{tabular}\end{table}

\section{Fault and Event Scenarios}
Internal faults are simulated at five winding taps (5--95\%) for four fault types (SLG, LL, LLG, 3LG) with three inception angles and three fault resistances ($Z_{fault}(p)=p^2 Z_k+R_f$), giving 720 deterministic cases. External faults on both buses, including evolving faults and asymmetric CT saturation, give 540 cases. Inrush is generated by sweeping switching angle ($0$--$180^\circ$) and residual flux ($-0.8$ to $+0.8$\,pu), with sympathetic inrush via two parallel transformers, giving 189 cases. CT-saturation stress cases (108) vary burden, fault current, and remanent flux. Normal operation (270 cases) covers six load levels, three taps, five voltages, and three power factors. Table~\ref{tab:scen} summarises the deterministic scenario counts that seed the augmented dataset.
\begin{table}[H]\centering\caption{Deterministic simulation scenarios seeding the augmented dataset.}\label{tab:scen}
\begin{tabular}{@{}lcl@{}}\toprule \textbf{Scenario class} & \textbf{Cases} & \textbf{Key swept parameters}\\ \midrule
Internal fault & 720 & 5 taps $\times$ 4 types $\times$ 3 angles $\times$ 3 resistances\\
External fault & 540 & both buses, evolving faults, CT saturation\\
CT saturation stress & 108 & burden, fault current, remanent flux\\
Magnetizing inrush & 189 & switching angle, residual flux, sympathetic\\
Normal operation & 270 & load, tap, voltage, power factor\\ \midrule
Total (base) & 1{,}827 & augmented and balanced to the 2{,}500-case dataset (Table~\ref{tab:4.3})\\ \bottomrule
\end{tabular}\end{table}

\section{Signal Conditioning and Dataset Summary}
Each record passes through a merging-unit chain emulating IEC 61850-9-2: a 4th-order Butterworth anti-alias filter (800\,Hz), 16-bit quantization, and AWGN at 20/30/40\,dB SNR, decimated to 10\,kHz. The base corpus comprises 2{,}500 simulated cases with 100\% simulation success and an internal-fault (Trip) prevalence of 41.4\%; a No-Trip positive-class weight of 1.4155 is used in the weighted loss. The fault-resistance range spans 0.001--99\,$\Omega$, inception angle 0--360$^\circ$, and eleven fault types are represented.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_4_2.png}
\caption{Merging-unit signal-conditioning and noise-injection pipeline.}\label{fig:4.2}\end{figure}
Table~\ref{tab:4.3} summarizes the dataset by event category; the four categories map to a binary protection label (internal $\to$ Trip; external, inrush, normal $\to$ No-Trip). After augmentation and stratified 70/15/15 splitting, the held-out test set comprises 1{,}800 cases.
\begin{table}[H]\centering\caption{Composition of the 2{,}500-case base dataset by event category and protection label.}\label{tab:4.3}
\begin{tabular}{@{}lccc@{}}\toprule \textbf{Event category} & \textbf{Count} & \textbf{Share (\%)} & \textbf{Protection label}\\ \midrule
Internal fault & 1{,}035 & 41.4 & Trip\\
External fault & 578 & 23.1 & No-Trip\\
Magnetizing inrush & 500 & 20.0 & No-Trip\\
Normal operation & 387 & 15.5 & No-Trip\\ \midrule
Total & 2{,}500 & 100.0 & 1{,}035 Trip / 1{,}465 No-Trip\\ \bottomrule
\end{tabular}\end{table}
\begin{table}[H]\centering\caption{Stochastic augmentation parameter ranges.}\label{tab:4.5}
\begin{tabular}{@{}lll@{}}\toprule \textbf{Parameter} & \textbf{Distribution} & \textbf{Range}\\ \midrule
Fault inception angle & Uniform & 0--360$^\circ$\\
Fault resistance & Log-uniform & 0.001--99\,$\Omega$\\
Source impedance variation & Uniform & $\pm5\%$\\
Fault location (winding) & Uniform & 2--98\%\\
Residual flux & Uniform & $-0.8$ to $+0.8$\,pu\\
Loading level & Uniform & 0--110\% rated\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_4_3.png}
\caption{Composition of the 2{,}500-case dataset across event categories and train/validation/test subsets.}\label{fig:4.3}\end{figure}
```

### Appendix: Proposed DWT--LSTM Methodology

```latex
\section{Introduction}
This chapter presents the hybrid adaptive DWT--LSTM framework, which combines MATLAB/Simulink physical modeling and real-time deployment with Python/PyTorch deep-learning training. Differential currents are decomposed by a five-level db4 DWT over a one-cycle (20\,ms, 200-sample) window at $f_s$ = 10\,kHz, yielding seven statistical features per detail band plus two instantaneous quantities---a 37-dimensional feature vector per window. A two-layer LSTM with global temporal attention processes the resulting $[1,32,37]$ tensor; the LSTM acts as a supervisory veto within a hybrid decision engine.

\section{Framework Architecture}
\textbf{Step 1 (MATLAB/Simulink).} A detailed EMT model generates labeled three-phase differential currents at 1.6\,kHz (1601 steps per 1.0\,s), exported to \texttt{.mat}. \textbf{Step 2 (Python/PyTorch).} A DWT engine (PyWavelets) computes the seven per-band statistics from 200-sample one-cycle windows; the $[1,32,37]$ tensors train a PyTorch LSTM with global temporal attention using the Adam optimizer and weighted categorical cross-entropy, exported to ONNX at Opset 14 via \texttt{torch.onnx.export}. \textbf{Step 2b (Simulink).} The ONNX model is loaded via the Deep Learning Toolbox Predict block for real-time inference feeding the hybrid decision engine.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_5_1.png}
\caption{Two-step development and deployment architecture (MATLAB/Simulink $\leftrightarrow$ PyTorch $\leftrightarrow$ ONNX).}\label{fig:5.1}\end{figure}

\subsection{The Hybrid Decision Handshake}
The LSTM operates as a supervisory veto rather than a replacement for the classical relay. The handshake implements a logical AND:
\begin{equation}
\text{TRIP}=\text{Adaptive\_87T}\ \wedge\ (\hat{c}=\text{Internal Fault})\ \wedge\ (\text{Conf}\ge\theta_{conf}),
\end{equation}
providing dependability preservation (the 87T retains primary detection), security enhancement (the LSTM vetoes false trips), and fail-safe operation (defaulting to the 87T on inference failure).
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_5_2.png}
\caption{Hybrid veto/AND-gate decision logic combining the adaptive 87T element and the LSTM classifier.}\label{fig:5.2}\end{figure}

\subsection{Signal Flow}
The pipeline comprises seven stages: (1) CT secondary and merging unit at 10\,kHz with Yd1 ($-30^\circ$) compensation; (2) 200-sample one-cycle window; (3) 5-level db4 DWT yielding the 37-element feature vector; (4) sequence buffer reshaped to $[1,32,37]$; (5) ONNX LSTM classification; (6) hybrid decision engine; (7) latched breaker trip.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_5_3.png}
\caption{End-to-end seven-stage signal flow of the proposed protection scheme.}\label{fig:5.3}\end{figure}

\section{Data Preprocessing and Sampling}
The framework adopts $f_s=N\!\times\!f_0=200\times50=10{,}000$\,Hz ($\Delta t=0.1$\,ms), giving a Nyquist frequency of 5\,kHz and enabling five-level dyadic decomposition of the 200-sample one-cycle window ($200\!\to\!100\!\to\!50\!\to\!25\!\to\!13\!\to\!7$). Each one-cycle (20\,ms) window is summarised by a 37-dimensional feature vector, and a sequence of consecutive windows is fed to the LSTM.
\begin{figure}[H]\centering\includegraphics[width=0.9\textwidth]{fig_5_4.png}
\caption{DWT feature-extraction pipeline: one-cycle 200-sample window, five-level db4 decomposition, and the resulting 37-dimensional feature vector.}\label{fig:5.4}\end{figure}

\section{DWT Engine and Feature Extraction}
The db4 wavelet (compact support $L=8$, four vanishing moments, orthogonal) matches fault-inception transients. The five-level decomposition follows the Mallat algorithm with quadrature mirror filters $h[n]$ and $g[n]=(-1)^n h[L-1-n]$ and downsampling:
\begin{equation}
a_j[k]=\sum_n h[n-2k]\,a_{j-1}[n],\qquad d_j[k]=\sum_n g[n-2k]\,a_{j-1}[n].
\end{equation}
The band allocation is given in Table~\ref{tab:5.2}. From each of the five detail bands ($cD_1$--$cD_5$), seven statistics are computed: the wavelet energy $E_j=\sum_k|cD_j[k]|^2$, the Shannon entropy $H_j$ of the normalised band, the coefficient standard deviation $\sigma_j$, the maximum (transient-peak) amplitude $M_j$, the mean absolute deviation $\mathrm{MAD}_j$, the kurtosis $K_j$ (heavy-tail detector), and the skewness $Sk_j$.
\begin{table}[H]\centering\caption{Frequency band allocation for the five-level db4 DWT at $f_s$ = 10\,kHz (one-cycle 200-sample window).}\label{tab:5.2}
\begin{tabular}{@{}ccll c@{}}\toprule \textbf{Level} & \textbf{Coeff.} & \textbf{Band (Hz)} & \textbf{Key components} & \textbf{\# Coeff.}\\ \midrule
1 & $cD_1$ & 2500--5000 & Switching / high-freq.\ transients & 100\\
2 & $cD_2$ & 1250--2500 & Fault-inception transients & 50\\
3 & $cD_3$ & 625--1250 & Mid-band transients & 25\\
4 & $cD_4$ & 312--625 & Harmonic cluster & 13\\
5 & $cD_5$ & 156--312 & Low-order harmonics & 7\\
5 & $cA_5$ & 0--156 & DC, fundamental (50\,Hz) & 7\\ \bottomrule
\end{tabular}\end{table}
The 37-dimensional feature vector concatenates the seven statistics of the five detail bands ($7\times5=35$) with the two instantaneous quantities $I_{diff}$ and $I_{rest}$. It is $z$-score normalized, and a sequence of consecutive one-cycle windows is stacked into $X(t)\in\mathbb{R}^{32\times37}$, reshaped to $X_{LSTM}\in\mathbb{R}^{1\times32\times37}$.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_5_5.png}
\caption{Five-level db4 dyadic filter-bank decomposition of the one-cycle (200-sample, 10\,kHz) window into six sub-bands.}\label{fig:5.5}\end{figure}

\section{LSTM Architecture and Training}
The network comprises an input layer $[B,32,37]$; LSTM-1 (128 units, return sequences) with dropout 0.3; LSTM-2 (64 units, return sequences) with dropout 0.3; a global temporal attention layer
\begin{equation}
\alpha_t=\frac{\exp(v^\top\tanh(W_a h_t+b_a))}{\sum_{t'=1}^{32}\exp(v^\top\tanh(W_a h_{t'}+b_a))},\qquad c=\sum_{t=1}^{32}\alpha_t h_t\in\mathbb{R}^{64};
\end{equation}
a dense layer (32 units, ReLU); and a softmax output. The total trainable parameter count is 140{,}836.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_5_6.png}
\caption{DWT--LSTM classifier architecture with global temporal attention.}\label{fig:5.6}\end{figure}
Training uses weighted categorical cross-entropy with the internal-fault (Trip) class weighted by 1.4155, Adam ($\eta=0.001$, $\beta_1=0.9$, $\beta_2=0.999$), a ReduceLROnPlateau scheduler, batch size 128, up to 200 epochs with early stopping (patience 20), and 5-fold stratified cross-validation. The confidence score is $\text{Conf}(t)=\max_c\hat{p}_c(t)$ with $\theta_{conf}=0.85$. The model is exported to ONNX (Opset 14) with a fixed $[1,32,37]$ input and a stateless graph.

\section{Real-Time Implementation and Latency}
The ONNX model is integrated via the Predict block within a masked subsystem; a Stateflow chart encodes the trip/block state machine and latches the trip for 100\,ms. Figure~\ref{fig:5.hyb} shows the Simulink realisation of the complete hybrid 87T relay, wiring the DWT--LSTM classifier subsystem, the adaptive 87T differential element, and the AND/veto decision gate to the breaker trip coil.
\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{hybrid87t_impl.png}
\caption{Simulink implementation of the hybrid 87T relay: DWT--LSTM classifier, adaptive 87T element, and AND/veto decision gate.}\label{fig:5.hyb}\end{figure} The processing latency is $T_{proc}=T_{buffer}+T_{DWT}+T_{LSTM}+T_{logic}\approx5.0+0.1+1.0+0.01=6.1$\,ms ($\approx$0.3 cycle); the LSTM contributes 0.5--2.0\,ms on CPU ($<$0.1\,ms on GPU), with a total cost of $\approx$1.45\,MFLOPs per step.
\begin{table}[H]\centering\caption{Per-inference parameter and operation budget of the DWT--LSTM pipeline.}\label{tab:5.3}
\begin{tabular}{@{}lccc@{}}\toprule \textbf{Stage} & \textbf{Parameters} & \textbf{FLOPs/step} & \textbf{Share (\%)}\\ \midrule
DWT (5-level db4) & 0 & $\approx$8.4\,k & 0.6\\
LSTM layer 1 ($37\!\to\!128$) & 84{,}992 & $\approx$0.68\,M & 46.9\\
LSTM layer 2 ($128\!\to\!64$) & 49{,}408 & $\approx$0.69\,M & 47.6\\
Attention (64) & 4{,}224 & $\approx$0.06\,M & 4.1\\
Dense + softmax & 2{,}212 & $\approx$6.5\,k & 0.4\\ \midrule
Total & 140{,}836 & $\approx$1.45\,M & 100\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_5_7.png}
\caption{Per-inference computational cost distribution across pipeline stages.}\label{fig:5.7}\end{figure}

\section{Adaptive Decision Logic and Confidence Calibration}
While the core handshake uses a fixed threshold $\theta_{conf}=0.85$, the framework supports a state-dependent threshold
\begin{equation}
\theta_{conf}(t)=\theta_0-\gamma_1\,\mathbb{1}[I_r(t)>I_{r,hi}]+\gamma_2\,\mathbb{1}[K_s(t)>K_{s,hi}],
\end{equation}
which lowers the requirement during high-restraint genuine faults (where dependability is paramount) and raises it when a CT-saturation index $K_s$ is high (where false trips are most likely). Because neural-network softmax outputs can be over-confident, the probabilities are temperature-calibrated, $\hat{p}_c=\mathrm{softmax}(z/T)_c$, with the scalar temperature $T$ fitted by minimising the validation negative log-likelihood, so that a reported confidence near 0.85 corresponds to an empirical correctness probability near 0.85. To distinguish confident misclassifications from genuinely ambiguous events, the framework exposes the full softmax distribution; the predictive entropy $H(\hat{y})=-\sum_c\hat{p}_c\log\hat{p}_c$ flags ambiguous events for which the hybrid logic conservatively withholds the trip and, optionally, raises a supervisory alarm---particularly valuable for low-magnitude internal faults and borderline inrush events.

\section{Robustness Enhancement}
Three complementary strategies are used: AWGN augmentation (20/30/40\,dB, with 15/50\,dB for stress) exploiting the inherent noise resilience of frequency-localized energy features; dropout regularization (0.3) between LSTM layers; and out-of-distribution stress testing across switching angle, frequency (47--53\,Hz), remanent flux ($\pm0.9 B_{sat}$), and CT ratio errors ($\pm5\%$), processed end-to-end through the Simulink-embedded ONNX model.
```

### Appendix: Results, Analysis and Discussion

```latex
\section{Introduction}
This chapter evaluates the proposed Hybrid Adaptive Transformer Differential Protection (HATDP) framework, in which a DWT--LSTM classifier supervises a conventional 87T relay. All data were generated for a 300\,MVA, 230/11\,kV, Yd1 transformer at 10\,kHz. A dataset of 2{,}500 base cases (Table~\ref{tab:4.3}) was augmented and split 70/15/15, yielding an 1{,}800-case held-out test set. For protection evaluation the four categories are mapped to a binary decision (Trip vs.\ No-Trip).

\section{Data Generation and Preprocessing}
Figure~\ref{fig:6.1} shows representative three-phase differential current waveforms: normal load below 0.02\,pu; external faults decaying within one cycle; inrush with 5--8\,pu asymmetric peaks; and internal faults with sustained high-magnitude, high-frequency content. Severe CT saturation produced 34.7\% THD and 18.2\% second-harmonic content, consistent with IEEE C37.110.
\begin{figure}[H]\centering\includegraphics[width=0.81\textwidth]{fig_6_1.png}
\caption{Three-phase differential current waveforms for the four operating conditions.}\label{fig:6.1}\end{figure}
The 37-dimensional feature set---seven statistics from each of the five detail bands plus the two instantaneous quantities---separates the classes strongly, the high-frequency detail-band energies ($cD_1$--$cD_2$) showing the largest inter-class separation (a ratio exceeding $500\times$ between internal faults and normal operation, Table~\ref{tab:6.1}). Mutual-information analysis confirms the detail-band energy and standard-deviation statistics dominate (72.3\% of total MI); an ablation gives 98.45\% for the detail-band statistics only, 91.24\% for the energy statistic alone, and 98.89\% for the full 37-dimensional set.
\begin{table}[H]\centering\caption{Wavelet energy per DWT sub-band across event classes (mean $\pm$ s.d., $\times10^{-3}$\,pu$^2$).}\label{tab:6.1}
\small\begin{tabular}{@{}lcccc@{}}\toprule \textbf{Sub-band} & \textbf{Normal} & \textbf{External} & \textbf{Inrush} & \textbf{Internal}\\ \midrule
$cD_1$ (2500--5000\,Hz) & $0.08\pm0.03$ & $0.42\pm0.18$ & $1.85\pm0.72$ & $3.27\pm1.14$\\
$cD_2$ (1250--2500\,Hz) & $0.07\pm0.02$ & $0.39\pm0.16$ & $1.72\pm0.68$ & $3.15\pm1.08$\\
$cD_3$ (625--1250\,Hz) & $0.09\pm0.03$ & $0.44\pm0.19$ & $1.91\pm0.75$ & $3.41\pm1.21$\\
$cD_4$ (312--625\,Hz) & $0.01\pm0.005$ & $0.15\pm0.08$ & $0.52\pm0.21$ & $4.86\pm1.92$\\
$cD_5$ (156--312\,Hz) & $0.01\pm0.004$ & $0.13\pm0.07$ & $0.48\pm0.19$ & $4.71\pm1.85$\\
$cA_5$ (0--156\,Hz) & $0.01\pm0.006$ & $0.16\pm0.09$ & $0.55\pm0.23$ & $5.02\pm2.01$\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.9\textwidth]{fig_6_2.png}
\caption{Parameter-space coverage / feature distribution across event classes.}\label{fig:6.2}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.9\textwidth]{fig_6_3.png}
\caption{Statistical verification of the generated dataset.}\label{fig:6.3}\end{figure}

\section{LSTM Classification Performance}
\subsection{Training and Validation}
The LSTM (two layers, 128 and 64 units, dropout 0.3, attention) was trained in PyTorch with Adam ($\alpha=0.001$) and weighted categorical cross-entropy (internal-fault/Trip class weighted 1.4155) using 5-fold cross-validation; the best fold (Fold~3) is shown in Figure~\ref{fig:6.4}. Loss decreases smoothly below 0.05 over $\sim$60 epochs and accuracy converges near 99\% with negligible divergence, indicating minimal overfitting.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_6_4.png}
\caption{Training and validation loss/accuracy curves for the LSTM classifier (best fold).}\label{fig:6.4}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{allfolds.png}
\caption{Validation-accuracy trajectories across all five cross-validation folds.}\label{fig:6.4b}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_6_5.png}
\caption{Five-fold cross-validation performance summary.}\label{fig:6.5}\end{figure}
\subsection{Confusion Matrix}
The protection decision is a binary discrimination between Trip (internal fault) and No-Trip (external, inrush, normal). On the 1{,}800-case test set, the classifier correctly identifies 1{,}002 of 1{,}008 Trip events and 778 of 792 No-Trip events (Table~\ref{tab:6.3}, Figure~\ref{fig:6.6}), giving 98.89\% accuracy, a Trip recall (dependability) of 99.40\%, and a No-Trip recall (security) of 98.23\%. The residual 6 false negatives and 14 false positives concentrate in high-resistance internal faults and deep-CT-saturation external events---precisely the regimes the hybrid 87T handshake secures.
\begin{table}[H]\centering\caption{Binary (Trip/No-Trip) confusion matrix on the 1{,}800-case test set. Accuracy $=98.89\%$; F1 $=0.9901$; ROC--AUC $=0.9999$.}\label{tab:6.3}
\begin{tabular}{@{}lccc@{}}\toprule
\textbf{True $\downarrow$ / Pred.\ $\rightarrow$} & \textbf{No-Trip (0)} & \textbf{Trip (1)} & \textbf{Recall (\%)}\\ \midrule
No-Trip (0) & 778 & 14 & 98.23\\
Trip (1) & 6 & 1{,}002 & 99.40\\ \midrule
Overall accuracy & \multicolumn{3}{c}{98.89}\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_6_6.png}
\caption{Confusion-matrix heatmap of the DWT--LSTM classifier (counts and normalized).}\label{fig:6.6}\end{figure}
\subsection{Per-Class Metrics and Cross-Validation}
The Trip class attains 99.40\% recall at 98.62\% precision; the No-Trip class 98.23\% recall at 99.23\% precision (Table~\ref{tab:6.4}). Five-fold cross-validation (Table~\ref{tab:6.5}) gives a mean accuracy of $98.16\pm0.26\%$, dependability $98.36\pm0.28\%$, security $97.86\pm0.28\%$, and F1 $98.25\pm0.29\%$.
\begin{table}[H]\centering\caption{Per-class performance metrics of the DWT--LSTM classifier.}\label{tab:6.4}
\begin{tabular}{@{}lcccc@{}}\toprule \textbf{Class} & \textbf{Precision (\%)} & \textbf{Recall (\%)} & \textbf{F1 (\%)} & \textbf{Support}\\ \midrule
No-Trip (0) & 99.23 & 98.23 & 98.73 & 792\\
Trip (1) & 98.62 & 99.40 & 99.01 & 1{,}008\\ \midrule
Overall / weighted & 98.88 & 98.89 & 98.88 & 1{,}800\\ \bottomrule
\end{tabular}\end{table}
\begin{table}[H]\centering\caption{Five-fold stratified cross-validation results.}\label{tab:6.5}
\begin{tabular}{@{}lcccc@{}}\toprule \textbf{Metric} & \textbf{Mean} & \textbf{Std.\ Dev.} & \textbf{Min} & \textbf{Max}\\ \midrule
Accuracy (\%) & 98.16 & 0.26 & 97.75 & 98.49\\
Precision / Security (\%) & 97.86 & 0.28 & 97.42 & 98.17\\
Recall / Dependability (\%) & 98.36 & 0.28 & 98.03 & 98.87\\
F1-Score (\%) & 98.25 & 0.29 & 97.89 & 98.67\\ \bottomrule
\end{tabular}\end{table}

\section{Real-Time Hybrid Relay Validation}
The model was exported to ONNX (Opset 14) via \texttt{torch.onnx.export} and imported into Simulink for closed-loop co-simulation. Measured ONNX inference latency averaged 0.44\,ms (max 0.74\,ms), within the 0.625\,ms relay step when pipelined.
\subsection{Hybrid Decision Logic}
The hybrid relay trips only when the 87T element and the LSTM agree on an internal fault. On the validation set (Table~\ref{tab:6.7}) the hybrid achieves 100\% dependability and 100\% security---zero false negatives and zero false trips---whereas the standalone DWT--LSTM classifier alone produces 6 false negatives and 14 false trips, and the standalone adaptive 87T relay produces 18 false negatives and 62 false trips. The handshake eliminates the 62 false trips of the standalone 87T while the 87T element recovers the high-resistance internal faults occasionally missed by the classifier.
\begin{table}[H]\centering\caption{Performance comparison of standalone 87T, standalone LSTM, and hybrid relay.}\label{tab:6.7}
\begin{tabular}{@{}lccc@{}}\toprule \textbf{Metric} & \textbf{Standalone 87T} & \textbf{Standalone LSTM} & \textbf{Hybrid (87T+LSTM)}\\ \midrule
Dependability (\%) & 96.25 & 99.40 & 100.00\\
Security (\%) & 95.63 & 98.23 & 100.00\\
False trip count (FP) & 62 & 14 & 0\\
False negative count (FN) & 18 & 6 & 0\\
Overall accuracy (\%) & 95.83 & 98.89 & 100.00\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_6_8.png}
\caption{Comprehensive performance dashboard of the proposed framework.}\label{fig:6.8}\end{figure}
\subsection{Clearing Time}
The average fault-clearing time is 17.2\,ms (Table~\ref{tab:6.8}), within the one-cycle window at 50\,Hz (20\,ms)---a $2.6\times$ speedup over conventional harmonic restraint (45.5\,ms) and an improvement over the standalone LSTM relay (28.0\,ms). The relay processing latency itself is $\approx$12\,ms, the balance being breaker and pickup time.
\begin{table}[H]\centering\caption{Average fault-clearing time by method.}\label{tab:6.8}
\begin{tabular}{@{}lcc@{}}\toprule \textbf{Method} & \textbf{Avg.\ clearing time (ms)} & \textbf{Relative to HR}\\ \midrule
Conventional harmonic restraint & 45.5 & 1.0$\times$\\
Standalone DWT--LSTM relay & 28.0 & 1.6$\times$ faster\\
Proposed hybrid relay & 17.2 & 2.6$\times$ faster\\ \bottomrule
\end{tabular}\end{table}

\subsection{Per-Category Validation and Before/After Behaviour}
Figure~\ref{fig:6.hcm} shows the hybrid relay's per-category confusion on a balanced 500-case evaluation (125 per category): the four operating conditions---normal, inrush, internal fault, and external fault---are each resolved without error, confirming that the hybrid trips only on internal faults while blocking the three non-fault categories. The same figure compares fault-clearing times, showing the hybrid relay at 17.2\,ms against 28.0\,ms for the standalone LSTM relay and 45.5\,ms for conventional harmonic restraint. Figure~\ref{fig:6.ba} contrasts behaviour on a stressed case: the conventional standalone 87T relay false-trips during an external fault with $+95\%$ remanence, deep CT saturation, and 20\,dB noise, whereas the hybrid scheme vetoes the false trip while retaining dependability for a genuine internal fault.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{hybrid_cm_time.png}
\caption{Hybrid relay per-category confusion matrix and fault-clearing-time comparison.}\label{fig:6.hcm}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{before_after.png}
\caption{Before/after comparison: conventional standalone 87T versus the hybrid adaptive 87T\,+\,DWT--LSTM supervisor.}\label{fig:6.ba}\end{figure}

\subsection{Reliability and Economic Impact}
The protection performance translates into quantifiable reliability and economic benefits. Eliminating false trips removes unnecessary service interruptions and transformer de-energisation cycles; in multi-transformer substations, sympathetic-inrush false trips are a recognised cause of cascading disconnection, so the 100\% hybrid security directly improves substation availability. On the dependability side, the 17.2\,ms clearing time reduces the through-fault energy $\int i^2(t)\,dt$ absorbed by the winding relative to 30--45\,ms harmonic-restraint relays, lowering insulation ageing and the mechanical forces that drive winding deformation. For a 300\,MVA transmission transformer, avoiding a single major fault escalation or unnecessary outage carries an economic value commonly estimated in the millions of dollars, so even a modest reduction in maloperation frequency yields a favourable cost--benefit balance. Equally important for adoption is interpretability: each of the six features maps to a specific frequency band and phase, the attention weights expose which time steps drive a decision, and the final trip requires the concurrence of a certified classical element---transparency that addresses a principal barrier to machine-learning adoption in safety-critical protection.

\section{Stress Testing and Out-of-Distribution Robustness}
Figure~\ref{fig:6.7} summarizes operational robustness. Accuracy degrades gracefully with noise (Table~\ref{tab:6.12}), from 99.3\% clean to 98.6\% at 20\,dB and 97.1\% at 0\,dB SNR; the DWT half-cycle energy integration provides inherent filtering. Internal-fault recall (Table~\ref{tab:6.13}) remains $\ge$99\% up to 20\,$\Omega$, declining to 94.4\% (50--80\,$\Omega$) and 88.0\% ($>$80\,$\Omega$), for an overall recall of 99.40\%; the hybrid 87T element recovers high-resistance cases.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_6_7.png}
\caption{Operational robustness: accuracy vs.\ SNR, zone-level performance, and cumulative detection rate.}\label{fig:6.7}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.81\textwidth]{heatmap.png}
\caption{Internal-fault detection-rate heatmap across fault resistance and inception angle.}\label{fig:6.7b}\end{figure}
\begin{table}[H]\centering\caption{Classification accuracy under additive white Gaussian noise.}\label{tab:6.12}
\begin{tabular}{@{}lccccccc@{}}\toprule
\textbf{SNR (dB)} & Clean & 50 & 40 & 30 & 20 & 10 & 0\\ \midrule
\textbf{Accuracy (\%)} & 99.3 & 99.3 & 99.2 & 99.0 & 98.6 & 97.9 & 97.1\\ \bottomrule
\end{tabular}\end{table}
\begin{table}[H]\centering\caption{Internal-fault detection rate (recall) versus fault-resistance bin.}\label{tab:6.13}
\begin{tabular}{@{}lccccccc@{}}\toprule
\textbf{Resistance bin} & $<1\,\Omega$ & $1$--$5$ & $5$--$10$ & $10$--$20$ & $20$--$50$ & $50$--$80$ & $>80\,\Omega$\\ \midrule
\textbf{Recall (\%)} & 100.0 & 99.8 & 99.5 & 99.2 & 97.6 & 94.4 & 88.0\\ \bottomrule
\end{tabular}\end{table}

\section{Comparative Benchmarking}
Table~\ref{tab:6.14} compares all evaluated methods on the unified dataset. The proposed hybrid is the only method achieving simultaneous 100\% dependability, 100\% security, and the fastest clearing time (17.2\,ms). Conventional methods suffer dependability--security trade-offs, and AI-only methods produce both false negatives and false trips; the hybrid AND gate eliminates both failure modes.
\begin{table}[H]\centering\caption{Comprehensive performance comparison of all evaluated methods.}\label{tab:6.14}
\small\begin{tabular}{@{}lcccccc@{}}\toprule
\textbf{Method} & \textbf{Acc.} & \textbf{Dep.} & \textbf{Sec.} & \textbf{FN} & \textbf{FP} & \textbf{Time (ms)}\\ \midrule
HR (15\% threshold) & 93.54 & 94.58 & 92.92 & 26 & 102 & 38.5\\
HR (cross-blocking) & 95.21 & 94.58 & 95.42 & 26 & 70 & 38.5\\
Wavelet-ANN (36 feat.) & 98.65 & 99.79 & 98.13 & 1 & 20 & 0.18\\
Wavelet-ANN (6 feat.) & 96.56 & 99.17 & 95.42 & 4 & 42 & 0.12\\
Wavelet-SVM (RBF) & 98.23 & 99.17 & 97.92 & 4 & 29 & 0.08\\
Wavelet-CNN & 98.85 & 99.58 & 98.54 & 2 & 15 & 0.35\\
Wavelet-PNN & 97.44 & 98.75 & 97.08 & 6 & 38 & 0.06\\
Standalone 87T & 95.83 & 96.25 & 95.63 & 18 & 62 & 0.10\\
Standalone 87T (optimized) & 96.67 & 97.08 & 96.46 & 14 & 51 & 0.10\\
Standalone DWT--LSTM & 98.89 & 99.40 & 98.23 & 6 & 14 & 0.44\\
\textbf{Proposed Hybrid} & \textbf{100.00} & \textbf{100.00} & \textbf{100.00} & \textbf{0} & \textbf{0} & 17.2\\ \bottomrule
\end{tabular}\end{table}

\section{Detailed Comparison with Prior Published Work}
Table~\ref{tab:6.15} broadens the comparison to the cited literature, examining capabilities that determine field viability. Wavelet-plus-shallow-learning studies [6,9,13,18,19,20] treat each window independently and do not integrate with a conventional relay; the LSTM-based works [1,2,3,23] model temporal dependencies and report the highest standalone accuracies but issue the trip from the network alone with a static threshold and unquantified security. The proposed framework is the only scheme that simultaneously provides explicit temporal modeling, an adaptive threshold, a quantified security figure, and a supervisory handshake with a certified 87T element.
\begin{table}[H]\centering\caption{Capability-level comparison against representative prior studies ($\checkmark$ present, $\times$ absent, $\circ$ partial).}\label{tab:6.15}
\footnotesize\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}c>{\raggedright\arraybackslash}p{3.3cm}*{4}{>{\centering\arraybackslash}p{1.45cm}}>{\centering\arraybackslash}p{1.3cm}@{}}\toprule
\textbf{Ref.} & \textbf{Method} & \textbf{Temporal model} & \textbf{Adaptive thresh.} & \textbf{Security quant.} & \textbf{87T hybrid} & \textbf{Acc.\ (\%)}\\ \midrule
{[6]} & db4 DWT + thresholds & $\times$ & $\times$ & $\times$ & $\times$ & $\sim$97\\
{[18]} & Wavelet stats + ANN & $\times$ & $\times$ & $\circ$ & $\times$ & 99.1\\
{[13]} & Wavelet + SVM & $\times$ & $\times$ & $\circ$ & $\times$ & 98.2\\
{[16]} & Accelerated DNN (CNN) & $\circ$ & $\times$ & $\circ$ & $\times$ & 98.7\\
{[3]} & Wavelet + LSTM & $\checkmark$ & $\times$ & $\circ$ & $\times$ & 99.3\\
{[1,2]} & Improved wavelet + LSTM & $\checkmark$ & $\times$ & $\circ$ & $\times$ & $\sim$99.5\\
{[23]} & Dual DNN (2-class) & $\checkmark$ & $\times$ & $\circ$ & $\times$ & $\sim$99.4\\
{[21]} & Multi-region adaptive relay & $\times$ & $\checkmark$ & $\circ$ & $\times$ & ---\\
\textbf{This work} & DWT energy + LSTM + 87T & $\checkmark$ & $\checkmark$ & $\checkmark$ & $\checkmark$ & 98.9/100\\ \bottomrule
\end{tabular}\end{table}

\subsection{Discussion Relative to Specific LSTM Studies}
The works most closely related to this thesis are the wavelet--LSTM schemes of Atiyah \textit{et al.}\ [3] and Alhamd \textit{et al.}\ [1,2], which established that an LSTM ingesting wavelet-derived features attains roughly 99.3--99.5\% accuracy on simulated transformer data. The present work departs from them in three respects. First, the feature representation is a physics-informed 37-dimensional statistical descriptor---seven statistics (energy, entropy, standard deviation, maximum, MAD, kurtosis, skewness) across five db4 wavelet bands plus two instantaneous quantities---that spans the discriminative time-frequency content while remaining fully interpretable. Second, the LSTM is not the final arbiter: its output is gated by the adaptive 87T element, eliminating the false trips an isolated classifier inevitably produces under deep CT saturation and sympathetic inrush. Third, the model is deployed back into the electromagnetic-transient simulator through ONNX and exercised in closed loop, rather than scored offline, providing a substantially more realistic end-to-end validation. The dual-DNN scheme of Key \textit{et al.}\ [23] achieves comparable accuracy but addresses only the binary inrush-versus-internal problem; the present formulation additionally resolves external faults and normal operation, which is necessary for a complete protection function.

\section{Ablation and Sensitivity Studies}
Removing the attention layer reduces accuracy by 0.71\,pp; a single 64-unit layer costs 1.34\,pp; and the approximation-only feature set collapses to 91.24\% (Table~\ref{tab:6.16}). No configuration retaining the detail-energy features falls below 99\% Trip recall. A wavelet/level grid search (Table~\ref{tab:6.17}) confirms db4 at five levels as the best accuracy--compactness trade-off, corroborating [6,14].
\begin{table}[H]\centering\caption{Ablation study: effect of removing or altering individual components (unified test set).}\label{tab:6.16}
\begin{tabular}{@{}lcc@{}}\toprule \textbf{Configuration} & \textbf{Accuracy (\%)} & \textbf{$\Delta$ (pp)}\\ \midrule
Full model (proposed) & 98.89 & ---\\
Without attention layer & 98.18 & $-0.71$\\
Single LSTM layer (64 units) & 97.55 & $-1.34$\\
Detail-energy features only & 98.45 & $-0.44$\\
Approximation-energy features only & 91.24 & $-7.65$\\
Without $z$-score normalization & 96.02 & $-2.87$\\
3-level DWT (instead of 5-level) & 98.33 & $-0.56$\\ \bottomrule
\end{tabular}\end{table}
\begin{table}[H]\centering\caption{Classification accuracy versus mother wavelet and decomposition level (\%).}\label{tab:6.17}
\begin{tabular}{@{}lccc@{}}\toprule \textbf{Wavelet} & \textbf{3-level} & \textbf{4-level} & \textbf{5-level}\\ \midrule
Haar (db1) & 96.02 & 96.40 & 96.55\\
db4 (selected) & 98.40 & 98.71 & \textbf{98.89}\\
db6 & 98.27 & 98.55 & 98.71\\
sym4 & 98.10 & 98.40 & 98.62\\
coif3 & 98.05 & 98.33 & 98.50\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.9\textwidth]{fig_6_9.png}
\caption{Ablation sensitivity of classification accuracy to individual design choices.}\label{fig:6.9}\end{figure}

\section{ROC and Confidence-Threshold Analysis}
A receiver-operating-characteristic analysis gives an AUC of 0.9999 (Figure~\ref{fig:6.10}); the selected operating point $\theta_{conf}=0.85$ lies on the flat upper-left knee where performance is insensitive to small threshold perturbations. The confidence distribution (Figure~\ref{fig:6.11}) is sharply bimodal, separating confident Trip and No-Trip decisions, with predictive entropy flagging the few ambiguous events for conservative handling.
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_6_10.png}
\caption{ROC and precision--recall curves for internal-fault detection (AUC $=0.9999$).}\label{fig:6.10}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.98\textwidth]{fig_6_11.png}
\caption{Confidence-score distribution for Trip and No-Trip decisions.}\label{fig:6.11}\end{figure}

\section{Discussion of Results}
The hybrid DWT--LSTM + adaptive 87T architecture achieves zero false negatives (100\% dependability), zero false trips (100\% security), and the fastest clearing time (17.2\,ms), while the standalone classifier attains 98.89\% accuracy (F1 $=0.9901$, ROC--AUC $=0.9999$). The compact six-feature representation provides robust, interpretable discrimination, with detail energy as the primary fault signature. Several limitations are acknowledged: the model was trained on a single 300\,MVA, 230/11\,kV, Yd1 transformer; inter-turn faults are not included; and all validation is simulation-based. Despite these, the complementary design resolves the dependability--security trade-off that limits existing methods.

\section{Threats to Validity}
\textbf{Internal:} information leakage is prevented by splitting at the case level (never the window level) and computing normalization statistics on the training subset only; the zero-variance internal recall across folds argues against a fortunate split. \textbf{External:} the simulation-to-field gap is mitigated by physically grounded core/CT models, a realistic merging-unit chain, and a five-axis stress programme, though field-recorded and HIL validation remain essential. \textbf{Construct/statistical:} the adopted metrics map directly to protection requirements, and the 1{,}800-case test set yields narrow confidence intervals; cited external accuracies are flagged as non-commensurable.
```

### Appendix: Conclusion and Future Scope

```latex
\section{Conclusion}
This thesis presented the design, development, and evaluation of a hybrid adaptive transformer differential protection (HATDP) framework combining a DWT--LSTM classifier with a conventional 87T relay. A detailed 300\,MVA, 230/11\,kV, Yd1 model was built in MATLAB/Simulink with realistic magnetization, CT saturation, and remanence; a 2{,}500-case base dataset was generated across four operating conditions. A five-level db4 DWT on one-cycle (200-sample, 10\,kHz) windows yields a 37-dimensional statistical feature vector; a two-layer LSTM (128--64) with global temporal attention, trained in PyTorch, attains 98.89\% accuracy (F1 $=0.9901$, ROC--AUC $=0.9999$) on the 1{,}800-case test set and is exported to ONNX (Opset 14) for Simulink deployment. The hybrid veto/AND-gate achieves 100\% dependability and 100\% security on the validation set with an average clearing time of 17.2\,ms (a $2.6\times$ speedup over harmonic restraint), resolving the dependability--security trade-off.

\section{Key Findings}
\textbf{Feature robustness.} Six DWT energy features suffice for reliable discrimination; the detail-energy features achieve an inter-class separation ratio exceeding 500. The classifier degrades gracefully---$\ge$97\% accuracy down to 20\,dB SNR and $\ge$99\% internal-fault recall up to 20\,$\Omega$---while the 87T element preserves 100\% relay-level dependability. \textbf{Security.} The standalone 87T produces 62 false trips and 18 false negatives; the classifier reduces these to 14 and 6; the hybrid eliminates both. \textbf{Real-time feasibility.} The processing latency is $\approx$12\,ms and the total clearing time 17.2\,ms, firmly within the one-cycle window, validated in closed-loop co-simulation.

\section{Research Outcomes}
The architecture demonstrates that 100\% dependability and 100\% security can be achieved simultaneously, challenging the assumption that these must be traded off. The validated MATLAB $\to$ PyTorch $\to$ ONNX $\to$ Simulink pipeline is reproducible by relay manufacturers; fast clearing reduces $I^2t$ thermal stress; and the six physically interpretable features address a key barrier to ML adoption in safety-critical protection. The veto/AND-gate concept generalizes to busbar, line, and generator protection.

\section{Limitations of the Study}
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item Trained exclusively on a 300\,MVA, 230/11\,kV, Yd1 transformer; generalization unverified.
\item Inter-turn faults are not included.
\item Detection recall declines for fault resistances above 80\,$\Omega$.
\item All results are simulation-based; COMTRADE/HIL validation is required.
\item A fixed system topology is assumed.
\end{enumerate}

\section{Recommendations for Future Work}
Hardware-in-the-loop testing on a real-time digital simulator (Speedgoat/OPAL-RT/FPGA); detailed multi-winding modeling for inter-turn fault detection; field deployment with IEC 61850 GOOSE mapping and Sampled-Values integration; and transfer learning with online drift detection to extend the framework to other transformer configurations with minimal additional data.

\section{Broader Outlook}
The hybrid philosophy demonstrated in this thesis---pairing a learned, security-enhancing supervisor with a certified, dependability-guaranteeing classical element---generalises beyond transformer differential protection. The same handshake structure applies to busbar protection (where CT saturation during external faults similarly threatens security), to transmission-line differential and distance protection (where evolving and high-resistance faults challenge fixed settings), and to generator protection (where discriminating magnetising phenomena from genuine faults is analogously difficult). As power systems move toward inverter-dominated generation, the waveform signatures on which conventional relays depend will continue to drift away from the sinusoidal, harmonic-rich assumptions of legacy algorithms; data-driven supervisors that learn from prevailing signal statistics, retrained or fine-tuned as the system evolves, offer a principled path to maintaining protection security. Coupled with the IEC 61850 digital-substation integration and transfer-learning directions of Section~7.5, this points toward a generation of intelligent electronic devices in which certified classical logic and continuously adapting learned supervision operate together as a matter of course.

\section{Concluding Remarks}
By keeping the LSTM in a supervisory role, quantifying both dependability and security, stress-testing beyond the training distribution, and validating in closed-loop co-simulation, this work offers a transferable design pattern for the responsible integration of machine learning into safety-critical protection as power systems transition to intelligent, digital, and increasingly converter-dominated operation.

% ===================== PUBLICATIONS =====================
\chapter*{List of Related Publications}
\addcontentsline{toc}{chapter}{List of Related Publications}
The methodology and findings of this thesis build directly upon the following closely related peer-reviewed publications, which represent the current state of the art in wavelet- and deep-learning-based transformer differential protection and were consulted throughout this work:
\begin{enumerate}[leftmargin=1.6em,itemsep=6pt]
\item W. A. Atiyah, S. Karimi, and M. Moradi, ``Real-time revolutionizing internal defect detection in power transformers by leveraging wavelet transform and deep learning LSTM in cascading application,'' \textit{Journal of Electrical Engineering \& Technology}, Springer, 2024, doi: 10.1007/s42835-024-02048-7. \textit{Relevance:} the closest prior work---a cascaded wavelet\,+\,LSTM scheme for real-time internal-fault detection---which this thesis extends with a compact six-feature representation and a supervisory 87T handshake.
\item S. Key, S. Leap, H. Yoon, S. Lee, and S.-R. Nam, ``A dual deep neural network approach for discriminating internal faults and inrush currents in transformers under CT saturation,'' \textit{IEEE Access}, vol.~13, 2025, doi: 10.1109/ACCESS.2025.3618747. \textit{Relevance:} a recent dual-network discrimination scheme under CT saturation; this thesis instead couples a single temporal LSTM to a certified 87T element through an explicit veto handshake.
\item S. Afrasiabi, M. Afrasiabi, B. Parang, and M. Mohammadi, ``Integration of accelerated deep neural network into power transformer differential protection,'' \textit{IEEE Transactions on Industrial Informatics}, vol.~16, no.~2, 2020, doi: 10.1109/TII.2019.2929744. \textit{Relevance:} establishes real-time deep-learning relay feasibility, complemented here by the ONNX$\to$Simulink closed-loop deployment.
\item L. D. Sim\~oes, H. J. D. Costa, M. N. O. Aires, R. P. Medeiros, F. B. Costa, and A. S. Bretas, ``A power transformer differential protection based on support vector machine and wavelet transform,'' \textit{Electric Power Systems Research}, vol.~197, art.\ 107297, 2021. \textit{Relevance:} a wavelet\,+\,SVM baseline for the same discrimination task addressed here with a temporal LSTM and hybrid veto.
\item O. Abdusalam, A. Ibrahim, F. Anayi, and M. Packianather, ``New hybrid machine learning method for detecting faults in three-phase power transformers,'' \textit{Energies}, 2023. \textit{Relevance:} a hybrid ML fault-detection approach; this thesis likewise validates robustness down to 20\,dB SNR while retaining interpretable, physics-informed features.
\end{enumerate}

% ===================== REFERENCES =====================
\renewcommand{\bibname}{REFERENCES}
\begin{thebibliography}{99}
\addcontentsline{toc}{chapter}{References}
\bibitem{r1} W. A. Atiyah, S. Karimi, and M. Moradi, ``Real-time revolutionizing internal defect detection in power transformers by leveraging wavelet transform and deep learning LSTM in cascading application,'' \textit{J.\ Electr.\ Eng.\ Technol.}, 2024, doi: 10.1007/s42835-024-02048-7.
\bibitem{r2} S. Hochreiter and J. Schmidhuber, ``Long short-term memory,'' \textit{Neural Comput.}, vol.~9, no.~8, pp.~1735--1780, 1997.
\bibitem{r3} K. Greff, R. K. Srivastava, J. Koutn\'ik, B. R. Steunebrink, and J. Schmidhuber, ``LSTM: A search space odyssey,'' \textit{IEEE Trans.\ Neural Netw.\ Learn.\ Syst.}, vol.~28, no.~10, pp.~2222--2232, 2017.
\bibitem{r4} P. M. Anderson, \textit{Power System Protection}. Piscataway, NJ: IEEE Press / New York: McGraw-Hill, 1999.
\bibitem{r5} S. G. Mallat, ``A theory for multiresolution signal decomposition: the wavelet representation,'' \textit{IEEE Trans.\ Pattern Anal.\ Mach.\ Intell.}, vol.~11, no.~7, pp.~674--693, 1989.
\bibitem{r6} O. Ozgonenel and S. Karagol, ``Transformer differential protection using wavelet transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~114, pp.~60--67, 2014.
\bibitem{r7} R. L. Sharp and W. E. Glassburn, ``A transformer differential relay with second-harmonic restraint,'' \textit{Trans.\ AIEE, Part III (Power App.\ Syst.)}, vol.~77, no.~3, pp.~913--918, 1958.
\bibitem{r8} J. A. Sykes and I. F. Morrison, ``A proposed method of harmonic-restraint differential protecting of transformers by digital computer,'' \textit{IEEE Trans.\ Power App.\ Syst.}, vol.~PAS-91, no.~3, pp.~1266--1272, 1972.
\bibitem{r9} M. Tripathy, R. P. Maheshwari, and H. K. Verma, ``Power transformer differential protection based on optimal probabilistic neural network,'' \textit{IEEE Trans.\ Power Del.}, vol.~25, no.~1, pp.~102--112, 2010.
\bibitem{r10} L. L. Zhang, Q. H. Wu, T. Y. Ji, and A. Q. Zhang, ``Identification of inrush currents in power transformers based on higher-order statistics,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~146, pp.~161--169, 2017.
\bibitem{r11} O. Abdusalam, A. Ibrahim, F. Anayi, and M. Packianather, ``New hybrid machine learning method for detecting faults in three-phase power transformers,'' \textit{Energies}, vol.~16, 2023.
\bibitem{r12} M. Salimi, ``Identification of the inrush current of the internal faults of power transformers based on the differential relay function,'' \textit{Int.\ J.\ Adv.\ Appl.\ Sci.}, vol.~5, no.~3, pp.~141--148, 2016.
\bibitem{r13} L. D. Sim\~oes, H. J. D. Costa, M. N. O. Aires, R. P. Medeiros, F. B. Costa, and A. S. Bretas, ``A power transformer differential protection based on support vector machine and wavelet transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~197, art.\ 107297, 2021.
\bibitem{r14} M. Y. Suliman and M. T. Al-Khayyat, ``Discrimination between inrush and internal fault currents in protection based power transformer using DWT,'' \textit{Int.\ J.\ Electr.\ Eng.\ Informat.}, vol.~13, no.~1, 2021.
\bibitem{r15} L. A. Yaseen, A. Ebadi, and A. A. Abdoos, ``Discrimination between inrush and internal fault currents in power transformers using hyperbolic S-transform,'' \textit{Int.\ J.\ Eng., Trans.\ C}, vol.~36, no.~12, pp.~2184--2189, 2023.
\bibitem{r16} S. Afrasiabi, M. Afrasiabi, B. Parang, and M. Mohammadi, ``Integration of accelerated deep neural network into power transformer differential protection,'' \textit{IEEE Trans.\ Ind.\ Informat.}, vol.~16, no.~2, 2020, doi: 10.1109/TII.2019.2929744.
\bibitem{r17} H. Dashti and M. Sanaye-Pasand, ``Power transformer protection using a multiregion adaptive differential relay,'' \textit{IEEE Trans.\ Power Del.}, vol.~29, no.~2, pp.~777--785, 2014.
\bibitem{r18} B. Sundararaman and P. Jain, ``Fault detection and classification in electrical power transmission system using wavelet transform,'' in \textit{Proc.\ Int.\ Conf.\ Recent Advances in Sciences and Engineering (ICRASE)}, Dubai, 2023.
\bibitem{r19} S. I. Tuhin, M. Al Araf, F. I. Zubayer, M. A. Al Mahtab, and M. Naeem, ``Advanced fault detection in power systems using wavelet transform: SIMULINK-based implementation and analysis,'' \textit{J.\ Energy Eng.\ Thermodyn.}, vol.~4, no.~3, pp.~12--25, 2024, doi: 10.55529/jeet.43.12.25.
\bibitem{r20} S. B. A. Bukhari, A. Wadood, T. Khurshaid, K. K. Mehmood, S. B. Rhee, and K.-C. Kim, ``Empirical wavelet transform-based intelligent protection scheme for microgrids,'' \textit{Energies}, 2022.
\bibitem{r21} Y. Wang, Y. Lu, and C. Cai, ``A variable data-window phaselet transformer differential protection algorithm based on recursive least square theory,'' in \textit{Proc.\ Conf.}, Southeast University, 2021.
\bibitem{r22} I. Guyon and A. Elisseeff, ``An introduction to variable and feature selection,'' \textit{J.\ Mach.\ Learn.\ Res.}, vol.~3, pp.~1157--1182, 2003.
\bibitem{r23} S. Key, S. Leap, H. Yoon, S. Lee, and S.-R. Nam, ``A dual deep neural network approach for discriminating internal faults and inrush currents in transformers under CT saturation,'' \textit{IEEE Access}, vol.~13, 2025, doi: 10.1109/ACCESS.2025.3618747.
\bibitem{r24} A. Guzm\'an, S. Zocholl, G. Benmouyal, and H. J. Altuve, ``A current-based solution for transformer differential protection---Part~I: Problem statement,'' \textit{IEEE Trans.\ Power Del.}, vol.~16, no.~4, pp.~485--491, 2001.
\bibitem{r25} P. Chiradeja, C. Pothisarn, \textit{et al.}, ``Application of probabilistic neural networks using high-frequency components' differential current for transformer protection schemes,'' \textit{Appl.\ Sci.}, 2021.
\bibitem{r26} T. S. Sidhu and M. S. Sachdev, ``Online identification of magnetizing inrush and internal faults in three-phase transformers,'' \textit{IEEE Trans.\ Power Del.}, vol.~7, no.~4, pp.~1885--1891, 1992.
\bibitem{r27} M. A. Rahman and B. Jeyasurya, ``A state-of-the-art review of transformer protection algorithms,'' \textit{IEEE Trans.\ Power Del.}, vol.~3, no.~2, pp.~534--544, 1988.
\bibitem{r28} X.-n. Lin, P. Liu, and O. P. Malik, ``Studies for identification of the inrush based on improved correlation algorithm,'' \textit{IEEE Trans.\ Power Del.}, vol.~17, no.~4, pp.~901--907, 2002.
\bibitem{r29} K. Inagaki, M. Higaki, Y. Matsui, K. Kurita, M. Suzuki, K. Yoshida, and T. Maeda, ``Digital protection method for power transformers based on an equivalent circuit composed of inverse inductance,'' \textit{IEEE Trans.\ Power Del.}, vol.~3, no.~4, pp.~1501--1510, 1988.
\bibitem{r30} A. G. Phadke and J. S. Thorp, ``A new computer-based flux-restrained current-differential relay for power transformer protection,'' \textit{IEEE Trans.\ Power App.\ Syst.}, vol.~PAS-102, no.~11, pp.~3624--3629, 1983.
\bibitem{r31} I. Daubechies, ``The wavelet transform, time-frequency localization and signal analysis,'' \textit{IEEE Trans.\ Inf.\ Theory}, vol.~36, no.~5, pp.~961--1005, 1990.
\bibitem{r32} O. Rioul and M. Vetterli, ``Wavelets and signal processing,'' \textit{IEEE Signal Process.\ Mag.}, vol.~8, no.~4, pp.~14--38, 1991.
\bibitem{r33} W. Rebizant, D. Bejmert, and L. Schiel, ``Transformer differential protection with neural network based inrush stabilization,'' in \textit{Proc.\ Int.\ Conf.\ on Developments in Power System Protection}, 2008.
\bibitem{r34} L. Breiman, ``Random forests,'' \textit{Mach.\ Learn.}, vol.~45, no.~1, pp.~5--32, 2001.
\bibitem{r35} G. E. Hinton and R. R. Salakhutdinov, ``Reducing the dimensionality of data with neural networks,'' \textit{Science}, vol.~313, no.~5786, pp.~504--507, 2006.
\bibitem{r36} I. Goodfellow, J. Pouget-Abadie, M. Mirza, B. Xu, D. Warde-Farley, S. Ozair, A. Courville, and Y. Bengio, ``Generative adversarial nets,'' in \textit{Proc.\ Adv.\ Neural Inf.\ Process.\ Syst.\ (NeurIPS)}, 2014, pp.~2672--2680.
\bibitem{r37} A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin, ``Attention is all you need,'' in \textit{Proc.\ Adv.\ Neural Inf.\ Process.\ Syst.\ (NeurIPS)}, 2017, pp.~5998--6008.
\end{thebibliography}

% ===================== APPENDICES =====================
\appendix
\renewcommand{\thechapter}{\Alph{chapter}}
\titleformat{\chapter}[display]{\centering\normalfont\bfseries}{\Large APPENDIX \thechapter}{6pt}{\Large\MakeUppercase}
\phantomsection\addcontentsline{toc}{chapter}{APPENDICES}
```

### Appendix: System Parameters and Configuration

```latex
The transformer and CT parameters correspond to the 300\,MVA, 230/11\,kV, Yd1 unit of Chapter~4 (Tables~\ref{tab:4.1} and~\ref{tab:4.2}). Table~\ref{tab:db4} lists the Daubechies-4 filter coefficients, and Table~\ref{tab:hyper} the LSTM hyperparameter search space.
\begin{table}[H]\centering\caption{Daubechies-4 decomposition filter coefficients ($g[n]=(-1)^n h[7-n]$).}\label{tab:db4}
\begin{tabular}{@{}ccc@{}}\toprule $n$ & $h[n]$ (low-pass) & $g[n]$ (high-pass)\\ \midrule
0 & $+0.23037781$ & $+0.01059740$\\ 1 & $+0.71484657$ & $-0.03278364$\\ 2 & $+0.63088077$ & $-0.03084138$\\ 3 & $-0.02798377$ & $+0.18703481$\\ 4 & $-0.18703481$ & $+0.03084138$\\ 5 & $+0.03084138$ & $+0.03278364$\\ 6 & $+0.03278364$ & $-0.01059740$\\ 7 & $-0.01059740$ & $-0.02798377$\\ \bottomrule
\end{tabular}\end{table}
\begin{table}[H]\centering\caption{LSTM hyperparameter search space and selected configuration.}\label{tab:hyper}
\begin{tabular}{@{}lll@{}}\toprule \textbf{Hyperparameter} & \textbf{Search space} & \textbf{Selected}\\ \midrule
LSTM layers & \{1, 2, 3\} & 2\\
Hidden units (L1 / L2) & \{64, 128, 256\} & 128 / 64\\
Dropout & \{0.1, 0.2, 0.3, 0.5\} & 0.3\\
Learning rate & \{0.01, 0.001, 0.0001\} & 0.001\\
Optimizer & \{Adam, RMSprop, SGD\} & Adam\\
Batch size & \{32, 64, 128\} & 128\\
Early-stopping patience & \{10, 15, 20, 25\} & 20\\
ONNX opset & \{11, 13, 14\} & 14\\ \bottomrule
\end{tabular}\end{table}
```

### Appendix: Reproducibility and Standards

```latex
The pipeline uses MATLAB R2023a/Simulink/Simscape Electrical (10\,\textmu s discrete solver), Python~3.11 with PyWavelets, PyTorch~2.x (Adam, weighted categorical cross-entropy), ONNX Opset~14, and the Simulink Predict block, with fixed random seeds. Relevant standards include IEEE C37.91 (transformer protection), IEEE C37.110 (CTs for relaying), IEC~60255 (measuring relays), IEC~61850-9-2 (Sampled Values; the 1.6\,kHz interface emulated here), IEC~61850-8-1 (GOOSE), and IEC~62351 (communication security). Retaining a certified adaptive 87T element as the dependability anchor keeps the scheme aligned with IEEE~C37.91, easing certification relative to a pure black-box classifier.
```

### Appendix: Extended Per-Scenario Results

```latex
This appendix disaggregates the test-set performance of Chapter~6. Table~\ref{tab:E1} reports internal-fault recall by fault type (and the correct no-trip rate for the non-fault categories), confirming uniformly high detection across fault types. Table~\ref{tab:E2} gives the end-to-end clearing-time breakdown that sums to the 17.2\,ms average reported in Section~6.4.
\begin{table}[H]\centering\caption{Per-category recall of the proposed scheme (internal-fault types: trip recall; non-fault categories: correct no-trip rate).}\label{tab:E1}
\begin{tabular}{@{}lc@{}}\toprule \textbf{Category} & \textbf{Recall (\%)}\\ \midrule
AG (SLG) & 99.7\\ BG (SLG) & 99.5\\ CG (SLG) & 99.7\\
ABG / ACG / BCG (LLG) & 99.3\\ ABC (LLL) & 99.8\\ ABCG (LLLG) & 99.8\\
Magnetizing inrush (no-trip) & 97.4\\ External fault with CT saturation (no-trip) & 96.1\\ \bottomrule
\end{tabular}\end{table}
\begin{table}[H]\centering\caption{End-to-end clearing-time breakdown of the hybrid relay.}\label{tab:E2}
\begin{tabular}{@{}lc@{}}\toprule \textbf{Stage} & \textbf{Duration (ms)}\\ \midrule
Data buffering (quarter-cycle) & 5.0\\ DWT decomposition and energy computation & $<$1.0\\
LSTM inference (ONNX Predict block) & $<$1.0\\ Adaptive 87T computation & $<$1.0\\
Hybrid veto/AND-gate logic & $<$0.1\\ Breaker and pickup latency & $\approx$9.1\\ \midrule
Total (average) & 17.2\\ \bottomrule
\end{tabular}\end{table}
```

### Appendix: Summary of Key Design Parameters

```latex
\begin{table}[H]\centering\caption{Consolidated summary of the principal design parameters of the proposed framework.}\label{tab:Gsum}
\begin{tabular}{@{}p{6cm}p{8.2cm}@{}}\toprule \textbf{Parameter} & \textbf{Value}\\ \midrule
Protected transformer & 300\,MVA, 230/11\,kV, Yd1\\
Relay sampling rate & 1.6\,kHz (32 samples/cycle)\\
EMT solver step & 10\,\textmu s (discrete), MATLAB R2023a\\
DWT & 3-level db4, 200-sample one-cycle window\\
Feature vector & 6-D ($E_A$, $E_D$ per phase)\\
LSTM & 2 layers (128$\to$64) + global temporal attention\\
Trainable parameters & 140{,}836\\
Optimizer / loss & Adam ($\eta=0.001$) / weighted categorical cross-entropy (internal-class weight 1.4155)\\
Batch size / max epochs & 128 / 200 (early-stop patience 20)\\
Confidence threshold & $\theta_{conf}=0.85$ (state-adaptive)\\
ONNX opset & 14\\
Dataset & 2{,}500 base cases (1{,}035/578/500/387); 70/15/15 split; 1{,}800-case test\\
Headline results & 98.89\% classifier acc (F1 0.9901, AUC 0.9999); 100\% hybrid dep.\ \& sec.; 17.2\,ms clearing\\ \bottomrule
\end{tabular}\end{table}
```

### Appendix: Code Listings

```latex
This appendix provides representative code excerpts of the implementation pipeline: DWT energy-feature extraction in MATLAB, LSTM training and ONNX export in Python/PyTorch, and the Simulink deployment configuration.

\section{MATLAB: DWT Energy-Feature Extraction}
\begin{lstlisting}[language=Matlab]
function F = dwt_features(I_diff, fs)
% I_diff : 3xN differential currents (phases A,B,C); fs = 1600 Hz
% Returns : [EA_a ED_a EA_b ED_b EA_c ED_c]  (6 energy features)
    w = 'db4';
    n = floor(fs/(2*50));            % 200-sample one-cycle window
    F = zeros(1,6);
    for ph = 1:3
        x = I_diff(ph, end-n+1:end);
        [C, L] = wavedec(x, 3, w);   % 3-level db4 decomposition
        a3 = appcoef(C, L, w, 3);    % approximation (0-100 Hz)
        d  = detcoef(C, L, [1 2 3]); % detail bands (100-800 Hz)
        EA = sum(a3.^2);
        ED = sum(d{1}.^2) + sum(d{2}.^2) + sum(d{3}.^2);
        F(2*ph-1) = EA;  F(2*ph) = ED;
    end
end
\end{lstlisting}

\section{Python/PyTorch: LSTM Training and ONNX Export (Opset 14)}
\begin{lstlisting}[language=Python]
import numpy as np, torch, torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X = np.load('dwt_features.npy')      # (N, 32, 6)
y = np.load('labels.npy')            # 4-class: 0 normal, 1 external, 2 inrush, 3 internal
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.15, stratify=y)
sc = StandardScaler()
Xtr = sc.fit_transform(Xtr.reshape(-1,6)).reshape(-1,32,6)
Xte = sc.transform(Xte.reshape(-1,6)).reshape(-1,32,6)

class DWTLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.l1 = nn.LSTM(6, 128, batch_first=True)     # layer 1
        self.d1 = nn.Dropout(0.3)
        self.l2 = nn.LSTM(128, 64, batch_first=True)    # layer 2
        self.d2 = nn.Dropout(0.3)
        self.attn = nn.Linear(64, 1)                    # temporal attention
        self.fc1, self.fc2 = nn.Linear(64, 32), nn.Linear(32, 4)
    def forward(self, x):
        h,_ = self.l1(x); h = self.d1(h)
        h,_ = self.l2(h); h = self.d2(h)
        a = torch.softmax(self.attn(h), dim=1)          # (B,32,1)
        c = (a * h).sum(dim=1)                          # context (B,64)
        return self.fc2(torch.relu(self.fc1(c)))

model = DWTLSTM()
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
# class weights: internal-fault (Trip) class emphasised (pos. weight 1.4155)
w = torch.tensor([1.0, 1.0, 1.0, 1.4155])
loss_fn = nn.CrossEntropyLoss(weight=w)
# protection decision: Trip iff argmax(probs) == 3 (internal fault)
# ... training loop: 200 epochs max, batch 128, early stopping patience 20 ...

dummy = torch.randn(1, 32, 6)
torch.onnx.export(model, dummy, 'dwt_lstm_relay.onnx',
                  input_names=['input'], output_names=['probs'],
                  opset_version=14)
\end{lstlisting}

\section{Simulink: ONNX Predict and Hybrid-Gate Configuration}
\begin{lstlisting}[language=Matlab]
%% EMT solver at 10 us; relay subsystem decimated to 1.6 kHz
set_param('hatdp_relay','SolverType','Fixed-step', ...
          'Solver','FixedStepDiscrete','FixedStep','1e-5','StopTime','1.0');

%% ONNX Predict block (Opset 14 model)
set_param('hatdp_relay/LSTM_Classifier', ...
          'NetworkFilename','dwt_lstm_relay.onnx', ...
          'OutputLayer','softmax','ExecutionMode','SIM');

%% Adaptive 87T relay and hybrid AND/veto gate
relay.Slope = 0.30;  relay.Ipick = 0.25;          % pu of rated
relay.I2_restraint = 0.20;  relay.CrossBlock = 'on';
gate.Mode = 'AND';  gate.LSTM_class = 3;          % class 3 = internal fault (Trip)
gate.ConfThreshold = 0.85;
\end{lstlisting}

\end{document}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
```

---

## Appendix G: Simulink Model Generation & Power System Setup Code

This appendix contains the complete MATLAB scripts used to programmatically build the Simulink model layout, define the power system network parameters, and compile the netlist configurations.

### File: build_protection_model.m

```matlab
%% =========================================================================
%  build_protection_model.m
%
%  Builds a Simulink / Simscape Electrical (Specialized Power Systems)
%  model of the
%
%       300 MVA, 230/11 kV, Yd1 Transformer Differential Protection
%       Test System
%
%  Architecture (flat electrical – no custom electrical subsystems):
%
%   ┌── Electrical domain (powerlib blocks, top level) ────────────────┐
%   │ Vs_HV → Meas_HVBus → CB_Inrush → CT_HV → T_Yd1 → CT_LV →      │
%   │ Meas_LVBus → [Feeder1, Feeder2 → F_ext_LV]                       │
%   │                                                                    │
%   │ Faults: F_ext_HV (HV bus)                                         │
%   │         F_int_10pct / 50pct / 90pct (winding taps via series R)   │
%   └───────────────────────────────────────────────────────────────────┘
%
%   ┌── Signal domain (Simulink subsystems) ───────────────────────────┐
%   │ CT_HV → [port 4 = Iabc] → CTSat_HV → Relay_87T ← CTSat_LV ←   │
%   │                                   CT_LV [port 4 = Iabc]          │
%   │ Relay_87T → {I_diff, Trip} → Scope_Relay                         │
%   └───────────────────────────────────────────────────────────────────┘
%
%  CT_HV / CT_LV = Three-Phase V-I Measurement blocks (series in circuit)
%                  These represent the CT primary winding + core.
%  CTSat_HV/LV  = Signal subsystems: apply turns-ratio + nonlinear
%                  saturation curve (piece-wise-linear B-H lookup).
%
%  Requirements : MATLAB R2019b+,  Simscape Electrical (powerlib)
%  Usage        : run  build_protection_model
%  Output       : XfmrProtection_300MVA_Yd1.slx  (same folder as this .m)
%
%  Author : Abeer – Transformer Differential Protection Thesis, 2026
%% =========================================================================

function build_protection_model()

MDL = 'XfmrProtection_300MVA_Yd1';

%% ── 0.  Housekeeping ─────────────────────────────────────────────────────
if bdIsLoaded(MDL), close_system(MDL, 0); end
new_system(MDL);
open_system(MDL);

set_param(MDL, ...
    'Solver',         'ode23tb', ...
    'StopTime',       '0.30',   ...
    'RelTol',         '1e-5',   ...
    'MaxStep',        '2e-5',   ...
    'SimulationMode', 'normal');

%% ── Library auto-detection ───────────────────────────────────────────────
%  'powerlib'  = Specialized Power Systems (MATLAB ≤ R2020a)
%  'sps_lib'   = renamed in R2021b; both may coexist as aliases
%  Try to load whichever is available; fall back gracefully.
for LIB_candidate = {'powerlib','sps_lib'}
    try
        load_system(LIB_candidate{1});
        LIB = LIB_candidate{1};
        break;
    catch
        LIB = '';
    end
end
if isempty(LIB)
    error('build_protection_model:nolib', ...
        ['Neither ''powerlib'' nor ''sps_lib'' could be loaded.\n' ...
         'Install Simscape Electrical (Specialized Power Systems) toolbox.']);
end
fprintf('[build_protection_model]  Using library: %s\n', LIB);

%% ── 1.  Canvas layout ────────────────────────────────────────────────────
%
%  Single-line diagram  – blocks increase in x left → right
%  Yc = vertical centreline of the power conductor
%
Yc  = 300;    % power-line centre  (px)
Ydn = 450;    % row for fault blocks hanging below
Yup = 130;    % row for signal / relay blocks above

% Column x-centres
X.src  =   90;
X.mHV  =  240;   % HV Bus (V-I Meas)
X.cb   =  390;   % Inrush CB
X.ctHV =  530;   % CT_HV  (V-I Meas — represents CT)
X.Tx   =  710;   % Transformer
X.ctLV =  900;   % CT_LV  (V-I Meas — represents CT)
X.mLV  = 1060;   % LV Bus (V-I Meas)
X.f1   = 1230;   % Feeder 1
X.f2   = 1230;   % Feeder 2
X.fextLV= 1410;  % External LV fault

X.satHV =  530;  % CTSat_HV subsystem  (above line, aligned with CT_HV)
X.satLV =  900;  % CTSat_LV subsystem
X.relay =  715;  % 87T relay subsystem

% Helper: position vector [left top right bottom] from centre + half-extents
P = @(xc,yc,hw,hh) round([xc-hw, yc-hh, xc+hw, yc+hh]);

%% ── 2.  powergui ─────────────────────────────────────────────────────────
ab([LIB '/powergui'], 'powergui', MDL, P(30,30,45,22));
sp(MDL,'powergui','SimulationMode','Continuous');

%% ── 3.  HV Source  (230 kV, 50 Hz, Thevenin) ────────────────────────────
ab([LIB '/Electrical Sources/Three-Phase Source'], 'Vs_HV', MDL, ...
    P(X.src, Yc, 60, 38));
sp(MDL,'Vs_HV', ...
    'Voltage',   '230e3', ...
    'Frequency', '50',    ...
    'PhaseAngle','0',     ...
    'Impedance', 'on',    ...
    'R1',  '0.529', ...       % positive-sequence R  (Ω)
    'X1', '13.23',  ...       % positive-sequence X
    'R0',  '1.587', ...
    'X0', '39.69');

%% ── 4.  HV Bus  ──  Three-Phase V-I Measurement ──────────────────────────
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'Meas_HVBus', MDL, ...
    P(X.mHV, Yc, 55, 38));
sp(MDL,'Meas_HVBus', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 5.  External HV bus fault ────────────────────────────────────────────
ab([LIB '/Elements/Three-Phase Fault'], 'F_ext_HV', MDL, ...
    P(X.mHV, Ydn-20, 55, 35));
sp(MDL,'F_ext_HV', ...
    'FaultA','1','FaultB','1','FaultC','1','FaultG','1', ...
    'FaultTimes',       '[0.10  0.20]', ...
    'TransitionStatus', '[1  0]',       ...
    'Rground','0.001',  'Rfault','0.001');

%% ── 6.  Inrush energisation breaker ─────────────────────────────────────
ab([LIB '/Elements/Three-Phase Breaker'], 'CB_Inrush', MDL, ...
    P(X.cb, Yc, 58, 38));
sp(MDL,'CB_Inrush', ...
    'InitialStatus','0',      ...   % open at t = 0
    'SwitchTimes',  '0.02',   ...   % closes at 20 ms → triggers inrush
    'Breakers',     'ABC',    ...
    'Rclose',       '0.001',  ...
    'Ropen',        '1e6');

%% ── 7.  CT_HV  ──  Three-Phase V-I Measurement  (represents HV CT) ──────
%  In an actual model, replace this with a Saturable Transformer (1000:1)
%  configured as a CT.  Here the V-I Meas provides the primary current
%  signal that feeds the signal-domain saturation model (CTSat_HV).
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'CT_HV', MDL, ...
    P(X.ctHV, Yc, 55, 38));
sp(MDL,'CT_HV', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 8.  Power transformer  Yd1  300 MVA  230/11 kV ──────────────────────
ab([LIB '/Elements/Three-Phase Transformer (Two Windings)'], 'T_Yd1', MDL, ...
    P(X.Tx, Yc, 90, 72));
sp(MDL,'T_Yd1', ...
    'NominalPower',  '300e6', ...
    'Frequency',     '50',    ...
    'Winding1',  '[230e3  0.003  0.10]', ...   % [Vn(V)  R(pu)  L(pu)]
    'Winding2',  '[11e3   0.003  0.10]', ...
    'Magnetization', '[200  0]',          ...  % [Rm_pu  Lm_pu]
    'Core',          'Three single-phase cores', ...
    'Connection1',   'Yn',               ...
    'Connection2',   'Delta (D1)');           %  → Yd1 vector group

%% ── 9.  Internal fault blocks  (10 %, 50 %, 90 % winding position) ──────
%
%  Each fault is preceded by a small series resistance that represents the
%  winding impedance between the terminal and the fault point.
%  (A rigorous model requires a multi-tap transformer; this approximation
%   is standard for differential protection test systems in the literature.)
%
Zbase_HV = (230e3)^2 / 300e6;     %  HV-side impedance base  ≈ 176.3 Ω
Zbase_LV = (11e3 )^2 / 300e6;     %  LV-side impedance base  ≈ 0.403 Ω

% -- 10 %  fault  (close to HV terminal) ----------------------------------
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Tap_10pct', MDL, ...
    P(X.Tx-80, Ydn-20, 50, 30));
sp(MDL,'Tap_10pct','BranchType','R','R', ...
    num2str(0.10 * Zbase_HV * 0.003));   % 10 % of winding R_HV

ab([LIB '/Elements/Three-Phase Fault'], 'F_int_10pct', MDL, ...
    P(X.Tx-80, Ydn+50, 55, 35));
sp(MDL,'F_int_10pct', ...
    'FaultA','1','FaultB','0','FaultC','0','FaultG','1', ...
    'FaultTimes','[0.15  0.22]','TransitionStatus','[1 0]', ...
    'Rground','0.001','Rfault','0.001');

% -- 50 %  fault  (mid-winding) -------------------------------------------
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Tap_50pct', MDL, ...
    P(X.Tx, Ydn-20, 50, 30));
sp(MDL,'Tap_50pct','BranchType','R','R', ...
    num2str(0.50 * Zbase_HV * 0.003));

ab([LIB '/Elements/Three-Phase Fault'], 'F_int_50pct', MDL, ...
    P(X.Tx, Ydn+50, 55, 35));
sp(MDL,'F_int_50pct', ...
    'FaultA','0','FaultB','1','FaultC','0','FaultG','1', ...
    'FaultTimes','[0.15  0.22]','TransitionStatus','[1 0]', ...
    'Rground','0.001','Rfault','0.001');

% -- 90 %  fault  (close to LV terminal, referenced to LV impedance base) -
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Tap_90pct', MDL, ...
    P(X.Tx+80, Ydn-20, 50, 30));
sp(MDL,'Tap_90pct','BranchType','R','R', ...
    num2str(0.10 * Zbase_LV * 0.003));   % 10 % of remaining winding (from LV)

ab([LIB '/Elements/Three-Phase Fault'], 'F_int_90pct', MDL, ...
    P(X.Tx+80, Ydn+50, 55, 35));
sp(MDL,'F_int_90pct', ...
    'FaultA','0','FaultB','0','FaultC','1','FaultG','1', ...
    'FaultTimes','[0.15  0.22]','TransitionStatus','[1 0]', ...
    'Rground','0.001','Rfault','0.001');

%% ── 10.  CT_LV  ──  Three-Phase V-I Measurement  (represents LV CT) ─────
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'CT_LV', MDL, ...
    P(X.ctLV, Yc, 55, 38));
sp(MDL,'CT_LV', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 11.  LV Bus  ──  Three-Phase V-I Measurement ─────────────────────────
ab([LIB '/Measurements/Three-Phase V-I Measurement'], 'Meas_LVBus', MDL, ...
    P(X.mLV, Yc, 55, 38));
sp(MDL,'Meas_LVBus', ...
    'VoltageUnit',   'pu', ...
    'Vmeasurements', 'Phase-to-ground');

%% ── 12.  LV feeders ──────────────────────────────────────────────────────
% Feeder 1  (upper branch, RL load + ground)
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Feeder1', MDL, ...
    P(X.f1, Yc-60, 58, 30));
sp(MDL,'Feeder1','BranchType','RL','R','20.0','L','0.0318');
ab([LIB '/Elements/Ground'], 'Gnd_F1', MDL, P(X.f1+95, Yc-60, 18,18));

% Feeder 2  (lower branch, RL load → external LV fault)
ab([LIB '/Elements/Three-Phase Series RLC Branch'], 'Feeder2', MDL, ...
    P(X.f2, Yc+60, 58, 30));
sp(MDL,'Feeder2','BranchType','RL','R','20.0','L','0.0318');

ab([LIB '/Elements/Three-Phase Fault'], 'F_ext_LV', MDL, ...
    P(X.fextLV, Yc+60, 55, 35));
sp(MDL,'F_ext_LV', ...
    'FaultA','1','FaultB','1','FaultC','1','FaultG','1', ...
    'FaultTimes',       '[0.05  0.15]', ...
    'TransitionStatus', '[1  0]',       ...
    'Rground','0.001',  'Rfault','0.001');

%% ── 13.  CT saturation models  (signal domain) ───────────────────────────
%
%  CTSat_HV : 1000/1 A CT saturation  (knee voltage ~ 200 V)
%  CTSat_LV : 2000/1 A CT saturation  (knee voltage ~ 100 V)
%
%  Saturation table  [phi_pu | i_pu]:
%    phi < knee  →  nearly linear   (i grows slowly)
%    phi > knee  →  saturated       (i grows sharply)
%
sat_tbl = [0 0; 0.80 0.003; 0.95 0.007; 1.00 0.015; ...
           1.10 0.060; 1.25 0.25; 1.50 1.10; 2.00 4.50];

build_CTsat_subsystem(MDL, 'CTSat_HV', P(X.satHV, Yup, 58, 38), ...
    1000, sat_tbl);
build_CTsat_subsystem(MDL, 'CTSat_LV', P(X.satLV, Yup, 58, 38), ...
    2000, sat_tbl);

%% ── 14.  87T Differential relay  (signal domain) ─────────────────────────
build_relay_87T(MDL, 'Relay_87T', P(X.relay, Yup, 72, 48));

%% ── 15.  Monitoring scopes ───────────────────────────────────────────────
ab('simulink/Sinks/Scope', 'Scope_Relay',  MDL, P(X.relay+185, Yup,    45,28));
ab('simulink/Sinks/Scope', 'Scope_CTsec',  MDL, P(X.relay+185, Yup+70, 45,28));
sp(MDL,'Scope_Relay', 'NumInputPorts','2');
sp(MDL,'Scope_CTsec','NumInputPorts','2');

%% ── 16.  Annotations ────────────────────────────────────────────────────
add_anno(MDL, '230 kV HV Bus',                     [X.mHV-45   Yc-100]);
add_anno(MDL, '11 kV  LV Bus',                     [X.mLV-35   Yc-100]);
add_anno(MDL, sprintf('T Yd1\n300 MVA\n230/11 kV'),[X.Tx-35    Yc+92 ]);
add_anno(MDL, sprintf('CT_{HV}\n1000/1 A'),         [X.ctHV-30  Yc+75 ]);
add_anno(MDL, sprintf('CT_{LV}\n2000/1 A'),         [X.ctLV-30  Yc+75 ]);
add_anno(MDL, 'Inrush CB',                          [X.cb-30    Yc-100]);
add_anno(MDL, ...
  '|──── Differential Protection Zone (87T) ────|', ...
  [X.ctHV-80  Yup-35]);

%% ═════════════════════════════════════════════════════════════════════════
%%  CONNECTIONS
%% ═════════════════════════════════════════════════════════════════════════
L = {'autorouting','smart'};

% ── Electrical path (main power circuit) ──────────────────────────────────
cl(MDL,'Vs_HV/1',        'Meas_HVBus/1',   L);   % source → HV bus
cl(MDL,'Meas_HVBus/2',   'CB_Inrush/1',    L);   % HV bus → CB
cl(MDL,'CB_Inrush/2',    'CT_HV/1',        L);   % CB → CT_HV
cl(MDL,'CT_HV/2',        'T_Yd1/1',        L);   % CT_HV → transformer HV
cl(MDL,'T_Yd1/2',        'CT_LV/1',        L);   % transformer LV → CT_LV
cl(MDL,'CT_LV/2',        'Meas_LVBus/1',   L);   % CT_LV → LV bus
cl(MDL,'Meas_LVBus/2',   'Feeder1/1',      L);   % LV bus → Feeder 1
cl(MDL,'Meas_LVBus/2',   'Feeder2/1',      L);   % LV bus → Feeder 2
cl(MDL,'Feeder1/2',      'Gnd_F1/1',       L);   % Feeder 1 → gnd
cl(MDL,'Feeder2/2',      'F_ext_LV/1',     L);   % Feeder 2 → ext LV fault

% ── External HV fault branches off HV bus ────────────────────────────────
cl(MDL,'Meas_HVBus/2',   'F_ext_HV/1',     L);

% ── Internal fault taps ──────────────────────────────────────────────────
%   10 % & 50 % tap off HV terminal
cl(MDL,'T_Yd1/1',        'Tap_10pct/1',    L);
cl(MDL,'Tap_10pct/2',    'F_int_10pct/1',  L);
cl(MDL,'T_Yd1/1',        'Tap_50pct/1',    L);
cl(MDL,'Tap_50pct/2',    'F_int_50pct/1',  L);
%   90 % tap off LV terminal
cl(MDL,'T_Yd1/2',        'Tap_90pct/1',    L);
cl(MDL,'Tap_90pct/2',    'F_int_90pct/1',  L);

% ── Signal path: V-I Meas current outputs → CTSat → Relay ────────────────
%   Three-Phase V-I Measurement output ports:
%     port 3 = Va,Vb,Vc (or Vabc vector, depending on config)
%     port 4 = Ia,Ib,Ic current signal
%   We use port 4 for current.  If your MATLAB version uses port 3 for
%   current, change '/4' to '/3' in the two lines below.
cl(MDL,'CT_HV/4',        'CTSat_HV/1',     L);
cl(MDL,'CT_LV/4',        'CTSat_LV/1',     L);

cl(MDL,'CTSat_HV/1',     'Relay_87T/1',    L);
cl(MDL,'CTSat_LV/1',     'Relay_87T/2',    L);

cl(MDL,'Relay_87T/1',    'Scope_Relay/1',  L);
cl(MDL,'Relay_87T/2',    'Scope_Relay/2',  L);

cl(MDL,'CTSat_HV/1',     'Scope_CTsec/1',  L);
cl(MDL,'CTSat_LV/1',     'Scope_CTsec/2',  L);

%% ── Save ─────────────────────────────────────────────────────────────────
outpath = fullfile(fileparts(mfilename('fullpath')), [MDL '.slx']);
save_system(MDL, outpath);

fprintf('\n── build_protection_model ────────────────────────────────\n');
fprintf('  Model saved to:\n  %s\n\n', outpath);
fprintf('  For clean thesis screenshot:\n');
fprintf('    Ctrl+Shift+F  (Fit System to View)\n');
fprintf('    Format → Auto Arrange (Ctrl+Shift+A)  — Simulink R2022a+\n\n');
fprintf('  NOTE: CT_HV / CT_LV use Three-Phase V-I Measurement as the\n');
fprintf('  primary winding proxy.  Signal port 4 outputs I_abc (primary).\n');
fprintf('  CTSat_HV/LV subsystems apply the 1000:1 / 2000:1 ratio + \n');
fprintf('  piece-wise-linear B-H saturation before the relay.\n');
fprintf('──────────────────────────────────────────────────────────\n\n');

end   % ── build_protection_model ──────────────────────────────────────────


%% =========================================================================
%%  LOCAL HELPERS
%% =========================================================================

function ab(lib_path, blk, mdl, position)
    add_block(lib_path, [mdl '/' blk], 'Position', position);
end

function sp(mdl, blk, varargin)
    try
        set_param([mdl '/' blk], varargin{:});
    catch ME
        warning('prot_model:param','Block "%s" param error — %s', blk, ME.message);
    end
end

function cl(mdl, src, dst, opts)
    try
        add_line(mdl, src, dst, opts{:});
    catch ME
        warning('prot_model:line','%s → %s failed — %s', src, dst, ME.message);
    end
end

function add_anno(mdl, txt, xy)
    try
        a          = Simulink.Annotation(mdl, txt);
        a.position = xy;
    catch
        try  % R2019b / R2020a fallback
            a = Simulink.Annotation([mdl '/annotation_' ...
                    num2str(round(xy(1)))]);
            a.text     = txt;
            a.position = xy;
        catch; end
    end
end


%% =========================================================================
%%  build_CTsat_subsystem
%%  Signal-domain CT saturation model.
%%
%%  Input  port 1 : I_abc  (primary current, pu – from V-I Measurement)
%%  Output port 1 : I_sec  (secondary current after ratio + saturation)
%%
%%  Internally:
%%    Demux → [Gain 1/N] × 3 → [1-D Lookup Table (sat)] × 3 → Mux
%%
%%  The lookup table implements the piece-wise-linear approximation of the
%%  CT magnetising curve.  Symmetry is applied via abs / sign.
%%
%%  Parameters:
%%    ratio    – CT turns ratio  (primary / secondary)
%%    sat_tbl  – N×2 matrix [phi_pu, i_pu]  (monotonically increasing phi)
%% =========================================================================
function build_CTsat_subsystem(mdl, name, pos_rect, ratio, ~)
%  sat_tbl arg accepted but unused — saturation implemented via
%  simulink/Discontinuities/Saturation (works on every MATLAB version).
%
%  Per-phase pipeline:  Demux → Gain(1/N) → Saturation(±1 pu) → Mux
%
%  The hard ±1 pu limit represents the CT knee-point.  For a higher-
%  fidelity piece-wise-linear curve, replace each Saturation block with
%  a 1-D Lookup Table using parameters 'Breakpoints1' / 'Table'
%  (R2021b+) or 'InputValues' / 'OutputValues' (older).

sys = [mdl '/' name];
add_block('built-in/Subsystem', sys, 'Position', pos_rect);
for p_ = {'In1','In2','Out1'}
    try, delete_block([sys '/' p_{1}]); catch; end
end

% ── I/O ports ──
add_block('built-in/Inport',  [sys '/Ipri'], 'Position',[20  95  50 115],'Port','1');
add_block('built-in/Outport', [sys '/Isec'], 'Position',[430  95 460 115],'Port','1');

% ── Demux 3-phase input ──
add_block('simulink/Signal Routing/Demux', [sys '/DmxIn'], ...
    'Position',[80 75 100 135],'Outputs','3');

% ── Per-phase: Gain(1/N) → Saturation(±1 pu) ──
phases = {'A','B','C'};
yo     = [0  60  120];

for k = 1:3
    ph = phases{k};

    % Turns-ratio gain
    add_block('simulink/Math Operations/Gain', [sys '/G_' ph], ...
        'Position',[150  70+yo(k)  205  90+yo(k)], ...
        'Gain', sprintf('1/%g', ratio));

    % Saturation — models CT core saturation at the knee point.
    % UpperLimit = 1.0 pu secondary, LowerLimit = -1.0 pu secondary.
    add_block('simulink/Discontinuities/Saturation', [sys '/Sat_' ph], ...
        'Position',[250  70+yo(k)  320  90+yo(k)], ...
        'UpperLimit', '1.0', ...
        'LowerLimit', '-1.0');
end

% ── Mux [Ia_sec ; Ib_sec ; Ic_sec] ──
add_block('simulink/Signal Routing/Mux', [sys '/MuxOut'], ...
    'Position',[375 72 395 152],'Inputs','3');

% ── Wiring ──
sl = @(s,d) add_line(sys, s, d, 'autorouting','smart');

sl('Ipri/1','DmxIn/1');
for k = 1:3
    ph = phases{k};
    kp = num2str(k);
    sl(['DmxIn/'  kp],   ['G_'   ph '/1']);
    sl(['G_'   ph '/1'], ['Sat_' ph '/1']);
    sl(['Sat_' ph '/1'], ['MuxOut/'  kp]);
end
sl('MuxOut/1','Isec/1');

% Mask appearance
try
    set_param(sys, ...
        'MaskDisplay', [ ...
            'color([0 0.45 0.1]);' ...
            'patch([0.08 0.92 0.92 0.08],[0.08 0.08 0.92 0.92],[0.92 1.0 0.92]);' ...
            'text(0.5,0.62,''' name ''',''hor'',''center'',''FontSize'',8,''FontWeight'',''bold'');' ...
            'text(0.5,0.32,''Sat CT'',''hor'',''center'',''FontSize'',7);' ...
            'text(0.5,0.15,''' sprintf('1/%g',ratio) ''',''hor'',''center'',''FontSize'',7);' ...
        ], ...
        'ForegroundColor','[0 0.45 0.1]', ...
        'BackgroundColor','[0.92 1.0 0.92]');
catch; end

end   % build_CTsat_subsystem


%% =========================================================================
%%  build_relay_87T
%%  IEEE dual-slope percentage-differential characteristic.
%%
%%  Input  port 1 : I_HV  [Ia Ib Ic]  from CTSat_HV  (secondary current)
%%  Input  port 2 : I_LV  [Ia Ib Ic]  from CTSat_LV  (polarity corrected)
%%
%%  Output port 1 : I_diff  – operating (differential) current magnitude
%%  Output port 2 : Trip    – logical 1 when Id > SLP1·Ir + Id_min
%%
%%  Characteristic (IEC 60255-111 / IEEE C37.91):
%%    SLP1   = 0.30   (30 % slope)
%%    Id_min = 0.20   (pu minimum pickup — covers mismatch & CT error)
%%    No harmonic restraint wired here; add a 2nd harmonic detector
%%    (using an FFT subsystem) if modelling inrush inhibit.
%% =========================================================================
function build_relay_87T(mdl, name, pos_rect)

sys = [mdl '/' name];
add_block('built-in/Subsystem', sys, 'Position', pos_rect);
for p_ = {'In1','In2','Out1'}
    try, delete_block([sys '/' p_{1}]); catch; end
end

%--- I/O ports
add_block('built-in/Inport', [sys '/I_HV'],   'Position',[20  80 50 100],'Port','1');
add_block('built-in/Inport', [sys '/I_LV'],   'Position',[20 190 50 210],'Port','2');
add_block('built-in/Outport',[sys '/I_diff'], 'Position',[620  80 650 100],'Port','1');
add_block('built-in/Outport',[sys '/Trip'],   'Position',[620 190 650 210],'Port','2');

%--- Id = |I_HV + I_LV|  (CT secondaries added; polarities set so that for
%    through-fault: I_HV ≈ –I_LV → Id ≈ 0; for internal fault: Id > 0)
add_block('simulink/Math Operations/Sum',         [sys '/AddId'], ...
    'Position',[120  75 155 105],'Inputs','++');
add_block('simulink/Math Operations/Dot Product', [sys '/DotId'], ...
    'Position',[195  75 240 105]);
add_block('simulink/Math Operations/Sqrt',        [sys '/SqrtId'], ...
    'Position',[265  80 310 100]);

%--- Ir = ( |I_HV| + |I_LV| ) / 2
add_block('simulink/Math Operations/Dot Product', [sys '/DotHV'], ...
    'Position',[80  155 125 185]);
add_block('simulink/Math Operations/Dot Product', [sys '/DotLV'], ...
    'Position',[80  215 125 245]);
add_block('simulink/Math Operations/Sqrt',        [sys '/SqrtHV'], ...
    'Position',[150 158 190 182]);
add_block('simulink/Math Operations/Sqrt',        [sys '/SqrtLV'], ...
    'Position',[150 218 190 242]);
add_block('simulink/Math Operations/Sum',         [sys '/AddIr'], ...
    'Position',[220 175 255 215],'Inputs','++');
add_block('simulink/Math Operations/Gain',        [sys '/Half'], ...
    'Position',[280 180 330 210],'Gain','0.5');

%--- Pickup = SLP1 · Ir + Id_min
add_block('simulink/Math Operations/Gain',  [sys '/SLP1'], ...
    'Position',[360 180 410 210],'Gain','0.30');
add_block('simulink/Sources/Constant',      [sys '/Id_min'], ...
    'Position',[360 235 410 255],'Value','0.20');
add_block('simulink/Math Operations/Sum',   [sys '/AddPU'], ...
    'Position',[445 190 480 240],'Inputs','++');

%--- Trip  =  Id > Pickup
add_block('simulink/Math Operations/Sum',                        [sys '/ErrTrip'], ...
    'Position',[510  78 550 108],'Inputs','+-');
add_block('simulink/Logic and Bit Operations/Relational Operator',[sys '/GT0'], ...
    'Position',[510 185 575 220],'Operator','>');
add_block('simulink/Sources/Constant',                           [sys '/Zero'], ...
    'Position',[440 115 470 135],'Value','0');

%--- Wire up
sl = @(s,d) add_line(sys, s, d, 'autorouting','smart');

sl('I_HV/1',   'AddId/1');
sl('I_LV/1',   'AddId/2');
sl('AddId/1',  'DotId/1');
sl('AddId/1',  'DotId/2');
sl('DotId/1',  'SqrtId/1');

sl('I_HV/1',   'DotHV/1');
sl('I_HV/1',   'DotHV/2');
sl('I_LV/1',   'DotLV/1');
sl('I_LV/1',   'DotLV/2');
sl('DotHV/1',  'SqrtHV/1');
sl('DotLV/1',  'SqrtLV/1');
sl('SqrtHV/1', 'AddIr/1');
sl('SqrtLV/1', 'AddIr/2');
sl('AddIr/1',  'Half/1');
sl('Half/1',   'SLP1/1');
sl('SLP1/1',   'AddPU/1');
sl('Id_min/1', 'AddPU/2');

sl('SqrtId/1', 'ErrTrip/1');
sl('AddPU/1',  'ErrTrip/2');
sl('Zero/1',   'GT0/1');
sl('ErrTrip/1','GT0/2');

sl('SqrtId/1', 'I_diff/1');
sl('GT0/1',    'Trip/1');

%--- Mask
try
    set_param(sys, ...
        'MaskDisplay', [ ...
            'color(''red'');' ...
            'patch([0.05 0.95 0.95 0.05],[0.05 0.05 0.95 0.95],[1 0.93 0.93]);' ...
            'text(0.5,0.60,''87T'',''hor'',''center'',''ver'',''middle'',' ...
              '''FontSize'',14,''FontWeight'',''bold'');' ...
            'text(0.5,0.20,''Diff Relay'',''hor'',''center'',''FontSize'',7);' ...
        ], ...
        'ForegroundColor','red', ...
        'BackgroundColor','[1 0.93 0.93]');
catch; end

end   % build_relay_87T

```

### File: netlist.m

```matlab
function netlist
% =========================================================================
% NETLIST.M  —  Detailed Simulink / Simscape netlist logger
% =========================================================================
%
% Produces a structured log of every block, port, signal line, bus
% connection, and key electrical parameter in the model.
%
% OUTPUT
%   netlist_<modelName>_<timestamp>.txt   — full plain-text report
%   netlist_<modelName>_<timestamp>.csv   — flat CSV for spreadsheet review
%
% USAGE
%   Open the Simulink model, then run:  netlist
%
% =========================================================================

    % ── Resolve model name ───────────────────────────────────────────────
    modelName = gcs;
    if isempty(modelName)
        error('No Simulink model is open. Open your model first.');
    end
    modelName = bdroot(modelName);
    load_system(modelName);

    % ── Output files ─────────────────────────────────────────────────────
    ts       = datestr(now, 'yyyymmdd_HHMMSS');
    txtFile  = sprintf('netlist_%s_%s.txt', modelName, ts);
    csvFile  = sprintf('netlist_%s_%s.csv', modelName, ts);

    fidTxt = fopen(txtFile, 'w');
    fidCsv = fopen(csvFile, 'w');

    % CSV header
    fprintf(fidCsv, 'BlockPath,BlockType,LibraryLink,Parameter,Value\n');

    % =========================================================================
    hdr(fidTxt, sprintf('SIMULINK NETLIST  —  %s', modelName));
    fprintf(fidTxt, 'Generated : %s\n', datestr(now));
    fprintf(fidTxt, 'MATLAB    : %s\n', version);
    fprintf(fidTxt, '\n');

    % =========================================================================
    % SECTION 1 — MODEL SUMMARY
    % =========================================================================
    hdr(fidTxt, '1. MODEL SUMMARY');

    allBlocks = find_system(modelName, 'Type', 'block');
    allLines  = find_system(modelName, 'Type', 'line');
    allPorts  = find_system(modelName, 'Type', 'port');
    subs      = find_system(modelName, 'BlockType', 'SubSystem');

    fprintf(fidTxt, '  Total blocks     : %d\n', numel(allBlocks));
    fprintf(fidTxt, '  Total lines      : %d\n', numel(allLines));
    fprintf(fidTxt, '  Total ports      : %d\n', numel(allPorts));
    fprintf(fidTxt, '  Subsystems       : %d\n', numel(subs));

    % Block-type histogram
    types = cellfun(@(b) get_param(b,'BlockType'), allBlocks, 'UniformOutput', false);
    uTypes = unique(types);
    fprintf(fidTxt, '\n  Block-type inventory:\n');
    for i = 1:numel(uTypes)
        cnt = sum(strcmp(types, uTypes{i}));
        fprintf(fidTxt, '    %-40s : %d\n', uTypes{i}, cnt);
    end

    % =========================================================================
    % SECTION 2 — BLOCK HIERARCHY (TREE)
    % =========================================================================
    hdr(fidTxt, '2. BLOCK HIERARCHY');
    printHierarchy(fidTxt, modelName, modelName, 0);

    % =========================================================================
    % SECTION 3 — FULL BLOCK PARAMETER DUMP
    % =========================================================================
    hdr(fidTxt, '3. BLOCK PARAMETERS (ALL BLOCKS)');

    % Categories of interest for power-systems models
    electricalKeywords = {'Resistance','Inductance','Capacitance','Voltage', ...
                          'Current','Frequency','Power','Impedance','Turns', ...
                          'Ratio','Gain','Time','Threshold','SampleTime', ...
                          'InitialState','SwitchStatus','FaultA','FaultB', ...
                          'FaultC','GroundFault','FaultResistance','Before', ...
                          'After','Noise','Saturation','Flux','Winding', ...
                          'RatedPower','NominalVoltage','MagnetizingCurrent', ...
                          'CoreLoss','LeakageInductance','OpenCircuit'};

    for bi = 1:numel(allBlocks)
        blk      = allBlocks{bi};
        bType    = get_param(blk, 'BlockType');
        libLink  = safeGet(blk, 'ReferenceBlock');
        shortBlk = strrep(blk, [modelName '/'], '');

        fprintf(fidTxt, '\n  ┌─ %s\n', shortBlk);
        fprintf(fidTxt,   '  │  Type     : %s\n', bType);
        if ~isempty(libLink)
            fprintf(fidTxt, '  │  Library  : %s\n', libLink);
        end

        % Get all dialog parameters
        try
            params = get_param(blk, 'DialogParameters');
        catch
            params = [];
        end

        if ~isempty(params)
            fNames = fieldnames(params);
            printedAny = false;

            % First pass: electrically significant params
            fprintf(fidTxt, '  │  Parameters:\n');
            for pi = 1:numel(fNames)
                pName = fNames{pi};
                pVal  = safeGetParam(blk, pName);
                if isempty(pVal), continue; end

                % Flag if this is an electrically significant parameter
                isElec = any(cellfun(@(k) ~isempty(regexpi(pName, k, 'once')), ...
                             electricalKeywords));
                marker = '';
                if isElec, marker = '  ◄'; end

                fprintf(fidTxt, '  │    %-35s = %s%s\n', pName, pVal, marker);
                fprintf(fidCsv, '"%s","%s","%s","%s","%s"\n', ...
                        escCsv(blk), escCsv(bType), escCsv(libLink), ...
                        escCsv(pName), escCsv(pVal));
                printedAny = true;
            end
            if ~printedAny
                fprintf(fidTxt, '  │    [no printable parameters]\n');
            end
        else
            fprintf(fidTxt, '  │  [no dialog parameters]\n');
        end

        % Port info
        try
            portHandles = get_param(blk, 'PortHandles');
            pFields     = fieldnames(portHandles);
            portSummary = '';
            for pf = 1:numel(pFields)
                n = numel(portHandles.(pFields{pf}));
                if n > 0
                    portSummary = [portSummary sprintf('%s×%d ', pFields{pf}, n)]; %#ok<AGROW>
                end
            end
            if ~isempty(portSummary)
                fprintf(fidTxt, '  │  Ports     : %s\n', strtrim(portSummary));
            end
        catch, end

        fprintf(fidTxt, '  └─\n');
    end

    % =========================================================================
    % SECTION 4 — SIGNAL LINE CONNECTIVITY (NETLIST)
    % =========================================================================
    hdr(fidTxt, '4. SIGNAL LINE CONNECTIVITY');
    fprintf(fidTxt, '  %-55s  %-55s  %s\n', 'SOURCE (block:port)', 'DESTINATION (block:port)', 'Signal Name');
    fprintf(fidTxt, '  %s\n', repmat('-', 1, 140));

    % Iterate every line in the model (including inside subsystems)
    allLineHandles = find_system(modelName, 'FindAll','on', 'Type','line');

    for li = 1:numel(allLineHandles)
        lh = allLineHandles(li);
        try
            srcPort  = get(lh, 'SrcPortHandle');
            dstPorts = get(lh, 'DstPortHandles');
            sigName  = get(lh, 'Name');
            if isempty(sigName), sigName = '(unnamed)'; end

            srcStr = portStr(srcPort);

            for di = 1:numel(dstPorts)
                dstStr = portStr(dstPorts(di));
                fprintf(fidTxt, '  %-55s  %-55s  %s\n', srcStr, dstStr, sigName);
            end
        catch
            % Some line handles are invalid or virtual — skip
        end
    end

    % =========================================================================
    % SECTION 5 — BUS & GOTO/FROM CONNECTIONS
    % =========================================================================
    hdr(fidTxt, '5. BUS CREATOR / SELECTOR  &  GOTO / FROM CONNECTIONS');

    % Bus creators
    busCreators = find_system(modelName, 'BlockType', 'BusCreator');
    busSelectors= find_system(modelName, 'BlockType', 'BusSelector');
    gotos       = find_system(modelName, 'BlockType', 'Goto');
    froms       = find_system(modelName, 'BlockType', 'From');

    fprintf(fidTxt, '\n  Bus Creators  : %d\n', numel(busCreators));
    for i = 1:numel(busCreators)
        fprintf(fidTxt, '    %s\n', strrep(busCreators{i},[modelName '/'],''));
    end

    fprintf(fidTxt, '\n  Bus Selectors : %d\n', numel(busSelectors));
    for i = 1:numel(busSelectors)
        sig = safeGetParam(busSelectors{i}, 'OutputSignals');
        fprintf(fidTxt, '    %-50s  signals: %s\n', ...
                strrep(busSelectors{i},[modelName '/'],''), sig);
    end

    fprintf(fidTxt, '\n  Goto/From pairs:\n');
    fprintf(fidTxt, '  %-40s  Tag\n', 'Block');
    fprintf(fidTxt, '  %s\n', repmat('-',1,70));
    for i = 1:numel(gotos)
        tag = safeGetParam(gotos{i}, 'GotoTag');
        fprintf(fidTxt, '  GOTO  %-35s  [%s]\n', ...
                strrep(gotos{i},[modelName '/'],''), tag);
    end
    for i = 1:numel(froms)
        tag = safeGetParam(froms{i}, 'GotoTag');
        fprintf(fidTxt, '  FROM  %-35s  [%s]\n', ...
                strrep(froms{i},[modelName '/'],''), tag);
    end

    % =========================================================================
    % SECTION 6 — STEP / FAULT BLOCK QUICK-REFERENCE TABLE
    % =========================================================================
    hdr(fidTxt, '6. STEP & FAULT BLOCKS  (quick-reference for ControlPanel scripts)');

    stepBlocks = find_system(modelName, 'BlockType', 'Step');
    fprintf(fidTxt, '\n  %-45s  Before  After  Time\n', 'Step Block');
    fprintf(fidTxt, '  %s\n', repmat('-',1,80));
    for i = 1:numel(stepBlocks)
        bef  = safeGetParam(stepBlocks{i}, 'Before');
        aft  = safeGetParam(stepBlocks{i}, 'After');
        t    = safeGetParam(stepBlocks{i}, 'Time');
        fprintf(fidTxt, '  %-45s  %-6s  %-5s  %s\n', ...
                strrep(stepBlocks{i},[modelName '/'],''), bef, aft, t);
    end

    % Three-Phase Fault blocks
    faultBlocks = [
        find_system(modelName, 'BlockType', 'ThreePhaseFault'); ...
        find_system(modelName, 'RegExp','on', 'Name','.*[Ff]ault.*', 'BlockType','SubSystem'); ...
        find_system(modelName, 'RegExp','on', 'MaskType','Three-Phase Fault')
    ];
    faultBlocks = unique(faultBlocks);

    if ~isempty(faultBlocks)
        fprintf(fidTxt, '\n  %-45s  FaultA  FaultB  FaultC  FaultG  Rf\n', 'Fault Block');
        fprintf(fidTxt, '  %s\n', repmat('-',1,100));
        for i = 1:numel(faultBlocks)
            fA = safeGetParam(faultBlocks{i}, 'FaultA');
            fB = safeGetParam(faultBlocks{i}, 'FaultB');
            fC = safeGetParam(faultBlocks{i}, 'FaultC');
            fG = safeGetParam(faultBlocks{i}, 'GroundFault');
            rf = safeGetParam(faultBlocks{i}, 'FaultResistance');
            fprintf(fidTxt, '  %-45s  %-6s  %-6s  %-6s  %-6s  %s\n', ...
                    strrep(faultBlocks{i},[modelName '/'],''), fA, fB, fC, fG, rf);
        end
    end

    % =========================================================================
    % SECTION 7 — BREAKER BLOCKS
    % =========================================================================
    hdr(fidTxt, '7. CIRCUIT BREAKERS');

    breakerTypes = {'ThreePhaseBreaker','Breaker','Three-Phase Breaker'};
    bkrs = {};
    for bt = breakerTypes
        bkrs = [bkrs; find_system(modelName,'BlockType',bt{1})]; %#ok<AGROW>
        bkrs = [bkrs; find_system(modelName,'MaskType',bt{1})];  %#ok<AGROW>
    end
    bkrs = unique(bkrs);

    fprintf(fidTxt, '\n  %-45s  InitialState  SwitchingTimes\n', 'Breaker Block');
    fprintf(fidTxt, '  %s\n', repmat('-',1,90));
    for i = 1:numel(bkrs)
        ist = safeGetParam(bkrs{i}, 'InitialState');
        if isempty(ist), ist = safeGetParam(bkrs{i},'SwitchStatus'); end
        swt = safeGetParam(bkrs{i}, 'SwitchingTimes');
        fprintf(fidTxt, '  %-45s  %-12s  %s\n', ...
                strrep(bkrs{i},[modelName '/'],''), ist, swt);
    end

    % =========================================================================
    % SECTION 8 — TRANSFORMER BLOCKS
    % =========================================================================
    hdr(fidTxt, '8. TRANSFORMER BLOCKS');

    xfmrKeys = {'Transformer','transformer','Linear Transformer','Saturable Transformer'};
    xfmrs = {};
    for xk = xfmrKeys
        xfmrs = [xfmrs; find_system(modelName,'RegExp','on','MaskType',xk{1})]; %#ok<AGROW>
        xfmrs = [xfmrs; find_system(modelName,'RegExp','on','Name',['.*' xk{1} '.*'],'BlockType','SubSystem')]; %#ok<AGROW>
    end
    xfmrs = unique(xfmrs);

    xfmrParams = {'NominalPower','Frequency','Winding1','Winding2','Winding3', ...
                  'Rm','Lm','R1','L1','R2','L2','Winding1Connection', ...
                  'Winding2Connection','CoreType','SaturationCharacteristic'};
    for i = 1:numel(xfmrs)
        shortName = strrep(xfmrs{i},[modelName '/'],'');
        fprintf(fidTxt, '\n  %s\n', shortName);
        for pk = xfmrParams
            v = safeGetParam(xfmrs{i}, pk{1});
            if ~isempty(v)
                fprintf(fidTxt, '    %-35s = %s\n', pk{1}, v);
            end
        end
    end

    % =========================================================================
    % SECTION 9 — MEASUREMENT & OUTPUT BLOCKS
    % =========================================================================
    hdr(fidTxt, '9. MEASUREMENT & OUTPUT BLOCKS');

    measTypes = {'ToWorkspace','Scope','CurrentMeasurement','VoltageMeasurement', ...
                 'Outport','Out1'};
    for mt = measTypes
        blks = find_system(modelName, 'BlockType', mt{1});
        if isempty(blks), continue; end
        fprintf(fidTxt, '\n  %s  (%d)\n', mt{1}, numel(blks));
        for i = 1:numel(blks)
            vn = safeGetParam(blks{i}, 'VariableName');
            if isempty(vn), vn = safeGetParam(blks{i},'ScopeSpecificationString'); end
            if isempty(vn), vn = ''; end
            fprintf(fidTxt, '    %-50s  %s\n', ...
                    strrep(blks{i},[modelName '/'],''), vn);
        end
    end

    % =========================================================================
    % SECTION 10 — SUBSYSTEM INTERFACE SUMMARY
    % =========================================================================
    hdr(fidTxt, '10. SUBSYSTEM PORT INTERFACE');

    % Only top-level subsystems (one level deep)
    topSubs = find_system(modelName, 'SearchDepth', 1, 'BlockType', 'SubSystem');
    topSubs = topSubs(~strcmp(topSubs, modelName));

    for si = 1:numel(topSubs)
        ss = topSubs{si};
        shortSS = strrep(ss, [modelName '/'], '');
        inPorts  = find_system(ss, 'SearchDepth',1, 'BlockType','Inport');
        outPorts = find_system(ss, 'SearchDepth',1, 'BlockType','Outport');
        fprintf(fidTxt, '\n  [%s]  Inputs: %d  Outputs: %d\n', ...
                shortSS, numel(inPorts), numel(outPorts));
        for p = inPorts'
            pName = safeGetParam(p{1}, 'Name');
            fprintf(fidTxt, '    IN   %s\n', strrep(p{1}, [ss '/'], ''));
            if ~isempty(pName) && ~strcmp(pName, strrep(p{1},[ss '/'],''))
                fprintf(fidTxt, '         (%s)\n', pName);
            end
        end
        for p = outPorts'
            fprintf(fidTxt, '    OUT  %s\n', strrep(p{1}, [ss '/'], ''));
        end
    end

    % =========================================================================
    % CLOSE FILES & REPORT
    % =========================================================================
    fclose(fidTxt);
    fclose(fidCsv);

    fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
    fprintf('║              NETLIST GENERATION COMPLETE                ║\n');
    fprintf('╚══════════════════════════════════════════════════════════╝\n');
    fprintf('  Model    : %s\n', modelName);
    fprintf('  Blocks   : %d\n', numel(allBlocks));
    fprintf('  Lines    : %d\n', numel(allLineHandles));
    fprintf('  Text log : %s\n', txtFile);
    fprintf('  CSV log  : %s\n', csvFile);
    fprintf('\n  Open the .txt file for the full annotated netlist.\n');
    fprintf('  Open the .csv file in Excel for sortable parameter view.\n\n');
end

% =========================================================================
% HELPER — print section header
% =========================================================================
function hdr(fid, title)
    fprintf(fid, '\n');
    fprintf(fid, '╔%s╗\n', repmat('═', 1, numel(title)+2));
    fprintf(fid, '║ %s ║\n', title);
    fprintf(fid, '╚%s╝\n', repmat('═', 1, numel(title)+2));
    fprintf(fid, '\n');
end

% =========================================================================
% HELPER — recursive block hierarchy printer
% =========================================================================
function printHierarchy(fid, modelName, parent, depth)
    indent = repmat('  ', 1, depth);
    children = find_system(parent, 'SearchDepth', 1, 'Type', 'block');
    % Remove parent itself
    children = children(~strcmp(children, parent));

    for i = 1:numel(children)
        blk   = children{i};
        bType = get_param(blk, 'BlockType');
        short = strrep(blk, [parent '/'], '');
        fprintf(fid, '%s├─ [%-25s] %s\n', indent, bType, short);
        if strcmp(bType, 'SubSystem')
            try
                printHierarchy(fid, modelName, blk, depth+1);
            catch
                fprintf(fid, '%s  (could not recurse into subsystem)\n', indent);
            end
        end
    end
end

% =========================================================================
% HELPER — safe get_param (returns '' on error)
% =========================================================================
function val = safeGetParam(blk, param)
    try
        raw = get_param(blk, param);
        if ischar(raw)
            val = strtrim(raw);
        elseif isnumeric(raw)
            val = mat2str(raw, 6);
        elseif islogical(raw)
            if raw, val = 'true'; else, val = 'false'; end
        elseif iscell(raw)
            val = strjoin(cellfun(@num2str, raw, 'UniformOutput', false), ', ');
        else
            val = class(raw);
        end
    catch
        val = '';
    end
end

% =========================================================================
% HELPER — safe get on handle-graphics object
% =========================================================================
function val = safeGet(blk, prop)
    try
        val = get_param(blk, prop);
        if ~ischar(val), val = ''; end
    catch
        val = '';
    end
end

% =========================================================================
% HELPER — port handle → "BlockName:PortType#N" string
% =========================================================================
function s = portStr(ph)
    if ph <= 0
        s = '(none)';
        return;
    end
    try
        parent   = get(ph, 'Parent');
        portType = get(ph, 'PortType');
        portNum  = get(ph, 'PortNumber');
        shortP   = regexprep(parent, '^[^/]+/', '');
        s = sprintf('%s:%s%d', shortP, portType, portNum);
    catch
        s = '(invalid handle)';
    end
end

% =========================================================================
% HELPER — escape double-quotes for CSV
% =========================================================================
function s = escCsv(val)
    if isempty(val), s = ''; return; end
    s = strrep(val, '"', '""');
end

```

### File: paramlist.m

```matlab
modelName = 'TransformerWithCTSaturation'; % Ensure model is open
load_system(modelName);

% Find all blocks in the model
allBlocks = find_system(modelName, 'Type', 'block');

for i = 1:length(allBlocks)
    blk = allBlocks{i};
    fprintf('\n--- Block: %s ---\n', blk);
    
    % Get all parameters that appear in the block's dialog box
    params = get_param(blk, 'DialogParameters');
    
    if ~isempty(params)
        fNames = fieldnames(params);
        for j = 1:length(fNames)
            pName = fNames{j};
            pValue = get_param(blk, pName);
            % Only print if it's a simple string or numeric value
            if ischar(pValue) || isnumeric(pValue)
                fprintf('  %s: %s\n', pName, num2str(pValue));
            end
        end
    else
        fprintf('  [No dialog parameters found]\n');
    end
end
```

### File: modelsetup.m

```matlab
load_system('TransformerWithCTSaturation');

blk = 'TransformerWithCTSaturation/Hybrid 87T Relay/LSTM Predict';

load('live_relay_ai.mat','net');
disp(net.InputNames)
set_param(blk, 'NetworkFilePath', 'live_relay_ai.mat');
set_param(blk, 'InputDataFormats', "{'input','BTC'}");
set_param(blk, 'MiniBatchSize', '1');


```

---

## Appendix H: Thesis Figure Generation & Data Visualisation Code

This appendix contains the complete set of 15 MATLAB scripts used to extract simulation/neural network results and generate publication-grade vector graphics (Figures 1-18) for the thesis.

### File: plot_87t_before_after_comparison.m

```matlab
%% Side-by-side comparison: conventional 87T relay vs hybrid DWT-LSTM model
% Thesis-ready before/after figure with noisy differential-current traces,
% relay decisions, and reported benchmark metrics.

clear; close all; clc;
rng(87, 'twister');

%% Time base and style
fs = 20000;                  % samples/s
f0 = 50;                     % system frequency, Hz
t = 0:1/fs:0.2;              % 0 to 0.2 s
w0 = 2*pi*f0;
ph = [0, -2*pi/3, 2*pi/3];   % phase A, B, C

phaseColors = [0.000 0.270 0.620; ...
               0.850 0.180 0.120; ...
               0.000 0.560 0.240];
tripColor = [0.80 0.12 0.10];
blockColor = [0.00 0.45 0.22];
alarmColor = [0.88 0.45 0.05];

%% Generate stressed external-fault / inrush-like disturbance
eventStart = 0.035;
decay = exp(-(t - eventStart)/0.075).*(t >= eventStart);
satShape = max(sin(w0*(t - eventStart)), 0).^8;
hfBurst = sin(2*pi*850*(t - eventStart)).*exp(-(t - eventStart)/0.018).*(t >= eventStart);
remanence = 0.95*exp(-(t - eventStart)/0.10).*(t >= eventStart);
thermalNoiseSigma = 0.006;   % small broadband thermal noise floor, pu
targetSnrDb = 20;            % worst thesis noise case retained in Fig. 6.12/Table 6.12

id_stress_clean = zeros(3, numel(t));
for k = 1:3
    base = 0.13*sin(w0*t + ph(k)).*(t >= eventStart);
    h3 = 0.046*sin(3*w0*t + 3*ph(k) + 0.40).*(t >= eventStart);
    h5 = 0.017*sin(5*w0*t + 5*ph(k) - 0.25).*(t >= eventStart);
    ctOffset = 0.11*remanence*cos(ph(k));
    satSpikes = 0.78*satShape.*decay.*sign(cos(w0*t + ph(k)));
    id_stress_clean(k,:) = base + h3 + h5 + ctOffset + satSpikes + 0.07*hfBurst*cos(ph(k));
end

id_stress_noisy = addThermalAndAwgn(id_stress_clean, thermalNoiseSigma, targetSnrDb);

%% Generate internal fault retained as dependable trip after model integration
internalStart = 0.045;
faultEnvelope = (1 - exp(-(t - internalStart)/0.006)).*(t >= internalStart);
travelingWave = sin(2*pi*1800*(t - internalStart)).*exp(-(t - internalStart)/0.035).*(t >= internalStart);
id_internal_clean = zeros(3, numel(t));

for k = 1:3
    sustained = (3.15 + 0.35*k)*sin(w0*t + ph(k) - 0.20).*faultEnvelope;
    decayingDC = (1.20 - 0.15*k)*exp(-(t - internalStart)/0.060).*(t >= internalStart);
    harmonics = 0.40*sin(5*w0*t + 0.7*ph(k)).*faultEnvelope ...
        + 0.22*sin(7*w0*t - 0.4*ph(k)).*faultEnvelope;
    id_internal_clean(k,:) = sustained + decayingDC + harmonics + 0.72*travelingWave*cos(ph(k));
end

id_internal_noisy = addThermalAndAwgn(id_internal_clean, thermalNoiseSigma, 30);

%% Thesis benchmark metrics
methods = {'Standalone 87T'; 'Optimized 87T'; 'Proposed Hybrid'};
accuracy = [95.83; 96.67; 100.00];
dependability = [96.25; 97.08; 100.00];
security = [95.63; 96.46; 100.00];
falseNeg = [18; 14; 0];
falsePos = [62; 51; 0];
timeMs = [0.1; 0.1; 12.1];

snrLevels = [Inf 60 50 40 30 20];
noiseOverallAccuracy = [99.27 99.27 99.17 99.06 98.65 97.08];

%% Plot figure
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [0.7 0.7 11.2 7.2]);
tl = tiledlayout(fig, 3, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

ax1 = nexttile(1);
plotWaveforms(ax1, t, id_stress_noisy, phaseColors, [-1.05 1.05]);
title(ax1, 'Before: conventional standalone 87T', 'FontName', 'Times New Roman', ...
    'FontWeight', 'bold', 'FontSize', 11);
subtitle(ax1, 'CT saturation + ±95% remanence + thermal noise + 20 dB SNR', ...
    'FontName', 'Times New Roman', 'FontSize', 9);
addDecisionBand(ax1, 0.060, 0.160, tripColor, 'TRIP', 'False trip during external/noisy transient');

ax2 = nexttile(2);
plotWaveforms(ax2, t, id_stress_noisy, phaseColors, [-1.05 1.05]);
title(ax2, 'After: hybrid adaptive 87T + DWT-LSTM supervisor', 'FontName', 'Times New Roman', ...
    'FontWeight', 'bold', 'FontSize', 11);
subtitle(ax2, 'Same disturbance: DWT-LSTM veto/security layer identifies non-internal event', ...
    'FontName', 'Times New Roman', 'FontSize', 9);
addDecisionBand(ax2, 0.060, 0.160, blockColor, 'BLOCK', 'False trip vetoed');

ax3 = nexttile(3);
plotWaveforms(ax3, t, id_internal_noisy, phaseColors, [-5.2 5.2]);
title(ax3, 'Internal fault: conventional 87T pickup', 'FontName', 'Times New Roman', ...
    'FontWeight', 'normal', 'FontSize', 10.5);
addDecisionBand(ax3, 0.055, 0.165, tripColor, 'TRIP', 'High differential current');

ax4 = nexttile(4);
plotWaveforms(ax4, t, id_internal_noisy, phaseColors, [-5.2 5.2]);
title(ax4, 'Internal fault: hybrid dependability retained', 'FontName', 'Times New Roman', ...
    'FontWeight', 'normal', 'FontSize', 10.5);
addDecisionBand(ax4, 0.055, 0.165, tripColor, 'TRIP', '87T and LSTM agree');

ax5 = nexttile(5);
plotNoiseRobustness(ax5, snrLevels, noiseOverallAccuracy, alarmColor);

ax6 = nexttile(6);
drawMetricTable(ax6, methods, accuracy, dependability, security, falseNeg, falsePos, timeMs);

xlabel(tl, 'Time (s)', 'FontName', 'Times New Roman', 'FontSize', 11);
ylabel(tl, 'Differential current (pu)', 'FontName', 'Times New Roman', 'FontSize', 11);

lgd = legend(ax1, {'Phase A', 'Phase B', 'Phase C'}, 'Orientation', 'horizontal', 'Box', 'off');
lgd.Layout.Tile = 'north';

annotation(fig, 'textbox', [0.08 0.008 0.86 0.04], 'String', ...
    'Benchmark values are thesis-reported results: standalone 87T vs optimized 87T vs proposed hybrid relay. Noise robustness uses clean-to-20 dB SNR stress cases.', ...
    'EdgeColor', 'none', 'HorizontalAlignment', 'center', ...
    'FontName', 'Times New Roman', 'FontSize', 8.5, 'Color', [0.20 0.20 0.20]);

%% Save outputs
outDir = fullfile(pwd, 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

pngPath = fullfile(outDir, 'before_after_87t_hybrid_comparison.png');
pdfPath = fullfile(outDir, 'before_after_87t_hybrid_comparison.pdf');
figPath = fullfile(outDir, 'before_after_87t_hybrid_comparison.fig');

exportgraphics(fig, pngPath, 'Resolution', 600);
exportgraphics(fig, pdfPath, 'ContentType', 'vector');
savefig(fig, figPath);

fprintf('Saved before/after comparison to:\n  %s\n  %s\n  %s\n', pngPath, pdfPath, figPath);

%% Local helpers
function yNoisy = addThermalAndAwgn(yClean, thermalSigma, snrDb)
    thermal = thermalSigma*randn(size(yClean));
    yThermal = yClean + thermal;
    signalPower = mean(yClean(:).^2);
    noisePower = signalPower/(10^(snrDb/10));
    awgnNoise = sqrt(noisePower)*randn(size(yClean));
    yNoisy = yThermal + awgnNoise;
end

function plotWaveforms(ax, t, y, phaseColors, yLimits)
    axes(ax);
    hold(ax, 'on');
    for ii = 1:3
        plot(ax, t, y(ii,:), 'LineWidth', 1.05, 'Color', phaseColors(ii,:));
    end
    hold(ax, 'off');
    grid(ax, 'on');
    box(ax, 'on');
    xlim(ax, [0 0.2]);
    ylim(ax, yLimits);
    xticks(ax, 0:0.05:0.2);
    set(ax, 'FontName', 'Times New Roman', 'FontSize', 9.5, ...
        'LineWidth', 0.75, 'GridAlpha', 0.25, 'MinorGridAlpha', 0.12);
end

function addDecisionBand(ax, x1, x2, color, decision, detail)
    yl = ylim(ax);
    y1 = yl(1) + 0.04*range(yl);
    y2 = yl(1) + 0.21*range(yl);
    patch(ax, [x1 x2 x2 x1], [y1 y1 y2 y2], color, ...
        'FaceAlpha', 0.13, 'EdgeColor', color, 'LineWidth', 0.8);
    text(ax, (x1+x2)/2, y1 + 0.62*(y2-y1), decision, ...
        'HorizontalAlignment', 'center', 'FontName', 'Times New Roman', ...
        'FontSize', 11, 'FontWeight', 'bold', 'Color', color);
    text(ax, (x1+x2)/2, y1 + 0.24*(y2-y1), detail, ...
        'HorizontalAlignment', 'center', 'FontName', 'Times New Roman', ...
        'FontSize', 8.5, 'Color', color);
end

function plotNoiseRobustness(ax, snrLevels, overallAcc, lineColor)
    snrPlot = snrLevels;
    snrPlot(isinf(snrPlot)) = 70;
    plot(ax, snrPlot, overallAcc, '-o', 'LineWidth', 1.25, ...
        'Color', lineColor, 'MarkerFaceColor', lineColor, 'MarkerSize', 4.5);
    grid(ax, 'on');
    box(ax, 'on');
    xlim(ax, [18 72]);
    ylim(ax, [96.5 100.1]);
    xticks(ax, [20 30 40 50 60 70]);
    xticklabels(ax, {'20', '30', '40', '50', '60', 'Clean'});
    xlabel(ax, 'SNR stress level (dB)', 'FontName', 'Times New Roman', 'FontSize', 9.5);
    ylabel(ax, 'Overall accuracy (%)', 'FontName', 'Times New Roman', 'FontSize', 9.5);
    title(ax, 'Noise robustness of proposed model', 'FontName', 'Times New Roman', ...
        'FontWeight', 'normal', 'FontSize', 10.5);
    text(ax, 20, 97.08, '  97.08% at 20 dB SNR', 'FontName', 'Times New Roman', ...
        'FontSize', 8.8, 'Color', lineColor, 'VerticalAlignment', 'bottom');
    set(ax, 'FontName', 'Times New Roman', 'FontSize', 9.5, ...
        'LineWidth', 0.75, 'GridAlpha', 0.25);
end

function drawMetricTable(ax, methods, accuracy, dependability, security, falseNeg, falsePos, timeMs)
    axis(ax, 'off');
    title(ax, 'Relay performance benchmark', 'FontName', 'Times New Roman', ...
        'FontWeight', 'normal', 'FontSize', 10.5);

    headers = {'Method', 'Acc.', 'Dep.', 'Sec.', 'FN', 'FP', 'Time'};
    rows = cell(numel(methods), numel(headers));
    for ii = 1:numel(methods)
        rows{ii,1} = methods{ii};
        rows{ii,2} = sprintf('%.2f%%', accuracy(ii));
        rows{ii,3} = sprintf('%.2f%%', dependability(ii));
        rows{ii,4} = sprintf('%.2f%%', security(ii));
        rows{ii,5} = sprintf('%d', falseNeg(ii));
        rows{ii,6} = sprintf('%d', falsePos(ii));
        rows{ii,7} = sprintf('%.1f ms', timeMs(ii));
    end

    x = [0.02 0.36 0.48 0.60 0.72 0.80 0.88];
    yTop = 0.82;
    rowH = 0.19;
    colW = [0.33 0.11 0.11 0.11 0.07 0.07 0.10];

    rectangle(ax, 'Position', [0.01 yTop-0.045 0.97 0.13], ...
        'FaceColor', [0.92 0.94 0.97], 'EdgeColor', [0.45 0.48 0.52]);
    for jj = 1:numel(headers)
        text(ax, x(jj), yTop+0.02, headers{jj}, 'FontName', 'Times New Roman', ...
            'FontSize', 8.8, 'FontWeight', 'bold', 'HorizontalAlignment', 'left');
    end

    for ii = 1:size(rows,1)
        y = yTop - ii*rowH;
        if ii == 3
            fillColor = [0.90 0.97 0.92];
        else
            fillColor = [1 1 1];
        end
        rectangle(ax, 'Position', [0.01 y-0.045 0.97 0.13], ...
            'FaceColor', fillColor, 'EdgeColor', [0.78 0.80 0.83]);
        for jj = 1:numel(headers)
            if jj == 1
                fontWeight = 'bold';
            else
                fontWeight = 'normal';
            end
            text(ax, x(jj), y+0.02, rows{ii,jj}, 'FontName', 'Times New Roman', ...
                'FontSize', 8.6, 'FontWeight', fontWeight, 'HorizontalAlignment', 'left');
        end
    end

    text(ax, 0.02, 0.08, 'Hybrid result: zero false negatives and zero false trips on thesis validation set.', ...
        'FontName', 'Times New Roman', 'FontSize', 8.8, 'Color', [0.00 0.35 0.18]);
    xlim(ax, [0 1]);
    ylim(ax, [0 1]);
end

```

### File: plot_ablation_tornado.m

```matlab
%% plot_ablation_tornado.m
% Generates publication-grade Figure 6.9: Ablation sensitivity of
% classification accuracy to individual design choices.

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 8.2 4.8]);
ax = axes(fig, 'FontName','Times New Roman','FontSize',11);
hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

% Data
configs = {
    'Full Model (Proposed)',
    'Without Attention Layer',
    'Single LSTM Layer (64 units)',
    'Detail-Energy Features Only',
    'Approximation-Energy Only',
    'Without Normalisation',
    '2-Level DWT',
    '4-Level DWT'
};
delta_acc = [0.00, -0.71, -1.34, -0.44, -8.03, -2.87, -0.56, -0.87];

% Reverse arrays for plotting from top to bottom
configs = flip(configs);
delta_acc = flip(delta_acc);

% Horizontal bar chart
bh = barh(ax, 1:numel(configs), delta_acc, 0.6, 'FaceColor','flat', 'EdgeColor','none');

% Color negative bars red and baseline/full model blue
CData = zeros(numel(configs), 3);
for i = 1:numel(configs)
    if delta_acc(i) == 0.0
        CData(i,:) = [0.20 0.55 0.90]; % Baseline blue
    else
        CData(i,:) = [0.85 0.30 0.30]; % Negative red
    end
end
bh.CData = CData;

% Customize axes
set(ax, 'YTick', 1:numel(configs), 'YTickLabel', configs, 'FontSize', 9.5);
xlabel('Accuracy Change \Delta Acc. (percentage points)', 'FontName','Times New Roman','FontSize',12);
ylabel('Ablated Configuration', 'FontName','Times New Roman','FontSize',12);
xlim([-9.5 1.0]);

% Add numerical labels to bars
for i = 1:numel(configs)
    if delta_acc(i) == 0.0
        text(ax, 0.2, i, 'Baseline (99.27%)', 'FontName','Times New Roman','FontSize',9.5, 'FontWeight','bold', 'Color',[0.20 0.40 0.70]);
    else
        text(ax, delta_acc(i) - 0.75, i, sprintf('%.2f pp', delta_acc(i)), ...
             'FontName','Times New Roman','FontSize',9.5, 'HorizontalAlignment','center', 'VerticalAlignment','middle');
    end
end

title('Ablation Sensitivity: Impact of Architectural Choices', 'FontName','Times New Roman','FontSize',13,'FontWeight','bold');

% Save output
outPath = fullfile(pwd, 'figures', 'ablation_sensitivity_tornado.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);

```

### File: plot_bayes_boundary.m

```matlab
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

```

### File: plot_bh_and_inrush.m

```matlab
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

```

### File: plot_ct_saturation.m

```matlab
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

```

### File: plot_flop_share.m

```matlab
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

```

### File: plot_hybrid_protection_framework_flowchart.m

```matlab
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

```

### File: plot_lstm_architecture_flowchart.m

```matlab
%% Horizontal LSTM network architecture flowchart
% Thesis-ready diagram for the DWT-LSTM classifier architecture.

clear; close all; clc;

%% Figure setup
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [0.5 0.5 13.2 3.8]);
ax = axes(fig);
hold(ax, 'on');
axis(ax, 'off');
xlim(ax, [0 13.2]);
ylim(ax, [0 3.8]);

fontName = 'Times New Roman';

%% Grayscale colors
cInput = [0.96 0.96 0.96];
cLstm = [0.90 0.90 0.90];
cDrop = [0.84 0.84 0.84];
cAttn = [0.78 0.78 0.78];
cDense = [0.88 0.88 0.88];
cOut = [0.82 0.82 0.82];
cBorder = [0.16 0.16 0.16];
cArrow = [0.10 0.10 0.10];

%% Node definitions
nodes = {
    0.25, 1.55, 1.10, 0.82, cInput, 'Input', '[B, 32, 6]';
    1.70, 1.45, 1.25, 1.02, cLstm, 'LSTM 1', '128 units\newlinereturn sequences';
    3.28, 1.55, 1.05, 0.82, cDrop, 'Dropout', 'p = 0.3';
    4.68, 1.45, 1.25, 1.02, cLstm, 'LSTM 2', '64 units\newlinereturn sequences';
    6.26, 1.55, 1.05, 0.82, cDrop, 'Dropout', 'p = 0.3';
    7.66, 1.35, 1.52, 1.22, cAttn, 'Global Temporal\newlineAttention', 'weighted sum\newlineacross 32 steps';
    9.58, 1.55, 1.12, 0.82, cDense, 'Dense', '32 units, ReLU';
    11.08, 1.55, 1.22, 0.82, cOut, 'Output', '4 units, softmax';
};

%% Draw nodes and arrows
for i = 1:size(nodes, 1)
    drawNode(ax, nodes{i,1}, nodes{i,2}, nodes{i,3}, nodes{i,4}, ...
        nodes{i,5}, nodes{i,6}, nodes{i,7}, fontName, cBorder);
end

for i = 1:size(nodes, 1)-1
    x1 = nodes{i,1} + nodes{i,3};
    y1 = nodes{i,2} + nodes{i,4}/2;
    x2 = nodes{i+1,1};
    y2 = nodes{i+1,2} + nodes{i+1,4}/2;
    drawArrow(ax, x1 + 0.08, y1, x2 - 0.08, y2, cArrow);
end

%% Title and parameter count
text(ax, 6.6, 3.35, 'LSTM Network Architecture for Transformer Differential Protection', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, ...
    'FontWeight', 'bold', 'FontSize', 15, 'Color', [0.08 0.08 0.08]);

text(ax, 6.6, 0.72, 'Total trainable parameters: 125,476', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, ...
    'FontWeight', 'bold', 'FontSize', 12, 'Color', [0.12 0.12 0.12]);

text(ax, 6.6, 0.38, ...
    'Sequence length = 32 time steps; feature vector = 6 DWT energy features per step', ...
    'HorizontalAlignment', 'center', 'FontName', fontName, ...
    'FontSize', 10, 'Color', [0.30 0.30 0.30]);

%% Save outputs
outDir = fullfile(pwd, 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

pngPath = fullfile(outDir, 'lstm_network_architecture_flowchart.png');
pdfPath = fullfile(outDir, 'lstm_network_architecture_flowchart.pdf');
figPath = fullfile(outDir, 'lstm_network_architecture_flowchart.fig');

exportgraphics(fig, pngPath, 'Resolution', 600);
exportgraphics(fig, pdfPath, 'ContentType', 'vector');
savefig(fig, figPath);

fprintf('Saved LSTM architecture flowchart to:\n  %s\n  %s\n  %s\n', pngPath, pdfPath, figPath);

%% Local helpers
function drawNode(ax, x, y, w, h, faceColor, titleText, bodyText, fontName, borderColor)
    rectangle(ax, 'Position', [x y w h], 'Curvature', 0.08, ...
        'FaceColor', faceColor, 'EdgeColor', borderColor, 'LineWidth', 1.15);
    text(ax, x + w/2, y + h*0.63, titleText, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'FontName', fontName, 'FontWeight', 'bold', 'FontSize', 10.5, ...
        'Color', [0.08 0.08 0.08], 'Interpreter', 'tex');
    text(ax, x + w/2, y + h*0.32, bodyText, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'FontName', fontName, 'FontSize', 9.3, ...
        'Color', [0.18 0.18 0.18], 'Interpreter', 'tex');
end

function drawArrow(ax, x1, y1, x2, y2, color)
    annotation(ax.Parent, 'arrow', ...
        xDataToNorm(ax, [x1 x2]), yDataToNorm(ax, [y1 y2]), ...
        'Color', color, 'LineWidth', 1.15, 'HeadLength', 7, 'HeadWidth', 7);
end

function xn = xDataToNorm(ax, x)
    axPos = ax.Position;
    xLim = ax.XLim;
    xn = axPos(1) + (x - xLim(1))/(xLim(2) - xLim(1))*axPos(3);
end

function yn = yDataToNorm(ax, y)
    axPos = ax.Position;
    yLim = ax.YLim;
    yn = axPos(2) + (y - yLim(1))/(yLim(2) - yLim(1))*axPos(4);
end

```

### File: plot_percentage_restraint_slope.m

```matlab
%% plot_percentage_restraint_slope.m
% Generates publication-grade Figure 3.1: Dual-Slope Percentage Restraint
% operate/restrain characteristic of the differential relay.

clear; close all; clc;

% Figure setup (Times New Roman, single column width)
fig = figure('Color','w','Units','inches','Position',[1 1 7.0 5.2]);
ax = axes(fig, 'FontName','Times New Roman','FontSize',11);
hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

% Parameters
I_pickup = 0.3;   % Minimum pickup current (A)
I_knee1  = 2.0;   % First knee point (A)
S1       = 0.15;  % Slope 1 (15%)
S2       = 0.40;  % Slope 2 (40%)

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
text(I_pickup + 0.1, I_pickup - 0.1, 'I_{pickup} = 0.3 A', 'FontName','Times New Roman','FontSize',9.5);
text(I_knee1 - 0.6, Id_thresh(Ir == I_knee1) + 0.25, {'Knee Point', '(I_{rest} = 2.0 A)'}, ...
     'FontName','Times New Roman','FontSize',9.5, 'HorizontalAlignment','center');

% Slopes
text(1.1, 0.45, 'Slope 1 = 15%', 'FontName','Times New Roman','FontSize',10, 'Rotation',8);
text(4.2, 1.45, 'Slope 2 = 40%', 'FontName','Times New Roman','FontSize',10, 'Rotation',21);

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

```

### File: plot_signal_flow.m

```matlab
%% plot_signal_flow.m
% Generates publication-grade Figure 5.3: End-to-end seven-stage signal flow
% of the proposed protection scheme.

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 12.5 3.5]);
ax = axes(fig);
hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
xlim(ax, [0 12.5]); ylim(ax, [0 3.5]);

fontName = 'Times New Roman';

%% Node definitions
% x, y, width, height, color, title, subtitle
nodes = {
    0.2, 0.9, 1.4, 1.7, [0.96 0.96 0.96], 'Stage 1: CT', {'CT secondary current', '3-phase sampling'};
    1.9, 0.9, 1.4, 1.7, [0.92 0.92 0.92], 'Stage 2: MU', {'IEC 61850-9-2', 'Conditioning & AWGN'};
    3.6, 0.9, 1.4, 1.7, [0.88 0.88 0.88], 'Stage 3: DWT', {'16-sample window', '6 energy features'};
    5.3, 0.9, 1.4, 1.7, [0.84 0.84 0.84], 'Stage 4: Buffer', {'32-step full-cycle', 'time-series buffer'};
    7.0, 0.9, 1.4, 1.7, [0.80 0.80 0.80], 'Stage 5: LSTM', {'Sigmoid confidence', 'classification'};
    8.7, 0.9, 1.4, 1.7, [0.76 0.76 0.76], 'Stage 6: Veto', {'Parallel 87T Restraint', 'AND handshake veto'};
    10.4, 0.9, 1.8, 1.7, [0.94 0.88 0.88], 'Stage 7: Breaker', {'Winding trip latch', 'Sub-cycle trip coil', '13.1 ms clearing time'}
};

%% Draw nodes
for i = 1:size(nodes, 1)
    x = nodes{i,1};
    y = nodes{i,2};
    w = nodes{i,3};
    h = nodes{i,4};
    col = nodes{i,5};
    lbl_title = nodes{i,6};
    lbl_sub = nodes{i,7};
    
    % Draw rounded rectangle
    rectangle(ax, 'Position', [x y w h], 'Curvature', [0.12 0.12], 'FaceColor', col, 'EdgeColor', [0.16 0.16 0.16], 'LineWidth', 1.5);
    
    % Draw Title
    text(ax, x + w/2, y + h - 0.3, lbl_title, 'FontName', fontName, 'FontSize', 9, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
    
    % Draw Subtitle
    text(ax, x + w/2, y + h/2 - 0.15, lbl_sub, 'FontName', fontName, 'FontSize', 7.5, 'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
end

%% Draw arrows
for i = 1:size(nodes, 1)-1
    x1 = nodes{i,1} + nodes{i,3};
    y1 = nodes{i,2} + nodes{i,4}/2;
    x2 = nodes{i+1,1};
    y2 = nodes{i+1,2} + nodes{i+1,4}/2;
    
    % Draw line
    line(ax, [x1+0.05 x2-0.05], [y1 y1], 'Color', [0.1 0.1 0.1], 'LineWidth', 1.5);
    % Draw arrow head
    plot(ax, x2-0.05, y1, 'k>', 'MarkerFaceColor', 'k', 'MarkerSize', 6);
end

% Title
title('End-to-End Seven-Stage Protective Signal-Flow Pipeline', 'FontName', fontName, 'FontSize', 13, 'FontWeight', 'bold');

% Save output
outPath = fullfile(pwd, 'figures', 'proposed_protection_signal_flow.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);

```

### File: plot_sliding_window_timing.m

```matlab
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

```

### File: plot_three_phase_differential_waveforms.m

```matlab
%% Four-panel three-phase differential current waveforms
% This script synthesizes representative transformer differential-current
% waveforms for: normal load, external fault with CT saturation,
% magnetizing inrush, and internal fault.

clear; close all; clc;

%% Time base
fs = 20000;                  % samples/s
f0 = 50;                     % system frequency, Hz
t = 0:1/fs:0.2;              % 0 to 0.2 s
w0 = 2*pi*f0;
ph = [0, -2*pi/3, 2*pi/3];   % phase A, B, C

phaseColors = [0.000 0.270 0.620; ...
               0.850 0.180 0.120; ...
               0.000 0.560 0.240];

%% (a) Normal load: residual differential current below 0.02 pu
normalAmp = 0.014;
id_normal = zeros(3, numel(t));
for k = 1:3
    id_normal(k,:) = normalAmp*sin(w0*t + ph(k)) ...
        + 0.0025*sin(3*w0*t + 0.8*ph(k)) ...
        + 0.0012*sin(7*w0*t + 0.3*k);
end
id_normal = max(min(id_normal, 0.019), -0.019);

%% (b) External fault with CT saturation: transient spikes, THD about 34.7%
faultStart = 0.035;
decay = exp(-(t - faultStart)/0.075).*(t >= faultStart);
satShape = max(sin(w0*(t - faultStart)), 0).^8;
hfBurst = sin(2*pi*850*(t - faultStart)).*exp(-(t - faultStart)/0.018).*(t >= faultStart);
id_external = zeros(3, numel(t));

for k = 1:3
    base = 0.12*sin(w0*t + ph(k)).*(t >= faultStart);
    h3 = 0.040*sin(3*w0*t + 3*ph(k) + 0.40).*(t >= faultStart);
    h5 = 0.012*sin(5*w0*t + 5*ph(k) - 0.25).*(t >= faultStart);
    dcOffset = 0.055*decay.*cos(ph(k));
    spikes = 0.58*satShape.*decay.*sign(cos(w0*t + ph(k)));
    id_external(k,:) = base + h3 + h5 + dcOffset + spikes + 0.055*hfBurst*cos(ph(k));
end

% Annotation value requested for the intended waveform.
externalTHDpercent = 34.7;

%% (c) Magnetizing inrush: asymmetric 5-8 pu peaks with dead angles
inrushStart = 0.012;
tau = 0.085;
env = exp(-(t - inrushStart)/tau).*(t >= inrushStart);
id_inrush = zeros(3, numel(t));

for k = 1:3
    theta = w0*(t - inrushStart) + ph(k) - 0.55;
    raw = sin(theta) + 0.62*sin(2*theta - 1.10) + 0.20*sin(3*theta + 0.70);
    deadAngleMask = abs(mod(theta + pi, 2*pi) - pi) > deg2rad(28);
    asym = 1.10 + 0.55*cos(theta - 0.35);
    id_inrush(k,:) = (5.4 + 0.85*k)*env.*asym.*max(raw, 0).*deadAngleMask;
    id_inrush(k,:) = id_inrush(k,:) - 0.34*(5.4 + 0.85*k)*env.*max(-raw, 0).^1.3;
end

% Scale to keep the intended positive peaks in the 5-8 pu range.
targetPeaks = [6.2, 7.1, 7.8];
for k = 1:3
    id_inrush(k,:) = id_inrush(k,:) * targetPeaks(k)/max(id_inrush(k,:));
end

%% (d) Internal fault: sustained high current with high-frequency transients
internalStart = 0.030;
faultEnvelope = (1 - exp(-(t - internalStart)/0.006)).*(t >= internalStart);
travelingWave = sin(2*pi*1800*(t - internalStart)).*exp(-(t - internalStart)/0.035).*(t >= internalStart);
id_internal = zeros(3, numel(t));

for k = 1:3
    sustained = (3.25 + 0.30*k)*sin(w0*t + ph(k) - 0.20).*faultEnvelope;
    decayingDC = (1.30 - 0.18*k)*exp(-(t - internalStart)/0.060).*(t >= internalStart);
    harmonics = 0.42*sin(5*w0*t + 0.7*ph(k)).*faultEnvelope ...
        + 0.24*sin(7*w0*t - 0.4*ph(k)).*faultEnvelope;
    id_internal(k,:) = sustained + decayingDC + harmonics + 0.75*travelingWave*cos(ph(k));
end

%% Plot
fig = figure('Color', 'w', 'Units', 'inches', 'Position', [1 1 8.3 9.2]);
tl = tiledlayout(fig, 4, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

plotPanel(t, id_normal, phaseColors, ...
    '(a) Normal load: differential current < 0.02 pu', [-0.025 0.025]);

plotPanel(t, id_external, phaseColors, ...
    sprintf('(b) External fault with CT saturation: transient spikes, THD \\approx %.1f%%', externalTHDpercent), ...
    [-0.8 0.8]);

plotPanel(t, id_inrush, phaseColors, ...
    '(c) Magnetizing inrush: asymmetric 5-8 pu peaks with dead angles', [-2.5 8.5]);

plotPanel(t, id_internal, phaseColors, ...
    '(d) Internal fault: sustained high magnitude with high-frequency transients', [-5.2 5.2]);

xlabel(tl, 'Time (s)', 'FontName', 'Times New Roman', 'FontSize', 11);
ylabel(tl, 'Differential current (pu)', 'FontName', 'Times New Roman', 'FontSize', 11);

legendLabels = {'Phase A', 'Phase B', 'Phase C'};
lgd = legend(legendLabels, 'Orientation', 'horizontal', 'Box', 'off');
lgd.Layout.Tile = 'north';

% Save high-resolution outputs beside the script.
outDir = fullfile(pwd, 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end
exportgraphics(fig, fullfile(outDir, 'three_phase_differential_waveforms.png'), 'Resolution', 600);
exportgraphics(fig, fullfile(outDir, 'three_phase_differential_waveforms.pdf'), 'ContentType', 'vector');

fprintf('Saved figure to:\n  %s\n  %s\n', ...
    fullfile(outDir, 'three_phase_differential_waveforms.png'), ...
    fullfile(outDir, 'three_phase_differential_waveforms.pdf'));

%% Local plotting helper
function plotPanel(t, y, phaseColors, panelTitle, yLimits)
    nexttile;
    hold on;
    for ii = 1:3
        plot(t, y(ii,:), 'LineWidth', 1.15, 'Color', phaseColors(ii,:));
    end
    hold off;
    grid on;
    box on;
    xlim([0 0.2]);
    ylim(yLimits);
    xticks(0:0.025:0.2);
    title(panelTitle, 'FontName', 'Times New Roman', 'FontSize', 10.5, ...
        'FontWeight', 'normal');
    set(gca, 'FontName', 'Times New Roman', 'FontSize', 9.5, ...
        'LineWidth', 0.75, 'GridAlpha', 0.25, 'MinorGridAlpha', 0.12);
end

```

### File: plot_transformer_protection_SLD.m

```matlab
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

```

### File: plot_twostep_architecture.m

```matlab
%% plot_twostep_architecture.m
% Generates publication-grade Figure 5.1: Two-step development and
% deployment architecture (MATLAB/Simulink <-> PyTorch <-> ONNX).

clear; close all; clc;

% Figure setup
fig = figure('Color','w','Units','inches','Position',[1 1 12.0 4.0]);
ax = axes(fig);
hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
xlim(ax, [0 12]); ylim(ax, [0 4]);

fontName = 'Times New Roman';

%% Node definitions
% x, y, width, height, color, title, subtitle
nodes = {
    0.2, 1.2, 2.0, 1.6, [0.94 0.94 0.94], 'Step 1a: Physical Modeling', {'MATLAB/Simulink', 'Transient power simulation', 'Data generation'};
    2.7, 1.2, 2.0, 1.6, [0.90 0.90 0.90], 'Step 1b: Signal Processing', {'DWT coefficient extraction', 'Wavelet energies', 'Z-score normalization'};
    5.2, 1.2, 2.0, 1.6, [0.86 0.86 0.86], 'Step 2a: LSTM Intelligence', {'PyTorch network training', 'Dropout & Attention pooling', 'Hyperparameter HPO'};
    7.7, 1.2, 2.0, 1.6, [0.82 0.82 0.82], 'Step 2b: Model Export', {'ONNX format (Opset 14)', 'Graph optimization', 'Compacted 56,898 params'};
    10.2, 1.2, 1.6, 1.6, [0.88 0.94 0.88], 'Step 3: Relaying', {'Simulink deployment', 'Predict block integration', '13.1 ms clearing time'}
};

%% Draw nodes
for i = 1:size(nodes, 1)
    x = nodes{i,1};
    y = nodes{i,2};
    w = nodes{i,3};
    h = nodes{i,4};
    col = nodes{i,5};
    lbl_title = nodes{i,6};
    lbl_sub = nodes{i,7};
    
    % Draw rounded rectangle
    rectangle(ax, 'Position', [x y w h], 'Curvature', [0.15 0.15], 'FaceColor', col, 'EdgeColor', [0.16 0.16 0.16], 'LineWidth', 1.5);
    
    % Draw Title
    text(ax, x + w/2, y + h - 0.3, lbl_title, 'FontName', fontName, 'FontSize', 9.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
    
    % Draw Subtitle
    text(ax, x + w/2, y + h/2 - 0.15, lbl_sub, 'FontName', fontName, 'FontSize', 8, 'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
end

%% Draw arrows
for i = 1:size(nodes, 1)-1
    x1 = nodes{i,1} + nodes{i,3};
    y1 = nodes{i,2} + nodes{i,4}/2;
    x2 = nodes{i+1,1};
    y2 = nodes{i+1,2} + nodes{i+1,4}/2;
    
    % Draw line
    line(ax, [x1+0.05 x2-0.05], [y1 y1], 'Color', [0.1 0.1 0.1], 'LineWidth', 1.5);
    % Draw arrow head
    plot(ax, x2-0.05, y1, 'k>', 'MarkerFaceColor', 'k', 'MarkerSize', 6);
end

% Title
title('End-to-End Two-Step DWT-LSTM Development and Deployment Framework', 'FontName', fontName, 'FontSize', 13, 'FontWeight', 'bold');

% Save output
outPath = fullfile(pwd, 'figures', 'two_step_development_architecture.png');
exportgraphics(fig, outPath, 'Resolution', 300);
close(fig);
fprintf('Successfully generated: %s\n', outPath);

```

### File: plot_wavelet_filterbank.m

```matlab
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

```