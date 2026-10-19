CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    monthly_budget REAL NOT NULL DEFAULT 200.0,
    per_purchase_cap REAL NOT NULL DEFAULT 100.0,
    blocked_categories TEXT NOT NULL DEFAULT '["alcohol"]',
    savings_goal_name TEXT NOT NULL DEFAULT 'Emergency fund',
    savings_goal_target REAL NOT NULL DEFAULT 1000.0,
    savings_goal_saved REAL NOT NULL DEFAULT 0.0,
    monthly_savings REAL NOT NULL DEFAULT 300.0
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    original_request TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    authorization_id TEXT,
    decision_reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    order_id TEXT,
    product_id TEXT,
    product_name TEXT,
    amount REAL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
