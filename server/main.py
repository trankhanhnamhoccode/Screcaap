"""FastAPI application bootstrap."""

from fastapi import FastAPI

app = FastAPI(title="Screcaap")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process is responding."""
    return {"status": "ok"}
