# ============================================================
# member_dashboard.py
# Member's personal dashboard: profile, books, fines, extensions, links.
# Members can only see their OWN data.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
from datetime import datetime, date

from db import get_rows, get_one, run_query
from ui_helpers import COLORS, FONTS, section_title, make_card
from activity_log import log_action


# ------------------------------------------------------------
# Read a setting value (used for links + limits)
# ------------------------------------------------------------
def get_setting(key, default=""):
    row = get_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row[0] if row and row[0] else default


# ------------------------------------------------------------
# Open URL in default browser
# ------------------------------------------------------------
def open_url(url):
    if not url:
        messagebox.showinfo("Info", "No link configured. Please contact the librarian.")
        return
    try:
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open link:\n{e}")


# ------------------------------------------------------------
# MAIN MEMBER WINDOW
# ------------------------------------------------------------
def show_member_window(member_id, member_name, on_logout=None):
    win = tk.Tk()
    win.title(f"Member Dashboard - {member_name}")
    win.geometry("1100x680")
    win.configure(bg=COLORS["bg"])

    # ---- Header ----
    header = tk.Frame(win, bg=COLORS["success"], height=60)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header, text="MEMBER DASHBOARD",
        font=("Segoe UI", 16, "bold"),
        bg=COLORS["success"], fg="white"
    ).pack(side="left", padx=20)

    tk.Label(
        header, text=f"Welcome, {member_name}  (Member ID: {member_id})",
        font=FONTS["body"], bg=COLORS["success"], fg="#e8f5f3"
    ).pack(side="right", padx=20)

    # ---- Sidebar + content ----
    body = tk.Frame(win, bg=COLORS["bg"])
    body.pack(fill="both", expand=True)

    sidebar = tk.Frame(body, bg="#1e7d72", width=200)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    content = tk.Frame(body, bg=COLORS["card"])
    content.pack(side="left", fill="both", expand=True)

    def clear_content():
        for w in content.winfo_children():
            w.destroy()

    def do_logout():
        if messagebox.askyesno("Logout", "Do you want to logout?"):
            log_action("MEMBER", member_id, "LOGOUT", f"Member '{member_name}' logged out")
            win.destroy()
            if on_logout:
                on_logout()

    # ---- Sidebar buttons ----
    def sidebar_btn(text, command):
        return tk.Button(
            sidebar, text=text, command=command,
            bg="#1e7d72", fg="white",
            font=FONTS["body"], activebackground=COLORS["success"],
            activeforeground="white", relief="flat",
            anchor="w", padx=18, pady=10, cursor="hand2"
        )

    sidebar_btn("🏠  Overview",       lambda: show_overview()).pack(fill="x")
    sidebar_btn("📚  My Books",       lambda: show_my_books()).pack(fill="x")
    sidebar_btn("📜  History",        lambda: show_history()).pack(fill="x")
    sidebar_btn("💰  My Fines",       lambda: show_fines()).pack(fill="x")
    sidebar_btn("📩  Extensions",     lambda: show_extensions()).pack(fill="x")
    sidebar_btn("🔗  Latest News",    lambda: open_url(get_setting("news_link"))).pack(fill="x")
    sidebar_btn("🎓  College Portal", lambda: open_url(get_setting("college_portal"))).pack(fill="x")

    tk.Frame(sidebar, bg="#1e7d72", height=20).pack(fill="x")

    tk.Button(
        sidebar, text="🚪  Logout", command=do_logout,
        bg=COLORS["danger"], fg="white", font=FONTS["body_b"],
        relief="flat", anchor="w", padx=18, pady=10, cursor="hand2"
    ).pack(fill="x", side="bottom")

    # ============================================================
    # SCREEN 1: OVERVIEW
    # ============================================================
    def show_overview():
        clear_content()
        section_title(content, f"Welcome, {member_name}", "Your library at a glance")

        # Stats
        stats = tk.Frame(content, bg=COLORS["card"])
        stats.pack(fill="x", padx=20, pady=(5, 15))

        currently_issued = get_one(
            "SELECT COUNT(*) FROM issue_return WHERE member_id = ? AND status = 'ISSUED'",
            (member_id,)
        )[0]

        overdue = get_one(
            "SELECT COUNT(*) FROM issue_return "
            "WHERE member_id = ? AND status = 'ISSUED' "
            "AND due_date IS NOT NULL AND due_date < date('now')",
            (member_id,)
        )[0]

        unpaid = get_one(
            "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM fines "
            "WHERE member_id = ? AND status = 'UNPAID'",
            (member_id,)
        )
        unpaid_count, unpaid_total = unpaid[0], unpaid[1]

        pending_ext = get_one(
            "SELECT COUNT(*) FROM extension_requests "
            "WHERE member_id = ? AND status = 'PENDING'",
            (member_id,)
        )[0]

        cards = [
            ("Books Issued",    currently_issued, COLORS["primary"]),
            ("Overdue",         overdue,          COLORS["danger"]),
            ("Unpaid Fines",    f"₹{unpaid_total:.2f}", COLORS["warning"]),
            ("Pending Ext.",    pending_ext,      COLORS["accent"]),
        ]
        for i, (t, v, c) in enumerate(cards):
            make_card(stats, t, v, color=c).grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
            stats.grid_columnconfigure(i, weight=1)

        # Profile card
        section_title(content, "My Profile", "Your registered details")
        profile_frame = tk.Frame(content, bg=COLORS["card"])
        profile_frame.pack(fill="x", padx=20, pady=(0, 15))

        mem = get_one(
            "SELECT name, phone, email FROM members WHERE member_id = ?",
            (member_id,)
        )
        if mem:
            rows = [
                ("Name",  mem[0]),
                ("Phone", mem[1] or "-"),
                ("Email", mem[2] or "-"),
            ]
            for i, (k, v) in enumerate(rows):
                tk.Label(profile_frame, text=f"{k}:", font=FONTS["body_b"],
                         bg=COLORS["card"], fg=COLORS["text_muted"]
                         ).grid(row=i, column=0, sticky="w", padx=(0, 15), pady=3)
                tk.Label(profile_frame, text=str(v), font=FONTS["body"],
                         bg=COLORS["card"], fg=COLORS["text"]
                         ).grid(row=i, column=1, sticky="w", pady=3)

        # Quick links
        section_title(content, "Quick Links", "Useful external resources")
        links = tk.Frame(content, bg=COLORS["card"])
        links.pack(fill="x", padx=20, pady=(0, 15))

        tk.Button(
            links, text="📰  Latest News", width=20,
            bg=COLORS["primary"], fg="white", font=FONTS["body_b"],
            relief="flat", cursor="hand2",
            command=lambda: open_url(get_setting("news_link"))
        ).grid(row=0, column=0, padx=6, pady=6)

        tk.Button(
            links, text="🎓  College Portal", width=20,
            bg=COLORS["success"], fg="white", font=FONTS["body_b"],
            relief="flat", cursor="hand2",
            command=lambda: open_url(get_setting("college_portal"))
        ).grid(row=0, column=1, padx=6, pady=6)

    # ============================================================
    # SCREEN 2: MY BOOKS (currently issued)
    # ============================================================
    def show_my_books():
        clear_content()
        section_title(content, "My Books", "Books currently issued to you")

        btn_row = tk.Frame(content, bg=COLORS["card"])
        btn_row.pack(side="bottom", pady=(5, 12))

        table_frame = tk.Frame(content, bg=COLORS["card"])
        table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        cols = ("issue_id", "title", "author", "issue_date", "due_date", "status")
        heads = ("Issue ID", "Title", "Author", "Issued On", "Due On", "Status")
        widths = (80, 240, 170, 110, 110, 110)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

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

            for r in rows:
                issue_id, title, author, issue_date, due_date, status = r
                due_display = due_date or "-"
                status_display = status
                if due_date:
                    try:
                        d = datetime.strptime(due_date, "%Y-%m-%d").date()
                        if d < date.today():
                            status_display = "OVERDUE"
                    except Exception:
                        pass
                tree.insert("", tk.END, values=(
                    issue_id, title, author, issue_date, due_display, status_display
                ))

        # Request Extension button
        def request_extension():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a book first.")
                return
            values = tree.item(sel[0])["values"]
            issue_id = values[0]
            title = values[1]

            days = simpledialog.askinteger(
                "Request Extension",
                f"Book: {title}\n\nHow many extra days do you need?",
                minvalue=1, maxvalue=30, parent=content
            )
            if not days:
                return

            reason = simpledialog.askstring(
                "Reason (optional)",
                "Why do you need the extension?",
                parent=content
            )

            # Check max extensions per book
            max_ext = int(get_setting("max_extensions_per_book", "1"))
            current_ext = get_one(
                "SELECT extension_count FROM issue_return WHERE issue_id = ?",
                (issue_id,)
            )
            current_ext = current_ext[0] if current_ext else 0
            if current_ext >= max_ext:
                messagebox.showerror(
                    "Limit Reached",
                    f"You have already used the maximum of {max_ext} extension(s) for this book."
                )
                return

            # Check no pending request for this issue
            existing = get_one(
                "SELECT request_id FROM extension_requests "
                "WHERE issue_id = ? AND status = 'PENDING'",
                (issue_id,)
            )
            if existing:
                messagebox.showinfo("Info", "You already have a pending request for this book.")
                return

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            run_query(
                "INSERT INTO extension_requests "
                "(issue_id, member_id, requested_days, reason, status, requested_on) "
                "VALUES (?, ?, ?, ?, 'PENDING', ?)",
                (issue_id, member_id, days, reason or "", now)
            )
            log_action("MEMBER", member_id, "EXTENSION_REQUESTED",
                       f"Issue #{issue_id}, days={days}")
            messagebox.showinfo("Success", "Extension request sent to the librarian.")

        ttk.Button(btn_row, text="Request Extension",
                   command=request_extension).grid(row=0, column=0, padx=5)
        ttk.Button(btn_row, text="Refresh",
                   command=refresh).grid(row=0, column=1, padx=5)

        refresh()

    # ============================================================
    # SCREEN 3: HISTORY
    # ============================================================
    def show_history():
        clear_content()
        section_title(content, "Borrowing History", "All books you have borrowed")

        table_frame = tk.Frame(content, bg=COLORS["card"])
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("issue_id", "title", "issue_date", "due_date", "return_date", "status")
        heads = ("Issue ID", "Title", "Issued On", "Due On", "Returned On", "Status")
        widths = (80, 240, 110, 110, 110, 110)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

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

        for r in rows:
            issue_id, title, issue_date, due_date, ret_date, status = r
            tree.insert("", tk.END, values=(
                issue_id, title, issue_date or "-",
                due_date or "-", ret_date or "-", status
            ))

    # ============================================================
    # SCREEN 4: MY FINES
    # ============================================================
    def show_fines():
        clear_content()
        section_title(content, "My Fines", "Fines from overdue returns")

        # Summary
        summary = get_one(
            "SELECT "
            "COALESCE(SUM(CASE WHEN status='UNPAID' THEN amount ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN status='PAID'   THEN amount ELSE 0 END), 0) "
            "FROM fines WHERE member_id = ?",
            (member_id,)
        )
        unpaid_total = summary[0] if summary else 0
        paid_total   = summary[1] if summary else 0

        sum_frame = tk.Frame(content, bg=COLORS["card"])
        sum_frame.pack(fill="x", padx=20, pady=(5, 10))

        make_card(sum_frame, "Unpaid", f"₹{unpaid_total:.2f}",
                  color=COLORS["danger"]).grid(row=0, column=0, padx=6, pady=6)
        make_card(sum_frame, "Paid", f"₹{paid_total:.2f}",
                  color=COLORS["success"]).grid(row=0, column=1, padx=6, pady=6)

        # Table
        table_frame = tk.Frame(content, bg=COLORS["card"])
        table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        cols = ("fine_id", "book", "amount", "status", "generated", "paid")
        heads = ("Fine ID", "Book", "Amount (₹)", "Status", "Generated On", "Paid On")
        widths = (80, 240, 100, 100, 130, 130)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        rows = get_rows("""
            SELECT f.fine_id, b.title, f.amount, f.status,
                   f.generated_on, f.paid_on
            FROM fines f
            JOIN issue_return ir ON f.issue_id = ir.issue_id
            JOIN books b ON ir.book_id = b.book_id
            WHERE f.member_id = ?
            ORDER BY f.fine_id DESC
        """, (member_id,))

        for r in rows:
            fine_id, title, amt, st, gen, paid = r
            tree.insert("", tk.END, values=(
                fine_id, title, f"{amt:.2f}", st, gen or "-", paid or "-"
            ))

    # ============================================================
    # SCREEN 5: EXTENSIONS
    # ============================================================
    def show_extensions():
        clear_content()
        section_title(content, "My Extension Requests", "Status of your renewal requests")

        table_frame = tk.Frame(content, bg=COLORS["card"])
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("request_id", "book", "days", "status", "requested", "decided")
        heads = ("ID", "Book", "Days", "Status", "Requested On", "Decided On")
        widths = (60, 240, 60, 110, 130, 130)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="w")

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

        for r in rows:
            rid, title, days, st, req, dec = r
            tree.insert("", tk.END, values=(
                rid, title, days, st, req or "-", dec or "-"
            ))

    # ---- Show overview first ----
    show_overview()
    win.mainloop()