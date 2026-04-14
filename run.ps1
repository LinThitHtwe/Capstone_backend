Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  python -m venv .venv
}

.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate

# Bind all interfaces so ESP32 / LAN devices can reach this PC (ipconfig Wi‑Fi IPv4).
# Browser: http://127.0.0.1:8001/ — IoT: same port, host = PC LAN address (e.g. 10.x.x.x).
# Windows often has port 8000 taken by a system service. Use 8001 by default.
.\.venv\Scripts\python manage.py runserver 0.0.0.0:8001

