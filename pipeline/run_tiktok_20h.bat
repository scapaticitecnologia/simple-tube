@echo off
setlocal
set PYTHONIOENCODING=utf-8
set AUTOPILOT_UNATTENDED=1
cd /d "%~dp0\.."

echo [SIMPLE-TUBE TIKTOK 20H] Iniciando slot da noite: %date% %time% >> pipeline\tiktok_runner.log
python pipeline\publishing\tiktok_slots_manager.py --slot 20h >> pipeline\tiktok_runner.log 2>&1
echo [SIMPLE-TUBE TIKTOK 20H] Concluido: %date% %time% >> pipeline\tiktok_runner.log
