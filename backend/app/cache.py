"""Tiny SQLite response cache — keyed on question + schema + provider + model."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from .config import settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "response-cache.sqlite"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.execute(
        "CREATE TABLE IF NOT EXISTS cache ("
        " key TEXT PRIMARY KEY, value TEXT NOT NULL, created_at INTEGER NOT NULL)"
    )
    return c


def _key(parts: dict[str, Any]) -> str:
    blob = json.dumps(parts, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def get(parts: dict[str, Any]) -> Any | None:
    if settings.response_cache_ttl <= 0:
        return None
    k = _key(parts)
    with _conn() as c:
        row = c.execute("SELECT value, created_at FROM cache WHERE key=?", (k,)).fetchone()
    if not row:
        return None
    value, created = row
    if time.time() - created > settings.response_cache_ttl:
        return None
    return json.loads(value)


def set_(parts: dict[str, Any], value: Any) -> None:
    if settings.response_cache_ttl <= 0:
        return
    k = _key(parts)
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?, ?, ?)",
            (k, json.dumps(value, default=str), int(time.time())),
        )
