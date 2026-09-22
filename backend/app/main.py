"""FastAPI application entrypoint.

Run from the backend/ folder:
    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import documents as db
from app.api import documents as documents_api
from app.api import upload as upload_api
from app.api import query as query_api
from app.security import require_api_key

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

    if not settings.api_key:
        logging.getLogger("app").warning(
            "API_KEY is not set - all endpoints are open to anyone who can "
            "reach this server. Set API_KEY in backend/.env before exposing "
            "it beyond localhost."
        )

    yield


app = FastAPI(title="ChunkWise", version="0.1.0", lifespan=lifespan)

# The frontend dev server runs on :5173 and proxies /api to us. The proxy makes
# requests same-origin, so CORS isn't strictly required, but allowing it means a
# direct browser call to :8000 also works. In production, FRONTEND_ORIGIN should
# be set to the deployed frontend's URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth = [Depends(require_api_key)]
app.include_router(documents_api.router, dependencies=_auth)
app.include_router(upload_api.router, dependencies=_auth)
app.include_router(query_api.router, dependencies=_auth)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
