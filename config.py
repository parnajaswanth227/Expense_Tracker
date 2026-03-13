"""
config.py
─────────
Central configuration from environment variables.

REQUIRED:
    SECRET_KEY           — JWT signing key
    AND one of:
      DATABASE_URL       — Neon / cloud Postgres connection string
      OR: DB_HOST + DB_PORT + DB_NAME + DB_USER + DB_PASSWORD

OPTIONAL:
    ACCESS_TOKEN_EXPIRE_MINUTES  — default 525600 (1 year)
    ALLOW_REGISTRATION           — "true" / "false"  (default: true)
    EXPORT_DIR                   — CSV export directory
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(
            f"\n❌  [CONFIG ERROR]  Required env var '{name}' is not set.\n"
            f"    Fix: cp .env.example .env  then fill in '{name}'\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
_db_password: str = os.getenv("DB_PASSWORD", "").strip()

if not DATABASE_URL and not _db_password:
    print(
        "\n❌  [CONFIG ERROR]  No database configured.\n"
        "    Set DATABASE_URL (Neon) OR DB_HOST+DB_PORT+DB_NAME+DB_USER+DB_PASSWORD\n",
        file=sys.stderr,
    )
    sys.exit(1)

DB_CONFIG: dict = {
    "host":     os.getenv("DB_HOST",  "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",  "expense_tracker"),
    "user":     os.getenv("DB_USER",  "postgres"),
    "password": _db_password,
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SECRET_KEY:                  str = _require("SECRET_KEY")
ALGORITHM:                   str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "525600"))

# ── Registration control ──────────────────────────────────────────────────────
# Set ALLOW_REGISTRATION=false in .env to lock down new signups after setup.
ALLOW_REGISTRATION: bool = os.getenv("ALLOW_REGISTRATION", "true").strip().lower() == "true"

# ── CSV export directory ──────────────────────────────────────────────────────
EXPORT_DIR: str = os.getenv(
    "EXPORT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports"),
).strip()
os.makedirs(EXPORT_DIR, exist_ok=True)
