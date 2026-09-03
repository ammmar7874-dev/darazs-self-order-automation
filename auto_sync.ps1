# Auto Git Sync Background Engine
$projectDir = "d:\automation_projects"
Set-Location $projectDir

# Log file for background sync
$logFile = "$projectDir\auto_sync.log"

Add-Content -Path $logFile -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Auto Git Sync Service Started."

while ($true) {
    try {
        $status = git status --porcelain
        if ($status) {
            $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            git add .
            git commit -m "auto-sync: $timestamp"
            $pushResult = git push origin main 2>&1
            Add-Content -Path $logFile -Value "[$timestamp] Pushed changes to GitHub. Result: $pushResult"
        }
    }
    catch {
        Add-Content -Path $logFile -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Error during sync: $_"
    }
    
    # 1-Minute Interval (60 Seconds)
    Start-Sleep -Seconds 60
}
