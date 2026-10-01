# ============================================================
# book_ui.py
# Book Management screen: add / update / delete / display.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from db import run_query, get_rows, get_one


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

    tk.Label(parent, text="Book Management", font=("Arial", 16, "bold"), bg="white").pack(pady=8)

    # ---------- Form ----------
    form = tk.Frame(parent, bg="white")
    form.pack(pady=5)

    tk.Label(form, text="Title", bg="white").grid(row=0, column=0, padx=6, pady=4, sticky="e")
    title_entry = tk.Entry(form, width=28)
    title_entry.grid(row=0, column=1, padx=6, pady=4)

    tk.Label(form, text="Author", bg="white").grid(row=0, column=2, padx=6, pady=4, sticky="e")
    author_entry = tk.Entry(form, width=28)
    author_entry.grid(row=0, column=3, padx=6, pady=4)

    tk.Label(form, text="Category", bg="white").grid(row=1, column=0, padx=6, pady=4, sticky="e")
    category_entry = tk.Entry(form, width=28)
    category_entry.grid(row=1, column=1, padx=6, pady=4)

    tk.Label(form, text="Total Copies", bg="white").grid(row=1, column=2, padx=6, pady=4, sticky="e")
    copies_entry = tk.Entry(form, width=28)
    copies_entry.grid(row=1, column=3, padx=6, pady=4)

    # ---------- Table ----------
    table_frame = tk.Frame(parent, bg="white")
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    columns = ("id", "title", "author", "category", "total", "available")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

    tree.heading("id", text="ID")
    tree.heading("title", text="Title")
    tree.heading("author", text="Author")
    tree.heading("category", text="Category")
    tree.heading("total", text="Total")
    tree.heading("available", text="Available")

    tree.column("id", width=50, anchor="center")
    tree.column("title", width=200)
    tree.column("author", width=160)
    tree.column("category", width=140)
    tree.column("total", width=70, anchor="center")
    tree.column("available", width=90, anchor="center")

    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)

    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)
        rows = get_rows("""
            SELECT b.book_id, b.title, a.author_name, c.category_name,
                   b.total_copies, b.available_copies
            FROM books b
            JOIN authors a    ON b.author_id = a.author_id
            JOIN categories c ON b.category_id = c.category_id
            ORDER BY b.book_id
        """)
        for row in rows:
            tree.insert("", tk.END, values=row)

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

        if title == "" or author == "" or category == "" or copies_text == "":
            messagebox.showwarning("Warning", "Please fill all fields.")
            return
        if not copies_text.isdigit() or int(copies_text) < 1:
            messagebox.showerror("Error", "Total copies must be a positive number.")
            return

        copies = int(copies_text)
        author_id = get_or_create_author(author)
        category_id = get_or_create_category(category)

        existing = get_one(
            "SELECT book_id FROM books WHERE title = ? AND author_id = ?",
            (title, author_id)
        )
        if existing is not None:
            messagebox.showerror("Error", "This book already exists.")
            return

        run_query(
            "INSERT INTO books (title, author_id, category_id, total_copies, available_copies) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, author_id, category_id, copies, copies)
        )
        messagebox.showinfo("Success", "Book added.")
        clear_form()
        refresh_table()

    def update_book():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a book from the table first.")
            return

        book_id = tree.item(selected[0])["values"][0]
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        category = category_entry.get().strip()
        copies_text = copies_entry.get().strip()

        if title == "" or author == "" or category == "" or copies_text == "":
            messagebox.showwarning("Warning", "Please fill all fields.")
            return
        if not copies_text.isdigit() or int(copies_text) < 1:
            messagebox.showerror("Error", "Total copies must be a positive number.")
            return

        new_total = int(copies_text)
        current = get_one(
            "SELECT total_copies, available_copies FROM books WHERE book_id = ?",
            (book_id,)
        )
        old_total, old_available = current[0], current[1]
        issued = old_total - old_available

        if new_total < issued:
            messagebox.showerror(
                "Error",
                f"Cannot reduce total below {issued} (copies currently issued)."
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
        messagebox.showinfo("Success", "Book updated.")
        clear_form()
        refresh_table()

    def delete_book():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a book from the table first.")
            return

        values = tree.item(selected[0])["values"]
        book_id = values[0]
        book_title = values[1]

        row = get_one(
            "SELECT total_copies, available_copies FROM books WHERE book_id = ?",
            (book_id,)
        )
        if row[0] != row[1]:
            messagebox.showerror("Error", "Cannot delete: some copies are currently issued.")
            return

        history = get_one("SELECT COUNT(*) FROM issue_return WHERE book_id = ?", (book_id,))
        if history[0] > 0:
            messagebox.showerror("Error", "Cannot delete: this book has issue/return history.")
            return

        if not messagebox.askyesno("Confirm", f"Delete '{book_title}' ?"):
            return

        run_query("DELETE FROM books WHERE book_id = ?", (book_id,))
        messagebox.showinfo("Success", "Book deleted.")
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

    button_row = tk.Frame(parent, bg="white")
    button_row.pack(pady=6)

    tk.Button(button_row, text="Add Book",   width=12, command=add_book).grid(row=0, column=0, padx=5)
    tk.Button(button_row, text="Update",     width=12, command=update_book).grid(row=0, column=1, padx=5)
    tk.Button(button_row, text="Delete",     width=12, command=delete_book).grid(row=0, column=2, padx=5)
    tk.Button(button_row, text="Clear Form", width=12, command=clear_form).grid(row=0, column=3, padx=5)
    tk.Button(button_row, text="Refresh",    width=12, command=refresh_table).grid(row=0, column=4, padx=5)

    refresh_table()