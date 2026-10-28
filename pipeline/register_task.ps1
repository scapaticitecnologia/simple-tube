# Register Simple-Tube Task Scheduler in Windows
$batPath = "c:\Users\ripia\OneDrive\Documentos\projetos\simple-tube\pipeline\run_daily_autopilot.bat"
$workDir = "c:\Users\ripia\OneDrive\Documentos\projetos\simple-tube"

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`"" -WorkingDirectory $workDir

# 1. Disparo diário pontual às 09:00
$triggerDaily = New-ScheduledTaskTrigger -Daily -At "09:00"

# 2. Disparo ao fazer login / inicializar a máquina
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn

# 3. Configurações essenciais:
# - StartWhenAvailable: Se a máquina estava desligada no horário das 09:00, o Windows executa assim que ela ligar!
# - AllowStartIfOnBatteries / DontStopIfGoingOnBatteries: Permite execução mesmo em notebooks/bateria
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName "SimpleTube-DailyProduction" -Action $action -Trigger @($triggerDaily, $triggerLogon) -Settings $settings -Description "Criacao e publicacao diaria automatica do canal Scapatici Tecnologia as 09h" -Force

Write-Host "✅ Tarefa agendada com sucesso no Windows Task Scheduler!"
