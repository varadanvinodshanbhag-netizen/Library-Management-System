# ============================================================
# auth.py
# Password hashing and verification using bcrypt.
# ============================================================

import bcrypt
import sqlite3
from datetime import datetime

DB_NAME = "library.db"


# ------------------------------------------------------------
# Hash a plain password
# ------------------------------------------------------------
def hash_password(plain_password):
    if isinstance(plain_password, str):
        plain_password = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password, salt).decode("utf-8")


# ------------------------------------------------------------
# Verify a plain password against a stored hash
# ------------------------------------------------------------
def verify_password(plain_password, hashed):
    if not hashed:
        return False
    if isinstance(plain_password, str):
        plain_password = plain_password.encode("utf-8")
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(plain_password, hashed)
    except Exception:
        return False


# ------------------------------------------------------------
# One-time migration: hash any plain passwords in users table
# ------------------------------------------------------------
def migrate_plain_admin_passwords():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT user_id, password, password_hash FROM users")
    rows = cur.fetchall()

    migrated = 0
    for user_id, plain, hashed in rows:
        if hashed:
            continue
        if not plain:
            continue
        new_hash = hash_password(plain)
        cur.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?",
            (new_hash, user_id)
        )
        migrated += 1

    conn.commit()
    conn.close()

    if migrated:
        print(f"[auth] Migrated {migrated} plain admin password(s) to bcrypt.")
    else:
        print("[auth] No admin passwords needed migration.")


# ------------------------------------------------------------
# Ensure the default admin exists with a bcrypt hash
# ------------------------------------------------------------
def ensure_default_admin():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("admin",))
    exists = cur.fetchone()[0]

    if exists == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "INSERT INTO users (username, password, password_hash, role, is_active, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "", hash_password("admin123"), "ADMIN", 1, now)
        )
        print("[auth] Default admin created (admin / admin123)")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    ensure_default_admin()
    migrate_plain_admin_passwords()