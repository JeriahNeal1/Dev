[CmdletBinding()]
param(
 [string]$CodexExe = '',
 [string]$DevRoot = 'C:\Dev',
 [ValidateSet('batch','interactive')][string]$Mode='batch',
 [string]$Resume=''
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$Py=Join-Path $Root '.venv\Scripts\python.exe'
if (-not $CodexExe) {
 $ProbePath=Join-Path $Root 'reports\local\preflight\model_probe.json'
 if (-not (Test-Path -LiteralPath $ProbePath)) {throw 'Run Prepare-CDev.ps1 first.'}
 $Probe=Get-Content -LiteralPath $ProbePath -Raw | ConvertFrom-Json
 $CodexExe=$Probe.codex_exe
 if (-not $CodexExe) {throw 'The model preflight did not establish a native Codex executable.'}
}
if (-not (Test-Path -LiteralPath $Py)) {throw 'Run Prepare-CDev.ps1 first.'}
$NativeArgs=@((Join-Path $Root 'tools\run_codex.py'),'--dev',$DevRoot,'--codex',$CodexExe,'--mode',$Mode)
if ($Resume) {$NativeArgs+=@('--resume',$Resume)}
& $Py @NativeArgs
if ($LASTEXITCODE -ne 0) {throw "Codex launcher/run exited $LASTEXITCODE. Inspect the saved report and resume the same session after remediation."}
