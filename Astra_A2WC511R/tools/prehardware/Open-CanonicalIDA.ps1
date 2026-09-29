param([switch]$PrintOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$paths = Get-Content -LiteralPath (Join-Path $projectRoot 'config\host_paths.json') -Raw | ConvertFrom-Json
$idbPath = [IO.Path]::GetFullPath($paths.idb)
if ($idbPath -eq [IO.Path]::GetFullPath($paths.damaged_idb_evidence.path)) {
    throw 'Refusing to use the damaged evidence database as authority'
}
if (-not (Test-Path -LiteralPath $idbPath -PathType Leaf)) { throw 'Canonical IDB missing' }
if ($PrintOnly) {
    [pscustomobject]@{ ida=$paths.ida; canonical_idb=$idbPath; sha256=(Get-FileHash -LiteralPath $idbPath -Algorithm SHA256).Hash }
    return
}
# This explicitly requested launcher opens an interactive IDA window for its user.
# No database bytes are changed by the launcher; IDA's later saves are separate.
Start-Process -FilePath $paths.ida -ArgumentList ('"' + $idbPath + '"')
