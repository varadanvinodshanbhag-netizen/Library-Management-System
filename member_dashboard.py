# ============================================================
# member_dashboard.py
# Student & Member Self-Service Portal.
# Optimized to fit 1280x720 presentation displays.
# Action buttons placed directly adjacent to controls for immediate visibility.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
from datetime import datetime, date

from db import get_rows, get_one, run_query
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_card, load_photo, center_window,
    primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, configure_styles, show_success, show_error, show_warning
)
from activity_log import log_action


def get_setting(key, default=""):
    row = get_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row[0] if row and row[0] else default


def open_url(url):
    if not url:
        messagebox.showinfo("Information", "No link configured. Please contact the librarian.")
        return
    try:
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror("Error", f"Could not launch browser:\n{e}")


# ============================================================
# MAIN MEMBER PORTAL WINDOW
# ============================================================
def show_member_window(member_id, member_name, on_logout=None):
    mem_info = get_one("SELECT card_id, dept, member_type FROM members WHERE member_id = ?", (member_id,))
    card_id = mem_info[0] if mem_info and mem_info[0] else f"M{member_id}"
    dept = mem_info[1] if mem_info and mem_info[1] else "CSE"
    member_type = mem_info[2] if mem_info and mem_info[2] else "STUDENT"

    win = tk.Tk()
    win.title(f"Library Member Portal - {member_name} ({card_id})")
    win.geometry("1150x640")
    center_window(win, 1150, 640)
    win.configure(bg=COLORS["bg"])
    win.minsize(1050, 580)

    configure_styles()

    # ---- Top Navigation Bar ----
    navbar = tk.Frame(win, bg="#ffffff", height=48, highlightbackground=COLORS["border"], highlightthickness=1)
    navbar.pack(fill="x")
    navbar.pack_propagate(False)

    brand_box = tk.Frame(navbar, bg="#ffffff")
    brand_box.pack(side="left", padx=16)

    tk.Label(
        brand_box,
        text="🎓  STUDENT & MEMBER PORTAL",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        fg=COLORS["success"]
    ).pack(side="left")

    tk.Label(
        brand_box,
        text=" |  RNS Rural Polytechnic",
        font=FONTS["small"],
        bg="#ffffff",
        fg=COLORS["text_muted"]
    ).pack(side="left")

    user_pill = tk.Frame(
        navbar, bg=COLORS["success_light"],
        highlightbackground="#a7f3d0",
        highlightthickness=1
    )
    user_pill.pack(side="right", padx=16, pady=7)

    tk.Label(
        user_pill,
        text=f"  👤 {member_name}  |  Card: {card_id}  |  Dept: {dept}  ",
        font=FONTS["small_b"],
        bg=COLORS["success_light"],
        fg="#065f46",
        pady=2
    ).pack()

    # ---- Body Layout ----
    body = tk.Frame(win, bg=COLORS["bg"])
    body.pack(fill="both", expand=True)

    sidebar = tk.Frame(body, bg=COLORS["sidebar_member"], width=204,
                       highlightbackground=COLORS["sidebar_member_border"], highlightthickness=1)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    sb_header = tk.Frame(sidebar, bg=COLORS["card_alt"], height=32)
    sb_header.pack(fill="x")
    sb_header.pack_propagate(False)
    tk.Label(
        sb_header, text="STUDENT SERVICES",
        font=FONTS["caption"],
        bg=COLORS["card_alt"],
        fg=COLORS["text_muted"]
    ).pack(expand=True)

    content = tk.Frame(body, bg=COLORS["card"])
    content.pack(side="left", fill="both", expand=True)

    def clear_content():
        for w in content.winfo_children():
            w.destroy()

    def do_logout():
        if messagebox.askyesno("Confirm Sign Out", "Are you sure you want to sign out of your account?"):
            log_action("MEMBER", member_id, "LOGOUT", f"Member '{member_name}' signed out")
            win.destroy()
            if on_logout:
                on_logout()

    nav_buttons = []

    def add_member_nav(text, command, key):
        row = tk.Frame(sidebar, bg=COLORS["sidebar_member"], height=34)
        row.pack(fill="x")
        row.pack_propagate(False)

        # 4px vertical Hook Indicator
        hook = tk.Frame(row, bg=COLORS["sidebar_member"], width=4)
        hook.pack(side="left", fill="y")

        btn = tk.Button(
            row,
            text=text,
            command=command,
            bg=COLORS["sidebar_member"],
            fg=COLORS["sidebar_member_text"],
            font=FONTS["nav"],
            activebackground=COLORS["sidebar_member_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            anchor="w",
            padx=12,
            pady=4,
            cursor="hand2",
            bd=0,
            highlightthickness=0,
        )
        btn.pack(side="left", fill="both", expand=True)

        def on_enter(e):
            if btn.cget("bg") != COLORS["sidebar_member_active_bg"]:
                btn.config(bg=COLORS["sidebar_member_hover"], fg=COLORS["text"])

        def on_leave(e):
            if btn.cget("bg") != COLORS["sidebar_member_active_bg"]:
                btn.config(bg=COLORS["sidebar_member"], fg=COLORS["sidebar_member_text"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        nav_buttons.append((btn, hook, key))
        return btn

    def set_active_nav(key):
        for b_ref, hook_ref, b_key in nav_buttons:
            if b_key == key:
                hook_ref.config(bg=COLORS["sidebar_member_active_hook"])
                b_ref.config(bg=COLORS["sidebar_member_active_bg"], fg=COLORS["sidebar_member_active_fg"], font=FONTS["nav_b"])
            else:
                hook_ref.config(bg=COLORS["sidebar_member"])
                b_ref.config(bg=COLORS["sidebar_member"], fg=COLORS["sidebar_member_text"], font=FONTS["nav"])

    add_member_nav("🏠   Overview",       lambda: (set_active_nav("overview"), show_overview()), "overview")
    add_member_nav("📚   My Active Loans", lambda: (set_active_nav("books"),    show_my_books()), "books")
    add_member_nav("📜   Borrow History",  lambda: (set_active_nav("history"),  show_history()),  "history")
    add_member_nav("💰   My Fine Dues",    lambda: (set_active_nav("fines"),    show_fines()),    "fines")
    add_member_nav("📩   Renewal Status",  lambda: (set_active_nav("ext"),      show_extensions()), "ext")
    add_member_nav("📰   Campus News",     lambda: open_url(get_setting("news_link")), "news")
    add_member_nav("🏛️   College Portal",  lambda: open_url(get_setting("college_portal")), "portal")

    tk.Frame(sidebar, bg=COLORS["sidebar_member"]).pack(fill="both", expand=True)

    logout_frame = tk.Frame(sidebar, bg=COLORS["sidebar_member"])
    logout_frame.pack(fill="x", side="bottom", padx=8, pady=8)

    logout_btn = tk.Button(
        logout_frame,
        text="🚪   Sign Out",
        command=do_logout,
        bg=COLORS["danger_light"],
        fg=COLORS["danger"],
        font=FONTS["body_b"],
        relief="flat",
        anchor="center",
        pady=6,
        cursor="hand2",
        bd=0,
        highlightthickness=0,
    )
    logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg=COLORS["danger"], fg="white"))
    logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg=COLORS["danger_light"], fg=COLORS["danger"]))
    logout_btn.pack(fill="x")

    # ============================================================
    # SCREEN 1: OVERVIEW
    # ============================================================
    def show_overview():
        clear_content()

        # Hero Banner with Campus Photo (LIGHT AESTHETIC HOOK STYLE: 80px)
        hero = tk.Frame(content, bg=COLORS["card"], height=80,
                        highlightbackground=COLORS["border"], highlightthickness=1)
        hero.pack(fill="x", padx=PAD["section_x"], pady=(8, 4))
        hero.pack_propagate(False)

        # 5px vertical Hook Bar
        hook = tk.Frame(hero, bg=COLORS["success"], width=5)
        hook.pack(side="left", fill="y")

        hero_inner = tk.Frame(hero, bg=COLORS["card"])
        hero_inner.pack(side="left", fill="both", expand=True, padx=12, pady=6)

        photo_box = tk.Frame(hero_inner, bg=COLORS["card"], highlightbackground=COLORS["border"], highlightthickness=1)
        photo_box.pack(side="left", padx=(0, 14))

        img = None
        try:
            top_win = hero_inner.winfo_toplevel()
            img = load_photo(size=(110, 62), variant="small", master=top_win)
        except Exception:
            img = None

        if img:
            photo_lbl = tk.Label(photo_box, image=img, bg=COLORS["card"], bd=0)
            photo_lbl.image = img
            photo_lbl.pack()

        info_box = tk.Frame(hero_inner, bg=COLORS["card"])
        info_box.pack(side="left", fill="both", expand=True)

        tk.Label(
            info_box,
            text=f"Welcome, {member_name}!",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(anchor="w")

        tk.Label(
            info_box,
            text=f"Library Card ID: {card_id}  •  Dept: {dept} ({member_type})  •  R. N. S. Rural Polytechnic",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg="#047857",
            anchor="w"
        ).pack(anchor="w", pady=(1, 0))

        # KPI Metrics Cards
        section_title(content, "Borrowing Status", "Your current borrowing and fee status")

        stats_row = tk.Frame(content, bg=COLORS["card"])
        stats_row.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

        currently_issued = get_one(
            "SELECT COUNT(*) FROM issue_return WHERE member_id = ? AND status = 'ISSUED'",
            (member_id,)
        )[0]

        overdue_cnt = get_one(
            "SELECT COUNT(*) FROM issue_return "
            "WHERE member_id = ? AND status = 'ISSUED' AND due_date IS NOT NULL AND date(due_date) < date('now')",
            (member_id,)
        )[0]

        unpaid = get_one(
            "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM fines WHERE member_id = ? AND status = 'UNPAID'",
            (member_id,)
        )
        unpaid_total = unpaid[1] or 0

        pending_ext = get_one(
            "SELECT COUNT(*) FROM extension_requests WHERE member_id = ? AND status = 'PENDING'",
            (member_id,)
        )[0]

        member_cards = [
            ("Books on Loan",    currently_issued,       COLORS["primary"]),
            ("Overdue Books",    overdue_cnt,            COLORS["danger"]),
            ("Unpaid Fines",     f"Rs {unpaid_total:.2f}", COLORS["warning"]),
            ("Pending Renewals", pending_ext,            COLORS["accent"]),
        ]

        for i, (title, val, col) in enumerate(member_cards):
            card = make_card(stats_row, title, val, color=col, width=160, height=66)
            card.grid(row=0, column=i, padx=3, pady=2, sticky="nsew")
            stats_row.grid_columnconfigure(i, weight=1)

        # Split Container: Profile & Quick Links
        bottom_container = tk.Frame(content, bg=COLORS["card"])
        bottom_container.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 6))

        # Profile Card
        profile_col = tk.Frame(bottom_container, bg=COLORS["card"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        profile_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        p_header = tk.Frame(profile_col, bg=COLORS["card_alt"], height=30)
        p_header.pack(fill="x")
        p_header.pack_propagate(False)
        tk.Label(p_header, text="  👤  STUDENT & MEMBER PROFILE",
                 font=FONTS["small_b"], bg=COLORS["card_alt"], fg=COLORS["text"]).pack(side="left", padx=8)

        p_body = tk.Frame(profile_col, bg=COLORS["card"])
        p_body.pack(fill="both", expand=True, padx=12, pady=8)

        mem = get_one("SELECT name, phone, email, card_id, dept, member_type FROM members WHERE member_id = ?", (member_id,))
        if mem:
            fields = [
                ("Student / Member ID", f"#{member_id}"),
                ("Library Card ID", mem[3] or card_id),
                ("Department", mem[4] or dept),
                ("Member Category", mem[5] or member_type),
                ("Full Name", mem[0]),
                ("Phone", mem[1] or "None"),
                ("Email", mem[2] or "None"),
            ]
            for r_idx, (k, v) in enumerate(fields):
                tk.Label(p_body, text=f"{k}:", font=FONTS["small_b"],
                         bg=COLORS["card"], fg=COLORS["text_muted"]).grid(row=r_idx, column=0, sticky="w", pady=2, padx=(0, 12))
                tk.Label(p_body, text=str(v), font=FONTS["body"],
                         bg=COLORS["card"], fg=COLORS["text"]).grid(row=r_idx, column=1, sticky="w", pady=2)

        # Quick Links Card
        links_col = tk.Frame(bottom_container, bg=COLORS["card"],
                             highlightbackground=COLORS["border"], highlightthickness=1)
        links_col.pack(side="right", fill="both", expand=True)

        l_header = tk.Frame(links_col, bg=COLORS["card_alt"], height=30)
        l_header.pack(fill="x")
        l_header.pack_propagate(False)
        tk.Label(l_header, text="  🔗  QUICK CAMPUS LAUNCHPAD",
                 font=FONTS["small_b"], bg=COLORS["card_alt"], fg=COLORS["text"]).pack(side="left", padx=8)

        l_body = tk.Frame(links_col, bg=COLORS["card"])
        l_body.pack(fill="both", expand=True, padx=12, pady=8)

        tk.Label(
            l_body,
            text="Access RNS Rural Polytechnic portal updates and campus announcements directly:",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            wraplength=300,
            justify="left"
        ).pack(anchor="w", pady=(0, 6))

        primary_button(
            l_body, "📰  Campus News",
            command=lambda: open_url(get_setting("news_link")),
            width=20
        ).pack(anchor="w", pady=3)

        success_button(
            l_body, "🏛️  College Portal",
            command=lambda: open_url(get_setting("college_portal")),
            width=20
        ).pack(anchor="w", pady=3)

    # ============================================================
    # SCREEN 2: MY BOOKS (ACTIVE LOANS)
    # ============================================================
    def show_my_books():
        clear_content()
        section_title(
            content,
            "My Active Book Loans",
            "Books currently checked out in your custody. You may submit renewal requests for eligible loans."
        )

        # Action Toolbar (PACKED BEFORE TABLE FOR IMMEDIATE ACCESS)
        toolbar = tk.Frame(content, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
        toolbar.pack(fill="x", padx=PAD["section_x"], pady=(0, 6), ipady=3)

        success_button(toolbar, "📩 Request Renewal", lambda: request_extension(), width=16).pack(side="left", padx=6)
        neutral_button(toolbar, "🔄 Refresh Table",   lambda: refresh(),           width=14).pack(side="left", padx=6)

        table_frame = tk.Frame(content, bg=COLORS["card"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 8))

        cols = ("issue_id", "title", "author", "issue_date", "due_date", "status")
        heads = ("Loan ID", "Book Title", "Author", "Borrowed On", "Due Date", "Loan Status")
        widths = (70, 260, 200, 110, 110, 110)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

        configure_styles()
        tree.tag_configure("even", background=COLORS["card"])
        tree.tag_configure("odd",  background=COLORS["card_alt"])

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def refresh():
            for i in tree.get_children():
                tree.delete(i)

            rows = get_rows("""
                SELECT ir.issue_id, b.title, a.author_name,
                       ir.issue_date, ir.due_date, ir.status
                FROM issue_return ir
                JOIN books   b ON ir.book_id  = b.book_id
                JOIN authors a ON b.author_id = a.author_id
                WHERE ir.member_id = ? AND ir.status = 'ISSUED'
                ORDER BY ir.issue_id DESC
            """, (member_id,))

            for idx, r in enumerate(rows):
                iid, title, author, iss, due, st = r
                tag = "odd" if idx % 2 == 1 else "even"
                st_display = "🟢 Current"
                if due:
                    try:
                        d = datetime.strptime(due, "%Y-%m-%d").date()
                        if d < date.today():
                            st_display = "🔴 Overdue"
                    except Exception:
                        pass
                tree.insert("", tk.END, values=(f"#{iid}", title, author, iss or "-", due or "-", st_display), tags=(tag,))

        def request_extension():
            sel = tree.selection()
            if not sel:
                show_warning("Selection Required", "Please select a borrowed book from the table first.")
                return

            values = tree.item(sel[0])["values"]
            issue_id = int(str(values[0]).replace("#", ""))
            title = values[1]

            days = simpledialog.askinteger(
                "Request Loan Renewal",
                f"Book: '{title}'\n\nHow many additional days extension do you need?",
                minvalue=1, maxvalue=30, parent=content
            )
            if not days:
                return

            reason = simpledialog.askstring(
                "Extension Justification",
                "Brief reason for renewal request (e.g., project research, exam prep):",
                parent=content
            )

            max_ext = int(get_setting("max_extensions_per_book", "1"))
            cur_ext = get_one("SELECT extension_count FROM issue_return WHERE issue_id = ?", (issue_id,))
            cur_ext = cur_ext[0] if cur_ext else 0
            if cur_ext >= max_ext:
                show_error("Renewal Limit", f"You have already reached the maximum of {max_ext} renewal(s) for this book.")
                return

            existing = get_one(
                "SELECT request_id FROM extension_requests WHERE issue_id = ? AND status = 'PENDING'",
                (issue_id,)
            )
            if existing:
                show_warning("Pending Request", "You already have a pending extension request submitted for this loan.")
                return

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            run_query(
                "INSERT INTO extension_requests (issue_id, member_id, requested_days, reason, status, requested_on) "
                "VALUES (?, ?, ?, ?, 'PENDING', ?)",
                (issue_id, member_id, days, reason or "", now)
            )
            log_action("MEMBER", member_id, "EXTENSION_REQUESTED", f"Loan #{issue_id}, requested {days} days")
            show_success("Request Submitted", "Your extension request was dispatched to the librarian for approval.")

        refresh()

    # ============================================================
    # SCREEN 3: BORROWING HISTORY
    # ============================================================
    def show_history():
        clear_content()
        section_title(
            content,
            "Complete Circulation History",
            "Chronological log of all books borrowed and returned by your account"
        )

        table_frame = tk.Frame(content, bg=COLORS["card"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 8))

        cols = ("issue_id", "title", "issue_date", "due_date", "return_date", "status")
        heads = ("Loan ID", "Book Title", "Borrowed On", "Due Date", "Returned On", "Loan Status")
        widths = (70, 260, 110, 110, 110, 110)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

        configure_styles()
        tree.tag_configure("even", background=COLORS["card"])
        tree.tag_configure("odd",  background=COLORS["card_alt"])

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        rows = get_rows("""
            SELECT ir.issue_id, b.title, ir.issue_date, ir.due_date,
                   COALESCE(ir.actual_return_date, ir.return_date) AS ret_date,
                   ir.status
            FROM issue_return ir
            JOIN books b ON ir.book_id = b.book_id
            WHERE ir.member_id = ?
            ORDER BY ir.issue_id DESC
        """, (member_id,))

        for idx, r in enumerate(rows):
            iid, title, iss, due, ret, st = r
            tag = "odd" if idx % 2 == 1 else "even"
            st_display = "🟢 Returned" if st == "RETURNED" else "🔵 Active Loan"
            tree.insert("", tk.END, values=(f"#{iid}", title, iss or "-", due or "-", ret or "-", st_display), tags=(tag,))

    # ============================================================
    # SCREEN 4: MY FINES
    # ============================================================
    def show_fines():
        clear_content()
        section_title(
            content,
            "My Fine Assessment & Receipts",
            "Record of charges incurred for overdue returns and receipts for settled payments"
        )

        summary = get_one("""
            SELECT
                COALESCE(SUM(CASE WHEN status='UNPAID' THEN amount ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN status='PAID'   THEN amount ELSE 0 END), 0)
            FROM fines WHERE member_id = ?
        """, (member_id,))
        unpaid_amt = summary[0] if summary else 0
        paid_amt   = summary[1] if summary else 0

        sum_row = tk.Frame(content, bg=COLORS["card"])
        sum_row.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

        make_card(sum_row, "Outstanding Dues", f"Rs {unpaid_amt:.2f}",
                  color=COLORS["danger"], height=66).grid(row=0, column=0, padx=3, pady=2)
        make_card(sum_row, "Settled / Paid", f"Rs {paid_amt:.2f}",
                  color=COLORS["success"], height=66).grid(row=0, column=1, padx=3, pady=2)

        table_frame = tk.Frame(content, bg=COLORS["card"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 8))

        cols = ("fine_id", "book", "amount", "status", "generated", "paid")
        heads = ("Fine ID", "Associated Book Title", "Assessed Amount", "Status", "Incurred On", "Payment Date")
        widths = (70, 260, 110, 100, 120, 120)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

        configure_styles()
        tree.tag_configure("even", background=COLORS["card"])
        tree.tag_configure("odd",  background=COLORS["card_alt"])

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        rows = get_rows("""
            SELECT f.fine_id, b.title, f.amount, f.status, f.generated_on, f.paid_on
            FROM fines f
            JOIN issue_return ir ON f.issue_id = ir.issue_id
            JOIN books b ON ir.book_id = b.book_id
            WHERE f.member_id = ?
            ORDER BY f.fine_id DESC
        """, (member_id,))

        for idx, r in enumerate(rows):
            fid, title, amt, st, gen, paid = r
            tag = "odd" if idx % 2 == 1 else "even"
            st_display = "🟢 Paid" if st == "PAID" else ("🔴 Unpaid" if st == "UNPAID" else "⚪ Waived")
            tree.insert("", tk.END, values=(f"#{fid}", title, f"Rs {float(amt):.2f}", st_display, gen or "-", paid or "-"), tags=(tag,))

    # ============================================================
    # SCREEN 5: EXTENSIONS / RENEWALS
    # ============================================================
    def show_extensions():
        clear_content()
        section_title(
            content,
            "My Renewal Requests Status",
            "Track administrative review and decision status for submitted loan extensions"
        )

        table_frame = tk.Frame(content, bg=COLORS["card"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 8))

        cols = ("request_id", "book", "days", "status", "requested", "decided")
        heads = ("Request ID", "Book Title", "Days Requested", "Decision Status", "Submitted On", "Reviewed On")
        widths = (80, 260, 110, 110, 130, 130)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

        configure_styles()
        tree.tag_configure("even", background=COLORS["card"])
        tree.tag_configure("odd",  background=COLORS["card_alt"])

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        rows = get_rows("""
            SELECT er.request_id, b.title, er.requested_days, er.status,
                   er.requested_on, er.decided_on
            FROM extension_requests er
            JOIN issue_return ir ON er.issue_id = ir.issue_id
            JOIN books b ON ir.book_id = b.book_id
            WHERE er.member_id = ?
            ORDER BY er.request_id DESC
        """, (member_id,))

        for idx, r in enumerate(rows):
            rid, title, days, st, req, dec = r
            tag = "odd" if idx % 2 == 1 else "even"
            if st == "APPROVED":
                st_display = "🟢 Approved"
            elif st == "PENDING":
                st_display = "🟡 Pending Review"
            else:
                st_display = "🔴 Rejected"

            tree.insert("", tk.END, values=(f"#{rid}", title, f"{days} days", st_display, req or "-", dec or "-"), tags=(tag,))

    set_active_nav("overview")
    show_overview()
    win.mainloop()