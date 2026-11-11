@echo off
setlocal
set PYTHONIOENCODING=utf-8
set AUTOPILOT_UNATTENDED=1
cd /d "%~dp0\.."

echo [SIMPLE-TUBE TIKTOK 16H] Iniciando slot da tarde: %date% %time% >> pipeline\tiktok_runner.log
python pipeline\publishing\tiktok_slots_manager.py --slot 16h >> pipeline\tiktok_runner.log 2>&1
echo [SIMPLE-TUBE TIKTOK 16H] Concluido: %date% %time% >> pipeline\tiktok_runner.log
