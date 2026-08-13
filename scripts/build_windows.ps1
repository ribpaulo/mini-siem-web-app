$ErrorActionPreference = "Stop"

$ProjectDirectory = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectDirectory

$VirtualEnvironmentPython = Join-Path $ProjectDirectory ".venv\Scripts\python.exe"
if (Test-Path $VirtualEnvironmentPython) {
    $PythonCommand = $VirtualEnvironmentPython
} else {
    $PythonCommand = "python"
}

& $PythonCommand -m PyInstaller --clean --noconfirm ssh-sentinel.spec

Write-Host ""
Write-Host "Windows-Build erstellt: $ProjectDirectory\dist\ssh-sentinel.exe"
Write-Host "Start: .\dist\ssh-sentinel.exe"
