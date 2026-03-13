"""
tools/category_tools.py — multi-user
─────────────────────────────────────
Categories are GLOBAL (shared across all users).
All users see the same category list. Any user can add a category.
Deletion is blocked if ANY user's expense references it.

Tools (4): get_categories, add_category, update_category, delete_category
"""

from context import current_user
from db import execute_query
from logger import get_logger

log = get_logger("category_tools")


def _uid() -> str:
    return current_user.get()


async def get_categories() -> list | dict:
    """
    Return all expense categories sorted alphabetically.

    Returns:
        List of {"id": int, "name": str} dicts.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    result = await execute_query("SELECT id, name FROM categories ORDER BY name", fetch=True)
    log.info(f"get_categories | user={uid} | {len(result)} categories")
    return result


async def add_category(name: str) -> dict:
    """
    Create a new expense category (shared across all users).

    Args:
        name: Category name (unique, non-empty).

    Returns:
        {"category_id": int} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not name or not name.strip():
        return {"error": "Category name cannot be empty."}

    result = await execute_query(
        "INSERT INTO categories (name) VALUES (%s) RETURNING id",
        (name.strip(),),
        fetch=True,
    )
    cid = result[0]["id"]
    log.info(f"add_category | user={uid} | category_id={cid}")
    return {"category_id": cid}


async def update_category(category_id: int, name: str) -> dict:
    """
    Rename a category.

    Args:
        category_id: ID of the category to rename.
        name:        New name (non-empty).

    Returns:
        {"status": "updated"} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    if not name or not name.strip():
        return {"error": "Category name cannot be empty."}

    result = await execute_query(
        "UPDATE categories SET name = %s WHERE id = %s RETURNING id",
        (name.strip(), category_id),
        fetch=True,
    )

    if not result:
        return {"error": f"Category {category_id} not found."}

    log.info(f"update_category | user={uid} | category_id={category_id}")
    return {"status": "updated"}


async def delete_category(category_id: int) -> dict:
    """
    Delete a category. Blocked if any user's expense references it.

    Args:
        category_id: ID of the category to delete.

    Returns:
        {"status": "deleted", "category_id": int} or {"error": str}.
    """
    uid = _uid()
    if not uid:
        return {"error": "Not authenticated."}

    in_use = await execute_query(
        "SELECT COUNT(*) AS cnt FROM expenses WHERE category_id = %s",
        (category_id,),
        fetch=True,
    )
    count = in_use[0]["cnt"]

    if count > 0:
        return {
            "error": (
                f"Cannot delete category {category_id} — referenced by "
                f"{count} expense(s) across all users. "
                "Reassign or delete those expenses first."
            )
        }

    result = await execute_query(
        "DELETE FROM categories WHERE id = %s RETURNING id",
        (category_id,),
        fetch=True,
    )

    if not result:
        return {"error": f"Category {category_id} not found."}

    log.info(f"delete_category | user={uid} | category_id={category_id}")
    return {"status": "deleted", "category_id": category_id}
