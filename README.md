# TaskFlow - Full-Stack React + FastAPI Task Management Platform

![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=111111)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-111827)
![Docker](https://img.shields.io/badge/DevOps-Docker-2496ED?logo=docker&logoColor=white)

TaskFlow is a portfolio-ready full-stack task management app built with React and FastAPI. It demonstrates secure authentication, role-based access control, task workflows, dashboard analytics, comments, file upload metadata, search/filtering, Docker, and CI.

Suggested GitHub topics: `react`, `fastapi`, `fullstack`, `jwt-authentication`, `task-management`, `docker`, `github-actions`.

## Why this version is stronger for a resume

The original idea was good, but it listed a lot of features at the same level. This project makes the scope more believable by implementing the core workflow end to end:

- Users can register and log in with JWT authentication.
- Admins can manage users and assign tasks.
- Users can update assigned tasks and add comments.
- Dashboards summarize task status, priority, overdue work, and upcoming due dates.
- Search and filters work through REST API query parameters.
- Upload support stores file metadata locally so the project remains easy to run.
- SQLite is the default for local development, with PostgreSQL-ready configuration through `DATABASE_URL`.

## Tech Stack

- Frontend: React, Vite, plain CSS
- Backend: Python, FastAPI, SQLAlchemy
- Database: SQLite locally, PostgreSQL-ready through environment config
- Auth: JWT access tokens, password hashing
- DevOps: Docker, Docker Compose, GitHub Actions
- Deployment targets: Vercel for frontend, Render for backend

## Run Locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\run_dev.ps1
```

The API runs at `http://localhost:8000`. Use `.\run_dev_reload.ps1` only when you want automatic reloads while editing backend code.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

### Docker

```powershell
docker compose up --build
```

## Demo Accounts

The backend creates these users on startup:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@taskflow.dev` | `Admin123!` |
| User | `user@taskflow.dev` | `User123!` |

## API Highlights

- `POST /auth/register`
- `POST /auth/login`
- `GET /users/me`
- `GET /admin/users`
- `GET /tasks`
- `POST /tasks`
- `PATCH /tasks/{task_id}`
- `POST /tasks/{task_id}/comments`
- `POST /tasks/{task_id}/attachments`
- `GET /dashboard/summary`
- `GET /reports/tasks`

## Testing

```powershell
cd backend
pytest
```

## Resume Bullet

Developed a full-stack task management platform using React and Python FastAPI with secure JWT authentication and role-based access control. Built REST APIs for task assignment, dashboard analytics, comments, upload metadata, search/filtering, reports, and user administration. Integrated SQLAlchemy database models, responsive React views, Docker Compose, CI checks with GitHub Actions, and deployment configs for Vercel and Render.
