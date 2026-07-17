param(
    [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$VenvName = ".venv-lstm"
)

$ErrorActionPreference = "Stop"

$VenvPath = Join-Path $ProjectRoot $VenvName
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

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

if (!(Test-Path $ActivateScript)) {
    throw "Virtual environment not found at $VenvPath. Run .\setup_lstm_env.ps1 first."
}

. $ActivateScript

Write-Host "Activated XFormer LSTM environment on F drive."
Write-Host "Python: $VenvPath\Scripts\python.exe"
