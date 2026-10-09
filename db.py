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

# If running as PyInstaller .exe and local DB doesn't exist, extract bundled sample DB
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    bundled_db = os.path.join(sys._MEIPASS, "library.db")
    if os.path.isfile(bundled_db) and not os.path.isfile(DB_NAME):
        try:
            import shutil
            shutil.copyfile(bundled_db, DB_NAME)
        except Exception:
            pass


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
            member_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id     TEXT UNIQUE,
            name        TEXT NOT NULL,
            dept        TEXT NOT NULL DEFAULT 'CSE',
            member_type TEXT NOT NULL DEFAULT 'STUDENT',
            email       TEXT UNIQUE,
            phone       TEXT NOT NULL
        )
    """)

    # Safe migration: ensure existing tables get new columns
    cur.execute("PRAGMA table_info(members)")
    m_cols = [c[1] for c in cur.fetchall()]
    if "card_id" not in m_cols:
        cur.execute("ALTER TABLE members ADD COLUMN card_id TEXT")
    if "dept" not in m_cols:
        cur.execute("ALTER TABLE members ADD COLUMN dept TEXT NOT NULL DEFAULT 'CSE'")
    if "member_type" not in m_cols:
        cur.execute("ALTER TABLE members ADD COLUMN member_type TEXT NOT NULL DEFAULT 'STUDENT'")

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
    cur.execute("CREATE INDEX IF NOT EXISTS idx_members_card   ON members(card_id)")

    # Backfill card_id and dept for any legacy members without card_id
    cur.execute("SELECT member_id, name FROM members WHERE card_id IS NULL OR card_id = ''")
    unassigned = cur.fetchall()
    if unassigned:
        dept_cycle = ["CSE", "ME", "AE", "EE"]
        for idx, (mid, mname) in enumerate(unassigned):
            d = dept_cycle[idx % len(dept_cycle)]
            cur.execute("SELECT card_id FROM members WHERE dept = ? AND card_id IS NOT NULL", (d,))
            existing_cids = [r[0] for r in cur.fetchall()]
            next_num = 1
            for cid in existing_cids:
                if cid and cid.startswith(d):
                    parts = cid.replace("-", " ").split()
                    for p in parts:
                        if p.isdigit():
                            next_num = max(next_num, int(p) + 1)
            cid_val = f"{d} {next_num}"
            cur.execute(
                "UPDATE members SET dept = ?, card_id = ?, member_type = 'STUDENT' WHERE member_id = ?",
                (d, cid_val, mid)
            )

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
# 6. Card ID Generation Helper
# ------------------------------------------------------------
def get_next_card_id(dept="CSE"):
    """
    Computes the next sequence number for a department Card ID.
    e.g. if 'ME 1', 'ME 2' exist, returns 'ME 3'.
    Works for CSE, ME, AE, EE or any department prefix.
    """
    conn = get_connection()
    cur = conn.cursor()
    dept_clean = (dept or "CSE").strip().upper()
    cur.execute(
        "SELECT card_id FROM members WHERE card_id LIKE ? OR dept = ?",
        (f"{dept_clean}%", dept_clean)
    )
    rows = cur.fetchall()
    conn.close()

    max_num = 0
    for (cid,) in rows:
        if not cid:
            continue
        parts = cid.strip().replace("-", " ").split()
        for p in parts:
            if p.isdigit():
                max_num = max(max_num, int(p))
                break

    return f"{dept_clean} {max_num + 1}"


# ------------------------------------------------------------
# 7. Run this file directly to create the database.
# ------------------------------------------------------------
if __name__ == "__main__":
    setup_database()