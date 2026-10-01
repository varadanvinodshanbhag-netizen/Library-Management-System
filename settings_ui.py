# ============================================================
# settings_ui.py
# Admin settings screen: change fine rate, loan period, links, etc.
# Also: send bulk reminders + test email.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from db import get_rows, get_one, run_query
from activity_log import log_action
from notification_config import is_email_configured, describe_config
from reminders import send_bulk_due_reminders, send_email
from ui_helpers import (
    COLORS, FONTS, section_title, primary_button,
    success_button, danger_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


# ------------------------------------------------------------
# Read a setting safely
# ------------------------------------------------------------
def _get_setting(key, default=""):
    row = get_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row[0] if row and row[0] is not None else default


def _set_setting(key, value):
    row = get_one("SELECT key FROM settings WHERE key = ?", (key,))
    if row:
        run_query("UPDATE settings SET value = ? WHERE key = ?", (str(value), key))
    else:
        run_query("INSERT INTO settings (key, value) VALUES (?, ?)", (key, str(value)))


def show_settings_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(parent, "Settings", "Configure fine rates, loan period, links and reminders")

    # ============================================================
    # 1. Library / Fine settings
    # ============================================================
    tk.Label(parent, text="Library Rules", font=FONTS["h3"],
             bg=COLORS["card"], fg=COLORS["primary"]
             ).pack(anchor="w", padx=20, pady=(10, 5))

    frame1 = tk.Frame(parent, bg=COLORS["card"])
    frame1.pack(fill="x", padx=20, pady=(0, 10))

    def labeled_entry(parent, label, key, width=12, row=0, col=0):
        tk.Label(parent, text=label, bg=COLORS["card"], font=FONTS["body"]
                 ).grid(row=row, column=col*2, sticky="w", padx=(0, 6), pady=5)
        e = tk.Entry(parent, width=width, font=FONTS["body"],
                     relief="solid", bd=1)
        e.insert(0, _get_setting(key, ""))
        e.grid(row=row, column=col*2 + 1, padx=(0, 20), pady=5, ipady=3)
        return e

    fine_rate_entry   = labeled_entry(frame1, "Fine rate (Rs/day)",     "fine_rate_per_day",        12, 0, 0)
    loan_period_entry = labeled_entry(frame1, "Loan period (days)",     "loan_period_days",         12, 0, 1)
    max_ext_days_entry= labeled_entry(frame1, "Max extension days",     "max_extension_days",       12, 1, 0)
    max_ext_book_entry= labeled_entry(frame1, "Max extensions / book",  "max_extensions_per_book",  12, 1, 1)
    reminder_entry    = labeled_entry(frame1, "Reminder days before due", "reminder_days_before_due", 12, 2, 0)

    # ============================================================
    # 2. Links
    # ============================================================
    tk.Label(parent, text="Links (opened in default browser)",
             font=FONTS["h3"], bg=COLORS["card"], fg=COLORS["primary"]
             ).pack(anchor="w", padx=20, pady=(10, 5))

    frame2 = tk.Frame(parent, bg=COLORS["card"])
    frame2.pack(fill="x", padx=20, pady=(0, 10))

    def wide_entry(parent, label, key, row=0):
        tk.Label(parent, text=label, bg=COLORS["card"], font=FONTS["body"]
                 ).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=5)
        e = tk.Entry(parent, width=64, font=FONTS["body"],
                     relief="solid", bd=1)
        e.insert(0, _get_setting(key, ""))
        e.grid(row=row, column=1, padx=(0, 10), pady=5, ipady=3)
        return e

    news_entry    = wide_entry(frame2, "Latest News URL",    "news_link",             0)
    portal_entry  = wide_entry(frame2, "College Portal URL", "college_portal",        1)
    website_entry = wide_entry(frame2, "Library Website URL","library_website_url",   2)

    # ============================================================
    # 3. Notification
    # ============================================================
    tk.Label(parent, text="Notifications", font=FONTS["h3"],
             bg=COLORS["card"], fg=COLORS["primary"]
             ).pack(anchor="w", padx=20, pady=(10, 5))

    frame3 = tk.Frame(parent, bg=COLORS["card"])
    frame3.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(frame3, text="Channel:", bg=COLORS["card"], font=FONTS["body"]
             ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=5)
    channel_var = tk.StringVar(value=_get_setting("notification_channel", "none"))
    ttk.Combobox(
        frame3, textvariable=channel_var, width=12,
        values=["none", "email"], state="readonly"
    ).grid(row=0, column=1, padx=(0, 20), pady=5)

    # Diagnostic label
    diag = describe_config()
    if is_email_configured():
        diag_text = f"Email: READY  ({diag['user']})"
        diag_color = COLORS["success"]
    else:
        diag_text = ("Email: NOT CONFIGURED. "
                     "Create a .env file with LMS_SMTP_USER and LMS_SMTP_PASS.")
        diag_color = COLORS["danger"]

    tk.Label(frame3, text=diag_text, bg=COLORS["card"],
             fg=diag_color, font=FONTS["small"]
             ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

    # ============================================================
    # 4. Buttons (bottom, packed first so they stay at bottom)
    # ============================================================
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 15))

    # ============================================================
    # Save all
    # ============================================================
    def save_settings():
        # Validate numeric fields
        fields = [
            ("Fine rate", fine_rate_entry.get().strip()),
            ("Loan period", loan_period_entry.get().strip()),
            ("Max extension days", max_ext_days_entry.get().strip()),
            ("Max extensions / book", max_ext_book_entry.get().strip()),
            ("Reminder days", reminder_entry.get().strip()),
        ]
        for name, val in fields:
            if not val:
                show_warning("Warning", f"{name} cannot be empty.")
                return
            if name == "Fine rate":
                try:
                    float(val)
                except ValueError:
                    show_error("Error", "Fine rate must be a number.")
                    return
            else:
                if not val.isdigit():
                    show_error("Error", f"{name} must be a number.")
                    return

        _set_setting("fine_rate_per_day",        fine_rate_entry.get().strip())
        _set_setting("loan_period_days",         loan_period_entry.get().strip())
        _set_setting("max_extension_days",       max_ext_days_entry.get().strip())
        _set_setting("max_extensions_per_book",  max_ext_book_entry.get().strip())
        _set_setting("reminder_days_before_due", reminder_entry.get().strip())
        _set_setting("news_link",                news_entry.get().strip())
        _set_setting("college_portal",           portal_entry.get().strip())
        _set_setting("library_website_url",      website_entry.get().strip())
        _set_setting("notification_channel",     channel_var.get())

        log_action("ADMIN", admin_id, "SETTINGS_UPDATED",
                   "Library settings changed")
        show_success("Saved", "All settings updated successfully.")

    def reset_links():
        if not ask_confirm("Reset Links",
                           "Reset News and College Portal to the defaults?"):
            return
        _set_setting("news_link", "https://dailyvarthe.com/?p=105698")
        _set_setting("college_portal", "https://rnspolytechnic.in/")
        news_entry.delete(0, tk.END)
        news_entry.insert(0, "https://dailyvarthe.com/?p=105698")
        portal_entry.delete(0, tk.END)
        portal_entry.insert(0, "https://rnspolytechnic.in/")
        log_action("ADMIN", admin_id, "SETTINGS_RESET_LINKS",
                   "Reset news and portal URLs")
        show_success("Reset", "Default links restored.")

    def send_reminders_now():
        if not ask_confirm("Send Reminders",
                           "Send due-date reminders to all members whose books "
                           "are due soon or overdue?"):
            return
        try:
            days = int(_get_setting("reminder_days_before_due", "2"))
        except ValueError:
            days = 2

        result = send_bulk_due_reminders(days_ahead=days, admin_id=admin_id)
        msg = (
            f"Total: {result['total']}\n"
            f"Sent: {result['sent']}\n"
            f"Logged (no email): {result['logged']}\n"
            f"Failed: {result['failed']}"
        )
        messagebox.showinfo("Reminder Summary", msg)

    def test_email():
        if not is_email_configured():
            show_error("Not Configured",
                       "Email is not configured.\n\n"
                       "Add LMS_SMTP_USER and LMS_SMTP_PASS in .env, "
                       "then restart the app.")
            return
        to = tk.simpledialog.askstring("Test Email",
                                       "Send a test email to:",
                                       parent=parent) if hasattr(tk, "simpledialog") else None
        # Fallback (simpledialog may not be imported by default)
        from tkinter import simpledialog
        to = simpledialog.askstring("Test Email",
                                    "Send a test email to:", parent=parent)
        if not to:
            return
        subject = "Library Management System - Test Email"
        body = ("This is a test email from your Library Management System.\n\n"
                "If you received this, your email configuration is working.")
        ok, err = send_email(to, subject, body)
        if ok:
            log_action("ADMIN", admin_id, "TEST_EMAIL_SENT",
                       f"Test email sent to {to}")
            show_success("Sent", f"Test email sent to {to}.")
        else:
            show_error("Failed", f"Could not send:\n{err}")

    # ---------- Buttons ----------
    success_button(btn_row, "Save All Settings", save_settings,     width=18).grid(row=0, column=0, padx=5)
    neutral_button(btn_row, "Reset Links",       reset_links,       width=14).grid(row=0, column=1, padx=5)
    primary_button(btn_row, "Send Reminders",    send_reminders_now, width=16).grid(row=0, column=2, padx=5)
    primary_button(btn_row, "Test Email",        test_email,        width=14).grid(row=0, column=3, padx=5)