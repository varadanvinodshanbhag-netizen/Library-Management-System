# ============================================================
# search_ui.py
# Python Data Structures & Algorithms (DSA) Demonstration Screen.
# Showcases:
# - Linear Search (Title matching - O(n))
# - Binary Search (ID matching - O(log n))
# - Bubble Sort (Title or ID sorting - O(n²))
# - Dictionary (Frequency distribution by category)
# - Set (Unique author counting)
# Optimized for 720p presentation displays.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import time

from db import get_rows
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_table, styled_entry,
    primary_button, success_button, neutral_button,
    populate_tree_with_striping, show_warning, show_error, show_success
)


def linear_search(items, key):
    key_lower = key.lower()
    matches = []
    for i in range(len(items)):
        if key_lower in str(items[i][1]).lower():
            matches.append(i)
    return matches


def binary_search(items, target_id):
    low = 0
    high = len(items) - 1
    while low <= high:
        mid = (low + high) // 2
        current_id = items[mid][0]
        if current_id == target_id:
            return mid
        elif current_id < target_id:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def bubble_sort(items, index):
    data = list(items)
    n = len(data)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            a = data[j][index]
            b = data[j + 1][index]
            if isinstance(a, str): a = a.lower()
            if isinstance(b, str): b = b.lower()
            if a > b:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data


def show_search_screen(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(
        parent,
        "Search & Sorting Algorithms",
        "Interactive Data Structures & Algorithms (DSA) demonstration in pure Python"
    )

    # ---------- DSA Education Banner ----------
    dsa_banner = tk.Frame(parent, bg=COLORS["card"])
    dsa_banner.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    dsa_inner = tk.Frame(dsa_banner, bg=COLORS["primary_subtle"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
    dsa_inner.pack(fill="x", ipady=3)

    tk.Label(
        dsa_inner,
        text="🧠 Core Concepts: Linear Search [O(n)]  •  Binary Search [O(log n)]  •  Bubble Sort [O(n²)]  •  Dict & Set Metrics",
        font=FONTS["small_b"],
        bg=COLORS["primary_subtle"],
        fg=COLORS["primary"]
    ).pack(side="left", padx=12)

    # ---------- Search & Sort Interactive Card (PACKED BEFORE TABLE) ----------
    controls_card = tk.Frame(
        parent, bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    controls_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    ctrl_grid = tk.Frame(controls_card, bg=COLORS["card"])
    ctrl_grid.pack(fill="x", padx=14, pady=6)

    # Row 0: Search Inputs
    tk.Label(ctrl_grid, text="Title:", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=0, sticky="w", padx=(0, 4))
    title_entry = styled_entry(ctrl_grid, width=20)
    title_entry.grid(row=0, column=1, sticky="w", padx=(0, 8), ipady=3)

    primary_button(ctrl_grid, "🔍 Linear Search", lambda: do_linear_search(), width=14
                   ).grid(row=0, column=2, padx=(0, 16))

    tk.Label(ctrl_grid, text="Book ID:", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=3, sticky="w", padx=(0, 4))
    id_entry = styled_entry(ctrl_grid, width=8)
    id_entry.grid(row=0, column=4, sticky="w", padx=(0, 8), ipady=3)

    primary_button(ctrl_grid, "⚡ Binary Search", lambda: do_binary_search(), width=14
                   ).grid(row=0, column=5)

    # Row 1: Sorting Actions Toolbar
    sort_row = tk.Frame(controls_card, bg=COLORS["card_alt"], height=36)
    sort_row.pack(fill="x", padx=1, pady=(4, 0), ipady=3)

    tk.Label(sort_row, text=" Sorting:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(10, 6))

    neutral_button(sort_row, "Sort Title (A-Z)", lambda: do_sort_title(), width=14).pack(side="left", padx=2)
    neutral_button(sort_row, "Sort ID (Asc)",    lambda: do_sort_id(),    width=13).pack(side="left", padx=2)
    success_button(sort_row, "Show Catalog",     lambda: show_all(),      width=12).pack(side="left", padx=2)

    perf_lbl = tk.Label(sort_row, text="", bg=COLORS["card_alt"],
                        fg=COLORS["text_muted"], font=FONTS["caption"])
    perf_lbl.pack(side="right", padx=10)

    # ---------- Dynamic Stats Card ----------
    stats_card = tk.Frame(parent, bg=COLORS["card"])
    stats_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    stats_inner = tk.Frame(stats_card, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"], highlightthickness=1)
    stats_inner.pack(fill="x", ipady=3)

    stats_text_lbl = tk.Label(
        stats_inner,
        text="Calculating data structure statistics...",
        font=FONTS["small"],
        bg=COLORS["card_alt"],
        fg=COLORS["text_secondary"],
        justify="left"
    )
    stats_text_lbl.pack(side="left", padx=12)

    # ---------- Table Setup (AT BOTTOM) ----------
    columns = ("id", "title", "author", "category", "total", "available")
    headings = ("Book ID", "Book Title", "Author", "Category", "Total Stock", "Available")
    widths = (65, 260, 200, 160, 95, 95)

    tree = make_table(parent, columns, headings, widths, height=8)

    # ---------- Data Handling & Operations ----------
    def load_all_books():
        return get_rows("""
            SELECT b.book_id, b.title, a.author_name, c.category_name,
                   b.total_copies, b.available_copies
            FROM books b
            JOIN authors a    ON b.author_id = a.author_id
            JOIN categories c ON b.category_id = c.category_id
            ORDER BY b.book_id
        """)

    def update_stats_panel(items):
        cat_counts = {}
        for r in items:
            cat = r[3]
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        unique_authors = {r[2] for r in items}

        breakdown = "  •  ".join(f"{k}: {v}" for k, v in sorted(cat_counts.items()))
        stats_text_lbl.config(
            text=f"📊 Showing: {len(items)} Books   |   Unique Authors (Set): {len(unique_authors)}\n"
                 f"🏷️ Category Frequency (Dict): {breakdown}"
        )

    def do_linear_search():
        key = title_entry.get().strip()
        if not key:
            show_warning("Search Term Required", "Please enter a title keyword to search.")
            return

        all_books = load_all_books()
        t0 = time.perf_counter()
        match_indices = linear_search(all_books, key)
        t_elapsed = (time.perf_counter() - t0) * 1000

        matched_rows = [all_books[i] for i in match_indices]
        populate_tree_with_striping(tree, matched_rows)
        update_stats_panel(matched_rows)
        perf_lbl.config(text=f"Linear: {len(matched_rows)} matches ({t_elapsed:.3f} ms)")

        if not matched_rows:
            messagebox.showinfo("Search Results", f"No book matches found for '{key}'.")

    def do_binary_search():
        id_str = id_entry.get().strip()
        if not id_str.isdigit():
            show_error("Validation Error", "Book ID must be a numeric integer.")
            return

        target_id = int(id_str)
        all_books = load_all_books()

        t0 = time.perf_counter()
        sorted_books = bubble_sort(all_books, 0)
        idx = binary_search(sorted_books, target_id)
        t_elapsed = (time.perf_counter() - t0) * 1000

        if idx != -1:
            matched_rows = [sorted_books[idx]]
            populate_tree_with_striping(tree, matched_rows)
            update_stats_panel(matched_rows)
            perf_lbl.config(text=f"Binary: Found ID #{target_id} in {t_elapsed:.3f} ms")
        else:
            populate_tree_with_striping(tree, [])
            update_stats_panel([])
            perf_lbl.config(text=f"Binary: ID #{target_id} not found ({t_elapsed:.3f} ms)")
            messagebox.showinfo("Search Results", f"No book found with Book ID #{target_id}.")

    def do_sort_title():
        all_books = load_all_books()
        t0 = time.perf_counter()
        sorted_books = bubble_sort(all_books, 1)
        t_elapsed = (time.perf_counter() - t0) * 1000

        populate_tree_with_striping(tree, sorted_books)
        update_stats_panel(sorted_books)
        perf_lbl.config(text=f"Bubble Sort: {len(sorted_books)} titles ({t_elapsed:.3f} ms)")

    def do_sort_id():
        all_books = load_all_books()
        t0 = time.perf_counter()
        sorted_books = bubble_sort(all_books, 0)
        t_elapsed = (time.perf_counter() - t0) * 1000

        populate_tree_with_striping(tree, sorted_books)
        update_stats_panel(sorted_books)
        perf_lbl.config(text=f"Bubble Sort: {len(sorted_books)} IDs ({t_elapsed:.3f} ms)")

    def show_all():
        all_books = load_all_books()
        populate_tree_with_striping(tree, all_books)
        update_stats_panel(all_books)
        perf_lbl.config(text=f"Loaded full catalog ({len(all_books)} items)")
        title_entry.delete(0, tk.END)
        id_entry.delete(0, tk.END)

    title_entry.bind("<Return>", lambda e: do_linear_search())
    id_entry.bind("<Return>", lambda e: do_binary_search())

    show_all()