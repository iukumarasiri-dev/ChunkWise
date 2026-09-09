"""FastAPI application entrypoint.

Run from the backend/ folder:
    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import documents as db
from app.api import documents as documents_api
from app.api import upload as upload_api
from app.api import query as query_api

# Show our own INFO logs (e.g. "Ingested … N chunks", ingestion failures) in the
# server console. basicConfig is a no-op if the root logger already has handlers,
# so also raise the level on the "app" hierarchy explicitly.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("app").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup, before the server accepts requests.
    settings = get_settings()
    settings.ensure_dirs()
    db.init_db()

    swept = db.fail_stale_processing()
    if swept:
        print(f"[startup] marked {swept} interrupted document(s) as failed")

    yield


app = FastAPI(title="ChunkWise", version="0.1.0", lifespan=lifespan)

# The frontend dev server runs on :5173 and proxies /api to us. The proxy makes
# requests same-origin, so CORS isn't strictly required, but allowing it means a
# direct browser call to :8000 also works.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_api.router)
app.include_router(upload_api.router)
app.include_router(query_api.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
