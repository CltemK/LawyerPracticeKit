$ErrorActionPreference = 'Continue'

$key = 'HKCU:\Software\Classes\*\shell\LegalFileRenamer'

Write-Host '[1/2] Removing context menu...'
try {
    Remove-Item -LiteralPath $key -Recurse -Force
    Write-Host '  Done.'
} catch {
    Write-Host '  Not found, skipping.'
}

Write-Host '[2/2] Restoring Win11 new context menu...'
try {
    Remove-Item -Path 'HKCU:\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}' -Recurse -Force
    Write-Host '  Done.'
} catch {
    Write-Host '  Not found, skipping.'
}

Write-Host ''
Write-Host 'Done! Restart Explorer for changes to take effect.'
