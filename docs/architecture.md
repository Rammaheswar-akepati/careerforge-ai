# Initial architecture

CareerForge AI starts as a modular monolith so its parts can evolve together without premature distributed-system complexity.

```text
React frontend
      ↓
REST API
      ↓
FastAPI backend
      ↓
Service layer
      ↓
Repository/data layer
      ↓
PostgreSQL
```

Phase 0 establishes only the React/Vite frontend foundation and a FastAPI health endpoint. The service and repository layers will be introduced with the features that need them; PostgreSQL is not configured yet.

AI and RAG components—including resume analysis, job-description analysis, compatibility matching, embeddings, retrieval, and interview support—will be added in later phases behind dedicated backend services. They will use validated, structured outputs and will not be exposed directly from the frontend.
