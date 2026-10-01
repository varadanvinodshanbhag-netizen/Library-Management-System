# ============================================================
# issue_ui.py
# Issue / Return / Transaction History with due dates and auto-fine.
# Also includes a "Print Slip" button for any selected transaction.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from db import run_query, get_rows, get_one
from activity_log import log_action
from fine_calc import (
    calculate_due_date, calculate_fine, get_fine_rate, get_loan_period_days
)
from slip_generator import show_slip_window
from ui_helpers import (
    COLORS, FONTS, section_title, make_table,
    primary_button, success_button, danger_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


def show_issue_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(parent, "Issue / Return Books",
                  "Track borrowing, due dates and fines")

    # ---------- Form ----------
    form = tk.Frame(parent, bg=COLORS["card"])
    form.pack(fill="x", padx=20, pady=(5, 10))

    tk.Label(form, text="Book ID",   bg=COLORS["card"], font=FONTS["body"]
             ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
    book_entry = tk.Entry(form, width=14, font=FONTS["body"],
                          relief="solid", bd=1)
    book_entry.grid(row=0, column=1, padx=(0, 20), ipady=3)

    tk.Label(form, text="Member ID", bg=COLORS["card"], font=FONTS["body"]
             ).grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
    member_entry = tk.Entry(form, width=14, font=FONTS["body"],
                            relief="solid", bd=1)
    member_entry.grid(row=0, column=3, padx=(0, 20), ipady=3)

    # Info line about loan period
    info_label = tk.Label(
        parent,
        text=f"Loan period: {get_loan_period_days()} days    |    "
             f"Fine rate: Rs {get_fine_rate():.2f} per day",
        bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["small"]
    )
    info_label.pack(anchor="w", padx=20, pady=(0, 5))

    # ---------- Filter bar ----------
    filter_frame = tk.Frame(parent, bg=COLORS["card"])
    filter_frame.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(filter_frame, text="Status:", bg=COLORS["card"], font=FONTS["body"]
             ).grid(row=0, column=0, padx=(0, 5))
    status_var = tk.StringVar(value="ALL")
    ttk.Combobox(
        filter_frame, textvariable=status_var, width=12,
        values=["ALL", "ISSUED", "RETURNED"], state="readonly"
    ).grid(row=0, column=1, padx=(0, 15))

    tk.Label(filter_frame, text="Member ID:", bg=COLORS["card"], font=FONTS["body"]
             ).grid(row=0, column=2, padx=(0, 5))
    filter_member = tk.Entry(filter_frame, width=10, font=FONTS["body"],
                             relief="solid", bd=1)
    filter_member.grid(row=0, column=3, padx=(0, 15), ipady=3)

    # ---------- Button row (packed BEFORE table) ----------
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 12))

    # ---------- Table ----------
    cols = ("issue_id", "book", "member", "issue_date",
            "due_date", "return_date", "status", "fine")
    heads = ("Issue ID", "Book", "Member", "Issued On",
             "Due On", "Returned On", "Status", "Fine (Rs)")
    widths = (70, 190, 140, 100, 100, 100, 90, 80)

    tree = make_table(parent, cols, heads, widths, height=12)

    # ---------- Refresh ----------
    def refresh():
        for item in tree.get_children():
            tree.delete(item)

        sql = """
            SELECT ir.issue_id, b.title, m.name, ir.issue_date,
                   ir.due_date,
                   COALESCE(ir.actual_return_date, ir.return_date),
                   ir.status, ir.fine_amount
            FROM issue_return ir
            JOIN books   b ON ir.book_id   = b.book_id
            JOIN members m ON ir.member_id = m.member_id
            WHERE 1=1
        """
        params = []

        if status_var.get() != "ALL":
            sql += " AND ir.status = ?"
            params.append(status_var.get())

        if filter_member.get().strip():
            if filter_member.get().strip().isdigit():
                sql += " AND ir.member_id = ?"
                params.append(int(filter_member.get().strip()))

        sql += " ORDER BY ir.issue_id DESC"

        for r in get_rows(sql, tuple(params)):
            iid, title, member, iss, due, ret, st, fine = r
            tree.insert("", tk.END, values=(
                iid, title, member,
                iss or "-",
                due or "-",
                ret or "-",
                st,
                f"{float(fine or 0):.2f}"
            ))

    def clear_form():
        book_entry.delete(0, tk.END)
        member_entry.delete(0, tk.END)

    def clear_filters():
        status_var.set("ALL")
        filter_member.delete(0, tk.END)
        refresh()

    # ---------- Issue ----------
    def issue_book():
        book_text = book_entry.get().strip()
        member_text = member_entry.get().strip()

        if book_text == "" or member_text == "":
            show_warning("Warning", "Enter both Book ID and Member ID.")
            return
        if not book_text.isdigit() or not member_text.isdigit():
            show_error("Error", "IDs must be numbers.")
            return

        book_id = int(book_text)
        member_id = int(member_text)

        book = get_one(
            "SELECT title, available_copies FROM books WHERE book_id = ?",
            (book_id,)
        )
        if book is None:
            show_error("Error", "Book ID not found.")
            return
        if book[1] <= 0:
            show_error("Error", f"No copies available for '{book[0]}'.")
            return

        member = get_one("SELECT name FROM members WHERE member_id = ?", (member_id,))
        if member is None:
            show_error("Error", "Member ID not found.")
            return

        already = get_one(
            "SELECT issue_id FROM issue_return "
            "WHERE book_id = ? AND member_id = ? AND status = 'ISSUED'",
            (book_id, member_id)
        )
        if already is not None:
            show_error("Error", "This member already holds a copy of this book.")
            return

        today_str = date.today().strftime("%Y-%m-%d")
        due_str = calculate_due_date(today_str)

        run_query(
            "INSERT INTO issue_return "
            "(book_id, member_id, issue_date, due_date, status, fine_status) "
            "VALUES (?, ?, ?, ?, 'ISSUED', 'NONE')",
            (book_id, member_id, today_str, due_str)
        )
        run_query(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (book_id,)
        )

        log_action("ADMIN", admin_id, "BOOK_ISSUED",
                   f"Book #{book_id} '{book[0]}' issued to member #{member_id} '{member[0]}' "
                   f"(due {due_str})")

        show_success(
            "Success",
            f"'{book[0]}' issued to {member[0]}.\nDue date: {due_str}"
        )
        clear_form()
        refresh()

    # ---------- Return ----------
    def return_book():
        sel = tree.selection()
        if not sel:
            show_warning("Warning", "Select a row from the table to return.")
            return

        values = tree.item(sel[0])["values"]
        issue_id = values[0]
        book = values[1]
        member = values[2]
        status = values[6]

        if status == "RETURNED":
            show_error("Error", "This book is already returned.")
            return

        rec = get_one(
            "SELECT book_id, due_date FROM issue_return WHERE issue_id = ?",
            (issue_id,)
        )
        if not rec:
            show_error("Error", "Transaction not found.")
            return

        book_id, due_date = rec[0], rec[1]
        today_str = date.today().strftime("%Y-%m-%d")

        overdue_days, fine_amount = calculate_fine(due_date, today_str)
        fine_rate = get_fine_rate()

        # Confirm dialog
        msg = f"Return '{book}' from {member}?"
        if overdue_days > 0:
            msg += (f"\n\nOverdue: {overdue_days} day(s)\n"
                    f"Fine: Rs {fine_amount:.2f} ({overdue_days} x Rs {fine_rate:.2f})")
        else:
            msg += "\n\nNo fine (returned on time)."

        if not ask_confirm("Confirm Return", msg):
            return

        # Update issue_return
        run_query("""
            UPDATE issue_return
            SET return_date = ?, actual_return_date = ?, status = 'RETURNED',
                overdue_days = ?, fine_rate = ?, fine_amount = ?,
                fine_status = ?
            WHERE issue_id = ?
        """, (
            today_str, today_str,
            overdue_days, fine_rate, fine_amount,
            "UNPAID" if fine_amount > 0 else "NONE",
            issue_id
        ))

        # Update book available_copies
        run_query(
            "UPDATE books SET available_copies = available_copies + 1 "
            "WHERE book_id = ?",
            (book_id,)
        )

        # Insert into fines table if there's a fine
        if fine_amount > 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            existing = get_one(
                "SELECT fine_id FROM fines WHERE issue_id = ?", (issue_id,)
            )
            if existing:
                run_query(
                    "UPDATE fines SET amount = ?, status = 'UNPAID', generated_on = ? "
                    "WHERE issue_id = ?",
                    (fine_amount, now, issue_id)
                )
            else:
                member_row = get_one(
                    "SELECT member_id FROM issue_return WHERE issue_id = ?",
                    (issue_id,)
                )
                run_query("""
                    INSERT INTO fines
                    (issue_id, member_id, amount, status, generated_on)
                    VALUES (?, ?, ?, 'UNPAID', ?)
                """, (issue_id, member_row[0], fine_amount, now))

        log_action("ADMIN", admin_id, "BOOK_RETURNED",
                   f"Issue #{issue_id} '{book}' returned. "
                   f"Overdue {overdue_days} days, fine Rs {fine_amount:.2f}")

        if fine_amount > 0:
            show_success(
                "Returned with Fine",
                f"Book returned.\n\n"
                f"Overdue: {overdue_days} day(s)\n"
                f"Fine: Rs {fine_amount:.2f} (UNPAID)"
            )
        else:
            show_success("Success", "Book returned on time. No fine.")

        refresh()

    # ---------- Print Slip ----------
    def print_slip():
        sel = tree.selection()
        if not sel:
            show_warning("Warning", "Select a transaction first.")
            return
        issue_id = tree.item(sel[0])["values"][0]
        show_slip_window(parent, issue_id)

    # ---------- Buttons ----------
    success_button(btn_row, "Issue Book",     issue_book,   width=14).grid(row=0, column=0, padx=5)
    primary_button(btn_row, "Return Book",    return_book,  width=14).grid(row=0, column=1, padx=5)
    primary_button(btn_row, "Print Slip",     print_slip,   width=14).grid(row=0, column=2, padx=5)
    neutral_button(btn_row, "Apply Filters",  refresh,      width=14).grid(row=0, column=3, padx=5)
    neutral_button(btn_row, "Clear",          clear_filters,width=10).grid(row=0, column=4, padx=5)
    neutral_button(btn_row, "Refresh",        refresh,      width=10).grid(row=0, column=5, padx=5)

    tk.Label(
        parent,
        text="Tip: Enter a Book ID and Member ID above → click 'Issue Book'.\n"
             "To return a book, select its row and click 'Return Book'. Fine is auto-calculated.\n"
             "Click 'Print Slip' to print the transaction slip for a selected row.",
        bg=COLORS["card"], fg=COLORS["text_muted"],
        font=FONTS["small"], justify="left"
    ).pack(pady=(0, 8))

    refresh()