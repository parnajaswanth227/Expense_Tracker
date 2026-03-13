# Expense Tracker MCP v3 — Multi-User

Fully async FastMCP expense tracker. Each user has their own isolated data.
29 tools, PostgreSQL (Neon or local), JWT authentication, bcrypt passwords.

---

## What Changed From v2 (Single-User)

| | v2 (single-user) | **v3 (multi-user)** |
|---|---|---|
| Users | 1 hardcoded in `.env` | Many — stored in `users` DB table |
| Passwords | Plain text in `.env` | bcrypt hashed in database |
| Data isolation | Everyone sees same data | Each user sees only their own |
| Registration | N/A | `POST /auth/register` |
| New file | — | `context.py` — ContextVar carries user through every async call |
| Middleware | BaseHTTPMiddleware | Pure ASGI (context vars propagate correctly) |
| Schema | No users table | `users` table + `user_id` on expenses/income/budgets |

---

## Project Structure

```
expense_tracker/
├── api/
│   ├── __init__.py
│   ├── server.py         ← FastAPI app, /auth/register, /auth/token
│   ├── auth.py           ← bcrypt hashing, DB-based auth, JWT
│   └── middleware.py     ← Pure ASGI JWT middleware (context vars safe)
├── tools/
│   ├── expense_tools.py  (5 tools)
│   ├── income_tools.py   (4 tools)
│   ├── budget_tools.py   (4 tools)
│   ├── category_tools.py (4 tools)
│   ├── summary_tools.py  (9 tools)
│   └── utility_tools.py  (3 tools)
├── resources/
│   └── category_resource.py
├── context.py            ← ContextVar: current_user
├── main.py               ← FastMCP instance, registers all 29 tools
├── db.py                 ← async execute_query()
├── init_db.py            ← async DB bootstrap (idempotent)
├── config.py             ← all config from env vars
├── utils.py              ← validate_date()
├── logger.py             ← structured logging
├── schema.sql            ← multi-user DB schema
├── categories.json       ← 22 default categories
├── create_user.py        ← CLI to create users when registration is off
├── Procfile              ← for Railway/Render deployment
├── requirements.txt
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## Local Setup

### 1. Install

```powershell
uv init
uv venv
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.venv\Scripts\activate
uv add fastmcp fastapi uvicorn psycopg[binary] python-dotenv python-jose[cryptography] passlib[bcrypt]
```

### 2. Configure

```powershell
copy .env.example .env
# Edit .env:
#   DATABASE_URL  (Neon)  OR  DB_PASSWORD (local postgres)
#   SECRET_KEY    →  python -c "import secrets; print(secrets.token_hex(32))"
#   ALLOW_REGISTRATION=true
```

### 3. Start server

```powershell
uvicorn api.server:app --port 8000
```

DB tables and categories are created automatically on first startup.

---

## User Management

### Register a new user

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/register" `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"jaswanth","password":"MyStrongPass123"}'
```

### Get a JWT token

```powershell
$r = Invoke-RestMethod -Uri "http://localhost:8000/auth/token" `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"jaswanth","password":"MyStrongPass123"}'

$token = $r.access_token
echo $token
```

### Lock down registration (after setup)

In `.env`:
```
ALLOW_REGISTRATION=false
```

Restart the server. Now `/auth/register` returns 403. To add more users use:

```powershell
python create_user.py --username alice --password StrongPass456
```

---

## Test MCP Tools

```powershell
# Initialize session
$init = Invoke-WebRequest `
  -Uri "http://localhost:8000/mcp" -Method POST `
  -Headers @{
    Authorization  = "Bearer $token"
    "Content-Type" = "application/json"
    "Accept"       = "application/json, text/event-stream"
  } `
  -Body '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

$sessionId = $init.Headers["mcp-session-id"]

# List all tools
Invoke-RestMethod `
  -Uri "http://localhost:8000/mcp" -Method POST `
  -Headers @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json"
    "Accept"           = "application/json, text/event-stream"
    "mcp-session-id"   = $sessionId
  } `
  -Body '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## Deploy to Railway / Render

1. Push code to GitHub (`.env` is gitignored — never pushed)
2. Connect your GitHub repo to Railway or Render
3. Set environment variables in the hosting dashboard:
   ```
   DATABASE_URL      = your Neon connection string
   SECRET_KEY        = your generated key
   ALLOW_REGISTRATION = true  (set false after setup)
   ```
4. The `Procfile` handles the start command automatically:
   ```
   web: uvicorn api.server:app --host 0.0.0.0 --port $PORT
   ```
5. Your server URL will be: `https://yourapp.railway.app`

---

## Claude Desktop Config

Replace `YOUR_SERVER_URL` and `YOUR_JWT_TOKEN`:

```json
{
  "mcpServers": {
    "ExpenseTracker": {
      "command": "C://Program Files//nodejs//npx",
      "args": [
        "-y",
        "mcp-remote@latest",
        "https://YOUR_SERVER_URL/mcp",
        "--header",
        "Authorization: Bearer YOUR_JWT_TOKEN"
      ]
    }
  }
}
```

Each user puts their own JWT token in their own Claude Desktop config.
User A's token → User A's data. User B's token → User B's data. Completely isolated.

---

## How Data Isolation Works

Every tool reads the authenticated username from a `ContextVar`:

```
Request arrives
     │
     ▼
JWTMiddleware validates token → sets current_user ContextVar = "jaswanth"
     │
     ▼
FastMCP calls add_expense(date, amount, category_id, ...)
     │
     ▼
Tool reads:  uid = current_user.get()  →  "jaswanth"
     │
     ▼
SQL:  INSERT INTO expenses (user_id, ...) VALUES ('jaswanth', ...)
```

User never passes their username — it comes invisibly from the JWT token.
Even if User B somehow knew User A's expense ID, they can't access it
because every query includes `AND user_id = 'userB'`.

---

## Tools Reference (29 total)

| Group | Tool | Description |
|---|---|---|
| **Expense** | `add_expense` | Add new expense |
| | `update_expense` | Partial update |
| | `delete_expense` | Delete by ID |
| | `list_expenses` | Paginated list by date range |
| | `get_expense_by_id` | Fetch single expense |
| **Income** | `add_income` | Add income record |
| | `list_income` | List by date range |
| | `delete_income` | Delete by ID |
| | `monthly_income` | Total for a month |
| **Budget** | `set_budget` | Create/update monthly limit |
| | `get_budget` | List your budgets |
| | `check_budget_status` | Compare spend vs limits |
| | `delete_budget` | Remove a budget |
| **Category** | `get_categories` | List all categories (shared) |
| | `add_category` | Create category |
| | `update_category` | Rename category |
| | `delete_category` | Delete (blocked if in use) |
| **Summary** | `summarize_expenses` | By category for date range |
| | `daily_summary` | Single day total |
| | `weekly_summary` | ISO week total |
| | `monthly_summary` | Calendar month total |
| | `yearly_summary` | Full year breakdown |
| | `category_breakdown` | Category + subcategory detail |
| | `top_spending` | Top N categories |
| | `compare_months` | Side-by-side comparison |
| | `get_balance` | All-time income vs expense |
| **Utility** | `get_last_expenses` | Most recent N expenses |
| | `search_expenses` | Keyword search |
| | `export_expenses_csv` | Export to CSV |
