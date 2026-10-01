# ============================================================
# reminders.py
# Email reminder sender + logging.
# - Builds message text
# - Logs every attempt to 'reminders' table
# - Sends via Gmail SMTP only if credentials are configured
# - Never crashes if email is not set up
# ============================================================

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from db import run_query, get_rows, get_one
from activity_log import log_action
from notification_config import (
    get_smtp_host, get_smtp_port, get_smtp_user, get_smtp_pass,
    get_library_name, is_email_configured
)


# ------------------------------------------------------------
# Build a standard reminder message
# ------------------------------------------------------------
def build_reminder_message(member_name, book_title, due_date,
                            status_text="due soon"):
    lib = get_library_name()
    subject = f"[{lib}] Reminder: '{book_title}' is {status_text}"
    body = f"""Dear {member_name},

This is a friendly reminder from {lib}.

Book      : {book_title}
Due date  : {due_date}
Status    : {status_text}

You may return the book on or before the due date to avoid a fine.
If you need more time, you can request an extension from your member dashboard.

Thank you,
{lib}
"""
    return subject, body


# ------------------------------------------------------------
# Log a reminder attempt (always runs, whether we send or not)
# ------------------------------------------------------------
def log_reminder(issue_id, member_id, channel, message, status="PENDING"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query(
        "INSERT INTO reminders "
        "(issue_id, member_id, channel, message, status, created_on) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (issue_id, member_id, channel, message, status, now)
    )
    return now


# ------------------------------------------------------------
# Mark the latest pending reminder as SENT
# ------------------------------------------------------------
def mark_reminder_sent(issue_id, member_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query(
        "UPDATE reminders SET status = 'SENT', sent_on = ? "
        "WHERE reminder_id = ("
        "   SELECT reminder_id FROM reminders "
        "   WHERE issue_id = ? AND member_id = ? "
        "   ORDER BY reminder_id DESC LIMIT 1"
        ")",
        (now, issue_id, member_id)
    )


# ------------------------------------------------------------
# Actual SMTP send
# Returns (success: bool, error_message: str|None)
# ------------------------------------------------------------
def send_email(to_email, subject, body):
    if not is_email_configured():
        return False, "Email not configured (missing LMS_SMTP_USER / LMS_SMTP_PASS)."

    if not to_email:
        return False, "Member has no email address."

    try:
        msg = MIMEMultipart()
        msg["From"] = get_smtp_user()
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP(get_smtp_host(), get_smtp_port(), timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(get_smtp_user(), get_smtp_pass())
            server.sendmail(get_smtp_user(), to_email, msg.as_string())

        return True, None
    except Exception as e:
        return False, str(e)


# ------------------------------------------------------------
# Send a due-date reminder for one specific issue
# ------------------------------------------------------------
def send_due_reminder(issue_id, admin_id=None):
    row = get_one("""
        SELECT ir.issue_id, ir.member_id, ir.due_date, ir.status,
               b.title, m.name, m.email
        FROM issue_return ir
        JOIN books b   ON ir.book_id   = b.book_id
        JOIN members m ON ir.member_id = m.member_id
        WHERE ir.issue_id = ?
    """, (issue_id,))

    if not row:
        return False, "Issue not found."

    (iid, member_id, due_date, status,
     title, member_name, member_email) = row

    if status != "ISSUED":
        return False, "This book is already returned."

    if not due_date:
        return False, "This issue has no due date set."

    today = datetime.now().date()
    try:
        due_dt = datetime.strptime(due_date, "%Y-%m-%d").date()
    except Exception:
        return False, "Invalid due date format."

    days_left = (due_dt - today).days
    if days_left < 0:
        status_text = f"OVERDUE by {abs(days_left)} day(s)"
    elif days_left == 0:
        status_text = "DUE TODAY"
    else:
        status_text = f"due in {days_left} day(s)"

    subject, body = build_reminder_message(
        member_name, title, due_date, status_text
    )

    log_reminder(iid, member_id, "email", body, "PENDING")

    ok, err = send_email(member_email, subject, body)

    if ok:
        mark_reminder_sent(iid, member_id)
        log_action(
            "SYSTEM", admin_id, "REMINDER_SENT",
            f"Reminder sent to {member_name} <{member_email}> for '{title}'"
        )
        return True, None
    else:
        log_action(
            "SYSTEM", admin_id, "REMINDER_LOGGED",
            f"Reminder logged (not sent): {err}"
        )
        return False, err


# ------------------------------------------------------------
# Send reminders to all members with books due within N days
# (or already overdue)
# ------------------------------------------------------------
def send_bulk_due_reminders(days_ahead=2, admin_id=None):
    rows = get_rows("""
        SELECT ir.issue_id
        FROM issue_return ir
        WHERE ir.status = 'ISSUED'
          AND ir.due_date IS NOT NULL
          AND date(ir.due_date) <= date('now', ?)
    """, (f"+{days_ahead} days",))

    sent, logged, failed = 0, 0, 0
    for r in rows:
        ok, err = send_due_reminder(r[0], admin_id=admin_id)
        if ok:
            sent += 1
        elif err and "not configured" in err.lower():
            logged += 1
        else:
            failed += 1

    return {"sent": sent, "logged": logged, "failed": failed, "total": len(rows)}


# ------------------------------------------------------------
# Test file directly
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Email configured:", is_email_configured())
    print("\nSending bulk reminders for books due in next 2 days or overdue...")
    result = send_bulk_due_reminders(days_ahead=2)
    print("Result:", result)