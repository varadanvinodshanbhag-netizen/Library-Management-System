# ============================================================
# db.py
# Database helpers for the Library Management System.
# Uses SQLite (built into Python - no install needed).
# Works both as a normal script and as a PyInstaller .exe.
# ============================================================

import sqlite3
import os
import sys


# ------------------------------------------------------------
# Determine where the database file should live
# - As a script : next to db.py
# - As an .exe  : next to the executable
# ------------------------------------------------------------
def _get_app_dir():
    if getattr(sys, "frozen", False):
        # Running from a PyInstaller-built .exe
        return os.path.dirname(sys.executable)
    # Running as a normal Python script
    return os.path.dirname(os.path.abspath(__file__))


DB_NAME = os.path.join(_get_app_dir(), "library.db")


# ------------------------------------------------------------
# 1. Open a connection to the database
# ------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")   # enforce foreign keys
    return conn


# ------------------------------------------------------------
# 2. Run INSERT / UPDATE / DELETE queries
# ------------------------------------------------------------
def run_query(sql, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


# ------------------------------------------------------------
# 3. Run SELECT queries that return many rows
#    Returns a list of tuples.
# ------------------------------------------------------------
def get_rows(sql, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows


# ------------------------------------------------------------
# 4. Run SELECT queries that return one row
#    Returns a tuple, or None if nothing found.
# ------------------------------------------------------------
def get_one(sql, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row


# ------------------------------------------------------------
# 5. Create all tables (only if they don't already exist)
#    Also inserts a default admin and default settings.
# ------------------------------------------------------------
def setup_database():
    conn = get_connection()
    cur = conn.cursor()

    # ----- users (admin login) -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password      TEXT NOT NULL DEFAULT '',
            password_hash TEXT,
            role          TEXT NOT NULL DEFAULT 'ADMIN',
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT,
            last_login    TEXT
        )
    """)

    # ----- authors -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            author_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            author_name TEXT NOT NULL UNIQUE
        )
    """)

    # ----- categories -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
    """)

    # ----- books -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT NOT NULL,
            author_id        INTEGER NOT NULL,
            category_id      INTEGER NOT NULL,
            total_copies     INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (author_id)   REFERENCES authors(author_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            CHECK (available_copies >= 0 AND available_copies <= total_copies)
        )
    """)

    # ----- members -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            email     TEXT UNIQUE,
            phone     TEXT NOT NULL
        )
    """)

    # ----- issue_return (with fine-related columns) -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS issue_return (
            issue_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id            INTEGER NOT NULL,
            member_id          INTEGER NOT NULL,
            issue_date         TEXT NOT NULL,
            return_date        TEXT,
            due_date           TEXT,
            actual_return_date TEXT,
            overdue_days       INTEGER DEFAULT 0,
            fine_rate          REAL DEFAULT 1.0,
            fine_amount        REAL DEFAULT 0.0,
            fine_status        TEXT DEFAULT 'NONE',
            extension_count    INTEGER DEFAULT 0,
            status             TEXT NOT NULL DEFAULT 'ISSUED',
            FOREIGN KEY (book_id)   REFERENCES books(book_id),
            FOREIGN KEY (member_id) REFERENCES members(member_id),
            CHECK (status IN ('ISSUED', 'RETURNED'))
        )
    """)

    # ----- member_accounts (member login) -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS member_accounts (
            account_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id     INTEGER NOT NULL UNIQUE,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_active     INTEGER DEFAULT 1,
            created_at    TEXT,
            last_login    TEXT,
            FOREIGN KEY (member_id) REFERENCES members(member_id)
        )
    """)

    # ----- fines -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            fine_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id     INTEGER NOT NULL UNIQUE,
            member_id    INTEGER NOT NULL,
            amount       REAL NOT NULL,
            paid_amount  REAL DEFAULT 0.0,
            status       TEXT DEFAULT 'UNPAID',
            generated_on TEXT,
            paid_on      TEXT,
            FOREIGN KEY (issue_id)  REFERENCES issue_return(issue_id),
            FOREIGN KEY (member_id) REFERENCES members(member_id),
            CHECK (status IN ('UNPAID','PAID','WAIVED'))
        )
    """)

    # ----- extension_requests -----
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

    # ----- reminders -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id    INTEGER NOT NULL,
            member_id   INTEGER NOT NULL,
            channel     TEXT,
            message     TEXT,
            status      TEXT DEFAULT 'PENDING',
            created_on  TEXT,
            sent_on     TEXT,
            FOREIGN KEY (issue_id)  REFERENCES issue_return(issue_id),
            FOREIGN KEY (member_id) REFERENCES members(member_id)
        )
    """)

    # ----- magazines -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS magazines (
            magazine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            publisher   TEXT,
            month       TEXT,
            year        INTEGER,
            category    TEXT,
            quantity    INTEGER DEFAULT 1,
            available   INTEGER DEFAULT 1,
            date_added  TEXT
        )
    """)

    # ----- newspapers -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newspapers (
            newspaper_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            publisher    TEXT,
            pub_date     TEXT,
            language     TEXT,
            quantity     INTEGER DEFAULT 1,
            available    INTEGER DEFAULT 1,
            date_added   TEXT
        )
    """)

    # ----- activity_logs -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT,
            user_id   INTEGER,
            action    TEXT,
            details   TEXT,
            timestamp TEXT
        )
    """)

    # ----- settings -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # ----- indexes -----
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_title    ON books(title)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_author   ON books(author_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ir_member      ON issue_return(member_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ir_status      ON issue_return(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ir_due         ON issue_return(due_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fines_status   ON fines(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON activity_logs(timestamp)")

    conn.commit()

    # ----- Insert default admin (with bcrypt hash) if none exists -----
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        try:
            from auth import hash_password
            pw_hash = hash_password("admin123")
        except Exception:
            pw_hash = None
        now = "2026-01-01 00:00:00"
        cur.execute(
            "INSERT INTO users (username, password, password_hash, role, is_active, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "", pw_hash, "ADMIN", 1, now)
        )
        print("Default admin created  ->  username: admin  |  password: admin123")

    # ----- Insert default settings -----
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
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()
    print("Database is ready.")


# ------------------------------------------------------------
# 6. Run this file directly to create the database.
# ------------------------------------------------------------
if __name__ == "__main__":
    setup_database()