# Read-only COM registration discovery. Does NOT instantiate COM or launch HEW.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$Rows = @()
foreach ($View in @([Microsoft.Win32.RegistryView]::Registry32,[Microsoft.Win32.RegistryView]::Registry64)) {
    $Base=$null; $ClsidRoot=$null
    try {
        $Base=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::ClassesRoot,$View)
        $ClsidRoot=$Base.OpenSubKey('CLSID')
        if ($null -eq $ClsidRoot) { continue }
        foreach ($Id in $ClsidRoot.GetSubKeyNames()) {
            $Key=$null; $Prog=$null; $InProc=$null; $Local=$null; $TypeLib=$null
            try {
                $Key=$ClsidRoot.OpenSubKey($Id)
                if ($null -eq $Key) { continue }
                $Name=[string]$Key.GetValue('')
                $Prog=$Key.OpenSubKey('ProgID'); $InProc=$Key.OpenSubKey('InprocServer32'); $Local=$Key.OpenSubKey('LocalServer32'); $TypeLib=$Key.OpenSubKey('TypeLib')
                $ProgId=if ($Prog) { [string]$Prog.GetValue('') } else { '' }
                $Server=if ($InProc) { [string]$InProc.GetValue('') } elseif ($Local) { [string]$Local.GetValue('') } else { '' }
                if (($Name+' '+$ProgId+' '+$Server) -match '(?i)Renesas|TargetServer|High.performance.Embedded|\bHEW\b') {
                    $Rows += [pscustomobject]@{View=$View.ToString();CLSID=$Id;Name=$Name;ProgID=$ProgId;Server=$Server;TypeLib=$(if ($TypeLib) { [string]$TypeLib.GetValue('') } else { '' })}
                }
            } catch { Write-Verbose $_.Exception.Message }
            finally { foreach ($K in @($TypeLib,$Local,$InProc,$Prog,$Key)) { if ($K) { $K.Dispose() } } }
        }
    } finally { if ($ClsidRoot) { $ClsidRoot.Dispose() }; if ($Base) { $Base.Dispose() } }
}
$Out=Join-Path $Root ('reports\hew-com-discovery-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')
@($Rows) | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Out -Encoding UTF8
Write-Host ('Read-only discovery saved: '+$Out)
Write-Host 'No COM methods were invoked. Inspect actual type libraries before writing a HEW adapter. Empty results do not prove all automation is unavailable.'
