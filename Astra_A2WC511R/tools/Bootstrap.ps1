param([string]$PythonExe='', [string]$CodexExe='', [string]$GnushGcc='')
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'Prepare-CDev.ps1') -PythonExe $PythonExe -CodexExe $CodexExe -GnushGcc $GnushGcc
