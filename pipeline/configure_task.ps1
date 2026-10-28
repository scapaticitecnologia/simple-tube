$taskName = "SimpleTube-DailyProduction"
$task = Get-ScheduledTask -TaskName $taskName

# 1. Habilitar StartWhenAvailable (executa assim que ligar caso o horario das 09h tenha sido perdido)
$task.Settings.StartWhenAvailable = $true
$task.Settings.DisallowStartIfOnBatteries = $false
$task.Settings.StopIfGoingOnBatteries = $false
$task.Settings.ExecutionTimeLimit = "PT2H"

# 2. Adicionar gatilho ao fazer logon / ligar o computador
$hasLogon = $false
foreach ($t in $task.Triggers) {
    if ($t.CimClass.CimClassName -match "LogonTrigger") {
        $hasLogon = $true
    }
}

if (-not $hasLogon) {
    $triggerLogon = New-ScheduledTaskTrigger -AtLogOn
    $task.Triggers += $triggerLogon
}

Set-ScheduledTask -InputObject $task

Write-Host "Configuracao da tarefa concluida com sucesso!"
Write-Host "Horario principal: Diario as 09:00"
Write-Host "StartWhenAvailable: $($task.Settings.StartWhenAvailable)"
Write-Host "Gatilhos ativos: $($task.Triggers.Count)"
