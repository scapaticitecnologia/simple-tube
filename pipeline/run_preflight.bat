@echo off
setlocal
set PYTHONIOENCODING=utf-8
set AUTOPILOT_UNATTENDED=1
cd /d "%~dp0\.."

echo [SIMPLE-TUBE PREFLIGHT] Iniciando check e pre-render: %date% %time% >> pipeline\autopilot_runner.log
python pipeline\health_check.py --pre-render >> pipeline\autopilot_runner.log 2>&1
echo [SIMPLE-TUBE PREFLIGHT] Concluido: %date% %time% >> pipeline\autopilot_runner.log

