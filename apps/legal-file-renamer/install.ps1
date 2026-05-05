$ErrorActionPreference = 'Continue'

$exe = Join-Path $PSScriptRoot 'LegalFileRenamer.exe'
if (-not (Test-Path $exe)) {
    Write-Host '[ERROR] LegalFileRenamer.exe not found' -ForegroundColor Red
    exit 1
}

Write-Host '[1/2] Registering context menu...'

$name = -join ([char]0x6CD5,[char]0x5F8B,[char]0x6587,[char]0x4EF6,[char]0x91CD,[char]0x547D,[char]0x540D)
$exeReg = $exe.Replace('\', '\\')
$regContent = @"
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Classes\*\shell\LegalFileRenamer]
@="$name"
"Position"="Top"

[HKEY_CURRENT_USER\Software\Classes\*\shell\LegalFileRenamer\command]
@="\"$exeReg\" \"%1\""
"@

$regFile = Join-Path $env:TEMP 'LegalFileRenamer_install.reg'
[System.IO.File]::WriteAllText($regFile, $regContent, [System.Text.Encoding]::Unicode)
reg import $regFile 2>$null | Out-Null
Remove-Item $regFile -ErrorAction SilentlyContinue
Write-Host '  Done.'

Write-Host '[2/2] Restoring classic context menu (Win11)...'
reg add 'HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32' /f /ve 2>$null | Out-Null
Write-Host '  Done.'

Write-Host ''
Write-Host 'Success! Right-click any file to see the menu.'
