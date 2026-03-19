Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  python -m venv .venv
}

.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate

# Windows often has port 8000 taken by a system service. Use 8001 by default.
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8001

