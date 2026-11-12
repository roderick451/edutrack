# Complete Step-by-Step Deployment of a Student Record Management System Using Python Flask, PostgreSQL, GitHub, and Render

## 1. Introduction
This guide explains how to build, test, and deploy the EduTrack student record management system so it can be hosted on a free web platform. The project uses Python Flask, PostgreSQL, SQLAlchemy, GitHub, and Render.

## 2. Project Overview
EduTrack is a modern academic administration platform for managing student records, course information, and dashboard analytics. It is designed for university or school administrators who need to track student data securely.

## 3. Objectives
- Build a professional web application using Flask.
- Store data in PostgreSQL.
- Secure the app with authentication and validation.
- Provide student and course management features.
- Deploy the app to a public hosting platform.

## 4. Software and Tools Used
- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- PostgreSQL
- Render
- GitHub
- Pytest
- Tailwind CSS
- Chart.js

## 5. System Requirements
- Python 3.10+
- PostgreSQL database server
- Git installed
- A Render account
- A GitHub account
- Access to a terminal or command line

## 6. Local Development Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Expected result: the virtual environment is created and dependencies are installed successfully.

## 7. PostgreSQL Database Creation
```sql
CREATE DATABASE edutrack;
```

Expected result: a local PostgreSQL database named `edutrack` is available for development.

## 8. Database Connection Configuration
Create a `.env` file using `.env.example`:

```powershell
Copy-Item .env.example .env
```

Example configuration:
```env
SECRET_KEY=change-this-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/edutrack
FLASK_ENV=development
```

Expected result: the app connects to PostgreSQL through the environment variables.

## 9. Application Development
The app uses a modular structure with:
- `app/__init__.py`
- `app/models.py`
- `app/routes/`
- `app/templates/`
- `app/static/`

The database models include `User`, `Course`, and `Student` with relationships and unique constraints.

## 10. Local Application Testing
Start the application:

```powershell
python run.py
```

Open the browser and visit:
```text
http://127.0.0.1:5000
```

Expected result: the app loads the login page and the dashboard after authentication.

Screenshot placeholder: `documentation/screenshots/local_app_running.png`

## 11. GitHub Repository Setup
```bash
git init
git add .
git commit -m "Initial EduTrack commit"
git branch -M main
git remote add origin <your-github-repository-url>
git push -u origin main
```

Expected result: source code is pushed to GitHub.

## 12. Render Account Setup
Create a Render account and sign in. Then create a new Web Service connected to the GitHub repository. Render will automatically detect a Python app.

## 13. PostgreSQL Cloud Database Setup
Create a PostgreSQL database on Render or another compatible provider. Copy the `DATABASE_URL` value into the Render environment variables. Do not store credentials in source code.

## 14. Render Web Service Configuration
Configure the Render service with:
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn "app:create_app()"` or the correct app entry point if you adjust the wsgi file.

## 15. Environment Variables Configuration
Set these variables in Render:
```env
DATABASE_URL=your_postgres_url
SECRET_KEY=strong-production-secret
FLASK_ENV=production
```

Expected result: the deployed app connects securely to PostgreSQL and uses production settings.

## 16. Deployment Process
1. Push changes to GitHub.
2. Create a Render web service.
3. Connect the repository.
4. Add environment variables.
5. Trigger the deployment.
6. Watch build logs for errors.

Expected result: the app is deployed and a public URL is generated.

## 17. Database Migration
Use migration commands to create database tables:
```bash
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

Expected result: the PostgreSQL database schema is created correctly.

## 18. Public Website Testing
After deployment, test the public URL for:
- login/logout
- dashboard access
- adding a student
- editing a student
- course creation
- CSV export

## 19. Troubleshooting Common Errors
- Missing `DATABASE_URL` environment variable
- PostgreSQL connection failure
- Gunicorn import errors
- CSS or JS not loading
- CSRF token issues
- `ModuleNotFoundError` for dependencies

## 20. Security Considerations
- Use hashed passwords.
- Store secrets in environment variables only.
- Keep `FLASK_ENV` set to production in deployment.
- Use secure session cookies.
- Validate all form inputs server-side.

## 21. Final Deployment Results
The final system should provide a functioning public web application with a real database connection, user authentication, and student management features. Record the exact public URL in your academic deliverable.

## 22. Conclusion
Deploying a Flask application to Render with PostgreSQL is a practical and professional way to host a student record system. This process teaches database integration, deployment configuration, environment management, and web hosting best practices.

Screenshot placeholder: `documentation/screenshots/render_deployment.png`
