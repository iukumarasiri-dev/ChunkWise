"""FastAPI application entrypoint.

Wires together the API routers (upload, documents, query) and app-level
middleware. Run with: ``uvicorn app.main:app --reload``
"""

from fastapi import FastAPI

# from app.api import upload, documents, query

app = FastAPI(title="ChunkWise", version="0.1.0")

# app.include_router(upload.router)
# app.include_router(documents.router)
# app.include_router(query.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
