param([Parameter(Mandatory=$true)][string]$JdkBin,[switch]$RunModelTests)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$Dir=Join-Path $Root 'integrations\romraider'
$Classes=Join-Path $Dir 'build\classes'
$Jar=Join-Path $Dir 'dist\romraider-bridge.jar'
New-Item -ItemType Directory -Force -Path $Classes,(Split-Path $Jar) | Out-Null
$Sources=Get-ChildItem (Join-Path $Dir 'src\rombridge') -Filter *.java | ForEach-Object {$_.FullName}
& (Join-Path $JdkBin 'javac.exe') --release 8 -d $Classes @Sources
if ($LASTEXITCODE -ne 0) { throw 'Compilation failed. Use JDK 11+ to build; runtime stays Java 8 compatible.' }
$Manifest=Join-Path $Dir 'build\MANIFEST.MF'
@('Manifest-Version: 1.0','Premain-Class: rombridge.Agent','Can-Redefine-Classes: false','Can-Retransform-Classes: false','','') | Set-Content $Manifest -Encoding ASCII
& (Join-Path $JdkBin 'jar.exe') cfm $Jar $Manifest -C $Classes .
if ($LASTEXITCODE -ne 0) { throw 'Jar packaging failed.' }
Get-FileHash $Jar -Algorithm SHA256
if ($RunModelTests) {
    $TestClasses=Join-Path $Dir 'build\test_classes'
    New-Item -ItemType Directory -Force -Path $TestClasses | Out-Null
    $TestSources=Get-ChildItem (Join-Path $Dir 'tests') -Filter *.java -Recurse | ForEach-Object {$_.FullName}
    & (Join-Path $JdkBin 'javac.exe') --release 8 -cp $Classes -d $TestClasses @TestSources
    if ($LASTEXITCODE -ne 0) { throw 'Test fixture compilation failed.' }
    & (Join-Path $JdkBin 'java.exe') '-Djava.awt.headless=true' -cp "$Classes;$TestClasses" rombridge.ModelTests
    if ($LASTEXITCODE -ne 0) { throw 'Java source-contract model tests failed.' }
    Write-Host 'These were model-double tests, not installed RomRaider/Windows application acceptance.'
    Write-Host 'Run tests\agent_transport_smoke.py with JAVA_EXE set to the tested java.exe for the separate transport smoke test.'
}
