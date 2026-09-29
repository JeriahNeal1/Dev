[CmdletBinding()]
param(
 [string]$PythonExe = '',
 [string]$CodexExe = '',
 [string]$DevRoot = 'C:\Dev',
 [string]$GnushGcc = '',
 [string]$Model = 'gpt-6-astra'
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$DevRoot=(Resolve-Path -LiteralPath $DevRoot).Path
if (-not $PythonExe) {
 $FoundPy=Get-Command python.exe -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps|IDA Professional' } | Select-Object -First 1
 if ($FoundPy) { $PythonExe=$FoundPy.Source }
 else {
  $PyLauncher=Get-Command py.exe -ErrorAction SilentlyContinue
  if ($PyLauncher) {
   $Detected=& $PyLauncher.Source -3 -c 'import sys; print(sys.executable)'
   if ($LASTEXITCODE -eq 0) {$PythonExe=([string]$Detected).Trim()}
  }
 }
 if (-not $PythonExe) {throw 'External Python not found. Supply -PythonExe with a real Python 3.11+ path; do not use a Store alias or IDA embedded interpreter.'}
}
if (-not $CodexExe) {
 $FoundCodex=Get-Command codex.exe -ErrorAction SilentlyContinue | Select-Object -First 1
 if ($FoundCodex) {$CodexExe=$FoundCodex.Source}
 else {
  $Shim=Get-Command codex -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($Shim) {
   $NativeRoot=Join-Path (Split-Path -Parent $Shim.Source) 'node_modules\@openai'
   if (Test-Path -LiteralPath $NativeRoot) {
    $Candidates=@(Get-ChildItem -LiteralPath $NativeRoot -Filter codex.exe -File -Recurse -ErrorAction SilentlyContinue)
    $X64Candidates=@($Candidates | Where-Object {$_.FullName -match 'x86_64|win32-x64'})
    if ($X64Candidates.Count -eq 1) {$CodexExe=$X64Candidates[0].FullName}
    elseif ($Candidates.Count -eq 1) {$CodexExe=$Candidates[0].FullName}
   }
  }
 }
 if (-not $CodexExe) {throw 'Native codex.exe not found. Install using the official standalone installer or supply -CodexExe; an npm .cmd/.ps1 shim is not the native binary.'}
}
$PythonExe=(Resolve-Path -LiteralPath $PythonExe).Path
$CodexExe=(Resolve-Path -LiteralPath $CodexExe).Path
if ((Split-Path -Leaf $Root) -ne 'Astra_A2WC511R' -or (Split-Path -Parent $Root) -ne $DevRoot) {
 throw 'Extract this package as C:\Dev\Astra_A2WC511R, alongside (not on top of) your existing repos.'
}
& $PythonExe -c 'import sys; print(sys.executable); print(sys.version); assert sys.version_info >= (3,11)'
if ($LASTEXITCODE -ne 0) {throw 'Use an external Python 3.11+ interpreter, separate from IDA embedded Python.'}
& $PythonExe (Join-Path $Root 'tools\package_acceptance.py')
if ($LASTEXITCODE -ne 0) {throw 'Package integrity check failed. Preserve edits and investigate before continuing.'}
$Venv=Join-Path $Root '.venv'
if (-not (Test-Path -LiteralPath $Venv)) {
 & $PythonExe -m venv $Venv
 if ($LASTEXITCODE -ne 0) {throw 'Virtual environment creation failed.'}
}
$Py=Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Py)) {throw 'Existing .venv is not a usable Windows environment.'}
& $Py (Join-Path $Root 'tools\setup_cdev.py') --dev $DevRoot --python $Py
if ($LASTEXITCODE -ne 0) {throw 'Root instructions/project MCP installation failed; see exact error.'}
& $Py (Join-Path $Root 'tools\audit_dev.py') --dev $DevRoot --out (Join-Path $Root 'reports\local\dev_audit')
if ($LASTEXITCODE -ne 0) {throw 'Read-only Dev audit failed.'}
$NativeArgs=@((Join-Path $Root 'tools\host_preflight.py'),'--dev',$DevRoot,'--codex',$CodexExe,'--model',$Model)
if ($GnushGcc) {$NativeArgs+=@('--cc',$GnushGcc)}
& $Py @NativeArgs
if ($LASTEXITCODE -ne 0) {throw 'Fix the listed readiness blockers before starting the main model run. No model prompt was sent.'}
Write-Host 'READY TO START THE OFFLINE PORT, NOT FLASH APPROVAL.'
Write-Host 'Save/backup the existing IDB, open it in IDA, enable the official Hex-Rays MCP, and keep ECU flashing/actuation manual.'
Write-Host 'Launch using tools\Start-Astra.ps1 -CodexExe <same native codex.exe>.'
