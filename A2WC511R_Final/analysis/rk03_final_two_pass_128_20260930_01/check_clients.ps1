param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutputPath) { throw 'Client-check output must be a new file' }
$taskSession = (Get-Process -Id $PID).SessionId
$known = @()
foreach ($p in Get-CimInstance Win32_Process) {
    if ($p.ProcessId -eq $PID) { continue }
    $named = $p.Name -match '^(ecuflash|romraider|freessm|ssm|broker|owned_physical_read32|rk03_transition_probe32|rk03_first_chunk_probe32|rk03_full_upload_no_start_physical32|rk03_kernel_start_identity_physical32|rk03_bounded_rom_read_physical32|rk03_bounded_rom_read_128_physical32|rk03_final_two_pass_128_physical32)(\.exe)?$'
    $javaDiagnostic = $p.Name -match '^java(w)?\.exe$' -and $p.CommandLine -match '(?i)romraider|ecuflash|j2534'
    if ($named -or $javaDiagnostic) {
        $known += [ordered]@{pid=$p.ProcessId;name=$p.Name;command_line=$p.CommandLine}
    }
}
$moduleUsers = @()
$inspectionFailures = @()
foreach ($p in Get-Process | Where-Object { $_.SessionId -eq $taskSession -and $_.Id -ne $PID }) {
    try {
        foreach ($m in $p.Modules) {
            if ($m.ModuleName -match '(?i)op20pt|j2534|passthru') {
                $moduleUsers += [ordered]@{pid=$p.Id;process=$p.ProcessName;module=$m.FileName}
            }
        }
    } catch {
        if (Get-Process -Id $p.Id -ErrorAction SilentlyContinue) {
            $inspectionFailures += [ordered]@{pid=$p.Id;process=$p.ProcessName;error=$_.Exception.Message}
        }
    }
}
$result = [ordered]@{
    utc=[DateTime]::UtcNow.ToString('o')
    scope='All process diagnostic-name/Java-command-line scan plus all same-Windows-session loaded-module scans'
    windows_session_id=$taskSession
    known_conflicting_clients=$known
    provider_module_users=$moduleUsers
    module_inspection_failures=$inspectionFailures
    pass=($known.Count -eq 0 -and $moduleUsers.Count -eq 0 -and $inspectionFailures.Count -eq 0)
    real_provider_loaded_by_check=$false
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
if (-not $result.pass) { throw 'Client absence not established; no launch allowed' }
Write-Output 'PASS_CLIENT_ABSENCE_CHECK'
