"""
Root-level entry point for FastMCP hosting.
Entry point: app.py:app
"""
import sys
import os

# Windows compatibility (no-op on Linux)
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.auth import authenticate_user, create_access_token, create_user
from api.middleware import JWTMiddleware
from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALLOW_REGISTRATION
from init_db import init_db
from main import mcp

# MCP sub-app
mcp_app = mcp.http_app(path="/mcp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with mcp_app.router.lifespan_context(mcp_app):
        yield


app = FastAPI(
    title="Expense Tracker MCP",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(JWTMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in_minutes: int

class RegisterResponse(BaseModel):
    status: str
    username: str
    message: str


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=RegisterResponse)
async def register(body: RegisterRequest):
    if not ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="Registration is currently disabled.")
    result = await create_user(body.username, body.password)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return RegisterResponse(
        status="created",
        username=result["username"],
        message=f"Account created for '{result['username']}'.",
    )


@app.post("/auth/token", response_model=TokenResponse)
async def login(body: LoginRequest):
    ok = await authenticate_user(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    token = create_access_token({"sub": body.username.strip().lower()})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "server": "Expense Tracker MCP v3",
        "registration": ALLOW_REGISTRATION,
    }


@app.get("/register", response_class=HTMLResponse)
def register_page():
    """Serve the user-facing registration + token setup page."""
    # Works whether deployed or local
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "register.html")
    with open(static_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── Mount MCP routes ──────────────────────────────────────────────────────────
for route in mcp_app.routes:
    app.router.routes.append(route)