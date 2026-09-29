# CareerForge AI

CareerForge AI is an AI-powered career, placement, and interview intelligence platform for students. It will help students manage career information, prepare for roles, and make informed job-application decisions. AI, database, and authentication capabilities will be introduced progressively in later phases.

## Technology stack

- Frontend: React, TypeScript, and Vite
- Backend: Python, FastAPI, and Uvicorn
- Planned data layer: PostgreSQL with SQLAlchemy and Alembic
- Planned AI capabilities: an LLM abstraction, structured outputs, embeddings, and RAG where they offer a real benefit

## Current development phase

**Phase 0 — Foundation.** The repository currently contains a minimal React/Vite frontend and FastAPI backend health endpoint. No authentication, database, or AI functionality has been implemented.

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
