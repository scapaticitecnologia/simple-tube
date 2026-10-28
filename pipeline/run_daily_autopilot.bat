@echo off
setlocal
cd /d "%~dp0\.."

echo [SIMPLE-TUBE AUTOPILOT] Iniciando rotina diaria: %date% %time% >> pipeline\autopilot_runner.log
python pipeline\daily_autopilot.py >> pipeline\autopilot_runner.log 2>&1
echo [SIMPLE-TUBE AUTOPILOT] Concluido: %date% %time% >> pipeline\autopilot_runner.log
