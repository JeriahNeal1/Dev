[CmdletBinding()]
param([switch]$IncludeStarterProposals)
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$Refs = Get-Content -LiteralPath (Join-Path $Root 'sources\REFERENCE_REVISIONS.json') -Raw | ConvertFrom-Json
$Git = (Get-Command git -ErrorAction Stop).Source
$Base = Join-Path $Root 'reference_repos'
New-Item -ItemType Directory -Path $Base -Force | Out-Null
foreach ($Ref in $Refs.repositories) {
    if (-not $IncludeStarterProposals -and $Ref.name -match 'starter_proposal') { continue }
    if ($Ref.commit -notmatch '^[0-9a-f]{40}$' -or $Ref.repository -notmatch '^Merp/[A-Za-z]+$') { throw 'Unexpected reference entry.' }
    $Dest = Join-Path $Base $Ref.name
    if (Test-Path -LiteralPath $Dest) { Write-Host ('Preserving existing reference folder: ' + $Dest); continue }
    & $Git init $Dest
    if ($LASTEXITCODE -ne 0) { throw 'git init failed.' }
    & $Git -C $Dest remote add origin ('https://github.com/' + $Ref.repository + '.git')
    if ($LASTEXITCODE -ne 0) { throw 'git remote add failed.' }
    & $Git -C $Dest fetch --depth=1 origin $Ref.commit
    if ($LASTEXITCODE -ne 0) { throw 'Fetch failed. Partial directory preserved for inspection; no existing project repo was changed.' }
    & $Git -C $Dest checkout --detach FETCH_HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Reference checkout failed.' }
    $Head = (& $Git -C $Dest rev-parse HEAD).Trim()
    if ($Head -cne $Ref.commit) { throw 'Reference hash mismatch.' }
    Write-Host ('Reference checked out: ' + $Ref.name + ' ' + $Head)
}
Write-Host 'Reference checkouts only. No builds, target changes, patches, installers or ECU operations performed.'
