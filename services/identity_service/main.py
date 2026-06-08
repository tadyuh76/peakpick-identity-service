from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from shared.auth import (
    AuthPrincipal,
    create_access_token,
    password_hash,
    principal_from_authorization,
    public_user,
)
from shared.logging import configure_logging, install_api_logging, log_event
from shared.settings import get_settings
from shared.tenancy import DEFAULT_STORE_ID


settings = get_settings("identity-service")
logger = configure_logging(settings.service_name)

DEMO_STORES = [
    {"store_id": "store-ueh", "name": "UEH Campus Store", "active": True},
    {"store_id": "store-d1", "name": "District 1 Store", "active": True},
]
DEMO_USERS = [
    {
        "username": "admin@peakpick.local",
        "password_hash": password_hash("admin123"),
        "role": "admin",
        "store_id": DEFAULT_STORE_ID,
        "display_name": "PeakPick Admin",
        "active": True,
    },
    {
        "username": "manager.ueh@peakpick.local",
        "password_hash": password_hash("manager123"),
        "role": "store_manager",
        "store_id": "store-ueh",
        "display_name": "UEH Store Manager",
        "active": True,
    },
    {
        "username": "manager.d1@peakpick.local",
        "password_hash": password_hash("manager123"),
        "role": "store_manager",
        "store_id": "store-d1",
        "display_name": "District 1 Store Manager",
        "active": True,
    },
]


class LoginRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=1)


def _database_enabled() -> bool:
    return bool(settings.database_url)


async def _find_user(username: str) -> dict[str, Any] | None:
    if not _database_enabled():
        return next((user for user in DEMO_USERS if user["username"] == username), None)
    return await asyncio.to_thread(_find_user_sync, username)


def _find_user_sync(username: str) -> dict[str, Any] | None:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        row = conn.execute(
            """
            SELECT username, password_hash, role, store_id, display_name, active
            FROM identity_users
            WHERE username = %s
            """,
            (username,),
        ).fetchone()
        return dict(row) if row else None


async def _list_stores() -> list[dict[str, Any]]:
    if not _database_enabled():
        return DEMO_STORES
    return await asyncio.to_thread(_list_stores_sync)


def _list_stores_sync() -> list[dict[str, Any]]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        rows = conn.execute(
            """
            SELECT store_id, name, active
            FROM stores
            ORDER BY store_id
            """
        ).fetchall()
        return [dict(row) for row in rows]


def _principal_from_user(user: dict[str, Any]) -> AuthPrincipal:
    return AuthPrincipal(
        username=str(user["username"]),
        role=str(user["role"]),
        store_id=str(user["store_id"]),
        display_name=str(user["display_name"]),
    )


app = FastAPI(
    title="PeakPick Identity Service",
    version="0.1.0",
    description="Demo authentication, roles, and store tenant identity.",
)
install_api_logging(app, logger, settings.service_name)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/auth/login")
async def login(payload: LoginRequest) -> dict[str, object]:
    user = await _find_user(payload.username.strip().lower())
    if not user or not user.get("active") or user["password_hash"] != password_hash(payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    principal = _principal_from_user(user)
    token = create_access_token(
        {
            "sub": principal.username,
            "role": principal.role,
            "store_id": principal.store_id,
            "display_name": principal.display_name,
        }
    )
    log_event(
        logger,
        settings.service_name,
        "user logged in",
        username=principal.username,
        role=principal.role,
        store_id=principal.store_id,
    )
    return {"access_token": token, "token_type": "bearer", "user": public_user(principal)}


@app.get("/auth/me")
async def me(authorization: str | None = Header(default=None)) -> dict[str, str]:
    return public_user(principal_from_authorization(authorization))


@app.get("/stores")
async def stores() -> list[dict[str, Any]]:
    return [store for store in await _list_stores() if store["active"]]
