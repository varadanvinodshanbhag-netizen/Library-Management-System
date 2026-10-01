# ============================================================
# fines_ui.py
# Admin screen: view, filter and manage library fines.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

from db import get_rows, get_one, run_query
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, section_title, make_card,
    primary_button, success_button, danger_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


def show_fines_screen(parent, admin_id=None):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(parent, "Fine Management", "Track unpaid and collected fines")

    # ---------- Summary cards (top) ----------
    summary_frame = tk.Frame(parent, bg=COLORS["card"])
    summary_frame.pack(fill="x", padx=20, pady=(5, 10))

    def get_summary():
        unpaid = get_one(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) "
            "FROM fines WHERE status = 'UNPAID'"
        )
        paid = get_one(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) "
            "FROM fines WHERE status = 'PAID'"
        )
        waived = get_one(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) "
            "FROM fines WHERE status = 'WAIVED'"
        )
        return {
            "unpaid_amount": unpaid[0] or 0, "unpaid_count": unpaid[1] or 0,
            "paid_amount":   paid[0] or 0,   "paid_count":   paid[1] or 0,
            "waived_amount": waived[0] or 0, "waived_count": waived[1] or 0,
        }

    summary = get_summary()

    make_card(summary_frame, "Unpaid Fines",
              f"Rs {summary['unpaid_amount']:.2f}",
              color=COLORS["danger"]).grid(row=0, column=0, padx=6, pady=6)
    make_card(summary_frame, "Collected",
              f"Rs {summary['paid_amount']:.2f}",
              color=COLORS["success"]).grid(row=0, column=1, padx=6, pady=6)
    make_card(summary_frame, "Waived",
              f"Rs {summary['waived_amount']:.2f}",
              color=COLORS["text_muted"]).grid(row=0, column=2, padx=6, pady=6)
    make_card(summary_frame, "Unpaid Count",
              summary["unpaid_count"],
              color=COLORS["warning"]).grid(row=0, column=3, padx=6, pady=6)

    # ---------- Filter bar ----------
    filter_frame = tk.Frame(parent, bg=COLORS["card"])
    filter_frame.pack(fill="x", padx=20, pady=(5, 10))

    tk.Label(filter_frame, text="Status:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=0, padx=(0, 5))
    status_var = tk.StringVar(value="ALL")
    status_combo = ttk.Combobox(
        filter_frame, textvariable=status_var, width=12,
        values=["ALL", "UNPAID", "PAID", "WAIVED"], state="readonly"
    )
    status_combo.grid(row=0, column=1, padx=(0, 15))

    tk.Label(filter_frame, text="Member ID:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=2, padx=(0, 5))
    member_entry = tk.Entry(filter_frame, width=10, font=FONTS["body"],
                            relief="solid", bd=1)
    member_entry.grid(row=0, column=3, padx=(0, 15), ipady=3)

    tk.Label(filter_frame, text="Book ID:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=4, padx=(0, 5))
    book_entry = tk.Entry(filter_frame, width=10, font=FONTS["body"],
                          relief="solid", bd=1)
    book_entry.grid(row=0, column=5, padx=(0, 15), ipady=3)

    # ---------- Button row (packed BEFORE table so it stays on top) ----------
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 12))

    # ---------- Table frame ----------
    table_frame = tk.Frame(parent, bg=COLORS["card"])
    table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

    cols = ("fine_id", "issue_id", "member", "book",
            "overdue", "amount", "status", "generated", "paid")
    heads = ("Fine ID", "Issue ID", "Member", "Book",
             "Days", "Amount (Rs)", "Status", "Generated On", "Paid On")
    widths = (70, 70, 160, 200, 60, 100, 90, 120, 120)

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

    # ---------- Refresh table ----------
    def refresh():
        for item in tree.get_children():
            tree.delete(item)

        sql = """
            SELECT f.fine_id, f.issue_id, m.name, b.title,
                   ir.overdue_days, f.amount, f.status,
                   f.generated_on, f.paid_on
            FROM fines f
            JOIN issue_return ir ON f.issue_id = ir.issue_id
            JOIN members m ON f.member_id = m.member_id
            JOIN books   b ON ir.book_id   = b.book_id
            WHERE 1=1
        """
        params = []

        if status_var.get() != "ALL":
            sql += " AND f.status = ?"
            params.append(status_var.get())

        if member_entry.get().strip():
            if member_entry.get().strip().isdigit():
                sql += " AND f.member_id = ?"
                params.append(int(member_entry.get().strip()))

        if book_entry.get().strip():
            if book_entry.get().strip().isdigit():
                sql += " AND ir.book_id = ?"
                params.append(int(book_entry.get().strip()))

        sql += " ORDER BY f.fine_id DESC"

        rows = get_rows(sql, tuple(params))
        for r in rows:
            fine_id, issue_id, member, book, days, amount, status, gen, paid = r
            tree.insert("", tk.END, values=(
                fine_id, issue_id, member, book,
                days or 0, f"{amount:.2f}", status,
                gen or "-", paid or "-"
            ))

    # ---------- Actions ----------
    def get_selected():
        sel = tree.selection()
        if not sel:
            show_warning("Warning", "Select a fine from the table first.")
            return None
        return tree.item(sel[0])["values"]

    def record_payment():
        values = get_selected()
        if not values:
            return

        fine_id = values[0]
        member = values[2]
        book = values[3]
        amount = values[5]
        status = values[6]

        if status == "PAID":
            show_error("Error", "This fine is already paid.")
            return
        if status == "WAIVED":
            show_error("Error", "This fine was waived; cannot record payment.")
            return

        if not ask_confirm(
            "Confirm Payment",
            f"Record payment of Rs {amount} from '{member}' for '{book}'?"
        ):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "UPDATE fines SET status = 'PAID', paid_amount = amount, paid_on = ? "
            "WHERE fine_id = ?",
            (now, fine_id)
        )
        run_query(
            "UPDATE issue_return SET fine_status = 'PAID' "
            "WHERE issue_id = (SELECT issue_id FROM fines WHERE fine_id = ?)",
            (fine_id,)
        )

        log_action("ADMIN", admin_id, "FINE_PAID",
                   f"Fine #{fine_id} paid by '{member}' for '{book}' (Rs {amount})")

        show_success("Success", f"Payment of Rs {amount} recorded.")
        # Refresh cards + table
        for w in summary_frame.winfo_children():
            w.destroy()
        s = get_summary()
        make_card(summary_frame, "Unpaid Fines", f"Rs {s['unpaid_amount']:.2f}",
                  color=COLORS["danger"]).grid(row=0, column=0, padx=6, pady=6)
        make_card(summary_frame, "Collected", f"Rs {s['paid_amount']:.2f}",
                  color=COLORS["success"]).grid(row=0, column=1, padx=6, pady=6)
        make_card(summary_frame, "Waived", f"Rs {s['waived_amount']:.2f}",
                  color=COLORS["text_muted"]).grid(row=0, column=2, padx=6, pady=6)
        make_card(summary_frame, "Unpaid Count", s["unpaid_count"],
                  color=COLORS["warning"]).grid(row=0, column=3, padx=6, pady=6)
        refresh()

    def waive_fine():
        values = get_selected()
        if not values:
            return

        fine_id = values[0]
        member = values[2]
        book = values[3]
        amount = values[5]
        status = values[6]

        if status == "PAID":
            show_error("Error", "Cannot waive a fine that is already paid.")
            return
        if status == "WAIVED":
            show_error("Error", "This fine is already waived.")
            return

        if not ask_confirm(
            "Waive Fine",
            f"Waive Rs {amount} fine for '{member}' on '{book}'?\n"
            f"This action is logged."
        ):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "UPDATE fines SET status = 'WAIVED', paid_on = ? WHERE fine_id = ?",
            (now, fine_id)
        )
        run_query(
            "UPDATE issue_return SET fine_status = 'WAIVED' "
            "WHERE issue_id = (SELECT issue_id FROM fines WHERE fine_id = ?)",
            (fine_id,)
        )

        log_action("ADMIN", admin_id, "FINE_WAIVED",
                   f"Fine #{fine_id} waived for '{member}' (Rs {amount})")

        show_success("Success", "Fine waived.")
        refresh()

    def clear_filters():
        status_var.set("ALL")
        member_entry.delete(0, tk.END)
        book_entry.delete(0, tk.END)
        refresh()

    # ---------- Buttons ----------
    success_button(btn_row, "Record Payment", record_payment, width=16).grid(row=0, column=0, padx=5)
    danger_button (btn_row, "Waive Fine",     waive_fine,     width=14).grid(row=0, column=1, padx=5)
    primary_button(btn_row, "Apply Filters",  refresh,        width=14).grid(row=0, column=2, padx=5)
    neutral_button(btn_row, "Clear Filters",  clear_filters,  width=14).grid(row=0, column=3, padx=5)

    refresh()