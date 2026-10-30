# Comprehensive Literature Review Benchmarking Results

Performance of literature protection models on the identical transformer dataset (3,238 evaluated traces, grouped 5-fold cross-validation, identical 20-sample dwell persistence and 87T high-set instantaneous trip). Numbers are written by lstm_models/benchmark_literature_models.py from the saved fold results.

## Table 1: Standalone Classifier Performance (Literature Operating Mode)

In this mode, each AI classifier directly issues the trip signal once persistence is fulfilled, exactly as evaluated in prior literature.

| Architecture | Reference / Paradigm | Model Category | Parameters | Dependability (%) | Security (%) | Overall Accuracy (%) | Median $T_{op}$ (ms) | $\le$ 2 Cycles (%) | False Trips |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Conventional 87T** | Sharp & Glassburn [7] | Physics-based Relay | --- | 80.34% | 63.41% | 69.95% | 1.2 | 100.0% | 727 |
| **Wavelet-SVM** | Simoes et al. [13] | Kernel Machine | 5,880 | 84.01% | 74.23% | 78.01% | 15.6 | 93.1% | 512 |
| **Wavelet-ANN** | Guzman [19] / Costa [18] | Shallow Neural Network | 5,441 | 97.12% | 96.28% | 96.60% | 16.2 | 95.6% | 74 |
| **Wavelet-RF** | Abdusalam et al. [11] | Ensemble Trees | 37,802 | 96.32% | 96.88% | 96.66% | 16.2 | 87.8% | 62 |
| **1D-CNN** | Afrasiabi et al. [16] | Convolutional Network | 14,561 | 97.52% | 96.73% | 97.04% | 16.2 | 96.8% | 65 |
| **Wavelet-GRU** | Lin et al. [23] | Recurrent Sequence | 44,354 | 98.40% | 96.53% | 97.25% | 15.0 | 95.9% | 69 |
| **Standalone LSTM** | Alhamd [1] / Atiyah [3] | Recurrent Sequence | 58,241 | 97.92% | 96.78% | 97.22% | 15.6 | 96.4% | 64 |

## Table 2: Performance Under the Proposed Supervisory Hybrid Architecture

Here, each learned model is integrated into the proposed dual-path supervisory architecture:
$$\text{TRIP} = \text{HighSet} \vee (\text{87T\_Vote} \wedge p_{\text{AI,conf}} \ge \theta_{\text{AI}}) \vee (p_{\text{AI,conf}} \ge \theta_{\text{solo}})$$ 

| Architecture | Paradigm | Dependability (%) | Security (%) | Overall Accuracy (%) | Median $T_{op}$ (ms) | Pre-Fault Trips | False Trips | Missed Faults |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Wavelet-SVM** | Dual-Path Hybrid | 80.82% | 98.24% | 91.51% | 18.1 | 6 | 35 | 234 |
| **Wavelet-ANN** | Dual-Path Hybrid | 92.57% | 99.09% | 96.57% | 16.9 | 0 | 18 | 93 |
| **Wavelet-RF** | Dual-Path Hybrid | 92.09% | 99.25% | 96.48% | 19.4 | 0 | 15 | 99 |
| **1D-CNN** | Dual-Path Hybrid | 92.25% | 99.14% | 96.48% | 18.1 | 0 | 17 | 97 |
| **Wavelet-GRU** | Dual-Path Hybrid | 93.29% | 99.04% | 96.82% | 15.6 | 0 | 19 | 84 |
| **Proposed Hybrid DWT-LSTM** | Dual-Path Hybrid | 93.92% | 99.14% | 97.13% | 16.2 | 0 | 17 | 76 |

## Reading the tables

The two tables above are the result; this report contains no interpretation. Dependability and security are pooled over the evaluated traces of the first CV repetition; the comparison with the proposed relay over 3 repetitions is in runs/<tag>_cv5_seeds/summary.txt.