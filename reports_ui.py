# ============================================================
# reports_ui.py
# Admin Reports screen: choose report, view table, export CSV, print.
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import platform
import subprocess
import tempfile
from datetime import datetime

from db import get_rows
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, section_title,
    primary_button, success_button, neutral_button
)
from report_generator import REPORTS, export_to_csv


def show_reports_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(parent, "Reports", "View, print and export library reports")

    # ---- Top controls ----
    top = tk.Frame(parent, bg=COLORS["card"])
    top.pack(fill="x", padx=20, pady=(5, 10))

    tk.Label(top, text="Report:", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=0, padx=(0, 5))

    report_var = tk.StringVar(value="All Books")
    report_names = list(REPORTS.keys())
    combo = ttk.Combobox(
        top, textvariable=report_var, width=28,
        values=report_names, state="readonly"
    )
    combo.grid(row=0, column=1, padx=(0, 10))

    # Member ID filter (only used by Member Borrowing report)
    tk.Label(top, text="Member ID (optional):", bg=COLORS["card"],
             font=FONTS["body"]).grid(row=0, column=2, padx=(10, 5))
    member_entry = tk.Entry(top, width=8, font=FONTS["body"],
                            relief="solid", bd=1)
    member_entry.grid(row=0, column=3, ipady=3, padx=(0, 10))

    # ---- Info line ----
    info = tk.Label(parent, text="", bg=COLORS["card"],
                    fg=COLORS["text_muted"], font=FONTS["small"])
    info.pack(anchor="w", padx=20, pady=(0, 5))

    # ---- Bottom buttons (pack before table so they stay at bottom) ----
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 12))

    # ---- Table ----
    table_frame = tk.Frame(parent, bg=COLORS["card"])
    table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

    tree = ttk.Treeview(table_frame, show="headings", height=14)
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # Keep track of current report state for export/print
    state = {"headings": [], "rows": []}

    # ---- Load report ----
    def load_report():
        for col in tree["columns"]:
            tree.heading(col, text="")
        tree["columns"] = ()
        for item in tree.get_children():
            tree.delete(item)

        name = report_var.get()

        try:
            if name == "Member Borrowing" and member_entry.get().strip():
                if not member_entry.get().strip().isdigit():
                    messagebox.showerror("Error", "Member ID must be a number.")
                    return
                from report_generator import report_member_borrowing
                headings, rows = report_member_borrowing(
                    int(member_entry.get().strip())
                )
            else:
                headings, rows = REPORTS[name]()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load report:\n{e}")
            return

        # Configure columns
        cols = [f"c{i}" for i in range(len(headings))]
        tree["columns"] = cols
        for cid, h in zip(cols, headings):
            tree.heading(cid, text=h)
            # auto-width based on heading text length
            w = max(90, len(str(h)) * 12 + 20)
            tree.column(cid, width=w, anchor="w")

        for r in rows:
            tree.insert("", tk.END, values=r)

        state["headings"] = headings
        state["rows"] = rows
        info.config(text=f"{name}: {len(rows)} row(s)")

    # ---- Export CSV ----
    def do_export_csv():
        if not state["rows"]:
            messagebox.showinfo("Info", "No rows to export.")
            return
        fname = filedialog.asksaveasfilename(
            parent=parent, defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("All files", "*.*")],
            initialfile=f"{report_var.get().replace(' ', '_')}_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not fname:
            return
        try:
            export_to_csv(state["headings"], state["rows"], fname)
            log_action("ADMIN", admin_id, "REPORT_EXPORTED",
                       f"Report '{report_var.get()}' exported to {fname}")
            messagebox.showinfo("Exported", f"Saved to:\n{fname}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ---- Print ----
    def do_print():
        if not state["headings"]:
            messagebox.showinfo("Info", "Load a report first.")
            return

        # Build a plain-text version
        library = "Library Management System"
        lines = []
        lines.append("=" * 70)
        lines.append(f"  {library}")
        lines.append(f"  Report: {report_var.get()}")
        lines.append(f"  Printed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)
        lines.append("")

        widths = []
        for i, h in enumerate(state["headings"]):
            max_w = len(str(h))
            for r in state["rows"][:200]:  # cap for speed
                max_w = max(max_w, len(str(r[i] if i < len(r) else "")))
            widths.append(min(max_w, 40))

        header = "  ".join(
            str(h).ljust(widths[i])[:widths[i]]
            for i, h in enumerate(state["headings"])
        )
        lines.append(header)
        lines.append("-" * len(header))

        for r in state["rows"]:
            line = "  ".join(
                str(r[i] if i < len(r) else "").ljust(widths[i])[:widths[i]]
                for i in range(len(state["headings"]))
            )
            lines.append(line)

        text = "\n".join(lines)

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(text)
                path = f.name

            system = platform.system()
            if system == "Windows":
                os.startfile(path, "print")
            elif system == "Darwin":
                subprocess.run(["lp", path])
            else:
                subprocess.run(["lp", path])

            log_action("ADMIN", admin_id, "REPORT_PRINTED",
                       f"Report '{report_var.get()}' sent to printer")
            messagebox.showinfo("Print", "Report sent to the printer.")
        except Exception as e:
            messagebox.showerror("Print Error", str(e))

    # ---- Buttons ----
    primary_button(btn_row, "Load Report", load_report, width=14).grid(row=0, column=0, padx=5)
    success_button(btn_row, "Export CSV",  do_export_csv, width=14).grid(row=0, column=1, padx=5)
    primary_button(btn_row, "Print",       do_print,     width=10).grid(row=0, column=2, padx=5)
    neutral_button(btn_row, "Refresh",     load_report,  width=10).grid(row=0, column=3, padx=5)

    # Auto-load on change
    combo.bind("<<ComboboxSelected>>", lambda e: load_report())

    load_report()