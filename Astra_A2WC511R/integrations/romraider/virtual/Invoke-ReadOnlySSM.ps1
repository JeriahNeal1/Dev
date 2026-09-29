[CmdletBinding()]
param(
    [ValidateSet('Virtual', 'PhysicalJ2534', 'PhysicalSerial')][string]$Mode = 'Virtual',
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$ComPort,
    [switch]$AcknowledgeReadOnlyPhysicalConnection
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$manifestPath = Join-Path $PSScriptRoot 'collector_runtime_manifest.json'
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
foreach ($directory in $manifest.runtime_directories) {
    $entries = @((Get-Item -LiteralPath $directory.path -Force)) + @(Get-ChildItem -LiteralPath $directory.path -Recurse -Force)
    if ($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw "Runtime reparse points are forbidden: $($directory.path)" }
    $expectedFiles = @($directory.files | Sort-Object)
    $actualFiles = @(Get-ChildItem -LiteralPath $directory.path -Recurse -File -Force | ForEach-Object { $_.FullName } | Sort-Object)
    if (Compare-Object -ReferenceObject $expectedFiles -DifferenceObject $actualFiles) { throw "Runtime directory inventory changed: $($directory.path). Revalidate offline; additional classes/resources are forbidden." }
}
foreach ($item in $manifest.artifacts) {
    if (-not (Test-Path -LiteralPath $item.path -PathType Leaf)) { throw "Required reviewed artifact missing: $($item.path)" }
    $actualHash = (Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $item.sha256) { throw "Reviewed artifact changed: $($item.path). Revalidate offline before any physical invocation." }
}
$classes = Join-Path $projectRoot 'work\gate_closure\virtual_rr\classes'
if (Test-Path -LiteralPath (Join-Path $classes 'com\romraider\io\connection\ConnectionManagerFactory.class')) { throw 'GUI virtual override must never appear in collector classes' }
$outPath = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $outPath) { throw 'Output directory must be new; no acquisition is overwritten' }
if ($Mode -ne 'Virtual' -and -not $AcknowledgeReadOnlyPhysicalConnection) { throw 'Physical mode is a future human action. Read the reviewed one-connection procedure, connect manually, then explicitly pass -AcknowledgeReadOnlyPhysicalConnection.' }
$classPath = $manifest.classpath -join ';'
$workPath = Join-Path $projectRoot 'work\gate_closure\virtual_rr'
$javaArgs = @(('-Duser.home=' + (Join-Path $workPath 'home')), '-cp', $classPath, 'a2wc.virtualrr.ReadOnlySSMCollector')
if ($Mode -eq 'Virtual') {
    $javaArgs += @('virtual', $outPath, $manifest.snapshot.path, $manifest.snapshot.sha256, $manifest.rom.path, $manifest.rom.sha256)
} elseif ($Mode -eq 'PhysicalJ2534') {
    $javaArgs += @('physical-j2534', $outPath, $manifest.provider.path, $manifest.provider.sha256, 'I_AUTHORIZE_READ_ONLY_SSM')
} else {
    if ($ComPort -notmatch '^COM[1-9][0-9]*$') { throw 'An actual serial interface COM port is required; the OpenPort J2534 provider is not a COM port' }
    $javaArgs += @('physical-serial', $outPath, $ComPort, 'I_AUTHORIZE_READ_ONLY_SSM')
}
Write-Host "Read-only collector mode: $Mode. No reset, kernel upload, ECU memory-write command, or automatic transport fallback."
if ($Mode -ne 'Virtual') { Write-Host 'OEM A0 ROM accessibility remains unproven. Denied/invalid/mismatched data aborts the acquisition. Two 1 MiB reads at 4800 baud can take roughly 80 minutes. Follow the reviewed stable bench-power, engine-off procedure. Initial and final bursts each collect 60 six-byte samples.' }
Push-Location -LiteralPath $workPath
try {
    & $manifest.java.path @javaArgs
    if ($LASTEXITCODE -ne 0) { throw "Collector aborted with exit code $LASTEXITCODE; preserve output and do not substitute a kernel-based reader." }
} finally { Pop-Location }
