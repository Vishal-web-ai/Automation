$action = New-ScheduledTaskAction -Execute "D:\Automation\run_daily_words.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "6:00AM"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName "DailyEnglishWords" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Get 5 English words daily at 6AM via Telegram"

Write-Host "Task scheduled successfully!" -ForegroundColor Green
Write-Host "You will receive words every day at 6:00 AM"
