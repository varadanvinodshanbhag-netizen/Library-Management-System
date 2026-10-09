# ============================================================
# member_login.py
# Member / Student Authentication Window.
# Authenticates against the member_accounts table with bcrypt verification.
# ============================================================

import tkinter as tk
from tkinter import messagebox

from db import get_one, run_query
from auth import verify_password
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, configure_styles, load_photo, styled_entry,
    success_button, neutral_button, show_warning, show_error
)


def show_member_login_window(on_success=None, on_back=None):
    """
    Renders the Student / Member Login window.
    on_success(member_id, member_name): invoked on valid credentials
    on_back(): returns to portal selector
    """
    win = tk.Tk()
    win.title("Library Management System - Student / Member Sign In")
    win.geometry("480x520")
    win.configure(bg=COLORS["bg"])
    win.resizable(False, False)

    # Center window
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - 480) // 2)
    y = max(0, (sh - 520) // 2 - 20)
    win.geometry(f"480x520+{x}+{y}")

    configure_styles()

    # ---- Header Band ----
    header = tk.Frame(win, bg=COLORS["card"], height=64, highlightbackground=COLORS["border"], highlightthickness=1)
    header.pack(fill="x")
    header.pack_propagate(False)

    h_inner = tk.Frame(header, bg=COLORS["card"])
    h_inner.pack(expand=True)

    tk.Label(
        h_inner, text="🎓  STUDENT & MEMBER SIGN IN",
        font=("Segoe UI", 13, "bold"),
        bg=COLORS["card"], fg=COLORS["success"]
    ).pack()
    tk.Label(
        h_inner, text="RNS Rural Polytechnic  •  Library Circulation",
        font=FONTS["small"],
        bg=COLORS["card"], fg=COLORS["text_muted"]
    ).pack(pady=(2, 0))

    # ---- College Photo Card / Header ----
    photo_box = tk.Frame(win, bg=COLORS["bg"])
    photo_box.pack(pady=(14, 0))

    try:
        img = load_photo(size=(110, 70), variant="small", master=win)
        if img:
            img_lbl = tk.Label(photo_box, image=img, bg=COLORS["bg"])
            img_lbl.image = img
            img_lbl.pack()
    except Exception:
        pass

    # ---- Login Card ----
    card = tk.Frame(
        win, bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    card.pack(padx=40, pady=(12, 14), fill="x")

    inner = tk.Frame(card, bg=COLORS["card"])
    inner.pack(padx=24, pady=18, fill="x")

    tk.Label(
        inner, text="Username or Library Card ID",
        font=FONTS["small_b"], bg=COLORS["card"], fg=COLORS["text_secondary"]
    ).pack(anchor="w", pady=(0, 4))
    username_entry = styled_entry(inner, width=28)
    username_entry.pack(ipady=5, fill="x")

    tk.Label(
        inner, text="Account Password",
        font=FONTS["small_b"], bg=COLORS["card"], fg=COLORS["text_secondary"]
    ).pack(anchor="w", pady=(12, 4))
    password_entry = styled_entry(inner, width=28, show="•")
    password_entry.pack(ipady=5, fill="x")

    # Inline feedback message
    err_lbl = tk.Label(
        inner, text="", font=FONTS["caption"],
        bg=COLORS["card"], fg=COLORS["danger"]
    )
    err_lbl.pack(anchor="w", pady=(6, 0))

    username_entry.focus_set()

    def try_login():
        login_input = username_entry.get().strip()
        password = password_entry.get().strip()

        if not login_input or not password:
            err_lbl.config(text="⚠️ Please enter both username/card ID and password.")
            return

        row = get_one("""
            SELECT ma.account_id, ma.member_id, ma.password_hash, ma.is_active, ma.username
            FROM member_accounts ma
            JOIN members m ON ma.member_id = m.member_id
            WHERE ma.username = ? OR UPPER(TRIM(m.card_id)) = UPPER(?)
        """, (login_input, login_input))

        if row is None:
            err_lbl.config(text="❌ Invalid username/Card ID or account not found.")
            password_entry.delete(0, tk.END)
            return

        account_id, member_id, pw_hash, is_active, uname = row

        if not is_active:
            err_lbl.config(text="⛔ Account disabled. Please contact the librarian.")
            password_entry.delete(0, tk.END)
            return

        if not verify_password(password, pw_hash):
            err_lbl.config(text="❌ Invalid credentials. Please try again.")
            password_entry.delete(0, tk.END)
            return

        mem = get_one("SELECT name FROM members WHERE member_id = ?", (member_id,))
        member_name = mem[0] if mem else "Member"

        run_query(
            "UPDATE member_accounts SET last_login = datetime('now') WHERE account_id = ?",
            (account_id,)
        )
        log_action("MEMBER", member_id, "LOGIN", f"Student '{uname}' (ID #{member_id}) logged in")

        win.destroy()
        if on_success:
            on_success(member_id, member_name)

    password_entry.bind("<Return>", lambda e: try_login())
    username_entry.bind("<Return>", lambda e: password_entry.focus_set())

    # Buttons
    btn_row = tk.Frame(win, bg=COLORS["bg"])
    btn_row.pack(padx=40, fill="x")

    login_btn = success_button(btn_row, "SIGN IN", try_login, width=16)
    login_btn.config(font=("Segoe UI", 10, "bold"), pady=8)
    login_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

    def go_back():
        win.destroy()
        if on_back:
            on_back()

    back_btn = neutral_button(btn_row, "BACK", go_back, width=14)
    back_btn.config(font=FONTS["body_b"], pady=8)
    back_btn.pack(side="right", expand=True, fill="x", padx=(6, 0))

    tk.Label(
        win,
        text="Need an account? Ask your library administrator to provision one.",
        font=FONTS["caption"],
        bg=COLORS["bg"],
        fg=COLORS["text_muted"]
    ).pack(side="bottom", pady=12)

    win.mainloop()