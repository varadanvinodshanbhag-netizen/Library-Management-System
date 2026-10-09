# ============================================================
# issue_ui.py
# Book Loan & Return Processing Screen.
# Action buttons placed directly adjacent to controls for immediate visibility.
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
    COLORS, FONTS, PAD, section_title, make_table, styled_entry,
    primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)


def show_issue_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(
        parent,
        "Book Circulation: Issue & Return",
        "Manage book loans, check-ins, due dates, and auto-calculated fines"
    )

    # ---------- Loan Policy Info Banner ----------
    policy_frame = tk.Frame(parent, bg=COLORS["card"])
    policy_frame.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    policy_inner = tk.Frame(policy_frame, bg=COLORS["primary_subtle"],
                            highlightbackground=COLORS["border"], highlightthickness=1)
    policy_inner.pack(fill="x", ipady=3)

    loan_days = get_loan_period_days()
    fine_rate = get_fine_rate()

    tk.Label(
        policy_inner,
        text=f"📋 Policy: {loan_days}-day loan period  •  Overdue: Rs {fine_rate:.2f}/day  •  Slips available for all transactions",
        font=FONTS["small_b"],
        bg=COLORS["primary_subtle"],
        fg=COLORS["primary"]
    ).pack(side="left", padx=12)

    # ---------- Form & Filters Container ----------
    controls_container = tk.Frame(
        parent, bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    controls_container.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    # Top Half: Issue Book Form
    issue_row = tk.Frame(controls_container, bg=COLORS["card"])
    issue_row.pack(fill="x", padx=14, pady=6)

    tk.Label(issue_row, text="Book ID *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=0, sticky="w", padx=(0, 4))
    book_entry = styled_entry(issue_row, width=10)
    book_entry.grid(row=0, column=1, sticky="w", padx=(0, 14), ipady=3)

    tk.Label(issue_row, text="Card ID / Member ID *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=2, sticky="w", padx=(0, 4))
    member_entry = styled_entry(issue_row, width=16)
    member_entry.grid(row=0, column=3, sticky="w", padx=(0, 14), ipady=3)

    success_button(issue_row, "📤 Issue Book", lambda: issue_book(), width=13).grid(row=0, column=4, padx=(0, 6))

    # Bottom Half: Action Toolbar & Filter Controls (PACKED BEFORE TABLE)
    filter_row = tk.Frame(controls_container, bg=COLORS["card_alt"], height=38)
    filter_row.pack(fill="x", padx=1, pady=(2, 0), ipady=3)

    tk.Label(filter_row, text=" Status:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(10, 4))
    status_var = tk.StringVar(value="ALL")
    status_combo = ttk.Combobox(
        filter_row, textvariable=status_var, width=10,
        values=["ALL", "ISSUED", "RETURNED"], state="readonly"
    )
    status_combo.pack(side="left", padx=(0, 10))

    tk.Label(filter_row, text="Card / ID:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(0, 4))
    filter_member = styled_entry(filter_row, width=10)
    filter_member.pack(side="left", padx=(0, 10), ipady=2)

    neutral_button(filter_row, "Filter", lambda: refresh(), width=8).pack(side="left", padx=(0, 4))
    neutral_button(filter_row, "Reset", lambda: clear_filters(), width=8).pack(side="left", padx=(0, 12))

    # Direct action buttons placed right in toolbar BEFORE table
    primary_button(filter_row, "📥 Process Return", lambda: return_book(), width=15).pack(side="left", padx=3)
    success_button(filter_row, "🖨️ Print Slip",     lambda: print_slip(),  width=13).pack(side="left", padx=3)
    neutral_button(filter_row, "🔁 Refresh",        lambda: refresh(),     width=10).pack(side="left", padx=3)

    status_combo.bind("<<ComboboxSelected>>", lambda e: refresh())

    # ---------- Table Setup (AT BOTTOM) ----------
    cols = ("issue_id", "book", "member", "card_id", "issue_date",
            "due_date", "return_date", "status", "fine")
    heads = ("Loan ID", "Book Title", "Student Name", "Card ID", "Issued On",
             "Due Date", "Returned On", "Status", "Fine (Rs)")
    widths = (55, 220, 160, 85, 90, 90, 90, 85, 80)

    tree = make_table(parent, cols, heads, widths, height=8)

    # ---------- Data Refresh ----------
    def refresh():
        sql = """
            SELECT ir.issue_id, b.title, m.name, COALESCE(m.card_id, '-' ), ir.issue_date,
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

        m_filter = filter_member.get().strip()
        if m_filter:
            if m_filter.isdigit():
                sql += " AND (ir.member_id = ? OR m.card_id = ?)"
                params.extend([int(m_filter), m_filter])
            else:
                sql += " AND m.card_id LIKE ?"
                params.append(f"%{m_filter}%")

        sql += " ORDER BY ir.issue_id DESC"

        raw_rows = get_rows(sql, tuple(params))
        formatted_rows = []
        for r in raw_rows:
            iid, title, mem, cid, iss, due, ret, st, fine = r
            formatted_rows.append((
                f"#{iid}",
                title,
                mem,
                cid,
                iss or "-",
                due or "-",
                ret or "-",
                st,
                f"Rs {float(fine or 0):.2f}"
            ))

        populate_tree_with_striping(tree, formatted_rows)

    def clear_filters():
        status_var.set("ALL")
        filter_member.delete(0, tk.END)
        refresh()

    def clear_form():
        book_entry.delete(0, tk.END)
        member_entry.delete(0, tk.END)

    # ---------- Issue Book ----------
    def issue_book():
        book_text = book_entry.get().strip()
        member_text = member_entry.get().strip()

        if not book_text or not member_text:
            show_warning("Input Required", "Enter both Book ID and Card ID / Member ID to issue.")
            return
        if not book_text.isdigit():
            show_error("Validation Error", "Book ID must be a numeric value.")
            return

        book_id = int(book_text)

        # Resolve member by numeric ID or by Card ID
        member = None
        if member_text.isdigit():
            member = get_one("SELECT member_id, name, card_id FROM members WHERE member_id = ?", (int(member_text),))
        if member is None:
            # Case-insensitive search on card_id
            member = get_one("SELECT member_id, name, card_id FROM members WHERE UPPER(TRIM(card_id)) = UPPER(?)", (member_text,))

        if member is None:
            show_error("Not Found", f"No student/member found matching '{member_text}' (by Member ID or Card ID).")
            return

        member_id, member_name, card_id_val = member[0], member[1], member[2]

        book = get_one(
            "SELECT title, available_copies FROM books WHERE book_id = ?",
            (book_id,)
        )
        if book is None:
            show_error("Not Found", f"No book found with ID #{book_id}.")
            return
        if book[1] <= 0:
            show_error("Stock Depleted", f"No available copies for '{book[0]}'.")
            return

        already = get_one(
            "SELECT issue_id FROM issue_return "
            "WHERE book_id = ? AND member_id = ? AND status = 'ISSUED'",
            (book_id, member_id)
        )
        if already is not None:
            show_error("Active Loan Exists", f"{member_name} already holds an active copy of '{book[0]}'.")
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

        log_action(
            "ADMIN", admin_id, "BOOK_ISSUED",
            f"Book #{book_id} '{book[0]}' issued to {member_name} ({card_id_val or f'#{member_id}'}) (due {due_str})"
        )

        show_success(
            "Loan Registered",
            f"'{book[0]}' issued to {member_name} ({card_id_val or f'#{member_id}'}).\n\nDue Date: {due_str}"
        )
        clear_form()
        refresh()

    # ---------- Return Book ----------
    def return_book():
        sel = tree.selection()
        if not sel:
            show_warning("Selection Required", "Select a transaction from the table to process return.")
            return

        values = tree.item(sel[0])["values"]
        issue_id = int(str(values[0]).replace("#", ""))
        book = values[1]
        member = values[2]
        status = values[7]

        if status == "RETURNED":
            show_error("Already Returned", "This book loan has already been marked returned.")
            return

        rec = get_one(
            "SELECT book_id, due_date FROM issue_return WHERE issue_id = ?",
            (issue_id,)
        )
        if not rec:
            show_error("Error", "Loan record not found.")
            return

        book_id, due_date = rec[0], rec[1]
        today_str = date.today().strftime("%Y-%m-%d")

        overdue_days, fine_amount = calculate_fine(due_date, today_str)
        fine_rate = get_fine_rate()

        msg = f"Return '{book}' from member '{member}'?"
        if overdue_days > 0:
            msg += f"\n\n⚠️ Overdue: {overdue_days} day(s)\nFine Due: Rs {fine_amount:.2f} ({overdue_days} days × Rs {fine_rate:.2f})"
        else:
            msg += "\n\n✅ On time return: No fine applicable."

        if not ask_confirm("Confirm Return", msg):
            return

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

        run_query(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
            (book_id,)
        )

        if fine_amount > 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            existing = get_one("SELECT fine_id FROM fines WHERE issue_id = ?", (issue_id,))
            if existing:
                run_query(
                    "UPDATE fines SET amount = ?, status = 'UNPAID', generated_on = ? WHERE issue_id = ?",
                    (fine_amount, now, issue_id)
                )
            else:
                member_row = get_one("SELECT member_id FROM issue_return WHERE issue_id = ?", (issue_id,))
                run_query("""
                    INSERT INTO fines (issue_id, member_id, amount, status, generated_on)
                    VALUES (?, ?, ?, 'UNPAID', ?)
                """, (issue_id, member_row[0], fine_amount, now))

        log_action(
            "ADMIN", admin_id, "BOOK_RETURNED",
            f"Loan #{issue_id} '{book}' returned. Overdue: {overdue_days}d, Fine: Rs {fine_amount:.2f}"
        )

        if fine_amount > 0:
            show_success(
                "Return Processed with Fine",
                f"Book returned successfully.\n\nOverdue: {overdue_days} day(s)\nFine Outstanding: Rs {fine_amount:.2f}"
            )
        else:
            show_success("Return Complete", "Book checked in on time. No fines recorded.")

        refresh()

    # ---------- Print Slip ----------
    def print_slip():
        sel = tree.selection()
        if not sel:
            show_warning("Selection Required", "Select a transaction from the table to print a slip.")
            return
        issue_id = int(str(tree.item(sel[0])["values"][0]).replace("#", ""))
        show_slip_window(parent, issue_id)

    refresh()