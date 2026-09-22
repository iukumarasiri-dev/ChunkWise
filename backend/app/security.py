"""Shared-secret API key auth.

Protects every endpoint except /health. Set API_KEY in backend/.env to turn
it on; leave it blank for frictionless local development (auth is skipped).
Required before exposing the app beyond localhost — e.g. via a tunnel.
"""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from app.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().api_key
    if not expected:
        return  # auth disabled - no API_KEY configured
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
