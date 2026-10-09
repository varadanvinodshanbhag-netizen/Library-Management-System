# ============================================================
# settings_ui.py
# Administrator Portal: System Configuration & Notification Rules.
# Features:
# - Lending periods and fine rate thresholds
# - Extension limits and overdue reminder settings
# - External institutional portal URLs
# - SMTP email configuration diagnostics and bulk dispatch
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from db import get_rows, get_one, run_query
from activity_log import log_action
from notification_config import is_email_configured, describe_config
from reminders import send_bulk_due_reminders, send_email
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, styled_entry,
    primary_button, success_button, danger_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


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

    section_title(
        parent,
        "System Configuration & Rules",
        "Configure circulation policies, fine charges, external links, and automated reminders"
    )

    # Scrollable container for settings if window is compact
    canvas = tk.Canvas(parent, bg=COLORS["card"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=COLORS["card"])

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=parent.winfo_width() or 960)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ============================================================
    # 1. CIRCULATION & FINES POLICY CARD
    # ============================================================
    card1 = tk.Frame(scroll_frame, bg=COLORS["card"],
                     highlightbackground=COLORS["border"], highlightthickness=1)
    card1.pack(fill="x", padx=PAD["section_x"], pady=(0, 14))

    # Header bar
    h1 = tk.Frame(card1, bg=COLORS["card_alt"], height=36)
    h1.pack(fill="x")
    h1.pack_propagate(False)
    tk.Label(h1, text="  📜  CIRCULATION & FINE POLICIES",
             font=FONTS["small_b"], bg=COLORS["card_alt"], fg=COLORS["primary"]).pack(side="left", padx=10)

    grid1 = tk.Frame(card1, bg=COLORS["card"])
    grid1.pack(fill="x", padx=16, pady=12)

    def policy_field(container, label_text, key, row, col, unit=""):
        tk.Label(container, text=label_text, bg=COLORS["card"],
                 fg=COLORS["text_secondary"], font=FONTS["small_b"]
                 ).grid(row=row, column=col*3, sticky="w", padx=(0, 6), pady=6)
        entry = styled_entry(container, width=12)
        entry.insert(0, _get_setting(key, ""))
        entry.grid(row=row, column=col*3 + 1, sticky="w", padx=(0, 4), pady=6, ipady=3)
        if unit:
            tk.Label(container, text=unit, bg=COLORS["card"],
                     fg=COLORS["text_muted"], font=FONTS["caption"]
                     ).grid(row=row, column=col*3 + 2, sticky="w", padx=(0, 24), pady=6)
        return entry

    fine_rate_entry    = policy_field(grid1, "Daily Fine Rate *",       "fine_rate_per_day",        0, 0, "Rs / day")
    loan_period_entry  = policy_field(grid1, "Standard Loan Period *",  "loan_period_days",         0, 1, "days")
    max_ext_days_entry = policy_field(grid1, "Max Extension Length *",  "max_extension_days",       1, 0, "days / request")
    max_ext_book_entry = policy_field(grid1, "Max Extensions Limit *",  "max_extensions_per_book",  1, 1, "times / loan")
    reminder_entry     = policy_field(grid1, "Pre-due Alert Timing *",  "reminder_days_before_due", 2, 0, "days prior")

    # ============================================================
    # 2. EXTERNAL RESOURCE LINKS CARD
    # ============================================================
    card2 = tk.Frame(scroll_frame, bg=COLORS["card"],
                     highlightbackground=COLORS["border"], highlightthickness=1)
    card2.pack(fill="x", padx=PAD["section_x"], pady=(0, 14))

    h2 = tk.Frame(card2, bg=COLORS["card_alt"], height=36)
    h2.pack(fill="x")
    h2.pack_propagate(False)
    tk.Label(h2, text="  🔗  INSTITUTIONAL PORTAL & EXTERNAL LINKS",
             font=FONTS["small_b"], bg=COLORS["card_alt"], fg=COLORS["primary"]).pack(side="left", padx=10)

    grid2 = tk.Frame(card2, bg=COLORS["card"])
    grid2.pack(fill="x", padx=16, pady=12)

    def link_field(container, label_text, key, row):
        tk.Label(container, text=label_text, bg=COLORS["card"],
                 fg=COLORS["text_secondary"], font=FONTS["small_b"]
                 ).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
        entry = styled_entry(container, width=64)
        entry.insert(0, _get_setting(key, ""))
        entry.grid(row=row, column=1, sticky="w", padx=(0, 10), pady=5, ipady=3)
        return entry

    news_entry    = link_field(grid2, "Campus News Link:", "news_link", 0)
    portal_entry  = link_field(grid2, "College Portal URL:", "college_portal", 1)
    website_entry = link_field(grid2, "Library Web URL:", "library_website_url", 2)

    # ============================================================
    # 3. NOTIFICATIONS & EMAIL AUTOMATION CARD
    # ============================================================
    card3 = tk.Frame(scroll_frame, bg=COLORS["card"],
                     highlightbackground=COLORS["border"], highlightthickness=1)
    card3.pack(fill="x", padx=PAD["section_x"], pady=(0, 14))

    h3 = tk.Frame(card3, bg=COLORS["card_alt"], height=36)
    h3.pack(fill="x")
    h3.pack_propagate(False)
    tk.Label(h3, text="  ✉️  AUTOMATED ALERTS & NOTIFICATION ENGINE",
             font=FONTS["small_b"], bg=COLORS["card_alt"], fg=COLORS["primary"]).pack(side="left", padx=10)

    grid3 = tk.Frame(card3, bg=COLORS["card"])
    grid3.pack(fill="x", padx=16, pady=12)

    tk.Label(grid3, text="Alert Channel Mode:", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

    channel_var = tk.StringVar(value=_get_setting("notification_channel", "none"))
    channel_combo = ttk.Combobox(
        grid3, textvariable=channel_var, width=14,
        values=["none", "email"], state="readonly"
    )
    channel_combo.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=4)

    diag = describe_config()
    if is_email_configured():
        status_text = f"✅ SMTP Configured & Ready  ({diag['user']})"
        status_color = COLORS["success"]
    else:
        status_text = "⚠️ SMTP Credentials Not Set (Optional: Set LMS_SMTP_USER & LMS_SMTP_PASS in .env)"
        status_color = COLORS["accent"]

    tk.Label(
        grid3, text=status_text,
        bg=COLORS["card"], fg=status_color, font=FONTS["small"]
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

    # ============================================================
    # 4. SAVE & ACTIONS TOOLBAR
    # ============================================================
    action_panel = tk.Frame(scroll_frame, bg=COLORS["card"])
    action_panel.pack(fill="x", padx=PAD["section_x"], pady=(6, 24))

    def save_settings():
        fields = [
            ("Fine rate", fine_rate_entry.get().strip()),
            ("Loan period", loan_period_entry.get().strip()),
            ("Max extension days", max_ext_days_entry.get().strip()),
            ("Max extensions limit", max_ext_book_entry.get().strip()),
            ("Reminder timing", reminder_entry.get().strip()),
        ]
        for name, val in fields:
            if not val:
                show_warning("Validation Error", f"{name} cannot be empty.")
                return
            if name == "Fine rate":
                try:
                    float(val)
                except ValueError:
                    show_error("Validation Error", "Fine rate must be a valid numeric value.")
                    return
            else:
                if not val.isdigit():
                    show_error("Validation Error", f"{name} must be an integer number.")
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

        log_action("ADMIN", admin_id, "SETTINGS_UPDATED", "Updated system and circulation policies")
        show_success("Configuration Saved", "All system configuration parameters have been applied.")

    def reset_links():
        if not ask_confirm("Reset Default URLs", "Restore official RNS Polytechnic and campus news links?"):
            return
        default_news = "https://dailyvarthe.com/?p=105698"
        default_portal = "https://rnspolytechnic.in/"
        _set_setting("news_link", default_news)
        _set_setting("college_portal", default_portal)
        news_entry.delete(0, tk.END); news_entry.insert(0, default_news)
        portal_entry.delete(0, tk.END); portal_entry.insert(0, default_portal)
        log_action("ADMIN", admin_id, "SETTINGS_RESET_LINKS", "Restored default external URLs")
        show_success("Links Restored", "Default institution URLs restored.")

    def send_reminders_now():
        if not ask_confirm(
            "Dispatch Overdue Reminders",
            "Scan database and queue due-date alerts for books due within upcoming window or overdue?"
        ):
            return
        try:
            days = int(_get_setting("reminder_days_before_due", "2"))
        except ValueError:
            days = 2

        result = send_bulk_due_reminders(days_ahead=days, admin_id=admin_id)
        msg = (
            f"Total Overdue/Due-Soon Loans: {result['total']}\n"
            f"Successfully Dispatched: {result['sent']}\n"
            f"Logged to Audit Trail: {result['logged']}\n"
            f"Failed: {result['failed']}"
        )
        messagebox.showinfo("Reminder Execution Summary", msg)

    def test_email():
        if not is_email_configured():
            show_error(
                "SMTP Unconfigured",
                "Email credentials are not configured.\n\n"
                "Please configure LMS_SMTP_USER and LMS_SMTP_PASS in your .env file."
            )
            return

        to_addr = simpledialog.askstring("Test SMTP Dispatch", "Enter recipient email address:", parent=parent)
        if not to_addr:
            return

        subj = "Library Management System - Notification Verification"
        body = ("This is a test notification from RNS Rural Polytechnic Library Management System.\n\n"
                "If you received this message, automated due date alerts are operational.")
        ok, err = send_email(to_addr, subj, body)
        if ok:
            log_action("ADMIN", admin_id, "TEST_EMAIL_SENT", f"Sent test alert to {to_addr}")
            show_success("Test Email Dispatched", f"Test message successfully delivered to {to_addr}.")
        else:
            show_error("Dispatch Error", f"Could not send email:\n{err}")

    success_button(action_panel, "💾  Save Configuration", save_settings,     width=20).grid(row=0, column=0, padx=6)
    neutral_button(action_panel, "🔄  Reset URLs",         reset_links,       width=15).grid(row=0, column=1, padx=6)
    primary_button(action_panel, "📤  Run Alert Dispatch", send_reminders_now, width=20).grid(row=0, column=2, padx=6)
    primary_button(action_panel, "🧪  Test Email",         test_email,        width=15).grid(row=0, column=3, padx=6)