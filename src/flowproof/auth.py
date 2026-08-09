from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

KEY_PREFIX = "fpk_"
SESSION_TTL_SECONDS = 7 * 24 * 3600


def _hash_password(password: str, salt: bytes) -> str:
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return f"{salt.hex()}${derived.hex()}"


def hash_password(password: str) -> str:
    return _hash_password(password, secrets.token_bytes(16))


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, _ = stored.split("$", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, stored)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ApiKey:
    id: int
    label: str
    prefix: str
    created_at: int


class AuthError(Exception):
    pass


class AuthStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    label TEXT NOT NULL,
                    prefix TEXT NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    created_at INTEGER NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at INTEGER NOT NULL
                );
                """
            )

    def create_user(self, email: str, password: str) -> int:
        email = email.strip().lower()
        if "@" not in email or len(password) < 8:
            raise AuthError("invalid email or password too short")
        with self._conn() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                    (email, hash_password(password), int(time.time())),
                )
            except sqlite3.IntegrityError as exc:
                raise AuthError("email already registered") from exc
            return int(cur.lastrowid)

    def authenticate(self, email: str, password: str) -> int:
        email = email.strip().lower()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, password_hash FROM users WHERE email = ?", (email,)
            ).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            raise AuthError("invalid credentials")
        return int(row["id"])

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (_hash_token(token), user_id, int(time.time()) + SESSION_TTL_SECONDS),
            )
        return token

    def user_for_session(self, token: str) -> int | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id, expires_at FROM sessions WHERE token_hash = ?",
                (_hash_token(token),),
            ).fetchone()
        if not row or row["expires_at"] < int(time.time()):
            return None
        return int(row["user_id"])

    def create_api_key(self, user_id: int, label: str) -> str:
        token = KEY_PREFIX + secrets.token_hex(24)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO api_keys (user_id, label, prefix, token_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, label[:80] or "key", token[:12], _hash_token(token), int(time.time())),
            )
        return token

    def list_api_keys(self, user_id: int) -> list[ApiKey]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, label, prefix, created_at FROM api_keys "
                "WHERE user_id = ? AND revoked = 0 ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [ApiKey(r["id"], r["label"], r["prefix"], r["created_at"]) for r in rows]

    def revoke_api_key(self, user_id: int, key_id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE api_keys SET revoked = 1 WHERE id = ? AND user_id = ?",
                (key_id, user_id),
            )
            return cur.rowcount > 0

    def user_for_api_key(self, token: str) -> int | None:
        if not token.startswith(KEY_PREFIX):
            return None
        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id FROM api_keys WHERE token_hash = ? AND revoked = 0",
                (_hash_token(token),),
            ).fetchone()
        return int(row["user_id"]) if row else None


def default_store() -> AuthStore:
    base = os.environ.get("FLOWPROOF_RUNS_DIR", str(Path.home() / ".flowproof" / "runs"))
    return AuthStore(Path(base).parent / "flowproof.db")
