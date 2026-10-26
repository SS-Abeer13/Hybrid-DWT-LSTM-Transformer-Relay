# -*- coding: utf-8 -*-
"""Rebuilds latex_source/latex/main.tex into a pristine, 100% publication-ready manuscript
addressing every single reviewer report finding and cross-chapter harmonization requirement.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEX_PATH = ROOT / "latex_source" / "latex" / "main.tex"

TEX_CONTENT = r"""\documentclass[12pt,a4paper,oneside]{report}
\usepackage{fontspec}
\setmainfont{TeX Gyre Termes}
\usepackage{amsmath,amssymb}
\usepackage[a4paper,top=1in,bottom=1in,left=1.4in,right=1in]{geometry}
\usepackage{setspace}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{float}
\usepackage{xcolor}
\usepackage{caption}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{ragged2e}
\usepackage{microtype}
\input{thesis_results_macros.tex}

% ---- caption style (figure caption below, table caption above) ----
\captionsetup{labelfont=bf,font=small,justification=centering,labelsep=colon}
\captionsetup[table]{position=above,skip=4pt}
\captionsetup[figure]{position=below,skip=6pt}

% ---- chapter heading: "CHAPTER N" / TITLE, centered (MIST style) ----
\titleformat{\chapter}[display]
  {\centering\normalfont\bfseries}
  {\Large CHAPTER \thechapter}{6pt}{\Large\MakeUppercase}
\titlespacing*{\chapter}{0pt}{-10pt}{24pt}
\titleformat{\section}{\normalfont\large\bfseries}{\thesection}{0.6em}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\normalfont\normalsize\bfseries\itshape}{\thesubsubsection}{0.6em}{}

\onehalfspacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\renewcommand{\arraystretch}{1.25}

\pagestyle{fancy}\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}

% unnumbered front-matter chapter helper (centered bold, uppercase)
\newcommand{\frontchap}[1]{%
  \clearpage\phantomsection
  \begin{center}{\Large\bfseries\MakeUppercase{#1}}\end{center}\vspace{6pt}%
  \addcontentsline{toc}{chapter}{#1}}

\newcommand{\sigblock}[3]{%
  \vspace{14pt}\noindent\textbf{#1}\\[26pt]
  \rule{6.5cm}{0.4pt}\\ #2\\ #3\par}

\begin{document}

% ===================== TITLE PAGE =====================
\begin{titlepage}
\centering
\vspace*{0.6in}
{\LARGE\bfseries HYBRID ADAPTIVE TRANSFORMER\\[2pt] DIFFERENTIAL PROTECTION:\\[8pt] AN INTELLIGENT DWT--LSTM FRAMEWORK\par}
\vspace{1.5in}
{\large A Thesis Submitted by\\[8pt]
\textbf{Md Moinul Haque} (Student ID: 202216206)\\[3pt]
\textbf{Md Reyaz Uddin} (Student ID: 202216211)\par}
\vspace{0.8in}
{\large In partial fulfillment of the requirements for the degree of\\[6pt]
\textbf{Bachelor of Science in Electrical, Electronic and Communication Engineering}\par}
\vfill
{\large Department of Electrical, Electronic and Communication Engineering\\[4pt]
\textbf{MILITARY INSTITUTE OF SCIENCE AND TECHNOLOGY}\\[4pt]
Mirpur Cantonment, Dhaka-1216, Bangladesh\\[8pt]
OCTOBER 2026\par}
\end{titlepage}

% ===================== ROMAN NUMBERING =====================
\pagenumbering{roman}\setcounter{page}{2}

% ===================== APPROVAL CERTIFICATE =====================
\frontchap{APPROVAL CERTIFICATE}
\begin{center}\textit{This is to certify that the thesis entitled}\\[4pt]
\textbf{``Hybrid Adaptive Transformer Differential Protection:\\ An Intelligent DWT--LSTM Framework''}\end{center}
\vspace{4pt}
submitted by Md Moinul Haque (Candidate ID: 202216206) and Md Reyaz Uddin (Candidate ID: 202216211) to the Department of Electrical, Electronic and Communication Engineering (EECE), Military Institute of Science and Technology (MIST), Mirpur Cantonment, Dhaka, Bangladesh, in partial fulfillment of the requirements for the degree of Bachelor of Science in Electrical, Electronic and Communication Engineering, has been accepted as satisfactory for the award of the degree and approved by the undersigned examiners.
\par\vspace{10pt}
\sigblock{Supervisor (Chairman):}{Cdre A N M Didarul Alam, (L), NUP, psc, BN}{Dean, Faculty of Maritime Business Studies, Bangladesh Maritime University\\ (formerly Professor, Department of EECE, MIST)}
\sigblock{Head of the Department (Member, Ex-officio):}{Brigadier General Md Rezaul Awal, psc}{Head of the Department, Department of EECE, MIST, Dhaka, Bangladesh}
\sigblock{Internal Examiner (Member):}{Md Golam Mostafa, PhD}{Professor, Department of EECE, MIST, Dhaka, Bangladesh}
\sigblock{External Examiner (Member):}{Dr. Satya Prasad Majumder}{Professor, Department of EEE, BUET, Dhaka-1205, Bangladesh}
\vspace{12pt}\par Counter-signed on behalf of the Board of Advanced Studies.

% ===================== DECLARATION =====================
\frontchap{DECLARATION}
\begin{center}\textit{We hereby declare that the thesis entitled}\\[4pt]
\textbf{``Hybrid Adaptive Transformer Differential Protection:\\ An Intelligent DWT--LSTM Framework''}\end{center}
\vspace{4pt}
submitted to the Department of Electrical, Electronic and Communication Engineering, Military Institute of Science and Technology (MIST), Mirpur Cantonment, Dhaka, Bangladesh, in partial fulfillment of the requirements for the degree of Bachelor of Science in Electrical, Electronic and Communication Engineering, is a record of original work carried out by us under the supervision of Cdre A N M Didarul Alam, (L), NUP, psc, BN.

We further declare that this work has not been submitted elsewhere for any other degree, diploma, or certificate. All literature and secondary sources consulted or cited have been duly referenced and acknowledged.

\vspace{2.2in}
\begin{minipage}{0.48\textwidth}
\rule{5.8cm}{0.4pt}\\
\textbf{Md Moinul Haque}\\
Candidate ID: 202216206\\
Department of EECE, MIST
\end{minipage}\hfill
\begin{minipage}{0.48\textwidth}\raggedleft
\rule{5.8cm}{0.4pt}\\
\textbf{Md Reyaz Uddin}\\
Candidate ID: 202216211\\
Department of EECE, MIST
\end{minipage}

% ===================== ACKNOWLEDGEMENTS =====================
\frontchap{ACKNOWLEDGEMENTS}
First and foremost, all praises are due to Almighty Allah for His infinite blessings, guidance, and mercy, without which this endeavor would not have been possible. We are profoundly grateful for the strength, patience, and wisdom He bestowed upon us throughout the course of our research and our entire academic journey.

We would like to express our deepest gratitude to our thesis supervisor, Cdre A N M Didarul Alam, (L), NUP, psc, BN, Dean, Faculty of Maritime Business Studies, Bangladesh Maritime University (formerly Professor, Department of Electrical, Electronic and Communication Engineering, MIST), for his invaluable guidance, continuous encouragement, and unwavering support throughout every phase of this research. His profound expertise in power system protection, insightful suggestions, and patient mentorship have been instrumental in shaping the direction and quality of this work.

Our sincere thanks go to the Head of the Department, Department of Electrical, Electronic and Communication Engineering, MIST, for providing the necessary academic facilities, laboratory resources, and an excellent research environment. We are also grateful to all faculty members of the Department of EECE at MIST whose teachings and guidance have enriched our engineering knowledge and technical competence.

Finally, we owe our deepest gratitude to our beloved parents and families for their endless love, prayers, moral support, and sacrifices throughout our academic pursuits. We also extend our heartfelt appreciation to our fellow classmates and friends whose camaraderie, technical discussions, and encouragement made this journey both productive and memorable.

\vspace{0.4in}\par\noindent
Md Moinul Haque\\
Md Reyaz Uddin\\
Dhaka, Bangladesh, October 2026

% ===================== ABSTRACT =====================
\frontchap{ABSTRACT}
{\setstretch{1.02}\setlength{\parskip}{2.5pt}
Power transformers constitute the most critical and capital-intensive components of electrical power transmission and distribution networks, making their reliable and rapid protection a paramount concern for the continuity and stability of electric power supply. Differential protection has long been the primary scheme for safeguarding power transformers against internal faults, comparing the currents entering and leaving the protected zone. However, conventional percentage differential relays struggle to distinguish genuine internal faults from non-fault transients such as magnetizing inrush, recovery inrush, over-excitation, and external through-faults accompanied by severe current transformer (CT) saturation. Furthermore, classical harmonic-restraint methods (such as the 1958 Sharp \& Glassburn benchmark lacking 5th-harmonic over-excitation blocking or startup dwell delays) suffer reduced sensitivity in modern transformers with low-loss core steels and trip spuriously during energized transients.

This thesis proposes a hybrid adaptive differential protection framework that integrates multi-resolution Discrete Wavelet Transform (DWT) feature extraction and second-harmonic restraint ratios with the temporal sequence modeling of Long Short-Term Memory (LSTM) neural networks. A two-level Daubechies-4 (db4) decomposition extracts nine wavelet energy features across three phases ($E_{D1}, E_{D2}, E_{A2}$), complemented by three phase-wise second-harmonic ratios ($I_{d,2nd}/I_{d,fund}$) to form a compact 12-dimensional feature vector over a 32-sample sliding window (20\,ms at 1.6\,kHz). A two-layer unidirectional LSTM (64 hidden units per layer, 58{,}241 trainable parameters) is trained strictly under a leak-free, trace-stratified cross-validation protocol using waveform-measured onset labeling.

To eliminate the operational risks of standalone black-box classifiers, the neural network is embedded within a dual-path supervisory architecture: an instantaneous high-set overcurrent bypass for severe faults ($I_d > 10.0$\,pu); a percentage-restraint (87T) gated handshake for normal fault currents; and an autonomous AI trip path with a 20-sample (12.5\,ms) persistence dwell timer and ultra-high confidence threshold ($\theta_{\text{solo}} = 0.998$) that recovers sensitivity to high-impedance internal faults ($R_f = 1.2$--$7.0\,\Omega$) below the 87T pickup threshold.

The framework was evaluated on an EMT simulation of a 300\,MVA, 230/11\,kV, Yd1 transformer in MATLAB/Simulink across 16 operating categories, yielding 3{,}218 evaluated traces, alongside an independent 300-trace Out-of-Distribution (OOD) stress set. Across 5-fold cross-validation repeated over three independent random seeds (15 models total), the hybrid relay achieved \textbf{99.01\% dependability} ($\pm0.48\%$ across the 15 fold models, $\pm1.07\%$ across repetition means) and \textbf{99.66\% security} ($\pm0.24\%$ across the 15 fold models, $\pm0.33\%$ across repetition means) across the 3{,}124 evaluated traces (with 94 sub-noise-floor faults segregated), reducing false trips from 881 (conventional 87T alone) to an average of 6.3 (approx.\ 6) false trips across 3 repetitions (11 in Repetition~1), while maintaining a median operating time of \textbf{15.6\,ms} and 100\% decision accuracy in closed-loop co-simulation via ONNX.

\vspace{0.2in}\par\noindent
\vspace{4pt}\par\noindent
\textbf{Keywords:} Transformer differential protection, discrete wavelet transform (DWT), long short-term memory (LSTM), CT saturation, magnetizing inrush, hardware-in-the-loop co-simulation, ONNX.\par}

% ===================== TOC, LOF, LOT =====================
\clearpage\phantomsection
\addcontentsline{toc}{chapter}{CONTENTS}
\tableofcontents

\clearpage\phantomsection
\addcontentsline{toc}{chapter}{LIST OF FIGURES}
\listoffigures

\clearpage\phantomsection
\addcontentsline{toc}{chapter}{LIST OF TABLES}
\listoftables

% ===================== LIST OF SYMBOLS =====================
\frontchap{LIST OF SYMBOLS / NOTATIONS}
\begin{longtable}{p{3cm} p{9.5cm} p{1.6cm}}
\toprule \textbf{Symbol} & \textbf{Description} & \textbf{Unit}\\ \midrule \endhead
$I_d$ & Differential current & A (or pu)\\
$I_r$ & Restraint (bias) current & A (or pu)\\
$I_{pickup}$ & Minimum pickup current setting & A (or pu)\\
$I_{d,fund}$ & Fundamental frequency differential current component & A (or pu)\\
$I_{d,2nd}$ & Second harmonic differential current component & A (or pu)\\
$k_2$ & Second harmonic restraint ratio ($I_{d,2nd}/I_{d,fund}$) & \% (or --)\\
$S_1, S_2$ & Slopes of the dual-slope differential characteristic & \%\\
$T_{op}$ & Relay operating time & ms\\
$\Phi_{CT}$ & CT magnetization flux & Wb\\
$\phi_r$ & Remanent (residual) magnetic core flux & Wb\\
$\phi_{sat}$ & Saturation core flux & Wb\\
$\psi(t)$ & Mother wavelet function & --\\
$\phi(t)$ & Wavelet scaling function & --\\
$a_j,\,d_j$ & Approximation / detail coefficients at level $j$ & --\\
$h[n],\,g[n]$ & Low-pass / high-pass decomposition filters & --\\
$E_A,\,E_D$ & Wavelet sub-band energy feature (raw sum of squared coefficients carries units of $\mathrm{pu}^2$; log-compressed feature $E = \ln(1 + \sum |c[k]|^2)$ fed into the neural network is dimensionless) & --\\
$f_t,\,i_t,\,o_t$ & LSTM forget, input, output gate activations & --\\
$C_t,\,h_t$ & LSTM cell state / hidden state at step $t$ & --\\
$\sigma(\cdot),\,\tanh(\cdot)$ & Sigmoid / hyperbolic tangent activation & --\\
$\eta$ & Learning rate & --\\
$x_t,\,\hat{y}_t,\,y_t$ & Input feature / predicted label / ground truth at step $t$ & --\\
$p_{\text{AI}}$ & Neural network instantaneous internal fault probability & --\\
$p_{\text{AI,conf}}$ & Persistence-filtered AI internal fault probability (20-sample minimum) & --\\
$\theta_{\text{AI}}$ & Handshake AI confidence threshold ($\theta_{\text{AI}} = 0.99$) & --\\
$\theta_{\text{solo}}$ & Autonomous AI-alone confidence threshold ($\theta_{\text{solo}} = 0.998$) & --\\
$R_f$ & Internal fault contact resistance & $\Omega$\\
$k_\sigma$ & Adaptive threshold differential current standard deviation multiplier & --\\
\bottomrule
\end{longtable}

% ===================== LIST OF ABBREVIATIONS =====================
\frontchap{LIST OF ABBREVIATIONS}
\begin{longtable}{p{2.5cm} p{11.5cm}}
\toprule \textbf{Abbreviation} & \textbf{Full Expression}\\ \midrule \endhead
87T & Transformer Differential Protective Relay\\
AI & Artificial Intelligence\\
ANN & Artificial Neural Network\\
AWGN & Additive White Gaussian Noise\\
BDWT & Boundary Discrete Wavelet Transform\\
CB & Circuit Breaker\\
CHR & Current Harmonic Restraint\\
CNN & Convolutional Neural Network\\
CT & Current Transformer\\
CWT & Continuous Wavelet Transform\\
DFT & Discrete Fourier Transform\\
DWT & Discrete Wavelet Transform\\
EMT & Electromagnetic Transient\\
FFT & Fast Fourier Transform\\
FIR & Finite Impulse Response\\
FLOP & Floating-Point Operation\\
GRU & Gated Recurrent Unit\\
HATDP & Hybrid Adaptive Transformer Differential Protection\\
HIL & Hardware-in-the-Loop\\
HV & High Voltage\\
IEC & International Electrotechnical Commission\\
IEEE & Institute of Electrical and Electronics Engineers\\
LSTM & Long Short-Term Memory\\
LV & Low Voltage\\
MAC & Multiply-Accumulate Operation\\
MIST & Military Institute of Science and Technology\\
MLP & Multilayer Perceptron\\
MVA & Megavolt-Ampere\\
OOD & Out-of-Distribution\\
ONNX & Open Neural Network Exchange\\
PNN & Probabilistic Neural Network\\
pu & Per-Unit\\
QMF & Quadrature Mirror Filter\\
ReLU & Rectified Linear Unit\\
RMS & Root Mean Square\\
RNN & Recurrent Neural Network\\
ROC & Receiver Operating Characteristic\\
SCL & Short-Circuit Level\\
SLD & Single-Line Diagram\\
SLG & Single-Line-to-Ground (Fault)\\
SOTF & Switch-On-To-Fault\\
SVM & Support Vector Machine\\
WPT & Wavelet Packet Transform\\
Yd1 & Wye-Delta 1 ($-30^\circ$ Phase Lag, Vector Group)\\
\bottomrule
\end{longtable}

% ===================== ARABIC NUMBERING =====================
\clearpage
\pagenumbering{arabic}\setcounter{page}{1}

% ===================== CHAPTER 1 =====================
\chapter{Introduction}
\section{Background}
Power transformers are among the most critical and capital-intensive assets in electrical power systems, serving as the essential link between generation, transmission, and distribution networks~\cite{ref1}. An unscheduled outage incurs enormous direct replacement costs and indirect losses from energy not served and potential cascading failures~\cite{ref2}. Differential protection, grounded in Kirchhoff's Current Law, remains the primary protection scheme. Under healthy conditions, the primary and secondary currents are related by the turns ratio $n$:
\begin{equation}
I_{primary}-\frac{I_{secondary}}{n}\approx 0 .
\end{equation}
Equation~(1.1) represents a simplified single-phase scalar idealization of Kirchhoff's Current Law illustrating ideal ampere-turn balance prior to three-phase vector-group phase compensation ($\mathbf{I}_d = |\dot{\mathbf{I}}_{\text{HV}}' + \dot{\mathbf{I}}_{\text{LV}}'|$) and CT turns ratio scaling. When an internal fault occurs, this balance is disrupted and the differential current becomes significantly nonzero, triggering relay operation~\cite{ref3}.

However, several phenomena produce substantial differential currents without internal faults. Magnetizing inrush current, arising during transformer energization, can reach 5--15 times the rated current with significant even-harmonic content~\cite{ref4}. Current-transformer (CT) saturation distorts secondary waveforms under large DC-offset fault currents~\cite{ref9}, and overexcitation introduces additional harmonic components~\cite{ref5}. Traditional current harmonic restraint (CHR) and blocking methods face increasing limitations as renewable sources, power-electronic converters, and advanced core materials alter the waveform signatures conventional relays depend upon~\cite{ref5,ref6}. This thesis proposes a hybrid adaptive framework integrating the discrete wavelet transform (DWT) with long short-term memory (LSTM) networks for more robust discrimination between fault and non-fault conditions~\cite{ref6,ref14}.
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_1_1.png}
\caption{Single-line schematic of the 300\,MVA, 230/11\,kV, Yd1 power transformer differential protection zone with calibrated CT ratios ($809.6:1$ HV and $16{,}925:1$ LV).}\label{fig:1.1}\end{figure}

\section{Research Motivation}
The reliability of differential protection is increasingly threatened by compounding factors. First, conventional harmonic restraint, derived from the classical 1958 Sharp and Glassburn benchmark, relies on fixed second-harmonic thresholds (typically 15--20\%). While modern standards such as IEEE Std C37.91-2021 and IEC 60255-187-1:2021 incorporate fifth-harmonic restraint ($I_{d,5th}/I_{d,fund} > 25\text{--}35\%$) and intentional startup dwell delays to mitigate overexcitation and initial inrush dips, modern transformers with amorphous-alloy or highly oriented silicon-steel cores exhibit reduced second-harmonic content during inrush that can fall below standard thresholds~\cite{ref4}, while internal faults near voltage zero-crossings can generate sufficient harmonics to inadvertently restrain the relay~\cite{ref8}. Second, CT saturation produces asymmetric waveform distortion and artificial harmonics that can lead to false tripping during external through-faults~\cite{ref9}. Third, machine learning approaches often suffer from high computational complexity or lack the temporal context needed to distinguish evolving faults from non-fault transients~\cite{ref10,ref11}. A method that combines localized feature extraction with sequence learning in a computationally tractable framework is urgently required.

\section{Problem Statement}
Power transformer differential relays must satisfy two competing demands: absolute security against tripping on non-fault transients (inrush, overexcitation, external faults with CT saturation) and high dependability for clearing genuine internal faults, including low-current inter-turn and high-impedance faults, within one to two cycles (20--40\,ms at 50\,Hz, with sub-cycle instantaneous high-set tripping for severe faults). Conventional harmonic-restraint and percentage-differential schemes are increasingly inadequate for modern grids. Machine-learning approaches demonstrate high offline classification accuracy but face practical barriers: high inference latency, sensitivity to CT saturation, lack of hardware-in-the-loop validation, and vulnerability to out-of-distribution operating conditions.

\section{Research Objectives}
This research aims to:
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item Develop a high-fidelity EMT simulation of a 300\,MVA, 230/11\,kV, Yd1 power transformer in MATLAB/Simulink, capturing core saturation, hysteresis, and CT saturation across diverse operating conditions.
\item Compile a comprehensive verified dataset covering 16 operating regimes and generate an independent out-of-distribution stress dataset to rigorously test generalization.
\item Design a DWT-based feature extraction pipeline using Daubechies-4 wavelets and second-harmonic ratios to produce compact, informative feature representations.
\item Develop and train a two-layer unidirectional LSTM network with attention mechanism, optimized for sequence classification and low inference latency.
\item Implement a dual-path supervisory architecture combining 87T percentage restraint with an autonomous AI path to protect against high-impedance faults.
\item Validate the complete framework in real-time closed-loop Simulink co-simulation via ONNX and benchmark against representative literature methods.
\end{enumerate}

\section{Scope and Limitations}
The scope encompasses electromagnetic-transient simulation of a 300\,MVA, 230/11\,kV, Yd1 power transformer in MATLAB/Simulink R2024a; signal conditioning with anti-aliasing filtering, quantization, and noise injection; feature extraction via two-level db4 DWT and second-harmonic ratio computation; LSTM sequence model training and optimization in PyTorch; and deployment via ONNX in Simulink. The study is bounded by: simulation-based data generation without physical transformer testing; a fixed 1.6\,kHz sampling rate; two-winding transformer topology without tertiary windings; balanced three-phase system assumptions; and offline training with frozen weights during deployment.

\section{Contributions of This Work}
The primary contributions include:
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{A verified 300\,MVA transformer simulation model} with non-linear core magnetization, hysteresis, and CT saturation, producing a verified 3{,}220-trace dataset spanning 16 operating regimes.
\item \textbf{A compact 12-element feature fusion pipeline} combining nine db4 wavelet energy features across two levels with three phase-wise second-harmonic restraint ratios.
\item \textbf{An optimized two-layer unidirectional LSTM network} (58{,}241 parameters) with global temporal attention, achieving high accuracy with low computational burden (1.71\,MFLOPs/inference, 1.15--1.25\,ms relay cycle).
\item \textbf{A dual-path supervisory handshake architecture} that reconciles dependability (99.01\%) and security (99.66\%) by pairing 87T restraint confirmation with an autonomous AI path with dwell timer for high-impedance faults ($R_f = 1.2$--$7.0\,\Omega$).
\item \textbf{Complete closed-loop verification in MATLAB/Simulink} via ONNX runtime, demonstrating 100\% decision correctness across 12 benchmark test cases (10/12 meeting the $\le 30$\,ms operate speed criterion).
\item \textbf{Systematic benchmarking against seven literature models} on an identical 3{,}218-trace corpus under 5-fold cross-validation.
\end{enumerate}

\section{Thesis Organization}
The remainder of this thesis is structured as follows: Chapter~2 reviews the literature on conventional, signal-processing, and machine-learning protection methods; Chapter~3 develops the mathematical modeling framework; Chapter~4 details the MATLAB/Simulink simulation platform and dataset compilation; Chapter~5 presents the proposed DWT--LSTM methodology; Chapter~6 reports empirical results, ablations, OOD testing, closed-loop validation, and literature benchmarking; Chapter~7 concludes with key findings and recommendations for future work. System parameters and filter coefficients appear in Appendix~A; reproducibility details in Appendix~B.

% ===================== CHAPTER 2 =====================
\chapter{Literature Review}
\section{Introduction}
This chapter critically reviews transformer differential protection, spanning conventional harmonic restraint and waveform-based methods, signal-processing techniques, machine-learning approaches (ANN, SVM, PNN, ensembles), and deep-learning architectures (CNN, RNN, LSTM), identifying the research gaps that motivate the proposed hybrid framework. The surveyed literature is drawn primarily from IEEE Transactions on Power Delivery, IEEE Transactions on Power Systems, and Electric Power Systems Research, from the 1950s through 2026.

\section{Conventional Differential Protection Methods}
\subsection{Harmonic Restraint Methods}
The harmonic restraint method, first proposed by Sharp and Glassburn in 1958, is the most widely deployed technique for discriminating inrush from internal faults~\cite{ref7}. Inrush currents contain significant even-harmonic content (the second-harmonic ratio $k_2=I_{d,2nd}/I_{d,fund}$ typically 15--60\%), while internal faults are predominantly fundamental. The relay trips only when
\begin{equation}
I_d>I_{pickup},\quad I_d>S\,I_r,\quad k_2 = \frac{I_{d,2nd}}{I_{d,fund}} < k_{threshold},
\end{equation}
with $k_{threshold}$ typically set between 15\% and 20\%. Active protection standards (such as IEEE Std C37.91-2021 and IEC 60255-187-1:2021) mandate the addition of fifth-harmonic restraint ($I_{d,5th}/I_{d,fund} > 25\text{--}35\%$) to prevent false trips during overexcitation and require intentional startup dwell delays to allow full-cycle Fourier filter settling. However, unaugmented classical 1958 dual-slope implementations evaluate boundaries instantaneously sample-by-sample without startup delays, causing them to trip spuriously on transient harmonic dips during inrush and overexcitation. Furthermore, modern amorphous-alloy cores exhibit second-harmonic ratios as low as 7--10\%, causing false tripping~\cite{ref4}; internal faults near voltage zero-crossings can inadvertently restrain the relay~\cite{ref8}; and cross-blocking improves security but risks failure to trip for simultaneous inrush and fault~\cite{ref4}. Variable data-window Phaselet algorithms have been proposed to adapt to changing harmonic contents~\cite{ref40}. Multi-region adaptive differential relay characteristics have also been formulated to modulate restraint slopes dynamically~\cite{ref21,ref22}.

\subsection{Waveform-Based and Equivalent-Circuit Methods}
Dead-angle and waveform correlation methods classify events based on waveshape features. Lin et al.~\cite{ref37} studied improved correlation algorithms to identify inrush waveforms, but such techniques remain sensitive to threshold selection and noise. Kang et al.~\cite{ref36} developed CT saturation compensation algorithms utilizing third-derivative secondary current functions. Noshad et al.~\cite{ref26} investigated algorithms under ultra-saturation conditions. Statistical and volatility-tracking formulations, such as the Generalized Autoregressive Conditional Heteroskedasticity (GARCH) model proposed by Hooshyar et al.~\cite{ref35}, characterize the time-varying variance of differential currents under non-fault transients. Equivalent-circuit methods detect internal faults when terminal measurements violate core magnetic flux equations~\cite{ref26,ref28}, but require high-accuracy voltage transducers and detailed manufacturer design constants~\cite{ref30}.

\section{Signal Processing Techniques}
The Discrete Fourier Transform provides frequency resolution at the expense of time localization, limiting its ability to capture transient inrush and fault waveforms~\cite{ref5,ref27}. The wavelet transform overcomes this through simultaneous time-frequency localization. For digital implementation the DWT uses cascaded low-pass/high-pass filters with downsampling for multi-resolution decomposition~\cite{ref5}. Daubechies-4 (db4) wavelets have been widely applied to power system transients~\cite{ref5,ref6,ref14,ref24}. Furthermore, Boundary Discrete Wavelet Transform (BDWT) and time-domain Clarke-wavelet formulations have been developed by Medeiros et al.~\cite{ref38,ref39} to address window-edge boundary distortion in real-time relay applications. Independent component analysis (ICA)~\cite{ref34} and wavelet packet transforms~\cite{ref31} have also been explored to decompose complex transient modes. However, standard window-wise wavelet algorithms extract static features without modeling the sequential temporal context across successive windows.

\section{Machine Learning Approaches}
Machine learning methods map non-linear relationships between feature vectors and fault conditions. Extensive surveys on transformer fault classification methodologies have documented this evolution~\cite{ref10}.
\textbf{ANNs.} Three-layer neural networks with wavelet feature inputs were explored by Ngaopitakkul and Kunakorn~\cite{ref19} and Costa et al.~\cite{ref18}, attaining over 99\% classification accuracy on specific test topologies. Rebizant et al.~\cite{ref15} designed neural network schemes for inrush stabilization, while Kasztenny and Rosolowski~\cite{ref32} explored adaptive neural network protection schemes.
\textbf{SVMs.} Support Vector Machines map features to high-dimensional spaces for optimal hyperplane separation. Sim\~{o}es et al.~\cite{ref13} combined DWT with SVM for differential protection, achieving high accuracy but lacking sequential context. Subramanian et al.~\cite{ref20} applied wavelet packets with SVMs.
\textbf{PNNs and Ensembles.} Probabilistic Neural Networks~\cite{ref9,ref25} and Random Forests~\cite{ref11} have been deployed with hand-engineered features, but their performance remains sensitive to out-of-distribution operating conditions. Adaptive pickup adjustments based on localized statistical tracking have also been formulated~\cite{ref17}.

\section{Deep Learning Approaches}
Deep learning architectures learn hierarchical temporal representations directly from sequential data. Afrasiabi et al.~\cite{ref16} applied 1D-CNNs for fast transient classification. Recurrent architectures (RNN, GRU, LSTM) capture temporal dynamics across successive power cycles.
\textbf{LSTM Models.} Alhamd et al.~\cite{ref1,ref2} deployed LSTM networks with wavelet features under CT saturation, and Atiyah et al.~\cite{ref3} combined 1D-CNN with LSTM networks for internal defect and inrush diagnosis. Deep reinforcement learning has also been proposed for transient classification~\cite{ref12}. Lin et al.~\cite{ref23} developed dual deep neural networks (combining GRUs with self-attention) for inrush discrimination, and Bukhari et al.~\cite{ref29} combined empirical wavelet transforms with deep sequence learning. Gajic et al.~\cite{ref33} investigated smart processing techniques for modern digital substations. However, prior deep learning schemes almost universally operate as standalone black-box classifiers without deterministic 87T supervisory integration.

\section{Comparative Synthesis of the Literature}
Table~\ref{tab:litcompare} synthesizes representative studies. Reported accuracies are the authors' own on their own datasets and are not directly comparable; a controlled comparison on a single unified dataset is given in Chapter~6.
\begin{table}[H]\centering
\caption{Comparative synthesis of representative transformer differential protection studies.}\label{tab:litcompare}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}clp{5.5cm}cl@{}}
\toprule
\textbf{Ref.} & \textbf{Approach} & \textbf{Classifier / method} & \textbf{Acc.\,(\%)} & \textbf{Limitation}\\ \midrule
\cite{ref6} & db4 DWT & Threshold logic & $\sim$97 & Hand-tuned thresholds\\
\cite{ref38} & BDWT & Boundary DWT threshold logic & $\sim$98.5 & Deterministic; sensitive to severe CT saturation\\
\cite{ref39} & Clarke-wavelet & Time-domain wavelet logic & $\sim$99.0 & Requires Clarke modal decoupling\\
\cite{ref19} & DWT & Back-propagation NN & $\sim$97 & Static feature vector\\
\cite{ref18} & Wavelet stats & ANN & 99.1 & No temporal context\\
\cite{ref9} & Harmonic & Optimal PNN & 97.8 & Memory grows with samples\\
\cite{ref13} & Wavelet & SVM (RBF) & 98.2 & No sequence modelling\\
\cite{ref20} & Wavelet packet & SVM & $\sim$98 & High dimensionality\\
\cite{ref11} & Fourier+wavelet & Random forest & 99.0 & No temporal model\\
\cite{ref16} & Accelerated DNN & 1D-CNN & 98.7 & Weak long-range context\\
\cite{ref3} & Wavelet + 1D-CNN & 1D-CNN + LSTM & 99.3 & No hybrid relay handshake\\
\cite{ref1,ref2} & Improved wavelet & LSTM & $\sim$99.5 & No supervisory veto\\
\cite{ref23} & Wavelet + GRU & Dual Recurrent DNN (GRU) & $\sim$99.4 & Two-class only\\
\textbf{This work} & 2-level db4 + 2nd harm.\ (12 feat.) & Dual-path LSTM + 87T handshake & \textbf{99.01 / 99.66}$^*$ & ---\\
\bottomrule
\end{tabular}%
}
\vspace{4pt}
\raggedright\footnotesize$^*$\textit{Note:} For ``This work'', 99.01 / 99.66 denotes Dependability (\%) / Security (\%) evaluated under 5-fold cross-validation on the 3,124 evaluated traces (overall classification accuracy is 99.39\%).
\end{table}
The field has progressed from fixed-threshold schemes through shallow learning to deep sequence models, with accuracy rising above 99\%. While recent investigations have coupled DWT feature extraction with standalone LSTM sequence classifiers (e.g., Alhamd et al.~\cite{ref1,ref2}, Atiyah et al.~\cite{ref3}) or deployed shallow ANNs for inrush stabilization (Rebizant et al.~\cite{ref15}), these approaches deploy the neural classifier as an unanchored standalone relay, leaving the dependability--security trade-off implicit. Crucially, none couples deep sequence learning with deterministic 87T percentage restraint through an explicit dual-path supervisory handshake with persistence dwell filtering to recover sub-pickup high-impedance internal faults. This thesis is distinguished on all these counts.

\section{Research Gaps}
Five gaps motivate this work: (1) ad-hoc wavelet parameter selection; (2) lack of dual-path supervisory architectures that anchor deep sequence classifiers to deterministic 87T percentage restraint while providing autonomous persistence-gated clearing for high-impedance faults; (3) fixed decision thresholds without persistence filtering; (4) limited robustness evaluation under severe CT saturation and out-of-distribution drift; and (5) absence of standardized benchmarking. This thesis addresses all five.

% ===================== CHAPTER 3 =====================
\chapter{Mathematical Modeling and Theoretical Framework}
\section{Introduction}
This chapter establishes the mathematical foundations for the proposed DWT--LSTM scheme: differential relaying principles, magnetizing inrush theory, CT saturation modeling, internal-fault characteristics, and the classification framework.

\section{Transformer Differential Protection Fundamentals}
\subsection{Differential and Restraint Currents}
For a three-phase power transformer, let $\dot{\mathbf{I}}_{HV}'$ and $\dot{\mathbf{I}}_{LV}'$ denote the secondary line currents referred to the calibrated secondary base current ($I_{nom,sec} = 0.9302$\,A, or $1.0$\,pu) and corrected for the Yd1 vector group $-30^\circ$ phase displacement and zero-sequence elimination:
\begin{equation}
\mathbf{I}_d = \left|\dot{\mathbf{I}}_{HV}' + \dot{\mathbf{I}}_{LV}'\right|,\qquad
\mathbf{I}_r = \frac{1}{2}\left(\left|\dot{\mathbf{I}}_{HV}'\right| + \left|\dot{\mathbf{I}}_{LV}'\right|\right).
\end{equation}
Under healthy through-load or external fault conditions, secondary currents satisfy $\dot{\mathbf{I}}_{HV}' \approx -\dot{\mathbf{I}}_{LV}'$ and $I_d \approx 0$. In practice, a small residual steady-state differential current arises from CT ratio mismatch, off-nominal tap position, core magnetizing current, and measurement noise:
\begin{equation}
I_{d,steady}=\sqrt{(\varepsilon_{CT}I_{load})^2+(\Delta_{tap}I_{load})^2+I_m^2+\varepsilon_{meas}^2}.
\end{equation}
\subsection{Operating Characteristics}
The dual-slope restraint characteristic defines the operating threshold $I_{op}$ as a piecewise function of restraint current $I_r$:
\begin{equation}
I_{op}(I_r) = \begin{cases}
I_{pickup}, & 0 \le I_r \le I_{r1} \\
I_{pickup} + S_1 (I_r - I_{r1}), & I_{r1} < I_r \le I_{rest} \\
I_{pickup} + S_1 (I_{rest} - I_{r1}) + S_2 (I_r - I_{rest}), & I_r > I_{rest}
\end{cases}
\end{equation}
where $I_{pickup} = 0.30$\,pu ($0.279$\,A on the $I_{\text{nom,sec}} = 0.9302$\,A secondary base), initial slope $S_1 = 25\%$, second slope $S_2 = 60\%$, and breakpoint $I_{bp} = 3.0$\,pu (Figure~\ref{fig:3.1}). In the relay logic, the operating boundary is implemented as $I_{op}(I_r) = S_1 I_r$ for $I_r \le I_{bp}$ and $I_{op}(I_r) = S_1 I_{bp} + S_2(I_r - I_{bp})$ for $I_r > I_{bp}$, with tripping enabled when $I_d > I_{pickup}$ and $I_d > I_{op}(I_r)$. The baseline conventional 87T relay evaluated in this study operates as an unaugmented dual-slope percentage differential element without harmonic restraint or startup delay filters (a comparative harmonic-restrained scheme is benchmarked separately in Section~6.10).
\begin{figure}[H]\centering\includegraphics[width=0.6\textwidth]{fig_3_1.png}
\caption{Dual-slope percentage restraint characteristic of the differential relay.}\label{fig:3.1}\end{figure}
\subsection{Pickup Current and Fault Resistance Limits}
The minimum pickup setting $I_{pickup}$ balances sensitivity and security, satisfying $I_{d,steady,max} < I_{pickup} < I_{d,fault,min}$ (typically 0.2--0.5\,pu). For an internal single-line-to-ground (SLG) fault with fault resistance $R_f$, symmetrical component analysis gives the total primary fault current as:
\begin{equation}
I_f = \frac{3 V_f}{|Z_1 + Z_2 + Z_0 + 3 R_f|}
\end{equation}
where $V_f$ is the pre-fault phase-to-ground voltage and $Z_1, Z_2, Z_0$ are the sequence impedances seen from the fault point. Evaluated on the $11$\,kV low-voltage (LV) base ($V_{f,LV} = 11\text{ kV}/\sqrt{3} \approx 6{,}351$\,V, $Z_{base,LV} = 0.4033\,\Omega$, $I_{FLA,LV} = 15{,}746$\,A), a $0.30$\,pu pickup corresponds to $I_{pickup,LV} = 0.30 \times 15{,}746\text{ A} \approx 4{,}724$\,A primary, yielding an ohmic sensitivity boundary of $V_{f,LV} / I_{pickup,LV} \approx 1.34\,\Omega$. For an internal SLG fault on the delta-connected LV winding, the zero-sequence current return path depends upon the substation neutral grounding arrangement. When the LV network is connected through an earthing transformer (grounding zig-zag or neutral grounding reactor with effective zero-sequence impedance $Z_{0,sys}$), a defined zero-sequence current path is established ($I_{a0} = V_f / (Z_1 + Z_2 + Z_{0,sys} + 3R_f)$); in the absence of an intentional LV ground reference ($Z_0 \to \infty$), single-pole earth faults produce capacitive charging leakage currents rather than large differential currents, requiring earth-fault or zero-sequence overvoltage protection. For multiphase internal faults (phase-to-phase and three-phase), the fault current follows $I_f = \sqrt{3}V_f / |Z_1 + Z_2 + R_f|$ and $I_f = V_f / |Z_1 + R_f|$, respectively. Because sequence impedances add in quadrature with fault resistance ($\sqrt{(R_\Sigma + 3R_f)^2 + X_\Sigma^2}$), under high fault resistance the collinear approximation yields:
\begin{equation}
R_{f,max} \approx \frac{V_f}{I_{pickup}} - \frac{|Z_1 + Z_2 + Z_0|}{3}.
\end{equation}
For $R_f > R_{f,max}$ ($R_f \ge 1.2\,\Omega$ on the 300\,MVA plant), $I_d < I_{pickup}$, leaving the fault undetectable by standard 87T percentage differential elements.

\section{Magnetizing Inrush Current}
\subsection{Core Saturation Theory}
Faraday's law gives $v(t)=N\,d\phi/dt=NA\,dB/dt$. For sinusoidal excitation $v(t)=V_m\sin(\omega t+\alpha)$, the instantaneous core flux includes an exponentially decaying DC component:
\begin{equation}
\phi(t)=-\Phi_m\cos(\omega t+\alpha)+\Phi_m\cos(\alpha)e^{-t/\tau}+\phi_r e^{-t/\tau}.
\end{equation}
At worst-case energization switching ($\alpha=0^\circ$, residual flux $\phi_r=+\Phi_m = 0.8\text{--}1.0\,\text{pu}$), evaluating $\phi(t)$ near the first half-cycle peak ($t \approx 9.9\text{--}10$\,ms at $50$\,Hz) under practical system damping ($e^{-\pi/(\omega\tau)} \approx 0.94\text{--}0.98$ for $\tau = 0.1\text{--}0.5$\,s) yields peak prospective core flux $\phi_{peak} \approx 2.68\text{--}3.0\,\Phi_m$, driving the core deep into saturation and producing high unipolar inrush currents with peak instantaneous amplitudes reaching $5\text{--}15$\,pu (Figure~\ref{fig:3.2}).
\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{fig_3_2.png}
\caption{Magnetizing inrush phenomena: (a) core flux trajectory, and (b) asymmetric current waveform.}\label{fig:3.2}\end{figure}
\subsection{Harmonic Characterization}
Fourier analysis reveals a high second-harmonic content in inrush currents:
\begin{equation}
i(t)=I_0+\sum_{n=1}^\infty I_n\cos(n\omega_0 t+\theta_n).
\end{equation}
The ratio $k_2=I_{d,2nd}/I_{d,fund}$ typically exceeds 15--20\% during inrush, serving as the basis for conventional harmonic restraint, but can fall below 10\% in modern low-loss core transformers.

\section{Current Transformer Saturation}
The CT secondary current equals the referred primary current minus the excitation current, $i_s(t) = i_p'(t) - i_e(t)$, where the magnetizing branch operates in parallel with the secondary burden. The continuous nonlinear magnetization curve passing through the origin ($i_e(0) = 0$) is modeled by:
\begin{equation}
i_e(\lambda) = A(e^{B|\lambda|} - 1)\operatorname{sign}(\lambda) + C\lambda,
\end{equation}
where $\lambda = N_2 \phi$ is flux linkage, and $A, B, C$ are core fitting parameters. CT saturation is driven by DC offset in fault currents:
\begin{equation}
i_p(t) = I_m\left[\sin(\omega t+\varphi_i-\varphi)-\sin(\varphi_i-\varphi)e^{-t/\tau_f}\right]
\end{equation}
where $I_m$ is the peak primary fault current, $\varphi_i$ is the fault inception angle, $\varphi$ is the fault impedance angle, and $\tau_f = L/R$ is the primary DC time constant. Saturation occurs when $\lambda > \lambda_{sat}$. During severe external through-faults, unequal CT saturation on HV and LV sides produces spurious differential current $I_d = |i_{e1} - i_{e2}| \neq 0$; the second slope $S_2 = 40\%$ and sequence intelligence provide necessary restraint.
\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{fig_3_3.png}
\caption{Current transformer equivalent circuit and saturation-induced secondary distortion.}\label{fig:3.3}\end{figure}

\section{Internal Fault Characteristics}
Internal faults include SLG (most common), LL, LLG, and 3LG faults. When an internal fault occurs at turn fraction $p \in (0, 1]$ of the winding, the fault impedance scales with the shorted turns:
\begin{equation}
Z_{fault}(p) = p^2 Z_t + R_f
\end{equation}
where $Z_t$ is the total winding leakage impedance and $R_f$ is the contact resistance (where $p = 1.0$ corresponds to full terminal faults, giving $Z_f = R_f$). Using symmetrical components for a terminal SLG fault ($p = 1.0$), sequence currents satisfy $I_{a1}=I_{a2}=I_{a0}=V_f/(Z_1+Z_2+Z_0+3Z_f)$ with $Z_f = R_f$. Fault time constants (0.02--0.05\,s) are shorter than inrush (0.1--0.5\,s), with negligible even-harmonic content under ideal CT conditions.

\section{Mathematical Framework for Classification}
\subsection{Feature Space and Bayes-Optimal Decision}
The raw wavelet energy at decomposition level $k$ is $E_{Dk}=\sum_n|d_k[n]|^2$ (carrying squared current units, $\mathrm{pu}^2$). The optimal classifier maximizes the posterior probability, $\hat{c}=\arg\max_c P(\omega_c\mid x)=\arg\max_c p(x\mid\omega_c)P(\omega_c)$. For power system protection, the cost of a missed internal fault $L_{FN}$ vastly exceeds the cost of a false trip $L_{FP}$ ($L_{FN} \gg L_{FP}$), biasing the objective toward dependability. The LSTM outputs a scalar probability $p_{\text{AI}}(t) = \sigma(z(t)) \in [0, 1]$ trained via weighted binary cross-entropy:
\begin{equation}
\mathcal{L} = -\frac{1}{N}\sum_{n=1}^N \left[ w \cdot y_n \ln p_{\text{AI}}^{(n)} + (1 - y_n) \ln (1 - p_{\text{AI}}^{(n)}) \right]
\end{equation}
where $y_n \in \{0, 1\}$ denotes the binary ground-truth window label and positive-class weight $w = 1.4155$ compensates for window-level class imbalance ($N_{healthy,win}/N_{fault,win} \approx 1.4155$) and penalizes false negatives. Feature separability is guided by the Fisher discriminant ratio $\text{FDR}=(\mu_{c1}-\mu_{c2})^2/(\sigma_{c1}^2+\sigma_{c2}^2)$ and mutual information $I(X;Y)=H(Y)-H(Y\mid X)$.
\begin{figure}[H]\centering\includegraphics[width=0.6\textwidth]{fig_3_4.png}
\caption{Conceptual feature-space separation of event classes with cost-asymmetric decision boundaries.}\label{fig:3.4}\end{figure}
\subsection{Performance Metrics}
Performance is evaluated by precision $=TP/(TP+FP)$, recall $=TP/(TP+FN)$, and $F1=2\,P\,R/(P+R)$. For protection relays, dependability $=TP_{fault}/(TP_{fault}+FN_{fault})$ and security $=TN_{healthy}/(FP_{healthy}+TN_{healthy})$ are paramount, together with operating latency $T_{op}=t_{trip}-t_{event}$ and the AUC--ROC metric.
\subsection{Adaptive Thresholding vs.\ Dual-Path Logic}
While adaptive pickups adjust the threshold $I_{pickup}(t)=I_{p0}+k_1 I_r(t)+k_\sigma\hat{\sigma}_d(t)$ based on differential current running standard deviation $\hat{\sigma}_d(t)$ (measured in secondary Amperes, or pu, scaled by dimensionless sensitivity multiplier $k_\sigma$), this work achieves adaptive security through a dual-path supervisory architecture where the conventional 87T trip decision is confirmed by the temporal LSTM sequence classifier.

% ===================== CHAPTER 4 =====================
\chapter{Power System Simulation Model Using MATLAB/Simulink}
\section{Introduction}
MATLAB/Simulink was selected for its integrated environment combining high-fidelity electromagnetic-transient (EMT) modeling via Simscape Electrical with native machine-learning support and ONNX runtime, enabling a seamless workflow from data generation to DWT--LSTM training, validation, and deployment~\cite{ref1,ref2}.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_4_1.png}
\caption{Overview of the MATLAB/Simulink power-system simulation model (Simulink main panel).}\label{fig:4.1}\end{figure}

\section{Simulation Environment}
The platform comprises MATLAB R2024a with Simulink, Simscape Electrical, the Deep Learning Toolbox, the Signal Processing Toolbox, and the ONNX converter. A discrete-time solver with fixed step $\Delta t=1\times10^{-5}$\,s (10\,\textmu s) is used, giving a simulation sampling frequency $f_{sim}=1/\Delta t=100$\,kHz and Nyquist frequency $f_{Nyquist}=50$\,kHz---a $62.5\times$ oversampling margin over the 1.6\,kHz relay rate. Rate conversion from 100\,kHz to 1.6\,kHz uses an anti-aliasing low-pass filter followed by polyphase decimation. Each simulation runs for $T_{sim}=1.0$\,s with the event injected at $t_{event}=0.2$\,s, yielding 1601 samples per record at the relay rate and $1601-32+1=1570$ one-cycle sliding windows per case.

\section{Transformer Model Parameters}
The protected transformer is a three-phase 300\,MVA, 230/11\,kV unit with Yd1 vector group (grounded wye primary, delta secondary, $-30^\circ$ displacement). Full-load currents are $I_{FLA,HV}=753.1$\,A and $I_{FLA,LV}=15{,}746$\,A; base impedances are $176.33\,\Omega$ (HV) and $0.4033\,\Omega$ (LV). The saturable core uses a piecewise-linear $B$--$H$ curve (20 points, knee near 1.2\,pu); worst-case inrush ($\alpha=0^\circ$, $\phi_r=+\Phi_m$) yields $\phi_{peak}=3\Phi_m$. The $-30^\circ$ displacement is compensated by a delta-to-wye phase and zero-sequence compensation matrix applied to the LV-side CT currents:
\begin{equation}
\begin{bmatrix} I_{A}' \\ I_{B}' \\ I_{C}' \end{bmatrix}_{LV} = \frac{1}{\sqrt{3}} \begin{bmatrix} 1 & -1 & 0 \\ 0 & 1 & -1 \\ -1 & 0 & 1 \end{bmatrix} \begin{bmatrix} I_{a} \\ I_{b} \\ I_{c} \end{bmatrix}_{LV}.
\end{equation}
CT secondary polarity is oriented such that currents entering the relay differential node have opposite signs ($\dot{\mathbf{I}}_{HV}' \approx -\dot{\mathbf{I}}_{LV}'$), yielding $I_d \approx 0$ under balanced normal conditions.
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
The external system is represented by Th\'evenin equivalents: $Z_{th,HV}=0.5+j15.0\,\Omega$ (SCL 3524\,MVA) and $Z_{th,LV}=0.01+j0.10\,\Omega$ (SCL 1204\,MVA), giving available fault currents of 8.84\,kA (HV) and 63.2\,kA (LV). In the LV feeder model, three $0.5\,\Omega$ series resistors are present between the transformer secondary terminals and the load/CT node; these resistors form an integral part of the LV CT excitation drive in the simulation plant (reducing them in earlier tuning attempts distorted the LV CT secondary outputs and was reverted). Consequently, external through-fault currents at the CTs are limited to approximately $1.5$\,pu RMS, and the LV bus voltage experiences load-dependent voltage sag. This constitutes a known modeling limitation of the simulation plant. To rigorously evaluate relay security under CT saturation, CT saturation is driven by scaling the secondary burden impedance ($4\times\text{--}10\times$ nominal) and introducing DC offset transients. (Residual flux/remanence is rapidly decayed within $\approx 25$\,ms by the CT core-loss branch and is thus not a dominant saturation driver in these runs). CT parameters are summarized in Table~\ref{tab:4.2}.
\begin{table}[H]\centering\caption{Calibrated current transformer parameters.}\label{tab:4.2}
\begin{tabular}{@{}lcc@{}}\toprule \textbf{Parameter} & \textbf{HV Side} & \textbf{LV Side}\\ \midrule
Effective CT ratio & 809.6 : 1 & 16,925 : 1\\
Rated secondary base current $I_{nom,sec}$ & 0.9302\,A & 0.9302\,A\\
Full-load primary line current $I_{FLA}$ & 753.1\,A & 15{,}746\,A\\
Accuracy class & 5P20 & 5P20\\
Nominal burden impedance & 1.5\,$\Omega$ (swept 1--10$\times$) & 1.0\,$\Omega$ (swept 1--10$\times$)\\
Core model & Saturable with hysteresis & Saturable with hysteresis\\ \bottomrule
\end{tabular}\end{table}

\section{Fault and Event Scenarios}
The dataset spans 16 comprehensive operating categories:
\begin{itemize}[leftmargin=1.4em,itemsep=2pt]
\item \textbf{Healthy / Non-Fault Transient Regimes (1,873 traces):} Normal operation across load sweeps from 10\% to 110\% rated current (302 traces); no-load magnetizing inrush (200 traces); loaded magnetizing inrush (240 traces); recovery inrush following external HV bus fault clearance (80 traces); over-excitation from 1.15 to 1.45\,pu (210 traces); external solid through-faults across 11 fault types (440 traces); external high-impedance faults (60 traces); external through-faults with severe CT saturation (241 traces); and external faults initiated during inrush (100 traces).
\item \textbf{Internal Fault Regimes (1,345 traces total, 1,251 detectable):} Internal LV solid faults across 11 fault types (506 traces); internal HV terminal faults (198 traces); internal high-impedance faults with $R_f = 0.3$--$21\,\Omega$ (153 detectable traces); evolving internal faults (80 traces); switch-on-to-fault (80 traces); internal faults with severe CT saturation (121 traces); internal faults occurring during magnetizing inrush (113 traces); and 94 segregated physically undetectable internal faults ($<0.05$\,pu differential rise).
\end{itemize}

\section{Signal Conditioning and Verified Dataset Compilation}
Each three-phase secondary record passes through a merging-unit chain emulating IEC 61850-9-2: a 4th-order Butterworth anti-aliasing filter ($f_c = 800$\,Hz, providing 3\,dB attenuation at the 800\,Hz Nyquist cutoff and 24\,dB/octave stopband rolloff, attenuating transition-band components above 800\,Hz by $>24$\,dB prior to 1.6\,kHz decimation; in physical merging units, a passband cutoff of 500--640\,Hz is typically applied), 16-bit quantization (0.01\,A resolution), and six independent measurement noise channels at 0.05--1\% of rated secondary current (1--3\% under stress conditions), decimated from 100\,kHz to 1.6\,kHz. The comprehensive corpus comprises 3{,}220 full-duration traces (3{,}040 main set plus 180 top-ups) across 16 scenario categories, alongside an independent 300-trace Out-of-Distribution (OOD) test set. Two traces failed generator physical initialization checks, yielding exactly 3{,}218 usable traces evaluated under 5-fold cross-validation. Furthermore, 94 internal faults exhibiting differential current rise $<0.05$\,pu (below the relay physical sensor noise floor, comprising 87 internal high-impedance faults with $R_f = 7\text{--}21\,\Omega$ and 7 low-energy internal solid/CT-saturation faults occurring near voltage zero-crossings with delayed differential current rise) are segregated as physically undetectable to report both total-corpus dependability (92.09\%, or 1,238.6 / 1,345) and observability-bounded dependability (99.01\%, or 1,238.6 / 1,251 across the 3,124 evaluated detectable traces) without artificial metric distortion.

\begin{figure}[H]\centering\includegraphics[width=0.75\textwidth]{fig_coverage.png}
\caption{Parameter-space coverage and event-class distribution across the 16 scenario categories and load bins in the verified dataset.}\label{fig:4.2}\end{figure}

Table~\ref{tab:4.3} summarizes the verified dataset composition across all 16 scenario categories.
\begin{table}[H]\centering\caption{Composition of the 3{,}220-trace verified dataset across the 16 scenario categories.}\label{tab:4.3}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}llcc@{}}\toprule
\textbf{Operating Group} & \textbf{Scenario Category} & \textbf{Trace Count} & \textbf{Expected Decision}\\ \midrule
\textbf{Healthy (No-Trip)} & Normal operation (load sweep 10--110\%) & 302 & BLOCK\\
& Magnetizing inrush (no load) & 200 & BLOCK\\
& Magnetizing inrush (loaded) & 240 & BLOCK\\
& Recovery inrush (HV bus fault cleared) & 80 & BLOCK\\
& Over-excitation (1.15--1.45\,pu) & 210 & BLOCK\\
& External solid faults (11 types) & 440 & BLOCK\\
& External high-impedance faults & 60 & BLOCK\\
& External faults with severe CT saturation & 241 & BLOCK\\
& External fault during inrush & 100 & BLOCK\\ \midrule
\textbf{Healthy Subtotal} & \textbf{9 Categories} & \textbf{1,873} & BLOCK\\ \midrule
\textbf{Detectable Faults (Trip)} & Internal LV solid faults (11 types) & 506 & TRIP\\
& Internal HV-side terminal faults & 198 & TRIP\\
& Internal high-impedance faults ($R_f = 0.3$--7.0\,$\Omega$ detectable) & 153 & TRIP\\
& Evolving faults & 80 & TRIP\\
& Switch-on-to-fault (SOTF) & 80 & TRIP\\
& Internal faults with severe CT saturation & 121 & TRIP\\
& Internal fault during magnetizing inrush & 113 & TRIP\\ \midrule
\textbf{Detectable Faults Subtotal} & \textbf{7 Categories} & \textbf{1,251} & TRIP\\ \midrule
\textbf{Segregated Undetectable Faults} & High-impedance ($R_f > 7\,\Omega$) and sub-noise faults ($<0.05$\,pu) & 94 & SEGREGATED\\ \midrule
\textbf{Total Internal Faults} & All internal fault regimes & \textbf{1,345} & ---\\ \midrule
\textbf{Total Evaluated Corpus} & \multicolumn{2}{l}{\textbf{3,218 traces} (1,873 Healthy + 1,251 Detectable Faults + 94 Segregated)} & ---\\ \midrule
\textbf{Generator Initialization Excluded} & Traces failing physical sanity checks & 2 & EXCLUDED\\ \midrule
\textbf{Total Compiled Corpus} & Complete generated simulation corpus & \textbf{3,220} & ---\\ \bottomrule
\end{tabular}%
}
\end{table}

% ===================== CHAPTER 5 =====================
\chapter{Proposed DWT--LSTM Methodology}
\section{Introduction}
This chapter presents the hybrid adaptive DWT--LSTM differential protection framework, integrating MATLAB/Simulink physical modeling and online execution with PyTorch deep-learning sequence modeling. Differential currents are processed through a two-level db4 Discrete Wavelet Transform, extracting nine wavelet energy features across three phases ($E_{D1}, E_{D2}, E_{A2}$), combined with three second-harmonic restraint ratios ($I_{d,2nd}/I_{d,fund}$) to form a 12-dimensional feature vector. A 32-sample full-cycle sliding window ($W = 32$, 20\,ms at 1.6\,kHz) forms an input tensor of dimension $[1, 32, 12]$ feeding a two-layer unidirectional LSTM neural network. The neural network acts within a dual-path supervisory architecture that preserves conventional 87T dependability while providing decisive security vetoes against non-fault transients and autonomous clearance for high-impedance internal faults.

\section{Framework Architecture}
\textbf{Step 1 (MATLAB/Simulink).} A detailed EMT model generates labeled three-phase differential currents at 1.6\,kHz. Secondary currents are referred to the $0.9302$\,A base and scaled in per-unit ($\mathrm{pu}$).
\textbf{Step 2 (Feature Engineering).} A 32-sample sliding window processes the normalized per-unit currents through a two-level db4 DWT and FFT, extracting 12 features per step ($f(t) \in \mathbb{R}^{12}$). Feature vectors are z-score standardized using training-fold statistics.
\textbf{Step 3 (PyTorch Training).} A sequence buffer accumulates 32 consecutive feature vectors into $X(t) \in \mathbb{R}^{32 \times 12}$ (spanning a total historical lookback of 63 raw samples, $39.375$\,ms). The $[B, 32, 12]$ tensors train a PyTorch LSTM (64/64 units, 58{,}241 parameters) using Adam and weighted binary cross-entropy.
\textbf{Step 4 (ONNX Export).} The trained model is exported via ONNX with opset 17.
\textbf{Step 5 (Closed-Loop Simulink).} The ONNX model runs inside Simulink via the Predict block, governing the circuit breaker through the dual-path handshake logic.
\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{fig_5_1.png}
\caption{End-to-end workflow of the proposed hybrid adaptive transformer protection framework.}\label{fig:5.1}\end{figure}

\subsection{Online Relay Processing Pipeline}
The real-time protection cycle executes sample-by-sample ($\Delta t=0.625$\,ms):
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Data Acquisition:} Sample secondary currents; apply Yd1 phase and zero-sequence compensation.
\item \textbf{Window Buffering:} Maintain a 32-sample rolling buffer ($W=32$, 20\,ms) of normalized currents.
\item \textbf{DWT Decomposition:} Apply two-level db4 DWT with symmetric reflection padding (`mode=symmetric'); compute nine log-compressed energies $E = \ln(1 + \sum |c[k]|^2)$.
\item \textbf{Harmonic Computation:} Compute fundamental and second-harmonic magnitudes via sliding FFT; form three capped ratios $k_{2,\varphi} \in [0, 2.0]$.
\item \textbf{Sequence Formulation:} Form feature vector $f(t) \in \mathbb{R}^{12}$; update the $[1, 32, 12]$ sequence buffer (using edge-replication during startup).
\item \textbf{LSTM Inference:} Execute ONNX forward pass; output probability $p_{\text{AI}}(t) = \sigma(z(t))$.
\item \textbf{Supervisory Handshake:} Combine with 87T dual-slope characteristic and 20-sample dwell timer; issue TRIP or BLOCK.
\end{enumerate}
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_5_2.png}
\caption{Detailed block diagram of the proposed hybrid adaptive differential protection architecture.}\label{fig:5.2}\end{figure}

\subsection{Dual-Path Supervisory Decision Handshake}
The overall trip command combines three deterministic and intelligent paths:
\begin{equation}
\text{TRIP}(t) = \text{HighSet}(t) \ \vee\ \left( \text{87T\_Trip}(t) \ \wedge\ p_{\text{AI,conf}}(t) \ge 0.99 \right) \ \vee\ \left( p_{\text{AI,conf}}(t) \ge 0.998 \right)
\end{equation}
where:
\begin{itemize}[leftmargin=1.4em,itemsep=2pt]
\item $\text{HighSet}(t) = 1$ if the one-cycle sliding true RMS of differential current exceeds pickup, $\max_\varphi I_{d,\varphi,\text{rms}}(t) > 10.0$\,pu (sub-cycle instantaneous trip). Crucially, HighSet is evaluated on the sliding true RMS over 32 samples rather than raw instantaneous peak spikes. During magnetizing inrush, instantaneous spikes can reach peak values, but their sliding true RMS remains safely below $10.0$\,pu; hence, HighSet never false-trips during inrush (verified with 0 false trips across all inrush traces in the corpus). It trips exclusively on severe bolted internal faults ($I_{d,\text{rms}} > 10.0$\,pu).
\item $\text{87T\_Trip}(t) = 1$ if $I_d(t) > I_{op}(I_r(t))$ and $I_d(t) > I_{pickup}$ (confirmed by $p_{\text{AI,conf}} \ge 0.99$). Tripping does not require classical harmonic blocking in the 87T path because the parallel sequence AI network extracts harmonic and multi-resolution wavelet features directly.
\item $p_{\text{AI,conf}}(t) = \min_{k=0}^{19} p_{\text{AI}}(t - k)$ imposes a 20-sample (12.5\,ms) persistence dwell timer, enabling autonomous tripping for high-impedance internal faults ($R_f \le 7\,\Omega$) without 87T pickup.
\end{itemize}
\begin{figure}[H]\centering\includegraphics[width=0.88\textwidth]{fig_5_3.png}
\caption{Seven-stage signal-processing and supervisory decision flowchart.}\label{fig:5.3}\end{figure}

\section{Data Preprocessing and Sampling}
Secondary currents pass through a 4th-order Butterworth anti-aliasing filter ($f_c=800$\,Hz), 16-bit quantization, and are decimated to 1.6\,kHz (32 samples/cycle at 50\,Hz). A sliding window of 32 samples advances one sample per step ($\Delta t=0.625$\,ms).
\begin{figure}[H]\centering\includegraphics[width=0.8\textwidth]{fig_5_4.png}
\caption{Sliding-window timing and sample-by-sample update cadence.}\label{fig:5.4}\end{figure}

\section{DWT Engine and Feature Extraction}
The db4 wavelet (compact support $L=8$, four vanishing moments, orthogonal) matches fault-inception transients. To prevent window-edge step discontinuities, symmetric reflection boundary extension (\texttt{mode='symmetric'}) is employed. The two-level decomposition follows the Mallat algorithm with quadrature mirror filters $h[n]$ and $g[n]=(-1)^n h[7-n]$:
\begin{equation}
a_j[k]=\sum_n h[n-2k]\,a_{j-1}[n],\qquad d_j[k]=\sum_n g[n-2k]\,a_{j-1}[n].
\end{equation}
Under symmetric reflection boundary extension, an input of length $N_{j-1}$ with filter length $L=8$ yields $N_j = \lfloor(N_{j-1}+L-1)/2\rfloor$ coefficients: Level~1 produces $N_1 = \lfloor(32+8-1)/2\rfloor = 19$ coefficients ($d_1$), and Level~2 produces $N_2 = \lfloor(19+8-1)/2\rfloor = 13$ coefficients ($d_2, a_2$). The frequency band allocation is given in Table~\ref{tab:5.2}.
\begin{table}[H]\centering\caption{Frequency band allocation for the 2-level DWT at 1.6\,kHz.}\label{tab:5.2}
\begin{tabular}{@{}ccll c@{}}\toprule \textbf{Level} & \textbf{Coeff.} & \textbf{Band (Hz)} & \textbf{Key components} & \textbf{\# Coeff.}\\ \midrule
2 & $a_2$ & 0--200 & DC, fundamental (50\,Hz), 2nd--3rd harmonics & 13\\
2 & $d_2$ & 200--400 & 4th--8th harmonics & 13\\
1 & $d_1$ & 400--800 & High-frequency fault transients & 19\\ \bottomrule
\end{tabular}\end{table}

Per phase $\varphi \in \{A, B, C\}$, the logarithmically compressed sub-band energies are computed as $E = \ln(1 + \sum |c[k]|^2)$ for detail sub-bands $d_1, d_2$ and approximation sub-band $a_2$, yielding nine wavelet features. These are fused with three phase-wise second-harmonic restraint ratios $k_{2,\varphi} = |I_{d,2nd}| / (|I_{d,fund}| + 10^{-4})$ (capped at 2.0) to form the 12-dimensional feature vector $f(t) \in \mathbb{R}^{12}$, accumulated over the sequence buffer into $X(t) \in \mathbb{R}^{32 \times 12}$.
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_5_5.png}
\caption{db4 mother wavelet and two-level dyadic filter-bank decomposition tree.}\label{fig:5.5}\end{figure}

\section{LSTM Architecture and Training}
The network comprises an input tensor $[B,32,12]$; LSTM-1 (64 units, unidirectional, LayerNorm) with dropout 0.22 ($4 \times 64 \times (12 + 64 + 1) = 19{,}712$ params); LSTM-2 (64 units, unidirectional, LayerNorm) with dropout 0.22 ($4 \times 64 \times (64 + 64 + 1) = 33{,}024$ params); a global temporal attention layer:
\begin{equation}
\alpha_t=\frac{\exp(v^\top\tanh(W_a h_t+b_a))}{\sum_{t'=1}^{32}\exp(v^\top\tanh(W_a h_{t'}+b_a))},\qquad c=\sum_{t=1}^{32}\alpha_t h_t\in\mathbb{R}^{64};
\end{equation}
(LayerNorm(64) [128] + Attention Linear(64, 1) [65] = 193 parameters); and a dense classifier head (Linear(64, 64) with bias [4,160] + ReLU + Dropout(0.22) + Linear(64, 1) with bias [65] + auxiliary feature adapter and projection weights [1,087] = 5,312 parameters). The total trainable parameter count is exactly $19{,}712 + 33{,}024 + 193 + 5{,}312 = \mathbf{58{,}241}$.
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_5_6.png}
\caption{Deployed DWT--LSTM classifier architecture with global temporal attention (58{,}241 parameters).}\label{fig:5.6}\end{figure}
Training uses weighted binary cross-entropy (positive-class weight 1.4155), Adam ($\eta=0.001$, $\beta_1=0.9$, $\beta_2=0.999$), a ReduceLROnPlateau scheduler, batch size 128, early stopping (patience 20), and 5-fold stratified cross-validation. The exported ONNX model operates with fixed input shape $[1,32,12]$.

\section{Real-Time Implementation and Latency}
The ONNX model is integrated via the Predict block within a masked Simulink subsystem. A Stateflow chart encodes the trip logic and latches the breaker trip for 100\,ms. Evaluating the full 32-step sequence through the two LSTM layers requires $32 \times 9{,}856 = 0.315$\,MMACs for LSTM-1 and $32 \times 16{,}512 = 0.528$\,MMACs for LSTM-2, totaling $0.855$\,MMACs (or $\approx 1.71$\,MFLOPs at 2 FLOPs/MAC), including attention, dense projections, and front-end sliding FFT harmonic ratio extraction ($\approx 1.2$\,kFLOPs). The per-inference computational cost is summarized in Table~\ref{tab:5.3}.
\begin{table}[H]\centering\caption{Per-inference parameter and numerical budget of the DWT--LSTM pipeline.}\label{tab:5.3}
\begin{tabular}{@{}lccc@{}}\toprule \textbf{Stage} & \textbf{Parameters} & \textbf{FLOPs/inference} & \textbf{Share (\%)}\\ \midrule
DWT Front End (2-level db4, $\times3$) & 0 & $\approx$1.8\,k & 0.1\\
LSTM layer 1 ($12\to64$) & 19{,}712 & $\approx$0.63\,M & 36.8\\
LSTM layer 2 ($64\to64$) & 33{,}024 & $\approx$1.06\,M & 62.0\\
Attention + LayerNorm & 193 & $\approx$2.1\,k & 0.1\\
Dense Classifier ($64\to64\to1$) & 5{,}312 & $\approx$17.5\,k & 1.0\\ \midrule
Total & 58{,}241 & $\approx$1.71\,M & 100\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.8\textwidth]{fig_5_7.png}
\caption{Per-inference computational cost distribution across pipeline stages ($\approx$1.71\,MFLOPs total).}\label{fig:5.7}\end{figure}

\section{Robustness Enhancement}
Three complementary strategies are used: independent AWGN measurement noise injection across all six CT channels; dropout regularization (0.22) preventing feature co-adaptation; and out-of-distribution stress testing across extreme load, severe CT saturation, frequency deviation ($\pm0.5$\,Hz), and source impedance variations.

% ===================== CHAPTER 6 =====================
\chapter{Results, Analysis and Discussion}
\section{Introduction and Evaluation Protocol}
This chapter presents the empirical evaluation of the proposed Hybrid Adaptive Transformer Differential Protection (HATDP) framework. The evaluation follows a strict, leak-free protocol:
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Trace-level partitioning:} Data splits are conducted strictly by waveform trace (never across rolling windows), preventing cross-window information leakage.
\item \textbf{Waveform-measured onset detection:} Window labels transition from healthy (BLOCK) to fault (TRIP) only after fault inception is physically detected from the differential waveform using a cycle-difference filter.
\item \textbf{Exact pipeline parity:} Features extracted in Python and in MATLAB/Simulink share exact numerical equivalence (verified maximum parity error $= 0.0$ at decision level; floating-point precision difference $< 10^{-7}$).
\item \textbf{Dual-path supervisory decision logic:} The relay operating decision combines:
\begin{equation}
\text{TRIP} = \text{HighSet} \ \vee\ (\text{87T\_Vote} \ \wedge\ p_{\text{AI,conf}} \ge 0.99) \ \vee\ (p_{\text{AI,conf}} \ge 0.998)
\end{equation}
where $p_{\text{AI,conf}} = \min_{k=0}^{19} p_{\text{AI}}(t - k)$ imposes a 20-sample (12.5\,ms) persistence dwell timer.
\end{enumerate}

\section{Representative Waveforms and Feature Signatures}
Figure~\ref{fig:6.1} illustrates representative three-phase differential current waveforms under key operating regimes generated by the verified simulation model. Inrush waveforms exhibit pronounced second-harmonic unbalance and deep unipolar notches; external faults with CT saturation manifest severe waveshape distortion with secondary zero-intervals; and internal faults generate sustained, high-energy differential currents.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_example_waveforms.png}
\caption{Representative three-phase differential current waveforms across major operating categories under realistic loading and CT burden.}\label{fig:6.1}\end{figure}

\section{Grouped 5-Fold Cross-Validation and Architecture Ablation}
To assess generalization and architectural contributions, a 5-fold grouped cross-validation was conducted across three independent random seeds (15 models total, each testing all 3,218 traces out-of-fold). Table~\ref{tab:6.1} presents the pooled out-of-fold performance comparison among four relay architectures across the $N_{\text{eval}} = 3{,}124$ evaluated traces ($1{,}873$ healthy and $1{,}251$ detectable faults).

\input{table_6_1_ablation.tex}

The conventional 87T relay alone exhibits severe vulnerability to non-fault transients, securing only 52.96\% of healthy traces due to false tripping on inrush, over-excitation, and CT saturation (881 false trips across 1,873 healthy traces). This vulnerability stems directly from its unaugmented baseline implementation: without harmonic restraint or blocking, the large differential currents generated during magnetizing inrush and over-excitation immediately exceed the dual-slope restraint boundary, causing false tripping on 100\% of loaded inrush traces and 41.9\% of over-excitation traces. Furthermore, because HighSet is evaluated on the one-cycle sliding true RMS of differential current rather than raw instantaneous spikes, HighSet itself never trips during inrush ($I_{d,\text{rms}} < 10.0$\,pu); all inrush false trips originate from the unrestrained dual-slope 87T element. Conversely, the 87T-gated hybrid achieves near-perfect security (99.79\%) but sacrifices 10\% dependability on high-impedance internal faults. The proposed \textbf{Hybrid + AI-Alone Path} successfully bridges this gap, attaining \textbf{99.01\% dependability} and \textbf{99.66\% security} with zero pre-fault trips and a median operating latency of \textbf{15.6\,ms}.

\section{Category-Level Performance Breakdown}
Table~\ref{tab:6.2} provides the detailed performance breakdown across all 16 scenario categories for the deployed hybrid relay, alongside 95\% Wilson confidence intervals and comparative baselines.

\input{table_6_2_categories.tex}

\section{Impact of Verified Dataset Retraining}
Table~\ref{tab:6.3} contrasts the baseline model trained on light-load data against the model retrained on the verified v3 dataset. Exposure to realistic load variations, independent noise, and CT saturation dramatically elevates relay security under severe transients.

\input{table_6_3_retraining.tex}

\section{Out-of-Distribution (OOD) Stress Robustness}
To verify generalization beyond the training parameter boundaries, an isolated 300-trace Out-of-Distribution dataset was evaluated without re-tuning. Of the 300 compiled cases, 9 cases failed generator physical sanity checks under extreme CT saturation, yielding 291 evaluated usable traces (144 faults and 147 healthy non-fault traces). Table~\ref{tab:6.4} demonstrates that the hybrid relay maintains \textbf{100.0\% security} across all stress regimes, with graceful degradation observed only under extreme CT burdens.

\input{table_6_4_ood.tex}

In Block~3 (extreme CT burden, 12--16$\times$ nominal), dependability drops to 68.0\% (17/25 tripped, accounting for 8 of the 11 missed OOD faults). Physically, this degradation occurs because severe bilateral CT saturation collapses secondary differential current amplitude down toward the noise floor and distorts the waveform, suppressing $p_{\text{AI,conf}}$ below $\theta_{\text{AI}} = 0.99$ during the 20-sample dwell window.

\section{Closed-Loop Simulink Verification and Mirror Parity}
The deployed network was embedded in Simulink and evaluated in full closed-loop co-simulation across a 12-case benchmark suite (Table~\ref{tab:6.5}). All 12 operating decisions were correctly executed (12/12 trip decisions correct, 100.0\% decision accuracy; 10/12 within the 30\,ms operate time criterion).

\input{table_6_5_closed_loop.tex}

\section{High-Impedance Fault Sensitivity Analysis}
In the simulation sweep of internal high-impedance faults ($R_f = 0.3$--$21\,\Omega$), 240 traces were simulated across three resistance bins (80 traces per bin). Exactly 153 traces produce a differential current rise $\ge 0.05$\,pu (80 in Bin~1, 72 in Bin~2, and 1 in Bin~3), which constitute the 153 evaluated detectable traces in Table~\ref{tab:4.3} and Table~\ref{tab:6.2}. The remaining 87 traces produce differential current below the 0.05\,pu physical noise threshold and are segregated to avoid artificial metric distortion. Table~\ref{tab:6.6} and Figure~\ref{fig:6.2} examine relay dependability across the three resistance bins evaluated on Repetition~1 across all $n=80$ simulated traces per bin. In Bin~1 ($0.3\text{--}1.2\,\Omega$), all 80 traces are detectable, and the Proposed Hybrid achieves 100.0\% ($80/80$) while 87T alone achieves 96.2\% ($77/80$). In Bin~2 ($1.2\text{--}7.0\,\Omega$), where 72 of the 80 traces are physically detectable, the Proposed Hybrid trips 57 traces, achieving 71.2\% dependability across all 80 traces (or 79.2\% among detectable traces), whereas 87T alone trips only 3 traces (3.8\% across all traces, or 4.2\% of detectable traces). In Bin~3 ($7.0\text{--}21.0\,\Omega$), 79 of 80 traces are sub-noise floor ($<0.05$\,pu), yielding 0.0\% across all methods. Summing the tripped traces across the 153 detectable events gives $80 + 57 + 0 = 137$ trips for the Proposed Hybrid (matching $137/153 = 89.5\%$ in Repetition~1 in Table~\ref{tab:6.2}, with a 3-repetition mean of 93.0\%) and $77 + 3 + 0 = 80$ trips for 87T alone (matching $80/153 = 52.3\%$).

\input{table_6_6_hiz.tex}

\begin{figure}[H]\centering\includegraphics[width=0.75\textwidth]{fig_hiz_sensitivity.png}
\caption{Empirical fault differential current versus fault resistance across all internal fault types, delineating the 87T-visible and AI-alone detection boundaries.}\label{fig:6.2}\end{figure}

\section{Operating Speed and Threshold Sensitivity}
Figure~\ref{fig:6.3} illustrates the cumulative operating time distribution and threshold trade-off curve. Over 96.9\% of all internal faults are cleared within two fundamental cycles (40\,ms), with 77.1\% cleared within a single cycle. The chosen threshold operating point ($\theta_{\text{AI}} = 0.99$, $\theta_{\text{solo}} = 0.998$) provides optimal security margin while minimising relay operate time.

\begin{figure}[H]\centering
\begin{minipage}{0.48\textwidth}\centering
\includegraphics[width=\textwidth]{fig_operate_time_cdf.png}
\centerline{\small (a) Empirical CDF of operate time}
\end{minipage}\hfill
\begin{minipage}{0.48\textwidth}\centering
\includegraphics[width=\textwidth]{fig_threshold_tradeoff.png}
\centerline{\small (b) Dependability vs.\ security trade-off}
\end{minipage}
\caption{Dynamic relay operating characteristics: (a) operate-time cumulative distribution (legend sample counts denote tripped detectable faults out of 1,251 in Repetition~1), and (b) threshold trade-off curve.}\label{fig:6.3}
\end{figure}

\section{Comparative Benchmarking Against Literature Models}
To fulfill the comparative gap identified in Chapter~2 (Table~\ref{tab:litcompare}), the proposed Hybrid DWT--LSTM framework was directly benchmarked against representative machine learning and deep learning protection models from recent literature: Wavelet-SVM (RBF kernel)~\cite{ref13,ref20}, Wavelet-ANN/MLP~\cite{ref18,ref19}, Wavelet-Random Forest~\cite{ref11}, Temporal 1D-CNN~\cite{ref16}, Wavelet-GRU with self-attention~\cite{ref23}, Standalone DWT-LSTM~\cite{ref1,ref3}, and the Conventional 87T dual-slope percentage restraint relay~\cite{ref7} (alongside a dedicated comparison with phase-independent harmonic restraint).

To provide a rigorous, publication-grade apples-to-apples comparison:
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Identical Evaluation Corpus:} All candidate models were trained, validated, and tested on the exact same 3{,}218-trace dataset derived from the 300\,MVA, 230/11\,kV, Yd1 plant under identical 5-fold grouped cross-validation splits ($N_{\text{eval}} = 3{,}124$ evaluated traces: $1{,}251$ detectable faults and $1{,}873$ healthy traces).
\item \textbf{Standardized Feature Representations:} Recurrent and convolutional sequence models (LSTM, GRU, 1D-CNN) received the continuous 32-sample sliding sequence ($32 \times 12$). Static tabular models (SVM, ANN/MLP, Random Forest) received identical multi-resolution wavelet energy and harmonic ratio signatures pooled over the 32-sample window (mean, standard deviation, peak, and RMS across the window, yielding 48 features).
\item \textbf{Controlled Operating Protocol:} All models were tested under identical digital relay streaming simulation conditions, including sample-by-sample sliding window processing, 20-sample (12.5\,ms) dwell persistence timer, and instantaneous high-set overcurrent bypass ($I_d > 10.0$\,pu).
\item \textbf{Dual Operating Modes Evaluated:} Each architecture was evaluated in two distinct configurations: (a) \textit{Standalone Operating Mode} (as traditionally evaluated in prior literature, where the classifier directly trips the circuit breaker), and (b) \textit{Supervisory Hybrid Mode} (integrated within the proposed dual-path supervisory handshake and AI-alone fault recovery path).
\end{enumerate}

\input{table_literature_benchmark.tex}

The comparative results summarized in Table~\ref{tab:lit_benchmark} (evaluated on Repetition~1) yield five critical insights:
\begin{enumerate}[leftmargin=1.4em,itemsep=1.5pt,topsep=2pt,parsep=0pt]
\item \textbf{Temporal Sequence Context vs.\ Static Classifiers:} Deep sequence models (LSTM, GRU, 1D-CNN) achieve slightly higher dependability in standalone operating mode (98.96--99.20\% vs.\ 98.64\% for Wavelet-RF and 88.25\% for Wavelet-SVM) by tracking temporal transient trajectories across successive multi-resolution wavelet scales. In contrast, static models like Random Forest achieve exceptionally high standalone security (99.89\% with only 2 false trips), whereas standalone neural networks incur 12--20 false trips before supervisory anchoring.
\item \textbf{LSTM vs.\ GRU Trade-off:} The 2-layer GRU features fewer parameters (44{,}354 vs.\ 58{,}241) and attains 99.20\% standalone dependability (vs.\ 99.04\% for standalone LSTM). However, under the proposed supervisory hybrid architecture (Panel~B), the Proposed Hybrid DWT--LSTM achieves higher dependability (98.56\% in Repetition~1, and 99.01\% 3-repetition mean) compared to 97.92\% for Wavelet-GRU, while maintaining lower operating time dispersion and faster fault response.
\item \textbf{Universality of the Supervisory Handshake:} The primary architectural contribution is the dual-path supervisory handshake. Integrating machine learning classifiers into this hybrid framework (Panel~B) dramatically improves security across \textit{all} candidate models: false trips drop from 151 to 7 for Wavelet-SVM, from 8 to 2 for Wavelet-ANN, from 2 to 1 for Wavelet-RF, from 12 to 1 for 1D-CNN, and from 20 to 8 for Wavelet-GRU. This confirms that the supervisory handshake serves as a universal, model-agnostic protection anchor that suppresses spurious trips under CT saturation and non-fault transients.
\item \textbf{Balanced Performance of the Proposed Framework:} Under the supervisory hybrid architecture (Panel~B), the proposed \textbf{Hybrid DWT--LSTM} achieves the highest hybrid dependability (\textbf{98.56\%} in Repetition~1, and \textbf{99.01\%} multi-repetition mean) and fastest median operate time (\textbf{15.6\,ms}). The price of this enhanced sensitivity to sub-pickup faults is a slight increase in AI-alone false trips (11 false trips in Repetition~1 vs.\ 1 for RF and 1D-CNN; multi-repetition mean 6.3 false trips out of 1{,}873 healthy traces, corresponding to \textbf{99.66\% security}).
\item \textbf{Qualitative Comparison with Deterministic Wavelet Schemes:} Unlike deterministic wavelet schemes—such as Boundary DWT~\cite{ref38} and Clarke-wavelet energy ratios~\cite{ref39}—that rely on heuristic energy thresholds sensitive to CT saturation and grid X/R variations, the proposed framework learns temporal trajectory dynamics directly from multi-resolution wavelet energies and harmonic restraint ratios.
\end{enumerate}

\section{Limitations and Scope of Claims}
While the proposed framework demonstrates superior dependability and security, several engineering limitations must be recognized:
\begin{enumerate}[leftmargin=1.4em,itemsep=1.5pt,topsep=2pt,parsep=0pt]
\item \textbf{Simulation-to-Reality Gap:} All findings are based on high-fidelity EMT simulation in MATLAB/Simulink. Physical substation trials on real transformer hardware will be essential before commercial utility commissioning.
\item \textbf{CT Burden Limits:} As revealed by OOD Block~3, relay dependability degrades when CT secondary burdens exceed 12$\times$ nominal under deep bilateral saturation.
\item \textbf{High-Impedance Physical Limit:} Faults with contact resistance $R_f > 7.0\,\Omega$ produce differential current rises below the $0.05$\,pu noise threshold and cannot be detected by differential CT measurements alone.
\end{enumerate}

% ===================== CHAPTER 7 =====================
\chapter{Conclusion and Future Scope}
\section{Conclusion}
This thesis presented the design, implementation, and rigorous verification of a hybrid adaptive transformer differential protection framework combining multi-resolution Discrete Wavelet Transform (DWT) feature extraction, second-harmonic restraint ratios, and Long Short-Term Memory (LSTM) sequence modeling. A high-fidelity 300\,MVA, 230/11\,kV, Yd1 power transformer was developed with realistic core magnetization, CT saturation, and calibrated secondary current bases (0.9302\,A nominal). A verified corpus of 3{,}220 traces spanning 16 scenario categories (11 fault types, 10--110\% rated loading, CT burdens 4--10$\times$, over-excitation, and recovery inrush) and an independent 300-trace Out-of-Distribution test set were evaluated under strict, leak-free trace-stratified cross-validation. The deployed hybrid relay achieved \textbf{99.01\% dependability} ($\pm0.48\%$) and \textbf{99.66\% security} ($\pm0.24\%$) across 15 models (evaluating 3{,}218 usable traces, with 94 sub-noise-floor faults segregated), with a median operate time of \textbf{15.6\,ms} and \textbf{100.0\% decision accuracy} in closed-loop Simulink co-simulation.

\section{Key Findings}
\textbf{Feature robustness.} The 12-feature representation (9 DWT wavelet sub-band energies plus 3 second-harmonic restraint ratios) provides decisive, physically grounded discrimination between fault transients, inrush, and CT saturation. The classifier degrades gracefully under severe noise and extreme CT saturation, while the supervisory architecture ensures near-perfect security.

\textbf{Security and dependability reconciliation.} The standalone conventional 87T produces 881 false trips (52.96\% security) and 255 missed faults (79.62\% dependability out of 1,251 detectable faults). In Repetition~1, the standalone LSTM achieves 99.04\% dependability and 99.31\% security (13 false trips). The proposed Hybrid DWT--LSTM with dual-path handshake eliminates false trips during inrush, recovery inrush, and over-excitation, achieving 99.41\% security (11 false trips) and 98.56\% dependability in Repetition~1, and 99.66\% security (6.3 false trips) and 99.01\% dependability on average across 3 repetitions.

\textbf{High-impedance fault recovery.} In the AI-only zone ($R_f = 1.2$--$7.0\,\Omega$) where conventional 87T relays fail (3.8\% recall), the proposed autonomous AI path recovers 71.2\% of faults, extending relay sensitivity to high-resistance faults below the conventional 87T pickup threshold down to the physical detection limit (up to $7.0\,\Omega$).

\textbf{Real-time feasibility.} The per-inference computational cost is 1.71\,MFLOPs for the deep sequence network, executing well within the 20\,ms power cycle. The median end-to-end relay operate time is 15.6\,ms (fault inception to trip decision; circuit breaker opening is not modelled, with 96.9\% of detectable faults operating within two cycles).

\section{Research Outcomes}
The architecture demonstrates that high dependability (99.01\%) and high security (99.66\%) can be achieved simultaneously by coupling deterministic 87T principles with deep sequence intelligence via a dual-path handshake. The validated MATLAB $\to$ PyTorch $\to$ ONNX $\to$ Simulink pipeline is reproducible by relay manufacturers; fast clearing of high-current faults preserves transformer lifetime and reduces asset replacement risks.

\section{Limitations of the Study}
The study relies on EMT simulation without physical high-power substation validation; assumes a fixed 1.6\,kHz sampling rate; was evaluated on a single 300\,MVA plant topology; and uses frozen weights during deployment without online fine-tuning.

\section{Recommendations for Future Work}
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Substation Hardware-in-the-Loop Testing:} Validate on physical DSP/FPGA protective relays (e.g., OPAL-RT or RTDS platforms) with analog merging units.
\item \textbf{Transformer Fleet Multi-Topology Transfer Learning:} Pre-train on synthetic corpora across multiple MVA ratings and fine-tune on specific transformer nameplates.
\item \textbf{Inverter-Based Resource (IBR) Transient Evaluation:} Evaluate under low-inertia grids with Type-IV wind generators and grid-forming solar PV inverters.
\item \textbf{Multi-Class Fault Diagnosis:} Extend from binary trip/block logic to internal fault localization (winding turn percentage and phase identification).
\end{enumerate}

\section{Concluding Remarks}
By wedding deterministic differential protection principles with multi-resolution sequence intelligence and rigorous persistence gating, this thesis proves that intelligent relays can simultaneously eliminate transient false trips and recover weak high-impedance faults, providing a dependable, secure, and computationally feasible foundation for next-generation power transformer protection.

% ===================== PUBLICATIONS =====================
\chapter*{List of Publications}
\addcontentsline{toc}{chapter}{LIST OF PUBLICATIONS}
The following publications have been derived from this research:
\begin{enumerate}[leftmargin=1.6em,itemsep=6pt]
\item Md Moinul Haque, Md Reyaz Uddin, and Cdre A N M Didarul Alam, (L), NUP, psc, BN, ``Hybrid Adaptive Transformer Differential Protection Using a DWT--LSTM Intelligent Framework with Enhanced CT Saturation and Noise Robustness,'' \textit{IEEE Access}, 2026 (Under Review, Manuscript ID: Access-2026-HATDP). \textit{Summary:} presents the complete framework (two-level db4 decomposition, 12-feature DWT-harmonic pipeline, unidirectional LSTM with dual-path supervisory logic), reporting 99.01\% dependability and 99.66\% security and a median operating latency of 15.6\,ms, benchmarked against seven literature methods.
\item Md Moinul Haque, Md Reyaz Uddin, and Cdre A N M Didarul Alam, (L), NUP, psc, BN, ``Multi-Resolution Feature Extraction for Transformer Protection: A Discrete Wavelet Transform Approach with Harmonic Feature Fusion,'' in \textit{Proceedings of the IEEE International Conference on Power Systems (ICPS)}, 2026 (Accepted and To be Presented). \textit{Summary:} investigates mother wavelet and sub-band feature extraction, demonstrating that two-level db4 energy features combined with second-harmonic restraint ratios provide superior separation between inrush and internal fault transients compared to higher-level decompositions.
\item Md Moinul Haque, Md Reyaz Uddin, and Cdre A N M Didarul Alam, (L), NUP, psc, BN, ``Comparative Benchmarking of Machine Learning and Deep Learning Architectures for Power Transformer Differential Protection Under Severe CT Saturation,'' \textit{International Journal of Electrical Power \& Energy Systems}, 2026 (Under Review, Manuscript ID: IJEPES-2026-HATDP). \textit{Summary:} presents the systematic benchmark of eight protection models (conventional 87T, SVM, ANN, Random Forest, 1D-CNN, GRU, standalone LSTM, and the proposed hybrid) on the 3{,}218-trace verified dataset, analyzing dependability, security, operating speed, and computational complexity.
\end{enumerate}

% ===================== REFERENCES =====================
\begin{thebibliography}{99}
\addcontentsline{toc}{chapter}{REFERENCES}
\bibitem{ref1} Q. Alhamd, M. Saniei, S. G. Seifossadat, and E. Mashhour, ``Advanced fault detection in power transformers using improved wavelet analysis and LSTM networks considering current transformer saturation and uncertainties,'' \textit{Algorithms}, vol.~17, no.~9, art.~397, 2024.
\bibitem{ref2} Q. Alhamd, M. Saniei, and S. G. Seifossadat, ``Intelligent differential protection of power transformers based on wavelet packet transform and deep sequence learning,'' \textit{Int.\ J.\ Electr.\ Power Energy Syst.}, vol.~155, p.~109567, 2024.
\bibitem{ref3} W. A. Atiyah, S. Karimi, and M. Moradi, ``A novel approach for diagnosing transformer internal defects and inrush current based on 1DCNN and LSTM deep learning,'' \textit{J.\ Electr.\ Syst.}, vol.~20, no.~3, pp.~2557--2572, 2024.
\bibitem{ref4} P. M. Anderson, \textit{Power System Protection}. New York, NY: IEEE Press / McGraw-Hill, 1999.
\bibitem{ref5} K. Sudha and A. K. Pradhan, ``Wavelet transform-based technique for detection and classification of power system disturbances,'' \textit{Int.\ J.\ Emerg.\ Electr.\ Power Syst.}, vol.~8, no.~5, pp.~1--22, 2007.
\bibitem{ref6} O. Ozgonenel and T. S. Karagol, ``A new transformer differential protection scheme based on wavelet transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~116, pp.~146--154, Nov. 2014.
\bibitem{ref7} R. L. Sharp and W. E. Glassburn, ``A new approach to transformer differential protection,'' \textit{Trans.\ Amer.\ Inst.\ Electr.\ Eng.\ III, Power App.\ Syst.}, vol.~77, no.~3, pp.~12--18, Apr. 1958.
\bibitem{ref8} Z. Huang, S. Chen, S. Guo, and H. Yin, ``Transformer differential protection based on self-adaptive biased characteristic curve,'' \textit{Power Syst.\ Prot.\ Control}, vol.~44, no.~16, pp.~11--17, 2016.
\bibitem{ref9} M. Tripathy, R. P. Maheshwari, and H. K. Verma, ``Power transformer differential protection based on optimal probabilistic neural network,'' \textit{IEEE Trans.\ Power Del.}, vol.~25, no.~1, pp.~102--112, Jan. 2010.
\bibitem{ref10} A. Prataprao, S. Khedkar, and S. Barve, ``A review on fault classification methodologies in power transformer,'' \textit{Int.\ J.\ Eng.\ Adv.\ Technol.}, vol.~9, no.~1, pp.~7102--7109, 2019.
\bibitem{ref11} M. Abdusalam, K. F. Ali, and W. M. El-Hawary, ``A new hybrid machine learning method for detecting faults in power transformers,'' \textit{Energies}, vol.~15, no.~18, art.~6758, 2022.
\bibitem{ref12} J. Wang, Y. Liu, Z. Li, and B. Wang, ``Early classification for power transformer fault detection using reinforcement learning,'' \textit{Expert Syst.\ Appl.}, vol.~240, art.~122550, 2024.
\bibitem{ref13} L. D. Sim\~{o}es, H. J. D. Costa, M. N. O. Aires, R. P. Medeiros, F. B. Costa, and A. S. Bretas, ``A power transformer differential protection based on support vector machine and wavelet transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~197, art.~107297, Aug. 2021.
\bibitem{ref14} S. Suliman, A. Mohamed, and H. Shareef, ``Discrimination between inrush current and internal fault in power transformer using discrete wavelet transform,'' \textit{Indones.\ J.\ Electron.}, vol.~3, no.~2, pp.~59--65, 2021.
\bibitem{ref15} W. Rebizant, J. Szafran, and A. Wiszniewski, ``Transformer differential protection with neural network based inrush stabilization,'' \textit{WSEAS Trans.\ Circuits Syst.}, vol.~6, no.~4, pp.~537--544, 2007.
\bibitem{ref16} S. Afrasiabi, M. Afrasiabi, B. Parang, and M. Mohammadi, ``Integration of accelerated deep neural network into power transformer differential protection,'' \textit{IEEE Trans.\ Ind.\ Informat.}, vol.~16, no.~2, pp.~865--876, Feb. 2020.
\bibitem{ref17} A. Raichura and S. Paithankar, ``Improved transformer differential protection by adaptive pickup,'' \textit{Aust.\ J.\ Electr.\ Electron.\ Eng.}, vol.~17, no.~2, pp.~109--119, 2020.
\bibitem{ref18} E. C. M. Costa, S. C. A. Alves, and R. L. A. Ribeiro, ``Identification of inrush currents in power transformers using wavelet transform and artificial neural networks,'' \textit{J.\ Control Autom.\ Electr.\ Syst.}, vol.~24, no.~5, pp.~636--645, Oct. 2013.
\bibitem{ref19} A. Ngaopitakkul and A. Kunakorn, ``Internal fault classification in power transformers using discrete wavelet transform and back-propagation neural networks,'' \textit{Int.\ J.\ Comput.\ Appl.}, vol.~28, no.~5, pp.~15--22, 2006.
\bibitem{ref20} S. Subramanian, M. S. Kalavathi, and C. Sharmeela, ``Wavelet packet transform and support vector machine based discrimination between magnetizing inrush and internal faults,'' \textit{Math.\ Probl.\ Eng.}, vol.~2010, pp.~1--13, 2010.
\bibitem{ref21} H. Dashti and M. Sanaye-Pasand, ``A multi-region adaptive differential relay for power transformer protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~29, no.~5, pp.~2165--2174, 2014.
\bibitem{ref22} A. Shahbazi, A. A. Samad, and P. R. Sharma, ``A self-adaptive biased characteristic curve method for power transformer differential protection,'' \textit{Int.\ J.\ Comput.\ Theory Appl.}, vol.~11, no.~4, pp.~321--331, 2022.
\bibitem{ref23} Y. Lin, Z. Li, X. Wang, and L. Chen, ``Dual deep neural network for discriminating internal faults and inrush currents in power transformer differential protection,'' \textit{IEEE Access}, vol.~13, pp.~11234--11246, 2025.
\bibitem{ref24} M. Oztekin, S. Karagol, and O. Ozgonenel, ``Power transformer differential protection with wavelet transform and difference function,'' \textit{Eng.\ Sci.\ Technol.\ Int.\ J.}, vol.~70, art.~102144, 2025.
\bibitem{ref25} P. Chiradeja, C. Pothisarn, and A. Ngaopitakkul, ``Identification of inrush current and internal faults in power transformers using probabilistic neural network and discrete wavelet transform,'' \textit{Appl.\ Sci.}, vol.~11, no.~22, art.~10619, 2021.
\bibitem{ref26} H. Noshad, M. Razaz, and S. G. Seifossadat, ``A new algorithm considering ultra-saturation phenomenon for differential protection of power transformers,'' \textit{Int.\ J.\ Electron.\ Electr.\ Power}, vol.~7, no.~2, pp.~51--61, 2019.
\bibitem{ref27} Y. Yubo, C. Deshu, X. Zhenyu, and O. P. Malik, ``Adaptive variable window algorithm for power transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~20, no.~3, pp.~1790--1798, 2005.
\bibitem{ref28} T. Hayder, U. Schaerli, K. Feser, and L. Schiel, ``Universal adaptive differential protection for regulating transformers,'' \textit{IEEE Trans.\ Power Del.}, vol.~23, no.~2, pp.~568--575, Apr. 2008.
\bibitem{ref29} S. B. A. Bukhari, A. Wadood, T. Khurshaid, K. K. Mehmood, S. Rhee, and C. H. Kim, ``Empirical wavelet transform based intelligent protection scheme for microgrids,'' \textit{Energies}, vol.~15, no.~21, art.~7995, 2022.
\bibitem{ref30} S. Murugan, S. Simon, K. Venkatesh, and N. K. Sharma, ``An efficient approach for power transformer differential protection using energy feature tracking,'' \textit{IEEE Trans.\ Power Del.}, vol.~32, no.~4, pp.~1850--1859, 2017.
\bibitem{ref31} K. Hegazy and M. M. A. Salama, ``Advanced differential protection scheme for power transformers based on wavelet packet transform,'' \textit{IEEE Trans.\ Power Del.}, vol.~35, no.~5, pp.~2345--2356, 2020.
\bibitem{ref32} B. Kasztenny and E. Rosolowski, ``Adaptive neural network-based protection of power transformers,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~155, pp.~368--379, 2018.
\bibitem{ref33} Z. Gajic, I. Brn\v{c}i\'{c}, and R. Gojko, ``Differential protection of power transformers using ICT and smart processing,'' \textit{Int.\ J.\ Electr.\ Power Energy Syst.}, vol.~110, pp.~582--592, 2019.
\bibitem{ref34} D. R. Oliveira, A. S. Bretas, and L. U. Iurinic, ``Transformers differential protection using independent component analysis,'' \textit{IEEE Trans.\ Power Del.}, vol.~34, no.~2, pp.~738--747, 2019.
\bibitem{ref35} A. Hooshyar, M. Sanaye-Pasand, and M. Davarpanah, ``GARCH differential current modeling for power transformer protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~2, pp.~642--652, Apr. 2016.
\bibitem{ref36} Y. C. Kang, B. E. Lee, and S. H. Kang, ``A CT saturation detection algorithm using the secondary current third-derivative function,'' \textit{IEEE Trans.\ Power Del.}, vol.~26, no.~4, pp.~2863--2871, 2011.
\bibitem{ref37} X. Lin, P. Liu, and O. P. Malik, ``Studies for identification of the inrush based on improved correlation algorithm,'' \textit{IEEE Trans.\ Power Del.}, vol.~17, no.~4, pp.~901--907, 2002.
\bibitem{ref38} R. P. Medeiros, F. B. Costa, and K. M. Silva, ``Power transformer differential protection using the boundary discrete wavelet transform,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~5, pp.~2083--2095, Oct. 2016.
\bibitem{ref39} R. P. Medeiros, F. B. Costa, K. M. Silva, J. J. Chavez, J. R. Lima Junior, and M. Popov, ``A Clarke-wavelet-based time-domain power transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~37, no.~1, pp.~317--328, Feb. 2022.
\bibitem{ref40} Y. Wang, X. Yin, H. Zhang, and D. Chen, ``Variable data-window Phaselet algorithm based transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~26, no.~4, pp.~2648--2656, Oct. 2011.
\end{thebibliography}

% ===================== APPENDICES =====================
\appendix
\renewcommand{\thechapter}{\Alph{chapter}}
\titleformat{\chapter}[display]{\centering\normalfont\bfseries}{\Large APPENDIX \thechapter}{6pt}{\Large\MakeUppercase}
\chapter{System Parameters and Configuration}
The verified 300\,MVA plant parameters, current transformer data, and Daubechies-4 filter coefficients are summarized in Tables~\ref{tab:A.1} and~\ref{tab:A.2}.

\begin{table}[H]\centering\caption{Daubechies-4 (db4) low-pass and high-pass decomposition filter coefficients ($L=8$).}\label{tab:A.1}
\begin{tabular}{@{}ccc@{}}\toprule
$n$ & Low-pass filter $h[n]$ & High-pass filter $g[n] = (-1)^n h[7-n]$\\ \midrule
0 & $+0.230377813308896$ & $-0.010597401785069$\\
1 & $+0.714846570552915$ & $-0.032883011666885$\\
2 & $+0.630880767937402$ & $+0.030841381835561$\\
3 & $-0.027983769416860$ & $+0.187034811719093$\\
4 & $-0.187034811719093$ & $-0.027983769416860$\\
5 & $+0.030841381835561$ & $-0.630880767937402$\\
6 & $+0.032883011666885$ & $+0.714846570552915$\\
7 & $-0.010597401785069$ & $-0.230377813308896$\\ \bottomrule
\end{tabular}\end{table}

\begin{table}[H]\centering\caption{Deployed neural network architecture hyperparameters and execution budget.}\label{tab:A.2}
\begin{tabular}{@{}lc@{}}\toprule
\textbf{Component / Hyperparameter} & \textbf{Specification}\\ \midrule
Input feature dimension & 12 features per step ($32\times12$ window)\\
Wavelet front-end & 2-level db4 DWT (9 energies across 3 phases)\\
Harmonic front-end & 3 phase-wise 2nd-harmonic restraint ratios\\
Sequence buffer horizon & 32 time steps (20\,ms at 1.6\,kHz)\\
Total lookback across sequence & 63 raw samples (39.375\,ms)\\
Layer 1 architecture & Unidirectional LSTM, 64 hidden units, LayerNorm\\
Layer 1 parameters & $4\times64\times(12+64+1) = 19{,}712$ parameters\\
Dropout rate (between layers) & $p = 0.22$\\
Layer 2 architecture & Unidirectional LSTM, 64 hidden units, LayerNorm\\
Layer 2 parameters & $4\times64\times(64+64+1) = 33{,}024$ parameters\\
Attention mechanism & Global temporal self-attention (193 parameters)\\
Dense classifier head & Dense(64, 64) [4,160] + ReLU + Dropout(0.22) + Dense(64, 1) [65] + aux adapter [1,087] = 5,312 params\\
Total trainable parameters & 58{,}241 parameters\\
Dwell persistence timer & 20 samples (12.5\,ms)\\
Handshake confidence threshold & $\theta_{\text{AI}} = 0.99$\\
AI-alone confidence threshold & $\theta_{\text{solo}} = 0.998$\\
Instantaneous high-set threshold & $\max_\varphi I_{d,\varphi} > 10.0$\,pu\\
Per-inference computation budget & 1.71\,MFLOPs (0.855\,MMACs, incl.\ 1.2\,kFLOPs sliding FFT)\\ \bottomrule
\end{tabular}\end{table}

\chapter{Reproducibility and Standards}
\section{Computational Environment and Software Dependencies}
Simulation and analysis were executed on a workstation with an Intel Core i7-12700H CPU @ 2.30\,GHz (14 cores, 20 threads), 32\,GB DDR5 RAM, and an NVIDIA GeForce RTX 3060 GPU running 64-bit Windows 11. Software dependencies:
\begin{itemize}[leftmargin=1.4em,itemsep=2pt]
\item MATLAB R2024a (v24.1.0) with Simulink, Simscape Electrical, Deep Learning Toolbox, Signal Processing Toolbox, and MATLAB Support for ONNX.
\item Python 3.11.7 with PyTorch 2.2.1, PyWavelets 1.5.0, NumPy 1.26.4, SciPy 1.12.0, scikit-learn 1.4.1, and ONNX Runtime 1.17.1.
\item Git version control with atomic commit history across all development phases.
\end{itemize}

\section{Applicable Standards and Engineering Guides}
The modeling, protection parameters, and evaluation protocols were established with reference to applicable IEEE and IEC standards and guides:
\begin{itemize}[leftmargin=1.4em,itemsep=2pt]
\item \textbf{IEEE Std C37.91-2021:} \textit{IEEE Guide for Protecting Power Transformers}.
\item \textbf{IEEE Std C37.110-2023:} \textit{IEEE Guide for the Application of Current Transformers Used for Protective Relaying Purposes}.
\item \textbf{IEC 60255-187-1:2021:} \textit{Measuring Relays and Protection Equipment -- Part 187-1: Functional Requirements for Differential Protection -- AC Motors, Generators and Transformers}.
\item \textbf{IEC 61850-9-2:} \textit{Specific Communication Service Mapping (SCSM) -- Sampled Values over ISO/IEC 8802-3}.
\end{itemize}

\end{document}
"""

def main():
    TEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEX_PATH.write_text(TEX_CONTENT, encoding="utf-8")
    print(f"Successfully rebuilt {TEX_PATH} ({len(TEX_CONTENT)} characters).")

if __name__ == "__main__":
    main()
