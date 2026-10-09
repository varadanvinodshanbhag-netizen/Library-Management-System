# ============================================================
# activity_log_ui.py
# Administrator Portal: System Security & Activity Audit Log.
# Action buttons placed directly adjacent to controls for immediate visibility.
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from datetime import datetime

from db import get_rows, run_query
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_table, styled_entry,
    primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)


def show_activity_log_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(
        parent,
        "System Security & Audit Activity Log",
        "Chronological ledger of user logins, circulation transactions, fine payments, and system events"
    )

    # ---------- Filter Bar Card (PACKED BEFORE TABLE) ----------
    filter_card = tk.Frame(parent, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
    filter_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6), ipady=3)

    # Actor Filter
    tk.Label(filter_card, text=" Actor:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).grid(row=0, column=0, padx=(10, 2), pady=3)
    user_var = tk.StringVar(value="ALL")
    user_combo = ttk.Combobox(
        filter_card, textvariable=user_var, width=8,
        values=["ALL", "ADMIN", "MEMBER", "SYSTEM"], state="readonly"
    )
    user_combo.grid(row=0, column=1, padx=(0, 8), pady=3)

    # Action Keyword
    tk.Label(filter_card, text="Keyword:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).grid(row=0, column=2, padx=(0, 2), pady=3)
    action_entry = styled_entry(filter_card, width=14)
    action_entry.grid(row=0, column=3, padx=(0, 8), pady=3, ipady=2)

    # Date
    tk.Label(filter_card, text="Date:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).grid(row=0, column=4, padx=(0, 2), pady=3)
    date_entry = styled_entry(filter_card, width=11)
    date_entry.grid(row=0, column=5, padx=(0, 8), pady=3, ipady=2)

    # Limit
    tk.Label(filter_card, text="Limit:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).grid(row=0, column=6, padx=(0, 2), pady=3)
    limit_var = tk.StringVar(value="200")
    limit_combo = ttk.Combobox(
        filter_card, textvariable=limit_var, width=6,
        values=["50", "100", "200", "500", "1000"], state="readonly"
    )
    limit_combo.grid(row=0, column=7, padx=(0, 8), pady=3)

    neutral_button(filter_card, "Filter", lambda: refresh(), width=8).grid(row=0, column=8, padx=2)
    success_button(filter_card, "📥 Export", lambda: export_csv(), width=10).grid(row=0, column=9, padx=2)
    danger_button (filter_card, "🧹 Purge >30d", lambda: clear_old_logs(), width=12).grid(row=0, column=10, padx=2)
    neutral_button(filter_card, "🔁 Refresh", lambda: refresh(), width=9).grid(row=0, column=11, padx=2)

    # ---------- Table Setup (AT BOTTOM) ----------
    cols = ("log_id", "time", "user_type", "user_id", "action", "details")
    heads = ("Log ID", "Timestamp", "Actor Role", "User ID", "Action Code", "Transaction Event Details")
    widths = (65, 140, 85, 75, 170, 480)

    tree = make_table(parent, cols, heads, widths, height=9)

    # ---------- Data Operations ----------
    def refresh():
        sql = "SELECT log_id, timestamp, user_type, user_id, action, details FROM activity_logs WHERE 1=1"
        params = []

        if user_var.get() != "ALL":
            sql += " AND user_type = ?"
            params.append(user_var.get())

        act_kw = action_entry.get().strip()
        if act_kw:
            sql += " AND action LIKE ?"
            params.append(f"%{act_kw}%")

        d_str = date_entry.get().strip()
        if d_str:
            sql += " AND date(timestamp) = date(?)"
            params.append(d_str)

        try:
            lim = int(limit_var.get())
        except ValueError:
            lim = 200
        sql += f" ORDER BY log_id DESC LIMIT {lim}"

        raw_rows = get_rows(sql, tuple(params))
        formatted_rows = []
        for r in raw_rows:
            lid, ts, u_type, uid, action, det = r
            uid_str = f"#{uid}" if uid else "SYSTEM"
            formatted_rows.append((
                f"#{lid}",
                ts or "-",
                u_type,
                uid_str,
                action,
                det or "-"
            ))

        populate_tree_with_striping(tree, formatted_rows)

    def clear_filters():
        user_var.set("ALL")
        action_entry.delete(0, tk.END)
        date_entry.delete(0, tk.END)
        limit_var.set("200")
        refresh()

    def export_csv():
        rows = [tree.item(i)["values"] for i in tree.get_children()]
        if not rows:
            show_warning("Empty Table", "No log rows are available to export.")
            return

        fname = filedialog.asksaveasfilename(
            parent=parent,
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
            initialfile=f"activity_audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not fname:
            return

        try:
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(heads)
                writer.writerows(rows)
            log_action("ADMIN", admin_id, "ACTIVITY_LOG_EXPORTED", f"Exported {len(rows)} logs to {fname}")
            show_success("Export Complete", f"Audit logs saved to:\n{fname}")
        except Exception as e:
            show_error("Export Error", str(e))

    def clear_old_logs():
        if not ask_confirm(
            "Purge Historic Logs",
            "Permanently delete all audit entries older than 30 days?\n\nThis maintenance operation cannot be undone."
        ):
            return

        run_query("DELETE FROM activity_logs WHERE timestamp < datetime('now', '-30 days')")
        log_action("ADMIN", admin_id, "ACTIVITY_LOG_CLEANED", "Purged logs older than 30 days")
        show_success("Purge Complete", "Audit log entries older than 30 days have been cleared.")
        refresh()

    user_combo.bind("<<ComboboxSelected>>", lambda e: refresh())
    limit_combo.bind("<<ComboboxSelected>>", lambda e: refresh())
    action_entry.bind("<Return>", lambda e: refresh())
    date_entry.bind("<Return>", lambda e: refresh())

    refresh()