"""
tools/utility_tools.py — multi-user
Tools (3): get_last_expenses, search_expenses, export_expenses_csv
"""

import csv
import os
from typing import Optional

from config import EXPORT_DIR
from context import current_user
from db import execute_query
from logger import get_logger
from utils import validate_date

log = get_logger("utility_tools")


def _uid() -> str:
    return current_user.get()


async def get_last_expenses(limit: int = 10) -> list | dict:
    """
    Return your N most recent expense records.

    Args:
        limit: How many records to return (1–100, default 10).

    Returns:
        List of expense dicts or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not (1 <= limit <= 100):
        return {"error": f"Limit must be 1–100. Got: {limit}"}

    result = await execute_query(
        """
        SELECT  e.id, e.date, e.amount,
                c.name AS category, e.subcategory, e.note
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.user_id = %s
        ORDER   BY e.date DESC, e.created_at DESC
        LIMIT   %s
        """,
        (uid, limit),
        fetch=True,
    )
    log.info(f"get_last_expenses | user={uid} | {len(result)} rows")
    return result


async def search_expenses(
    keyword: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    Case-insensitive keyword search across your expenses (note, subcategory, category).

    Args:
        keyword:    Text to search (non-empty).
        start_date: Optional range start YYYY-MM-DD.
        end_date:   Optional range end   YYYY-MM-DD.

    Returns:
        {"keyword": str, "count": int, "data": [...]} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not keyword or not keyword.strip():
        return {"error": "Keyword cannot be empty."}

    if start_date:
        err = validate_date(start_date)
        if err:
            return err
    if end_date:
        err = validate_date(end_date)
        if err:
            return err

    like = f"%{keyword.strip()}%"
    conditions = [
        "e.user_id = %s",
        "(e.note ILIKE %s OR e.subcategory ILIKE %s OR c.name ILIKE %s)",
    ]
    params: list = [uid, like, like, like]

    if start_date:
        conditions.append("e.date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("e.date <= %s")
        params.append(end_date)

    rows = await execute_query(
        f"""
        SELECT  e.id, e.date, e.amount,
                c.name AS category, e.subcategory, e.note
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   {' AND '.join(conditions)}
        ORDER   BY e.date DESC
        """,
        params,
        fetch=True,
    )

    log.info(f"search_expenses | user={uid} | '{keyword}' → {len(rows)} results")
    return {"keyword": keyword, "count": len(rows), "data": rows}


async def export_expenses_csv(start_date: str, end_date: str) -> dict:
    """
    Export your expenses in a date range to a CSV file on the server.

    Args:
        start_date: YYYY-MM-DD (inclusive).
        end_date:   YYYY-MM-DD (inclusive).

    Returns:
        {"status": "exported", "file": str, "path": str, "total_rows": int}
        or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    err = validate_date(start_date) or validate_date(end_date)
    if err:
        return err

    rows = await execute_query(
        """
        SELECT  e.id, e.date, e.amount,
                c.name AS category, e.subcategory, e.note, e.created_at
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.user_id = %s AND e.date BETWEEN %s AND %s
        ORDER   BY e.date DESC
        """,
        (uid, start_date, end_date),
        fetch=True,
    )

    if not rows:
        return {"error": f"No expenses found between {start_date} and {end_date}."}

    # Include username in filename to avoid conflicts between users
    filename = f"expenses_{uid}_{start_date}_to_{end_date}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)
    os.makedirs(EXPORT_DIR, exist_ok=True)

    fieldnames = ["id", "date", "amount", "category", "subcategory", "note", "created_at"]
    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    log.info(f"export_expenses_csv | user={uid} | {len(rows)} rows → {filepath}")
    return {
        "status":     "exported",
        "file":       filename,
        "path":       filepath,
        "total_rows": len(rows),
    }
