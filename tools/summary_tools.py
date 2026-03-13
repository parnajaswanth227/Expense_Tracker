"""
tools/summary_tools.py — multi-user
Tools (9): summarize_expenses, daily_summary, weekly_summary, monthly_summary,
           yearly_summary, category_breakdown, top_spending, compare_months, get_balance
"""

from context import current_user
from db import execute_query
from logger import get_logger
from utils import validate_date

log = get_logger("summary_tools")


def _uid() -> str:
    return current_user.get()


async def summarize_expenses(start_date: str, end_date: str) -> list | dict:
    """
    Your total expenses grouped by category for a date range, highest first.

    Args:
        start_date: YYYY-MM-DD (inclusive).
        end_date:   YYYY-MM-DD (inclusive).

    Returns:
        List of {"category": str, "total": float} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    err = validate_date(start_date) or validate_date(end_date)
    if err:
        return err

    result = await execute_query(
        """
        SELECT  c.name AS category, SUM(e.amount) AS total
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.user_id = %s AND e.date BETWEEN %s AND %s
        GROUP   BY c.name
        ORDER   BY total DESC
        """,
        (uid, start_date, end_date),
        fetch=True,
    )
    log.info(f"summarize_expenses | user={uid} | {len(result)} categories")
    return result


async def daily_summary(date: str) -> dict:
    """
    Your total spending and transaction count for a single day.

    Args:
        date: YYYY-MM-DD.

    Returns:
        {"total_spent": float, "transactions": int} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    err = validate_date(date)
    if err:
        return err

    result = await execute_query(
        "SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transactions "
        "FROM expenses WHERE user_id = %s AND date = %s",
        (uid, date),
        fetch=True,
    )
    return result[0] if result else {"total_spent": 0, "transactions": 0}


async def weekly_summary(year: int, week: int) -> dict:
    """
    Your total spending for an ISO week number (1–53).

    Args:
        year: Four-digit year.
        week: ISO week number 1–53.

    Returns:
        {"total_spent": float, "transactions": int} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not (1 <= week <= 53):
        return {"error": f"Week must be 1–53. Got: {week}"}

    result = await execute_query(
        """
        SELECT  COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transactions
        FROM    expenses
        WHERE   user_id = %s
          AND   EXTRACT(YEAR FROM date) = %s
          AND   EXTRACT(WEEK FROM date) = %s
        """,
        (uid, year, week),
        fetch=True,
    )
    return result[0] if result else {"total_spent": 0, "transactions": 0}


async def monthly_summary(year: int, month: int) -> dict:
    """
    Your total spending for a calendar month.

    Args:
        year:  Four-digit year.
        month: Month 1–12.

    Returns:
        {"total_spent": float, "transactions": int} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not (1 <= month <= 12):
        return {"error": f"Month must be 1–12. Got: {month}"}

    result = await execute_query(
        """
        SELECT  COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transactions
        FROM    expenses
        WHERE   user_id = %s
          AND   EXTRACT(YEAR  FROM date) = %s
          AND   EXTRACT(MONTH FROM date) = %s
        """,
        (uid, year, month),
        fetch=True,
    )
    return result[0] if result else {"total_spent": 0, "transactions": 0}


async def yearly_summary(year: int) -> dict:
    """
    Your total spending broken down by month for a full year.

    Args:
        year: Four-digit year.

    Returns:
        {"year": int, "total_spent": float, "transactions": int, "by_month": [...]}
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    result = await execute_query(
        """
        SELECT  EXTRACT(MONTH FROM date)::int AS month,
                COALESCE(SUM(amount), 0)      AS total_spent,
                COUNT(*)                      AS transactions
        FROM    expenses
        WHERE   user_id = %s AND EXTRACT(YEAR FROM date) = %s
        GROUP   BY month
        ORDER   BY month
        """,
        (uid, year),
        fetch=True,
    )

    total_spent = sum(r["total_spent"] for r in result)
    total_trans = sum(r["transactions"] for r in result)

    log.info(f"yearly_summary | user={uid} | total={total_spent}")
    return {
        "year":         year,
        "total_spent":  total_spent,
        "transactions": total_trans,
        "by_month":     result,
    }


async def category_breakdown(year: int, month: int) -> dict:
    """
    Your per-category and per-subcategory spending detail for a month.

    Args:
        year:  Four-digit year.
        month: Month 1–12.

    Returns:
        {"year": int, "month": int, "categories": [...]} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not (1 <= month <= 12):
        return {"error": f"Month must be 1–12. Got: {month}"}

    cat_rows = await execute_query(
        """
        SELECT  c.name AS category, SUM(e.amount) AS total, COUNT(*) AS transactions
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.user_id = %s
          AND   EXTRACT(YEAR  FROM e.date) = %s
          AND   EXTRACT(MONTH FROM e.date) = %s
        GROUP   BY c.name
        ORDER   BY total DESC
        """,
        (uid, year, month),
        fetch=True,
    )

    sub_rows = await execute_query(
        """
        SELECT  c.name AS category, e.subcategory,
                SUM(e.amount) AS total, COUNT(*) AS transactions
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.user_id = %s
          AND   EXTRACT(YEAR  FROM e.date) = %s
          AND   EXTRACT(MONTH FROM e.date) = %s
          AND   e.subcategory != ''
        GROUP   BY c.name, e.subcategory
        ORDER   BY total DESC
        """,
        (uid, year, month),
        fetch=True,
    )

    subs_by_cat: dict = {}
    for sr in sub_rows:
        subs_by_cat.setdefault(sr["category"], []).append({
            "subcategory":  sr["subcategory"],
            "total":        sr["total"],
            "transactions": sr["transactions"],
        })

    categories = []
    for cr in cat_rows:
        categories.append({
            "category":      cr["category"],
            "total":         cr["total"],
            "transactions":  cr["transactions"],
            "subcategories": subs_by_cat.get(cr["category"], []),
        })

    log.info(f"category_breakdown | user={uid} | {len(categories)} categories")
    return {"year": year, "month": month, "categories": categories}


async def top_spending(year: int, month: int, limit: int = 5) -> dict:
    """
    Your top N categories by spend for a given month.

    Args:
        year:  Four-digit year.
        month: Month 1–12.
        limit: How many top categories to return (1–20, default 5).

    Returns:
        {"year": int, "month": int, "top_categories": [...]} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not (1 <= month <= 12):
        return {"error": f"Month must be 1–12. Got: {month}"}
    if not (1 <= limit <= 20):
        return {"error": f"limit must be 1–20. Got: {limit}"}

    result = await execute_query(
        """
        SELECT  c.name AS category, SUM(e.amount) AS total, COUNT(*) AS transactions
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.user_id = %s
          AND   EXTRACT(YEAR  FROM e.date) = %s
          AND   EXTRACT(MONTH FROM e.date) = %s
        GROUP   BY c.name
        ORDER   BY total DESC
        LIMIT   %s
        """,
        (uid, year, month, limit),
        fetch=True,
    )
    return {"year": year, "month": month, "top_categories": result}


async def compare_months(year: int, month1: int, month2: int) -> dict:
    """
    Side-by-side comparison of your spending between two months in the same year.

    Args:
        year:   Four-digit year.
        month1: First month (1–12).
        month2: Second month (1–12).

    Returns:
        Comparison dict with per-category deltas and grand totals.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    for m in (month1, month2):
        if not (1 <= m <= 12):
            return {"error": f"Month must be 1–12. Got: {m}"}

    async def _month_totals(month: int) -> dict:
        rows = await execute_query(
            """
            SELECT  c.name AS category, SUM(e.amount) AS total
            FROM    expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE   e.user_id = %s
              AND   EXTRACT(YEAR  FROM e.date) = %s
              AND   EXTRACT(MONTH FROM e.date) = %s
            GROUP   BY c.name
            """,
            (uid, year, month),
            fetch=True,
        )
        return {r["category"]: float(r["total"]) for r in rows}

    d1 = await _month_totals(month1)
    d2 = await _month_totals(month2)
    all_cats = sorted(set(d1) | set(d2))

    comparison = []
    for cat in all_cats:
        t1   = d1.get(cat, 0)
        t2   = d2.get(cat, 0)
        diff = t2 - t1
        pct  = round(diff / t1 * 100, 1) if t1 > 0 else None
        comparison.append({
            "category":       cat,
            "month1_total":   t1,
            "month2_total":   t2,
            "difference":     round(diff, 2),
            "change_percent": pct,
        })

    log.info(f"compare_months | user={uid} | {len(comparison)} categories")
    return {
        "year":               year,
        "month1":             month1,
        "month2":             month2,
        "month1_grand_total": round(sum(d1.values()), 2),
        "month2_grand_total": round(sum(d2.values()), 2),
        "comparison":         comparison,
    }


async def get_balance() -> dict:
    """
    Your all-time balance: total income minus total expenses.

    Returns:
        {"total_income": float, "total_expense": float, "balance": float}
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    income_row = await execute_query(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s",
        (uid,), fetch=True,
    )
    expense_row = await execute_query(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s",
        (uid,), fetch=True,
    )

    income  = float(income_row[0]["total"])
    expense = float(expense_row[0]["total"])
    balance = income - expense

    log.info(f"get_balance | user={uid} | income={income} expense={expense}")
    return {
        "total_income":  income,
        "total_expense": expense,
        "balance":       round(balance, 2),
    }
