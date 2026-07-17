# Explanation of Figures in Hybrid Adaptive Transformer Differential Protection Thesis

This document provides a detailed breakdown of all the figures used in the thesis **"Hybrid Adaptive Transformer Differential Protection: An Intelligent DWT–LSTM Framework"**. Each entry details the file path, the figure caption, its context in the text, and a comprehensive explanation of what the figure represents.

---

## Chapter 1: Introduction

### 1. Figure 1.1: Single-Line Diagram of the Protection Scheme
* **File Name:** `sld.png`
* **LaTeX Label:** `fig:1.1`
* **Caption:** *Single-line diagram of the 300 MVA, 230/11 kV Yd1 power transformer and its differential (87T) protection scheme.*
* **What it Represents:** 
  This figure illustrates the physical electrical connection and protection boundary of the system under study. It shows:
  * A two-winding three-phase power transformer rated at **300 MVA, 230/11 kV** with a **Yd1** (Wye-Grounded / Delta-1, $-30^\circ$ phase shift) connection.
  * Current Transformers (CTs) installed on both the High Voltage (HV) and Low Voltage (LV) sides of the transformer.
  * The differential zone (87T protection zone) bounded by these CTs.
  * The measurement signal lines routing current signals to the differential relay logic, illustrating how the primary and secondary currents are compared to check for internal faults.

---

## Chapter 3: Mathematical Modeling and Theoretical Framework

### 2. Figure 3.1: Dual-Slope Restraint Characteristic
* **File Name:** `fig_3_1.png`
* **LaTeX Label:** `fig:3.1`
* **Caption:** *Dual-slope percentage restraint characteristic of the differential relay.*
* **What it Represents:** 
  This graph represents the operating limits of a conventional percentage differential relay. It plots the **differential current ($I_d$)** on the y-axis against the **restraint (bias) current ($I_r$)** on the x-axis:
  * **$I_{pickup}$:** The minimum differential current required to trip under low-current conditions (typically 0.2–0.5 pu).
  * **Slope 1 ($S_1$, typically 25–40%):** Handles small measurement errors, steady-state mismatches, and tap-changer deviations under normal operating conditions.
  * **Slope 2 ($S_2$, typically 50–80%):** Provides a higher restraint threshold at high currents to prevent maloperation during through-faults accompanied by current transformer (CT) saturation.
  * It splits the operational space into two distinct regions: **Trip (operate)** above the curve, and **Restraint (block)** below the curve.

### 3. Figure 3.2: Core B-H Saturation Curve and Inrush Waveform
* **File Name:** `fig_3_2.png`
* **LaTeX Label:** `fig:3.2`
* **Caption:** *Core $B$–$H$ saturation curve and the resulting magnetizing inrush waveform.*
* **What it Represents:** 
  This figure visualizes the physical mechanism of magnetizing inrush current during transformer energization:
  * On the left, it shows the nonlinear **$B$–$H$ curve** of the core material.
  * On the right, it shows how switching on the transformer at a voltage zero-crossing (worst-case angle $\alpha=0$) or with high residual flux ($\Phi_r$) drives the magnetic flux $\Phi$ deep into the core's saturation region.
  * Because the core saturates, the magnetizing impedance drops drastically, resulting in a highly distorted, asymmetric, and peaked current waveform (the **magnetizing inrush current**). This inrush waveform is rich in harmonics (especially the 2nd harmonic), which conventional schemes use for blocking.

### 4. Figure 3.3: Current Transformer Equivalent Circuit and Saturation
* **File Name:** `fig_3_3.png`
* **LaTeX Label:** `fig:3.3`
* **Caption:** *Current transformer equivalent circuit and saturation-induced secondary distortion.*
* **What it Represents:** 
  This diagram models why and how current transformers saturate during heavy external faults:
  * It shows the standard **CT equivalent circuit** consisting of primary referred current, secondary winding resistance ($R_s$), leakage inductance ($X_s$), the nonlinear magnetizing branch representing core excitation, and the connected burden ($Z_b$).
  * It details the waveform distortion: when primary current contains a large DC offset, the magnetic flux in the CT core builds up and exceeds the saturation limit. When this happens, the magnetizing current ($I_e$) shoots up, causing the secondary current ($I_s$) to collapse near the peaks. This distortion creates a false differential current ($I_d = |I_{s1} - I_{s2}|$) that can cause standard relays to maloperate.

### 5. Figure 3.4: Conceptual Feature-Space Separation
* **File Name:** `fig_3_4.png`
* **LaTeX Label:** `fig:3.4`
* **Caption:** *Conceptual feature-space separation of the event classes with cost-asymmetric decision boundaries.*
* **What it Represents:** 
  This conceptual scatter plot demonstrates:
  * How the four system states (Normal Operation, External Fault, Magnetizing Inrush, and Internal Fault) cluster in a multi-dimensional feature space.
  * The **decision boundary** that separates the "Trip" state (Internal Fault) from the "No-Trip" states (Normal, External, Inrush).
  * The cost-asymmetric nature of protection engineering: a missed internal fault (False Negative) has a catastrophically high cost compared to a false trip (False Positive). The boundary is therefore mathematically biased to ensure high dependability, which is physically anchored in this thesis by the hybrid 87T logic.

---

## Chapter 4: Power System Simulation Model Using MATLAB/Simulink

### 6. Figure 4.1: Simulink Main Panel Overview
* **File Name:** `fig_4_1.png`
* **LaTeX Label:** `fig:4.1`
* **Caption:** *Overview of the MATLAB/Simulink power-system simulation model (Simulink main panel).*
* **What it Represents:** 
  This screenshot shows the top-level block diagram of the electromagnetic-transient (EMT) model built in MATLAB/Simulink using Simscape Electrical. It shows the three-phase sources representing the HV and LV power grids, the breaker blocks, the 300 MVA transformer model, the loads, and the signal-routing buses.

### 7. Figure 4.1b: Primary-Side CT Subsystem
* **File Name:** `ct_primary.png`
* **LaTeX Label (referred in line 460):** *None (referenced inline)*
* **Caption:** *Current-transformer primary (HV-side) subsystem implementing core saturation and remanence.*
* **What it Represents:** 
  This block diagram shows the internal structure of the primary (HV) side CT simulation block. It includes the mathematical logic to compute core excitation, nonlinear saturation characteristics, and the injection of remanent flux ($\Phi_{rem}$) to test the relay under realistic magnetic stress.

### 8. Figure 4.1c: Secondary-Side CT Subsystem
* **File Name:** `ct_secondary.png`
* **LaTeX Label (referred in line 462):** *None (referenced inline)*
* **Caption:** *Current-transformer secondary subsystem implementing core saturation and remanence.*
* **What it Represents:** 
  This shows the internal modeling of the secondary-side CT block. It captures secondary winding impedance, the burden connection, and measurement decimation blocks that downsample the high-fidelity 10 $\mu$s solver signals to the 1.6 kHz relay sampling rate.

### 9. Figure 4.2: Merging-Unit Signal-Conditioning Pipeline
* **File Name:** `fig_4_2.png`
* **LaTeX Label:** `fig:4.2`
* **Caption:** *Merging-unit signal-conditioning and noise-injection pipeline.*
* **What it Represents:** 
  This block diagram details the preprocessing pipeline that emulates an IEC 61850-9-2 Merging Unit:
  1. **Anti-Aliasing Filter:** A 4th-order Butterworth low-pass filter with an 800 Hz cutoff.
  2. **Quantization:** 16-bit analog-to-digital conversion.
  3. **Noise Injection:** Additive White Gaussian Noise (AWGN) to simulate instrument transformer and line noise (at 20, 30, and 40 dB SNR).
  4. **Decimation:** Resampling to a 1.6 kHz rate (32 samples per 50 Hz cycle) to yield the digital current signals used by the protection algorithm.

### 10. Figure 4.3: Dataset Composition and Splitting
* **File Name:** `fig_4_3.png`
* **LaTeX Label:** `fig:4.3`
* **Caption:** *Composition of the 2,500-case dataset across event categories and train/validation/test subsets.*
* **What it Represents:** 
  A bar chart or pie chart representing the composition of the 2,500-case database:
  * **Internal Faults:** 1,035 cases (41.4%) $\to$ Trip
  * **External Faults:** 578 cases (23.1%) $\to$ No-Trip
  * **Magnetizing Inrush:** 500 cases (20.0%) $\to$ No-Trip
  * **Normal Operation:** 387 cases (15.5%) $\to$ No-Trip
  * It also displays the stratified split: **70% Training**, **15% Validation**, and **15% Test** (leaving 1,800 cases for the held-out validation and testing).

---

## Chapter 5: Proposed DWT–LSTM Methodology

### 11. Figure 5.1: Two-Step Development and Deployment Workflow
* **File Name:** `fig_5_1.png`
* **LaTeX Label:** `fig:5.1`
* **Caption:** *Two-step development and deployment architecture (MATLAB/Simulink $\leftrightarrow$ PyTorch $\leftrightarrow$ ONNX).*
* **What it Represents:** 
  This flow diagram outlines the hybrid development lifecycle:
  * **Step 1 (Offline Training):** Simulated current waveforms are generated in Simulink, features are extracted via DWT in MATLAB, and the LSTM neural network is trained in PyTorch (Python). The trained model is then exported as an `.onnx` file.
  * **Step 2 (Online Deployment):** The ONNX model is loaded directly back into the Simulink model using the Deep Learning Toolbox's "Predict" block. This allows the neural network to execute in real-time in closed-loop co-simulation with the simulated power grid.

### 12. Figure 5.2: Hybrid Veto/AND-Gate Decision Logic
* **File Name:** `fig_5_2.png`
* **LaTeX Label:** `fig:5.2`
* **Caption:** *Hybrid veto/AND-gate decision logic combining the adaptive 87T element and the LSTM classifier.*
* **What it Represents:** 
  This logic diagram explains the core architectural contribution of the thesis:
  * The classical **Adaptive 87T relay element** and the **DWT-LSTM neural network classifier** run in parallel.
  * The final **TRIP** signal is a logical **AND** of:
    1. The 87T relay operating.
    2. The LSTM classifier predicting an "Internal Fault".
    3. The LSTM confidence score being above a threshold ($\theta_{conf} \ge 0.85$).
  * This structure keeps the safety-certified 87T element as the primary driver (dependability floor) while using the LSTM as a supervisory "veto" to block false trips during inrush or saturation (enhancing security).

### 13. Figure 5.3: End-to-End Seven-Stage Signal Flow
* **File Name:** `fig_5_3.png`
* **LaTeX Label:** `fig:5.3`
* **Caption:** *End-to-end seven-stage signal flow of the proposed protection scheme.*
* **What it Represents:** 
  This block diagram tracks a measurement from physical current to breaker trip through 7 stages:
  1. Secondary CT current measurements & phase compensation (Yd1).
  2. Sliding 16-sample (10 ms) windowing.
  3. 3-level db4 Discrete Wavelet Transform (DWT).
  4. Calculation of Phase $a_3$ and $d_{1\text{--}3}$ energy to construct the 6D feature vector.
  5. 32-sample sliding buffer to construct a $[1, 32, 6]$ input tensor.
  6. ONNX LSTM classifier execution.
  7. Hybrid decision handshake and breaker trip command.

### 14. Figure 5.4: Dual Sliding-Window Timing Diagram
* **File Name:** `fig_5_4.png`
* **LaTeX Label:** `fig:5.4`
* **Caption:** *Dual sliding-window timing: half-cycle DWT window and full-cycle LSTM buffer.*
* **What it Represents:** 
  This timing diagram visualizes the two windows used in the scheme:
  * **DWT Feature Window (10 ms):** A half-cycle sliding window of 16 samples. At each step, DWT is computed on these 16 samples to extract the approximation and detail energy features.
  * **LSTM Context Buffer (20 ms):** A full-cycle buffer that stores 32 successive 6D feature vectors. The LSTM processes this sequence of 32 steps to capture the temporal evolution of the currents.

### 15. Figure 5.5: db4 Wavelet and 3-Level Dyadic Filter Bank
* **File Name:** `fig_5_5.png`
* **LaTeX Label:** `fig:5.5`
* **Caption:** *db4 mother wavelet and the three-level dyadic filter-bank decomposition tree.*
* **What it Represents:** 
  * On the left, it shows the wave shape of the **Daubechies-4 (db4)** mother wavelet, highlighting its asymmetric, compact, and fast-decaying nature which makes it ideal for capturing sharp transients (fault inception).
  * On the right, it shows the **filter-bank tree**: the input signal $x[n]$ is passed through low-pass ($h$) and high-pass ($g$) filters, followed by downsampling by 2 ($\downarrow 2$). This dyadic splitting is repeated to level 3, decomposing the 1.6 kHz signal into approximation band $a_3$ (0–100 Hz) and detail bands $d_3$ (100–200 Hz), $d_2$ (200–400 Hz), and $d_1$ (400–800 Hz).

### 16. Figure 5.6: DWT-LSTM Classifier Architecture
* **File Name:** `fig_5_6.png`
* **LaTeX Label:** `fig:5.6`
* **Caption:** *DWT–LSTM classifier architecture with global temporal attention.*
* **What it Represents:** 
  A schematic of the neural network architecture:
  * **Input Layer:** Receives the shape $[B, 32, 6]$.
  * **LSTM Layer 1:** 128 hidden units, outputting a sequence of hidden states.
  * **LSTM Layer 2:** 64 hidden units, outputting a sequence of hidden states.
  * **Attention Layer:** Applies a softmax function across the 32 time steps to dynamically weight the most important steps, outputting a 64-dimensional context vector.
  * **Dense & Softmax Layers:** Compresses the context vector to output probabilities for the 4 classes (Normal, External, Inrush, Internal).

### 17. Figure 5.7: Per-Inference Computational Cost Distribution
* **File Name:** `fig_5_7.png`
* **LaTeX Label:** `fig:5.7`
* **Caption:** *Per-inference computational cost distribution across pipeline stages.*
* **What it Represents:** 
  A pie chart illustrating the computational load of each stage of the protection pipeline:
  * **DWT Feature Extraction:** 0.2% of the FLOPs.
  * **LSTM Layer 1:** 42.0% of the FLOPs.
  * **LSTM Layer 2:** 52.7% of the FLOPs.
  * **Attention & Softmax Layers:** 5.1% of the FLOPs.
  * This shows that the sequential deep learning layers dominate the computational budget, but the overall cost (1.31 MFLOPs/step) is well within the capabilities of modern microprocessors.

### 18. Figure 5.hyb: Simulink Implementation of the Hybrid Relay
* **File Name:** `hybrid87t_impl.png`
* **LaTeX Label (referred in line 588):** *None (referenced inline)*
* **Caption:** *Simulink implementation of the hybrid 87T relay: DWT–LSTM classifier, adaptive 87T element, and AND/veto decision gate.*
* **What it Represents:** 
  This is a block diagram showing the actual wiring and logic blocks implemented in the Simulink environment. It connects the current measurements to:
  * The DWT feature calculation block.
  * The ONNX model predictor block.
  * The traditional adaptive 87T relay block.
  * The decision logic gate that issues the breaker trip signal, verifying that the entire system can run in closed loop.

---

## Chapter 6: Results, Analysis and Discussion

### 19. Figure 6.1: Three-Phase Current Waveforms for the 4 Classes
* **File Name:** `fig_6_1.png`
* **LaTeX Label:** `fig:6.1`
* **Caption:** *Three-phase differential current waveforms for the four operating conditions.*
* **What it Represents:** 
  This figure plots actual simulated three-phase differential current waveforms under the four main operating regimes:
  * **Normal loading:** Waveform is a flat line near zero (current imbalance is negligible).
  * **External fault:** A transient spike that quickly decays to zero as the fault is outside the protection zone.
  * **Magnetizing inrush:** Highly asymmetric, unidirectional peaked current spikes that decay slowly over several cycles.
  * **Internal fault:** Large, symmetric, high-frequency, and sustained sinusoidal-like current waveforms that persist until the breaker operates.

### 20. Figure 6.2: Parameter-Space Coverage / Feature Distribution
* **File Name:** `fig_6_2.png`
* **LaTeX Label:** `fig:6.2`
* **Caption:** *Parameter-space coverage / feature distribution across event classes.*
* **What it Represents:** 
  A scatter plot representing the separation of the four classes in the DWT feature space. By plotting the approximation energy ($E_A$) versus the detail energy ($E_D$), it shows how the four classes occupy different zones, visually verifying why DWT energy is an effective feature set for classification.

### 21. Figure 6.3: Statistical Verification of the Generated Dataset
* **File Name:** `fig_6_3.png`
* **LaTeX Label:** `fig:6.3`
* **Caption:** *Statistical verification of the generated dataset.*
* **What it Represents:** 
  Plots (such as histograms) demonstrating that the generated scenarios cover a wide and unbiased distribution of physical parameters. It verifies that fault inception angles are uniformly swept from $0^\circ$ to $360^\circ$ and fault resistances are swept log-uniformly from $0.001\ \Omega$ to $99\ \Omega$.

### 22. Figure 6.4: LSTM Training and Validation History
* **File Name:** `fig_6_4.png`
* **LaTeX Label:** `fig:6.4`
* **Caption:** *Training and validation loss/accuracy curves for the LSTM classifier (best fold).*
* **What it Represents:** 
  This graph plots the training and validation loss (left y-axis) and accuracy (right y-axis) across 200 epochs:
  * It shows the loss decreasing smoothly to below 0.05.
  * Validation accuracy converges stably near 99%.
  * The absence of divergence between the training and validation lines confirms that the model generalizes well and does not overfit.

### 23. Figure 6.4b: Cross-Validation Trajectories across Folds
* **File Name:** `allfolds.png`
* **LaTeX Label (referred in line 639):** *None (referenced inline)*
* **Caption:** *Validation-accuracy trajectories across all five cross-validation folds.*
* **What it Represents:** 
  A line plot showing the epoch-by-epoch validation accuracy for all five cross-validation folds. The tightly bound paths show that the model's performance is highly stable and independent of the specific random train/validation split.

### 24. Figure 6.5: Five-Fold Cross-Validation Performance Summary
* **File Name:** `fig_6_5.png`
* **LaTeX Label:** `fig:6.5`
* **Caption:** *Five-fold cross-validation performance summary.*
* **What it Represents:** 
  A bar chart or box plot summarizing key performance metrics (Accuracy, Precision, Recall, F1-Score) across all five cross-validation runs, showing tight standard deviations (mean accuracy of $98.16 \pm 0.26\%$).

### 25. Figure 6.6: Confusion-Matrix Heatmap
* **File Name:** `fig_6_6.png`
* **LaTeX Label:** `fig:6.6`
* **Caption:** *Confusion-matrix heatmap of the DWT–LSTM classifier (counts and normalized).*
* **What it Represents:** 
  A detailed heatmap showing the classifier's predictions on the 1,800-case test set:
  * It shows that the standalone classifier correctly predicted 1,002 out of 1,008 Trip cases and 778 out of 792 No-Trip cases.
  * It highlights where the classifier failed: 6 false negatives and 14 false positives (which occur during extreme scenarios like high-resistance faults or severe saturation).

### 26. Figure 6.7: Operational Robustness Plots
* **File Name:** `fig_6_7.png`
* **LaTeX Label:** `fig:6.7`
* **Caption:** *Operational robustness: accuracy vs. SNR, zone-level performance, and cumulative detection rate.*
* **What it Represents:** 
  A multi-panel figure assessing the relay under non-ideal conditions:
  * **Accuracy vs. SNR:** Shows that the DWT-LSTM classifier maintains an accuracy of 98.6% even under severe 20 dB noise, degrading gracefully to 97.1% at 0 dB.
  * **Zone-Level Performance:** Verifies that fault detection remains high regardless of where the fault occurs along the winding (from 5% to 95% of winding taps).
  * **Cumulative Detection Rate:** Shows the distribution of fault detection times, confirming that the majority of faults are detected within 10–15 ms.

### 27. Figure 6.7b: Fault Detection Rate Heatmap
* **File Name:** `heatmap.png`
* **LaTeX Label (referred in line 708):** *None (referenced inline)*
* **Caption:** *Internal-fault detection-rate heatmap across fault resistance and inception angle.*
* **What it Represents:** 
  A 2D heatmap showing internal fault recall as a function of **fault resistance ($R_f$)** on one axis and **fault inception angle ($\varphi_i$)** on the other. It illustrates that the classifier achieves 100% detection for low-resistance faults, but the detection rate drops slightly (to ~88%) for high-resistance faults ($R_f > 80\ \Omega$) at specific angles. (Note: these missed cases are successfully recovered by the hybrid 87T element).

### 28. Figure 6.8: Comprehensive Performance Dashboard
* **File Name:** `fig_6_8.png`
* **LaTeX Label:** `fig:6.8`
* **Caption:** *Comprehensive performance dashboard of the proposed framework.*
* **What it Represents:** 
  A visual summary compiling all key metrics of the proposed hybrid protection system, showing its performance side-by-side with conventional harmonic restraint and standalone LSTM classifiers.

### 29. Figure 6.hcm: Hybrid Relay Confusion Matrix and Clearing Times
* **File Name:** `hybrid_cm_time.png`
* **LaTeX Label (referred in line 695):** *None (referenced inline)*
* **Caption:** *Hybrid relay per-category confusion matrix and fault-clearing-time comparison.*
* **What it Represents:** 
  * A confusion matrix showing that the **proposed hybrid relay** achieves **100% accuracy** (zero false trips, zero missed faults) on a balanced 500-case evaluation set, outperforming the standalone versions.
  * A bar chart comparing average clearing times: conventional harmonic restraint takes **45.5 ms**, the standalone LSTM takes **28.0 ms**, and the proposed hybrid relay takes **17.2 ms** (a $2.6\times$ speedup that significantly reduces thermal stress on the transformer).

### 30. Figure 6.ba: Before/After Protection Response Waveform
* **File Name:** `before_after.png`
* **LaTeX Label (referred in line 697):** *None (referenced inline)*
* **Caption:** *Before/after comparison: conventional standalone 87T versus the hybrid adaptive 87T + DWT–LSTM supervisor.*
* **What it Represents:** 
  Transient waveforms comparing the trip/restrain decisions of the conventional 87T relay and the proposed hybrid relay during a highly stressed test case:
  * Under an external fault with severe CT saturation and 20 dB noise, the conventional 87T relay false-trips (maloperates) due to distorted currents.
  * The proposed hybrid scheme successfully **vetoes** the false trip (restrains), proving the security enhancement provided by the DWT-LSTM supervisor.

### 31. Figure 6.9: Ablation Sensitivity Chart
* **File Name:** `fig_6_9.png`
* **LaTeX Label:** `fig:6.9`
* **Caption:** *Ablation sensitivity of classification accuracy to individual design choices.*
* **What it Represents:** 
  A bar chart showing the drop in classification accuracy when specific parts of the proposed model are removed:
  * Removing the temporal attention layer drops accuracy by **0.71 pp**.
  * Removing normalization drops accuracy by **2.87 pp**.
  * Using only approximation features (0-100 Hz) drops accuracy by a massive **7.65 pp**, proving that high-frequency detail features are critical.

### 32. Figure 6.10: ROC and Precision–Recall Curves
* **File Name:** `fig_6_10.png`
* **LaTeX Label:** `fig:6.10`
* **Caption:** *ROC and precision–recall curves for internal-fault detection (AUC $=0.9999$).*
* **What it Represents:** 
  * **Receiver Operating Characteristic (ROC) Curve:** Plots True Positive Rate vs. False Positive Rate, showing an Area Under the Curve (AUC) of 0.9999. It confirms the classifier's near-perfect discriminative capability.
  * **Precision-Recall Curve:** Confirms that high precision is maintained even at very high recall rates.
  * The chosen confidence threshold of **0.85** is shown to lie on the optimal knee of the curves.

### 33. Figure 6.11: Confidence-Score Distribution
* **File Name:** `fig_6_11.png`
* **LaTeX Label:** `fig:6.11`
* **Caption:** *Confidence-score distribution for Trip and No-Trip decisions.*
* **What it Represents:** 
  A histogram showing the frequency of the model's confidence scores:
  * The distribution is highly bimodal: correct predictions have confidence scores very close to 1.0 (highly confident).
  * Very few predictions lie in the ambiguous middle range (0.5 to 0.8), demonstrating that the classifier makes decisive and reliable predictions.
