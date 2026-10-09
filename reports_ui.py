# ============================================================
# reports_ui.py
# Administrator Portal: Statistical Analysis & Reporting Engine.
# Action buttons placed directly adjacent to controls for immediate visibility.
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
    COLORS, FONTS, PAD, section_title, styled_entry,
    primary_button, success_button, neutral_button,
    populate_tree_with_striping, configure_styles, show_success, show_error, show_warning
)
from report_generator import REPORTS, export_to_csv


def show_reports_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(
        parent,
        "Statistical Reports & Analytics",
        "Generate audit, circulation, financial, and inventory reports with CSV export and printing"
    )

    # ---------- Report Selection & Action Toolbar (PACKED BEFORE TABLE) ----------
    ctrl_card = tk.Frame(parent, bg=COLORS["card_alt"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
    ctrl_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6), ipady=4)

    # Row 1: Selectors & Actions
    r1 = tk.Frame(ctrl_card, bg=COLORS["card_alt"])
    r1.pack(fill="x", padx=10, pady=3)

    tk.Label(r1, text=" Report:", bg=COLORS["card_alt"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]).pack(side="left", padx=(0, 4))

    report_var = tk.StringVar(value="All Books")
    report_names = list(REPORTS.keys())
    combo = ttk.Combobox(
        r1, textvariable=report_var, width=22,
        values=report_names, state="readonly"
    )
    combo.pack(side="left", padx=(0, 12))

    tk.Label(r1, text="Member ID:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(0, 4))
    member_entry = styled_entry(r1, width=8)
    member_entry.pack(side="left", ipady=2, padx=(0, 12))

    neutral_button(r1, "Generate", lambda: load_report(), width=10).pack(side="left", padx=2)
    success_button(r1, "📥 Export CSV", lambda: do_export_csv(), width=13).pack(side="left", padx=2)
    primary_button(r1, "🖨️ Print",      lambda: do_print(),      width=10).pack(side="left", padx=2)
    neutral_button(r1, "🔁 Refresh",    lambda: load_report(),   width=10).pack(side="left", padx=2)

    # Metric badge on the right
    info_lbl = tk.Label(r1, text="", bg=COLORS["card_alt"],
                        fg=COLORS["primary"], font=FONTS["small_b"])
    info_lbl.pack(side="right", padx=10)

    # ---------- Table Container (AT BOTTOM) ----------
    table_frame = tk.Frame(parent, bg=COLORS["card"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
    table_frame.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 8))

    tree = ttk.Treeview(table_frame, show="headings", height=9)
    configure_styles()

    tree.tag_configure("even", background=COLORS["card"])
    tree.tag_configure("odd",  background=COLORS["card_alt"])

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    state = {"headings": [], "rows": []}

    # ---------- Report Loader ----------
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
                    show_error("Validation Error", "Member ID must be a numeric integer.")
                    return
                from report_generator import report_member_borrowing
                headings, rows = report_member_borrowing(int(member_entry.get().strip()))
            else:
                headings, rows = REPORTS[name]()
        except Exception as e:
            show_error("Report Error", f"Failed to generate report:\n{e}")
            return

        cols = [f"c{i}" for i in range(len(headings))]
        tree["columns"] = cols
        for cid, h in zip(cols, headings):
            tree.heading(cid, text=h)
            calc_width = max(90, min(360, len(str(h)) * 12 + 25))
            tree.column(cid, width=calc_width, anchor="w")

        populate_tree_with_striping(tree, rows)

        state["headings"] = headings
        state["rows"] = rows
        info_lbl.config(text=f"📊 {len(rows)} record(s)")

    # ---------- Export to CSV ----------
    def do_export_csv():
        if not state["rows"]:
            show_warning("Empty Report", "There are no data rows to export.")
            return

        fname = filedialog.asksaveasfilename(
            parent=parent,
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
            initialfile=f"{report_var.get().replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not fname:
            return

        try:
            export_to_csv(state["headings"], state["rows"], fname)
            log_action("ADMIN", admin_id, "REPORT_EXPORTED", f"Exported '{report_var.get()}' to {fname}")
            show_success("Export Successful", f"Report saved successfully to:\n{fname}")
        except Exception as e:
            show_error("Export Error", str(e))

    # ---------- Formatted Printing ----------
    def do_print():
        if not state["headings"]:
            show_warning("No Data", "Please generate a report first.")
            return

        lines = [
            "=" * 72,
            "  R. N. S. RURAL POLYTECHNIC - LIBRARY MANAGEMENT SYSTEM",
            f"  REPORT: {report_var.get().upper()}",
            f"  Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Rows: {len(state['rows'])}",
            "=" * 72,
            ""
        ]

        widths = []
        for i, h in enumerate(state["headings"]):
            max_w = len(str(h))
            for r in state["rows"][:200]:
                max_w = max(max_w, len(str(r[i] if i < len(r) else "")))
            widths.append(min(max_w, 36))

        header_line = "  ".join(
            str(h).ljust(widths[i])[:widths[i]]
            for i, h in enumerate(state["headings"])
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        for r in state["rows"]:
            line_str = "  ".join(
                str(r[i] if i < len(r) else "").ljust(widths[i])[:widths[i]]
                for i in range(len(state["headings"]))
            )
            lines.append(line_str)

        lines.extend([
            "",
            "=" * 72,
            "  End of Report  •  Generated by Library Management System",
            "=" * 72,
        ])
        content_text = "\n".join(lines)

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(content_text)
                path = f.name

            system = platform.system()
            if system == "Windows":
                os.startfile(path, "print")
            elif system == "Darwin":
                subprocess.run(["lp", path])
            else:
                subprocess.run(["lp", path])

            log_action("ADMIN", admin_id, "REPORT_PRINTED", f"Printed report '{report_var.get()}'")
            show_success("Print Queue", "Report successfully dispatched to printer.")
        except Exception as e:
            show_error("Print Error", str(e))

    combo.bind("<<ComboboxSelected>>", lambda e: load_report())
    load_report()