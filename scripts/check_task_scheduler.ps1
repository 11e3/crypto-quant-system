
    $task = Get-ScheduledTask -TaskName "CryptoQuantMonitoring" -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "Task found: CryptoQuantMonitoring"
        Write-Host "State: $($task.State)"
        Write-Host "Last run time: $($task.LastRunTime)"
        Write-Host "Last result: $($task.LastTaskResult)"
    } else {
        Write-Host "Task not found: CryptoQuantMonitoring"
    }
    