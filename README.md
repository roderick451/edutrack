# EduTrack — Student Record Management System

EduTrack is a modern Flask-based student record management system designed for academic administration. It includes secure login, dashboard analytics, student and course CRUD, PostgreSQL integration, reporting, and deployment configuration for Render.

## Features
- Admin authentication with hashed passwords
- Dashboard with live database totals and charts
- Student CRUD with validation and search filters
- Course management with search and enrollment counts
- Reports and enrollment summaries based on live database records
- CSV export for student records
- Admin account settings with current-password verification and optional password updates
- Light/dark appearance toggle and responsive navigation
- Responsive SaaS-style layout
- PostgreSQL support with SQLAlchemy
- Local development and Render deployment setup

## Local setup

### 1) Create virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Configure environment variables
Create a `.env` file based on `.env.example`.

```powershell
Copy-Item .env.example .env
```

Set:
```env
SECRET_KEY=your-long-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/edutrack
FLASK_ENV=development
```

### 4) Create PostgreSQL database
```sql
CREATE DATABASE edutrack;
```

### 5) Run app
```powershell
python run.py
```

Open: http://127.0.0.1:5000

### 6) Create admin account
```powershell
$env:ADMIN_USERNAME='admin'
$env:ADMIN_PASSWORD='admin123'
python scripts\create_admin.py
```

### 7) Seed sample data
```powershell
python scripts\seed.py
```

## Deployment
- Use Render with a PostgreSQL database and the Gunicorn start command.
- Set `DATABASE_URL`, `SECRET_KEY`, and `FLASK_ENV=production` as environment variables.
- The dashboard totals and report values come from the deployed database. Use `python scripts\seed.py` only when you intentionally want sample records in a development database.
- Password recovery email is not configured; the sign-in help page directs admins to their deployment administrator.

## Testing
```powershell
pytest
```

## Project structure
- `app/` — application package
- `scripts/` — admin creation and seed scripts
- `tests/` — automated tests
- `documentation/screenshots/` — deployment screenshots or placeholders
