"""
db.py
─────
Fully async PostgreSQL layer (psycopg v3).
Single execute_query() works for both stdio and HTTP modes.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from config import DATABASE_URL, DB_CONFIG
from logger import get_logger

log = get_logger("db")


def _cast(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _cast_row(row: dict) -> dict:
    return {k: _cast(v) for k, v in row.items()}


async def _get_connection() -> psycopg.AsyncConnection:
    if DATABASE_URL:
        log.debug("DB → cloud (DATABASE_URL)")
        return await psycopg.AsyncConnection.connect(DATABASE_URL, row_factory=dict_row)
    log.debug("DB → local PostgreSQL")
    return await psycopg.AsyncConnection.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        row_factory=dict_row,
    )


async def execute_query(
    query: str,
    params: Any = None,
    fetch: bool = False,
) -> list[dict] | None:
    """
    Execute SQL asynchronously.

    Args:
        query:  SQL with %s placeholders.
        params: Tuple / list of parameters.
        fetch:  Return rows when True.

    Returns:
        list[dict] if fetch=True, else None.
    """
    try:
        async with await _get_connection() as conn:
            async with conn.cursor() as cur:
                log.debug(f"SQL: {query.strip()[:100]}")
                await cur.execute(query, params)
                if fetch:
                    rows = await cur.fetchall()
                    return [_cast_row(dict(r)) for r in rows]
                return None
    except psycopg.Error as exc:
        log.error(f"DB error | {exc}")
        raise
