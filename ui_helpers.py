# ============================================================
# ui_helpers.py
# Shared UI styles and helpers for consistent look across screens.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox


# ---------- Color palette ----------
COLORS = {
    "primary":      "#0d3b66",   # dark navy blue
    "primary_dark": "#082a4a",
    "accent":       "#f4a261",   # warm orange
    "success":      "#2a9d8f",   # teal green
    "danger":       "#b22222",   # firebrick red
    "warning":      "#e9c46a",   # soft yellow
    "bg":           "#f5f6fa",   # light gray
    "card":         "#ffffff",   # white
    "text":         "#1a1a1a",
    "text_muted":   "#6c757d",
    "border":       "#dcdde1",
}

# ---------- Fonts ----------
FONTS = {
    "h1":       ("Segoe UI", 20, "bold"),
    "h2":       ("Segoe UI", 16, "bold"),
    "h3":       ("Segoe UI", 13, "bold"),
    "body":     ("Segoe UI", 10),
    "body_b":   ("Segoe UI", 10, "bold"),
    "small":    ("Segoe UI", 9),
    "mono":     ("Consolas", 10),
}


# ------------------------------------------------------------
# Section title inside content area
# ------------------------------------------------------------
def section_title(parent, text, subtitle=None):
    frame = tk.Frame(parent, bg=COLORS["card"])
    frame.pack(fill="x", padx=20, pady=(15, 5))

    tk.Label(
        frame, text=text,
        font=FONTS["h2"], bg=COLORS["card"], fg=COLORS["primary"]
    ).pack(anchor="w")

    if subtitle:
        tk.Label(
            frame, text=subtitle,
            font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 0))

    # thin separator line
    sep = tk.Frame(parent, bg=COLORS["border"], height=1)
    sep.pack(fill="x", padx=20, pady=(8, 10))


# ------------------------------------------------------------
# Primary action button
# ------------------------------------------------------------
def primary_button(parent, text, command, width=14):
    return tk.Button(
        parent, text=text, width=width, command=command,
        bg=COLORS["primary"], fg="white",
        font=FONTS["body_b"], activebackground=COLORS["primary_dark"],
        activeforeground="white", relief="flat", cursor="hand2",
        padx=6, pady=4
    )


def success_button(parent, text, command, width=14):
    return tk.Button(
        parent, text=text, width=width, command=command,
        bg=COLORS["success"], fg="white",
        font=FONTS["body_b"], activebackground="#21867a",
        activeforeground="white", relief="flat", cursor="hand2",
        padx=6, pady=4
    )


def danger_button(parent, text, command, width=14):
    return tk.Button(
        parent, text=text, width=width, command=command,
        bg=COLORS["danger"], fg="white",
        font=FONTS["body_b"], activebackground="#8b1a1a",
        activeforeground="white", relief="flat", cursor="hand2",
        padx=6, pady=4
    )


def neutral_button(parent, text, command, width=14):
    return tk.Button(
        parent, text=text, width=width, command=command,
        bg="#e1e5ea", fg=COLORS["text"],
        font=FONTS["body_b"], activebackground="#cfd4da",
        relief="flat", cursor="hand2",
        padx=6, pady=4
    )


# ------------------------------------------------------------
# Form field: label + entry stacked vertically
# ------------------------------------------------------------
def form_field(parent, label_text, width=26, show=None):
    tk.Label(
        parent, text=label_text,
        bg=COLORS["card"], fg=COLORS["text"],
        font=FONTS["body"]
    ).pack(anchor="w", pady=(6, 2))

    entry = tk.Entry(
        parent, width=width, font=FONTS["body"],
        relief="solid", bd=1
    )
    if show:
        entry.config(show=show)
    entry.pack(anchor="w", ipady=4)
    return entry


# ------------------------------------------------------------
# Treeview with scrollbar (returns tree widget)
# ------------------------------------------------------------
def make_table(parent, columns, headings, widths, height=12):
    frame = tk.Frame(parent, bg=COLORS["card"])
    frame.pack(fill="both", expand=True, padx=20, pady=10)

    tree = ttk.Treeview(
        frame, columns=columns, show="headings", height=height
    )

    for col, head, w in zip(columns, headings, widths):
        tree.heading(col, text=head)
        tree.column(col, width=w, anchor="w")

    # ttk style
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "Treeview",
        background="white",
        foreground=COLORS["text"],
        rowheight=26,
        fieldbackground="white",
        font=FONTS["body"]
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["primary"],
        foreground="white",
        font=FONTS["body_b"]
    )
    style.map("Treeview.Heading", background=[("active", COLORS["primary_dark"])])

    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)

    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    return tree


# ------------------------------------------------------------
# Message helpers (consistent styling)
# ------------------------------------------------------------
def show_success(title="Success", message="Done."):
    messagebox.showinfo(title, message)


def show_error(title="Error", message="Something went wrong."):
    messagebox.showerror(title, message)


def show_warning(title="Warning", message="Please check your input."):
    messagebox.showwarning(title, message)


def ask_confirm(title="Confirm", message="Are you sure?"):
    return messagebox.askyesno(title, message)


# ------------------------------------------------------------
# Card frame (used for dashboard tiles)
# ------------------------------------------------------------
def make_card(parent, title, value, color=None, width=180, height=90):
    color = color or COLORS["primary"]
    card = tk.Frame(
        parent, bg=COLORS["card"], relief="solid", bd=1,
        width=width, height=height
    )
    card.pack_propagate(False)

    accent = tk.Frame(card, bg=color, height=6)
    accent.pack(fill="x")

    tk.Label(
        card, text=title,
        font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text_muted"]
    ).pack(anchor="w", padx=12, pady=(10, 0))

    tk.Label(
        card, text=str(value),
        font=("Segoe UI", 24, "bold"),
        bg=COLORS["card"], fg=color
    ).pack(anchor="w", padx=12)

    return card