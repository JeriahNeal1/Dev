[CmdletBinding()]
param([string[]]$ScanRoots = @('C:\Dev', (Join-Path $env:USERPROFILE 'Documents\SUBARU TUNING')))
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dest = Join-Path $Root ('reports\environment-' + $stamp)
New-Item -ItemType Directory -Path $dest | Out-Null
$os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
$commands = @()
foreach ($name in @('git','python','py','codex','MSBuild','sh-elf-gcc','sh-elf-objdump')) {
    $c = Get-Command $name -ErrorAction SilentlyContinue
    if ($c) { $commands += [pscustomobject]@{Name=$name;Path=$c.Source} }
}
$serial = @(Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue | Select-Object DeviceID,Name,PNPDeviceID)
$roots = @($ScanRoots | Where-Object { Test-Path -LiteralPath $_ })
$files = @()
foreach ($r in $roots) {
    # User-selected project roots only. No entire-drive/profile crawling and no process command lines.
    $files += @(Get-ChildItem -LiteralPath $r -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\.git\\|\\.venv\\|\\node_modules\\' -and $_.Extension -in @('.bin','.xml','.hwp','.hws','.map','.mot','.elf','.abs','.i64','.idb') } |
        Select-Object FullName,Length,LastWriteTimeUtc)
}
$repos = @()
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    $candidates = @()
    foreach ($r in $roots) {
        if (Test-Path -LiteralPath (Join-Path $r '.git')) { $candidates += $r }
        $candidates += @(Get-ChildItem -LiteralPath $r -Directory -Force -ErrorAction SilentlyContinue |
            Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName '.git') } | ForEach-Object { $_.FullName })
    }
    foreach ($r in ($candidates | Select-Object -Unique)) {
        $head = (& $git.Source -C $r rev-parse HEAD 2>&1 | Out-String).Trim()
        $branch = (& $git.Source -C $r branch --show-current 2>&1 | Out-String).Trim()
        $status = (& $git.Source -C $r status --porcelain=v1 2>&1 | Out-String)
        $repos += [pscustomobject]@{Path=$r;Head=$head;Branch=$branch;Status=$status}
    }
}
$hashes = @()
foreach ($f in $files) {
    if ([IO.Path]::GetExtension($f.FullName) -eq '.bin') {
        $h=Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256
        $hashes += [pscustomobject]@{Path=$f.FullName;SHA256=$h.Hash;Size=$f.Length}
    }
}
[pscustomobject]@{Created=(Get-Date).ToString('o');OS=$os;PowerShell=$PSVersionTable.PSVersion.ToString();Commands=$commands;SerialPorts=$serial;Roots=$roots;Repositories=$repos;RomHashes=$hashes;Files=$files;Notes='Read-only inventory. Missing tools may simply not be on PATH. No executables other than Git were run; no driver or device connection was opened.'} |
 ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $dest 'inventory.json') -Encoding UTF8
Write-Host ('Inventory saved: ' + $dest)
Write-Host 'Review local paths/device identifiers before sharing. Inventory is not a hardware health check.'
