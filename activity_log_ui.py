# ============================================================
# activity_log_ui.py
# Admin screen: view and filter the activity log.
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from datetime import datetime

from db import get_rows
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, section_title, make_table,
    primary_button, success_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


def show_activity_log_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(parent, "Activity Log", "Track important actions in the system")

    # ---------- Filter bar ----------
    filter_frame = tk.Frame(parent, bg=COLORS["card"])
    filter_frame.pack(fill="x", padx=20, pady=(5, 10))

    tk.Label(filter_frame, text="User type:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=0, padx=(0, 5), pady=4)

    user_var = tk.StringVar(value="ALL")
    ttk.Combobox(
        filter_frame, textvariable=user_var, width=10,
        values=["ALL", "ADMIN", "MEMBER", "SYSTEM"], state="readonly"
    ).grid(row=0, column=1, padx=(0, 15))

    tk.Label(filter_frame, text="Action contains:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=2, padx=(0, 5), pady=4)
    action_entry = tk.Entry(filter_frame, width=20, font=FONTS["body"],
                            relief="solid", bd=1)
    action_entry.grid(row=0, column=3, padx=(0, 15), ipady=3)

    tk.Label(filter_frame, text="Date (YYYY-MM-DD):", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=4, padx=(0, 5), pady=4)
    date_entry = tk.Entry(filter_frame, width=14, font=FONTS["body"],
                          relief="solid", bd=1)
    date_entry.grid(row=0, column=5, padx=(0, 15), ipady=3)

    tk.Label(filter_frame, text="Limit:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=6, padx=(0, 5), pady=4)
    limit_var = tk.StringVar(value="200")
    ttk.Combobox(
        filter_frame, textvariable=limit_var, width=8,
        values=["50", "100", "200", "500", "1000"], state="readonly"
    ).grid(row=0, column=7, padx=(0, 10))

    # ---------- Bottom buttons (packed BEFORE table) ----------
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 12))

    # ---------- Table ----------
    cols = ("log_id", "time", "user_type", "user_id", "action", "details")
    heads = ("ID", "Timestamp", "User Type", "User ID", "Action", "Details")
    widths = (60, 150, 90, 70, 180, 500)

    tree = make_table(parent, cols, heads, widths, height=14)

    # ---------- Refresh ----------
    def refresh():
        for item in tree.get_children():
            tree.delete(item)

        sql = "SELECT log_id, timestamp, user_type, user_id, action, details FROM activity_logs WHERE 1=1"
        params = []

        if user_var.get() != "ALL":
            sql += " AND user_type = ?"
            params.append(user_var.get())

        if action_entry.get().strip():
            sql += " AND action LIKE ?"
            params.append(f"%{action_entry.get().strip()}%")

        if date_entry.get().strip():
            sql += " AND date(timestamp) = date(?)"
            params.append(date_entry.get().strip())

        try:
            limit = int(limit_var.get())
        except ValueError:
            limit = 200
        sql += f" ORDER BY log_id DESC LIMIT {limit}"

        rows = get_rows(sql, tuple(params))
        for r in rows:
            tree.insert("", tk.END, values=r)

    # ---------- Actions ----------
    def clear_filters():
        user_var.set("ALL")
        action_entry.delete(0, tk.END)
        date_entry.delete(0, tk.END)
        limit_var.set("200")
        refresh()

    def export_csv():
        rows = [tree.item(i)["values"] for i in tree.get_children()]
        if not rows:
            show_warning("Warning", "Nothing to export.")
            return

        fname = filedialog.asksaveasfilename(
            parent=parent, defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")],
            initialfile=f"activity_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not fname:
            return

        try:
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(heads)
                writer.writerows(rows)
            log_action("ADMIN", admin_id, "ACTIVITY_LOG_EXPORTED",
                       f"Exported {len(rows)} log entries to {fname}")
            show_success("Exported", f"Saved to:\n{fname}")
        except Exception as e:
            show_error("Export Error", str(e))

    def clear_old_logs():
        if not ask_confirm("Confirm",
                           "Delete all logs OLDER than 30 days?\n"
                           "This cannot be undone."):
            return
        from db import run_query
        run_query(
            "DELETE FROM activity_logs WHERE timestamp < datetime('now', '-30 days')"
        )
        log_action("ADMIN", admin_id, "ACTIVITY_LOG_CLEANED",
                   "Cleared logs older than 30 days")
        show_success("Done", "Old logs cleared.")
        refresh()

    # ---------- Buttons ----------
    primary_button(btn_row, "Apply Filters", refresh,        width=14).grid(row=0, column=0, padx=5)
    neutral_button(btn_row, "Clear Filters", clear_filters,  width=14).grid(row=0, column=1, padx=5)
    success_button(btn_row, "Export CSV",    export_csv,     width=14).grid(row=0, column=2, padx=5)
    primary_button(btn_row, "Cleanup 30d",   clear_old_logs, width=14).grid(row=0, column=3, padx=5)

    refresh()