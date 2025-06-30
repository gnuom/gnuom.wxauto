$processes = Get-Process python | Where-Object {$_.Path -like "*wechat_wechaty*"}
$processes | Stop-Process -Force
Write-Host "已终止 $($processes.Count) 个微信机器人进程"