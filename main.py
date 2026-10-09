# ============================================================
# main.py
# Application Entry Point & Primary Window Controller
# - Role Selection Screen (Admin vs Member)
# - Admin Authentication Window
# - Admin Master Workspace (Sidebar + Responsive Content Panel)
# Optimized for 720p/1080p presentation screens.
# ============================================================

import tkinter as tk
from tkinter import messagebox

from db import setup_database, get_one, run_query
from auth import (
    ensure_default_admin,
    migrate_plain_admin_passwords,
    verify_password,
)

from ui_helpers import (
    COLORS, FONTS, PAD, configure_styles, center_window,
    primary_button, success_button, neutral_button, danger_button,
    styled_entry, load_photo,
    show_warning, show_error
)
from activity_log import log_action

# ---- Admin Screen Modules ----
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

# ---- Member Screen Modules ----
from member_login import show_member_login_window
from member_dashboard import show_member_window


# Scaled down to fit comfortably inside 1280x720 display with Windows taskbar
WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 640


# ============================================================
# 1. ROLE CHOOSER WINDOW
# ============================================================
def show_role_chooser():
    root = tk.Tk()
    root.title("Library Management System - Portal Selector")
    root.geometry("480x490")
    center_window(root, 480, 490)
    root.configure(bg=COLORS["bg"])
    root.resizable(False, False)

    configure_styles()

    # ---- Header Band ----
    header = tk.Frame(root, bg=COLORS["card"], height=60, highlightbackground=COLORS["border"], highlightthickness=1)
    header.pack(fill="x")
    header.pack_propagate(False)

    h_inner = tk.Frame(header, bg=COLORS["card"])
    h_inner.pack(expand=True)

    tk.Label(
        h_inner,
        text="📚  LIBRARY MANAGEMENT SYSTEM",
        font=("Segoe UI", 13, "bold"),
        bg=COLORS["card"],
        fg=COLORS["primary"]
    ).pack()

    tk.Label(
        h_inner,
        text="RNS Rural Polytechnic  •  DSP Mini Project",
        font=FONTS["small"],
        bg=COLORS["card"],
        fg=COLORS["text_muted"]
    ).pack(pady=(1, 0))

    # ---- Aesthetic Hook Portal Card ----
    card_shell = tk.Frame(
        root, bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    card_shell.pack(padx=32, pady=(12, 8), fill="x")

    # Left vertical 4px hook indicator
    hook_bar = tk.Frame(card_shell, bg=COLORS["primary"], width=4)
    hook_bar.pack(side="left", fill="y")

    card_body = tk.Frame(card_shell, bg=COLORS["card"])
    card_body.pack(side="left", fill="both", expand=True, padx=20, pady=12)

    # Campus / Student Photo Preview (Fail-safe)
    photo_loaded = False
    try:
        img = load_photo(size=(130, 74), variant="thumb", master=root)
        if img:
            img_box = tk.Frame(card_body, bg=COLORS["card"], highlightbackground=COLORS["border"], highlightthickness=1)
            img_box.pack(pady=(0, 8))
            img_lbl = tk.Label(img_box, image=img, bg=COLORS["card"], bd=0)
            img_lbl.image = img
            img_lbl.pack()
            photo_loaded = True
    except Exception:
        photo_loaded = False

    if not photo_loaded:
        badge = tk.Frame(card_body, bg=COLORS["primary_subtle"], height=48)
        badge.pack(fill="x", pady=(0, 8))
        tk.Label(
            badge, text="🏛️  RNS Rural Polytechnic",
            font=FONTS["h3"], bg=COLORS["primary_subtle"], fg=COLORS["primary"]
        ).pack(expand=True)

    tk.Label(
        card_body,
        text="Select your access portal to continue:",
        font=FONTS["body_b"],
        bg=COLORS["card"],
        fg=COLORS["text"]
    ).pack(pady=(0, 10))

    # ---- Portal Selection Navigation ----
    def go_admin():
        root.destroy()
        show_login_window()

    def go_member():
        root.destroy()
        show_member_login_window(
            on_success=handle_member_login,
            on_back=show_role_chooser
        )

    admin_btn = primary_button(card_body, "👤   ADMINISTRATOR PORTAL", go_admin, width=28)
    admin_btn.config(font=("Segoe UI", 10, "bold"), pady=7)
    admin_btn.pack(pady=4, fill="x")

    member_btn = success_button(card_body, "🎓   STUDENT / MEMBER PORTAL", go_member, width=28)
    member_btn.config(font=("Segoe UI", 10, "bold"), pady=7)
    member_btn.pack(pady=4, fill="x")

    exit_btn = neutral_button(card_body, "✕   Exit Application", root.destroy, width=28)
    exit_btn.config(font=FONTS["body_b"], pady=5)
    exit_btn.pack(pady=(6, 2), fill="x")

    # ---- Footer ----
    tk.Label(
        root,
        text="Built with Python + Tkinter + SQLite  |  Varadan Vinod Shanbhag",
        font=FONTS["caption"],
        bg=COLORS["bg"],
        fg=COLORS["text_muted"]
    ).pack(side="bottom", pady=8)

    root.mainloop()


def handle_member_login(member_id, member_name):
    show_member_window(
        member_id, member_name,
        on_logout=show_role_chooser
    )


# ============================================================
# 2. ADMIN LOGIN WINDOW
# ============================================================
def show_login_window():
    login = tk.Tk()
    login.title("Library Management System - Administrator Sign In")
    login.geometry("420x420")
    center_window(login, 420, 420)
    login.configure(bg=COLORS["bg"])
    login.resizable(False, False)

    configure_styles()

    # Header
    header = tk.Frame(login, bg=COLORS["card"], height=58, highlightbackground=COLORS["border"], highlightthickness=1)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header, text="🔐  ADMINISTRATOR SIGN IN",
        font=("Segoe UI", 12, "bold"),
        bg=COLORS["card"], fg=COLORS["primary"]
    ).pack(expand=True)

    # Login card
    card = tk.Frame(
        login, bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    card.pack(padx=32, pady=(16, 12), fill="x")

    inner = tk.Frame(card, bg=COLORS["card"])
    inner.pack(padx=20, pady=16, fill="x")

    tk.Label(
        inner, text="Username",
        font=FONTS["small_b"], bg=COLORS["card"], fg=COLORS["text_secondary"]
    ).pack(anchor="w", pady=(0, 2))
    username_entry = styled_entry(inner, width=28)
    username_entry.pack(ipady=4, fill="x")

    tk.Label(
        inner, text="Password",
        font=FONTS["small_b"], bg=COLORS["card"], fg=COLORS["text_secondary"]
    ).pack(anchor="w", pady=(10, 2))
    password_entry = styled_entry(inner, width=28, show="•")
    password_entry.pack(ipady=4, fill="x")

    err_lbl = tk.Label(
        inner, text="", font=FONTS["caption"],
        bg=COLORS["card"], fg=COLORS["danger"]
    )
    err_lbl.pack(anchor="w", pady=(4, 0))

    username_entry.focus_set()

    def try_login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:
            err_lbl.config(text="⚠️ Please enter both username and password.")
            return

        row = get_one(
            "SELECT user_id, password_hash, role, is_active FROM users WHERE username = ?",
            (username,)
        )

        if row is None or not row[3]:
            err_lbl.config(text="❌ Invalid credentials or account deactivated.")
            password_entry.delete(0, tk.END)
            return

        if not verify_password(password, row[1]):
            err_lbl.config(text="❌ Invalid credentials. Please try again.")
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
    username_entry.bind("<Return>", lambda e: password_entry.focus_set())

    # Buttons
    btn_row = tk.Frame(login, bg=COLORS["bg"])
    btn_row.pack(padx=32, fill="x")

    login_btn = primary_button(btn_row, "SIGN IN", try_login, width=15)
    login_btn.config(font=("Segoe UI", 10, "bold"), pady=7)
    login_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

    def go_back():
        login.destroy()
        show_role_chooser()

    back_btn = neutral_button(btn_row, "BACK", go_back, width=12)
    back_btn.config(font=FONTS["body_b"], pady=7)
    back_btn.pack(side="right", expand=True, fill="x", padx=(4, 0))

    tk.Label(
        login,
        text="Default admin credentials: admin / admin123",
        font=FONTS["caption"],
        bg=COLORS["bg"],
        fg=COLORS["text_muted"]
    ).pack(pady=(12, 0))

    login.mainloop()


# ============================================================
# 3. ADMIN MASTER WORKSPACE (SIDEBAR + CONTENT)
# ============================================================
def show_main_window(user_id, role):
    main = tk.Tk()
    main.title("Library Management System - Administrator Workspace")
    main.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    center_window(main, WINDOW_WIDTH, WINDOW_HEIGHT)
    main.configure(bg=COLORS["bg"])
    main.minsize(1050, 580)

    configure_styles()

    # ---- Top Navigation Bar ----
    navbar = tk.Frame(main, bg="#ffffff", height=48, highlightbackground=COLORS["border"], highlightthickness=1)
    navbar.pack(fill="x")
    navbar.pack_propagate(False)

    brand_box = tk.Frame(navbar, bg="#ffffff")
    brand_box.pack(side="left", padx=16)

    tk.Label(
        brand_box,
        text="📚  LIBRARY MANAGEMENT SYSTEM",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        fg=COLORS["primary"]
    ).pack(side="left")

    tk.Label(
        brand_box,
        text=" |  RNS Rural Polytechnic",
        font=FONTS["small"],
        bg="#ffffff",
        fg=COLORS["text_muted"]
    ).pack(side="left")

    user_pill = tk.Frame(
        navbar, bg=COLORS["primary_subtle"],
        highlightbackground="#c7d2fe",
        highlightthickness=1
    )
    user_pill.pack(side="right", padx=16, pady=7)

    tk.Label(
        user_pill,
        text=f"  👤 Administrator (ID: #{user_id})  ",
        font=FONTS["small_b"],
        bg=COLORS["primary_subtle"],
        fg=COLORS["primary_dark"],
        pady=2
    ).pack()

    # ---- Body Layout ----
    body = tk.Frame(main, bg=COLORS["bg"])
    body.pack(fill="both", expand=True)

    # Sidebar (Light Aesthetic with border)
    sidebar = tk.Frame(body, bg=COLORS["sidebar"], width=214,
                       highlightbackground=COLORS["sidebar_border"], highlightthickness=1)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    sb_header = tk.Frame(sidebar, bg=COLORS["card_alt"], height=32)
    sb_header.pack(fill="x")
    sb_header.pack_propagate(False)
    tk.Label(
        sb_header, text="CORE MODULES",
        font=FONTS["caption"],
        bg=COLORS["card_alt"],
        fg=COLORS["text_muted"]
    ).pack(expand=True)

    content = tk.Frame(body, bg=COLORS["card"])
    content.pack(side="left", fill="both", expand=True)

    def clear_content():
        for w in content.winfo_children():
            w.destroy()

    # ---- Navigation handlers ----
    def nav_books():           clear_content(); show_books_screen(content)
    def nav_members():         clear_content(); show_members_screen(content)
    def nav_issue():           clear_content(); show_issue_screen(content, admin_id=user_id)
    def nav_search():          clear_content(); show_search_screen(content)
    def nav_member_accounts(): clear_content(); show_member_accounts_screen(content, admin_id=user_id)
    def nav_fines():           clear_content(); show_fines_screen(content, admin_id=user_id)
    def nav_extensions():      clear_content(); show_extensions_screen(content, admin_id=user_id)
    def nav_reports():         clear_content(); show_reports_screen(content, admin_id=user_id)
    def nav_magazines():       clear_content(); show_magazines_screen(content, admin_id=user_id)
    def nav_newspapers():      clear_content(); show_newspapers_screen(content, admin_id=user_id)
    def nav_settings():        clear_content(); show_settings_screen(content, admin_id=user_id)
    def nav_activity_log():    clear_content(); show_activity_log_screen(content, admin_id=user_id)

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
        if key in routes:
            for b_ref, hook_ref, b_key in nav_buttons:
                if b_key == key:
                    hook_ref.config(bg=COLORS["sidebar_active_hook"])
                    b_ref.config(bg=COLORS["sidebar_active_bg"], fg=COLORS["sidebar_active_fg"], font=FONTS["nav_b"])
                else:
                    hook_ref.config(bg=COLORS["sidebar"])
                    b_ref.config(bg=COLORS["sidebar"], fg=COLORS["sidebar_text"], font=FONTS["nav"])
            routes[key]()

    def go_home():
        clear_content()
        for b_ref, hook_ref, b_key in nav_buttons:
            if b_key == "home":
                hook_ref.config(bg=COLORS["sidebar_active_hook"])
                b_ref.config(bg=COLORS["sidebar_active_bg"], fg=COLORS["sidebar_active_fg"], font=FONTS["nav_b"])
            else:
                hook_ref.config(bg=COLORS["sidebar"])
                b_ref.config(bg=COLORS["sidebar"], fg=COLORS["sidebar_text"], font=FONTS["nav"])
        show_dashboard(content, navigate=navigate, logout=do_logout)

    def do_logout():
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to sign out?"):
            log_action("ADMIN", user_id, "LOGOUT", "Admin logged out")
            main.destroy()
            show_role_chooser()

    nav_buttons = []

    def add_nav_btn(text, command, key):
        row = tk.Frame(sidebar, bg=COLORS["sidebar"], height=33)
        row.pack(fill="x")
        row.pack_propagate(False)

        # 4px vertical Hook Indicator
        hook = tk.Frame(row, bg=COLORS["sidebar"], width=4)
        hook.pack(side="left", fill="y")

        btn = tk.Button(
            row,
            text=text,
            command=lambda: navigate(key) if key != "home" else go_home(),
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_text"],
            font=FONTS["nav"],
            activebackground=COLORS["sidebar_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            anchor="w",
            padx=12,
            pady=4,
            cursor="hand2",
            bd=0,
            highlightthickness=0,
        )
        btn.pack(side="left", fill="both", expand=True)

        def on_enter(e):
            if btn.cget("bg") != COLORS["sidebar_active_bg"]:
                btn.config(bg=COLORS["sidebar_hover"], fg=COLORS["text"])

        def on_leave(e):
            if btn.cget("bg") != COLORS["sidebar_active_bg"]:
                btn.config(bg=COLORS["sidebar"], fg=COLORS["sidebar_text"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        nav_buttons.append((btn, hook, key))
        return btn

    add_nav_btn("🏠   Dashboard",         go_home,             "home")
    add_nav_btn("📚   Books",             nav_books,           "books")
    add_nav_btn("👥   Students & Members",nav_members,         "members")
    add_nav_btn("🔁   Issue & Return",    nav_issue,           "issue")
    add_nav_btn("🔍   Search & Sort",     nav_search,          "search")
    add_nav_btn("👤   Student Accounts",  nav_member_accounts, "member_accounts")
    add_nav_btn("💰   Fines",             nav_fines,           "fines")
    add_nav_btn("📩   Extensions",        nav_extensions,      "extensions")
    add_nav_btn("📊   Reports",           nav_reports,         "reports")
    add_nav_btn("📖   Magazines",         nav_magazines,       "magazines")
    add_nav_btn("📰   Newspapers",        nav_newspapers,      "newspapers")
    add_nav_btn("⚙️    Settings",          nav_settings,        "settings")
    add_nav_btn("🗒️    Activity Log",      nav_activity_log,    "activity_log")

    # Spacer
    tk.Frame(sidebar, bg=COLORS["sidebar"]).pack(fill="both", expand=True)

    logout_frame = tk.Frame(sidebar, bg=COLORS["sidebar"])
    logout_frame.pack(fill="x", side="bottom", padx=8, pady=8)

    logout_btn = tk.Button(
        logout_frame,
        text="🚪   Sign Out",
        command=do_logout,
        bg=COLORS["danger_light"],
        fg=COLORS["danger"],
        font=FONTS["body_b"],
        relief="flat",
        anchor="center",
        pady=6,
        cursor="hand2",
        bd=0,
        highlightthickness=0,
    )
    logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg=COLORS["danger"], fg="white"))
    logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg=COLORS["danger_light"], fg=COLORS["danger"]))
    logout_btn.pack(fill="x")

    go_home()
    main.mainloop()


# ============================================================
# 4. ENTRY POINT
# ============================================================
if __name__ == "__main__":
    setup_database()
    ensure_default_admin()
    migrate_plain_admin_passwords()
    show_role_chooser()