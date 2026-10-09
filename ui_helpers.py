# ============================================================
# ui_helpers.py
# Universal UI styling, design tokens, and components for
# the Library Management System.
# Optimized for 720p/1080p desktop presentation displays.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# ------------------------------------------------------------
# 1. DESIGN TOKENS & COLOR PALETTE
# ------------------------------------------------------------
COLORS = {
    # Brand Primary - Aesthetic Royal Indigo
    "primary":        "#4f46e5",   # Aesthetic Indigo
    "primary_dark":   "#312e81",   # Deep Indigo Accent
    "primary_light":  "#6366f1",   # Vibrant Indigo
    "primary_subtle": "#eef2ff",   # Soft Light Lavender/Indigo Tint

    # Accents & Semantics
    "accent":         "#f59e0b",   # Warm Amber
    "accent_light":   "#fef3c7",   # Pale Amber Tint
    "success":        "#10b981",   # Emerald Sage Green
    "success_light":  "#ecfdf5",   # Mint Tint
    "danger":         "#ef4444",   # Coral Rose Red
    "danger_light":   "#fee2e2",   # Soft Rose Tint
    "warning":        "#f59e0b",   # Warm Amber
    "warning_light":  "#fffbeb",   # Cream Tint
    "info":           "#0284c7",   # Sky Blue
    "info_light":     "#e0f2fe",   # Ice Blue Tint

    # Backgrounds & Surfaces (Light Aesthetic)
    "bg":             "#f8fafc",   # Crisp Soft Porcelain Canvas
    "card":           "#ffffff",   # Pure White Surface
    "card_alt":       "#f8fafc",   # Subtle Surface Tint
    "surface_hover":  "#f1f5f9",   # Soft Slate Hover Tint

    # Typography (High-contrast, Crisp legibility)
    "text":           "#0f172a",   # Deep Slate (WCAG AAA)
    "text_secondary": "#334155",   # Slate-700
    "text_muted":     "#64748b",   # Slate-500
    "text_on_dark":   "#ffffff",
    "header_sub":     "#6366f1",   # Vibrant Indigo

    # Borders & Dividers
    "border":         "#e2e8f0",   # Crisp Slate-200 Border
    "border_dark":    "#cbd5e1",   # Slate-300 Border
    "input_bg":       "#ffffff",   # Clean White Entry
    "input_focus":    "#4f46e5",   # Focused Ring

    # Sidebar (Light Aesthetic Hook Style)
    "sidebar":               "#ffffff",   # Crisp White Sidebar
    "sidebar_border":        "#e2e8f0",   # Clean Dividing Border
    "sidebar_text":          "#334155",   # Dark Slate Text
    "sidebar_hover":         "#f8fafc",   # Soft Pearl Hover
    "sidebar_active_bg":     "#eef2ff",   # Soft Indigo Active Background
    "sidebar_active_fg":     "#4338ca",   # Deep Indigo Active Text
    "sidebar_active_hook":   "#4f46e5",   # Aesthetic 4px Indigo Hook Bar

    # Member Portal Sidebar
    "sidebar_member":             "#ffffff",
    "sidebar_member_border":      "#e2e8f0",
    "sidebar_member_text":        "#334155",
    "sidebar_member_hover":       "#f8fafc",
    "sidebar_member_active_bg":   "#ecfdf5",   # Soft Mint Active Background
    "sidebar_member_active_fg":   "#065f46",   # Deep Emerald Active Text
    "sidebar_member_active_hook": "#10b981",   # Aesthetic 4px Emerald Hook Bar
}

# ------------------------------------------------------------
# 2. TYPOGRAPHY
# ------------------------------------------------------------
FONTS = {
    "h1":          ("Segoe UI", 16, "bold"),
    "h2":          ("Segoe UI", 13, "bold"),
    "h3":          ("Segoe UI", 10, "bold"),
    "title":       ("Segoe UI", 15, "bold"),
    "body":        ("Segoe UI", 9),
    "body_b":      ("Segoe UI", 9, "bold"),
    "small":       ("Segoe UI", 8),
    "small_b":     ("Segoe UI", 8, "bold"),
    "caption":     ("Segoe UI", 8),
    "mono":        ("Consolas", 9),
    "mono_b":      ("Consolas", 9, "bold"),
    "stat_val":    ("Segoe UI", 17, "bold"),
    "stat_lbl":    ("Segoe UI", 8, "bold"),
    "nav":         ("Segoe UI", 9),
    "nav_b":       ("Segoe UI", 9, "bold"),
}

# ------------------------------------------------------------
# 3. SPACING & SIZING CONSTANTS
# Compact padding to fit 720p screens cleanly
# ------------------------------------------------------------
PAD = {
    "section_x": 16,
    "section_y": (8, 4),
    "card_x": 4,
    "card_y": 4,
    "form_pad_x": 12,
    "form_pad_y": 6,
}


# ------------------------------------------------------------
# 4. WINDOW CENTERING HELPER
# ------------------------------------------------------------
def center_window(win, width, height):
    """Positions the Tkinter window safely in the visible screen area."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    # Clamp height to fit within display
    actual_h = min(height, sh - 60)
    actual_w = min(width, sw - 40)
    x = max(0, (sw - actual_w) // 2)
    y = max(0, (sh - actual_h) // 2 - 25)
    win.geometry(f"{actual_w}x{actual_h}+{x}+{y}")


# ------------------------------------------------------------
# 5. IMAGE LOADING WITH PIL + PURE TKINTER FALLBACK
# ------------------------------------------------------------
_IMAGE_CACHE = {}


def clear_image_cache():
    """Explicitly clears the PhotoImage cache."""
    _IMAGE_CACHE.clear()


def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_photo(size=None, variant="banner", master=None):
    """
    Safely load college/student photo.
    Checks for resized PNG variants first (zero dependencies),
    falls back to PIL if available, or returns None safely.
    Caches loaded PhotoImage objects per Tk root instance to prevent
    'image doesn't exist' TclErrors across window teardowns.
    """
    root = master or tk._default_root
    root_id = id(root) if root is not None else 0
    cache_key = (root_id, variant, size)

    if cache_key in _IMAGE_CACHE:
        cached = _IMAGE_CACHE[cache_key]
        if root is not None:
            try:
                root.tk.call("image", "type", str(cached))
                return cached
            except Exception:
                try:
                    del _IMAGE_CACHE[cache_key]
                except KeyError:
                    pass
        else:
            return cached

    app_dir = get_app_dir()

    variant_map = {
        "thumb":  ["college_thumb.png", "college_banner.png", "college_photo.png", "college_photo.webp"],
        "banner": ["college_banner.png", "college_thumb.png", "college_photo.png", "college_photo.webp"],
        "small":  ["college_small.png", "college_banner.png", "college_photo.png", "college_photo.webp"],
        "full":   ["college_photo.png", "college_banner.png", "college_photo.webp"],
    }
    candidate_names = variant_map.get(variant, ["college_photo.png", "college_photo.webp"])

    search_dirs = [app_dir]
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        search_dirs.append(sys._MEIPASS)

    found_path = None
    for d in search_dirs:
        for name in candidate_names:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                found_path = p
                break
        if found_path:
            break

    if not found_path:
        return None

    # Method A: Try PIL/Pillow for dynamic scaling
    try:
        from PIL import Image, ImageTk
        img = Image.open(found_path)
        if size:
            img = img.resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img, master=root)
        _IMAGE_CACHE[cache_key] = photo
        return photo
    except Exception:
        pass

    # Method B: Native Tkinter PhotoImage (supports PNG without external library)
    try:
        if found_path.lower().endswith((".png", ".gif")):
            photo = tk.PhotoImage(file=found_path, master=root)
            _IMAGE_CACHE[cache_key] = photo
            return photo
    except Exception:
        pass

    return None


# ------------------------------------------------------------
# 6. TTK GLOBAL STYLING
# ------------------------------------------------------------
def configure_styles():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Treeview
    style.configure(
        "Treeview",
        background="white",
        foreground=COLORS["text"],
        rowheight=26,
        fieldbackground="white",
        font=FONTS["body"],
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        background="#f1f5f9",
        foreground=COLORS["text"],
        font=FONTS["body_b"],
        borderwidth=1,
        relief="flat",
        padding=(6, 5),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#e2e8f0")],
        foreground=[("active", COLORS["text"])]
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["primary_subtle"])],
        foreground=[("selected", COLORS["primary_dark"])]
    )

    # Combobox
    style.configure(
        "TCombobox",
        font=FONTS["body"],
        padding=2,
        background="white",
        fieldbackground="white"
    )

    # Scrollbars
    style.configure(
        "Vertical.TScrollbar",
        troughcolor=COLORS["bg"],
        background=COLORS["border"],
        borderwidth=0,
        arrowsize=11
    )
    style.configure(
        "Horizontal.TScrollbar",
        troughcolor=COLORS["bg"],
        background=COLORS["border"],
        borderwidth=0,
        arrowsize=11
    )


# ------------------------------------------------------------
# 7. HEADER & SECTION TITLE
# ------------------------------------------------------------
def section_title(parent, text, subtitle=None):
    container = tk.Frame(parent, bg=COLORS["card"])
    container.pack(fill="x", padx=PAD["section_x"], pady=PAD["section_y"])

    row = tk.Frame(container, bg=COLORS["card"])
    row.pack(fill="x")

    # Aesthetic vertical Hook Pill
    pill = tk.Frame(row, bg=COLORS["primary"], width=4, height=20)
    pill.pack(side="left", padx=(0, 8))
    pill.pack_propagate(False)

    text_frame = tk.Frame(row, bg=COLORS["card"])
    text_frame.pack(side="left", fill="x")

    tk.Label(
        text_frame, text=text,
        font=FONTS["h2"], bg=COLORS["card"], fg=COLORS["text"]
    ).pack(anchor="w")

    if subtitle:
        tk.Label(
            text_frame, text=subtitle,
            font=FONTS["small"], bg=COLORS["card"], fg=COLORS["text_muted"]
        ).pack(anchor="w", pady=(1, 0))

    # Divider
    divider = tk.Frame(parent, bg=COLORS["border"], height=1)
    divider.pack(fill="x", padx=PAD["section_x"], pady=(4, 8))


# ------------------------------------------------------------
# 8. BUTTON COMPONENTS
# ------------------------------------------------------------
def _create_button(parent, text, command, width, bg, fg, hover_bg, hover_fg="white", font=None):
    btn_font = font or FONTS["body_b"]
    btn = tk.Button(
        parent,
        text=text,
        width=width,
        command=command,
        bg=bg,
        fg=fg,
        font=btn_font,
        activebackground=hover_bg,
        activeforeground=hover_fg,
        relief="flat",
        cursor="hand2",
        padx=8,
        pady=4,
        bd=0,
        highlightthickness=0,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg, fg=hover_fg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg, fg=fg))
    return btn


def primary_button(parent, text, command, width=14):
    return _create_button(parent, text, command, width,
                          COLORS["primary"], "white", COLORS["primary_light"], "white")


def success_button(parent, text, command, width=14):
    return _create_button(parent, text, command, width,
                          COLORS["success"], "white", "#059669", "white")


def danger_button(parent, text, command, width=14):
    return _create_button(parent, text, command, width,
                          COLORS["danger"], "white", "#dc2626", "white")


def warning_button(parent, text, command, width=14):
    return _create_button(parent, text, command, width,
                          COLORS["accent"], "white", "#d97706", "white")


def neutral_button(parent, text, command, width=14):
    return _create_button(parent, text, command, width,
                          COLORS["card_alt"], COLORS["text"],
                          COLORS["border"], COLORS["text"])


# ------------------------------------------------------------
# 9. INPUT FIELD HELPERS
# ------------------------------------------------------------
def styled_entry(parent, width=24, show=None, **kwargs):
    entry = tk.Entry(
        parent,
        width=width,
        font=FONTS["body"],
        relief="solid",
        bd=1,
        bg=COLORS["input_bg"],
        fg=COLORS["text"],
        insertbackground=COLORS["text"],
        highlightthickness=1,
        highlightcolor=COLORS["input_focus"],
        highlightbackground=COLORS["border_dark"],
        **kwargs
    )
    if show:
        entry.config(show=show)
    return entry


def form_field(parent, label_text, width=24, show=None):
    wrapper = tk.Frame(parent, bg=COLORS["card"])
    wrapper.pack(fill="x", pady=(3, 5))

    tk.Label(
        wrapper, text=label_text,
        bg=COLORS["card"], fg=COLORS["text_secondary"],
        font=FONTS["small_b"]
    ).pack(anchor="w", pady=(0, 2))

    entry = styled_entry(wrapper, width=width, show=show)
    entry.pack(anchor="w", ipady=3, fill="x")
    return entry


# ------------------------------------------------------------
# 10. STATISTIC CARD (AESTHETIC HOOK STYLE)
# ------------------------------------------------------------
def make_card(parent, title, value, color=None, width=160, height=74):
    color = color or COLORS["primary"]
    card = tk.Frame(
        parent,
        bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
        width=width,
        height=height,
    )
    card.pack_propagate(False)

    # Aesthetic Left Hook Bar (5px accent pill)
    hook = tk.Frame(card, bg=color, width=5)
    hook.pack(side="left", fill="y")

    # Content
    body = tk.Frame(card, bg=COLORS["card"])
    body.pack(side="left", fill="both", expand=True, padx=12, pady=(6, 4))

    tk.Label(
        body,
        text=title.upper(),
        font=FONTS["caption"],
        bg=COLORS["card"],
        fg=COLORS["text_muted"]
    ).pack(anchor="w")

    val_label = tk.Label(
        body,
        text=str(value),
        font=FONTS["stat_val"],
        bg=COLORS["card"],
        fg=color
    )
    val_label.pack(anchor="w", pady=(1, 0))

    return card


# ------------------------------------------------------------
# 11. TREEVIEW TABLE GENERATOR (COMPACT HEIGHT)
# ------------------------------------------------------------
def make_table(parent, columns, headings, widths, height=8):
    frame = tk.Frame(parent, bg=COLORS["card"],
                     highlightbackground=COLORS["border"],
                     highlightthickness=1)
    frame.pack(fill="both", expand=True, padx=PAD["section_x"], pady=(0, 8))

    tree = ttk.Treeview(
        frame, columns=columns, show="headings", height=height
    )

    for col, head, w in zip(columns, headings, widths):
        tree.heading(col, text=head)
        tree.column(col, width=w, anchor="w")

    configure_styles()

    tree.tag_configure("even", background=COLORS["card"])
    tree.tag_configure("odd",  background=COLORS["card_alt"])

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    return tree


def populate_tree_with_striping(tree, rows, format_fn=None):
    """Utility to clear and repopulate a treeview with alternating row tags."""
    for item in tree.get_children():
        tree.delete(item)

    for idx, r in enumerate(rows):
        tag = "odd" if idx % 2 == 1 else "even"
        vals = format_fn(r) if format_fn else r
        tree.insert("", tk.END, values=vals, tags=(tag,))


# ------------------------------------------------------------
# 12. SIDEBAR NAVIGATION BUTTON FACTORY
# ------------------------------------------------------------
def make_sidebar_btn(sidebar, text, command, bg_color=None, hover_color=None, active_color=None):
    bg = bg_color or COLORS["sidebar"]
    hover = hover_color or COLORS["sidebar_hover"]

    btn = tk.Button(
        sidebar,
        text=text,
        command=command,
        bg=bg,
        fg="white",
        font=FONTS["nav"],
        activebackground=hover,
        activeforeground="white",
        relief="flat",
        anchor="w",
        padx=16,
        pady=7,
        cursor="hand2",
        bd=0,
        highlightthickness=0,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


# ------------------------------------------------------------
# 13. MESSAGE HELPERS
# ------------------------------------------------------------
def show_success(title="Success", message="Operation completed successfully."):
    messagebox.showinfo(title, message)


def show_error(title="Error", message="An error occurred."):
    messagebox.showerror(title, message)


def show_warning(title="Warning", message="Please review the entered information."):
    messagebox.showwarning(title, message)


def ask_confirm(title="Confirmation", message="Are you sure you want to proceed?"):
    return messagebox.askyesno(title, message)