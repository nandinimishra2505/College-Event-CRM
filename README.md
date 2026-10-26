# CampusConnect — College Event Management System

A full-stack Flask + SQLite college event registration app with a student-facing events page and an admin dashboard.

## Features

- Responsive events landing page
- Student registration with client- and server-side validation
- Duplicate phone-number prevention per event
- Admin login with hashed password
- Admin dashboard to create/delete events and review registrations
- SQLite database initialised automatically for local runs and Gunicorn deployments
- Health endpoint at `/health`

## Project structure

```text
college_event_crm_fullstack/
├── app.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── templates/
│   ├── index.html
│   ├── login.html
│   └── admin.html
└── static/
    ├── style.css
    ├── script.js
    └── admin.js
```

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (optional but recommended):

   **Windows**
   ```powershell
   py -m venv .venv
   .venv\\Scripts\\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set a secret key and admin password before running in a shared environment. For a quick local demo, the default login is `admin` / `admin123`.
6. Start the app:
   ```bash
   python app.py
   ```
7. Open http://127.0.0.1:5000

Admin dashboard: http://127.0.0.1:5000/login

## Deploy on Render

Create a **Web Service** connected to this repository.

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`

Add environment variables in Render:
- `SECRET_KEY`: a long, random secret value
- `ADMIN_USERNAME`: `admin` (or your preferred username)
- `ADMIN_PASSWORD`: a strong password

Then deploy. Visit `/health` to check that the service responds.

### Important SQLite hosting note

On a free/ephemeral hosting filesystem, SQLite data may be lost when the service restarts or redeploys. For persistent real-world data, use a managed PostgreSQL database or a persistent disk. This project is a student demo, not a production-ready system.

## Important admin-password note

The admin account is created only when that username does not already exist in the database. Changing `ADMIN_PASSWORD` later will not change an already-created account's password. For a fresh deployment, use a fresh database. Never upload a real database or real student data to a public repository.

## Security notes

- Do not commit `.env`, real credentials, or `database.db`.
- Set `SECRET_KEY` and `ADMIN_PASSWORD` in the hosting provider's environment settings.
- The default `admin` / `admin123` credentials are for local demonstration only; change them before sharing the app.
- Add CSRF protection, rate limiting, stronger phone/email validation, and a persistent production database before real use.
