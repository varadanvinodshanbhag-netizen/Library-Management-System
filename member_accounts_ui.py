# ============================================================
# member_accounts_ui.py
# Administrator Portal: Member Login Account Management.
# Action buttons placed directly adjacent to controls for immediate visibility.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from db import run_query, get_rows, get_one
from auth import hash_password
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_table, make_card, styled_entry,
    primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)


def show_member_accounts_screen(parent, admin_id=None):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(
        parent,
        "Student & Member Accounts",
        "Provision and manage portal access credentials for registered students and members"
    )

    # ---------- Summary Metrics Row ----------
    metrics_row = tk.Frame(parent, bg=COLORS["card"])
    metrics_row.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    def get_account_metrics():
        total_members = get_one("SELECT COUNT(*) FROM members")[0]
        active_accounts = get_one("SELECT COUNT(*) FROM member_accounts WHERE is_active = 1")[0]
        inactive_accounts = get_one("SELECT COUNT(*) FROM member_accounts WHERE is_active = 0")[0]
        no_account = total_members - (active_accounts + inactive_accounts)
        return total_members, active_accounts, no_account, inactive_accounts

    def render_metrics():
        for w in metrics_row.winfo_children():
            w.destroy()
        tot, act, none_cnt, inact = get_account_metrics()

        cards = [
            ("Total Students/Members", tot,      COLORS["primary"]),
            ("Active Accounts",       act,      COLORS["success"]),
            ("Pending Setup",         none_cnt, COLORS["accent"]),
            ("Disabled Accounts",     inact,    COLORS["danger"]),
        ]
        for i, (title, val, col) in enumerate(cards):
            c = make_card(metrics_row, title, val, color=col, width=160, height=66)
            c.grid(row=0, column=i, padx=3, pady=2, sticky="nsew")
            metrics_row.grid_columnconfigure(i, weight=1)

    # ---------- Filter Bar & Action Toolbar (PACKED BEFORE TABLE) ----------
    filter_card = tk.Frame(parent, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
    filter_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6), ipady=3)

    # Row 1: Search & Filter
    f_row1 = tk.Frame(filter_card, bg=COLORS["card_alt"])
    f_row1.pack(fill="x", padx=10, pady=(4, 2))

    tk.Label(f_row1, text=" State:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(0, 4))

    state_var = tk.StringVar(value="ALL")
    state_combo = ttk.Combobox(
        f_row1, textvariable=state_var, width=14,
        values=["ALL", "ACTIVE ONLY", "NO ACCOUNT", "INACTIVE ONLY"],
        state="readonly"
    )
    state_combo.pack(side="left", padx=(0, 14))

    tk.Label(f_row1, text="Search:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(0, 4))
    search_entry = styled_entry(f_row1, width=18)
    search_entry.pack(side="left", ipady=2, padx=(0, 14))

    # Action buttons right in toolbar before table
    success_button(f_row1, "➕ Provision Login", lambda: create_account(), width=16).pack(side="left", padx=2)
    primary_button(f_row1, "🔑 Reset Password",  lambda: reset_password(), width=15).pack(side="left", padx=2)
    primary_button(f_row1, "🔄 Toggle Status",   lambda: toggle_active(),  width=14).pack(side="left", padx=2)
    danger_button (f_row1, "🗑️ Delete",          lambda: delete_account(), width=10).pack(side="left", padx=2)
    neutral_button(f_row1, "🔁 Refresh",         lambda: refresh_table(),  width=10).pack(side="left", padx=2)

    # ---------- Table Setup (AT BOTTOM) ----------
    columns = ("member_id", "card_id", "name", "dept", "phone",
               "username", "status", "last_login")
    headings = ("ID", "Card ID", "Student Name", "Dept", "Phone",
                "Username", "Status", "Last Login")
    widths = (50, 80, 160, 65, 110, 110, 105, 140)

    tree = make_table(parent, columns, headings, widths, height=8)

    # ---------- Refresh & Data Operations ----------
    def refresh_table():
        sql = """
            SELECT m.member_id, m.card_id, m.name, m.dept, m.phone, m.email,
                   ma.username, ma.is_active, ma.last_login
            FROM members m
            LEFT JOIN member_accounts ma ON m.member_id = ma.member_id
            WHERE 1=1
        """
        params = []

        filt = state_var.get()
        if filt == "ACTIVE ONLY":
            sql += " AND ma.is_active = 1"
        elif filt == "NO ACCOUNT":
            sql += " AND ma.username IS NULL"
        elif filt == "INACTIVE ONLY":
            sql += " AND ma.is_active = 0"

        kw = search_entry.get().strip()
        if kw:
            sql += " AND (m.name LIKE ? OR m.card_id LIKE ? OR ma.username LIKE ? OR m.email LIKE ? OR m.dept LIKE ?)"
            params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%", f"%{kw}%", f"%{kw}%"])

        sql += " ORDER BY m.member_id DESC"

        raw_rows = get_rows(sql, tuple(params))
        formatted_rows = []
        for r in raw_rows:
            member_id, card_id, name, dept, phone, email, username, is_active, last_login = r
            if username is None:
                status = "⚪ No Account"
                uname = "-"
                login_ts = "-"
            else:
                status = "🟢 Active" if is_active else "🔴 Deactivated"
                uname = username
                login_ts = last_login or "Never"

            formatted_rows.append((
                f"#{member_id}",
                card_id or "-",
                name,
                dept or "-",
                phone or "-",
                uname,
                status,
                login_ts
            ))

        populate_tree_with_striping(tree, formatted_rows)
        render_metrics()

    state_combo.bind("<<ComboboxSelected>>", lambda e: refresh_table())
    search_entry.bind("<KeyRelease>", lambda e: refresh_table())

    def get_selected():
        sel = tree.selection()
        if not sel:
            show_warning("Selection Required", "Please select a member row from the table first.")
            return None
        return tree.item(sel[0])["values"]

    # ---------- Credential Actions ----------
    def create_account():
        values = get_selected()
        if not values:
            return

        member_id = int(str(values[0]).replace("#", ""))
        card_id_str = values[1]
        member_name = values[2]

        existing = get_one("SELECT account_id FROM member_accounts WHERE member_id = ?", (member_id,))
        if existing:
            show_error("Account Exists", f"'{member_name}' already possesses a registered login account.")
            return

        username = simpledialog.askstring(
            "New Portal Account",
            f"Provision member login for: {member_name} (Card: {card_id_str})\n\nEnter unique username:",
            parent=parent
        )
        if not username:
            return
        username = username.strip()
        if len(username) < 3:
            show_error("Validation Error", "Username must be at least 3 characters in length.")
            return

        if get_one("SELECT user_id FROM users WHERE username = ?", (username,)):
            show_error("Username Conflict", "This username is reserved by an administrator.")
            return
        if get_one("SELECT account_id FROM member_accounts WHERE username = ?", (username,)):
            show_error("Username Conflict", "This username is already taken by another member.")
            return

        password = simpledialog.askstring(
            "Set Member Password",
            f"Set initial password for '{username}':\n(Minimum 6 characters)",
            show="*",
            parent=parent
        )
        if not password or len(password) < 6:
            show_error("Security Error", "Password must be at least 6 characters.")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query(
            "INSERT INTO member_accounts (member_id, username, password_hash, is_active, created_at) "
            "VALUES (?, ?, ?, 1, ?)",
            (member_id, username, hash_password(password), now)
        )

        log_action(
            "ADMIN", admin_id, "MEMBER_ACCOUNT_CREATED",
            f"Provisioned portal account '{username}' for member #{member_id} ({card_id_str})"
        )
        show_success("Account Provisioned", f"Login created for '{member_name}'.\nUsername: {username}")
        refresh_table()

    def reset_password():
        values = get_selected()
        if not values:
            return

        member_id = int(str(values[0]).replace("#", ""))
        member_name = values[2]
        username = values[5]

        if username == "-":
            show_error("No Account", "This member does not have an active login account yet.")
            return

        new_pw = simpledialog.askstring(
            "Reset Password",
            f"Enter new password for member '{username}':\n(Minimum 6 characters)",
            show="*",
            parent=parent
        )
        if not new_pw or len(new_pw) < 6:
            show_error("Security Error", "Password must be at least 6 characters.")
            return

        run_query(
            "UPDATE member_accounts SET password_hash = ? WHERE member_id = ?",
            (hash_password(new_pw), member_id)
        )

        log_action(
            "ADMIN", admin_id, "MEMBER_PASSWORD_RESET",
            f"Reset password for '{username}' (member_id={member_id})"
        )
        show_success("Password Reset", f"Password successfully updated for '{member_name}'.")

    def toggle_active():
        values = get_selected()
        if not values:
            return

        member_id = int(str(values[0]).replace("#", ""))
        username = values[5]
        status = values[6]

        if username == "-":
            show_error("No Account", "This member does not have an active login account.")
            return

        if "Active" in status:
            if not ask_confirm("Confirm Deactivation", f"Deactivate portal access for '{username}'?"):
                return
            run_query("UPDATE member_accounts SET is_active = 0 WHERE member_id = ?", (member_id,))
            log_action("ADMIN", admin_id, "MEMBER_ACCOUNT_DEACTIVATED", f"Deactivated '{username}'")
            show_success("Deactivated", f"Account '{username}' deactivated.")
        else:
            run_query("UPDATE member_accounts SET is_active = 1 WHERE member_id = ?", (member_id,))
            log_action("ADMIN", admin_id, "MEMBER_ACCOUNT_ACTIVATED", f"Activated '{username}'")
            show_success("Activated", f"Account '{username}' is now active.")

        refresh_table()

    def delete_account():
        values = get_selected()
        if not values:
            return

        member_id = int(str(values[0]).replace("#", ""))
        member_name = values[2]
        username = values[5]

        if username == "-":
            show_error("No Account", "This member does not have a login account.")
            return

        if not ask_confirm(
            "Confirm Account Deletion",
            f"Delete portal login for '{username}'?\n(The underlying library member record will remain intact.)"
        ):
            return

        run_query("DELETE FROM member_accounts WHERE member_id = ?", (member_id,))
        log_action("ADMIN", admin_id, "MEMBER_ACCOUNT_DELETED", f"Deleted account '{username}'")
        show_success("Account Deleted", f"Portal credentials for '{member_name}' deleted.")
        refresh_table()

    refresh_table()