"""
api/auth.py
───────────
Database-backed user authentication with bcrypt password hashing.

Key differences from V2 (single-user)
──────────────────────────────────────
  • Users are stored in the `users` DB table, not in .env
  • Passwords are hashed with bcrypt — never stored plain text
  • create_user()      — register a new user (called from /auth/register)
  • authenticate_user() — query DB + verify bcrypt hash
  • verify_token() and create_access_token() are unchanged from V2
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from db import execute_query
from logger import get_logger

log = get_logger("auth")


# ── Password hashing (direct bcrypt — no passlib) ─────────────────────────────
def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt. Returns a utf-8 string."""
    # bcrypt has a 72-byte hard limit — we SHA-256 the password first
    # so any length password works safely.
    import hashlib
    key = hashlib.sha256(password.encode()).hexdigest().encode()
    return bcrypt.hashpw(key, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    import hashlib
    key = hashlib.sha256(plain.encode()).hexdigest().encode()
    return bcrypt.checkpw(key, hashed.encode("utf-8"))


# ── User management ───────────────────────────────────────────────────────────

async def create_user(username: str, password: str) -> dict:
    """
    Register a new user.

    Args:
        username: Must be unique, 3–50 chars, alphanumeric + underscore only.
        password: Must be at least 8 characters.

    Returns:
        {"status": "created", "username": str}  on success.
        {"error": str}                           on failure.
    """
    username = username.strip().lower()

    if not username or len(username) < 3:
        return {"error": "Username must be at least 3 characters."}
    if len(username) > 50:
        return {"error": "Username must be 50 characters or fewer."}
    if not all(c.isalnum() or c == "_" for c in username):
        return {"error": "Username can only contain letters, numbers, and underscores."}
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters."}

    # Check if username already exists
    existing = await execute_query(
        "SELECT id FROM users WHERE username = %s", (username,), fetch=True
    )
    if existing:
        return {"error": f"Username '{username}' is already taken."}

    hashed = hash_password(password)
    await execute_query(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed),
    )
    log.info(f"create_user | new user registered: '{username}'")
    return {"status": "created", "username": username}


async def authenticate_user(username: str, password: str) -> bool:
    """
    Verify credentials against the users table.

    Returns:
        True if username exists and password matches the bcrypt hash.
        False otherwise.
    """
    username = username.strip().lower()

    result = await execute_query(
        "SELECT password FROM users WHERE username = %s",
        (username,),
        fetch=True,
    )

    if not result:
        log.warning(f"authenticate_user | unknown user: '{username}'")
        return False

    stored_hash = result[0]["password"]

    if not verify_password(password, stored_hash):
        log.warning(f"authenticate_user | wrong password for: '{username}'")
        return False

    log.info(f"authenticate_user | success: '{username}'")
    return True


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """Create a signed JWT with expiry."""
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    log.info(f"Token issued for sub='{data.get('sub')}'")
    return token


def verify_token(token: str) -> str | None:
    """
    Decode and verify a JWT.

    Returns:
        username string on success, None on failure.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            log.warning("verify_token | no 'sub' claim")
            return None
        return username
    except JWTError as exc:
        log.warning(f"verify_token | {exc}")
        return None