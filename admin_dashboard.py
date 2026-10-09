# ============================================================
# admin_dashboard.py
# Presentation-Ready Admin Dashboard for the Library Management System.
# Optimized to fit 1280x720 displays with high-contrast presentation.
# ============================================================

import tkinter as tk
from tkinter import ttk

from db import get_one, get_rows
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_card,
    primary_button, success_button, neutral_button, danger_button,
    load_photo, populate_tree_with_striping, configure_styles
)


def _count(sql, params=()):
    row = get_one(sql, params)
    return row[0] if row else 0


def show_dashboard(parent, navigate=None, logout=None):
    for widget in parent.winfo_children():
        widget.destroy()

    container = tk.Frame(parent, bg=COLORS["card"])
    container.pack(fill="both", expand=True)

    # ============================================================
    # 1. INSTITUTION & PROJECT HERO BANNER (LIGHT AESTHETIC HOOK STYLE: 80px)
    # ============================================================
    hero = tk.Frame(container, bg=COLORS["card"], height=80,
                    highlightbackground=COLORS["border"], highlightthickness=1)
    hero.pack(fill="x", padx=PAD["section_x"], pady=(8, 4))
    hero.pack_propagate(False)

    # Aesthetic vertical Hook Bar on the left
    hook = tk.Frame(hero, bg=COLORS["primary"], width=5)
    hook.pack(side="left", fill="y")

    hero_inner = tk.Frame(hero, bg=COLORS["card"])
    hero_inner.pack(side="left", fill="both", expand=True, padx=12, pady=6)

    # Campus photo thumbnail
    photo_box = tk.Frame(
        hero_inner,
        bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    photo_box.pack(side="left", padx=(0, 14))

    img = None
    try:
        top_win = hero_inner.winfo_toplevel()
        img = load_photo(size=(110, 64), variant="small", master=top_win)
    except Exception:
        img = None

    if img:
        photo_lbl = tk.Label(photo_box, image=img, bg=COLORS["card"], bd=0)
        photo_lbl.image = img
        photo_lbl.pack()
    else:
        badge_box = tk.Frame(photo_box, bg=COLORS["primary_subtle"], width=100, height=60)
        badge_box.pack_propagate(False)
        badge_box.pack()
        tk.Label(badge_box, text="🏛️ RNS", font=FONTS["h3"],
                 bg=COLORS["primary_subtle"], fg=COLORS["primary"]).pack(expand=True)

    # Details
    info_box = tk.Frame(hero_inner, bg=COLORS["card"])
    info_box.pack(side="left", fill="both", expand=True)

    tk.Label(
        info_box,
        text="LIBRARY MANAGEMENT SYSTEM",
        font=("Segoe UI", 13, "bold"),
        bg=COLORS["card"],
        fg=COLORS["text"],
        anchor="w"
    ).pack(anchor="w")

    tk.Label(
        info_box,
        text="R. N. S. Rural Polytechnic  |  Dept. of Computer Science & Engineering",
        font=FONTS["small"],
        bg=COLORS["card"],
        fg=COLORS["text_secondary"],
        anchor="w"
    ).pack(anchor="w")

    meta_row = tk.Frame(info_box, bg=COLORS["card"])
    meta_row.pack(anchor="w", pady=(3, 0))

    dsp_badge = tk.Frame(meta_row, bg=COLORS["info_light"], padx=8, pady=1)
    dsp_badge.pack(side="left", padx=(0, 8))
    tk.Label(
        dsp_badge,
        text="📘 DSP Mini Project",
        font=FONTS["caption"],
        bg=COLORS["info_light"],
        fg=COLORS["info"]
    ).pack()

    dev_badge = tk.Frame(meta_row, bg=COLORS["accent_light"], padx=8, pady=1)
    dev_badge.pack(side="left")
    tk.Label(
        dev_badge,
        text="👨‍💻 Developer: Varadan Vinod Shanbhag",
        font=FONTS["caption"],
        bg=COLORS["accent_light"],
        fg=COLORS["accent"]
    ).pack()

    # ============================================================
    # 2. KEY PERFORMANCE INDICATORS (KPIs)
    # ============================================================
    section_title(container, "System Overview", "Key operational metrics at a glance")

    stats_row = tk.Frame(container, bg=COLORS["card"])
    stats_row.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    total_books   = _count("SELECT COUNT(*) FROM books")
    total_members = _count("SELECT COUNT(*) FROM members")
    issued_now    = _count("SELECT COUNT(*) FROM issue_return WHERE status = 'ISSUED'")
    overdue_now   = _count(
        "SELECT COUNT(*) FROM issue_return "
        "WHERE status = 'ISSUED' AND due_date IS NOT NULL AND date(due_date) < date('now')"
    )
    unpaid_fines  = _count("SELECT COUNT(*) FROM fines WHERE status = 'UNPAID'")
    pending_ext   = _count("SELECT COUNT(*) FROM extension_requests WHERE status = 'PENDING'")

    kpi_cards = [
        ("Total Books",        total_books,   COLORS["primary"]),
        ("Students & Members", total_members, COLORS["success"]),
        ("Books on Loan",      issued_now,    COLORS["info"]),
        ("Overdue Loans",      overdue_now,   COLORS["danger"]),
        ("Unpaid Fines",       unpaid_fines,  COLORS["warning"]),
        ("Pending Ext.",       pending_ext,   COLORS["primary_light"]),
    ]

    for i, (title, val, col) in enumerate(kpi_cards):
        card = make_card(stats_row, title, val, color=col, width=145, height=68)
        card.grid(row=0, column=i, padx=3, pady=2, sticky="nsew")
        stats_row.grid_columnconfigure(i, weight=1)

    # ============================================================
    # 3. SPLIT SECTION: QUICK ACTIONS (LEFT) + RECENT ACTIVITY (RIGHT)
    # ============================================================
    split_container = tk.Frame(container, bg=COLORS["card"])
    split_container.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 6))

    # ---- Left column: Quick Actions ----
    left_col = tk.Frame(split_container, bg=COLORS["card"])
    left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(
        left_col, text="QUICK NAVIGATION",
        font=FONTS["small_b"], bg=COLORS["card"], fg=COLORS["text_muted"]
    ).pack(anchor="w", pady=(0, 4))

    actions_grid = tk.Frame(left_col, bg=COLORS["card"])
    actions_grid.pack(fill="x")

    quick_modules = [
        ("📚  Book Inventory",      "books"),
        ("👥  Students & Members",  "members"),
        ("🔁  Issue & Return",      "issue"),
        ("🔍  Search & Sort (DSA)", "search"),
        ("👤  Student Accounts",    "member_accounts"),
        ("💰  Fine Management",     "fines"),
        ("📩  Renewal Requests",    "extensions"),
        ("📊  Statistical Reports", "reports"),
        ("📖  Periodicals / Mags",  "magazines"),
        ("📰  Daily Newspapers",    "newspapers"),
        ("⚙️   System Settings",     "settings"),
        ("🗒️   Audit Activity Log",  "activity_log"),
    ]

    for idx, (label, key) in enumerate(quick_modules):
        btn = tk.Button(
            actions_grid,
            text=label,
            command=(lambda k=key: navigate(k) if navigate else None),
            bg=COLORS["card_alt"],
            fg=COLORS["text"],
            font=FONTS["small_b"],
            activebackground=COLORS["primary_subtle"],
            activeforeground=COLORS["primary"],
            relief="flat",
            anchor="w",
            padx=10,
            pady=5,
            cursor="hand2",
            bd=0,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["primary_subtle"], fg=COLORS["primary"]))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["card_alt"], fg=COLORS["text"]))
        btn.grid(row=idx // 2, column=idx % 2, padx=3, pady=3, sticky="ew")

    actions_grid.grid_columnconfigure(0, weight=1)
    actions_grid.grid_columnconfigure(1, weight=1)

    # ---- Right column: Live Activity Snapshot ----
    right_col = tk.Frame(split_container, bg=COLORS["card"])
    right_col.pack(side="right", fill="both", expand=True)

    tk.Label(
        right_col, text="RECENT SYSTEM ACTIVITY",
        font=FONTS["small_b"], bg=COLORS["card"], fg=COLORS["text_muted"]
    ).pack(anchor="w", pady=(0, 4))

    activity_table_frame = tk.Frame(right_col, bg=COLORS["card"],
                                    highlightbackground=COLORS["border"],
                                    highlightthickness=1)
    activity_table_frame.pack(fill="both", expand=True)

    tree_cols = ("time", "action", "details")
    tree = ttk.Treeview(activity_table_frame, columns=tree_cols, show="headings", height=7)
    tree.heading("time", text="Timestamp")
    tree.heading("action", text="Action")
    tree.heading("details", text="Event Details")

    tree.column("time", width=110, anchor="w")
    tree.column("action", width=100, anchor="w")
    tree.column("details", width=200, anchor="w")

    configure_styles()
    tree.tag_configure("even", background=COLORS["card"])
    tree.tag_configure("odd",  background=COLORS["card_alt"])

    vsb = ttk.Scrollbar(activity_table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    recent_logs = get_rows("""
        SELECT timestamp, action, details
        FROM activity_logs
        ORDER BY log_id DESC LIMIT 8
    """)
    for idx, r in enumerate(recent_logs):
        tag = "odd" if idx % 2 == 1 else "even"
        ts = r[0] if r[0] else "-"
        action = r[1] if r[1] else "-"
        det = r[2] if r[2] else "-"
        tree.insert("", tk.END, values=(ts, action, det), tags=(tag,))

    # ============================================================
    # 4. ACTION TOOLBAR & FOOTER (VISIBLE WITHOUT SCROLLING)
    # ============================================================
    footer = tk.Frame(container, bg=COLORS["card"])
    footer.pack(fill="x", padx=PAD["section_x"], pady=(6, 8))

    neutral_button(
        footer, "🔄  Refresh Dashboard",
        command=lambda: show_dashboard(parent, navigate, logout),
        width=18
    ).pack(side="left")

    status_note = tk.Label(
        footer,
        text="Status: Online  •  SQLite Database Connected",
        font=FONTS["caption"],
        bg=COLORS["card"],
        fg=COLORS["success"]
    )
    status_note.pack(side="left", padx=12)

    if logout:
        danger_button(
            footer, "🚪  Logout",
            command=logout,
            width=12
        ).pack(side="right")