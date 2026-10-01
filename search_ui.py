# ============================================================
# search_ui.py
# Search & Sort demo - shows Python data structures in action.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from db import get_rows


# ------------------------------------------------------------
# DSA 1: Linear search - check each item one by one.
# ------------------------------------------------------------
def linear_search(items, key):
    for i in range(len(items)):
        if items[i][1].lower() == key.lower():
            return i
    return -1


# ------------------------------------------------------------
# DSA 2: Binary search - list must be sorted by book_id first.
# ------------------------------------------------------------
def binary_search(items, book_id):
    low = 0
    high = len(items) - 1
    while low <= high:
        mid = (low + high) // 2
        if items[mid][0] == book_id:
            return mid
        elif items[mid][0] < book_id:
            low = mid + 1
        else:
            high = mid - 1
    return -1


# ------------------------------------------------------------
# DSA 3: Bubble sort - sort list of tuples by a chosen index.
# ------------------------------------------------------------
def bubble_sort(items, index):
    n = len(items)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            a = items[j][index]
            b = items[j + 1][index]
            if isinstance(a, str):
                a = a.lower()
            if isinstance(b, str):
                b = b.lower()
            if a > b:
                items[j], items[j + 1] = items[j + 1], items[j]
    return items


def show_search_screen(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    tk.Label(parent, text="Search & Sort", font=("Arial", 16, "bold"), bg="white").pack(pady=8)

    # ---------- Search bar ----------
    search_bar = tk.Frame(parent, bg="white")
    search_bar.pack(pady=5)

    tk.Label(search_bar, text="Search by Title", bg="white").grid(row=0, column=0, padx=6, pady=4)
    keyword_entry = tk.Entry(search_bar, width=26)
    keyword_entry.grid(row=0, column=1, padx=6)

    tk.Label(search_bar, text="Find by Book ID", bg="white").grid(row=0, column=2, padx=6)
    id_entry = tk.Entry(search_bar, width=10)
    id_entry.grid(row=0, column=3, padx=6)

    # ---------- Table ----------
    table_frame = tk.Frame(parent, bg="white")
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    columns = ("id", "title", "author", "category", "total", "available")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    tree.heading("id", text="ID")
    tree.heading("title", text="Title")
    tree.heading("author", text="Author")
    tree.heading("category", text="Category")
    tree.heading("total", text="Total")
    tree.heading("available", text="Available")

    tree.column("id", width=50, anchor="center")
    tree.column("title", width=210)
    tree.column("author", width=170)
    tree.column("category", width=140)
    tree.column("total", width=70, anchor="center")
    tree.column("available", width=90, anchor="center")

    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # ---------- Stats label ----------
    stats_label = tk.Label(parent, text="", bg="white", fg="darkblue",
                           font=("Arial", 10), justify="left")
    stats_label.pack(pady=6)

    # ------------------------------------------------------------
    # Load all books into a list of tuples
    # ------------------------------------------------------------
    def load_all_books():
        rows = get_rows("""
            SELECT b.book_id, b.title, a.author_name, c.category_name,
                   b.total_copies, b.available_copies
            FROM books b
            JOIN authors a    ON b.author_id = a.author_id
            JOIN categories c ON b.category_id = c.category_id
            ORDER BY b.book_id
        """)
        return rows

    def show_rows(rows):
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert("", tk.END, values=row)

    def update_stats(rows):
        # Dictionary: count books per category
        category_count = {}
        for r in rows:
            cat = r[3]
            if cat in category_count:
                category_count[cat] += 1
            else:
                category_count[cat] = 1

        # Set: unique authors
        unique_authors = set()
        for r in rows:
            unique_authors.add(r[2])

        text = f"Total books: {len(rows)}    |    Unique authors: {len(unique_authors)}\n"
        text += "Books per category:  "
        for cat in category_count:
            text += f"{cat}={category_count[cat]}   "
        stats_label.config(text=text)

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------
    def do_search_title():
        keyword = keyword_entry.get().strip()
        if keyword == "":
            messagebox.showwarning("Warning", "Type a title to search.")
            return
        all_books = load_all_books()
        index = linear_search(all_books, keyword)
        if index == -1:
            show_rows([])
            messagebox.showinfo("Not Found", f"No book titled '{keyword}'.")
        else:
            show_rows([all_books[index]])
        update_stats(all_books)

    def do_search_id():
        id_text = id_entry.get().strip()
        if not id_text.isdigit():
            messagebox.showerror("Error", "Book ID must be a number.")
            return
        target_id = int(id_text)
        all_books = load_all_books()
        all_books = bubble_sort(all_books, 0)
        index = binary_search(all_books, target_id)
        if index == -1:
            show_rows([])
            messagebox.showinfo("Not Found", f"No book with ID {target_id}.")
        else:
            show_rows([all_books[index]])
        update_stats(all_books)

    def show_all():
        all_books = load_all_books()
        show_rows(all_books)
        update_stats(all_books)

    def sort_by_title():
        all_books = load_all_books()
        sorted_books = bubble_sort(all_books, 1)
        show_rows(sorted_books)
        update_stats(sorted_books)

    def sort_by_id():
        all_books = load_all_books()
        sorted_books = bubble_sort(all_books, 0)
        show_rows(sorted_books)
        update_stats(sorted_books)

    # ---------- Buttons ----------
    button_row = tk.Frame(parent, bg="white")
    button_row.pack(pady=6)

    tk.Button(button_row, text="Search Title",   width=14, command=do_search_title).grid(row=0, column=0, padx=5)
    tk.Button(button_row, text="Search by ID",   width=14, command=do_search_id).grid(row=0, column=1, padx=5)
    tk.Button(button_row, text="Sort by Title",  width=14, command=sort_by_title).grid(row=0, column=2, padx=5)
    tk.Button(button_row, text="Sort by ID",     width=14, command=sort_by_id).grid(row=0, column=3, padx=5)
    tk.Button(button_row, text="Show All",       width=14, command=show_all).grid(row=0, column=4, padx=5)

    tk.Label(
        parent,
        text="Uses: List + Tuple (books), Dictionary (category count), "
             "Set (unique authors),\nLinear search (title), Binary search (ID), "
             "Bubble sort (title/ID).",
        bg="white", fg="gray", font=("Arial", 9), justify="center"
    ).pack(pady=4)

    show_all()