# Run in Windows PowerShell as a normal user.
# This pins the same source revisions used by the companion guide.
$ErrorActionPreference = 'Stop'
$Root = 'C:\Dev'
New-Item -ItemType Directory -Force -Path $Root | Out-Null

function Clone-PinnedRepo([string]$Url, [string]$Path, [string]$Commit) {
    if (-not (Test-Path $Path)) {
        git clone $Url $Path
    }
    git -C $Path fetch --all --tags
    git -C $Path checkout $Commit
}

Clone-PinnedRepo 'https://github.com/Merp/MerpMod.git'  "$Root\MerpMod"  '8720d209df107a81fd171131cfba96d8cae1f118'
Clone-PinnedRepo 'https://github.com/Merp/SharpTune.git' "$Root\SharpTune" 'ecabea89615132dac2de37c05f72adae16d966d1'
Clone-PinnedRepo 'https://github.com/Merp/SubaruDefs.git' "$Root\SubaruDefs" '9b2992eba8133fe5338b89aa77b22c1bb14d6507'

# Create a writable porting branch after pinning MerpMod.
git -C "$Root\MerpMod" switch -C a2wc511r-port

New-Item -ItemType Directory -Force -Path "$Root\SubaruRoms\OEM" | Out-Null
Write-Host 'Repositories are ready under C:\Dev.'
Write-Host 'Copy your untouched A2WC511R read to C:\Dev\SubaruRoms\OEM\A2WC511R.bin'
