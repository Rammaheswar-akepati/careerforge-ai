# CareerForge AI — Project Instructions

## Project purpose

Build **CareerForge AI**, a production-style final-year project for career, placement, and interview preparation. Optimize for learning, maintainability, correctness, security, and portfolio quality—not speed of code generation.

## Development workflow

- Build one major phase at a time, in this order: foundation, authentication, student profile, resumes, jobs, AI analysis, compatibility matching, skill gaps, learning plans, application tracking, RAG, interview preparation, mock interviews, analytics, testing, Docker/CI, deployment, and final documentation.
- Before changing existing code, inspect the repository and preserve working behavior.
- For every major feature, explain what is being built, why it exists, where it fits, the files affected, core concepts, how to run/test it, common debugging points, and relevant interview questions.
- After each major phase: implement and test only that phase; report files changed, commands run, results/issues; then stop for user confirmation before starting the next phase.
- Do not claim tests, features, metrics, AI results, or integrations work unless they were actually verified.

## Architecture

- Use a modular monolith. Avoid microservices, Kubernetes, Kafka, and unnecessary infrastructure.
- Default flow: React frontend -> REST API -> FastAPI route -> service layer -> repository/data layer -> PostgreSQL -> response.
- Keep frontend, backend, database, and AI concerns separated with small, readable, typed components/functions.
- Intended stack: React + TypeScript + Vite, React Router, TanStack Query, Tailwind CSS, Recharts; FastAPI, Pydantic, SQLAlchemy, Alembic; PostgreSQL (pgvector only when RAG/semantic search needs it).
- Add database entities progressively with the features they support; use appropriate relationships, constraints, and indexes.

## AI features

- Treat AI as a real subsystem behind FastAPI services, not a demo chatbot.
- Use an LLM-provider abstraction, structured outputs validated by Pydantic, error handling, timeouts/retries where appropriate, and safe metadata logging.
- Never expose API keys or secrets to the frontend. Do not trust AI output blindly.
- Label AI-generated feedback/information clearly and distinguish it from verified application data.
- Resume/job matching must be called a **Compatibility Score**, never a hiring prediction. Explain matched, partially matched, and missing skills.
- Use embeddings, pgvector, RAG, LangChain, or LangGraph only when they deliver a concrete need. Do not download local AI models without explicit approval.

## Security and data rules

- Never hardcode, commit, log, or expose secrets. Use `.env` locally and maintain `.env.example` when configuration is introduced.
- Implement secure password hashing, JWT access/refresh handling, authorization/ownership checks, input validation, upload validation, safe errors, and suitable rate/cost controls as relevant phases are built.
- AI extraction must not silently overwrite information entered manually by a user.
- Do not web-scrape jobs unless the user explicitly approves it.

## Storage and environment

- Keep all project work under `D:\careerforge-ai`; avoid intentionally placing project environments, dependencies, caches, models, or datasets on `C:`.
- npm cache is `D:\npm-cache`; pip cache is `D:\pip-cache`.
- When approved, create the Python environment at `D:\careerforge-ai\backend\.venv` and frontend dependencies at `D:\careerforge-ai\frontend\node_modules`.
- Before a potentially large install/download, explain what will be downloaded, why, and its approximate storage impact. Never install dependencies, create environments, run Docker, or download models without task/user authorization.

## Quality, testing, and documentation

- Prefer clear names, small functions, reusable components, separation of concerns, type safety, environment configuration, and real error handling. Avoid giant files, duplication, unnecessary dependencies/abstractions, hardcoded values, and fake placeholders presented as complete.
- Add tests progressively: pytest/API/integration/security tests for backend; Vitest/React Testing Library for frontend; structured-output, retrieval-relevance, grounding/citation, and feedback-consistency checks for AI.
- Maintain useful project documentation as features warrant it: `README.md`, `docs/architecture.md`, `docs/database.md`, `docs/api.md`, `docs/security.md`, `docs/ai-architecture.md`, and `docs/ai-evaluation.md`.

## Git practices

- Repository: `https://github.com/Rammaheswar-akepati/careerforge-ai.git`; default branch: `main`.
- Use focused, meaningful commits when asked (for example, `feat: add authentication`).
- Never commit or push automatically; do so only with explicit user instruction.
