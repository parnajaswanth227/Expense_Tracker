# 💰 Expense Tracker MCP Server

A **multi-user AI-powered expense tracking server** built using **FastMCP, FastAPI, and PostgreSQL**.

This server integrates with **Claude Desktop via the Model Context Protocol (MCP)**, allowing users to **manage personal finances using natural language**.

Example:

> “Add ₹250 lunch expense under Food for today”

The AI automatically calls the appropriate MCP tool.

---

# ✨ Features

### 🔐 Secure Authentication

* JWT-based authentication
* Each user receives a **personal token**
* Fully isolated user data

### 👥 Multi-User Architecture

* One server supports **many users**
* Each user's data remains private

### 🧰 29 MCP Tools

Full financial toolkit including:

* Expenses
* Income
* Budgets
* Categories
* Summaries
* CSV export

### ☁️ Cloud Ready

Deploy easily using:

* **Railway**
* **Neon PostgreSQL**

### 📋 Self-Service Registration

Users can create accounts via:

```
/register
```

---

# 🏗️ System Architecture

```
Claude Desktop
(MCP Client)
        │
        │  Bearer Token (JWT)
        ▼
FastAPI Application
        │
        │ JWT Middleware
        ▼
FastMCP Server
(29 Financial Tools)
        │
        ▼
Neon PostgreSQL
(users, expenses, income, budgets)
```

---

# 📁 Project Structure

```
expense_tracker_v3/
│
├── main.py
├── run.py
├── app.py
├── config.py
├── context.py
├── db.py
├── init_db.py
├── logger.py
├── utils.py
├── create_user.py
├── schema.sql
├── categories.json
├── requirements.txt
├── pyproject.toml
├── Procfile
│
├── api/
│   ├── auth.py
│   ├── middleware.py
│   └── server.py
│
├── tools/
│   ├── expense_tools.py
│   ├── income_tools.py
│   ├── budget_tools.py
│   ├── category_tools.py
│   ├── summary_tools.py
│   └── utility_tools.py
│
└── static/
    └── register.html
```

---

# 🛠️ MCP Tools

### Expense Tools

* add_expense
* update_expense
* delete_expense
* list_expenses
* get_expense_by_id

### Income Tools

* add_income
* list_income
* delete_income
* monthly_income

### Budget Tools

* set_budget
* get_budget
* check_budget_status
* delete_budget

### Category Tools

* get_categories
* add_category
* update_category
* delete_category

### Summary Tools

* summarize_expenses
* daily_summary
* weekly_summary
* monthly_summary
* yearly_summary
* category_breakdown
* top_spending
* compare_months
* get_balance

### Utility Tools

* get_last_expenses
* search_expenses
* export_expenses_csv

Total: **29 MCP tools**

---

# 🗄️ Database Schema

### Users

```
users
- id
- username (UNIQUE)
- password (bcrypt)
- created_at
```

### Categories

```
categories
- id
- name (UNIQUE)
```

Shared across all users.

### Expenses

```
expenses
- id
- user_id
- date
- amount
- category_id
- subcategory
- note
```

### Income

```
income
- id
- user_id
- date
- amount
- source
- note
```

### Budgets

```
budgets
- id
- user_id
- category_id
- monthly_limit
```

Unique constraint:

```
(user_id, category_id)
```

---

# 🚀 Local Setup (Windows)

## 1. Clone Repository

```
git clone https://github.com/parnajaswanth227/Expense_Tracker_With_Claude.git
cd Expense_Tracker_With_Claude
```

---

## 2. Initialize Environment

```
uv init
uv venv --python 3.12
.venv\Scripts\activate
```

---

## 3. Fix Windows Link Mode

```
$env:UV_LINK_MODE="copy"
```

---

## 4. Install Dependencies

```
uv add fastmcp fastapi uvicorn psycopg[binary] python-dotenv python-jose[cryptography] bcrypt
uv pip install -r requirements.txt
```

---

## 5. Create Environment File

Create `.env`

```
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
SECRET_KEY=your_secret_key
ALLOW_REGISTRATION=true
ACCESS_TOKEN_EXPIRE_MINUTES=525600
```

Generate secret key:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 6. Start Server

```
uv run python run.py
```

Server runs at:

```
http://localhost:8000
```

---

# 🔑 Authentication Flow

```
User
 │
 │ POST /auth/register
 ▼
Server creates user
 │
 │ returns JWT token
 ▼
User calls MCP tools
 │
 │ Authorization: Bearer TOKEN
 ▼
JWT middleware verifies user
 │
 ▼
Tool executes with user_id
```

---

# 🧪 Testing with PowerShell

### Health Check

```
Invoke-RestMethod http://localhost:8000/health
```

---

### Register User

```
Invoke-RestMethod `
  -Uri "http://localhost:8000/auth/register" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"username":"jaswanth","password":"MyPassword123"}'
```

---

### Login

```
$r = Invoke-RestMethod `
  -Uri "http://localhost:8000/auth/token" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"username":"jaswanth","password":"MyPassword123"}'

$token = $r.access_token
```

---

### Initialize MCP Session

```
$init = Invoke-WebRequest `
  -Uri "http://localhost:8000/mcp" `
  -Method POST `
  -Headers @{
    Authorization="Bearer $token"
    "Content-Type"="application/json"
    "Accept"="application/json, text/event-stream"
  } `
  -Body '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

---

# 🖥️ Claude Desktop Integration

## Option 1 — Local (stdio)

```
uv run fastmcp install claude-desktop main.py
```

---

## Option 2 — Cloud HTTP

Edit:

```
%APPDATA%\Claude\claude_desktop_config.json
```

```
{
  "mcpServers": {
    "ExpenseTracker": {
      "command": "C://Program Files//nodejs//npx",
      "args": [
        "-y",
        "mcp-remote@latest",
        "https://your-app.railway.app/mcp",
        "--header",
        "Authorization: Bearer YOUR_TOKEN"
      ]
    }
  }
}
```

---

# ☁️ Cloud Deployment

## Neon Database

1. Create project at
   https://neon.tech

2. Copy connection string.

---

## Railway Deployment

1. Create project on Railway
2. Deploy from GitHub repository

Railway reads:

```
Procfile
```

```
web: uvicorn api.server:app --host 0.0.0.0 --port $PORT
```

---

## Environment Variables

```
DATABASE_URL
SECRET_KEY
ALLOW_REGISTRATION
ACCESS_TOKEN_EXPIRE_MINUTES
```

---

# 👤 Multi-User Workflow

```
User opens /register
        │
        ▼
Account created
        │
        ▼
JWT token generated
        │
        ▼
User adds token to Claude Desktop
        │
        ▼
All MCP tools operate
with isolated user data
```

---

# 📌 Example Natural Language Commands

Inside Claude Desktop:

```
Add ₹300 dinner expense under Food
Show my expenses for this week
Compare spending between February and March
What is my current balance?
Export my expenses to CSV
```

Claude automatically calls the correct MCP tool.


