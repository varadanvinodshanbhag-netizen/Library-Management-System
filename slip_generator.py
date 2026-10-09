# ============================================================
# slip_generator.py
# Printable Library Circulation Transaction Slip.
# Generates a formatted monospace receipt for book issue/return events.
# Provides OS native printing and text file export capabilities.
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from db import get_one
from notification_config import get_library_name
from ui_helpers import (
    COLORS, FONTS, configure_styles,
    primary_button, success_button, neutral_button
)


def fetch_slip_data(issue_id):
    row = get_one("""
        SELECT
            ir.issue_id,
            ir.issue_date,
            ir.due_date,
            COALESCE(ir.actual_return_date, ir.return_date) AS return_date,
            ir.overdue_days,
            ir.fine_amount,
            ir.fine_status,
            ir.status,
            m.member_id, m.name, m.phone, m.email,
            COALESCE(m.card_id, '-'), COALESCE(m.dept, '-'), COALESCE(m.member_type, 'STUDENT'),
            b.book_id, b.title,
            a.author_name
        FROM issue_return ir
        JOIN members  m ON ir.member_id = m.member_id
        JOIN books    b ON ir.book_id   = b.book_id
        JOIN authors  a ON b.author_id  = a.author_id
        WHERE ir.issue_id = ?
    """, (issue_id,))

    if not row:
        return None

    keys = [
        "issue_id", "issue_date", "due_date", "return_date",
        "overdue_days", "fine_amount", "fine_status", "status",
        "member_id", "member_name", "member_phone", "member_email",
        "card_id", "dept", "member_type",
        "book_id", "book_title", "author_name",
    ]
    return dict(zip(keys, row))


def format_slip_text(data):
    institution = "R. N. S. RURAL POLYTECHNIC"
    dept = "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING"
    library = get_library_name()
    line = "=" * 60
    dash = "-" * 60

    def row(label, value):
        val_str = str(value) if value not in (None, "") else "None / Nil"
        return f"  {label:<20}: {val_str}"

    parts = [
        line,
        f"  {institution}",
        f"  {dept}",
        f"  {library.upper()}",
        "  OFFICIAL CIRCULATION TRANSACTION SLIP",
        line,
        "",
        "  [1] TRANSACTION DETAILS",
        dash,
        row("Transaction Ref",   f"#{data['issue_id']}"),
        row("Circulation Status", data['status']),
        row("Date of Issue",     data['issue_date']),
        row("Due Date",          data['due_date']),
        row("Return Date",       data['return_date']),
        row("Overdue Duration",  f"{data['overdue_days'] or 0} day(s)"),
        "",
        "  [2] BORROWER DETAILS",
        dash,
        row("Member ID",         f"#{data['member_id']}"),
        row("Library Card ID",   data['card_id']),
        row("Department",        data['dept']),
        row("Member Category",   data['member_type']),
        row("Student/Member Name", data['member_name']),
        row("Contact Phone",     data['member_phone']),
        row("Registered Email",  data['member_email']),
        "",
        "  [3] ITEM PARTICULARS",
        dash,
        row("Book Accession ID",f"#{data['book_id']}"),
        row("Catalog Title",    data['book_title']),
        row("Author",           data['author_name']),
        "",
        "  [4] PENALTY ASSESSMENT",
        dash,
        row("Assessed Fine",    f"Rs {float(data['fine_amount'] or 0):.2f}"),
        row("Payment Status",   data['fine_status'] or "NONE"),
        "",
        line,
        f"  Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        line,
        "",
        "  Librarian Signature: ____________________________",
        "",
        "  Borrower Signature : ____________________________",
        "",
        "  Notice: Retain this slip as proof of circulation.",
        line,
    ]
    return "\n".join(parts)


def show_slip_window(parent, issue_id):
    data = fetch_slip_data(issue_id)
    if not data:
        messagebox.showerror("Error", f"Transaction loan #{issue_id} not found in database.")
        return

    text_content = format_slip_text(data)

    win = tk.Toplevel(parent)
    win.title(f"Circulation Receipt - Transaction #{issue_id}")
    win.geometry("680x700")
    win.configure(bg=COLORS["bg"])

    # Center to parent
    win.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    x = max(0, px + (pw - 680) // 2)
    y = max(0, py + (ph - 700) // 2)
    win.geometry(f"680x700+{x}+{y}")

    configure_styles()

    # Header
    header = tk.Frame(win, bg=COLORS["primary_dark"], height=56)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text=f"📄  Official Library Circulation Slip  [Ref: #{issue_id}]",
        font=FONTS["h3"],
        bg=COLORS["primary_dark"],
        fg="white"
    ).pack(expand=True)

    # Monospace Text Viewer Card
    body_card = tk.Frame(win, bg=COLORS["card"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
    body_card.pack(fill="both", expand=True, padx=20, pady=(12, 10))

    text_widget = tk.Text(
        body_card,
        wrap="none",
        font=FONTS["mono"],
        bg="#fcfdfe",
        fg="#0f172a",
        relief="flat",
        padx=18,
        pady=14
    )
    text_widget.insert("1.0", text_content)
    text_widget.config(state="disabled")

    ysb = ttk.Scrollbar(body_card, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=ysb.set)

    text_widget.pack(side="left", fill="both", expand=True)
    ysb.pack(side="right", fill="y")

    # Action Toolbar
    toolbar = tk.Frame(win, bg=COLORS["bg"])
    toolbar.pack(pady=(0, 14))

    def do_print():
        try:
            import tempfile
            import os
            import platform
            import subprocess

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(text_content)
                path = f.name

            sys_os = platform.system()
            if sys_os == "Windows":
                os.startfile(path, "print")
            elif sys_os == "Darwin":
                subprocess.run(["lp", path])
            else:
                subprocess.run(["lp", path])

            messagebox.showinfo("Print Queue", f"Slip sent to default printer.\n\nFile reference: {path}")
        except Exception as e:
            messagebox.showerror("Print Error", str(e))

    def do_save():
        try:
            fname = filedialog.asksaveasfilename(
                parent=win,
                defaultextension=".txt",
                filetypes=[("Text File", "*.txt"), ("All Files", "*.*")],
                initialfile=f"library_slip_ref_{issue_id}_{datetime.now().strftime('%Y%m%d')}.txt"
            )
            if not fname:
                return
            with open(fname, "w", encoding="utf-8") as f:
                f.write(text_content)
            messagebox.showinfo("Receipt Saved", f"Transaction slip successfully exported to:\n{fname}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    success_button(toolbar, "🖨️  Print Physical Slip", do_print, width=20).grid(row=0, column=0, padx=6)
    primary_button(toolbar, "💾  Export as Text",      do_save,  width=18).grid(row=0, column=1, padx=6)
    neutral_button(toolbar, "✕  Close Window",        win.destroy, width=15).grid(row=0, column=2, padx=6)