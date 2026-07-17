# XFormer LSTM Local Training Environment

This folder contains an isolated Python environment for the transformer differential-protection LSTM notebooks.

## What Was Set Up

- Virtual environment: `F:\Downloads\Transformer Thesis\.venv-lstm`
- Package/cache folders kept on F drive:
  - `.pip-cache`
  - `.uv-cache`
  - `.python-cache`
  - `.jupyter-data`
  - `.jupyter-runtime`
  - `.jupyter-config`
  - `.matplotlib`
- Notebook kernel name: `Python (XFormer LSTM Local RTX 5060 Ti)`

The package list was inferred from the readable notebooks:

- `XFormer_LTSM_Final.ipynb`
- `XFormer_LTSM_Final_with_Visualization.ipynb`

`XFormer_LSTM_Standalone.ipynb` has been rebuilt as a clean local notebook. The unreadable original was preserved as:

```text
XFormer_LSTM_Standalone_binary_backup_20260601_053915.ipynb
```

## Install Packages

Run this from PowerShell inside `F:\Downloads\Transformer Thesis`:

```powershell
.\setup_lstm_env.ps1
```

The script installs PyTorch CUDA 12.8 wheels for RTX 50-series compatibility, then installs the notebook dependencies from `requirements-lstm-core.txt`.

## Verify GPU and Packages

```powershell
.\activate_lstm_env.ps1
python .\verify_lstm_env.py
```

The verifier checks Python isolation, required imports, PyTorch CUDA access, GPU name/VRAM, and local dataset files.

## Launch Notebook

```powershell
.\launch_lstm_notebook.ps1
```

By default this launches the rebuilt standalone notebook using the project-local Jupyter folders:

```powershell
.\launch_lstm_notebook.ps1
```

Select the kernel named `Python (XFormer LSTM Local RTX 5060 Ti)`.

## Dataset Note

The local raw dataset is present:

```text
Datesets\StressTestDataset_20260531_115NEW.mat
```

The rebuilt standalone notebook is already pointed at:

```text
Datesets\LSTM_Features_Combined_20260601_024803.mat
```

Expected shape:

```text
X_LSTM  = [14128 x 1569 x 9]
Y_LSTM  = [14128 x 1]
Y_class = [14128 x 1]
```
