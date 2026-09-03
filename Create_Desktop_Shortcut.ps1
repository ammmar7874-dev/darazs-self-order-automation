$ws = New-Object -ComObject WScript.Shell
$desktop = [System.Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop "DarazBot Pro.lnk"
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

$targetBat = Join-Path $scriptDir "DarazBot_Pro_Desktop.bat"
$iconPath = Join-Path $scriptDir "frontend\assets\icon.ico"

$shortcut = $ws.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $scriptDir
$shortcut.Description = "DarazBot Pro Enterprise - Desktop Suite"
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()

Write-Host "[+] Successfully created Desktop shortcut: $shortcutPath" -ForegroundColor Green
Write-Host "[+] Icon linked: $iconPath" -ForegroundColor Cyan
