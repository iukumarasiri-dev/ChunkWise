"""FastAPI application entrypoint.

Run from the backend/ folder:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import documents as db
from app.api import documents as documents_api   





@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_dirs()
    db.init_db() 
    app.include_router(documents_api.router)
    yield


app = FastAPI(title="ChunkWise", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
