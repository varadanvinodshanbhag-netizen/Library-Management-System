# ============================================================
# fines_ui.py
# Administrator Portal: Library Fine Tracking & Collection.
# Action buttons placed directly adjacent to controls for immediate visibility.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from db import get_rows, get_one, run_query
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_card, styled_entry, make_table,
    primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)


def show_fines_screen(parent, admin_id=None):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(
        parent,
        "Fine Management & Revenue Tracking",
        "Track outstanding overdue charges, record collections, and process waivers"
    )

    # ---------- Summary KPI Row ----------
    summary_frame = tk.Frame(parent, bg=COLORS["card"])
    summary_frame.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    def get_summary():
        unpaid = get_one(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM fines WHERE status = 'UNPAID'"
        )
        paid = get_one(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM fines WHERE status = 'PAID'"
        )
        waived = get_one(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM fines WHERE status = 'WAIVED'"
        )
        return {
            "unpaid_amount": unpaid[0] or 0, "unpaid_count": unpaid[1] or 0,
            "paid_amount":   paid[0] or 0,   "paid_count":   paid[1] or 0,
            "waived_amount": waived[0] or 0, "waived_count": waived[1] or 0,
        }

    def render_summary():
        for w in summary_frame.winfo_children():
            w.destroy()
        s = get_summary()
        make_card(summary_frame, "Outstanding Fines", f"Rs {s['unpaid_amount']:.2f}",
                  color=COLORS["danger"], height=66).grid(row=0, column=0, padx=3, pady=2, sticky="nsew")
        make_card(summary_frame, "Collected Revenue", f"Rs {s['paid_amount']:.2f}",
                  color=COLORS["success"], height=66).grid(row=0, column=1, padx=3, pady=2, sticky="nsew")
        make_card(summary_frame, "Waived Amount", f"Rs {s['waived_amount']:.2f}",
                  color=COLORS["text_muted"], height=66).grid(row=0, column=2, padx=3, pady=2, sticky="nsew")
        make_card(summary_frame, "Unpaid Cases", s["unpaid_count"],
                  color=COLORS["warning"], height=66).grid(row=0, column=3, padx=3, pady=2, sticky="nsew")

        for c in range(4):
            summary_frame.grid_columnconfigure(c, weight=1)

    # ---------- Filter Bar & Action Toolbar (PACKED BEFORE TABLE) ----------
    filter_card = tk.Frame(parent, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
    filter_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6), ipady=3)

    tk.Label(filter_card, text=" Status:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(10, 4))
    status_var = tk.StringVar(value="ALL")
    status_combo = ttk.Combobox(
        filter_card, textvariable=status_var, width=10,
        values=["ALL", "UNPAID", "PAID", "WAIVED"], state="readonly"
    )
    status_combo.pack(side="left", padx=(0, 10))

    tk.Label(filter_card, text="Card/Member ID:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(0, 4))
    member_entry = styled_entry(filter_card, width=12)
    member_entry.pack(side="left", padx=(0, 10), ipady=2)

    tk.Label(filter_card, text="Book ID:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(0, 4))
    book_entry = styled_entry(filter_card, width=8)
    book_entry.pack(side="left", padx=(0, 10), ipady=2)

    neutral_button(filter_card, "Filter", lambda: refresh(), width=8).pack(side="left", padx=(0, 4))
    neutral_button(filter_card, "Reset", lambda: clear_filters(), width=8).pack(side="left", padx=(0, 12))

    # Action buttons right in toolbar before table
    success_button(filter_card, "💵 Record Payment", lambda: record_payment(), width=16).pack(side="left", padx=2)
    danger_button (filter_card, "🛡️ Waive Fine",     lambda: waive_fine(),     width=13).pack(side="left", padx=2)
    neutral_button(filter_card, "🔁 Refresh",        lambda: refresh(),        width=10).pack(side="left", padx=2)

    status_combo.bind("<<ComboboxSelected>>", lambda e: refresh())

    # ---------- Table Setup (AT BOTTOM) ----------
    cols = ("fine_id", "issue_id", "member", "book",
            "overdue", "amount", "status", "generated", "paid")
    heads = ("Fine ID", "Loan ID", "Student [Card ID]", "Book Title",
             "Days Overdue", "Amount (Rs)", "Payment Status", "Generated On", "Paid/Settled On")
    widths = (65, 65, 180, 210, 90, 95, 100, 110, 110)

    tree = make_table(parent, cols, heads, widths, height=8)

    # ---------- Data Operations ----------
    def refresh():
        sql = """
            SELECT f.fine_id, f.issue_id, m.name, m.card_id, b.title,
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

        m_id = member_entry.get().strip()
        if m_id:
            if m_id.isdigit():
                sql += " AND f.member_id = ?"
                params.append(int(m_id))
            else:
                sql += " AND (UPPER(TRIM(m.card_id)) = UPPER(?) OR m.name LIKE ?)"
                params.extend([m_id, f"%{m_id}%"])

        b_id = book_entry.get().strip()
        if b_id and b_id.isdigit():
            sql += " AND ir.book_id = ?"
            params.append(int(b_id))

        sql += " ORDER BY f.fine_id DESC"

        raw_rows = get_rows(sql, tuple(params))
        formatted_rows = []
        for r in raw_rows:
            fid, iid, mem, card_id, b_title, days, amt, st, gen, paid = r
            if st == "PAID":
                st_display = "🟢 Paid"
            elif st == "UNPAID":
                st_display = "🔴 Unpaid"
            else:
                st_display = "⚪ Waived"

            mem_label = f"{mem} [{card_id}]" if card_id else mem

            formatted_rows.append((
                f"#{fid}",
                f"#{iid}",
                mem_label,
                b_title,
                f"{days or 0} days",
                f"Rs {float(amt):.2f}",
                st_display,
                gen or "-",
                paid or "-"
            ))

        populate_tree_with_striping(tree, formatted_rows)
        render_summary()

    def get_selected():
        sel = tree.selection()
        if not sel:
            show_warning("Selection Required", "Please select a fine entry from the table.")
            return None
        return tree.item(sel[0])["values"]

    def record_payment():
        values = get_selected()
        if not values:
            return

        fine_id = int(str(values[0]).replace("#", ""))
        member = values[2]
        book = values[3]
        amount_str = values[5]
        status = values[6]

        if "Paid" in status:
            show_error("Already Settled", "This fine has already been paid in full.")
            return
        if "Waived" in status:
            show_error("Penalty Waived", "This fine was waived; payment cannot be accepted.")
            return

        if not ask_confirm(
            "Confirm Payment Collection",
            f"Record payment receipt of {amount_str} from member '{member}' for '{book}'?"
        ):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "UPDATE fines SET status = 'PAID', paid_amount = amount, paid_on = ? WHERE fine_id = ?",
            (now, fine_id)
        )
        run_query(
            "UPDATE issue_return SET fine_status = 'PAID' "
            "WHERE issue_id = (SELECT issue_id FROM fines WHERE fine_id = ?)",
            (fine_id,)
        )

        log_action(
            "ADMIN", admin_id, "FINE_PAID",
            f"Fine #{fine_id} paid by '{member}' for '{book}' ({amount_str})"
        )

        show_success("Payment Recorded", f"Payment of {amount_str} recorded successfully.")
        refresh()

    def waive_fine():
        values = get_selected()
        if not values:
            return

        fine_id = int(str(values[0]).replace("#", ""))
        member = values[2]
        book = values[3]
        amount_str = values[5]
        status = values[6]

        if "Paid" in status:
            show_error("Already Paid", "Cannot waive a fine that has already been collected.")
            return
        if "Waived" in status:
            show_error("Already Waived", "This fine is already in waived status.")
            return

        if not ask_confirm(
            "Confirm Fine Waiver",
            f"Waive {amount_str} fine for member '{member}' on '{book}'?\n\nThis administrative action will be logged."
        ):
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query("UPDATE fines SET status = 'WAIVED', paid_on = ? WHERE fine_id = ?", (now, fine_id))
        run_query(
            "UPDATE issue_return SET fine_status = 'WAIVED' "
            "WHERE issue_id = (SELECT issue_id FROM fines WHERE fine_id = ?)",
            (fine_id,)
        )

        log_action(
            "ADMIN", admin_id, "FINE_WAIVED",
            f"Fine #{fine_id} waived for '{member}' ({amount_str})"
        )

        show_success("Fine Waived", "Penalty waived successfully.")
        refresh()

    def clear_filters():
        status_var.set("ALL")
        member_entry.delete(0, tk.END)
        book_entry.delete(0, tk.END)
        refresh()

    refresh()