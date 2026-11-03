# CareerForge AI architecture

CareerForge AI is a modular monolith so features can evolve together without premature distributed-system complexity.

```text
React frontend (foundation; feature UI not yet implemented)
      ↓
REST API
      ↓
FastAPI routes -> authentication / feature services
      ↓
Repositories -> SQLAlchemy -> PostgreSQL
```

The current backend includes registration, JWT authentication, student profiles and skills, plus an authenticated resume PDF text-extraction endpoint. Persistent features follow the route -> service -> repository -> database flow. The Phase 5A resume endpoint intentionally does not use a repository or database model: it reads a PDF upload in bounded chunks, parses and extracts text in memory, returns the text and page count, and closes the upload without persisting the PDF or extracted text. Starlette's multipart parser may temporarily spool uploads to the operating system's temporary directory; this is request-scoped buffering, not application or database persistence.

The resume endpoint accepts PDF content only, with a 5 MiB upload limit, a 100-page limit, a 5 MiB per-stream decoded-data limit, a 20 MiB PDF decoding-work budget, and a 200,000-character extracted-text limit. It rejects empty, malformed, encrypted, and textless PDFs with safe client errors. Scanned-document OCR is not provided. Job-description analysis, compatibility scoring, AI, and RAG remain future phases; any AI functionality will live behind backend services and return validated, structured outputs rather than being called directly from the frontend.
