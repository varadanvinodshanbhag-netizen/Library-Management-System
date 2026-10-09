# ============================================================
# newspapers_ui.py
# Administrator Portal: Daily Newspaper & Journal Inventory.
# Action buttons placed directly adjacent to form for immediate visibility.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from db import run_query, get_rows, get_one
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_table, styled_entry,
    primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)


def show_newspapers_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(
        parent,
        "Daily Newspapers & Periodicals",
        "Track daily newspaper arrivals, publication languages, and archive copies"
    )

    # ---------- Form Card ----------
    form_card = tk.Frame(
        parent, bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    form_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    form_grid = tk.Frame(form_card, bg=COLORS["card"])
    form_grid.pack(padx=14, pady=8, fill="x")

    # Row 0
    tk.Label(form_grid, text="Name *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    name_entry = styled_entry(form_grid, width=26)
    name_entry.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=2, ipady=3)

    tk.Label(form_grid, text="Publisher", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    pub_entry = styled_entry(form_grid, width=22)
    pub_entry.grid(row=0, column=3, sticky="w", padx=(0, 16), pady=2, ipady=3)

    tk.Label(form_grid, text="Language", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=4, sticky="w", padx=(0, 4), pady=2)
    lang_entry = styled_entry(form_grid, width=18)
    lang_entry.grid(row=0, column=5, sticky="w", padx=(0, 4), pady=2, ipady=3)

    # Row 1
    tk.Label(form_grid, text="Date (YYYY-MM-DD)", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    date_entry = styled_entry(form_grid, width=26)
    date_entry.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=2, ipady=3)

    tk.Label(form_grid, text="Qty *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)
    qty_entry = styled_entry(form_grid, width=22)
    qty_entry.grid(row=1, column=3, sticky="w", padx=(0, 16), pady=2, ipady=3)

    # ---------- Action Toolbar (PACKED BEFORE TABLE) ----------
    button_row = tk.Frame(form_card, bg=COLORS["card_alt"], height=38)
    button_row.pack(fill="x", padx=1, pady=(4, 0), ipady=3)

    tk.Label(button_row, text=" Search:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(10, 4))
    search_entry = styled_entry(button_row, width=20)
    search_entry.pack(side="left", ipady=2, padx=(0, 14))

    success_button(button_row, "➕ Add Edition",  lambda: add_newspaper(),    width=12).pack(side="left", padx=3)
    primary_button(button_row, "💾 Update",       lambda: update_newspaper(), width=10).pack(side="left", padx=3)
    danger_button (button_row, "🗑️ Delete",       lambda: delete_newspaper(), width=10).pack(side="left", padx=3)
    neutral_button(button_row, "🔄 Clear",        lambda: clear_form(),       width=9).pack(side="left", padx=3)
    neutral_button(button_row, "🔁 Refresh",      lambda: refresh(),          width=9).pack(side="left", padx=3)

    # ---------- Table Setup (AT BOTTOM) ----------
    cols = ("id", "name", "publisher", "date", "language", "qty", "available")
    heads = ("ID", "Publication Name", "Publisher", "Edition Date", "Language", "Total", "Available")
    widths = (55, 230, 170, 110, 100, 65, 75)

    tree = make_table(parent, cols, heads, widths, height=8)

    # ---------- Actions & Data Handling ----------
    def refresh():
        kw = search_entry.get().strip()
        if kw:
            rows = get_rows("""
                SELECT newspaper_id, name, publisher, pub_date,
                       language, quantity, available
                FROM newspapers
                WHERE name LIKE ? OR publisher LIKE ? OR language LIKE ?
                ORDER BY newspaper_id DESC
            """, (f"%{kw}%", f"%{kw}%", f"%{kw}%"))
        else:
            rows = get_rows("""
                SELECT newspaper_id, name, publisher, pub_date,
                       language, quantity, available
                FROM newspapers
                ORDER BY newspaper_id DESC
            """)

        populate_tree_with_striping(tree, rows)

    search_entry.bind("<KeyRelease>", lambda e: refresh())

    def clear_form():
        for e in (name_entry, pub_entry, lang_entry, date_entry, qty_entry):
            e.delete(0, tk.END)
        tree.selection_remove(tree.selection())

    def add_newspaper():
        name = name_entry.get().strip()
        if not name:
            show_warning("Required Field", "Newspaper name is required.")
            return

        qty_text = qty_entry.get().strip() or "1"
        if not qty_text.isdigit() or int(qty_text) < 1:
            show_error("Validation Error", "Quantity must be a positive integer.")
            return

        qty = int(qty_text)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        run_query("""
            INSERT INTO newspapers
            (name, publisher, pub_date, language, quantity, available, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            pub_entry.get().strip() or None,
            date_entry.get().strip() or None,
            lang_entry.get().strip() or None,
            qty, qty, now
        ))

        log_action("ADMIN", admin_id, "NEWSPAPER_ADDED", f"Added newspaper '{name}' (qty {qty})")
        show_success("Added", f"Edition of '{name}' added to inventory.")
        clear_form()
        refresh()

    def update_newspaper():
        sel = tree.selection()
        if not sel:
            show_warning("Selection Required", "Select a newspaper from the table to update.")
            return

        nid = tree.item(sel[0])["values"][0]
        name = name_entry.get().strip()
        if not name:
            show_warning("Required Field", "Newspaper name is required.")
            return

        qty_text = qty_entry.get().strip() or "1"
        if not qty_text.isdigit() or int(qty_text) < 1:
            show_error("Validation Error", "Quantity must be a positive integer.")
            return

        qty = int(qty_text)

        run_query("""
            UPDATE newspapers
            SET name=?, publisher=?, pub_date=?, language=?, quantity=?, available=?
            WHERE newspaper_id=?
        """, (
            name,
            pub_entry.get().strip() or None,
            date_entry.get().strip() or None,
            lang_entry.get().strip() or None,
            qty, qty, nid
        ))

        log_action("ADMIN", admin_id, "NEWSPAPER_UPDATED", f"Updated newspaper #{nid} '{name}'")
        show_success("Updated", f"Newspaper edition #{nid} updated.")
        clear_form()
        refresh()

    def delete_newspaper():
        sel = tree.selection()
        if not sel:
            show_warning("Selection Required", "Select a newspaper from the table to delete.")
            return

        values = tree.item(sel[0])["values"]
        nid, name = values[0], values[1]

        if not ask_confirm("Confirm Deletion", f"Permanently delete '{name}' (ID #{nid})?"):
            return

        run_query("DELETE FROM newspapers WHERE newspaper_id = ?", (nid,))
        log_action("ADMIN", admin_id, "NEWSPAPER_DELETED", f"Deleted newspaper #{nid} '{name}'")
        show_success("Deleted", "Newspaper deleted from catalog.")
        clear_form()
        refresh()

    def on_row_select(event):
        sel = tree.selection()
        if not sel:
            return
        v = tree.item(sel[0])["values"]
        name_entry.delete(0, tk.END);  name_entry.insert(0, v[1] or "")
        pub_entry.delete(0, tk.END);   pub_entry.insert(0, v[2] or "")
        date_entry.delete(0, tk.END);  date_entry.insert(0, v[3] or "")
        lang_entry.delete(0, tk.END);  lang_entry.insert(0, v[4] or "")
        qty_entry.delete(0, tk.END);   qty_entry.insert(0, v[5] or "")

    tree.bind("<<TreeviewSelect>>", on_row_select)

    refresh()