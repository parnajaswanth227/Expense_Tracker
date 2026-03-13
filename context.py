"""
context.py
──────────
Single ContextVar that holds the authenticated username for the current request.

How it works
────────────
  1. JWTMiddleware validates the Bearer token and calls current_user.set(username)
  2. Because this is a pure ASGI middleware (not BaseHTTPMiddleware), the context
     propagates correctly through every awaited call in the same request.
  3. Every tool reads uid = current_user.get() to scope its DB queries to that user.
  4. No username is ever passed as a tool argument — Claude never sees it.
"""

from contextvars import ContextVar

current_user: ContextVar[str] = ContextVar("current_user", default="")
