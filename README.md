# 💰 Expense Tracker MCP v3

A **multi-user AI-powered expense tracking server** built with **FastMCP + FastAPI + PostgreSQL**.
Users can manage finances using **plain English with AI**.

Works with:

* 🖥 Claude Desktop
* 📱 Claude.ai Free (via N8N)
* 🌐 Any HTTP client

---

# ✨ Features

* 🔐 **JWT Authentication** – secure multi-user system
* 👥 **Multi-user support** – each user has isolated data
* 🧰 **29 MCP tools** for expenses, income, budgets and analytics
* 🌐 **Mobile friendly registration page**
* ☁ **Cloud deployable** (Railway + Neon)
* 🤖 **AI integration with Claude**
* 🔄 **Claude.ai free support using N8N bridge**

---

# 📁 Project Structure

```
expense_tracker_v3/

├── CORE
│   ├── main.py
│   ├── run.py
│   ├── app.py
│   ├── config.py
│   ├── context.py
│   ├── db.py
│   ├── init_db.py
│   ├── logger.py
│   ├── utils.py
│   └── create_user.py
│
├── DATABASE
│   ├── schema.sql
│   └── categories.json
│
├── API
│   └── api/
│       ├── __init__.py
│       ├── auth.py
│       ├── middleware.py
│       └── server.py
│
├── MCP TOOLS
│   └── tools/
│       ├── expense_tools.py
│       ├── income_tools.py
│       ├── budget_tools.py
│       ├── category_tools.py
│       ├── summary_tools.py
│       └── utility_tools.py
│
├── FRONTEND
│   └── static/
│       └── register.html
│
├── DEPLOYMENT
│   ├── Procfile
│   ├── pyproject.toml
│   └── requirements.txt
│
└── README.md
```

⚠ **Never commit `.env` to GitHub.**

---

# 🧰 MCP Tools (29)

## Expense Tools

* add_expense
* update_expense
* delete_expense
* list_expenses
* get_expense_by_id

## Income Tools

* add_income
* list_income
* delete_income
* monthly_income

## Budget Tools

* set_budget
* get_budget
* check_budget_status
* delete_budget

## Category Tools

* get_categories
* add_category
* update_category
* delete_category

## Summary Tools

* summarize_expenses
* daily_summary
* weekly_summary
* monthly_summary
* yearly_summary
* category_breakdown
* top_spending
* compare_months
* get_balance

## Utility Tools

* get_last_expenses
* search_expenses
* export_expenses_csv

---

# 🗄 Database Schema

```
users
 id
 username
 password
 created_at

categories
 id
 name

expenses
 id
 user_id
 date
 amount
 category_id
 note

income
 id
 user_id
 date
 amount
 source

budgets
 id
 user_id
 category_id
 monthly_limit
```

All queries automatically filter:

```
WHERE user_id = current_user
```

Each user has **completely isolated data**.

---

# 🚀 Local Setup

## 1️⃣ Clone Repository

```
git clone https://github.com/parnajaswanth227/Expense_Tracker_With_Claude.git
cd Expense_Tracker_With_Claude
```

---

## 2️⃣ Create Python Environment

```
uv init
uv venv --python 3.12
.venv\Scripts\activate
```

Windows users:

```
$env:UV_LINK_MODE="copy"
```

---

## 3️⃣ Install Dependencies

```
uv add fastmcp fastapi uvicorn psycopg[binary] python-dotenv python-jose bcrypt
uv pip install -r requirements.txt
```

---

## 4️⃣ Create `.env`

Create a `.env` file in the root folder.

```
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
SECRET_KEY=your_secret_key_here
ALLOW_REGISTRATION=true
ACCESS_TOKEN_EXPIRE_MINUTES=525600
```

Generate a secret key:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5️⃣ Start Server

```
uv run python run.py
```

Server runs at:

```
http://localhost:8000
```

---

# 🔑 API Endpoints

| Method | Endpoint       | Description   |
| ------ | -------------- | ------------- |
| GET    | /health        | Server status |
| GET    | /register      | Signup page   |
| POST   | /auth/register | Create user   |
| POST   | /auth/token    | Login         |
| POST   | /mcp           | MCP endpoint  |

---

# ☁ Cloud Deployment

## Step 1: Create PostgreSQL Database

Go to:

```
https://neon.tech
```

Create database and copy connection string.

---

## Step 2: Deploy on Railway

Go to:

```
https://railway.app
```

Create project → Deploy from GitHub.

Railway will automatically use:

```
web: uvicorn api.server:app --host 0.0.0.0 --port $PORT
```

Add environment variables:

| Variable                    | Value             |
| --------------------------- | ----------------- |
| DATABASE_URL                | Neon database URL |
| SECRET_KEY                  | generated secret  |
| ALLOW_REGISTRATION          | true              |
| ACCESS_TOKEN_EXPIRE_MINUTES | 525600            |

---

## Step 3: Verify Deployment

```
https://your-app.railway.app/health
```

Expected response:

```
{"status":"ok"}
```

---

# 🖥 Using with Claude Desktop

Install MCP server:

```
uv run fastmcp install claude-desktop main.py
```

Manual configuration:

```
%APPDATA%\Claude\claude_desktop_config.json
```

```
{
 "mcpServers": {
   "ExpenseTracker": {
     "command": "npx",
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

# 📱 Using Claude.ai Free (Mobile + Web)

Claude free plan does **not support MCP connectors directly**.
We use an **N8N workflow bridge**.

## N8N Architecture

```
Claude AI
   ↓
N8N Webhook
   ↓
Expense Tracker MCP
   ↓
PostgreSQL Database
```

---

# Setup N8N

## Step 1: Create Account

```
https://n8n.io
```

Create account.

---

## Step 2: Create Workflow

Click:

```
New Workflow
```

---

## Step 3: Import Workflow JSON

Click:

```
⋮ → Import from JSON
```

Paste provided workflow.

---

## Step 4: Add Token

Replace:

```
YOUR_JWT_TOKEN_HERE
```

with your token.

---

## Step 5: Activate Workflow

Click **Activate**.

You will receive webhook URL:

```
https://yourname.app.n8n.cloud/webhook/expense-tracker
```

---

# Connect N8N to Claude.ai

1. Open **Claude.ai**
2. Go to:

```
Settings → Connectors
```

3. Select **N8N**
4. Paste your webhook URL.

Claude can now control your expense tracker.

---

# Example Commands

Users can ask Claude:

```
Add expense ₹500 for lunch today
```

```
Show my expenses this month
```

```
Add ₹50,000 salary income
```

```
Show my balance
```

```
Check my budget
```

Claude will automatically call MCP tools.

---

# 👥 Multi-User Flow

```
User opens /register
      ↓
Creates username & password
      ↓
Receives JWT token
      ↓
Token used in
 - Claude Desktop
 - N8N workflow
 - API calls
```

Each user has **separate database data**.

---

# 🔧 Admin Create Users

```
python create_user.py --username alice --password pass123
```

Disable public signup:

```
ALLOW_REGISTRATION=false
```

---

# 🐛 Troubleshooting

| Error             | Solution            |
| ----------------- | ------------------- |
| 401 Unauthorized  | Token expired       |
| Database error    | Check DATABASE_URL  |
| MCP session error | Restart server      |
| N8N webhook error | Check workflow JSON |

---

# 🔐 Security

Never commit:

```
.env
JWT tokens
database credentials
```

Rotate tokens if exposed.

---

# 📦 Tech Stack

| Layer         | Technology |
| ------------- | ---------- |
| MCP Framework | FastMCP    |
| API           | FastAPI    |
| Database      | PostgreSQL |
| Cloud DB      | Neon       |
| Deployment    | Railway    |
| Automation    | N8N        |
| AI Client     | Claude     |

---

# ⭐ Project Goal

Create a **fully AI-powered personal finance assistant** where users manage expenses using **natural language with Claude AI**.

---

If you'd like, I can also help add:

* 🧭 Architecture diagrams
* 📸 Screenshots
* 🔄 Workflow diagrams
* 🏷 GitHub badges
* 🎬 Animated demo

to make your GitHub repository look like a **professional open-source project**.


# 📸 Screenshots
screenshorts\Screenshot 2026-03-14 113116.png
## 💻 Web Dashboard – Expense Summary

The AI assistant analyzes your expenses and presents a clear financial overview including income, spending distribution, and balance.

<p align="center">
  <img src="screenshots/claude_desktop.png" width="800">
</p>
Features shown:

* Total income, expenses, and balance
* Category-wise spending breakdown
* Interactive spending chart
* AI-generated financial insights

Example insight:

> You've spent ₹2,000 across 3 transactions. Food is the dominant category at 85% (₹1,700). With ₹60,000 income, you're saving **96.7%** — a healthy balance of **₹58,000**.

---

## 📱 Claude AI Mobile – Natural Language Expense Entry
C:\Users\parna\Videos\expense_tracker_v3\screenshorts\WhatsApp Image 2026-03-14 at 11.33.34 AM.jpeg
Users can add expenses using **natural language with AI**.
<p align="center">
  <img src="screenshots/webapp.jpeg" width="800">
</p>
Example command:

```
Add an expense 210 rs for petrol for my bike
```

Claude automatically:

1. Detects the **transport category**
2. Calls the **add_expense MCP tool**
3. Stores the expense in the database
4. Returns confirmation with details

![Claude AI Expense Entry](screenshots/claude-expense-add.png)

Returned response includes:

* Expense ID
* Amount
* Category
* Note
* Date

This demonstrates how users can **manage finances conversationally with AI**.


# 🌐 Live Demo

The project is deployed on **Railway Cloud**.

### 📝 User Registration Page

Create a new account:

```
https://web-production-d3df0.up.railway.app/register
```

This page allows users to:

* Create a username
* Set a password
* Generate a JWT token for authentication

---

### 🔌 MCP Server Endpoint

Main MCP endpoint used by Claude and N8N:

```
https://web-production-d3df0.up.railway.app/mcp
```

This endpoint handles:

* MCP tool execution
* AI requests from Claude
* Automation requests from N8N workflows

---

### 🧪 Health Check (Optional)

Check if the server is running:

```
https://web-production-d3df0.up.railway.app/health
```

Expected response:

```
{"status":"ok"}
```
