# CareerForge AI

CareerForge AI is an AI-powered career, placement, and interview intelligence platform for students. It will help students manage career information, prepare for roles, and make informed job-application decisions. AI, database, and authentication capabilities will be introduced progressively in later phases.

## Technology stack

- Frontend: React, TypeScript, and Vite
- Backend: Python, FastAPI, and Uvicorn
- Planned data layer: PostgreSQL with SQLAlchemy and Alembic
- Planned AI capabilities: an LLM abstraction, structured outputs, embeddings, and RAG where they offer a real benefit

## Current development phase

**Phase 3 — Login and JWT authentication.** The backend now includes secure user login, JWT-based access tokens, and a protected authenticated-user endpoint. Frontend authentication and refresh tokens remain intentionally out of scope.

## Local development

### Frontend

```powershell
cd D:\careerforge-ai\frontend
npm install
npm run dev
```

Vite serves the frontend at the URL it prints, normally `http://localhost:5173`.

### Backend

```powershell
cd D:\careerforge-ai\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/` for its status response and `http://127.0.0.1:8000/docs` for Swagger UI.

### Registration endpoint

```http
POST /api/v1/auth/register
```

Request body:

```json
{
  "email": "student@example.com",
  "password": "StrongPass123!",
  "full_name": "Student Name"
}
```

The backend normalizes the email, validates the password strength, hashes the password with bcrypt, persists the user record to PostgreSQL, and returns a safe user payload without exposing `password` or `password_hash`.

### Login and JWT authentication

```http
POST /api/v1/auth/login
```

Request body:

```json
{
  "email": "student@example.com",
  "password": "StrongPass123!"
}
```

The login endpoint validates credentials, verifies the stored bcrypt hash, and returns a JWT access token. Use the token in the `Authorization: Bearer <token>` header for protected endpoints such as:

```http
GET /api/v1/auth/me
```

The application requires a secure `JWT_SECRET` environment variable defined in the local backend `.env` file.

### Database migrations

```powershell
cd D:\careerforge-ai\backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Alembic is used for schema management so the application table definitions remain reproducible and do not rely on `Base.metadata.create_all()`.

## Project structure

```text
careerforge-ai/
├── frontend/             # React + TypeScript + Vite foundation
├── backend/              # FastAPI foundation
│   ├── app/              # API application package
│   └── tests/            # Backend tests, added progressively
├── docs/                 # Architecture and project documentation
├── AGENTS.md             # Project development rules
├── .env.example          # Shared environment-variable example
└── .gitignore
```
