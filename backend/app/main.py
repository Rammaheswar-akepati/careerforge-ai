from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.resumes import router as resumes_router

app = FastAPI(title="CareerForge AI API")
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resumes_router)


@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    """Return a simple API availability response."""
    return {"status": "CareerForge API is running"}
