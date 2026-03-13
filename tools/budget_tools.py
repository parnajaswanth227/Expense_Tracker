"""
tools/budget_tools.py — multi-user
Tools (4): set_budget, get_budget, check_budget_status, delete_budget

Key change from V2: UNIQUE constraint is now (user_id, category_id),
so each user has their own independent budget per category.
"""

from context import current_user
from db import execute_query
from logger import get_logger

log = get_logger("budget_tools")


def _uid() -> str:
    return current_user.get()


async def set_budget(category_id: int, monthly_limit: float) -> dict:
    """
    Create or update your monthly spending limit for a category.

    Args:
        category_id:   ID of an existing category.
        monthly_limit: Maximum monthly spend (must be > 0).

    Returns:
        {"status": "budget set", "category_id": int, "monthly_limit": float}
        or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    log.info(f"set_budget | user={uid} category_id={category_id} limit={monthly_limit}")

    exists = await execute_query(
        "SELECT id FROM categories WHERE id = %s", (category_id,), fetch=True
    )
    if not exists:
        return {"error": f"Category {category_id} does not exist."}

    if monthly_limit <= 0:
        return {"error": f"monthly_limit must be > 0. Got: {monthly_limit}"}

    await execute_query(
        """
        INSERT INTO budgets (user_id, category_id, monthly_limit)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, category_id)
        DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
        """,
        (uid, category_id, monthly_limit),
    )
    log.info(f"set_budget | success | user={uid} category_id={category_id}")
    return {
        "status":        "budget set",
        "category_id":   category_id,
        "monthly_limit": monthly_limit,
    }


async def get_budget() -> list | dict:
    """
    Return all your configured budgets, sorted A→Z by category name.

    Returns:
        List of {"category": str, "monthly_limit": float} dicts.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    result = await execute_query(
        """
        SELECT  c.name AS category, b.monthly_limit
        FROM    budgets b
        JOIN    categories c ON b.category_id = c.id
        WHERE   b.user_id = %s
        ORDER   BY c.name
        """,
        (uid,),
        fetch=True,
    )
    log.info(f"get_budget | user={uid} | {len(result)} budgets")
    return result


async def check_budget_status(year: int, month: int) -> dict:
    """
    Compare your actual spending against your budgets for a given month.

    Alerts:
      🔴 EXCEEDED — spending ≥ 100% of limit
      🟡 WARNING  — spending ≥ 80% of limit

    Args:
        year:  Four-digit year.
        month: Month 1–12.

    Returns:
        {"budgets": [...], "alerts": [...]} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not (1 <= month <= 12):
        return {"error": f"Month must be 1–12. Got: {month}"}

    result = await execute_query(
        """
        SELECT  c.name                                                       AS category,
                b.monthly_limit,
                COALESCE(SUM(e.amount), 0)                                   AS spent,
                ROUND(
                    COALESCE(SUM(e.amount), 0) / b.monthly_limit * 100, 1
                )                                                            AS percent_used
        FROM    budgets b
        JOIN    categories c ON b.category_id = c.id
        LEFT JOIN expenses e
               ON  e.category_id = b.category_id
               AND e.user_id = %s
               AND EXTRACT(YEAR  FROM e.date) = %s
               AND EXTRACT(MONTH FROM e.date) = %s
        WHERE   b.user_id = %s
        GROUP   BY c.name, b.monthly_limit
        ORDER   BY percent_used DESC
        """,
        (uid, year, month, uid),
        fetch=True,
    )

    alerts = []
    for row in result:
        pct = float(row.get("percent_used") or 0)
        if pct >= 100:
            alerts.append(f"🔴  {row['category']}: EXCEEDED ({pct}% used)")
        elif pct >= 80:
            alerts.append(f"🟡  {row['category']}: WARNING ({pct}% used)")

    log.info(f"check_budget_status | user={uid} | {len(alerts)} alert(s)")
    return {"budgets": result, "alerts": alerts}


async def delete_budget(category_id: int) -> dict:
    """
    Remove your budget for a category.

    Args:
        category_id: ID of the category.

    Returns:
        {"status": "deleted", "category_id": int} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    result = await execute_query(
        "DELETE FROM budgets WHERE user_id = %s AND category_id = %s RETURNING id",
        (uid, category_id),
        fetch=True,
    )

    if not result:
        return {"error": f"No budget found for category {category_id}."}

    log.info(f"delete_budget | user={uid} | category_id={category_id}")
    return {"status": "deleted", "category_id": category_id}
