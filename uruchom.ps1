$ErrorActionPreference = 'Stop'
$ProjectDir = $PSScriptRoot
$PythonExe = Join-Path $ProjectDir '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $PythonExe)) {
    throw 'Brak .venv. Przygotuj środowisko według README.md lub użyj paczki przenośnej.'
}
Start-Process -FilePath $PythonExe -WorkingDirectory $ProjectDir -ArgumentList '-m', 'meeting_timer'
