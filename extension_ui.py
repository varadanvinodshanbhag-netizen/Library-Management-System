# ============================================================
# extension_ui.py
# Administrator Portal: Book Loan Extension & Renewal Requests.
# Action buttons placed directly adjacent to controls for immediate visibility.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date, timedelta

from db import get_rows, get_one, run_query
from activity_log import log_action
from fine_calc import get_setting, parse_date
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_card, styled_entry, make_table,
    primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)


def show_extensions_screen(parent, admin_id=None):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(
        parent,
        "Book Loan Extension Requests",
        "Review and approve or reject member requests for borrowing period renewals"
    )

    # ---------- Summary KPI Row ----------
    summary_frame = tk.Frame(parent, bg=COLORS["card"])
    summary_frame.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    def get_summary():
        pending = get_one("SELECT COUNT(*) FROM extension_requests WHERE status = 'PENDING'")[0]
        approved = get_one("SELECT COUNT(*) FROM extension_requests WHERE status = 'APPROVED'")[0]
        rejected = get_one("SELECT COUNT(*) FROM extension_requests WHERE status = 'REJECTED'")[0]
        return pending, approved, rejected

    def render_summary():
        for w in summary_frame.winfo_children():
            w.destroy()
        p, a, r = get_summary()
        make_card(summary_frame, "Pending Approvals", p, color=COLORS["warning"], height=66).grid(row=0, column=0, padx=3, pady=2, sticky="nsew")
        make_card(summary_frame, "Approved Renewals", a, color=COLORS["success"], height=66).grid(row=0, column=1, padx=3, pady=2, sticky="nsew")
        make_card(summary_frame, "Rejected Requests", r, color=COLORS["danger"],  height=66).grid(row=0, column=2, padx=3, pady=2, sticky="nsew")
        for c in range(3):
            summary_frame.grid_columnconfigure(c, weight=1)

    # ---------- Filter Bar & Action Toolbar (PACKED BEFORE TABLE) ----------
    filter_card = tk.Frame(parent, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
    filter_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6), ipady=3)

    tk.Label(filter_card, text=" Status:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(10, 4))
    status_var = tk.StringVar(value="PENDING")
    status_combo = ttk.Combobox(
        filter_card, textvariable=status_var, width=12,
        values=["ALL", "PENDING", "APPROVED", "REJECTED"], state="readonly"
    )
    status_combo.pack(side="left", padx=(0, 10))

    neutral_button(filter_card, "Filter", lambda: refresh(), width=8).pack(side="left", padx=(0, 4))
    neutral_button(filter_card, "All", lambda: (status_var.set("ALL"), refresh()), width=6).pack(side="left", padx=(0, 14))

    # Action buttons right in toolbar before table
    success_button(filter_card, "✅ Approve Renewal", lambda: approve(), width=16).pack(side="left", padx=3)
    danger_button (filter_card, "❌ Reject Request",  lambda: reject(),  width=15).pack(side="left", padx=3)
    neutral_button(filter_card, "🔁 Refresh",        lambda: refresh(), width=10).pack(side="left", padx=3)

    status_combo.bind("<<ComboboxSelected>>", lambda e: refresh())

    # ---------- Table Setup (AT BOTTOM) ----------
    cols = ("req_id", "member", "book", "issue_id",
            "days", "reason", "status", "requested", "decided")
    heads = ("Request ID", "Student [Card ID]", "Book Title", "Loan ID",
             "Days", "Stated Reason", "Status", "Requested On", "Decision Date")
    widths = (70, 160, 220, 70, 55, 180, 95, 110, 110)

    tree = make_table(parent, cols, heads, widths, height=8)

    # ---------- Data Operations ----------
    def refresh():
        sql = """
            SELECT er.request_id, m.name, m.card_id, b.title, er.issue_id,
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

        raw_rows = get_rows(sql, tuple(params))
        formatted_rows = []
        for r in raw_rows:
            rid, mem, card_id, book, iid, days, reason, st, req, dec = r
            if st == "APPROVED":
                st_display = "🟢 Approved"
            elif st == "PENDING":
                st_display = "🟡 Pending"
            else:
                st_display = "🔴 Rejected"

            mem_label = f"{mem} [{card_id}]" if card_id else mem

            formatted_rows.append((
                f"#{rid}",
                mem_label,
                book,
                f"#{iid}",
                f"{days}d",
                (reason or "-")[:35],
                st_display,
                req or "-",
                dec or "-"
            ))

        populate_tree_with_striping(tree, formatted_rows)
        render_summary()

    def get_selected():
        sel = tree.selection()
        if not sel:
            show_warning("Selection Required", "Select an extension request from the table.")
            return None
        return tree.item(sel[0])["values"]

    def approve():
        values = get_selected()
        if not values:
            return

        req_id = int(str(values[0]).replace("#", ""))
        member = values[1]
        book = values[2]
        status = values[6]

        if "Pending" not in status:
            show_error("Invalid Action", "Only PENDING extension requests can be approved.")
            return

        req = get_one("SELECT issue_id, requested_days FROM extension_requests WHERE request_id = ?", (req_id,))
        issue_id, requested_days = req[0], req[1]

        issue = get_one("SELECT due_date, extension_count FROM issue_return WHERE issue_id = ?", (issue_id,))
        if not issue or not issue[0]:
            show_error("Data Error", "This borrowing record has no valid due date configured.")
            return

        current_due = issue[0]
        current_count = issue[1] or 0

        max_ext = int(get_setting("max_extensions_per_book", "1"))
        if current_count >= max_ext:
            show_error("Limit Exceeded", f"Maximum extensions limit ({max_ext}) already reached for this book loan.")
            return

        max_days = int(get_setting("max_extension_days", "7"))
        if requested_days > max_days:
            show_error("Days Exceeded", f"Requested {requested_days} days exceeds system limit of {max_days} days.")
            return

        old_due_dt = parse_date(current_due)
        if old_due_dt is None:
            show_error("Error", "Invalid current due date format.")
            return

        new_due_dt = old_due_dt + timedelta(days=requested_days)
        new_due = new_due_dt.strftime("%Y-%m-%d")

        if not ask_confirm(
            "Confirm Renewal Approval",
            f"Approve {requested_days} extra day(s) for member '{member}'?\n\n"
            f"Book: {book}\n"
            f"Current Due Date: {current_due}\n"
            f"Extended Due Date: {new_due}"
        ):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "UPDATE issue_return SET due_date = ?, extension_count = extension_count + 1 WHERE issue_id = ?",
            (new_due, issue_id)
        )
        run_query(
            "UPDATE extension_requests SET status = 'APPROVED', decided_on = ? WHERE request_id = ?",
            (now, req_id)
        )

        log_action(
            "ADMIN", admin_id, "EXTENSION_APPROVED",
            f"Request #{req_id} approved for '{member}'. Due: {current_due} -> {new_due}"
        )

        show_success("Extension Approved", f"Due date successfully extended to {new_due}.")
        refresh()

    def reject():
        values = get_selected()
        if not values:
            return

        req_id = int(str(values[0]).replace("#", ""))
        member = values[1]
        status = values[6]

        if "Pending" not in status:
            show_error("Invalid Action", "Only PENDING extension requests can be rejected.")
            return

        note = simpledialog.askstring(
            "Rejection Reason",
            f"Administrative reason for rejecting '{member}'s request (optional):",
            parent=parent
        )

        if not ask_confirm("Confirm Rejection", "Are you sure you want to reject this renewal request?"):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "UPDATE extension_requests SET status = 'REJECTED', decided_on = ?, admin_note = ? WHERE request_id = ?",
            (now, note or "", req_id)
        )

        log_action(
            "ADMIN", admin_id, "EXTENSION_REJECTED",
            f"Request #{req_id} for '{member}' rejected. Reason: {note or 'None'}"
        )

        show_success("Request Rejected", "The renewal request has been rejected.")
        refresh()

    refresh()