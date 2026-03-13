"""
init_db.py
──────────
Async database bootstrap: create tables + seed default categories.
Idempotent — safe to call on every startup.
"""

import asyncio
import json
import os

import psycopg
from psycopg.rows import dict_row

from config import DATABASE_URL, DB_CONFIG
from logger import get_logger

log = get_logger("init_db")

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH     = os.path.join(BASE_DIR, "schema.sql")
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")


async def _connect() -> psycopg.AsyncConnection:
    if DATABASE_URL:
        return await psycopg.AsyncConnection.connect(DATABASE_URL, row_factory=dict_row)
    return await psycopg.AsyncConnection.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        row_factory=dict_row,
    )


async def _create_database_if_needed() -> None:
    if DATABASE_URL:
        log.info("DATABASE_URL detected — skipping local DB creation")
        return

    target_db = DB_CONFIG["dbname"]
    log.info(f"Checking local database '{target_db}' …")

    conn = await psycopg.AsyncConnection.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname="postgres",
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        autocommit=True,
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (target_db,)
            )
            if await cur.fetchone():
                log.info(f"Database '{target_db}' already exists")
            else:
                await cur.execute(f'CREATE DATABASE "{target_db}"')
                log.info(f"Database '{target_db}' created")
    finally:
        await conn.close()


async def _migrate_old_schema() -> None:
    """
    If the database has old tables without user_id (from a pre-multi-user version),
    drop and recreate them so the new schema can be applied cleanly.
    Tables checked: expenses, income, budgets.
    The users and categories tables are kept as-is.
    """
    async with await _connect() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'expenses'
                  AND column_name = 'user_id'
            """)
            has_user_id = await cur.fetchone()

        if not has_user_id:
            log.warning(
                "Old schema detected (expenses.user_id missing) — "
                "dropping data tables and recreating with new schema."
            )
            async with conn.cursor() as cur:
                await cur.execute("""
                    DROP TABLE IF EXISTS budgets  CASCADE;
                    DROP TABLE IF EXISTS income   CASCADE;
                    DROP TABLE IF EXISTS expenses CASCADE;
                """)
            log.info("Old tables dropped — will recreate with new schema.")


async def _create_tables() -> None:
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"schema.sql not found at {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        sql = fh.read()

    log.info("Applying schema.sql …")
    async with await _connect() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
    log.info("Schema applied")


async def _seed_categories() -> None:
    if not os.path.exists(CATEGORIES_PATH):
        log.warning("categories.json not found — skipping seed")
        return

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as fh:
        categories: dict = json.load(fh)

    log.info(f"Seeding categories …")
    inserted = 0

    async with await _connect() as conn:
        async with conn.cursor() as cur:
            for name in categories.keys():
                await cur.execute(
                    "INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                    (name,),
                )
                inserted += cur.rowcount

    log.info(f"{inserted} new categories inserted")


async def init_db() -> None:
    """Full async DB setup — idempotent."""
    log.info("══════ DB INIT START ══════")
    await _create_database_if_needed()
    await _migrate_old_schema()
    await _create_tables()
    await _seed_categories()
    log.info("══════ DB INIT COMPLETE ══════")


if __name__ == "__main__":
    asyncio.run(init_db())