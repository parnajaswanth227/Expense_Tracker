-- schema.sql — Multi-user Expense Tracker MCP v3
-- Fully idempotent — safe to run on every startup (IF NOT EXISTS everywhere).

-- ── Users ─────────────────────────────────────────────────────────────────────
-- Stores registered users. Passwords are bcrypt hashed — never plain text.
CREATE TABLE IF NOT EXISTS users (
    id         SERIAL       PRIMARY KEY,
    username   VARCHAR(100) UNIQUE NOT NULL,
    password   TEXT         NOT NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Categories ────────────────────────────────────────────────────────────────
-- Global / shared — all users see the same categories.
-- Users can add their own via add_category (also shared).
CREATE TABLE IF NOT EXISTS categories (
    id   SERIAL       PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- ── Expenses ──────────────────────────────────────────────────────────────────
-- Each row belongs to exactly one user via user_id.
CREATE TABLE IF NOT EXISTS expenses (
    id          SERIAL        PRIMARY KEY,
    user_id     VARCHAR(100)  NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    date        DATE          NOT NULL,
    amount      NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    category_id INT           REFERENCES categories(id) ON DELETE SET NULL,
    subcategory VARCHAR(100)  NOT NULL DEFAULT '',
    note        TEXT          NOT NULL DEFAULT '',
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Income ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS income (
    id         SERIAL        PRIMARY KEY,
    user_id    VARCHAR(100)  NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    date       DATE          NOT NULL,
    amount     NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    source     VARCHAR(100)  NOT NULL,
    note       TEXT          NOT NULL DEFAULT '',
    created_at TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Budgets ───────────────────────────────────────────────────────────────────
-- Each user can set their own budget per category.
-- UNIQUE(user_id, category_id) ensures one budget per user per category.
CREATE TABLE IF NOT EXISTS budgets (
    id            SERIAL        PRIMARY KEY,
    user_id       VARCHAR(100)  NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    category_id   INT           REFERENCES categories(id) ON DELETE CASCADE,
    monthly_limit NUMERIC(10,2) NOT NULL CHECK (monthly_limit > 0),
    UNIQUE (user_id, category_id)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_expense_user_date  ON expenses(user_id, date);
CREATE INDEX IF NOT EXISTS idx_expense_category   ON expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_income_user_date   ON income(user_id, date);
CREATE INDEX IF NOT EXISTS idx_budget_user        ON budgets(user_id);
