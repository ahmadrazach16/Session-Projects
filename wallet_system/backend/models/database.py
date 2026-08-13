"""
Database layer.
Handles raw SQLite connection + schema creation.
Repositories talk to this module - nothing above the Repository layer
should ever import sqlite3 directly.
"""

import sqlite3
import os
import threading

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wallet_system.db")

# One lock so SQLite (which is not great with concurrent writers)
# behaves safely under multiple Flask threads for this demo/project.
_db_lock = threading.Lock()


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()

        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'CUSTOMER', -- CUSTOMER | ADMIN
                status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE | DISABLED
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                currency TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE | FROZEN | CLOSED
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, currency)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL UNIQUE,
                idempotency_key TEXT UNIQUE,
                type TEXT NOT NULL,          -- DEPOSIT | WITHDRAWAL | TRANSFER | ADJUSTMENT
                status TEXT NOT NULL,        -- PENDING | COMPLETED | FAILED | CANCELLED
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                source_wallet_id INTEGER,
                destination_wallet_id INTEGER,
                description TEXT,
                failure_reason TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (source_wallet_id) REFERENCES wallets(id),
                FOREIGN KEY (destination_wallet_id) REFERENCES wallets(id)
            );

            CREATE TABLE IF NOT EXISTS wallet_configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                max_single_deposit REAL NOT NULL DEFAULT 1000000,
                max_single_withdrawal REAL NOT NULL DEFAULT 50000,
                max_daily_withdrawal REAL NOT NULL DEFAULT 100000,
                max_single_transfer REAL NOT NULL DEFAULT 100000,
                max_daily_transfer REAL NOT NULL DEFAULT 500000
            );

            CREATE INDEX IF NOT EXISTS idx_tx_source ON transactions(source_wallet_id);
            CREATE INDEX IF NOT EXISTS idx_tx_dest ON transactions(destination_wallet_id);
            CREATE INDEX IF NOT EXISTS idx_tx_created ON transactions(created_at);
            """
        )

        cur.execute("SELECT COUNT(*) as c FROM wallet_configuration")
        if cur.fetchone()["c"] == 0:
            cur.execute("INSERT INTO wallet_configuration DEFAULT VALUES")

        # Seed a default admin so the system is usable immediately.
        cur.execute("SELECT COUNT(*) as c FROM users WHERE role='ADMIN'")
        if cur.fetchone()["c"] == 0:
            from werkzeug.security import generate_password_hash
            cur.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ("System Admin", "admin@wallet.com", generate_password_hash("admin123"), "ADMIN"),
            )

        conn.commit()
        conn.close()
