# ============================================================
# activity_log.py
# Central helper for logging important actions.
# ============================================================

from datetime import datetime
from db import run_query


def log_action(user_type, user_id, action, details=""):
    """
    Insert one row into activity_logs.

    user_type : 'ADMIN' or 'MEMBER' or 'SYSTEM'
    user_id   : the id of the user (or None for system events)
    action    : short string, e.g. 'LOGIN', 'BOOK_ADD', 'FINE_PAID'
    details   : optional longer text
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        run_query(
            "INSERT INTO activity_logs (user_type, user_id, action, details, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_type, user_id, action, details, ts)
        )
    except Exception as e:
        # Never let logging crash the app
        print(f"[activity_log] Failed to log: {e}")