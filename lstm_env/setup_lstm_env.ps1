param(
    [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$VenvName = ".venv-lstm"
)

$ErrorActionPreference = "Stop"

$VenvPath = Join-Path $ProjectRoot $VenvName
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "lstm_envequirements-lstm-core.txt"

function Invoke-PythonStep {
    param(
        [string]$StepName,
        [string[]]$Arguments
    )

    Write-Host ""
    Write-Host "[$StepName]"
    & $PythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE"
    }
}

# Keep package caches and Python bytecode off C:.
$env:PIP_CACHE_DIR = Join-Path $ProjectRoot ".pip-cache"
$env:UV_CACHE_DIR = Join-Path $ProjectRoot ".uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $ProjectRoot ".uv-python"
$env:PYTHONPYCACHEPREFIX = Join-Path $ProjectRoot ".python-cache"
$env:JUPYTER_DATA_DIR = Join-Path $ProjectRoot ".jupyter-data"
$env:JUPYTER_RUNTIME_DIR = Join-Path $ProjectRoot ".jupyter-runtime"
$env:JUPYTER_CONFIG_DIR = Join-Path $ProjectRoot ".jupyter-config"
$env:MPLCONFIGDIR = Join-Path $ProjectRoot ".matplotlib"

New-Item -ItemType Directory -Force -Path `
    $env:PIP_CACHE_DIR, $env:UV_CACHE_DIR, $env:UV_PYTHON_INSTALL_DIR, `
    $env:PYTHONPYCACHEPREFIX, $env:JUPYTER_DATA_DIR, $env:JUPYTER_RUNTIME_DIR, `
    $env:JUPYTER_CONFIG_DIR, $env:MPLCONFIGDIR | Out-Null

if (!(Test-Path $PythonExe)) {
    throw "Virtual environment not found at $VenvPath. Create it first with: python -m venv `"$VenvPath`""
}

Write-Host "Using project root: $ProjectRoot"
Write-Host "Using Python     : $PythonExe"
Write-Host "Pip cache        : $env:PIP_CACHE_DIR"

Invoke-PythonStep "Upgrade installer tools" @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")

# RTX 50-series / Blackwell GPUs require recent PyTorch CUDA 12.8+ wheels.
# Your driver reports CUDA 13.2, which can run PyTorch's bundled CUDA 12.8 runtime.
Invoke-PythonStep "Install PyTorch CUDA 12.8" @(
    "-m", "pip", "install",
    "torch==2.8.0", "torchvision==0.23.0", "torchaudio==2.8.0",
    "--index-url", "https://download.pytorch.org/whl/cu128"
)

Invoke-PythonStep "Install notebook dependencies" @("-m", "pip", "install", "-r", $Requirements)

Invoke-PythonStep "Register Jupyter kernel" @(
    "-m", "ipykernel", "install",
    "--sys-prefix",
    "--name", "xformer-lstm-local",
    "--display-name", "Python (XFormer LSTM Local RTX 5060 Ti)"
)

Write-Host ""
Write-Host "Environment setup complete."
Write-Host "Activate with:"
Write-Host "  & `"$VenvPath\Scripts\Activate.ps1`""
Write-Host ""
Write-Host "Verify with:"
Write-Host "  & `"$PythonExe`" `"$ProjectRoot\lstm_enverify_lstm_env.py`""
