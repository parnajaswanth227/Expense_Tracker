"""
tools/expense_tools.py — multi-user
────────────────────────────────────
All queries are automatically scoped to the authenticated user via
current_user ContextVar. Claude never passes a user_id — it's injected
invisibly from the JWT token.

Tools (5): add_expense, update_expense, delete_expense,
           list_expenses, get_expense_by_id
"""

from typing import Optional

from context import current_user
from db import execute_query
from logger import get_logger
from utils import validate_date

log = get_logger("expense_tools")


def _uid() -> str:
    """Get the current authenticated username. Empty string = not authed."""
    return current_user.get()


async def _category_exists(category_id: int) -> bool:
    result = await execute_query(
        "SELECT id FROM categories WHERE id = %s", (category_id,), fetch=True
    )
    return bool(result)


async def _expense_belongs_to_user(expense_id: int, uid: str) -> bool:
    result = await execute_query(
        "SELECT id FROM expenses WHERE id = %s AND user_id = %s",
        (expense_id, uid),
        fetch=True,
    )
    return bool(result)


# ── Tools ─────────────────────────────────────────────────────────────────────

async def add_expense(
    date: str,
    amount: float,
    category_id: int,
    subcategory: str = "",
    note: str = "",
) -> dict:
    """
    Add a new expense record for the current user.

    Args:
        date:        Date in YYYY-MM-DD format.
        amount:      Positive monetary amount.
        category_id: ID of an existing category (use get_categories to list).
        subcategory: Optional subcategory label.
        note:        Optional note (max 500 chars).

    Returns:
        {"expense_id": int}  on success.
        {"error": str}       on validation failure.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    log.info(f"add_expense | user={uid} date={date} amount={amount}")

    err = validate_date(date)
    if err:
        return err

    if amount <= 0:
        return {"error": f"Amount must be > 0. Got: {amount}"}

    if not await _category_exists(category_id):
        return {"error": f"Category {category_id} does not exist. Use get_categories()."}

    if note and len(note) > 500:
        return {"error": f"Note must be ≤ 500 chars. Got: {len(note)}"}

    result = await execute_query(
        """
        INSERT INTO expenses (user_id, date, amount, category_id, subcategory, note)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (uid, date, amount, category_id, subcategory or "", note or ""),
        fetch=True,
    )
    expense_id = result[0]["id"]
    log.info(f"add_expense | success | expense_id={expense_id}")
    return {"expense_id": expense_id}


async def update_expense(
    expense_id: int,
    date: Optional[str] = None,
    amount: Optional[float] = None,
    category_id: Optional[int] = None,
    subcategory: Optional[str] = None,
    note: Optional[str] = None,
) -> dict:
    """
    Partially update one of your expenses.
    Only provided fields are changed — omitted fields stay the same.

    Args:
        expense_id:  ID of the expense to update.
        date:        New date YYYY-MM-DD (optional).
        amount:      New positive amount (optional).
        category_id: New category ID (optional).
        subcategory: New subcategory (optional).
        note:        New note (optional).

    Returns:
        {"status": "updated", "expense": {...}}  on success.
        {"error": str}                           on failure.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    log.info(f"update_expense | user={uid} expense_id={expense_id}")

    if not await _expense_belongs_to_user(expense_id, uid):
        return {"error": f"Expense {expense_id} not found."}

    if date is not None:
        err = validate_date(date)
        if err:
            return err

    if amount is not None and amount <= 0:
        return {"error": f"Amount must be > 0. Got: {amount}"}

    if category_id is not None and not await _category_exists(category_id):
        return {"error": f"Category {category_id} does not exist."}

    sets, values = [], []
    if date        is not None: sets.append("date = %s");        values.append(date)
    if amount      is not None: sets.append("amount = %s");      values.append(amount)
    if category_id is not None: sets.append("category_id = %s"); values.append(category_id)
    if subcategory is not None: sets.append("subcategory = %s"); values.append(subcategory)
    if note        is not None: sets.append("note = %s");        values.append(note)

    if not sets:
        return {"error": "Nothing to update — provide at least one field."}

    sets.append("updated_at = CURRENT_TIMESTAMP")
    values.extend([expense_id, uid])

    result = await execute_query(
        f"UPDATE expenses SET {', '.join(sets)} "
        "WHERE id = %s AND user_id = %s "
        "RETURNING id, date, amount, subcategory, note",
        values,
        fetch=True,
    )

    if not result:
        return {"error": f"Expense {expense_id} not found."}

    log.info(f"update_expense | success | expense_id={expense_id}")
    return {"status": "updated", "expense": result[0]}


async def delete_expense(expense_id: int) -> dict:
    """
    Permanently delete one of your expenses.

    Args:
        expense_id: ID of the expense to delete.

    Returns:
        {"status": "deleted", "expense_id": int}  on success.
        {"error": str}                             if not found.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    log.info(f"delete_expense | user={uid} expense_id={expense_id}")

    result = await execute_query(
        "DELETE FROM expenses WHERE id = %s AND user_id = %s RETURNING id",
        (expense_id, uid),
        fetch=True,
    )

    if not result:
        return {"error": f"Expense {expense_id} not found."}

    log.info(f"delete_expense | success")
    return {"status": "deleted", "expense_id": expense_id}


async def list_expenses(
    start_date: str,
    end_date: str,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    List your expenses within a date range with pagination.

    Args:
        start_date: Start of range, YYYY-MM-DD (inclusive).
        end_date:   End of range, YYYY-MM-DD (inclusive).
        page:       Page number starting from 1.
        page_size:  Rows per page (1–200, default 50).

    Returns:
        {"data": [...], "page": int, "page_size": int, "total": int, "total_pages": int}
        or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    log.info(f"list_expenses | user={uid} {start_date}→{end_date} page={page}")

    err = validate_date(start_date) or validate_date(end_date)
    if err:
        return err

    if page < 1:
        return {"error": f"Page must be ≥ 1. Got: {page}"}
    if not (1 <= page_size <= 200):
        return {"error": f"page_size must be 1–200. Got: {page_size}"}

    offset = (page - 1) * page_size

    count = await execute_query(
        "SELECT COUNT(*) AS total FROM expenses "
        "WHERE user_id = %s AND date BETWEEN %s AND %s",
        (uid, start_date, end_date),
        fetch=True,
    )
    total = count[0]["total"]

    rows = await execute_query(
        """
        SELECT  e.id, e.date, e.amount,
                c.name AS category, e.subcategory, e.note
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.user_id = %s AND e.date BETWEEN %s AND %s
        ORDER   BY e.date DESC, e.created_at DESC
        LIMIT   %s OFFSET %s
        """,
        (uid, start_date, end_date, page_size, offset),
        fetch=True,
    )

    log.info(f"list_expenses | {len(rows)} of {total} total")
    return {
        "data":        rows,
        "page":        page,
        "page_size":   page_size,
        "total":       total,
        "total_pages": -(-total // page_size),
    }


async def get_expense_by_id(expense_id: int) -> dict:
    """
    Fetch one of your expenses by ID.

    Args:
        expense_id: ID of the expense.

    Returns:
        Expense dict on success or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    result = await execute_query(
        """
        SELECT  e.id, e.date, e.amount,
                c.name AS category, e.subcategory, e.note
        FROM    expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE   e.id = %s AND e.user_id = %s
        """,
        (expense_id, uid),
        fetch=True,
    )

    if not result:
        return {"error": f"Expense {expense_id} not found."}

    return result[0]
