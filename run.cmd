@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" manage.py migrate

REM Bind all interfaces so ESP32 on Wi-Fi can POST to this PC's LAN IPv4:8001.
REM Windows often has port 8000 taken by a system service. Use 8001 by default.
".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8001

