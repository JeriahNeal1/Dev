param(
 [Parameter(Mandatory=$true)][string]$JavaExe,
 [Parameter(Mandatory=$true)][string]$RomRaiderJar,
 [switch]$EnableEdits,
 [string[]]$RomRaiderArguments = @(),
 [string[]]$JvmArguments = @()
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$JavaExe = (Resolve-Path -LiteralPath $JavaExe).Path
$RomRaiderJar = (Resolve-Path -LiteralPath $RomRaiderJar).Path
$Agent = Join-Path $Root 'integrations\romraider\dist\romraider-bridge.jar'
if (!(Test-Path -LiteralPath $Agent)) { throw 'Compile bridge using Build-RomRaiderBridge.ps1 first.' }
$Runtime = Join-Path $Root '.runtime\romraider'
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
# Restrict token/config directory to the current Windows user and SYSTEM.
$Account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $Runtime /inheritance:r /grant:r "${Account}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Failed to secure runtime directory; do not continue with shared token files.' }
$Connection = Join-Path $Runtime 'connection.json'
if (Test-Path -LiteralPath $Connection) { throw 'A prior bridge connection exists. Confirm its process is stopped before removing only that stale connection file.' }
$TokenBytes = New-Object byte[] 32
$Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$Rng.GetBytes($TokenBytes); $Rng.Dispose()
$Token = -join ($TokenBytes | ForEach-Object { $_.ToString('x2') })
$Work = Join-Path $Root 'work\rr_editor_exports'
New-Item -ItemType Directory -Force -Path $Work | Out-Null
function Property-Escape([string]$Value) {
 # Java Properties ASCII escaping, including non-ASCII user/folder names.
 $b = New-Object System.Text.StringBuilder
 foreach ($c in $Value.ToCharArray()) {
  if ($c -eq '\') { [void]$b.Append('\\') }
  elseif ([int]$c -gt 126 -or [int]$c -lt 32) { [void]$b.Append(('\u{0:x4}' -f [int]$c)) }
  else { [void]$b.Append($c) }
 }
 return $b.ToString()
}
$Enabled = if ($EnableEdits) {'true'} else {'false'}
$Props = Join-Path $Runtime 'bridge.properties'
@("token=$Token", "connection=$(Property-Escape $Connection)", "work=$(Property-Escape $Work)", "allow_apply=$Enabled") | Set-Content -LiteralPath $Props -Encoding ASCII
Write-Host 'Save/close any existing editor instance first. Do not start a second vehicle client.'
Write-Host "Launching the same RomRaider jar with an additional Java agent. Apply=$Enabled"
Write-Host 'All commit operations still require a local YES/NO confirmation. No ECU flashing.'
Push-Location (Split-Path -Parent $RomRaiderJar)
try {
 & $JavaExe @JvmArguments "-javaagent:$Agent=$Props" -jar $RomRaiderJar @RomRaiderArguments
 if ($LASTEXITCODE -ne 0) { throw "RomRaider process exited $LASTEXITCODE" }
} finally { Pop-Location }
