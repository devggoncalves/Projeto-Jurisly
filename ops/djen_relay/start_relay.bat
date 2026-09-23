@echo off
REM Inicia o relay DJEN local (IP BR). Mantenha este terminal aberto.
cd /d "%~dp0"
if "%RELAY_SECRET%"=="" set RELAY_SECRET=jurisly-relay-temp-2026
echo RELAY_SECRET=%RELAY_SECRET%
python -m pip install -q -r requirements.txt
python main.py
