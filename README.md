# Capstone testing (Django REST API placeholder)

Minimal **Django + Django REST Framework** project scaffold so the team can clone, run, and start building endpoints later.

Notes/diagrams live in `docs/` (not wired to the code yet).

## Prerequisites

- **Python**: 3.11+ recommended (3.10+ usually works)
- **Git**: for cloning

Verify:

```powershell
python --version
git --version
```

## Clone

```powershell
git clone <your-repo-url>
cd capstone-testing
```

## Setup (Windows PowerShell)

### 1) Create & activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If activation is blocked, run this once (current user only):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Run database migrations

```powershell
python manage.py migrate
```

### 4) Start the dev server

```powershell
python manage.py runserver
```

Open the health endpoint to confirm it works:

- **GET** `http://127.0.0.1:8000/api/health/`

Expected response (example):

```json
{"status":"ok","message":"Capstone REST API placeholder","version":"0.0.0"}
```

## Setup (macOS / Linux)

```bash
git clone <your-repo-url>
cd capstone-testing

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/api/health/`.

## Useful commands

- **Run Django checks**:

```powershell
python manage.py check
```

- **Create an admin user** (optional, for `/admin/`):

```powershell
python manage.py createsuperuser
```

## Environment variables (optional)

- **`DJANGO_SECRET_KEY`**: overrides the dev placeholder secret key.

Windows PowerShell example:

```powershell
$env:DJANGO_SECRET_KEY="change-me"
python manage.py runserver
```

## Troubleshooting

- **Wrong Python is used**: ensure you activated `.venv` (you should see `(.venv)` in your terminal).
- **`pip` installs globally**: run `.\.venv\Scripts\Activate.ps1` again, then retry.
- **Port already in use**: run on another port:

```powershell
python manage.py runserver 8001
```
