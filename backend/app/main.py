from fastapi import FastAPI

app = FastAPI(title="CareerForge AI API")


@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    """Return a simple API availability response."""
    return {"status": "CareerForge API is running"}
