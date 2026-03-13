"""
tools/income_tools.py — multi-user
Tools (4): add_income, list_income, delete_income, monthly_income
"""

from context import current_user
from db import execute_query
from logger import get_logger
from utils import validate_date

log = get_logger("income_tools")


def _uid() -> str:
    return current_user.get()


async def add_income(date: str, amount: float, source: str, note: str = "") -> dict:
    """
    Add a new income record.

    Args:
        date:   Date in YYYY-MM-DD format.
        amount: Positive monetary amount.
        source: Income source label (e.g. "salary", "freelance").
        note:   Optional note.

    Returns:
        {"income_id": int}  on success.
        {"error": str}      on failure.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    log.info(f"add_income | user={uid} date={date} amount={amount} source={source}")

    err = validate_date(date)
    if err:
        return err

    if amount <= 0:
        return {"error": f"Amount must be > 0. Got: {amount}"}

    if not source or not source.strip():
        return {"error": "Source is required."}

    result = await execute_query(
        "INSERT INTO income (user_id, date, amount, source, note) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (uid, date, amount, source.strip(), note or ""),
        fetch=True,
    )
    income_id = result[0]["id"]
    log.info(f"add_income | success | income_id={income_id}")
    return {"income_id": income_id}


async def list_income(start_date: str, end_date: str) -> list | dict:
    """
    List your income entries within a date range, newest first.

    Args:
        start_date: YYYY-MM-DD (inclusive).
        end_date:   YYYY-MM-DD (inclusive).

    Returns:
        List of income dicts or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    err = validate_date(start_date) or validate_date(end_date)
    if err:
        return err

    result = await execute_query(
        """
        SELECT id, date, amount, source, note
        FROM   income
        WHERE  user_id = %s AND date BETWEEN %s AND %s
        ORDER  BY date DESC, created_at DESC
        """,
        (uid, start_date, end_date),
        fetch=True,
    )
    log.info(f"list_income | user={uid} | {len(result)} rows")
    return result


async def delete_income(income_id: int) -> dict:
    """
    Delete one of your income records.

    Args:
        income_id: ID of the income record.

    Returns:
        {"status": "deleted", "income_id": int}  on success.
        {"error": str}                            if not found.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    result = await execute_query(
        "DELETE FROM income WHERE id = %s AND user_id = %s RETURNING id",
        (income_id, uid),
        fetch=True,
    )

    if not result:
        return {"error": f"Income {income_id} not found."}

    log.info(f"delete_income | user={uid} | success")
    return {"status": "deleted", "income_id": income_id}


async def monthly_income(year: int, month: int) -> dict:
    """
    Total income for a specific calendar month.

    Args:
        year:  Four-digit year.
        month: Month 1–12.

    Returns:
        {"total_income": float, "entries": int} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not (1 <= month <= 12):
        return {"error": f"Month must be 1–12. Got: {month}"}

    result = await execute_query(
        """
        SELECT COALESCE(SUM(amount), 0) AS total_income,
               COUNT(*)                 AS entries
        FROM   income
        WHERE  user_id = %s
          AND  EXTRACT(YEAR  FROM date) = %s
          AND  EXTRACT(MONTH FROM date) = %s
        """,
        (uid, year, month),
        fetch=True,
    )
    data = result[0] if result else {"total_income": 0, "entries": 0}
    log.info(f"monthly_income | user={uid} | total={data['total_income']}")
    return data
