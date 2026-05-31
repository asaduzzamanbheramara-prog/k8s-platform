# Run in an elevated PowerShell to register a Scheduled Task that runs the WSL startup script at user logon
$taskName = "StartWSLShopnoServices"
$action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu -- /home/shopno/k8s-platform/bootstrap/auto_start_wsl.sh"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Force
Write-Output "Scheduled Task '$taskName' installed. It runs the WSL startup script at logon."
