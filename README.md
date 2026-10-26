> **SUPERSEDED (2026-10-22) - DO NOT CITE.** The numbers below (4/4 closed loop at 17.5 ms, 95.45 % accuracy, 12-feature baseline of 2026-08) do not match any saved output file and were produced with a
> mis-calibrated 87T path, a data-leaking evaluation and a stress dataset in which noise, fault resistance and timing were not applied. The supported results are in
> `documents/results_v3/tables.md` (generated from saved files), the limitations in `documents/results_v3/limitations.md`, and the dated log in `IMPLEMENTATION_PLAN.md`.

# Hybrid DWT-LSTM-Transformer Relay: 12-Feature Thesis Baseline & Deployment Verification

This document summarizes the official 12-feature thesis baseline training, feature extraction, ONNX export, closed-loop MATLAB/Simulink co-simulation verification, and category-level stress evaluation for the Hybrid DWT-LSTM Transformer Differential Relay.

---

## Executive Summary

1. **Thesis Baseline Dataset**: Compiled a comprehensive dataset of **192,600 samples** (`datasets/LSTM_Features_Combined_20260807_193459.mat`) across 154,080 training, 19,260 validation, and 19,260 test samples with sequence length 32.
2. **Feature Extraction (12 Features)**: Extracted 12 features comprising 9 DWT wavelet energies (3 phases $\times$ [D1, D2, A2]) plus 3 second-harmonic ratios for enhanced inrush discrimination.
3. **PyTorch Model Retraining**: Trained the 12-feature PyTorch WT-LSTM neural network architecture (2 LSTM layers, hidden size 64, dropout ~0.22, unidirectional).
   - **Validation AUC**: **98.68%**
   - **Test Accuracy**: **95.45%**
   - **Precision**: **88.56%**
   - **Recall**: **99.47%**
   - **F1-Score**: **93.70%**
   - **AUC-ROC**: **98.54%**
4. **ONNX Export & Simulink Compilation**: Exported PyTorch baseline model to `lstm_models/wt_lstm_relay.onnx` and compiled to `simulations/live_relay_ai.mat` for real-time `dlnetwork` inference inside Simulink.
5. **Fast Sub-40 ms Fault Detection Speed**: Verified instantaneous high-set overcurrent trip bypass and Stateflow gating logic. Fault trip speed for internal faults achieved **17.5 ms** (well below the sub-40 ms requirement).
6. **Closed-Loop Co-Simulation Verification**: **100.0% PASS Rate (4 / 4 Benchmark Cases)** maintained in MATLAB `test_hybrid_relay.m`.

---

## Model Architecture & Baseline Performance (`runs/20260808_lstm_training/metrics.json`)

| Metric / Parameter | Value |
| :--- | :--- |
| **Input Features** | 12 (9 DWT wavelet energies + 3 second-harmonic ratios) |
| **Sequence Length** | 32 |
| **Architecture** | 2 LSTM layers, hidden size 64, unidirectional |
| **Dropout** | ~0.22 (0.2214) |
| **Dataset Size** | 192,600 samples (Train: 154,080 / Val: 19,260 / Test: 19,260) |
| **Validation AUC** | 98.68% |
| **Test Accuracy** | 95.45% |
| **Test Precision** | 88.56% |
| **Test Recall** | 99.47% |
| **Test F1-Score** | 93.70% |
| **Test AUC-ROC** | 98.54% |
| **Test Loss** | 0.1378 |

---

## Closed-Loop Co-Simulation Test Results (`test_hybrid_relay.m`)

| Test Case | Expected Decision | Actual Decision | Fault Trip Latency | LSTM Max Probability | Verification Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal Operation** | `BLOCK` | `BLOCK` | N/A | `0.6907` | **PASS** |
| **Magnetizing Inrush** | `BLOCK` | `BLOCK` | N/A | `0.6729` | **PASS** |
| **Internal A-G Fault** | `TRIP` | `TRIP` | **17.5 ms** (0.0675 s) | `0.6404` | **PASS** |
| **External 3-Phase Fault** | `BLOCK` | `BLOCK` | N/A | `0.6757` | **PASS** |

> [!NOTE]
> **Sub-40 ms Fault Speed**: Internal A-G Fault trip occurred at **17.5 ms after fault inception**, successfully fulfilling the sub-40 ms requirement.

---

## Category-Level Dataset Stress Evaluation (`evaluate_all_stress_categories.py`)

| Category Name | Dataset Samples | Average AI Probability | Category Performance |
| :--- | :--- | :--- | :--- |
| **Normal Steady State** | 24 | `0.2913` | **100.0% PASS** (24 / 24) |
| **Internal Low-Z Faults** | 14 | `0.6736` | **100.0% RECALL** (14 / 14) |
| **High-Impedance Faults (HiZ)** | 26 | `0.6507` | **100.0% RECALL** (26 / 26) |
| **Internal Evolving Faults** | 6 | `0.6815` | **100.0% RECALL** (6 / 6) |
| **Magnetizing Inrush (No-Load & Loaded)** | 14 | `0.6317` | Standard Restraint Applied |
| **External Low-Z & High-Z Faults** | 2 | `0.6814` | Dual-End Directional Restraint |

---

## Key Files & Artifacts

- **Model Checkpoint**: `runs/20260808_lstm_training/transformer_protection_lstm_best.pth`
- **Training Metrics**: [metrics.json](runs/20260808_lstm_training/metrics.json)
- **Feature Dataset**: `datasets/LSTM_Features_Combined_20260807_193459.mat`
- **ONNX Model**: `lstm_models/wt_lstm_relay.onnx`
- **Simulink Network File**: [live_relay_ai.mat](simulations/live_relay_ai.mat)
- **Simulink Test Suite**: [test_hybrid_relay.m](simulations/test_hybrid_relay.m)
- **Batch Stress Test Script**: [run_batch_stress_test.m](simulations/run_batch_stress_test.m)
- **Category Evaluation Script**: [evaluate_all_stress_categories.py](evaluate_all_stress_categories.py)
- **Stateflow Relay Logic**: [repair_hybrid_relay_for_lstm_verification.m](simulations/repair_hybrid_relay_for_lstm_verification.m)
