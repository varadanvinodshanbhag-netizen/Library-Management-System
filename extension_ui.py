# ============================================================
# extension_ui.py
# Admin screen: review and decide member extension requests.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date, timedelta

from db import get_rows, get_one, run_query
from activity_log import log_action
from fine_calc import get_setting, parse_date
from ui_helpers import (
    COLORS, FONTS, section_title, make_card,
    primary_button, success_button, danger_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


def show_extensions_screen(parent, admin_id=None):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(parent, "Extension Requests",
                  "Approve or reject member requests to renew books")

    # ---------- Summary ----------
    summary_frame = tk.Frame(parent, bg=COLORS["card"])
    summary_frame.pack(fill="x", padx=20, pady=(5, 10))

    def get_summary():
        pending = get_one(
            "SELECT COUNT(*) FROM extension_requests WHERE status = 'PENDING'"
        )[0]
        approved = get_one(
            "SELECT COUNT(*) FROM extension_requests WHERE status = 'APPROVED'"
        )[0]
        rejected = get_one(
            "SELECT COUNT(*) FROM extension_requests WHERE status = 'REJECTED'"
        )[0]
        return pending, approved, rejected

    def draw_summary():
        for w in summary_frame.winfo_children():
            w.destroy()
        p, a, r = get_summary()
        make_card(summary_frame, "Pending",  p, color=COLORS["warning"]).grid(row=0, column=0, padx=6, pady=6)
        make_card(summary_frame, "Approved", a, color=COLORS["success"]).grid(row=0, column=1, padx=6, pady=6)
        make_card(summary_frame, "Rejected", r, color=COLORS["danger"]).grid(row=0, column=2, padx=6, pady=6)

    # ---------- Filter ----------
    filter_frame = tk.Frame(parent, bg=COLORS["card"])
    filter_frame.pack(fill="x", padx=20, pady=(5, 10))

    tk.Label(filter_frame, text="Status:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=0, padx=(0, 5))
    status_var = tk.StringVar(value="PENDING")
    ttk.Combobox(
        filter_frame, textvariable=status_var, width=12,
        values=["ALL", "PENDING", "APPROVED", "REJECTED"], state="readonly"
    ).grid(row=0, column=1, padx=(0, 15))

    # ---------- Button row (packed BEFORE table) ----------
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 12))

    # ---------- Table ----------
    table_frame = tk.Frame(parent, bg=COLORS["card"])
    table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

    cols = ("req_id", "member", "book", "issue_id",
            "days", "reason", "status", "requested", "decided")
    heads = ("ID", "Member", "Book", "Issue ID",
             "Days", "Reason", "Status", "Requested On", "Decided On")
    widths = (60, 150, 200, 70, 60, 200, 90, 130, 130)

    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
    for c, h, w in zip(cols, heads, widths):
        tree.heading(c, text=h)
        tree.column(c, width=w, anchor="w")

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # ---------- Refresh ----------
    def refresh():
        for i in tree.get_children():
            tree.delete(i)

        sql = """
            SELECT er.request_id, m.name, b.title, er.issue_id,
                   er.requested_days, er.reason, er.status,
                   er.requested_on, er.decided_on
            FROM extension_requests er
            JOIN members m ON er.member_id = m.member_id
            JOIN issue_return ir ON er.issue_id = ir.issue_id
            JOIN books b ON ir.book_id = b.book_id
            WHERE 1=1
        """
        params = []
        if status_var.get() != "ALL":
            sql += " AND er.status = ?"
            params.append(status_var.get())

        sql += " ORDER BY er.request_id DESC"

        for r in get_rows(sql, tuple(params)):
            rid, mem, book, iid, days, reason, st, req, dec = r
            tree.insert("", tk.END, values=(
                rid, mem, book, iid, days,
                (reason or "-")[:40],
                st, req or "-", dec or "-"
            ))
        draw_summary()

    # ---------- Selection ----------
    def get_selected():
        sel = tree.selection()
        if not sel:
            show_warning("Warning", "Select a request first.")
            return None
        return tree.item(sel[0])["values"]

    # ---------- Approve ----------
    def approve():
        values = get_selected()
        if not values:
            return

        req_id = values[0]
        member = values[1]
        book = values[2]
        status = values[6]

        if status != "PENDING":
            show_error("Error", "Only PENDING requests can be approved.")
            return

        req = get_one(
            "SELECT issue_id, requested_days FROM extension_requests WHERE request_id = ?",
            (req_id,)
        )
        issue_id, requested_days = req[0], req[1]

        issue = get_one(
            "SELECT due_date, extension_count FROM issue_return WHERE issue_id = ?",
            (issue_id,)
        )
        if not issue or not issue[0]:
            show_error("Error", "This loan has no due date set (old record).")
            return
        current_due = issue[0]
        current_count = issue[1] or 0

        max_ext = int(get_setting("max_extensions_per_book", "1"))
        if current_count >= max_ext:
            show_error("Error",
                       f"Max extensions ({max_ext}) already reached for this book.")
            return

        max_days = int(get_setting("max_extension_days", "7"))
        if requested_days > max_days:
            show_error("Error",
                       f"Requested days ({requested_days}) exceeds limit ({max_days}).")
            return

        # Calculate new due date
        old_due_dt = parse_date(current_due)
        if old_due_dt is None:
            show_error("Error", "Invalid current due date.")
            return
        new_due_dt = old_due_dt + timedelta(days=requested_days)
        new_due = new_due_dt.strftime("%Y-%m-%d")

        if not ask_confirm(
            "Approve Extension",
            f"Approve {requested_days} extra day(s) for '{member}'?\n\n"
            f"Book: {book}\n"
            f"Old due date: {current_due}\n"
            f"New due date: {new_due}"
        ):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update the issue
        run_query(
            "UPDATE issue_return SET due_date = ?, extension_count = extension_count + 1 "
            "WHERE issue_id = ?",
            (new_due, issue_id)
        )
        # Update the request
        run_query(
            "UPDATE extension_requests SET status = 'APPROVED', decided_on = ? "
            "WHERE request_id = ?",
            (now, req_id)
        )

        log_action("ADMIN", admin_id, "EXTENSION_APPROVED",
                   f"Request #{req_id} approved. Due {current_due} -> {new_due}")

        show_success("Approved", f"Due date updated to {new_due}.")
        refresh()

    # ---------- Reject ----------
    def reject():
        values = get_selected()
        if not values:
            return

        req_id = values[0]
        member = values[1]
        status = values[6]

        if status != "PENDING":
            show_error("Error", "Only PENDING requests can be rejected.")
            return

        note = simpledialog.askstring(
            "Rejection Note (optional)",
            f"Reason for rejecting '{member}'s request:",
            parent=parent
        )

        if not ask_confirm("Confirm", "Reject this request?"):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "UPDATE extension_requests SET status = 'REJECTED', decided_on = ?, "
            "admin_note = ? WHERE request_id = ?",
            (now, note or "", req_id)
        )

        log_action("ADMIN", admin_id, "EXTENSION_REJECTED",
                   f"Request #{req_id} rejected. Note: {note or 'none'}")

        show_success("Rejected", "The request has been rejected.")
        refresh()

    # ---------- Buttons ----------
    success_button(btn_row, "Approve",       approve, width=14).grid(row=0, column=0, padx=5)
    danger_button (btn_row, "Reject",        reject,  width=14).grid(row=0, column=1, padx=5)
    primary_button(btn_row, "Apply Filter",  refresh, width=14).grid(row=0, column=2, padx=5)
    neutral_button(btn_row, "Refresh",       refresh, width=12).grid(row=0, column=3, padx=5)

    refresh()