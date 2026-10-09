# ============================================================
# book_ui.py
# Book Inventory Management Screen.
# Action buttons placed directly adjacent to form for immediate visibility.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from db import run_query, get_rows, get_one
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_table,
    styled_entry, primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)


def get_or_create_author(author_name):
    row = get_one("SELECT author_id FROM authors WHERE author_name = ?", (author_name,))
    if row is None:
        run_query("INSERT INTO authors (author_name) VALUES (?)", (author_name,))
        row = get_one("SELECT author_id FROM authors WHERE author_name = ?", (author_name,))
    return row[0]


def get_or_create_category(category_name):
    row = get_one("SELECT category_id FROM categories WHERE category_name = ?", (category_name,))
    if row is None:
        run_query("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
        row = get_one("SELECT category_id FROM categories WHERE category_name = ?", (category_name,))
    return row[0]


def show_books_screen(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(parent, "Book Inventory Management", "Register, update, and manage cataloged books")

    # ---------- Top Summary Bar ----------
    summary_bar = tk.Frame(parent, bg=COLORS["card"])
    summary_bar.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    stats_inner = tk.Frame(summary_bar, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
    stats_inner.pack(fill="x", ipady=3)

    stat_lbl = tk.Label(
        stats_inner,
        text="Loading catalog metrics...",
        font=FONTS["small_b"],
        bg=COLORS["card_alt"],
        fg=COLORS["text_secondary"]
    )
    stat_lbl.pack(side="left", padx=12)

    def refresh_stats():
        row = get_one("""
            SELECT COUNT(book_id), COALESCE(SUM(total_copies), 0), COALESCE(SUM(available_copies), 0)
            FROM books
        """)
        titles = row[0] if row else 0
        total = row[1] if row else 0
        avail = row[2] if row else 0
        issued = total - avail
        stat_lbl.config(
            text=f"📚 Catalog: {titles} Titles   |   Total Stock: {total} Copies   |   "
                 f"Available: {avail}   |   On Loan: {issued}"
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

    # Row 0: Title & Author
    tk.Label(form_grid, text="Title *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    title_entry = styled_entry(form_grid, width=30)
    title_entry.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=2, ipady=3)

    tk.Label(form_grid, text="Author *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    author_entry = styled_entry(form_grid, width=28)
    author_entry.grid(row=0, column=3, sticky="w", padx=(0, 8), pady=2, ipady=3)

    # Row 1: Category & Total Copies
    tk.Label(form_grid, text="Category *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    category_entry = styled_entry(form_grid, width=30)
    category_entry.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=2, ipady=3)

    tk.Label(form_grid, text="Copies *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)
    copies_entry = styled_entry(form_grid, width=12)
    copies_entry.grid(row=1, column=3, sticky="w", padx=(0, 8), pady=2, ipady=3)

    # ---------- Action Buttons Toolbar (PACKED BEFORE TABLE FOR IMMEDIATE ACCESS) ----------
    button_row = tk.Frame(form_card, bg=COLORS["card_alt"], height=38)
    button_row.pack(fill="x", padx=1, pady=(6, 0), ipady=3)

    # Search filter on left of button row
    tk.Label(button_row, text=" Filter:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(10, 4))
    filter_entry = styled_entry(button_row, width=18)
    filter_entry.pack(side="left", ipady=2, padx=(0, 14))

    # Action Buttons on right of toolbar
    success_button(button_row, "➕ Add Book",   lambda: add_book(),      width=12).pack(side="left", padx=3)
    primary_button(button_row, "💾 Update",     lambda: update_book(),   width=11).pack(side="left", padx=3)
    danger_button (button_row, "🗑️ Delete",     lambda: delete_book(),   width=11).pack(side="left", padx=3)
    neutral_button(button_row, "🔄 Clear",      lambda: clear_form(),    width=10).pack(side="left", padx=3)
    neutral_button(button_row, "🔁 Refresh",    lambda: refresh_table(), width=10).pack(side="left", padx=3)

    # ---------- Table Setup (AT BOTTOM WITH SCROLLBAR) ----------
    columns = ("id", "title", "author", "category", "total", "available")
    headings = ("Book ID", "Title", "Author", "Category", "Total Copies", "Available")
    widths = (65, 260, 200, 160, 95, 95)

    tree = make_table(parent, columns, headings, widths, height=8)

    # ---------- Action Functions ----------
    def refresh_table():
        kw = filter_entry.get().strip()
        if kw:
            rows = get_rows("""
                SELECT b.book_id, b.title, a.author_name, c.category_name,
                       b.total_copies, b.available_copies
                FROM books b
                JOIN authors a    ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                WHERE b.title LIKE ? OR a.author_name LIKE ? OR c.category_name LIKE ?
                ORDER BY b.book_id DESC
            """, (f"%{kw}%", f"%{kw}%", f"%{kw}%"))
        else:
            rows = get_rows("""
                SELECT b.book_id, b.title, a.author_name, c.category_name,
                       b.total_copies, b.available_copies
                FROM books b
                JOIN authors a    ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                ORDER BY b.book_id DESC
            """)

        populate_tree_with_striping(tree, rows)
        refresh_stats()

    filter_entry.bind("<KeyRelease>", lambda e: refresh_table())

    def clear_form():
        title_entry.delete(0, tk.END)
        author_entry.delete(0, tk.END)
        category_entry.delete(0, tk.END)
        copies_entry.delete(0, tk.END)
        tree.selection_remove(tree.selection())

    def add_book():
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        category = category_entry.get().strip()
        copies_text = copies_entry.get().strip()

        if not title or not author or not category or not copies_text:
            show_warning("Missing Fields", "Please complete all required fields.")
            return
        if not copies_text.isdigit() or int(copies_text) < 1:
            show_error("Validation Error", "Total copies must be a positive integer.")
            return

        copies = int(copies_text)
        author_id = get_or_create_author(author)
        category_id = get_or_create_category(category)

        existing = get_one(
            "SELECT book_id FROM books WHERE title = ? AND author_id = ?",
            (title, author_id)
        )
        if existing is not None:
            show_error("Duplicate Entry", "This book is already in the inventory.")
            return

        run_query(
            "INSERT INTO books (title, author_id, category_id, total_copies, available_copies) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, author_id, category_id, copies, copies)
        )
        show_success("Book Added", f"'{title}' was added successfully.")
        clear_form()
        refresh_table()

    def update_book():
        selected = tree.selection()
        if not selected:
            show_warning("Selection Required", "Select a book from the table to update.")
            return

        book_id = tree.item(selected[0])["values"][0]
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        category = category_entry.get().strip()
        copies_text = copies_entry.get().strip()

        if not title or not author or not category or not copies_text:
            show_warning("Missing Fields", "Please complete all required fields.")
            return
        if not copies_text.isdigit() or int(copies_text) < 1:
            show_error("Validation Error", "Total copies must be a positive integer.")
            return

        new_total = int(copies_text)
        current = get_one(
            "SELECT total_copies, available_copies FROM books WHERE book_id = ?",
            (book_id,)
        )
        old_total, old_available = current[0], current[1]
        issued = old_total - old_available

        if new_total < issued:
            show_error(
                "Quantity Conflict",
                f"Cannot reduce total below {issued} (copies currently on loan)."
            )
            return

        new_available = new_total - issued
        author_id = get_or_create_author(author)
        category_id = get_or_create_category(category)

        run_query(
            "UPDATE books SET title = ?, author_id = ?, category_id = ?, "
            "total_copies = ?, available_copies = ? WHERE book_id = ?",
            (title, author_id, category_id, new_total, new_available, book_id)
        )
        show_success("Updated", f"Book #{book_id} details updated.")
        clear_form()
        refresh_table()

    def delete_book():
        selected = tree.selection()
        if not selected:
            show_warning("Selection Required", "Select a book from the table to delete.")
            return

        values = tree.item(selected[0])["values"]
        book_id = values[0]
        book_title = values[1]

        row = get_one(
            "SELECT total_copies, available_copies FROM books WHERE book_id = ?",
            (book_id,)
        )
        if row[0] != row[1]:
            show_error("Cannot Delete", "Some copies of this book are currently issued.")
            return

        history = get_one("SELECT COUNT(*) FROM issue_return WHERE book_id = ?", (book_id,))
        if history[0] > 0:
            show_error("Cannot Delete", "This book has active or historic loan records.")
            return

        if not ask_confirm("Confirm Deletion", f"Permanently delete '{book_title}' (ID #{book_id})?"):
            return

        run_query("DELETE FROM books WHERE book_id = ?", (book_id,))
        show_success("Deleted", "Book deleted successfully.")
        clear_form()
        refresh_table()

    def on_row_select(event):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0])["values"]
        title_entry.delete(0, tk.END);    title_entry.insert(0, values[1])
        author_entry.delete(0, tk.END);   author_entry.insert(0, values[2])
        category_entry.delete(0, tk.END); category_entry.insert(0, values[3])
        copies_entry.delete(0, tk.END);   copies_entry.insert(0, values[4])

    tree.bind("<<TreeviewSelect>>", on_row_select)

    refresh_table()