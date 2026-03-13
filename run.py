"""
run.py
──────
Windows-safe uvicorn launcher for Expense Tracker MCP v3.

ROOT CAUSE
──────────
uvicorn.run() calls asyncio.run() internally, which on Windows always
creates a ProactorEventLoop regardless of any policy you set beforehand.
set_event_loop_policy() only affects NEW loops created via get_event_loop(),
not loops created directly by asyncio.run().

THE FIX
───────
We call asyncio.run() ourselves with loop_factory=SelectorEventLoop.
This guarantees SelectorEventLoop is used — uvicorn then uses
whatever loop is already running instead of creating its own.

This is the exact fix psycopg recommends in its own error message.

USAGE
─────
  python run.py
  python run.py --port 8001
  python run.py --host 0.0.0.0 --port 8000
  python run.py --reload
"""

import argparse
import asyncio
import selectors
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Expense Tracker MCP v3")
    parser.add_argument("--host",   default="127.0.0.1", help="Bind host  (default: 127.0.0.1)")
    parser.add_argument("--port",   default=8000, type=int, help="Bind port  (default: 8000)")
    parser.add_argument("--reload", action="store_true",   help="Auto-reload on code changes (dev)")
    return parser.parse_args()


async def _serve(host: str, port: int, reload: bool) -> None:
    import uvicorn
    config = uvicorn.Config(
        "api.server:app",
        host=host,
        port=port,
        reload=reload,
        loop="none",   # tell uvicorn NOT to create its own loop — use ours
    )
    server = uvicorn.Server(config)
    await server.serve()


def _selector_loop_factory():
    """Always returns a SelectorEventLoop — the one psycopg needs."""
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


if __name__ == "__main__":
    args = parse_args()

    print("🚀  Expense Tracker MCP v3")
    print(f"    Host : {args.host}")
    print(f"    Port : {args.port}")
    print(f"    Docs : http://{args.host}:{args.port}/docs")
    print()

    if sys.platform == "win32":
        # loop_factory forces SelectorEventLoop on Windows.
        # asyncio.run() with loop_factory is available from Python 3.12+.
        asyncio.run(
            _serve(args.host, args.port, args.reload),
            loop_factory=_selector_loop_factory,
        )
    else:
        # Linux/Mac already use SelectorEventLoop by default.
        asyncio.run(_serve(args.host, args.port, args.reload))