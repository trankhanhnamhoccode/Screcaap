"""FastAPI application bootstrap."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.routes.captures import router as captures_router

app = FastAPI(title="Screcaap")
app.include_router(captures_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process is responding."""
    return {"status": "ok"}
