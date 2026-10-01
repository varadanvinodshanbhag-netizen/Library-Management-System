# ============================================================
# admin_dashboard.py
# Professional dashboard shown after admin login.
# ============================================================

import tkinter as tk
from tkinter import ttk

from db import get_one
from ui_helpers import (
    COLORS, FONTS, section_title, make_card, primary_button,
    success_button, neutral_button
)


def _count(sql, params=()):
    row = get_one(sql, params)
    return row[0] if row else 0


def show_dashboard(parent, navigate=None, logout=None):
    """
    parent   : the content frame
    navigate : callback(name) to switch screens
    logout   : callback() to log out
    """
    for widget in parent.winfo_children():
        widget.destroy()

    # ---- Heading ----
    section_title(
        parent,
        "Dashboard",
        "Overview of library activity"
    )

    # ---- Stat cards row ----
    stats_frame = tk.Frame(parent, bg=COLORS["card"])
    stats_frame.pack(fill="x", padx=20, pady=(5, 15))

    total_books     = _count("SELECT COUNT(*) FROM books")
    total_members   = _count("SELECT COUNT(*) FROM members")
    issued_now      = _count("SELECT COUNT(*) FROM issue_return WHERE status = 'ISSUED'")
    overdue_now     = _count(
        "SELECT COUNT(*) FROM issue_return "
        "WHERE status = 'ISSUED' AND due_date IS NOT NULL AND due_date < date('now')"
    )
    unpaid_fines    = _count("SELECT COUNT(*) FROM fines WHERE status = 'UNPAID'")
    pending_ext     = _count("SELECT COUNT(*) FROM extension_requests WHERE status = 'PENDING'")

    cards = [
        ("Total Books",     total_books,   COLORS["primary"]),
        ("Members",         total_members, COLORS["success"]),
        ("Issued Now",      issued_now,    "#457b9d"),
        ("Overdue",         overdue_now,   COLORS["danger"]),
        ("Unpaid Fines",    unpaid_fines,  COLORS["warning"]),
        ("Pending Ext.",    pending_ext,   COLORS["accent"]),
    ]

    for i, (title, value, color) in enumerate(cards):
        make_card(stats_frame, title, value, color=color).grid(
            row=0, column=i, padx=6, pady=6, sticky="nsew"
        )
        stats_frame.grid_columnconfigure(i, weight=1)

    # ---- Quick actions ----
    section_title(parent, "Quick Actions", "Jump to a module")

    actions_frame = tk.Frame(parent, bg=COLORS["card"])
    actions_frame.pack(fill="x", padx=20, pady=(0, 15))

    actions = [
        ("Manage Books",        "books"),
        ("Manage Members",      "members"),
        ("Issue / Return",      "issue"),
        ("Search & Sort",       "search"),
        ("Member Accounts",     "member_accounts"),
        ("Fine Management",     "fines"),
        ("Extension Requests",  "extensions"),
        ("Reports",             "reports"),
        ("Magazines",           "magazines"),
        ("Newspapers",          "newspapers"),
        ("Settings",            "settings"),
        ("Activity Log",        "activity_log"),
    ]

    for i, (label, key) in enumerate(actions):
        btn = primary_button(
            actions_frame, label,
            command=(lambda k=key: navigate(k) if navigate else None),
            width=18
        )
        btn.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="ew")

    for c in range(4):
        actions_frame.grid_columnconfigure(c, weight=1)

    # ---- Footer ----
    footer = tk.Frame(parent, bg=COLORS["card"])
    footer.pack(fill="x", padx=20, pady=(10, 15))

    neutral_button(
        footer, "Refresh Stats",
        command=lambda: show_dashboard(parent, navigate, logout),
        width=14
    ).pack(side="left")

    if logout:
        success_button(
            footer, "Logout",
            command=logout,
            width=14
        ).pack(side="right")