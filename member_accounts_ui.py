# ============================================================
# member_accounts_ui.py
# Admin screen: manage member login accounts.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from db import run_query, get_rows, get_one
from auth import hash_password
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, section_title,
    primary_button, success_button, danger_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


def show_member_accounts_screen(parent, admin_id=None):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(
        parent,
        "Member Accounts",
        "Create and manage login accounts for library members"
    )

    # ---------- Bottom button row (packed FIRST so it stays at bottom) ----------
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 12))

    # ---------- Tip label (above buttons) ----------
    tk.Label(
        parent,
        text="Tip: A member must already exist in 'Members' before you can create a login account.",
        bg=COLORS["card"], fg=COLORS["text_muted"],
        font=FONTS["small"]
    ).pack(side="bottom", pady=(0, 6))

    # ---------- Table frame (fills remaining space) ----------
    table_frame = tk.Frame(parent, bg=COLORS["card"])
    table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

    columns  = ("member_id", "name", "phone", "email",
                "username", "status", "last_login")
    headings = ("Member ID", "Name", "Phone", "Email",
                "Username", "Status", "Last Login")
    widths   = (70, 150, 100, 180, 110, 80, 110)

    tree = ttk.Treeview(
        table_frame, columns=columns, show="headings", height=12
    )

    for col, head, w in zip(columns, headings, widths):
        tree.heading(col, text=head)
        tree.column(col, width=w, anchor="w")

    # Style
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "Treeview",
        background="white", foreground=COLORS["text"],
        rowheight=26, fieldbackground="white", font=FONTS["body"]
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["primary"], foreground="white",
        font=FONTS["body_b"]
    )
    style.map("Treeview.Heading", background=[("active", COLORS["primary_dark"])])

    # Scrollbars (vertical + horizontal)
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # ---------- Data functions ----------
    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)

        rows = get_rows("""
            SELECT m.member_id, m.name, m.phone, m.email,
                   ma.username, ma.is_active, ma.last_login
            FROM members m
            LEFT JOIN member_accounts ma ON m.member_id = ma.member_id
            ORDER BY m.member_id
        """)

        for r in rows:
            member_id, name, phone, email, username, is_active, last_login = r
            if username is None:
                status = "No Account"
                username = "-"
                last_login = "-"
            else:
                status = "Active" if is_active else "Inactive"
                last_login = last_login or "Never"

            tree.insert("", tk.END, values=(
                member_id, name, phone or "-", email or "-",
                username, status, last_login
            ))

    def get_selected_member():
        sel = tree.selection()
        if not sel:
            show_warning("Warning", "Select a member from the table first.")
            return None
        return tree.item(sel[0])["values"]

    # ---------- Actions ----------
    def create_account():
        values = get_selected_member()
        if not values:
            return

        member_id = values[0]
        member_name = values[1]

        existing = get_one(
            "SELECT account_id FROM member_accounts WHERE member_id = ?",
            (member_id,)
        )
        if existing:
            show_error("Error", f"'{member_name}' already has a login account.")
            return

        username = simpledialog.askstring(
            "New Member Account",
            f"Create login for: {member_name}\n\nEnter username:",
            parent=parent
        )
        if not username:
            return
        username = username.strip()
        if len(username) < 3:
            show_error("Error", "Username must be at least 3 characters.")
            return

        if get_one("SELECT user_id FROM users WHERE username = ?", (username,)):
            show_error("Error", "This username is already used by an admin.")
            return
        if get_one("SELECT account_id FROM member_accounts WHERE username = ?", (username,)):
            show_error("Error", "This username is already taken.")
            return

        password = simpledialog.askstring(
            "Set Password",
            f"Set initial password for '{username}':\n(min 6 characters)",
            show="*", parent=parent
        )
        if not password or len(password) < 6:
            show_error("Error", "Password must be at least 6 characters.")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "INSERT INTO member_accounts "
            "(member_id, username, password_hash, is_active, created_at) "
            "VALUES (?, ?, ?, 1, ?)",
            (member_id, username, hash_password(password), now)
        )

        log_action(
            "ADMIN", admin_id, "MEMBER_ACCOUNT_CREATED",
            f"Created account '{username}' for member_id={member_id}"
        )
        show_success("Success", f"Account created for '{member_name}'.\nUsername: {username}")
        refresh_table()

    def reset_password():
        values = get_selected_member()
        if not values:
            return

        member_id = values[0]
        member_name = values[1]
        username = values[4]

        if username == "-":
            show_error("Error", "This member has no account yet.")
            return

        new_pw = simpledialog.askstring(
            "Reset Password",
            f"Enter NEW password for '{username}':\n(min 6 characters)",
            show="*", parent=parent
        )
        if not new_pw or len(new_pw) < 6:
            show_error("Error", "Password must be at least 6 characters.")
            return

        run_query(
            "UPDATE member_accounts SET password_hash = ? WHERE member_id = ?",
            (hash_password(new_pw), member_id)
        )

        log_action(
            "ADMIN", admin_id, "MEMBER_PASSWORD_RESET",
            f"Reset password for '{username}' (member_id={member_id})"
        )
        show_success("Success", f"Password reset for '{member_name}'.")

    def toggle_active():
        values = get_selected_member()
        if not values:
            return

        member_id = values[0]
        member_name = values[1]
        username = values[4]
        status = values[5]

        if username == "-":
            show_error("Error", "This member has no account yet.")
            return

        if status == "Active":
            if not ask_confirm("Confirm", f"Deactivate '{username}'?"):
                return
            run_query(
                "UPDATE member_accounts SET is_active = 0 WHERE member_id = ?",
                (member_id,)
            )
            log_action(
                "ADMIN", admin_id, "MEMBER_ACCOUNT_DEACTIVATED",
                f"Deactivated '{username}' (member_id={member_id})"
            )
            show_success("Success", f"Account '{username}' deactivated.")
        else:
            run_query(
                "UPDATE member_accounts SET is_active = 1 WHERE member_id = ?",
                (member_id,)
            )
            log_action(
                "ADMIN", admin_id, "MEMBER_ACCOUNT_ACTIVATED",
                f"Activated '{username}' (member_id={member_id})"
            )
            show_success("Success", f"Account '{username}' activated.")

        refresh_table()

    def delete_account():
        values = get_selected_member()
        if not values:
            return

        member_id = values[0]
        member_name = values[1]
        username = values[4]

        if username == "-":
            show_error("Error", "This member has no account.")
            return

        if not ask_confirm("Confirm",
                           f"Delete login account '{username}'?\n"
                           f"(Member record itself will NOT be deleted.)"):
            return

        run_query("DELETE FROM member_accounts WHERE member_id = ?", (member_id,))
        log_action(
            "ADMIN", admin_id, "MEMBER_ACCOUNT_DELETED",
            f"Deleted account '{username}' for member_id={member_id}"
        )
        show_success("Success", f"Account deleted for '{member_name}'.")
        refresh_table()

    # ---------- Buttons (in the already-packed btn_row) ----------
    primary_button(btn_row, "Create Account",      create_account,   width=16).grid(row=0, column=0, padx=5)
    primary_button(btn_row, "Reset Password",      reset_password,   width=16).grid(row=0, column=1, padx=5)
    success_button(btn_row, "Activate/Deactivate", toggle_active,    width=18).grid(row=0, column=2, padx=5)
    danger_button (btn_row, "Delete Account",      delete_account,   width=16).grid(row=0, column=3, padx=5)
    neutral_button(btn_row, "Refresh",             refresh_table,    width=12).grid(row=0, column=4, padx=5)

    refresh_table()