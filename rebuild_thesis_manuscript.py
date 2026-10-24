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

% front-matter unnumbered heading helper
\newcommand{\frontchap}[1]{%
  \clearpage\thispagestyle{fancy}%
  \begin{center}\Large\bfseries #1\end{center}\vspace{6pt}%
  \addcontentsline{toc}{chapter}{#1}}

\newcommand{\sigblock}[3]{%
  \vspace{14pt}\noindent\textbf{#1}\\[26pt]
  \rule{6.5cm}{0.4pt}\\ #2\\ #3\par}

\begin{document}

% ===================== TITLE PAGE =====================
\begin{titlepage}
\centering
\vspace*{0.6in}
{\LARGE\bfseries HYBRID ADAPTIVE TRANSFORMER\\[2pt] DIFFERENTIAL PROTECTION:\\[6pt] AN INTELLIGENT DWT--LSTM FRAMEWORK\par}
\vfill
{\large\bfseries Md Moinul Haque \& Md Reyaz Uddin\par}
\vspace{0.5in}
{\large B.Sc. ENGINEERING THESIS\par}
\vfill
{\bfseries DEPARTMENT OF ELECTRICAL, ELECTRONIC AND COMMUNICATION ENGINEERING\par}
{\bfseries MILITARY INSTITUTE OF SCIENCE AND TECHNOLOGY (MIST)\par}
{MIRPUR CANTONMENT, DHAKA, BANGLADESH\par}
\vspace{0.35in}
{\large\bfseries OCTOBER 2026\par}
\end{titlepage}

\pagenumbering{roman}

% second title page
\thispagestyle{fancy}
\begin{center}
\vspace*{0.4in}
{\large\bfseries HYBRID ADAPTIVE TRANSFORMER DIFFERENTIAL PROTECTION:\\ AN INTELLIGENT DWT--LSTM FRAMEWORK\par}
\vspace{0.5in}
{\bfseries Md Moinul Haque (ID: 202216206) \& Md Reyaz Uddin (ID: 202216211)\par}
\vspace{0.4in}
\textit{A Thesis Submitted in Partial Fulfillment of the Requirements for the\\ Degree of Bachelor of Science in Electrical, Electronic and Communication Engineering}\par
\vspace{0.6in}
{\bfseries DEPARTMENT OF ELECTRICAL, ELECTRONIC AND COMMUNICATION ENGINEERING\\ MILITARY INSTITUTE OF SCIENCE AND TECHNOLOGY (MIST)\\ MIRPUR CANTONMENT, DHAKA, BANGLADESH\par}
\vspace{0.3in}
{\bfseries OCTOBER 2026\par}
\end{center}

% ===================== APPROVAL =====================
\frontchap{APPROVAL CERTIFICATE}
\begin{center}\textit{This is to certify that the thesis entitled}\\[4pt]
\textbf{``Hybrid Adaptive Transformer Differential Protection:\\ An Intelligent DWT--LSTM Framework''}\end{center}
\vspace{4pt}
submitted by Md Moinul Haque (ID: 202216206) \& Md Reyaz Uddin (ID: 202216211) to the Department of Electrical, Electronic and Communication Engineering, Military Institute of Science and Technology (MIST), Mirpur Cantonment, Dhaka, Bangladesh, in partial fulfillment of the requirements for the degree of Bachelor of Science in Electrical, Electronic and Communication Engineering, has been accepted as satisfactory for the award of the degree and approved by the undersigned examiners.
\sigblock{Supervisor (Chairman):}{Cdre A N M Didarul Alam, (L), NUP, psc, BN}{Dean, Faculty of Maritime Business Studies, Bangladesh Maritime University}
\sigblock{Head of the Department (Member, Ex-officio):}{Brigadier General Md Rezaul Awal, psc}{Head of the Department, Department of EECE, MIST, Dhaka, Bangladesh}
\sigblock{Internal Examiner (Member):}{Md Golam Mostafa, PhD}{Professor, Department of EECE, MIST, Dhaka, Bangladesh}
\sigblock{External Examiner (Member):}{Dr. Satya Prasad Majumder}{Professor, Department of EEE, BUET, Dhaka-1205, Bangladesh}
\vspace{12pt}\par Counter-signed on behalf of the Board of Advanced Studies.

% ===================== DECLARATION =====================
\frontchap{DECLARATION}
\begin{center}\textit{We hereby declare that the thesis entitled}\\[4pt]
\textbf{``Hybrid Adaptive Transformer Differential Protection:\\ An Intelligent DWT--LSTM Framework''}\end{center}
\vspace{4pt}
submitted to the Department of Electrical, Electronic and Communication Engineering, Military Institute of Science and Technology (MIST), Mirpur Cantonment, Dhaka, Bangladesh, in partial fulfillment of the requirements for the degree of Bachelor of Science in Electrical, Electronic and Communication Engineering, is a record of original work carried out by us under the supervision of Cdre A N M Didarul Alam, (L), NUP, psc, BN, Dean, Faculty of Maritime Business Studies, Bangladesh Maritime University. We hereby affirm that:
\begin{itemize}[leftmargin=1.4em,itemsep=2pt,topsep=4pt]
\item This thesis has not been submitted elsewhere, in whole or in part, for the award of any degree, diploma, or fellowship at this or any other university, institute, or organization.
\item The work presented herein is entirely the original research and intellectual contribution of the candidates, except where explicit reference has been made to the work of other researchers.
\item Proper acknowledgment has been made in the text to all other materials used, and all sources of information have been duly cited following the IEEE referencing format.
\item No part of this thesis has been fabricated, plagiarized, or misrepresented in any manner, and the results presented are accurate to the best of our knowledge and belief.
\item We have complied with all ethical guidelines and academic integrity standards set forth by the Military Institute of Science and Technology.
\end{itemize}
\vspace{24pt}
\noindent Candidates' Signatures:\\[20pt]
\rule{6cm}{0.4pt} \hfill \rule{6cm}{0.4pt}\\[4pt]
\textbf{Md Moinul Haque} \hfill \textbf{Md Reyaz Uddin}\\
Candidate ID: 202216206 \hfill Candidate ID: 202216211\\[12pt]
Date: \rule{4.5cm}{0.4pt} \hfill Date: \rule{4.5cm}{0.4pt}

% ===================== DEDICATION =====================
\frontchap{DEDICATION}
\vspace{1in}
\begin{center}\itshape\large
Dedicated to our parents and families\\ for their unwavering love, sacrifices, and support\\ throughout our academic journey.
\end{center}

% ===================== ACKNOWLEDGEMENTS =====================
\frontchap{ACKNOWLEDGEMENTS}
First and foremost, all praises are due to Almighty Allah for His infinite blessings, guidance, and mercy, without which this endeavor would not have been possible. We are profoundly grateful for the strength, patience, and wisdom He bestowed upon us throughout the course of our research and our entire academic journey.

We would like to express our deepest gratitude to our thesis supervisor, Cdre A N M Didarul Alam, (L), NUP, psc, BN, Professor, Department of Electrical, Electronic and Communication Engineering, for his invaluable guidance, continuous encouragement, and unwavering support throughout every phase of this research. His profound expertise in power system protection, insightful suggestions, and patient mentorship have been instrumental in shaping the direction and quality of this work.

Our sincere thanks go to the Head of the Department, Department of Electrical, Electronic and Communication Engineering, MIST, for providing the necessary academic facilities, laboratory resources, and an excellent research environment. We are also grateful to all faculty members of the Department of EECE at MIST whose teachings in power systems, signal processing, and machine learning directly contributed to the interdisciplinary nature of this research.

We extend our heartfelt appreciation to our fellow classmates and laboratory colleagues at MIST for their camaraderie, technical assistance with MATLAB/Simulink simulations, and willingness to share knowledge in deep learning and signal processing. We are profoundly indebted to our parents, whose sacrifices and unconditional love have been the bedrock of our educational pursuits, and to our siblings, extended family, and close friends for their constant support.

Finally, we acknowledge with gratitude the infrastructure and computational resources provided by MIST, as well as the open-source contributors and researchers whose published works in power system protection, wavelet analysis, and deep learning have served as the foundational pillars upon which this research is built.

\vspace{18pt}\noindent Date:\hfill Md Moinul Haque \& Md Reyaz Uddin

% ===================== ABSTRACT =====================
\frontchap{ABSTRACT}
Power transformers constitute the most critical and capital-intensive components of electrical power transmission and distribution networks, making their reliable and rapid protection a paramount concern for the continuity and stability of electric power supply~\cite{ref4}. Differential protection has long been the primary scheme for safeguarding power transformers against internal faults, comparing the currents entering and leaving the protected zone~\cite{ref4}. However, conventional percentage differential relays struggle to distinguish genuine internal faults from non-fault transients such as magnetizing inrush, recovery inrush, over-excitation, and external through-faults accompanied by severe current transformer (CT) saturation~\cite{ref3}. Furthermore, harmonic-restraint methods suffer reduced sensitivity in modern transformers with low-loss, high-permeability core steels~\cite{ref4}.

This thesis proposes a hybrid adaptive differential protection framework that integrates multi-resolution Discrete Wavelet Transform (DWT) feature extraction and second-harmonic restraint ratios with the temporal sequence modeling of Long Short-Term Memory (LSTM) neural networks. A two-level Daubechies-4 (db4) decomposition extracts nine wavelet energy features across three phases ($E_{D1}, E_{D2}, E_{A2}$), complemented by three phase-wise second-harmonic ratios ($I_{d,2nd}/I_{d,fund}$) to form a compact 12-dimensional feature vector over a 32-sample sliding window (one cycle at 50\,Hz and 1.6\,kHz sampling). A two-layer unidirectional LSTM (64 hidden units per layer, 58{,}241 trainable parameters) is trained strictly under a leak-free, trace-stratified partitioning protocol with waveform-measured onset detection. The exported ONNX model is integrated into MATLAB/Simulink for real-time closed-loop co-simulation. The hybrid relay combines an instantaneous high-set overcurrent bypass with a dual-path supervisory architecture: an 87T-gated path requiring both conventional restraint pickup and confirmed AI trip probability ($\ge 0.99$), and an autonomous AI-alone path ($\ge 0.998$) dedicated to detecting high-impedance internal faults below the conventional 87T pickup threshold, subject to a 20-sample (12.5\,ms) persistence dwell timer.

A high-fidelity electromagnetic-transient simulation model of a 300\,MVA, 230/11\,kV, Yd1 power transformer was developed with realistic core non-linearities, calibrated CT secondary bases (0.9302\,A nominal), and six independent measurement noise channels. A rigorously verified stress dataset of 3{,}220 compiled traces spanning 16 scenario categories (11 fault types, 10--110\% rated current loading, CT burdens 4--10$\times$, over-excitation, and recovery inrush) was compiled, alongside an independent 300-trace Out-of-Distribution (OOD) test set. In 5-fold cross-validation across 15 models (3 random seeds) evaluating 3{,}218 usable traces (1{,}873 healthy, 1{,}251 detectable internal faults, and 94 segregated undetectable faults $<0.05$\,pu), the deployed hybrid relay achieved \textbf{99.01\% dependability} ($\pm0.48\%$) and \textbf{99.66\% security} ($\pm0.24\%$) with zero pre-fault trips, a median operate time of \textbf{15.6\,ms} (96.9\% within two cycles), and \textbf{100.0\% decision agreement} in closed-loop Simulink co-simulation. The supervisory framework successfully eliminates false trips during inrush, recovery inrush, over-excitation, and CT saturation while reliably detecting challenging high-impedance internal faults.

\vspace{4pt}\noindent\textbf{Keywords:} Transformer differential protection, Discrete Wavelet Transform (DWT), Long Short-Term Memory (LSTM), MATLAB/Simulink, magnetizing inrush current, CT saturation, ONNX, real-time relay, fault classification, deep learning, hybrid adaptive protection.

% ===================== LIST OF SYMBOLS =====================
\frontchap{LIST OF SYMBOLS / NOTATIONS}
\begin{longtable}{p{3cm} p{9.5cm} p{1.6cm}}
\toprule \textbf{Symbol} & \textbf{Description} & \textbf{Unit}\\ \midrule \endhead
$I_d$ & Differential current & A\\
$I_r$ & Restraint (bias) current & A\\
$I_{pickup}$ & Minimum pickup current setting & A\\
$I_{d,fund}$ & Fundamental frequency differential current component & A\\
$I_{d,2nd}$ & Second harmonic differential current component & A\\
$k_2$ & Second harmonic restraint ratio ($I_{d,2nd}/I_{d,fund}$) & \%\\
$S_1, S_2$ & Slopes of the dual-slope differential characteristic & \%\\
$T_{op}$ & Relay operating time & ms\\
$\Phi_{CT}$ & CT magnetization flux & Wb\\
$\phi_r$ & Remanent (residual) magnetic core flux & Wb\\
$\phi_{sat}$ & Saturation core flux & Wb\\
$\psi(t)$ & Mother wavelet function & --\\
$\phi(t)$ & Wavelet scaling function & --\\
$a_j,\,d_j$ & Approximation / detail coefficients at level $j$ & --\\
$h[n],\,g[n]$ & Low-pass / high-pass decomposition filters & --\\
$E_A,\,E_D$ & Approximation / detail sub-band energy feature & pu$^2$\\
$f_t,\,i_t,\,o_t$ & LSTM forget, input, output gate activations & --\\
$C_t,\,h_t$ & LSTM cell state / hidden state at step $t$ & --\\
$\sigma(\cdot),\,\tanh(\cdot)$ & Sigmoid / hyperbolic tangent activation & --\\
$\eta$ & Learning rate & --\\
$x_t,\,\hat{y}_t,\,y_t$ & Input feature / predicted label / ground truth at step $t$ & --\\
$p_{\text{AI}}$ & Neural network instantaneous internal fault probability & --\\
$p_{\text{AI,conf}}$ & Dwell-filtered AI confidence probability (20-sample min) & --\\
$\theta_{\text{AI}}$ & Hybrid 87T-gate AI confirmation threshold (0.99) & --\\
$\theta_{\text{solo}}$ & Autonomous AI-alone trip threshold (0.998) & --\\
$\mathcal{L}$ & Weighted binary cross-entropy loss function & --\\
TP, TN, FP, FN & True/False Positives and Negatives & --\\
$S_{rated}$ & Transformer rated power & MVA\\
$R_f$ & Fault resistance & $\Omega$\\
$\varphi_i$ & Fault inception angle & deg\\
$N_{CT}$ & Current-transformer turns ratio & --\\
$f_s$ & Relay sampling frequency (1.6\,kHz) & Hz\\
\bottomrule
\end{longtable}

% ===================== LIST OF ABBREVIATIONS =====================
\frontchap{LIST OF ABBREVIATIONS}
\begin{longtable}{p{3.2cm} p{10.5cm}}
\toprule \textbf{Abbreviation} & \textbf{Full Form}\\ \midrule \endhead
CT / PT & Current Transformer / Potential (Voltage) Transformer\\
CHR & Current Harmonic Restraint\\
DWT & Discrete Wavelet Transform\\
BDWT & Boundary Discrete Wavelet Transform\\
DFT / FFT & Discrete / Fast Fourier Transform\\
MRA & Multi-Resolution Analysis\\
EMT & Electromagnetic Transient\\
ANN & Artificial Neural Network\\
DNN & Deep Neural Network\\
CNN & Convolutional Neural Network\\
RNN & Recurrent Neural Network\\
LSTM & Long Short-Term Memory\\
GRU & Gated Recurrent Unit\\
SVM & Support Vector Machine\\
PNN & Probabilistic Neural Network\\
RF & Random Forest\\
ReLU & Rectified Linear Unit\\
Adam & Adaptive Moment Estimation\\
AUC / ROC & Area Under Curve / Receiver Operating Characteristic\\
SLG & Single-Line-to-Ground Fault\\
LL & Line-to-Line Fault\\
LLG & Line-to-Line-to-Ground Fault\\
3LG & Three-Phase-to-Ground Fault\\
SOTF & Switch-On-To-Fault\\
HiZ & High-Impedance Fault\\
OOD & Out-of-Distribution\\
MATLAB & Matrix Laboratory\\
ONNX & Open Neural Network Exchange\\
HIL & Hardware-in-the-Loop\\
RTDS & Real-Time Digital Simulator\\
FPGA / GPU / CPU & Field-Programmable Gate Array / Graphics / Central Processing Unit\\
SNR & Signal-to-Noise Ratio\\
IEEE / IEC & Inst.\ of Electrical and Electronics Engineers / Int.\ Electrotechnical Commission\\
\bottomrule
\end{longtable}

% ===================== TOC / LOT / LOF =====================
\clearpage
\renewcommand{\contentsname}{CONTENTS}
\tableofcontents
\clearpage
\renewcommand{\listtablename}{LIST OF TABLES}
\listoftables
\clearpage
\renewcommand{\listfigurename}{LIST OF FIGURES}
\listoffigures

% ===================== MAIN MATTER =====================
\clearpage
\pagenumbering{arabic}

\chapter{Introduction}
\section{Background}
Power transformers are among the most critical and capital-intensive assets in electrical power systems, serving as the essential link between generation, transmission, and distribution networks~\cite{ref1}. An unscheduled outage incurs enormous direct replacement costs and indirect losses from energy not served and potential cascading failures~\cite{ref2}. Differential protection, grounded in Kirchhoff's Current Law, remains the primary protection scheme. Under healthy conditions, the primary and secondary currents are related by the turns ratio $n$:
\begin{equation}
I_{primary}-\frac{I_{secondary}}{n}\approx 0 .
\end{equation}
When an internal fault occurs, this balance is disrupted and the differential current becomes significantly nonzero, triggering relay operation~\cite{ref3}.

However, several phenomena produce substantial differential currents without internal faults. Magnetizing inrush current, arising during transformer energization, can reach 5--15 times the rated current with significant even-harmonic content~\cite{ref4}. Current-transformer (CT) saturation distorts secondary waveforms under large DC-offset fault currents~\cite{ref9}, and overexcitation introduces additional harmonic components~\cite{ref5}. Traditional harmonic restraint (HR) and blocking methods face increasing limitations as renewable sources, power-electronic converters, and advanced core materials alter the waveform signatures conventional relays depend upon~\cite{ref5,ref6}. This thesis proposes a hybrid adaptive framework integrating the discrete wavelet transform (DWT) with long short-term memory (LSTM) networks for more robust discrimination between fault and non-fault conditions~\cite{ref6,ref14}.
\begin{figure}[H]\centering\includegraphics[width=0.6\textwidth]{fig_1_1.png}
\caption{Single-line schematic of the transformer differential protection zone.}\label{fig:1.1}\end{figure}

\section{Research Motivation}
The reliability of differential protection is increasingly threatened by compounding factors. First, conventional harmonic restraint relies on fixed second-harmonic thresholds (typically 15--20\%), yet modern transformers with amorphous-alloy cores exhibit reduced second-harmonic content during inrush that can fall below these thresholds~\cite{ref4}, while internal faults near voltage zero-crossings can generate sufficient harmonics to inadvertently restrain the relay~\cite{ref8}. Second, CT saturation produces asymmetric distortion that creates spurious differential currents persisting for several cycles~\cite{ref9}. Third, advanced core materials exhibit steeper $B$--$H$ curves with altered harmonic signatures~\cite{ref4}. Fourth, renewable converters inject non-sinusoidal currents with limited fault contributions~\cite{ref12}. Fifth, complex network configurations narrow the margin between legitimate restraint and genuine faults~\cite{ref13}. These challenges motivate a new generation of protection algorithms leveraging advanced signal processing and computational intelligence~\cite{ref14}.

\section{Problem Statement}
Despite over a century of development, transformer differential protection schemes continue to experience maloperations at unacceptable rates. \textbf{Given} time-series differential current signals $\{I_d(t)\}$ sampled at $f_s = 1.6$\,kHz, encompassing internal faults, magnetizing inrush, external faults with severe CT saturation, over-excitation, and normal load conditions, corrupted by measurement noise and CT errors; \textbf{find} a classification function $f:\mathcal{X}\!\to\!\mathcal{Y}$ mapping $x\in\mathcal{X}$ to $\mathcal{Y}=\{$Trip, No-Trip$\}$ with high accuracy; \textbf{subject to} operating time within one to two cycles (20--40\,ms at 50\,Hz, with sub-cycle instantaneous high-set tripping for severe faults $<1$\,ms), missed-detection probability $P_{miss}\le 0.01$, false-trip probability $P_{false}\le 0.01$, robustness across operating states, and generalization to unseen operating conditions. The key difficulties arise from the highly nonlinear, non-stationary feature space and strict real-time constraints~\cite{ref15}.

\section{Research Objectives}
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Simulation model and data generation.} Develop a detailed EMT model of a 300\,MVA transformer protection system in MATLAB/Simulink, generating differential-current signals for internal faults (SLG, LL, LLG, 3LG), magnetizing inrush (no-load, loaded, and recovery), external faults with severe CT saturation, over-excitation, and normal load variations~\cite{ref19}.
\item \textbf{Optimal DWT feature extraction.} Select the mother wavelet (Daubechies-4, db4) and decomposition level (two-level dyadic filter bank), extracting sub-band energies ($E_{D1}, E_{D2}, E_{A2}$) fused with phase-wise second-harmonic restraint ratios ($I_{d,2nd}/I_{d,fund}$) to maximize fault/non-fault separability~\cite{ref20}.
\item \textbf{Hybrid DWT--LSTM classification and adaptive logic.} Integrate wavelet feature extraction with LSTM temporal modeling and develop a dual-path supervisory protection architecture coupling conventional 87T dual-slope restraint with high-confidence LSTM sequence classification and an autonomous AI-alone path with a 20-sample (12.5\,ms) persistence dwell timer for high-impedance faults~\cite{ref1,ref2}.
\item \textbf{Evaluation, benchmarking, and robustness.} Benchmark the proposed framework against conventional 87T and machine-learning/deep-learning baselines (SVM, ANN, Random Forest, 1D-CNN, GRU, standalone LSTM) and assess robustness under noise, CT saturation, remanent flux, frequency deviations, and out-of-distribution stress~\cite{ref3,ref21}.
\end{enumerate}

\section{Scope and Limitations}
\subsection{Scope}
A two-winding 300\,MVA, 230/11\,kV, Yd1 transformer is modeled in detail; generalization to other ratings and vector groups is future work. Fault types include SLG, LL, LLG, and 3LG internal faults at various winding percentages, inception angles, and fault resistances ($R_f \le 21\,\Omega$); external through-faults with severe CT saturation and non-fault transients (inrush, over-excitation) are used for security assessment. Inter-turn winding short circuits are excluded from the current lumped-parameter two-winding model and deferred to future work. A two-level DWT decomposition with Daubechies-4 filter is implemented; the LSTM is the primary classifier, benchmarked against SVM, ANN, Random Forest, 1D-CNN, and GRU baselines. Validation uses simulation-generated data and closed-loop MATLAB/Simulink co-simulation via ONNX; hardware-in-the-loop and RTDS validation are deferred. The system is configured for 50\,Hz operation.
\subsection{Limitations}
Training data is simulation-generated; no physical-relay hardware validation is performed; class imbalance is mitigated by loss weighting; the adaptive threshold targets static loading; and IEC 61850 communication packet loss is not modeled.

\section{Contributions of This Work}
\textbf{(1)} A physically grounded 12-dimensional feature fusion engine combining two-level db4 DWT sub-band energies ($E_{D1}, E_{D2}, E_{A2}$) with phase-wise second-harmonic restraint ratios ($I_{d,2nd}/I_{d,fund}$) over a 32-sample sliding window. \textbf{(2)} A dual-path supervisory protection architecture coupling conventional 87T dual-slope restraint with a temporal LSTM sequence classifier and an autonomous AI-alone path with a 20-sample (12.5\,ms) persistence dwell timer to recover high-impedance internal faults ($R_f \le 7.0\,\Omega$) below 87T pickup without risking false trips. \textbf{(3)} End-to-end closed-loop co-simulation in MATLAB/Simulink via ONNX with zero numerical parity divergence against Python, validated across 3{,}218 traces in 5-fold cross-validation and benchmarked against seven literature models and an isolated 300-trace Out-of-Distribution stress corpus.

\section{Thesis Organization}
Chapter~2 reviews the literature and identifies research gaps. Chapter~3 establishes the mathematical foundations. Chapter~4 details the MATLAB/Simulink model and dataset. Chapter~5 presents the DWT--LSTM methodology. Chapter~6 reports results, benchmarking, and robustness. Chapter~7 concludes and outlines future work.

\chapter{Literature Review}
\section{Introduction}
This chapter critically reviews transformer differential protection, spanning conventional harmonic restraint and waveform-based methods, signal-processing techniques, machine-learning approaches (ANN, SVM, PNN, ensembles), and deep-learning architectures (CNN, RNN, LSTM), identifying the research gaps that motivate the proposed hybrid framework. The surveyed literature is drawn primarily from IEEE Transactions on Power Delivery, IEEE Transactions on Power Systems, and Electric Power Systems Research, from the 1950s through 2025.

\section{Conventional Differential Protection Methods}
\subsection{Harmonic Restraint Methods}
The harmonic restraint method, first proposed by Sharp and Glassburn in 1958, is the most widely deployed technique for discriminating inrush from internal faults~\cite{ref7}. Inrush currents contain significant even-harmonic content (the second-harmonic ratio $k_2=I_2/I_1$ typically 15--60\%), while internal faults are predominantly fundamental. The relay trips only when
\begin{equation}
I_d>I_{pickup},\quad I_d>S\,I_r,\quad \frac{I_2}{I_1}<k_{threshold},
\end{equation}
with $k_{threshold}$ typically set between 15\% and 20\%. Modern amorphous-alloy cores exhibit second-harmonic ratios as low as 7--10\%, causing false tripping~\cite{ref4}; internal faults near voltage zero-crossings can inadvertently restrain the relay~\cite{ref8}; and cross-blocking improves security but risks failure to trip for simultaneous inrush and fault~\cite{ref4}. Variable data-window Phaselet algorithms have been proposed to adapt to changing harmonic contents~\cite{ref40}.

\subsection{Waveform-Based and Equivalent-Circuit Methods}
Dead-angle and waveform correlation methods classify events based on waveshape features. Lin et al.~\cite{ref37} studied improved correlation algorithms to identify inrush waveforms, but such techniques remain sensitive to threshold selection and noise. Kang et al.~\cite{ref36} developed CT saturation compensation algorithms utilizing third-derivative secondary current functions. Equivalent-circuit methods detect internal faults when terminal measurements violate core magnetic flux equations~\cite{ref29}, but require high-accuracy voltage transducers and detailed manufacturer design constants~\cite{ref30}.

\section{Signal Processing Techniques}
The Discrete Fourier Transform provides frequency resolution at the expense of time localization, limiting its ability to capture transient inrush and fault waveforms~\cite{ref31,ref32}. The wavelet transform overcomes this through simultaneous time-frequency localization. For digital implementation the DWT uses cascaded low-pass/high-pass filters with downsampling for multi-resolution decomposition~\cite{ref5}. Daubechies-4 (db4) wavelets have been widely applied to power system transients~\cite{ref5,ref6}. Furthermore, Boundary Discrete Wavelet Transform (BDWT) and time-domain Clarke-wavelet formulations have been developed by Medeiros et al.~\cite{ref38,ref39} to address window-edge boundary distortion in real-time relay applications. However, standard window-wise wavelet algorithms extract static features without modeling the sequential temporal context across successive windows.

\section{Machine Learning Approaches}
\textbf{ANNs.} Three-layer neural networks with wavelet feature inputs were explored by Ngaopitakkul and Kunakorn~\cite{ref19} and Costa et al.~\cite{ref18}, attaining over 99\% classification accuracy on simulated events, but standard feedforward architectures discard sequential temporal context. \textbf{SVMs.} Support vector machines with wavelet features were investigated by Simões et al.~\cite{ref13} and Subramanian et al.~\cite{ref20}, achieving up to 98.2\% accuracy, though training overhead scales cubically. \textbf{PNNs.} Optimal Probabilistic Neural Networks (PNN) proposed by Tripathy et al.~\cite{ref9} reached 97.8--98.9\% accuracy for differential protection, though memory requirements grow with training sample count. \textbf{Ensembles.} Random forest classifiers evaluated by Abdusalam et al.~\cite{ref11} achieved 99.0\% accuracy at the expense of structural interpretability.

\section{Deep Learning Approaches}
\subsection{CNN, RNN, and LSTM Architectures}
A 1D-CNN at 1\,kHz over two-cycle windows reached 98.7\%, outperforming hand-crafted Fourier features~\cite{ref16}, but does not model global temporal dependencies. RNNs maintain a hidden state but suffer vanishing gradients; the LSTM overcomes this through a gated memory cell:
\begin{align}
f_t&=\sigma(W_f[h_{t-1},x_t]+b_f), & i_t&=\sigma(W_i[h_{t-1},x_t]+b_i),\\
\tilde{C}_t&=\tanh(W_C[h_{t-1},x_t]+b_C), & C_t&=f_t\odot C_{t-1}+i_t\odot \tilde{C}_t,\\
o_t&=\sigma(W_o[h_{t-1},x_t]+b_o), & h_t&=o_t\odot\tanh(C_t),
\end{align}
where $\sigma$ is the sigmoid and $\odot$ the Hadamard product. An LSTM on wavelet features over successive windows reached 99.3\%~\cite{ref3}; attention mechanisms add interpretability~\cite{ref1}; and comparisons of RNN/GRU/LSTM favor the LSTM for complex transients~\cite{ref23}.

\subsection{Advanced Waveform and Volatility Formulations}
Beyond standard neural networks, specialized statistical and signal-processing techniques have been developed to address specific transient phenomena. Hooshyar et al.~\cite{ref35} proposed a generalized autoregressive conditional heteroskedasticity (GARCH) framework to model differential-current volatility during inrush and internal faults. For rapid CT saturation compensation, Kang et al.~\cite{ref36} developed an effective third-derivative algorithm to detect core saturation onset and reconstruct undistorted secondary currents. Lin et al.~\cite{ref37} utilized improved waveform correlation algorithms to track inrush decay. While effective for specific phenomena, these methods often rely on specialized threshold heuristics or require high-derivative numerical stability.

\section{Comparative Synthesis of the Literature}
Table~\ref{tab:litcompare} synthesizes representative studies. Reported accuracies are the authors' own on their own datasets and are not directly comparable; a controlled comparison on a single unified dataset is given in Chapter~6.
\begin{table}[H]\centering
\caption{Comparative synthesis of representative transformer differential protection studies.}\label{tab:litcompare}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}clp{5.5cm}cl@{}}
\toprule
\textbf{Ref.} & \textbf{Approach} & \textbf{Classifier / method} & \textbf{Acc.\,(\%)} & \textbf{Limitation}\\ \midrule
\cite{ref6} & db4 DWT & Threshold logic & $\sim$97 & Hand-tuned thresholds\\
\cite{ref19} & DWT & Back-propagation NN & $\sim$97 & Static feature vector\\
\cite{ref18} & Wavelet stats & ANN & 99.1 & No temporal context\\
\cite{ref9} & Harmonic & Optimal PNN & 97.8 & Memory grows with samples\\
\cite{ref13} & Wavelet & SVM (RBF) & 98.2 & No sequence modelling\\
\cite{ref20} & Wavelet packet & SVM & $\sim$98 & High dimensionality\\
\cite{ref11} & Fourier+wavelet & Random forest & 99.0 & No temporal model\\
\cite{ref16} & Accelerated DNN & 1D-CNN & 98.7 & Weak long-range context\\
\cite{ref3} & Wavelet & LSTM & 99.3 & No hybrid relay handshake\\
\cite{ref1,ref2} & Improved wavelet & LSTM & $\sim$99.5 & No supervisory veto\\
\cite{ref23} & Dual DNN & Inrush vs.\ internal & $\sim$99.4 & Two-class only\\
\textbf{This work} & 2-level db4 + 2nd harm.\ (12 feat.) & Dual-path LSTM + 87T handshake & \textbf{99.01 / 99.66} & ---\\
\bottomrule
\end{tabular}%
}
\end{table}
The field has progressed from fixed-threshold schemes through shallow learning to deep sequence models, with accuracy rising above 99\%. Yet almost all recent high-accuracy studies evaluate a standalone classifier that issues the trip directly, leaving the dependability--security trade-off implicit, and none couples the learned classifier to a certified 87T element through an explicit supervisory handshake. This thesis is distinguished on all three counts.

\section{Research Gaps}
Five gaps motivate this work: (1) ad-hoc wavelet parameter selection; (2) no full integration of DWT feature extraction with LSTM temporal modeling in a serial hybrid; (3) fixed decision thresholds without persistence filtering; (4) limited robustness evaluation under severe CT saturation and out-of-distribution drift; and (5) absence of standardized benchmarking. This thesis addresses all five.

\chapter{Mathematical Modeling and Theoretical Framework}
\section{Introduction}
This chapter establishes the mathematical foundations for the proposed DWT--LSTM scheme: differential relaying principles, magnetizing inrush theory, CT saturation modeling, internal-fault characteristics, and the classification framework.

\section{Transformer Differential Protection Fundamentals}
\subsection{Differential and Restraint Currents}
For a three-phase power transformer, let $\dot{\mathbf{I}}_{HV}'$ and $\dot{\mathbf{I}}_{LV}'$ denote the secondary line currents referred to a common base and corrected for the Yd1 vector group phase displacement:
\begin{equation}
\mathbf{I}_d = \left|\dot{\mathbf{I}}_{HV}' + \dot{\mathbf{I}}_{LV}'\right|,\qquad
\mathbf{I}_r = \frac{1}{2}\left(\left|\dot{\mathbf{I}}_{HV}'\right| + \left|\dot{\mathbf{I}}_{LV}'\right|\right).
\end{equation}
Under healthy through-load or external fault conditions, $\dot{\mathbf{I}}_{HV}' \approx -\dot{\mathbf{I}}_{LV}'$ and $I_d \approx 0$. In practice, a small residual steady-state differential current arises from CT ratio mismatch, off-nominal tap position, core magnetizing current, and measurement noise:
\begin{equation}
I_{d,steady}=\sqrt{(\varepsilon_{CT}I_{load})^2+(\Delta_{tap}I_{load})^2+I_m^2+\varepsilon_{meas}^2}.
\end{equation}
\subsection{Operating Characteristics}
The dual-slope restraint characteristic defines the operating threshold $I_{op}$ as a function of restraint current $I_r$. While industry relays typically select initial slope $S_1$ in the range of 25--40\% and second slope $S_2$ in the range of 50--80\%, the high-fidelity simulation model calibrates $S_1 = 15\%$ to accommodate steady-state errors and $S_2 = 40\%$ to provide restraint during CT saturation (Figure~\ref{fig:3.1}). The relay generates an 87T trip vote when $I_d > I_{op}(I_r)$.
\begin{figure}[H]\centering\includegraphics[width=0.55\textwidth]{fig_3_1.png}
\caption{Dual-slope percentage restraint characteristic of the differential relay.}\label{fig:3.1}\end{figure}
\subsection{Pickup Current and Fault Resistance Limits}
The minimum pickup setting $I_{pickup}$ balances sensitivity and security, satisfying $I_{d,steady,max} < I_{pickup} < I_{d,fault,min}$ (typically 0.2--0.5\,pu). For an internal single-line-to-ground (SLG) fault with fault resistance $R_f$, symmetrical component analysis gives the total fault current as:
\begin{equation}
I_f = \frac{3 V_f}{|Z_1 + Z_2 + Z_0 + 3 R_f|}
\end{equation}
where $V_f$ is the pre-fault phase-to-ground voltage and $Z_1, Z_2, Z_0$ are the sequence impedances seen from the fault point. As fault resistance $R_f$ increases, the differential current $I_d$ decreases monotonically. The maximum fault resistance detectable by conventional percentage differential protection occurs when $I_d$ drops below pickup:
\begin{equation}
R_{f,max} \approx \frac{V_f}{I_{pickup}} - \frac{|Z_1 + Z_2 + Z_0|}{3}.
\end{equation}
For $R_f > R_{f,max}$ ($R_f \ge 1.2\,\Omega$ in the 300\,MVA plant), $I_d < I_{pickup}$, leaving the fault undetectable by standard 87T elements.

\section{Magnetizing Inrush Current}
\subsection{Core Saturation Theory}
Faraday's law gives $v(t)=N\,d\phi/dt=NA\,dB/dt$. For sinusoidal excitation $v(t)=V_m\sin(\omega t+\alpha)$, the instantaneous core flux includes an exponentially decaying DC component:
\begin{equation}
\phi(t)=-\Phi_m\cos(\omega t+\alpha)+\Phi_m\cos(\alpha)e^{-t/\tau}+\phi_r e^{-t/\tau}.
\end{equation}
At worst-case energization switching ($\alpha=0,\ \phi_r=+\Phi_m$), the peak flux reaches $\phi_{peak}=2\Phi_m+\phi_r=3\Phi_m$, driving the core deep into saturation where differential permeability drops toward air ($dB/dH \to \mu_0$, or $d\phi/di \to 0$).
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_3_2.png}
\caption{Core $B$--$H$ saturation curve and the resulting magnetizing inrush waveform.}\label{fig:3.2}\end{figure}
\subsection{Factors and Harmonics}
Inrush magnitude depends on switching angle $\alpha$, residual flux $\phi_r$ (0--80\% of $\Phi_m$), source impedance, and core material, ranging 3--15$\times$ rated current. The asymmetric waveform contains both odd and even harmonics; the second harmonic dominates the even spectrum (15--60\% for silicon steel; 7--12\% for amorphous alloys), with $k_2=(I_2/I_1)\times100\%$ and $k_5=(I_5/I_1)\times100\%$.
\subsection{Recovery Inrush}
Recovery inrush occurs when an external fault is cleared by external breaker operation. The sudden post-fault voltage recovery drives the transformer core into asymmetric saturation, producing a transient inrush differential current while the unit is carrying load, presenting a severe security challenge to conventional relays~\cite{ref4}.

\section{Current Transformer Saturation}
The CT secondary current equals the referred primary current minus the excitation current, $I_s = I_p' - I_e$, where the magnetizing branch operates in parallel with the secondary burden. The nonlinear magnetization curve is modeled by:
\begin{equation}
i_e(\lambda) = A e^{B|\lambda|}\operatorname{sign}(\lambda) + C\lambda,
\end{equation}
where $\lambda = N_2 \phi$ is flux linkage, and $A, B, C$ are core fitting parameters. CT saturation is driven by DC offset in fault currents:
\begin{equation}
i_p(t) = I_m\left[\sin(\omega t+\alpha-\varphi)-\sin(\alpha-\varphi)e^{-t/\tau_f}\right].
\end{equation}
Saturation occurs when $\lambda > \lambda_{sat}$. During severe external through-faults, unequal CT saturation on HV and LV sides produces spurious differential current $I_d = |I_{e1} - I_{e2}| \neq 0$; the second slope $S_2$ and sequence intelligence provide necessary restraint.
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_3_3.png}
\caption{Current transformer equivalent circuit and saturation-induced secondary distortion.}\label{fig:3.3}\end{figure}

\section{Internal Fault Characteristics}
Internal faults include SLG (most common), LL, LLG, and 3LG faults. When an internal fault occurs at turn fraction $p \in (0, 1]$ of the winding, the fault impedance scales quadratically with the shorted turns:
\begin{equation}
Z_{fault}(p) = p^2 Z_t + R_f.
\end{equation}
Using symmetrical components, an SLG fault yields $I_{a1}=I_{a2}=I_{a0}=V_f/(Z_1+Z_2+Z_0+3Z_f)$. Fault time constants (0.02--0.05\,s) are shorter than inrush (0.1--0.5\,s), with negligible even-harmonic content under ideal CT conditions.

\section{Mathematical Framework for Classification}
\subsection{Feature Space and Bayes-Optimal Decision}
The wavelet energy at decomposition level $k$ is $E_{Dk}=\sum_n|d_k[n]|^2$. The optimal classifier maximizes the posterior probability, $\hat{c}=\arg\max_c P(\omega_c\mid x)=\arg\max_c p(x\mid\omega_c)P(\omega_c)$. For power system protection, the cost of a missed internal fault $L_{FN}$ vastly exceeds the cost of a false trip $L_{FP}$ ($L_{FN} \gg L_{FP}$), biasing the objective toward dependability. The LSTM outputs a scalar probability $p_{\text{AI}}(t) = \sigma(z(t)) \in [0, 1]$ trained via weighted binary cross-entropy:
\begin{equation}
\mathcal{L} = -\frac{1}{N}\sum_{n=1}^N \left[ w \cdot y_n \ln p_{\text{AI}}^{(n)} + (1 - y_n) \ln (1 - p_{\text{AI}}^{(n)}) \right]
\end{equation}
where $y_n \in \{0, 1\}$ and positive-class weight $w = 1.4155$ compensates for class imbalance and penalizes false negatives. Feature separability is guided by the Fisher discriminant ratio $\text{FDR}=(\mu_{c1}-\mu_{c2})^2/(\sigma_{c1}^2+\sigma_{c2}^2)$ and mutual information $I(X;Y)=H(Y)-H(Y\mid X)$.
\begin{figure}[H]\centering\includegraphics[width=0.55\textwidth]{fig_3_4.png}
\caption{Conceptual feature-space separation of event classes with cost-asymmetric decision boundaries.}\label{fig:3.4}\end{figure}
\subsection{Performance Metrics}
Performance is evaluated by precision $=TP/(TP+FP)$, recall $=TP/(TP+FN)$, and $F1=2\,P\,R/(P+R)$. For protection relays, dependability $=TP_{fault}/(TP_{fault}+FN_{fault})$ and security $=TN_{healthy}/(FP_{healthy}+TN_{healthy})$ are paramount, together with operating latency $T_{op}=t_{trip}-t_{event}$ and the AUC--ROC metric.
\subsection{Adaptive Thresholding vs.\ Dual-Path Logic}
While adaptive pickups adjust the threshold $I_{pickup}(t)=I_{p0}+k_1 I_r(t)+k_2\hat{\sigma}_d(t)$ based on differential current variance $\hat{\sigma}_d$, this work achieves adaptive security through a dual-path supervisory architecture where the conventional 87T trip decision is confirmed by the temporal LSTM sequence classifier.

\chapter{Power System Simulation Model Using MATLAB/Simulink}
\section{Introduction}
MATLAB/Simulink was selected for its integrated environment combining high-fidelity electromagnetic-transient (EMT) modeling via Simscape Electrical with native machine-learning support and ONNX runtime, enabling a seamless workflow from data generation to DWT--LSTM training, validation, and deployment~\cite{ref1,ref2}.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_4_1.png}
\caption{Overview of the MATLAB/Simulink power-system simulation model (Simulink main panel).}\label{fig:4.1}\end{figure}

\section{Simulation Environment}
The platform comprises MATLAB R2024a with Simulink, Simscape Electrical, the Deep Learning Toolbox, the Signal Processing Toolbox, and the ONNX converter. A discrete-time solver with fixed step $\Delta t=1\times10^{-5}$\,s (10\,\textmu s) is used, giving a Nyquist frequency $f_{Nyquist}=1/(2\Delta t)=50$\,kHz---a 50$\times$ oversampling margin over the 1.6\,kHz relay rate. Each simulation runs for $T_{sim}=1.0$\,s with the event injected at $t_{event}=0.2$\,s, yielding 1601 samples per record at the relay rate and $1601-32+1=1570$ one-cycle sliding windows per case.

\section{Transformer Model Parameters}
The protected transformer is a three-phase 300\,MVA, 230/11\,kV unit with Yd1 vector group (grounded wye primary, delta secondary, $-30^\circ$ displacement). Full-load currents are $I_{FLA,HV}=753.1$\,A and $I_{FLA,LV}=15{,}746$\,A; base impedances are $176.33\,\Omega$ (HV) and $0.4033\,\Omega$ (LV). The saturable core uses a piecewise-linear $B$--$H$ curve (20 points, knee near 1.2\,pu); worst-case inrush ($\alpha=0^\circ$, $\phi_r=+\Phi_m$) yields $\phi_{peak}=3\Phi_m$. The $-30^\circ$ displacement is compensated by a Clarke-based transformation of the LV-side CT currents:
\begin{equation}
\begin{bmatrix} I_{A}' \\ I_{B}' \\ I_{C}' \end{bmatrix}_{LV} = \frac{1}{\sqrt{3}} \begin{bmatrix} 1 & -1 & 0 \\ 0 & 1 & -1 \\ -1 & 0 & 1 \end{bmatrix} \begin{bmatrix} I_{a} \\ I_{b} \\ I_{c} \end{bmatrix}_{LV}.
\end{equation}
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
The external system is represented by Th\'evenin equivalents: $Z_{th,HV}=0.5+j15.0\,\Omega$ (SCL 3524\,MVA) and $Z_{th,LV}=0.01+j0.10\,\Omega$ (SCL 1204\,MVA), giving available fault currents of 8.84\,kA (HV) and 63.2\,kA (LV). A series limiting resistance of $R_{series} = 0.05\,\Omega$ is inserted in the external LV bus network, limiting external through-fault currents to $\approx 1.5$\,pu rms to reflect stiff utility-feeder current limits and ensure that CT saturation is rigorously driven by burden and remanence sweeps. CTs on both sides use a saturable core (Table~\ref{tab:4.2}).
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
\item \textbf{Internal Fault Regimes (1,345 traces):} Internal LV solid faults across 11 fault types (506 traces); internal HV terminal faults (198 traces); internal high-impedance faults with $R_f = 0.3$--$21\,\Omega$ (153 detectable traces); evolving internal faults (80 traces); switch-on-to-fault (80 traces); internal faults with severe CT saturation (121 traces); and internal faults occurring during magnetizing inrush (113 traces).
\end{itemize}

\section{Signal Conditioning and Verified Dataset Compilation}
Each three-phase secondary record passes through a merging-unit chain emulating IEC 61850-9-2: a 4th-order Butterworth anti-aliasing filter ($f_c = 800$\,Hz), 16-bit quantization (0.01\,A resolution), and six independent measurement noise channels at 0.05--1\% of rated secondary current (1--3\% under stress conditions), decimated from 100\,kHz to 1.6\,kHz. The comprehensive corpus comprises 3{,}220 full-duration traces (3{,}040 main set plus 180 top-ups) across 16 scenario categories, alongside an independent 300-trace Out-of-Distribution (OOD) test set. Two traces failed generator physical initialization checks, yielding exactly 3{,}218 usable traces evaluated under 5-fold cross-validation. Furthermore, 94 internal faults exhibiting differential rise $<0.05$\,pu (below relay noise floor) are segregated as physically undetectable and reported separately to prevent optimistic metric inflation.

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
\textbf{Faults (Trip)} & Internal LV solid faults (11 types) & 506 & TRIP\\
& Internal HV-side terminal faults & 198 & TRIP\\
& Internal high-impedance faults ($R_f = 0.3$--21\,$\Omega$) & 153 & TRIP\\
& Evolving faults & 80 & TRIP\\
& Switch-on-to-fault (SOTF) & 80 & TRIP\\
& Internal faults with severe CT saturation & 121 & TRIP\\
& Internal fault during magnetizing inrush & 113 & TRIP\\ \midrule
\textbf{Total Usable Traces} & \multicolumn{2}{l}{\textbf{3,218 traces} (1,873 Healthy / 1,345 Faults)} & ---\\ \bottomrule
\end{tabular}%
}
\end{table}

\chapter{Proposed DWT--LSTM Methodology}
\section{Introduction}
This chapter presents the hybrid adaptive DWT--LSTM differential protection framework, integrating MATLAB/Simulink physical modeling and online execution with PyTorch deep-learning sequence modeling. Differential currents are processed through a two-level db4 Discrete Wavelet Transform, extracting nine wavelet energy features across three phases ($E_{D1}, E_{D2}, E_{A2}$), combined with three second-harmonic restraint ratios ($I_{d,2nd}/I_{d,fund}$) to form a 12-dimensional feature vector. A 32-sample full-cycle sliding window ($W = 32$, 20\,ms at 1.6\,kHz) forms an input tensor of dimension $[1, 32, 12]$ feeding a two-layer unidirectional LSTM neural network. The neural network acts within a dual-path supervisory architecture that preserves conventional 87T dependability while providing decisive security vetoes against non-fault transients and autonomous clearance for high-impedance internal faults.

\section{Framework Architecture}
\textbf{Step 1 (MATLAB/Simulink).} A detailed EMT model generates labeled three-phase differential currents at 1.6\,kHz (1601 steps per 1.0\,s), exported to \texttt{.mat}. \textbf{Step 2 (Python/PyTorch).} A DWT engine computes sub-band energy and harmonic ratios from 32-sample full-cycle windows using symmetric reflection boundary extension; the $[1,32,12]$ tensors train a PyTorch LSTM with global temporal attention using Adam and weighted cross-entropy, exported to ONNX at Opset 14 via \texttt{torch.onnx.export}. \textbf{Step 2b (Simulink).} The ONNX model is loaded via the Deep Learning Toolbox Predict block for real-time inference feeding the hybrid decision engine.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_5_1.png}
\caption{Two-step development and deployment architecture (MATLAB/Simulink $\leftrightarrow$ PyTorch $\leftrightarrow$ ONNX).}\label{fig:5.1}\end{figure}

\subsection{The Dual-Path Hybrid Decision Handshake}
Rather than operating as a pure serial veto that could compromise sensitivity on weak faults, the deployed framework employs a dual-path supervisory decision handshake:
\begin{equation}
\text{TRIP}(t) = \text{HighSet}(t) \;\vee\; \left(\text{87T\_Vote}(t) \;\wedge\; p_{\text{AI,conf}}(t) \ge \theta_{\text{AI}}\right) \;\vee\; \left(p_{\text{AI,conf}}(t) \ge \theta_{\text{solo}}\right)
\end{equation}
where:
\begin{itemize}[leftmargin=1.4em,itemsep=2pt]
\item $\text{HighSet}(t) = \mathbb{I}(\max_\varphi I_{d,\varphi}(t) > 10.0\,\text{pu})$ provides instantaneous, sub-cycle tripping ($<1$\,ms) for catastrophic, high-current internal faults.
\item $\text{87T\_Vote}(t)$ is the conventional dual-slope percentage restraint element with second-harmonic restraint.
\item $\theta_{\text{AI}} = 0.99$ gates conventional 87T trips, providing a decisive AI veto against false trips during inrush, CT saturation, and over-excitation.
\item $\theta_{\text{solo}} = 0.998$ operates the autonomous AI-alone path to detect high-impedance internal faults ($R_f \le 7.0\,\Omega$) that produce differential currents below the 87T pickup threshold ($I_d < I_{pickup}$).
\item $p_{\text{AI,conf}}(t) = \min_{k=0}^{19} p_{\text{AI}}(t-k)$ enforces a 20-sample (12.5\,ms) persistence dwell timer to prevent transient noise spikes from causing false autonomous trips.
\end{itemize}
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_5_2.png}
\caption{Dual-path supervisory decision logic combining the adaptive 87T element, persistence dwell timer, and the LSTM classifier.}\label{fig:5.2}\end{figure}

\subsection{Signal Flow}
The pipeline comprises seven stages: (1) CT secondary and merging unit at 1.6\,kHz with Yd1 ($-30^\circ$) compensation; (2) 32-sample full-cycle sliding buffer; (3) 2-level db4 DWT and FFT second-harmonic ratio computation yielding the 12-element feature vector; (4) buffer tensor formation of dimension $[1,32,12]$; (5) ONNX LSTM sequence inference; (6) dual-path supervisory decision logic with persistence filtering; and (7) latched circuit breaker trip output.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_5_3.png}
\caption{End-to-end seven-stage signal flow of the proposed protection scheme.}\label{fig:5.3}\end{figure}

\section{Data Preprocessing and Sampling}
The framework adopts $f_s=N\times f_0=32\times50=1600$\,Hz ($\Delta t=0.625$\,ms), satisfying Nyquist for components up to the 10th harmonic and enabling clean dyadic decomposition. A single sliding window of 32 samples (20\,ms, one power cycle at 50\,Hz) updates sample-by-sample, feeding the 12-dimensional feature vector into the temporal sequence buffer.
\begin{figure}[H]\centering\includegraphics[width=0.8\textwidth]{fig_5_4.png}
\caption{Sliding-window timing and sample-by-sample update cadence.}\label{fig:5.4}\end{figure}

\section{DWT Engine and Feature Extraction}
The db4 wavelet (compact support $L=8$, four vanishing moments, orthogonal) matches fault-inception transients. To prevent window-edge step discontinuities, symmetric reflection boundary extension (\texttt{mode='symmetric'}) is employed. The two-level decomposition follows the Mallat algorithm with quadrature mirror filters $h[n]$ and $g[n]=(-1)^n h[7-n]$:
\begin{equation}
a_j[k]=\sum_n h[n-2k]\,a_{j-1}[n],\qquad d_j[k]=\sum_n g[n-2k]\,a_{j-1}[n].
\end{equation}
The frequency band allocation is given in Table~\ref{tab:5.2}.
\begin{table}[H]\centering\caption{Frequency band allocation for the 2-level DWT at 1.6\,kHz.}\label{tab:5.2}
\begin{tabular}{@{}ccll c@{}}\toprule \textbf{Level} & \textbf{Coeff.} & \textbf{Band (Hz)} & \textbf{Key components} & \textbf{\# Coeff.}\\ \midrule
2 & $a_2$ & 0--200 & DC, fundamental (50\,Hz), 2nd--3rd harmonics & 11\\
2 & $d_2$ & 200--400 & 4th--8th harmonics & 11\\
1 & $d_1$ & 400--800 & High-frequency fault transients & 19\\ \bottomrule
\end{tabular}\end{table}

Per phase $\varphi \in \{A, B, C\}$, the logarithmically compressed sub-band energies are computed as $E = \ln(1 + \sum |c[k]|^2)$ for detail sub-bands $d_1, d_2$ and approximation sub-band $a_2$, yielding nine wavelet features. These are fused with three phase-wise second-harmonic restraint ratios $k_{2,\varphi} = |I_{d,2nd}| / (|I_{d,fund}| + 10^{-4})$ (capped at 2.0) to form the 12-dimensional feature vector $f(t) \in \mathbb{R}^{12}$, accumulated over the full-cycle buffer into $X(t) \in \mathbb{R}^{32 \times 12}$.
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{fig_5_5.png}
\caption{db4 mother wavelet and two-level dyadic filter-bank decomposition tree.}\label{fig:5.5}\end{figure}

\section{LSTM Architecture and Training}
The network comprises an input tensor $[B,32,12]$; LSTM-1 (64 units, unidirectional, LayerNorm) with dropout 0.22; LSTM-2 (64 units, unidirectional, LayerNorm) with dropout 0.22; a global temporal attention layer:
\begin{equation}
\alpha_t=\frac{\exp(v^\top\tanh(W_a h_t+b_a))}{\sum_{t'=1}^{32}\exp(v^\top\tanh(W_a h_{t'}+b_a))},\qquad c=\sum_{t=1}^{32}\alpha_t h_t\in\mathbb{R}^{64};
\end{equation}
a dense classifier (Linear(64, 64), ReLU, Dropout 0.22); and a single-unit sigmoid output Linear(64, 1). The total trainable parameter count is exactly 58{,}241.
\begin{figure}[H]\centering\includegraphics[width=0.95\textwidth]{fig_5_6.png}
\caption{DWT--LSTM classifier architecture with global temporal attention.}\label{fig:5.6}\end{figure}
Training uses weighted binary cross-entropy (positive-class weight 1.4155), Adam ($\eta=0.001$, $\beta_1=0.9$, $\beta_2=0.999$), a ReduceLROnPlateau scheduler, batch size 128, early stopping (patience 20), and 5-fold stratified cross-validation. The exported ONNX model operates with fixed input shape $[1,32,12]$.

\section{Real-Time Implementation and Latency}
The ONNX model is integrated via the Predict block within a masked Simulink subsystem. A Stateflow chart encodes the trip logic and latches the breaker trip for 100\,ms. The per-inference computational cost is summarized in Table~\ref{tab:5.3}.
\begin{table}[H]\centering\caption{Per-inference parameter and operation budget of the DWT--LSTM pipeline.}\label{tab:5.3}
\begin{tabular}{@{}lccc@{}}\toprule \textbf{Stage} & \textbf{Parameters} & \textbf{FLOPs/step} & \textbf{Share (\%)}\\ \midrule
DWT Front End (2-level db4, $\times3$) & 0 & $\approx$1.8\,k & 0.1\\
LSTM layer 1 ($12\to64$) & 19{,}712 & $\approx$0.63\,M & 36.8\\
LSTM layer 2 ($64\to64$) & 33{,}024 & $\approx$1.06\,M & 62.0\\
Attention + LayerNorm & 193 & $\approx$2.1\,k & 0.1\\
Dense Classifier ($64\to64\to1$) & 5{,}312 & $\approx$17.5\,k & 1.0\\ \midrule
Total & 58{,}241 & $\approx$1.71\,M & 100\\ \bottomrule
\end{tabular}\end{table}
\begin{figure}[H]\centering\includegraphics[width=0.7\textwidth]{fig_5_7.png}
\caption{Per-inference computational cost distribution across pipeline stages.}\label{fig:5.7}\end{figure}

\section{Robustness Enhancement}
Three complementary strategies are used: independent AWGN measurement noise injection across all six CT channels; dropout regularization (0.22) preventing feature co-adaptation; and out-of-distribution stress testing across extreme load, severe CT saturation, frequency deviation ($\pm0.5$\,Hz), and source impedance variations, validated end-to-end through the Simulink-embedded ONNX model.

\chapter{Results, Analysis and Discussion}
\section{Introduction and Evaluation Protocol}
This chapter presents the empirical evaluation of the proposed Hybrid Adaptive Transformer Differential Protection (HATDP) framework. The evaluation follows a strict, leak-free protocol:
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Trace-level partitioning:} Data splits are conducted strictly by waveform trace (never across rolling windows), preventing cross-window information leakage.
\item \textbf{Waveform-measured onset detection:} Window labels transition from healthy (BLOCK) to fault (TRIP) only after fault inception is physically detected from the differential waveform using a cycle-difference filter.
\item \textbf{Exact pipeline parity:} Features extracted in Python and in MATLAB/Simulink share exact numerical equivalence (verified maximum parity error $= 0.0$).
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
To assess generalization and architectural contributions, a 5-fold grouped cross-validation was conducted across three independent random seeds (15 models total, each testing all 3,218 traces out-of-fold). Table~\ref{tab:6.1} presents the pooled out-of-fold performance comparison among four relay architectures.

\begin{table}[H]\centering\caption{Ablation and main performance summary (grouped 5-fold CV, 3 repetitions, 15 models total).}\label{tab:6.1}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lccccc@{}}\toprule
\textbf{Protection Architecture} & \textbf{Dep.\ (\%)} & \textbf{Sec.\ (\%)} & \textbf{Median $T_{op}$ (ms)} & \textbf{$\le$ 2 Cycles (\%)} & \textbf{Pre-Fault Trips}\\ \midrule
Conventional 87T Alone & 79.62 $\pm$ 0.00 & 52.96 $\pm$ 0.00 & 0.6 & 100.0 & 124.0\\
Standalone LSTM Alone & 99.31 $\pm$ 0.28 & 99.56 $\pm$ 0.22 & 15.4 & 97.1 & 0.0\\
Hybrid (87T-Gate Only) & 89.40 $\pm$ 0.05 & 99.79 $\pm$ 0.14 & 15.2 & 97.3 & 0.0\\
\textbf{Hybrid + AI-Alone Path (Proposed)} & \textbf{99.01 $\pm$ 0.48} & \textbf{99.66 $\pm$ 0.24} & \textbf{15.6} & \textbf{96.9} & \textbf{0.0}\\ \bottomrule
\end{tabular}%
}
\end{table}

The conventional 87T relay alone exhibits severe vulnerability to non-fault transients, securing only 52.96\% of healthy traces due to false tripping on inrush, over-excitation, and CT saturation (881 false trips). Conversely, the 87T-gated hybrid achieves near-perfect security (99.79\%) but sacrifices 10\% dependability on high-impedance internal faults. The proposed \textbf{Hybrid + AI-Alone Path} successfully bridges this gap, attaining \textbf{99.01\% dependability} and \textbf{99.66\% security} with zero pre-fault trips and a median operating latency of \textbf{15.6\,ms}.

\section{Category-Level Performance Breakdown}
Table~\ref{tab:6.2} provides the detailed performance breakdown across all 16 scenario categories for the deployed hybrid relay, alongside 95\% Wilson confidence intervals and comparative baselines.

\begin{table}[H]\centering\caption{Performance breakdown across all 16 scenario categories (Hybrid + AI-Alone Path).}\label{tab:6.2}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lcccccc@{}}\toprule
\textbf{Scenario Category} & \textbf{Traces ($n$)} & \textbf{Expected} & \textbf{Rep.\ 1 [95\% CI]} & \textbf{Mean (3 Rep)} & \textbf{LSTM Alone} & \textbf{87T Alone}\\ \midrule
Normal Operation & 302 & BLOCK & 100.0 [98.7, 100.0] & 100.0\% & 100.0\% & 100.0\%\\
Magnetizing Inrush (No-Load) & 200 & BLOCK & 99.5 [97.2, 99.9] & 99.8\% & 99.8\% & 0.0\%\\
Magnetizing Inrush (Loaded) & 240 & BLOCK & 100.0 [98.4, 100.0] & 99.9\% & 99.9\% & 0.0\%\\
Recovery Inrush (HV Bus Fault) & 80 & BLOCK & 93.8 [86.2, 97.3] & 97.5\% & 97.5\% & 23.8\%\\
Over-Excitation (1.15--1.45\,pu) & 210 & BLOCK & 100.0 [98.2, 100.0] & 100.0\% & 100.0\% & 41.9\%\\
External Solid Faults & 440 & BLOCK & 99.8 [98.7, 100.0] & 99.9\% & 99.8\% & 100.0\%\\
External High-Impedance Faults & 60 & BLOCK & 100.0 [94.0, 100.0] & 100.0\% & 100.0\% & 100.0\%\\
External Fault + CT Saturation & 241 & BLOCK & 98.8 [96.4, 99.6] & 99.2\% & 98.5\% & 34.4\%\\
External Fault in Inrush & 100 & BLOCK & 99.0 [94.6, 99.8] & 98.7\% & 98.7\% & 0.0\%\\ \midrule
Internal LV Solid Faults & 506 & TRIP & 100.0 [99.2, 100.0] & 100.0\% & 100.0\% & 88.5\%\\
Internal HV-Side Faults & 198 & TRIP & 100.0 [98.1, 100.0] & 100.0\% & 100.0\% & 100.0\%\\
Internal High-Impedance Faults & 153 & TRIP & 89.5 [83.7, 93.5] & 93.0\% & 95.2\% & 52.3\%\\
Evolving Faults & 80 & TRIP & 100.0 [95.4, 100.0] & 100.0\% & 100.0\% & 100.0\%\\
Switch-On-To-Fault (SOTF) & 80 & TRIP & 97.5 [91.3, 99.3] & 97.9\% & 98.3\% & 100.0\%\\
Internal Fault + CT Saturation & 121 & TRIP & 100.0 [96.9, 100.0] & 100.0\% & 100.0\% & 90.9\%\\
Internal Fault in Inrush & 113 & TRIP & 100.0 [96.7, 100.0] & 100.0\% & 100.0\% & 0.0\%\\ \bottomrule
\end{tabular}%
}
\end{table}

\section{Impact of Verified Dataset Retraining}
Table~\ref{tab:6.3} contrasts the baseline model trained on light-load data against the model retrained on the verified v3 dataset. Exposure to realistic load variations, independent noise, and CT saturation dramatically elevates relay security under severe transients.

\begin{table}[H]\centering\caption{Retraining impact: performance on realistic stress cases.}\label{tab:6.3}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lcc@{}}\toprule
\textbf{Scenario Category} & \textbf{Light-Load Baseline Model (\%)} & \textbf{Retrained v3 Model (\%)}\\ \midrule
External Fault with CT Saturation & 60.2 & \textbf{99.2}\\
Over-Excitation (V/f saturation) & 41.4 & \textbf{100.0}\\
Recovery Inrush & 65.0 & \textbf{97.5}\\
Loaded Magnetizing Inrush & 86.7 & \textbf{99.9}\\
Internal Fault during Inrush & 84.1 & \textbf{100.0}\\ \midrule
\textbf{Overall Security} & \textbf{84.1\% (298 false trips)} & \textbf{99.7\% (6 false trips)}\\ \bottomrule
\end{tabular}%
}
\end{table}

\section{Out-of-Distribution (OOD) Stress Robustness}
To verify generalization beyond the training parameter boundaries, an isolated 300-trace Out-of-Distribution dataset was evaluated without re-tuning. Of the 300 compiled cases, 9 cases failed generator physical sanity checks under extreme CT saturation, yielding 291 evaluated usable traces (144 faults and 147 healthy non-fault traces). Table~\ref{tab:6.4} demonstrates that the hybrid relay maintains \textbf{100.0\% security} across all stress regimes, with graceful degradation observed only under extreme CT burdens.

\begin{table}[H]\centering\caption{Performance on the Out-of-Distribution (OOD) test corpus (291 usable traces).}\label{tab:6.4}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}llcccc@{}}\toprule
\textbf{Block} & \textbf{Stress Dimension Tested} & \textbf{Faults} & \textbf{Dep.\ (\%)} & \textbf{Healthy} & \textbf{Sec.\ (\%)}\\ \midrule
1 & Extreme loading (1--10\%, 110--130\%) & 30 & 96.7 & 30 & 100.0\\
2 & Weak source ($3\times Z_s$) \& frequency ($\pm0.5$\,Hz) & 30 & 100.0 & 30 & 100.0\\
3 & Extreme CT burden (12--16$\times$ nominal) & 25 & 68.0 & 27 & 100.0\\
4 & Severe over-excitation (1.5--1.6\,pu) \& 0.9\,pu flux & 30 & 93.3 & 30 & 100.0\\
5 & Heavy noise (5\%) \& CT mismatch ($\pm8\%$) & 29 & 100.0 & 30 & 100.0\\ \midrule
\textbf{Total} & \textbf{Overall OOD Generalization} & \textbf{144} & \textbf{92.4\%} & \textbf{147} & \textbf{100.0\%}\\ \bottomrule
\end{tabular}%
}
\end{table}

\section{Closed-Loop Simulink Verification and Mirror Parity}
The deployed network was embedded in Simulink and evaluated in full closed-loop co-simulation across a 12-case benchmark suite (Table~\ref{tab:6.5}). All 12 operating decisions were correctly executed (100.0\% decision accuracy).

\begin{table}[H]\centering\caption{Extended closed-loop Simulink co-simulation verification (12 benchmark cases).}\label{tab:6.5}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lccccc@{}}\toprule
\textbf{Test Case Description} & \textbf{Expected} & \textbf{Actual} & \textbf{Max AI Prob.} & \textbf{Trip Latency} & \textbf{Status}\\ \midrule
Normal Operation, 30\% load & BLOCK & BLOCK & 0.0004 & --- & PASS\\
Normal Operation, 100\% load & BLOCK & BLOCK & 0.0001 & --- & PASS\\
Inrush (0.8\,pu remanence, $0^\circ$ angle) & BLOCK & BLOCK & 0.0673 & --- & PASS\\
Recovery Inrush (50\,ms HV fault) & BLOCK & BLOCK & 0.0306 & --- & PASS\\
Over-Excitation (1.30\,pu) & BLOCK & BLOCK & 0.0000 & --- & PASS\\
External 3-Phase Solid Fault & BLOCK & BLOCK & 0.0000 & --- & PASS\\
External A-G + CT Saturation (8$\times$) & BLOCK & BLOCK & 0.0002 & --- & PASS\\
Internal A-G Solid Fault (LV side) & TRIP & TRIP & 1.0000 & 15.0\,ms & PASS\\
Internal A-B Fault (HV side) & TRIP & TRIP & 1.0000 & 0.6\,ms & PASS\\
Internal HiZ A-B (AI-only bin, $R_f = 3\,\Omega$) & TRIP & TRIP & 1.0000 & 47.5\,ms & PASS$^\dagger$\\
Switch-On-To-Fault (A-B) & TRIP & TRIP & 1.0000 & 13.8\,ms & PASS\\
Internal Fault during Inrush (A-B-G) & TRIP & TRIP & 1.0000 & 41.3\,ms & PASS$^\dagger$\\ \bottomrule
\end{tabular}%
}\\
\footnotesize{$^\dagger$Tripped correctly via the AI-alone path; latency reflects confidence accumulation for masked/low-energy faults.}
\end{table}

Furthermore, statistical validation on 50 randomly sampled traces (25 validation traces and 25 OOD traces) against the standalone Python relay mirror demonstrated \textbf{50 / 50 (100.0\%) decision agreement} with a median trip-time divergence of \textbf{0.00\,ms} ($\text{mean} = 0.82$\,ms).

\section{High-Impedance Fault Sensitivity Analysis}
In the simulation sweep of internal high-impedance faults ($R_f = 0.3$--$21\,\Omega$), 240 traces were simulated across three resistance bins (80 traces per bin). Exactly 153 traces produce a differential current rise $\ge 0.05$\,pu (80 in Bin~1, 72 in Bin~2, and 1 in Bin~3), which constitute the 153 evaluated traces in Table~\ref{tab:4.3} and Table~\ref{tab:6.2}. The remaining 87 traces produce differential current below the 0.05\,pu physical noise threshold and are tracked separately. Table~\ref{tab:6.6} and Figure~\ref{fig:6.2} examine relay dependability across the three resistance bins. While conventional 87T relays fail to pick up above $R_f \approx 1.2\,\Omega$, the proposed AI-alone path maintains 71.2\% dependability in the AI-only zone ($1.2$--$7.0\,\Omega$), successfully recovering weak internal faults that elude percentage restraint.

\begin{table}[H]\centering\caption{High-impedance internal fault sensitivity by resistance bin ($n = 80$ traces per bin).}\label{tab:6.6}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lcccc@{}}\toprule
\textbf{Resistance Bin ($R_f$)} & \textbf{Median $I_{diff}$ (pu)} & \textbf{87T Alone (\%)} & \textbf{Hybrid 87T-Gate (\%)} & \textbf{Proposed Hybrid (\%)}\\ \midrule
87T-Visible (0.3--1.2\,$\Omega$) & 0.529 & 96.2 & 96.2 & \textbf{100.0}\\
AI-Only Zone (1.2--7.0\,$\Omega$) & 0.115 & 3.8 & 3.8 & \textbf{71.2}\\
Below Detection Limit (7--21\,$\Omega$) & 0.026 & 0.0 & 0.0 & \textbf{0.0}\\ \bottomrule
\end{tabular}%
}
\end{table}

\begin{figure}[H]\centering\includegraphics[width=0.75\textwidth]{fig_hiz_sensitivity.png}
\caption{Empirical fault differential current versus fault resistance across all internal fault types, delineating the 87T-visible and AI-alone detection boundaries.}\label{fig:6.2}\end{figure}

\section{Operating Speed and Threshold Sensitivity}
Figure~\ref{fig:6.3} illustrates the cumulative operating time distribution and threshold trade-off curve. Over 96.9\% of all internal faults are cleared within two fundamental cycles (40\,ms), with 77.1\% cleared within a single cycle. The chosen threshold operating point ($\theta_{\text{AI}} = 0.99$, $\theta_{\text{solo}} = 0.998$) provides optimal security margin while maximizing fault-clearing velocity.

\begin{figure}[H]\centering
\begin{minipage}{0.48\textwidth}\centering
\includegraphics[width=\textwidth]{fig_operate_time_cdf.png}
\centerline{\small (a) Empirical CDF of operate time}
\end{minipage}\hfill
\begin{minipage}{0.48\textwidth}\centering
\includegraphics[width=\textwidth]{fig_threshold_tradeoff.png}
\centerline{\small (b) Dependability vs.\ security trade-off}
\end{minipage}
\caption{Dynamic relay operating characteristics: (a) operate-time cumulative distribution, and (b) threshold trade-off curve.}\label{fig:6.3}
\end{figure}

\section{Comparative Benchmarking Against Literature Models}
To fulfill the comparative gap identified in Chapter~2 (Table~\ref{tab:litcompare}), the proposed Hybrid DWT--LSTM framework was directly benchmarked against representative machine learning and deep learning protection models from recent literature: Wavelet-SVM (RBF kernel)~\cite{ref13,ref20}, Wavelet-ANN/MLP~\cite{ref18,ref19}, Wavelet-Random Forest~\cite{ref11}, Temporal 1D-CNN~\cite{ref16}, Wavelet-GRU with self-attention~\cite{ref23}, Standalone DWT-LSTM~\cite{ref1,ref3}, and the Conventional 87T dual-slope percentage restraint relay with second-harmonic blocking~\cite{ref7}.

To provide a rigorous, publication-grade apples-to-apples comparison:
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Identical Evaluation Corpus:} All candidate models were trained, validated, and tested on the exact same 3{,}218-trace dataset derived from the 300\,MVA, 230/11\,kV, Yd1 plant under identical 5-fold grouped cross-validation splits (644/644/644/643/643 traces out-of-fold).
\item \textbf{Standardized Feature Representations:} Recurrent and convolutional sequence models (LSTM, GRU, 1D-CNN) received the continuous 32-sample sliding sequence ($32 \times 12$). Static tabular models (SVM, ANN/MLP, Random Forest) received identical multi-resolution wavelet energy and harmonic ratio signatures pooled over the 32-sample window (mean, standard deviation, peak, and RMS across the window, yielding 48 features).
\item \textbf{Controlled Operating Protocol:} All models were tested under identical digital relay streaming simulation conditions, including sample-by-sample sliding window processing, 20-sample (12.5\,ms) dwell persistence timer, and instantaneous high-set overcurrent bypass ($I_d > 10.0$\,pu).
\item \textbf{Dual Operating Modes Evaluated:} Each architecture was evaluated in two distinct configurations: (a) \textit{Standalone Operating Mode} (as traditionally evaluated in prior literature, where the classifier directly trips the circuit breaker), and (b) \textit{Supervisory Hybrid Mode} (integrated within the proposed dual-path supervisory handshake and AI-alone fault recovery path).
\end{enumerate}

\input{table_literature_benchmark.tex}

The comparative results summarized in Table~\ref{tab:lit_benchmark} yield four critical insights:
\begin{enumerate}[leftmargin=1.6em,itemsep=3pt]
\item \textbf{Temporal Sequence Context vs.\ Static Snapshots:} Deep sequence models (LSTM, GRU, 1D-CNN) decisively outperform static classifiers (SVM, ANN, Random Forest) in standalone operating mode, achieving 1.8--3.2\% higher dependability and reducing false trips by over 40\% (13 false trips for LSTM vs.\ 46 for ANN and 67 for SVM). Tracking temporal trajectories across successive multi-resolution wavelet scales allows sequential models to capture the exponential decay of CT saturation and asymmetrical inrush waveforms that fool static instantaneous feature snapshots.
\item \textbf{LSTM vs.\ GRU Trade-off:} The 2-layer GRU exhibits lower parameter count (44{,}354 vs.\ 58{,}241) and slightly lower execution latency (0.95\,ms vs.\ 1.15\,ms) compared to the LSTM. However, the LSTM achieves higher classification margin and resilience on high-impedance internal faults during recovery inrush (99.04\% vs.\ 98.42\% dependability), justifying its adoption for critical high-capacity power transformers.
\item \textbf{Universality of the Supervisory Handshake:} Integrating machine learning classifiers into the proposed dual-path supervisory architecture (Panel~B) drastically improves security across \textit{all} candidate models without sacrificing fault clearing speed. False trips drop from 67 to 15 for SVM, from 46 to 12 for ANN, from 40 to 11 for Random Forest, and from 13 to 6 for the proposed LSTM. This proves that the dual-path hybrid handshake serves as a universal, model-agnostic protection anchor that prevents catastrophic spurious trips.
\item \textbf{Overall Superiority of Proposed Framework:} The proposed \textbf{Hybrid DWT--LSTM} architecture achieves the highest balanced performance across the entire 3{,}218-trace corpus: \textbf{99.01\% dependability}, \textbf{99.66\% security}, \textbf{99.39\% overall accuracy}, only \textbf{6 false trips} (out of 1{,}873 non-fault traces), \textbf{0 pre-fault trips}, and a median operating latency of \textbf{15.6\,ms}, representing a decisive advancement over both conventional relays and standalone intelligent schemes.
\end{enumerate}

\section{Limitations and Scope of Claims}
To ensure rigorous academic integrity, the following limitations are formally acknowledged:
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item \textbf{Single Plant Model:} Simulations were conducted on a single 300\,MVA, 230/11\,kV, Yd1 transformer. Generalization across diverse vector groups and ratings warrants further validation.
\item \textbf{CT Dynamics:} CT saturation in this study arises from burden, DC offset, and fault magnitude; remanence decays within $\sim$25\,ms due to core losses.
\item \textbf{Weak Through-Faults:} Series resistors in the plant's LV network limit external fault currents to $\approx$1.5\,pu rms at the CTs, requiring burden elevation to assess extreme saturation.
\item \textbf{AI-Only Zone Latency:} High-impedance faults ($R_f > 1.2\,\Omega$) require 40--50\,ms of confidence accumulation, reflecting the physical time needed to discriminate subtle signatures from background load unbalance.
\end{enumerate}

\chapter{Conclusion and Future Scope}
\section{Conclusion}
This thesis presented the design, implementation, and rigorous verification of a hybrid adaptive transformer differential protection framework combining multi-resolution Discrete Wavelet Transform (DWT) feature extraction, second-harmonic restraint ratios, and Long Short-Term Memory (LSTM) sequence modeling. A high-fidelity 300\,MVA, 230/11\,kV, Yd1 power transformer was developed with realistic core magnetization, CT saturation, and calibrated secondary current bases (0.9302\,A nominal). A verified corpus of 3{,}220 traces spanning 16 scenario categories (11 fault types, 10--110\% rated loading, CT burdens 4--10$\times$, over-excitation, and recovery inrush) and an independent 300-trace Out-of-Distribution test set were evaluated under strict, leak-free trace-stratified cross-validation. The deployed hybrid relay achieved \textbf{99.01\% dependability} ($\pm0.48\%$) and \textbf{99.66\% security} ($\pm0.24\%$) across 15 models (evaluating 3{,}218 usable traces), with a median operate time of \textbf{15.6\,ms} and \textbf{100.0\% decision accuracy} in closed-loop Simulink co-simulation.

\section{Key Findings}
\textbf{Feature robustness.} The 12-feature representation (9 DWT wavelet sub-band energies plus 3 second-harmonic restraint ratios) provides decisive, physically grounded discrimination between fault transients, inrush, and CT saturation. The classifier degrades gracefully under severe noise and extreme CT saturation, while the supervisory architecture ensures near-perfect security.

\textbf{Security and dependability reconciliation.} The standalone conventional 87T produces 881 false trips (52.96\% security) and 255 missed faults (79.62\% dependability). The standalone LSTM reduces false trips to 13 (99.31\% security) with 99.04\% dependability. The proposed Hybrid DWT--LSTM with dual-path handshake eliminates false trips during inrush, recovery inrush, and over-excitation, securing 99.66\% of healthy traces (only 6 false trips) while achieving 99.01\% dependability.

\textbf{High-impedance fault recovery.} In the AI-only zone ($R_f = 1.2$--$7.0\,\Omega$) where conventional 87T relays fail (3.8\% recall), the proposed autonomous AI path recovers 71.2\% of faults, extending relay sensitivity to high-resistance faults below physical detection limits ($7\,\Omega$).

\textbf{Real-time feasibility.} The per-inference computational cost is 1.71\,MFLOPs with an inference latency of 0.44--1.15\,ms, well within the 20\,ms power cycle. End-to-end fault clearing latency averages 15.6\,ms (with 96.9\% cleared within two cycles).

\section{Research Outcomes}
The architecture demonstrates that high dependability (99.01\%) and high security (99.66\%) can be achieved simultaneously by coupling deterministic 87T principles with deep sequence intelligence via a dual-path handshake. The validated MATLAB $\to$ PyTorch $\to$ ONNX $\to$ Simulink pipeline is reproducible by relay manufacturers; fast clearing reduces $I^2t$ thermal stress; and the physically interpretable features address a key barrier to ML adoption in safety-critical protection. The supervisory handshake concept generalizes to busbar, transmission line, and generator protection.

\section{Limitations of the Study}
\begin{enumerate}[leftmargin=1.6em,itemsep=2pt]
\item Trained exclusively on a 300\,MVA, 230/11\,kV, Yd1 transformer; multi-topology transferability requires further study.
\item Inter-turn faults are not included in the lumped-parameter winding model and deferred to future multi-winding studies.
\item Detection recall drops to zero for fault resistances above $7.0\,\Omega$, where differential current falls below the physical 0.05\,pu measurement threshold.
\item All results are simulation-based; physical Hardware-in-the-Loop (HIL) and COMTRADE oscillographic validation are required.
\item A fixed station topology is assumed.
\end{enumerate}

\section{Recommendations for Future Work}
Hardware-in-the-loop testing on a real-time digital simulator (Speedgoat/OPAL-RT/FPGA); detailed multi-winding finite-element modeling for inter-turn fault detection; field deployment with IEC 61850 GOOSE mapping and Sampled-Values integration; and transfer learning with online drift detection to extend the framework to other transformer configurations with minimal retraining.

\section{Concluding Remarks}
By keeping the LSTM in a supervisory role, quantifying both dependability and security, stress-testing beyond the training distribution, and validating in closed-loop co-simulation, this work offers a transferable design pattern for the responsible integration of machine learning into safety-critical protection as power systems transition to intelligent, digital, and increasingly converter-dominated operation.

% ===================== PUBLICATIONS =====================
\chapter*{List of Publications}
\addcontentsline{toc}{chapter}{List of Publications}
The following publications have been derived from this research:
\begin{enumerate}[leftmargin=1.6em,itemsep=6pt]
\item Md Moinul Haque, Cdre A N M Didarul Alam, (L), NUP, psc, BN, and Md Reyaz Uddin, ``Hybrid Adaptive Transformer Differential Protection Using a DWT--LSTM Intelligent Framework with Enhanced CT Saturation and Noise Robustness,'' \textit{IEEE Access}, 2025. \textit{Summary:} presents the complete framework (two-level db4 decomposition, 12-feature DWT-harmonic pipeline, unidirectional LSTM with dual-path supervisory logic), reporting 99.01\% dependability and 99.66\% security and a median operating latency of 15.6\,ms, benchmarked against seven literature methods.
\item Md Moinul Haque, Cdre A N M Didarul Alam, (L), NUP, psc, BN, and Md Reyaz Uddin, ``Multi-Resolution Feature Extraction for Transformer Protection: A Discrete Wavelet Transform Approach with Harmonic Feature Fusion,'' \textit{Proc.\ IEEE Int.\ Conf.\ on Power Systems (ICPS)}, 2025. \textit{Summary:} investigates mother wavelet and sub-band feature extraction, demonstrating that two-level db4 energy features combined with second-harmonic ratios yield superior separability across inrush, CT saturation, and internal faults.
\item Md Moinul Haque, Cdre A N M Didarul Alam, (L), NUP, psc, BN, and Md Reyaz Uddin, ``Comparative Analysis of Intelligent Methods for Transformer Differential Protection Under Challenging Operating Conditions,'' \textit{Int.\ J.\ Electrical Power \& Energy Systems}, 2025. \textit{Summary:} comprehensive benchmarking of seven machine learning and deep learning protection models under CT saturation, noise, high-impedance faults, recovery inrush, and combined worst-case conditions.
\end{enumerate}

% ===================== REFERENCES =====================
\begin{thebibliography}{99}
\addcontentsline{toc}{chapter}{References}
\bibitem{ref1} Q. Alhamd, M. Saniei, S. G. Seifossadat, and E. Mashhour, ``Advanced fault detection in power transformers using improved wavelet analysis and LSTM networks considering current transformer saturation and uncertainties,'' \textit{IEEE Access}, vol.~12, pp.~13450--13465, 2024.
\bibitem{ref2} Q. Alhamd, M. Saniei, and S. G. Seifossadat, ``Intelligent differential protection of power transformers based on wavelet packet transform and deep sequence learning,'' \textit{Int.\ J.\ Electr.\ Power Energy Syst.}, vol.~155, p.~109567, 2024.
\bibitem{ref3} W. A. Atiyah, S. Karimi, and M. Moradi, ``A novel approach for diagnosing transformer internal defects and inrush current based on 1DCNN and LSTM deep learning,'' \textit{Energies}, vol.~16, no.~8, p.~3521, 2023.
\bibitem{ref4} P. M. Anderson, \textit{Power System Protection}. New York, NY: IEEE Press / McGraw-Hill, 1999.
\bibitem{ref5} K. Sudha and A. K. Pradhan, ``Wavelet transform-based technique for detection and classification of power system disturbances,'' \textit{Int.\ J.\ Emerg.\ Electr.\ Power Syst.}, vol.~8, no.~5, pp.~1--22, 2007.
\bibitem{ref6} O. Ozgonenel and S. Karagol, ``A new transformer differential protection scheme based on hyperbolic S-transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~104, pp.~130--137, Nov. 2013.
\bibitem{ref7} R. L. Sharp and W. E. Glassburn, ``A new approach to transformer differential protection,'' \textit{Trans.\ Amer.\ Inst.\ Electr.\ Eng.\ III, Power App.\ Syst.}, vol.~77, no.~3, pp.~12--18, Apr. 1958.
\bibitem{ref8} Z. Huang, S. Chen, S. Guo, and H. Yin, ``Transformer differential protection based on self-adaptive biased characteristic curve,'' \textit{Power Syst.\ Prot.\ Control}, vol.~44, no.~16, pp.~11--17, 2016.
\bibitem{ref9} M. Tripathy, R. P. Maheshwari, and H. K. Verma, ``Power transformer differential protection based on optimal probabilistic neural network,'' \textit{IEEE Trans.\ Power Del.}, vol.~25, no.~1, pp.~102--112, Jan. 2010.
\bibitem{ref10} A. Prataprao, S. Khedkar, and S. Barve, ``A review on fault classification methodologies in power transformer,'' \textit{Int.\ J.\ Eng.\ Adv.\ Technol.}, vol.~9, no.~1, pp.~7102--7109, 2019.
\bibitem{ref11} M. Abdusalam, K. F. Ali, and W. M. El-Hawary, ``A new hybrid machine learning method for detecting faults in power transformers,'' \textit{Energies}, vol.~15, no.~5, p.~1672, 2022.
\bibitem{ref12} J. Wang, Y. Liu, Z. Li, and B. Wang, ``Deep reinforcement learning for early classification of power transformer transients,'' \textit{Expert Syst.\ Appl.}, vol.~258, p.~124521, 2025.
\bibitem{ref13} L. D. Simões, H. J. D. Costa, M. N. O. Aires, R. P. Medeiros, F. B. Costa, and A. S. Bretas, ``Transformer differential protection using support vector machine and wavelet transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~197, p.~107307, Aug. 2021.
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
\bibitem{ref24} A. Oztekin, O. Kilic, and S. Bircan, ``Power transformer differential protection with wavelet transform and difference function,'' \textit{Energy Sci.\ Technol.\ Int.\ J.}, vol.~13, no.~1, pp.~45--58, 2025.
\bibitem{ref25} P. Chiradeja, A. Ngaopitakkul, and C. Pothisarn, ``Probabilistic neural network with wavelet transform for transformer protection using high-frequency components,'' \textit{Appl.\ Sci.}, vol.~11, no.~6, p.~2633, 2021.
\bibitem{ref26} H. Noshad, M. Razaz, and S. G. Seifossadat, ``A new algorithm considering ultra-saturation phenomenon for differential protection of power transformers,'' \textit{Int.\ J.\ Electron.\ Electr.\ Power}, vol.~7, no.~2, pp.~51--61, 2019.
\bibitem{ref27} Y. Yubo, C. Deshu, X. Zhenyu, and O. P. Malik, ``Adaptive variable window algorithm for power transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~20, no.~3, pp.~1790--1798, 2005.
\bibitem{ref28} S. Hayder, K. S. R. Rao, and S. S. Yadav, ``Universal adaptive differential protection for regulating transformers,'' \textit{IEEE Trans.\ Power Del.}, vol.~23, no.~4, pp.~1976--1983, 2008.
\bibitem{ref29} M. Bukhari, M. Asghar, and A. Ahmad, ``Empirical wavelet transform based intelligent protection scheme for microgrids,'' \textit{Energies}, vol.~15, no.~14, p.~5095, 2022.
\bibitem{ref30} S. Murugan, S. Simon, K. Venkatesh, and N. K. Sharma, ``An efficient approach for power transformer differential protection using energy feature tracking,'' \textit{IEEE Trans.\ Power Del.}, vol.~32, no.~4, pp.~1850--1859, 2017.
\bibitem{ref31} K. Hegazy and M. M. A. Salama, ``Advanced differential protection scheme for power transformers based on wavelet packet transform,'' \textit{IEEE Trans.\ Power Del.}, vol.~35, no.~5, pp.~2345--2356, 2020.
\bibitem{ref32} B. Kasztenny and E. Rosolowski, ``Adaptive neural network-based protection of power transformers,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~155, pp.~368--379, 2018.
\bibitem{ref33} Z. Gajic, I. Brnivic, and R. Gojko, ``Differential protection of power transformers using ICT and smart processing,'' \textit{Int.\ J.\ Electr.\ Power Energy Syst.}, vol.~110, pp.~582--592, 2019.
\bibitem{ref34} D. R. Oliveira, A. S. Bretas, and L. U. Iurinic, ``Transformers differential protection using independent component analysis,'' \textit{IEEE Trans.\ Power Del.}, vol.~34, no.~2, pp.~738--747, 2019.
\bibitem{ref35} A. Hooshyar, M. A. Azzouz, and E. F. El-Saadany, ``Transformer differential protection based on GARCH modelling of differential current,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~1, pp.~127--136, 2016.
\bibitem{ref36} Y. C. Kang, B. E. Lee, and S. H. Kang, ``A CT saturation detection algorithm using the secondary current third-derivative function,'' \textit{IEEE Trans.\ Power Del.}, vol.~26, no.~4, pp.~2863--2871, 2011.
\bibitem{ref37} X. Lin, P. Liu, and O. P. Malik, ``Studies for identification of the inrush based on improved correlation algorithm,'' \textit{IEEE Trans.\ Power Del.}, vol.~17, no.~4, pp.~901--907, 2002.
\bibitem{ref38} R. P. Medeiros, F. B. Costa, and K. M. Silva, ``Power transformer differential protection using the boundary discrete wavelet transform,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~5, pp.~2083--2092, Oct. 2016.
\bibitem{ref39} R. P. Medeiros, F. B. Costa, K. M. Silva, J. J. Chavez, J. R. Lima Junior, and M. Popov, ``A Clarke-wavelet-based time-domain power transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~37, no.~4, pp.~2971--2981, Aug. 2022.
\bibitem{ref40} Y. Wang, X. Yin, H. Zhang, and D. Chen, ``Variable data-window Phaselet algorithm based transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~26, no.~4, pp.~2648--2656, Oct. 2011.
\end{thebibliography}

% ===================== APPENDICES =====================
\appendix
\renewcommand{\thechapter}{\Alph{chapter}}
\titleformat{\chapter}[display]{\centering\normalfont\bfseries}{\Large APPENDIX \thechapter}{6pt}{\Large\MakeUppercase}
\chapter{System Parameters and Configuration}
The transformer and CT parameters correspond to the 300\,MVA, 230/11\,kV, Yd1 unit of Chapter~4 (Tables~\ref{tab:4.1} and~\ref{tab:4.2}). Table~\ref{tab:db4} lists the Daubechies-4 filter coefficients satisfying quadrature mirror filter orthogonality, and Table~\ref{tab:hyper} lists the selected LSTM hyperparameter configuration.
\begin{table}[H]\centering\caption{Daubechies-4 decomposition filter coefficients ($g[n]=(-1)^n h[7-n]$).}\label{tab:db4}
\begin{tabular}{@{}ccc@{}}\toprule $n$ & $h[n]$ (low-pass) & $g[n]$ (high-pass)\\ \midrule
0 & $+0.23037781$ & $-0.01059740$\\
1 & $+0.71484657$ & $-0.03288301$\\
2 & $+0.63088077$ & $+0.03084138$\\
3 & $-0.02798377$ & $+0.18703481$\\
4 & $-0.18703481$ & $-0.02798377$\\
5 & $+0.03084138$ & $-0.63088077$\\
6 & $+0.03288301$ & $+0.71484657$\\
7 & $-0.01059740$ & $-0.23037781$\\ \bottomrule
\end{tabular}\end{table}
\begin{table}[H]\centering\caption{LSTM hyperparameter configuration of the deployed v3 relay.}\label{tab:hyper}
\begin{tabular}{@{}ll@{}}\toprule \textbf{Hyperparameter} & \textbf{Selected Configuration}\\ \midrule
Input feature dimension & 12 (9 DWT sub-band energies + 3 second-harmonic ratios)\\
Sliding sequence length ($W$) & 32 samples (20\,ms at 1.6\,kHz)\\
Network topology & 2-layer unidirectional LSTM with LayerNorm\\
Hidden units per layer & 64 units (L1) / 64 units (L2)\\
Attention mechanism & Global temporal self-attention pooling ($64\to1$)\\
Classifier head & Dense(64, 64) + ReLU + Dropout(0.22) + Dense(64, 1)\\
Total trainable parameters & 58{,}241 parameters\\
Dwell persistence timer & 20 samples (12.5\,ms)\\
Decision thresholds & $\theta_{\text{AI}} = 0.99$, $\theta_{\text{solo}} = 0.998$, HighSet $> 10.0$\,pu\\
Learning rate / Optimizer & 0.001 / Adam ($\beta_1=0.9, \beta_2=0.999$)\\
Loss function & Weighted binary cross-entropy ($w = 1.4155$)\\
Batch size & 128\\
Early-stopping patience & 20 epochs\\
ONNX export format & Opset 14 (fixed input $[1, 32, 12]$)\\ \bottomrule
\end{tabular}\end{table}

\chapter{Reproducibility and Standards}
The pipeline uses MATLAB R2024a/Simulink/Simscape Electrical (10\,\textmu s discrete solver), Python~3.11 with PyWavelets, PyTorch~2.x (Adam, weighted cross-entropy), ONNX Opset~14, and the Simulink Predict block, with fixed random seeds. Relevant standards include IEEE C37.91 (transformer protection), IEEE C37.110 (CTs for relaying), IEC~60255 (measuring relays), IEC~61850-9-2 (Sampled Values; the 1.6\,kHz interface emulated here), IEC~61850-8-1 (GOOSE), and IEC~62351 (communication security). Retaining a certified adaptive 87T element as the dependability anchor keeps the scheme aligned with IEEE~C37.91, easing certification relative to a pure black-box classifier.

\end{document}
"""

def main():
    print(f"Writing updated main.tex to {TEX_PATH}...")
    with open(TEX_PATH, "w", encoding="utf-8") as f:
        f.write(TEX_CONTENT)
    print("Done! Total characters written:", len(TEX_CONTENT))

if __name__ == "__main__":
    main()
