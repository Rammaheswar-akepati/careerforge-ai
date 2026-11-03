# CareerForge AI

CareerForge AI is an AI-powered career, placement, and interview intelligence platform for students. It helps students manage career information and prepare for roles. AI capabilities will be introduced progressively in later phases.

## Technology stack

- Frontend: React, TypeScript, and Vite
- Backend: Python, FastAPI, and Uvicorn
- Data layer: PostgreSQL with SQLAlchemy and Alembic
- Planned AI capabilities: an LLM abstraction, structured outputs, embeddings, and RAG where they offer a real benefit

## Current development status

Phase 5A implements authenticated, bounded PDF text extraction. Phase 5B adds resume persistence and authenticated resume-management APIs. The React frontend supports registration, login, and resume upload, listing, preview, pagination, and deletion.

AI resume analysis, job-description matching, Compatibility Scores, and other AI features are planned for later phases and are not implemented yet.

## Implemented functionality

- Account registration and login, plus retrieval of the authenticated user's profile.
- Bearer-token authentication for protected API endpoints.
- PDF-only resume upload with bounded in-memory text extraction.
- Persistence of extracted text and resume metadata in PostgreSQL; uploaded PDF files are not retained by the resume application flow.
- Authenticated, owner-scoped resume listing with pagination, detail retrieval, and deletion.
- A React interface for authentication and resume upload, library management, preview, and deletion.
- Safe handling of common authentication, validation, network, and server errors.

The access token and user are held in React memory. Reloading the browser clears that state, so the user must sign in again. The frontend does not persist the token in browser storage.

## Local development

### Prerequisites

- Node.js `^20.19.0` or `>=22.12.0` and npm, as required by the installed Vite 7 release.
- Python and the backend dependencies installed in the project's backend virtual environment.
- PostgreSQL configured for the backend. The backend requires `DATABASE_URL` and `JWT_SECRET` in its local environment; do not commit real secrets.

### Frontend

```powershell
Set-Location D:\careerforge-ai\frontend
npm install
```

For local development, create `frontend\.env.local` and set:

```dotenv
VITE_API_BASE_URL=/backend
```

Then start the frontend:

```powershell
Set-Location D:\careerforge-ai\frontend
npm run dev
```

Vite prints the development URL when it starts. The API client requires `VITE_API_BASE_URL`; it does not supply a default. With `/backend` configured, the existing Vite development proxy forwards requests to `http://127.0.0.1:8000` and removes the `/backend` prefix before forwarding. This same-origin proxy is the intended local setup and avoids requiring browser cross-origin configuration.

The frontend template `frontend\.env.example` currently shows the direct backend URL `http://127.0.0.1:8000`. The API client accepts either a direct base URL or the proxy path, but the backend does not configure CORS middleware. For local browser development, use `/backend` in `.env.local` as shown above rather than relying on cross-origin access to the direct URL.

### Backend

```powershell
Set-Location D:\careerforge-ai\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

The API listens at `http://127.0.0.1:8000` with this Uvicorn command. Visit `/` for its status response and `/docs` for Swagger UI. Start PostgreSQL and configure the backend's required environment before using database-backed endpoints.

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

The frontend keeps the access token in React memory only. Reloading the browser clears the in-memory token and user state, so the user must sign in again.

### Persistent resume management

The authenticated resume-management API is separate from the extraction-only endpoint below:

| Method | Path | Behavior |
|---|---|---|
| `POST` | `/api/v1/resumes` | Accepts a PDF in the `file` multipart field, extracts its text, persists the extracted text and metadata for the current user, and returns the created resume details. The uploaded PDF is not stored by the resume service. |
| `GET` | `/api/v1/resumes?page=1&page_size=20` | Returns a paginated list of the current user's resume metadata. Page size must be from 1 to 100. |
| `GET` | `/api/v1/resumes/{resume_id}` | Returns a resume owned by the current user, including extracted text. The frontend uses this endpoint for preview. |
| `DELETE` | `/api/v1/resumes/{resume_id}` | Deletes a resume owned by the current user and returns `204 No Content`. |

These endpoints require a valid bearer token and scope reads and deletion to the authenticated owner. An absent resume and a resume belonging to another user both return not found.

### Resume PDF text extraction

```http
POST /api/v1/resumes/extract-text
Authorization: Bearer <access-token>
Content-Type: multipart/form-data
```

Send a PDF in the `file` multipart field. The endpoint accepts at most 5 MiB, rejects encrypted and textless PDFs, and limits documents to 100 pages, decoded streams to 5 MiB per stream with a 20 MiB processing budget, and extracted text to 200,000 characters. It returns the extracted text and page count. The endpoint parses from an in-memory buffer and does not retain the PDF or text after the request or save them to PostgreSQL. Starlette may temporarily spool multipart uploads to the operating system's temporary directory while parsing the request. Scanned PDFs requiring OCR are not supported.

The backend uses `python-multipart` to parse form uploads and `pypdf` to validate PDFs and extract text. Install backend requirements into `backend\.venv` before starting the API.

### Database migrations

```powershell
cd D:\careerforge-ai\backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Alembic is used for schema management so the application table definitions remain reproducible and do not rely on `Base.metadata.create_all()`.

### Backend tests

```powershell
cd D:\careerforge-ai\backend
.\.venv\Scripts\python.exe -m pytest
```

The test bootstrap overrides `DATABASE_URL` with a uniquely created temporary SQLite database under `backend/`, applies the Alembic migrations, verifies the active engine points to that database, and removes the temporary database after the test session. Tests do not connect to the application's configured database.

## Project structure

```text
careerforge-ai/
├── frontend/             # React + TypeScript + Vite application
├── backend/              # FastAPI API, services, repositories, and tests
│   ├── app/              # API application package
│   └── tests/            # Backend tests, added progressively
├── docs/                 # Architecture and project documentation
├── AGENTS.md             # Project development rules
├── .env.example          # Shared environment-variable example
└── .gitignore
```
