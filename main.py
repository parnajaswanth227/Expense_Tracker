"""
main.py
───────
FastMCP entrypoint — registers all 29 async tools + 1 resource.

Run modes
─────────
  HTTP (deployed server, multi-user, JWT auth):
      uvicorn api.server:app --port 8000

  Stdio (Claude Desktop, single local user, no auth needed):
      python main.py
      OR: uv run fastmcp install claude-desktop main.py

Tool inventory (29 total)
──────────────────────────
  Expense  (5): add_expense, update_expense, delete_expense,
                list_expenses, get_expense_by_id
  Income   (4): add_income, list_income, delete_income, monthly_income
  Budget   (4): set_budget, get_budget, check_budget_status, delete_budget
  Category (4): get_categories, add_category, update_category, delete_category
  Summary  (9): summarize_expenses, daily_summary, weekly_summary,
                monthly_summary, yearly_summary, category_breakdown,
                top_spending, compare_months, get_balance
  Utility  (3): get_last_expenses, search_expenses, export_expenses_csv
"""

from fastmcp import FastMCP

from tools.expense_tools import (
    add_expense,
    delete_expense,
    get_expense_by_id,
    list_expenses,
    update_expense,
)
from tools.income_tools import (
    add_income,
    delete_income,
    list_income,
    monthly_income,
)
from tools.budget_tools import (
    check_budget_status,
    delete_budget,
    get_budget,
    set_budget,
)
from tools.category_tools import (
    add_category,
    delete_category,
    get_categories,
    update_category,
)
from tools.summary_tools import (
    category_breakdown,
    compare_months,
    daily_summary,
    get_balance,
    monthly_summary,
    summarize_expenses,
    top_spending,
    weekly_summary,
    yearly_summary,
)
from tools.utility_tools import (
    export_expenses_csv,
    get_last_expenses,
    search_expenses,
)
from resources.category_resource import load_categories


# ── FastMCP instance ──────────────────────────────────────────────────────────
mcp = FastMCP("ExpenseTrackerAI")


# ── Expense tools (5) ─────────────────────────────────────────────────────────
mcp.tool()(add_expense)
mcp.tool()(update_expense)
mcp.tool()(delete_expense)
mcp.tool()(list_expenses)
mcp.tool()(get_expense_by_id)

# ── Income tools (4) ──────────────────────────────────────────────────────────
mcp.tool()(add_income)
mcp.tool()(list_income)
mcp.tool()(delete_income)
mcp.tool()(monthly_income)

# ── Budget tools (4) ──────────────────────────────────────────────────────────
mcp.tool()(set_budget)
mcp.tool()(get_budget)
mcp.tool()(check_budget_status)
mcp.tool()(delete_budget)

# ── Category tools (4) ────────────────────────────────────────────────────────
mcp.tool()(get_categories)
mcp.tool()(add_category)
mcp.tool()(update_category)
mcp.tool()(delete_category)

# ── Summary tools (9) ─────────────────────────────────────────────────────────
mcp.tool()(summarize_expenses)
mcp.tool()(daily_summary)
mcp.tool()(weekly_summary)
mcp.tool()(monthly_summary)
mcp.tool()(yearly_summary)
mcp.tool()(category_breakdown)
mcp.tool()(top_spending)
mcp.tool()(compare_months)
mcp.tool()(get_balance)

# ── Utility tools (3) ─────────────────────────────────────────────────────────
mcp.tool()(get_last_expenses)
mcp.tool()(search_expenses)
mcp.tool()(export_expenses_csv)


# ── MCP resource: full category taxonomy ──────────────────────────────────────
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Expose the category → subcategory mapping as an MCP resource."""
    return load_categories()


# ── Stdio entry-point ─────────────────────────────────────────────────────────
# In stdio mode there is no HTTP server and no JWT — Claude Desktop talks
# directly to this process over stdin/stdout.
# We still run init_db so tables exist before any tool is called.
if __name__ == "__main__":
    import asyncio
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    from init_db import init_db

    async def _run():
        await init_db()
        mcp.run()

    asyncio.run(_run())
