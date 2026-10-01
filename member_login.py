# ============================================================
# member_login.py
# Separate login window for library members.
# Checks the member_accounts table (not users).
# ============================================================

import tkinter as tk
from tkinter import messagebox

from db import get_one, run_query
from auth import verify_password
from activity_log import log_action
from ui_helpers import COLORS, FONTS


def show_member_login_window(on_success=None, on_back=None):
    """
    on_success(member_id, member_name) : called after successful login
    on_back()                          : called if user wants to go back to admin login
    """
    win = tk.Tk()
    win.title("Library Management System - Member Login")
    win.geometry("440x400")
    win.configure(bg=COLORS["bg"])
    win.resizable(False, False)

    # ---- Header ----
    tk.Label(
        win,
        text="MEMBER LOGIN",
        font=("Segoe UI", 15, "bold"),
        bg=COLORS["success"], fg="white", pady=14
    ).pack(fill="x")

    tk.Label(
        win,
        text="Library Management System",
        font=("Segoe UI", 11), bg=COLORS["bg"], fg=COLORS["text_muted"]
    ).pack(pady=(15, 0))

    # ---- Card ----
    card = tk.Frame(win, bg=COLORS["card"], relief="solid", bd=1)
    card.pack(padx=30, pady=15, fill="x")

    tk.Label(card, text="Username", font=FONTS["body"],
             bg=COLORS["card"]).pack(anchor="w", padx=20, pady=(15, 2))
    username_entry = tk.Entry(card, width=26, font=FONTS["body"],
                              relief="solid", bd=1)
    username_entry.pack(padx=20, ipady=4)

    tk.Label(card, text="Password", font=FONTS["body"],
             bg=COLORS["card"]).pack(anchor="w", padx=20, pady=(12, 2))
    password_entry = tk.Entry(card, width=26, font=FONTS["body"],
                              show="*", relief="solid", bd=1)
    password_entry.pack(padx=20, ipady=4, pady=(0, 15))

    username_entry.focus_set()

    def try_login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if username == "" or password == "":
            messagebox.showwarning("Warning", "Please enter username and password.")
            return

        row = get_one(
            "SELECT account_id, member_id, password_hash, is_active "
            "FROM member_accounts WHERE username = ?",
            (username,)
        )

        if row is None:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            password_entry.delete(0, tk.END)
            return

        account_id, member_id, pw_hash, is_active = row

        if not is_active:
            messagebox.showerror(
                "Account Disabled",
                "Your account has been deactivated.\nPlease contact the librarian."
            )
            password_entry.delete(0, tk.END)
            return

        if not verify_password(password, pw_hash):
            messagebox.showerror("Login Failed", "Invalid username or password.")
            password_entry.delete(0, tk.END)
            return

        # Get member name for display
        mem = get_one("SELECT name FROM members WHERE member_id = ?", (member_id,))
        member_name = mem[0] if mem else "Member"

        # Update last_login
        run_query(
            "UPDATE member_accounts SET last_login = datetime('now') "
            "WHERE account_id = ?",
            (account_id,)
        )
        log_action(
            "MEMBER", member_id, "LOGIN",
            f"Member '{username}' (id={member_id}) logged in"
        )

        win.destroy()
        if on_success:
            on_success(member_id, member_name)

    password_entry.bind("<Return>", lambda e: try_login())

    # ---- Buttons ----
    btns = tk.Frame(win, bg=COLORS["bg"])
    btns.pack(pady=10)

    tk.Button(
        btns, text="LOGIN", width=14,
        font=FONTS["body_b"], bg=COLORS["success"], fg="white",
        activebackground="#21867a", activeforeground="white",
        relief="flat", cursor="hand2", command=try_login
    ).grid(row=0, column=0, padx=6)

    def go_back():
        win.destroy()
        if on_back:
            on_back()

    tk.Button(
        btns, text="BACK TO ADMIN", width=16,
        font=FONTS["body_b"], bg="#e1e5ea", fg=COLORS["text"],
        relief="flat", cursor="hand2", command=go_back
    ).grid(row=0, column=1, padx=6)

    tk.Label(
        win,
        text="If you don't have an account, ask the librarian to create one.",
        font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text_muted"]
    ).pack(pady=(10, 0))

    win.mainloop()