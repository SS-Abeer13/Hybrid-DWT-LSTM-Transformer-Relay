param(
    [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$Notebook = "lstm_models\XFormer_LSTM_Standalone.ipynb"
)

$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "activate_lstm_env.ps1") -ProjectRoot $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv-lstm\Scripts\python.exe"
$NotebookPath = Join-Path $ProjectRoot $Notebook

if (!(Test-Path $NotebookPath)) {
    throw "Notebook not found: $NotebookPath"
}

Set-Location $ProjectRoot
& $PythonExe -m notebook $NotebookPath
