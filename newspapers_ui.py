# ============================================================
# newspapers_ui.py
# Admin screen: manage daily newspaper inventory (add/edit/delete/search).
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from db import run_query, get_rows, get_one
from activity_log import log_action
from ui_helpers import (
    COLORS, FONTS, section_title, make_table,
    primary_button, success_button, danger_button, neutral_button,
    show_success, show_error, show_warning, ask_confirm
)


def show_newspapers_screen(parent, admin_id=None):
    for w in parent.winfo_children():
        w.destroy()

    section_title(parent, "Newspapers", "Manage daily newspaper inventory")

    # ---------- Form ----------
    form = tk.Frame(parent, bg=COLORS["card"])
    form.pack(fill="x", padx=20, pady=(5, 10))

    tk.Label(form, text="Name *",     bg=COLORS["card"], font=FONTS["body"]).grid(row=0, column=0, sticky="w", pady=4)
    name_entry = tk.Entry(form, width=28, font=FONTS["body"], relief="solid", bd=1)
    name_entry.grid(row=0, column=1, padx=(5, 15), pady=4, ipady=3)

    tk.Label(form, text="Publisher",  bg=COLORS["card"], font=FONTS["body"]).grid(row=0, column=2, sticky="w", pady=4)
    pub_entry = tk.Entry(form, width=24, font=FONTS["body"], relief="solid", bd=1)
    pub_entry.grid(row=0, column=3, padx=(5, 15), pady=4, ipady=3)

    tk.Label(form, text="Language",   bg=COLORS["card"], font=FONTS["body"]).grid(row=1, column=0, sticky="w", pady=4)
    lang_entry = tk.Entry(form, width=28, font=FONTS["body"], relief="solid", bd=1)
    lang_entry.grid(row=1, column=1, padx=(5, 15), pady=4, ipady=3)

    tk.Label(form, text="Date (YYYY-MM-DD)", bg=COLORS["card"], font=FONTS["body"]).grid(row=1, column=2, sticky="w", pady=4)
    date_entry = tk.Entry(form, width=24, font=FONTS["body"], relief="solid", bd=1)
    date_entry.grid(row=1, column=3, padx=(5, 15), pady=4, ipady=3)

    tk.Label(form, text="Quantity",   bg=COLORS["card"], font=FONTS["body"]).grid(row=2, column=0, sticky="w", pady=4)
    qty_entry = tk.Entry(form, width=28, font=FONTS["body"], relief="solid", bd=1)
    qty_entry.grid(row=2, column=1, padx=(5, 15), pady=4, ipady=3)

    # ---------- Search bar ----------
    search_frame = tk.Frame(parent, bg=COLORS["card"])
    search_frame.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(search_frame, text="Search:", bg=COLORS["card"], font=FONTS["body"]).pack(side="left", padx=(0, 5))
    search_entry = tk.Entry(search_frame, width=30, font=FONTS["body"], relief="solid", bd=1)
    search_entry.pack(side="left", ipady=3)
    neutral_button(search_frame, "Search",
                   command=lambda: refresh(), width=10).pack(side="left", padx=5)
    neutral_button(search_frame, "Clear",
                   command=lambda: (search_entry.delete(0, tk.END), refresh()),
                   width=8).pack(side="left", padx=5)

    # ---------- Button row (packed before table) ----------
    btn_row = tk.Frame(parent, bg=COLORS["card"])
    btn_row.pack(side="bottom", pady=(5, 12))

    # ---------- Table ----------
    cols = ("id", "name", "publisher", "date", "language", "qty", "available")
    heads = ("ID", "Name", "Publisher", "Date", "Language", "Qty", "Available")
    widths = (50, 200, 160, 120, 100, 60, 80)

    tree = make_table(parent, cols, heads, widths, height=12)

    # ---------- Data functions ----------
    def refresh():
        for item in tree.get_children():
            tree.delete(item)

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

        for r in rows:
            tree.insert("", tk.END, values=r)

    def clear_form():
        for e in (name_entry, pub_entry, lang_entry,
                  date_entry, qty_entry):
            e.delete(0, tk.END)
        tree.selection_remove(tree.selection())

    # ---------- Actions ----------
    def add_newspaper():
        name = name_entry.get().strip()
        if not name:
            show_warning("Warning", "Name is required.")
            return

        qty_text = qty_entry.get().strip() or "1"
        if not qty_text.isdigit() or int(qty_text) < 1:
            show_error("Error", "Quantity must be a positive number.")
            return

        qty = int(qty_text)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        run_query("""
            INSERT INTO newspapers
            (name, publisher, pub_date, language, quantity, available, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, pub_entry.get().strip() or None,
              date_entry.get().strip() or None,
              lang_entry.get().strip() or None,
              qty, qty, now))

        log_action("ADMIN", admin_id, "NEWSPAPER_ADDED",
                   f"Added newspaper '{name}' (qty {qty})")
        show_success("Success", "Newspaper added.")
        clear_form()
        refresh()

    def update_newspaper():
        sel = tree.selection()
        if not sel:
            show_warning("Warning", "Select a newspaper first.")
            return

        nid = tree.item(sel[0])["values"][0]
        name = name_entry.get().strip()
        if not name:
            show_warning("Warning", "Name is required.")
            return

        qty_text = qty_entry.get().strip() or "1"
        if not qty_text.isdigit() or int(qty_text) < 1:
            show_error("Error", "Quantity must be a positive number.")
            return

        qty = int(qty_text)

        run_query("""
            UPDATE newspapers
            SET name=?, publisher=?, pub_date=?, language=?,
                quantity=?, available=?
            WHERE newspaper_id=?
        """, (name, pub_entry.get().strip() or None,
              date_entry.get().strip() or None,
              lang_entry.get().strip() or None,
              qty, qty, nid))

        log_action("ADMIN", admin_id, "NEWSPAPER_UPDATED",
                   f"Updated newspaper #{nid} '{name}'")
        show_success("Success", "Newspaper updated.")
        clear_form()
        refresh()

    def delete_newspaper():
        sel = tree.selection()
        if not sel:
            show_warning("Warning", "Select a newspaper first.")
            return

        values = tree.item(sel[0])["values"]
        nid, name = values[0], values[1]

        if not ask_confirm("Confirm", f"Delete newspaper '{name}'?"):
            return

        run_query("DELETE FROM newspapers WHERE newspaper_id = ?", (nid,))
        log_action("ADMIN", admin_id, "NEWSPAPER_DELETED",
                   f"Deleted newspaper #{nid} '{name}'")
        show_success("Success", "Newspaper deleted.")
        clear_form()
        refresh()

    def on_row_select(event):
        sel = tree.selection()
        if not sel:
            return
        v = tree.item(sel[0])["values"]
        # id, name, publisher, date, language, qty, available
        name_entry.delete(0, tk.END);  name_entry.insert(0, v[1] or "")
        pub_entry.delete(0, tk.END);   pub_entry.insert(0, v[2] or "")
        date_entry.delete(0, tk.END);  date_entry.insert(0, v[3] or "")
        lang_entry.delete(0, tk.END);  lang_entry.insert(0, v[4] or "")
        qty_entry.delete(0, tk.END);   qty_entry.insert(0, v[5] or "")

    tree.bind("<<TreeviewSelect>>", on_row_select)

    # ---------- Buttons ----------
    primary_button(btn_row, "Add",     add_newspaper,    width=12).grid(row=0, column=0, padx=5)
    primary_button(btn_row, "Update",  update_newspaper, width=12).grid(row=0, column=1, padx=5)
    danger_button (btn_row, "Delete",  delete_newspaper, width=12).grid(row=0, column=2, padx=5)
    neutral_button(btn_row, "Clear",   clear_form,       width=12).grid(row=0, column=3, padx=5)
    success_button(btn_row, "Refresh", refresh,          width=12).grid(row=0, column=4, padx=5)

    refresh()