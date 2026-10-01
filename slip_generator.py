# ============================================================
# slip_generator.py
# Printable Library Issue / Return Slip.
# Shows a formatted slip in a Toplevel window.
# Buttons: Print (OS dialog) + Save as TXT.
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from db import get_one
from notification_config import get_library_name
from ui_helpers import COLORS, FONTS, primary_button, success_button, neutral_button


# ------------------------------------------------------------
# Fetch all slip data for a given issue_id
# Returns a dictionary, or None if not found
# ------------------------------------------------------------
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
        "book_id", "book_title", "author_name",
    ]
    return dict(zip(keys, row))


# ------------------------------------------------------------
# Format slip as plain text (also used for saving to file)
# ------------------------------------------------------------
def format_slip_text(data):
    library = get_library_name()
    line = "=" * 56
    dash = "-" * 56

    def row(label, value):
        return f"  {label:<18}: {value if value not in (None, '') else '-'}"

    parts = [
        line,
        f"  {library.upper()}",
        "  LIBRARY ISSUE / RETURN SLIP",
        line,
        "",
        "  TRANSACTION DETAILS",
        dash,
        row("Transaction ID", f"#{data['issue_id']}"),
        row("Status",         data['status']),
        row("Issue Date",     data['issue_date']),
        row("Due Date",       data['due_date']),
        row("Return Date",    data['return_date']),
        row("Overdue Days",   data['overdue_days']),
        "",
        "  MEMBER DETAILS",
        dash,
        row("Member ID",      f"#{data['member_id']}"),
        row("Name",           data['member_name']),
        row("Phone",          data['member_phone']),
        row("Email",          data['member_email']),
        "",
        "  BOOK DETAILS",
        dash,
        row("Book ID",        f"#{data['book_id']}"),
        row("Title",          data['book_title']),
        row("Author",         data['author_name']),
        "",
        "  FINE DETAILS",
        dash,
        row("Fine Amount",    f"Rs {float(data['fine_amount'] or 0):.2f}"),
        row("Fine Status",    data['fine_status'] or "NONE"),
        "",
        line,
        f"  Printed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        line,
        "",
        "  Signature (Librarian) : _______________________",
        "",
        "  Signature (Member)    : _______________________",
        "",
    ]
    return "\n".join(parts)


# ------------------------------------------------------------
# Show slip in a Toplevel window
# ------------------------------------------------------------
def show_slip_window(parent, issue_id):
    data = fetch_slip_data(issue_id)
    if not data:
        messagebox.showerror("Error", f"Issue #{issue_id} not found.")
        return

    text_content = format_slip_text(data)

    win = tk.Toplevel(parent)
    win.title(f"Issue / Return Slip - #{issue_id}")
    win.geometry("720x680")
    win.configure(bg=COLORS["bg"])

    # Header
    tk.Label(
        win,
        text=f"Library Slip - Transaction #{issue_id}",
        font=FONTS["h2"], bg=COLORS["primary"], fg="white", pady=12
    ).pack(fill="x")

    # Slip body (monospace so alignment works)
    body = tk.Frame(win, bg="white", relief="solid", bd=1)
    body.pack(fill="both", expand=True, padx=15, pady=10)

    text_widget = tk.Text(
        body, wrap="none", font=("Consolas", 11),
        bg="white", fg="#1a1a1a", relief="flat", padx=15, pady=10
    )
    text_widget.insert("1.0", text_content)
    text_widget.config(state="disabled")

    ysb = ttk.Scrollbar(body, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=ysb.set)

    text_widget.pack(side="left", fill="both", expand=True)
    ysb.pack(side="right", fill="y")

    # Buttons
    btn_row = tk.Frame(win, bg=COLORS["bg"])
    btn_row.pack(pady=10)

    def do_print():
        """Save to a temp file and ask OS to print it."""
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

            system = platform.system()
            if system == "Windows":
                os.startfile(path, "print")
            elif system == "Darwin":   # macOS
                subprocess.run(["lp", path])
            else:                       # Linux
                subprocess.run(["lp", path])

            messagebox.showinfo(
                "Print",
                "Slip sent to the default printer.\n\n"
                f"(File: {path})"
            )
        except Exception as e:
            messagebox.showerror("Print Error", str(e))

    def do_save():
        try:
            fname = filedialog.asksaveasfilename(
                parent=win, defaultextension=".txt",
                filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
                initialfile=f"slip_issue_{issue_id}.txt"
            )
            if not fname:
                return
            with open(fname, "w", encoding="utf-8") as f:
                f.write(text_content)
            messagebox.showinfo("Saved", f"Slip saved to:\n{fname}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    success_button(btn_row, "Print",        do_print, width=12).grid(row=0, column=0, padx=5)
    primary_button(btn_row, "Save as TXT",  do_save,  width=14).grid(row=0, column=1, padx=5)
    neutral_button(btn_row, "Close",        win.destroy, width=10).grid(row=0, column=2, padx=5)


# ------------------------------------------------------------
# Standalone test — asks for issue ID on command line
# ------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        iid = int(sys.argv[1])
        root = tk.Tk()
        root.withdraw()
        show_slip_window(root, iid)
        root.mainloop()
    else:
        print("Usage: python slip_generator.py <issue_id>")
        print("Example: python slip_generator.py 1")