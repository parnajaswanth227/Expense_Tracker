"""
api/middleware.py
─────────────────
Pure ASGI JWT middleware — NOT BaseHTTPMiddleware.

Why pure ASGI?
──────────────
  BaseHTTPMiddleware has a known bug: context vars set inside it do NOT
  propagate into the route handler via call_next, because it uses anyio
  task groups which create a fresh context copy.

  A pure ASGI middleware just awaits self.app(scope, receive, send) in the
  SAME task, so context vars set here are visible everywhere downstream —
  including inside FastMCP tool calls.

Public paths (no token required)
──────────────────────────────────
  /auth/token      — login
  /auth/register   — signup
  /health          — liveness probe
  /docs            — Swagger UI
  /redoc           — ReDoc
  /openapi.json    — OpenAPI spec
  /favicon.ico     — browser icon

Every other path (including /mcp/*) requires:
  Authorization: Bearer <jwt_token>
"""

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from api.auth import verify_token
from context import current_user
from logger import get_logger

log = get_logger("middleware")

_PUBLIC: frozenset = frozenset({
    "/auth/token",
    "/auth/register",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
})


class JWTMiddleware:
    """
    Pure ASGI middleware that:
      1. Passes public paths straight through.
      2. Extracts and validates the Bearer JWT on all other paths.
      3. Sets current_user ContextVar so every tool knows who is calling.
      4. Returns 401 immediately if token is missing or invalid.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only handle HTTP — pass WebSocket / lifespan straight through
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        path   = scope.get("path", "")
        method = scope.get("method", "")

        # ── Pass OPTIONS (CORS preflight) straight through ────────────────────
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # ── Pass public paths straight through ────────────────────────────────
        if (
            path in _PUBLIC
            or path.startswith("/docs/")
            or path.startswith("/.well-known")
        ):
            await self.app(scope, receive, send)
            return

        # ── Extract Bearer token ──────────────────────────────────────────────
        headers     = dict(scope.get("headers", []))
        auth_bytes  = headers.get(b"authorization", b"")
        auth_header = auth_bytes.decode("utf-8", errors="ignore")

        if not auth_header.startswith("Bearer "):
            log.warning(f"Missing/malformed Authorization header | path={path}")
            response = JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "Authorization header missing or malformed. "
                        "Expected:  Authorization: Bearer <token>  |  "
                        "Get a token via:  POST /auth/token"
                    )
                },
            )
            await response(scope, receive, send)
            return

        token = auth_header.split(" ", 1)[1]
        user  = verify_token(token)

        if not user:
            log.warning(f"Invalid or expired token | path={path}")
            response = JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "Token is invalid or has expired. "
                        "Get a new token via:  POST /auth/token"
                    )
                },
            )
            await response(scope, receive, send)
            return

        # ── Set context var + forward request ─────────────────────────────────
        # context var is visible to ALL awaited code in this same task,
        # which includes FastMCP's tool dispatch.
        log.debug(f"Auth OK | user='{user}' | path={path}")
        ctx_token = current_user.set(user)
        try:
            await self.app(scope, receive, send)
        finally:
            current_user.reset(ctx_token)
