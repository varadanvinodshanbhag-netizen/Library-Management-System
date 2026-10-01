# ============================================================
# migrate.py
# Safe database migration for Library Management System.
# - Backs up library.db
# - Adds new columns to existing tables (only if missing)
# - Creates new tables (only if missing)
# - Safe to run multiple times
# ============================================================

import sqlite3
import os
import shutil
from datetime import datetime

DB_NAME = "library.db"


# ------------------------------------------------------------
# Backup the database before making any changes
# ------------------------------------------------------------
def backup_database():
    if not os.path.exists(DB_NAME):
        print("No existing database found. A fresh one will be created.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"library_backup_{timestamp}.db"
    shutil.copy2(DB_NAME, backup_name)
    print(f"Backup created: {backup_name}")
    return backup_name


# ------------------------------------------------------------
# Check if a column exists in a table
# ------------------------------------------------------------
def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    return column in columns


# ------------------------------------------------------------
# Check if a table exists
# ------------------------------------------------------------
def table_exists(cur, table):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cur.fetchone() is not None


# ------------------------------------------------------------
# Add a column only if it does not exist
# ------------------------------------------------------------
def safe_add_column(cur, table, column, definition):
    if not table_exists(cur, table):
        return
    if column_exists(cur, table, column):
        print(f"  [SKIP] {table}.{column} already exists")
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    print(f"  [ADD ] {table}.{column}")


# ------------------------------------------------------------
# Run the migration
# ------------------------------------------------------------
def run_migration():
    print("=" * 60)
    print("LIBRARY MANAGEMENT SYSTEM - DATABASE MIGRATION")
    print("=" * 60)

    backup_database()

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        # -------- Alter existing tables --------
        print("\n[1] Updating 'users' table...")
        safe_add_column(cur, "users", "password_hash", "TEXT")
        safe_add_column(cur, "users", "role", "TEXT DEFAULT 'ADMIN'")
        safe_add_column(cur, "users", "is_active", "INTEGER DEFAULT 1")
        safe_add_column(cur, "users", "created_at", "TEXT")
        safe_add_column(cur, "users", "last_login", "TEXT")

        print("\n[2] Updating 'issue_return' table...")
        safe_add_column(cur, "issue_return", "due_date", "TEXT")
        safe_add_column(cur, "issue_return", "actual_return_date", "TEXT")
        safe_add_column(cur, "issue_return", "overdue_days", "INTEGER DEFAULT 0")
        safe_add_column(cur, "issue_return", "fine_rate", "REAL DEFAULT 1.0")
        safe_add_column(cur, "issue_return", "fine_amount", "REAL DEFAULT 0.0")
        safe_add_column(cur, "issue_return", "fine_status", "TEXT DEFAULT 'NONE'")
        safe_add_column(cur, "issue_return", "extension_count", "INTEGER DEFAULT 0")

        # -------- Create new tables --------
        print("\n[3] Creating new tables...")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS member_accounts (
                account_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id      INTEGER NOT NULL UNIQUE,
                username       TEXT NOT NULL UNIQUE,
                password_hash  TEXT NOT NULL,
                is_active      INTEGER DEFAULT 1,
                created_at     TEXT,
                last_login     TEXT,
                FOREIGN KEY (member_id) REFERENCES members(member_id)
            )
        """)
        print("  [OK] member_accounts")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS extension_requests (
                request_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id       INTEGER NOT NULL,
                member_id      INTEGER NOT NULL,
                requested_days INTEGER NOT NULL,
                reason         TEXT,
                status         TEXT DEFAULT 'PENDING',
                requested_on   TEXT,
                decided_on     TEXT,
                admin_note     TEXT,
                FOREIGN KEY (issue_id)  REFERENCES issue_return(issue_id),
                FOREIGN KEY (member_id) REFERENCES members(member_id),
                CHECK (status IN ('PENDING','APPROVED','REJECTED'))
            )
        """)
        print("  [OK] extension_requests")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS fines (
                fine_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id      INTEGER NOT NULL UNIQUE,
                member_id     INTEGER NOT NULL,
                amount        REAL NOT NULL,
                paid_amount   REAL DEFAULT 0.0,
                status        TEXT DEFAULT 'UNPAID',
                generated_on  TEXT,
                paid_on       TEXT,
                FOREIGN KEY (issue_id)  REFERENCES issue_return(issue_id),
                FOREIGN KEY (member_id) REFERENCES members(member_id),
                CHECK (status IN ('UNPAID','PAID','WAIVED'))
            )
        """)
        print("  [OK] fines")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id       INTEGER NOT NULL,
                member_id      INTEGER NOT NULL,
                channel        TEXT,
                message        TEXT,
                status         TEXT DEFAULT 'PENDING',
                created_on     TEXT,
                sent_on        TEXT,
                FOREIGN KEY (issue_id)  REFERENCES issue_return(issue_id),
                FOREIGN KEY (member_id) REFERENCES members(member_id)
            )
        """)
        print("  [OK] reminders")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS magazines (
                magazine_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                publisher     TEXT,
                month         TEXT,
                year          INTEGER,
                category      TEXT,
                quantity      INTEGER DEFAULT 1,
                available     INTEGER DEFAULT 1,
                date_added    TEXT
            )
        """)
        print("  [OK] magazines")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS newspapers (
                newspaper_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                publisher     TEXT,
                pub_date      TEXT,
                language      TEXT,
                quantity      INTEGER DEFAULT 1,
                available     INTEGER DEFAULT 1,
                date_added    TEXT
            )
        """)
        print("  [OK] newspapers")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                log_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_type    TEXT,
                user_id      INTEGER,
                action       TEXT,
                details      TEXT,
                timestamp    TEXT
            )
        """)
        print("  [OK] activity_logs")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key    TEXT PRIMARY KEY,
                value  TEXT
            )
        """)
        print("  [OK] settings")

        # -------- Default settings --------
        print("\n[4] Inserting default settings...")
        defaults = {
            "fine_rate_per_day":        "1.0",
            "loan_period_days":         "14",
            "max_extension_days":       "7",
            "max_extensions_per_book":  "1",
            "reminder_days_before_due": "2",
            "library_website_url":      "",
            "news_link":                "https://dailyvarthe.com/?p=105698",
            "college_portal":           "https://rnspolytechnic.in/",
            "notification_channel":     "none",
            "schema_version":           "2",
        }
        for k, v in defaults.items():
            cur.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (k, v)
            )
        print(f"  [OK] {len(defaults)} default settings ready")

        # -------- Indexes --------
        print("\n[5] Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_books_title    ON books(title)",
            "CREATE INDEX IF NOT EXISTS idx_books_author   ON books(author_id)",
            "CREATE INDEX IF NOT EXISTS idx_ir_member      ON issue_return(member_id)",
            "CREATE INDEX IF NOT EXISTS idx_ir_status      ON issue_return(status)",
            "CREATE INDEX IF NOT EXISTS idx_ir_due         ON issue_return(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_fines_status   ON fines(status)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON activity_logs(timestamp)",
        ]
        for sql in indexes:
            cur.execute(sql)
        print(f"  [OK] {len(indexes)} indexes created")

        conn.commit()
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print("\n!!! MIGRATION FAILED !!!")
        print(f"Error: {e}")
        print("Your database was NOT modified. Restore from backup if needed.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()