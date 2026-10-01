# ============================================================
# main.py
# Entry point. Role chooser -> Admin or Member login.
# Admin main window: sidebar + dashboard + all modules.
# ============================================================

import tkinter as tk
from tkinter import messagebox

from db import setup_database, get_one, run_query
from auth import (
    ensure_default_admin,
    migrate_plain_admin_passwords,
    verify_password,
)

from ui_helpers import COLORS, FONTS
from activity_log import log_action

# ---- Admin modules ----
from book_ui import show_books_screen
from members_ui import show_members_screen
from issue_ui import show_issue_screen
from search_ui import show_search_screen
from admin_dashboard import show_dashboard
from member_accounts_ui import show_member_accounts_screen
from fines_ui import show_fines_screen
from extension_ui import show_extensions_screen
from reports_ui import show_reports_screen
from magazines_ui import show_magazines_screen
from newspapers_ui import show_newspapers_screen
from settings_ui import show_settings_screen
from activity_log_ui import show_activity_log_screen

# ---- Member modules ----
from member_login import show_member_login_window
from member_dashboard import show_member_window


WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 700


# ============================================================
# 1. ROLE CHOOSER
# ============================================================
def show_role_chooser():
    root = tk.Tk()
    root.title("Library Management System")
    root.geometry("480x420")
    root.configure(bg=COLORS["bg"])
    root.resizable(False, False)

    tk.Label(
        root, text="LIBRARY MANAGEMENT SYSTEM",
        font=("Segoe UI", 16, "bold"),
        bg=COLORS["primary"], fg="white", pady=20
    ).pack(fill="x")

    tk.Label(
        root, text="Choose your login type",
        font=FONTS["h3"], bg=COLORS["bg"], fg=COLORS["text"]
    ).pack(pady=(30, 20))

    def go_admin():
        root.destroy()
        show_login_window()

    def go_member():
        root.destroy()
        show_member_login_window(
            on_success=handle_member_login,
            on_back=show_role_chooser
        )

    tk.Button(
        root, text="👤  ADMIN LOGIN", width=24, height=2,
        font=FONTS["body_b"], bg=COLORS["primary"], fg="white",
        relief="flat", cursor="hand2", command=go_admin
    ).pack(pady=8)

    tk.Button(
        root, text="🎓  MEMBER LOGIN", width=24, height=2,
        font=FONTS["body_b"], bg=COLORS["success"], fg="white",
        relief="flat", cursor="hand2", command=go_member
    ).pack(pady=8)

    tk.Button(
        root, text="EXIT", width=24,
        font=FONTS["body"], bg="#e1e5ea", fg=COLORS["text"],
        relief="flat", cursor="hand2", command=root.destroy
    ).pack(pady=20)

    root.mainloop()


def handle_member_login(member_id, member_name):
    show_member_window(
        member_id, member_name,
        on_logout=show_role_chooser
    )


# ============================================================
# 2. ADMIN LOGIN
# ============================================================
def show_login_window():
    login = tk.Tk()
    login.title("Library Management System - Admin Login")
    login.geometry("440x400")
    login.configure(bg=COLORS["bg"])
    login.resizable(False, False)

    tk.Label(
        login, text="ADMIN LOGIN",
        font=("Segoe UI", 15, "bold"),
        bg=COLORS["primary"], fg="white", pady=14
    ).pack(fill="x")

    tk.Label(
        login, text="Library Management System",
        font=("Segoe UI", 11), bg=COLORS["bg"], fg=COLORS["text_muted"]
    ).pack(pady=(15, 0))

    card = tk.Frame(login, bg=COLORS["card"], relief="solid", bd=1)
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
            "SELECT user_id, password_hash, role, is_active FROM users WHERE username = ?",
            (username,)
        )

        if row is None or not row[3]:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            password_entry.delete(0, tk.END)
            return

        if not verify_password(password, row[1]):
            messagebox.showerror("Login Failed", "Invalid username or password.")
            password_entry.delete(0, tk.END)
            return

        run_query(
            "UPDATE users SET last_login = datetime('now') WHERE user_id = ?",
            (row[0],)
        )
        log_action("ADMIN", row[0], "LOGIN", f"Admin '{username}' logged in")

        login.destroy()
        show_main_window(row[0], row[2])

    password_entry.bind("<Return>", lambda e: try_login())

    btns = tk.Frame(login, bg=COLORS["bg"])
    btns.pack(pady=10)

    tk.Button(
        btns, text="LOGIN", width=14,
        font=FONTS["body_b"], bg=COLORS["primary"], fg="white",
        activebackground=COLORS["primary_dark"], activeforeground="white",
        relief="flat", cursor="hand2", command=try_login
    ).grid(row=0, column=0, padx=6)

    def go_back():
        login.destroy()
        show_role_chooser()

    tk.Button(
        btns, text="BACK", width=14,
        font=FONTS["body_b"], bg="#e1e5ea", fg=COLORS["text"],
        relief="flat", cursor="hand2", command=go_back
    ).grid(row=0, column=1, padx=6)

    login.mainloop()


# ============================================================
# 3. ADMIN MAIN WINDOW
# ============================================================
def show_main_window(user_id, role):
    main = tk.Tk()
    main.title("Library Management System - Admin")
    main.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    main.configure(bg=COLORS["bg"])

    # ---- Header ----
    header = tk.Frame(main, bg=COLORS["primary"], height=60)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header, text="LIBRARY MANAGEMENT SYSTEM",
        font=("Segoe UI", 16, "bold"),
        bg=COLORS["primary"], fg="white"
    ).pack(side="left", padx=20)

    tk.Label(
        header, text=f"Admin (ID {user_id})",
        font=FONTS["body"], bg=COLORS["primary"], fg="#cfd8e3"
    ).pack(side="right", padx=20)

    # ---- Body ----
    body = tk.Frame(main, bg=COLORS["bg"])
    body.pack(fill="both", expand=True)

    sidebar = tk.Frame(body, bg=COLORS["primary_dark"], width=210)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    content = tk.Frame(body, bg=COLORS["card"])
    content.pack(side="left", fill="both", expand=True)

    def clear_content():
        for w in content.winfo_children():
            w.destroy()

    # ---- Navigation callbacks ----
    def nav_books():
        clear_content(); show_books_screen(content)
    def nav_members():
        clear_content(); show_members_screen(content)
    def nav_issue():
        clear_content(); show_issue_screen(content)
    def nav_search():
        clear_content(); show_search_screen(content)
    def nav_member_accounts():
        clear_content(); show_member_accounts_screen(content, admin_id=user_id)
    def nav_fines():
        clear_content(); show_fines_screen(content, admin_id=user_id)
    def nav_extensions():
        clear_content(); show_extensions_screen(content, admin_id=user_id)
    def nav_reports():
        clear_content(); show_reports_screen(content, admin_id=user_id)
    def nav_magazines():
        clear_content(); show_magazines_screen(content, admin_id=user_id)
    def nav_newspapers():
        clear_content(); show_newspapers_screen(content, admin_id=user_id)
    def nav_settings():
        clear_content(); show_settings_screen(content, admin_id=user_id)
    def nav_activity_log():
        clear_content(); show_activity_log_screen(content, admin_id=user_id)

    def navigate(key):
        routes = {
            "books":           nav_books,
            "members":         nav_members,
            "issue":           nav_issue,
            "search":          nav_search,
            "member_accounts": nav_member_accounts,
            "fines":           nav_fines,
            "extensions":      nav_extensions,
            "reports":         nav_reports,
            "magazines":       nav_magazines,
            "newspapers":      nav_newspapers,
            "settings":        nav_settings,
            "activity_log":    nav_activity_log,
        }
        routes.get(key, lambda: None)()

    def go_home():
        clear_content()
        show_dashboard(content, navigate=navigate, logout=do_logout)

    def do_logout():
        if messagebox.askyesno("Logout", "Do you want to logout?"):
            log_action("ADMIN", user_id, "LOGOUT", "Admin logged out")
            main.destroy()
            show_role_chooser()

    # ---- Sidebar buttons ----
    def sidebar_btn(text, command):
        return tk.Button(
            sidebar, text=text, command=command,
            bg=COLORS["primary_dark"], fg="white",
            font=FONTS["body"], activebackground=COLORS["primary"],
            activeforeground="white", relief="flat",
            anchor="w", padx=18, pady=9, cursor="hand2"
        )

    sidebar_btn("🏠  Dashboard",         go_home).pack(fill="x")
    sidebar_btn("📚  Books",             nav_books).pack(fill="x")
    sidebar_btn("👥  Members",           nav_members).pack(fill="x")
    sidebar_btn("🔁  Issue / Return",    nav_issue).pack(fill="x")
    sidebar_btn("🔍  Search & Sort",     nav_search).pack(fill="x")
    sidebar_btn("👤  Member Accounts",   nav_member_accounts).pack(fill="x")
    sidebar_btn("💰  Fines",             nav_fines).pack(fill="x")
    sidebar_btn("📩  Extensions",        nav_extensions).pack(fill="x")
    sidebar_btn("📊  Reports",           nav_reports).pack(fill="x")
    sidebar_btn("📖  Magazines",         nav_magazines).pack(fill="x")
    sidebar_btn("📰  Newspapers",        nav_newspapers).pack(fill="x")
    sidebar_btn("⚙️   Settings",          nav_settings).pack(fill="x")
    sidebar_btn("🗒️   Activity Log",       nav_activity_log).pack(fill="x")

    tk.Frame(sidebar, bg=COLORS["primary_dark"], height=20).pack(fill="x")

    tk.Button(
        sidebar, text="🚪  Logout", command=do_logout,
        bg=COLORS["danger"], fg="white", font=FONTS["body_b"],
        relief="flat", anchor="w", padx=18, pady=10, cursor="hand2"
    ).pack(fill="x", side="bottom")

    go_home()
    main.mainloop()


# ============================================================
# 4. START
# ============================================================
if __name__ == "__main__":
    setup_database()
    ensure_default_admin()
    migrate_plain_admin_passwords()
    show_role_chooser()