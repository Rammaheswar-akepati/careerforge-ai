# CareerForge AI architecture

CareerForge AI is a modular monolith. Its frontend, API, feature services, and persistence layer are kept in one application so features can evolve together without premature distributed-system complexity.

## Application flow

```text
React frontend
      ↓
Frontend API client
      ↓
REST API
      ↓
FastAPI routes
      ↓
Authentication and request dependencies
      ↓
Feature services
      ↓
Repositories
      ↓
SQLAlchemy models
      ↓
PostgreSQL
```

The React application provides registration and login, authenticated user retrieval, and resume upload and management. Its API client attaches bearer tokens to protected requests, handles `204 No Content`, and converts common network and HTTP failures into safe messages. Authentication state, including the access token, is held in React memory; it is not restored after a page reload.

The FastAPI application includes versioned authentication, profile, and resume routes. Protected routes resolve the current active user from the bearer token through a shared dependency. Feature services coordinate business logic, repositories perform database operations through SQLAlchemy, and the models define persisted entities and relationships.

## Resume processing and management

Two authenticated upload endpoints serve different purposes:

- `POST /api/v1/resumes/extract-text` validates and extracts text from a PDF and returns the text and page count without saving either the PDF or extracted text to the application database.
- `POST /api/v1/resumes` extracts text and persists that text and its metadata for the authenticated user. The resume service does not retain the uploaded PDF.

PDF processing reads the upload in bounded chunks and enforces a 5 MiB upload limit, a 100-page limit, a 5 MiB decoded-stream limit, a 20 MiB stream-decoding work budget, and a 200,000-character extracted-text limit. Empty, malformed, encrypted, and textless PDFs are rejected with safe client errors. OCR for scanned documents is not implemented. Starlette's multipart parser may temporarily spool upload data to the operating system's temporary directory while parsing the request.

Persisted resumes are owner-scoped:

- `GET /api/v1/resumes` returns paginated metadata for the authenticated user.
- `GET /api/v1/resumes/{resume_id}` returns a resume, including extracted text, only if it belongs to that user. The frontend calls this detail endpoint to display the resume preview.
- `DELETE /api/v1/resumes/{resume_id}` deletes only a resume belonging to that user and returns `204 No Content`.

The resume service uses the resume repository to create, list, retrieve, and delete records. Repository queries filter by the authenticated user's ID; requests for missing and non-owned resume IDs return not found.

## Data and future features

PostgreSQL stores user, student-profile, and resume data through SQLAlchemy models and Alembic-managed schema changes. The extraction-only endpoint does not use the persistence path. Resume upload through the management endpoint persists extracted text and metadata; it does not persist the original PDF.

AI resume analysis, job-description analysis, Compatibility Scores, skill-gap recommendations, learning plans, and RAG are future capabilities and are not part of the current implementation. When introduced, AI processing will remain behind backend services and use validated structured outputs rather than being called directly from the frontend.
