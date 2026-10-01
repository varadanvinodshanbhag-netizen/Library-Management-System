# ============================================================
# fine_calc.py
# Central place for fine calculation and due-date logic.
# All fine rates and loan periods come from the 'settings' table.
# ============================================================

from datetime import datetime, date, timedelta
from db import get_one


# ------------------------------------------------------------
# Read a setting from the database
# ------------------------------------------------------------
def get_setting(key, default=None):
    row = get_one("SELECT value FROM settings WHERE key = ?", (key,))
    if row and row[0] is not None:
        return row[0]
    return default


# ------------------------------------------------------------
# Get the current fine rate (Rs per day)
# ------------------------------------------------------------
def get_fine_rate():
    try:
        return float(get_setting("fine_rate_per_day", "1.0"))
    except (TypeError, ValueError):
        return 1.0


# ------------------------------------------------------------
# Get the loan period in days
# ------------------------------------------------------------
def get_loan_period_days():
    try:
        return int(get_setting("loan_period_days", "14"))
    except (TypeError, ValueError):
        return 14


# ------------------------------------------------------------
# Parse a date string (YYYY-MM-DD) into a date object
# ------------------------------------------------------------
def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


# ------------------------------------------------------------
# Calculate due date from issue date
# ------------------------------------------------------------
def calculate_due_date(issue_date_str):
    issue_dt = parse_date(issue_date_str)
    if issue_dt is None:
        return None
    due_dt = issue_dt + timedelta(days=get_loan_period_days())
    return due_dt.strftime("%Y-%m-%d")


# ------------------------------------------------------------
# Calculate overdue days and fine amount
# Returns: (overdue_days, fine_amount)
# ------------------------------------------------------------
def calculate_fine(due_date_str, return_date_str=None):
    due_dt = parse_date(due_date_str)
    if due_dt is None:
        return 0, 0.0

    if return_date_str:
        ret_dt = parse_date(return_date_str)
    else:
        ret_dt = date.today()

    if ret_dt is None:
        return 0, 0.0

    if ret_dt <= due_dt:
        return 0, 0.0

    overdue_days = (ret_dt - due_dt).days
    fine_amount = overdue_days * get_fine_rate()
    return overdue_days, round(fine_amount, 2)


# ------------------------------------------------------------
# Quick test (run this file directly)
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Fine rate per day :", get_fine_rate())
    print("Loan period       :", get_loan_period_days(), "days")

    today = date.today().strftime("%Y-%m-%d")
    due = calculate_due_date(today)
    print(f"Issued today ({today}) -> due on {due}")

    days, amt = calculate_fine("2026-10-10", "2026-10-14")
    print(f"Due 2026-10-10, Returned 2026-10-14 -> {days} days overdue, fine = Rs {amt}")

    days, amt = calculate_fine("2026-10-10", "2026-10-08")
    print(f"Due 2026-10-10, Returned 2026-10-08 -> {days} days overdue, fine = Rs {amt}")