# ============================================================
# members_ui.py
# Students & Members Directory Management Screen.
# Supports: Department assignment (CSE, ME, AE, EE),
# Sequential Card ID generation (e.g. CSE 1, ME 1, AE 1, EE 1),
# Member categories (STUDENT, STAFF/FACULTY), and complete CRUD.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from db import run_query, get_rows, get_one, get_next_card_id
from ui_helpers import (
    COLORS, FONTS, PAD, section_title, make_table,
    styled_entry, primary_button, success_button, danger_button, neutral_button,
    populate_tree_with_striping, show_success, show_error, show_warning, ask_confirm
)

DEPARTMENTS = ["CSE", "ME", "AE", "EE", "OTHER/STAFF"]
MEMBER_TYPES = ["STUDENT", "STAFF/FACULTY"]


def show_members_screen(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    section_title(
        parent,
        "Students & Members Directory",
        "Manage student enrollment, department affiliations (CSE, ME, AE, EE), and library card IDs"
    )

    # ---------- Summary Metrics Bar ----------
    summary_bar = tk.Frame(parent, bg=COLORS["card"])
    summary_bar.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    stats_inner = tk.Frame(summary_bar, bg=COLORS["card_alt"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
    stats_inner.pack(fill="x", ipady=3)

    stat_lbl = tk.Label(
        stats_inner,
        text="Loading student and member metrics...",
        font=FONTS["small_b"],
        bg=COLORS["card_alt"],
        fg=COLORS["text_secondary"]
    )
    stat_lbl.pack(side="left", padx=12)

    def refresh_stats():
        total = get_one("SELECT COUNT(*) FROM members")[0]
        students = get_one("SELECT COUNT(*) FROM members WHERE member_type = 'STUDENT'")[0]
        staff = total - students

        cse_cnt = get_one("SELECT COUNT(*) FROM members WHERE dept = 'CSE'")[0]
        me_cnt  = get_one("SELECT COUNT(*) FROM members WHERE dept = 'ME'")[0]
        ae_cnt  = get_one("SELECT COUNT(*) FROM members WHERE dept = 'AE'")[0]
        ee_cnt  = get_one("SELECT COUNT(*) FROM members WHERE dept = 'EE'")[0]

        stat_lbl.config(
            text=f"👥 Total: {total} (Students: {students}, Staff: {staff})   |   "
                 f"CSE: {cse_cnt}   •   ME: {me_cnt}   •   AE: {ae_cnt}   •   EE: {ee_cnt}"
        )

    # ---------- Form Card ----------
    form_card = tk.Frame(
        parent, bg=COLORS["card"],
        highlightbackground=COLORS["border"],
        highlightthickness=1
    )
    form_card.pack(fill="x", padx=PAD["section_x"], pady=(0, 6))

    form_grid = tk.Frame(form_card, bg=COLORS["card"])
    form_grid.pack(padx=14, pady=6, fill="x")

    # Row 0: Full Name, Department, Card ID
    tk.Label(form_grid, text="Full Name *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    name_entry = styled_entry(form_grid, width=24)
    name_entry.grid(row=0, column=1, sticky="w", padx=(0, 14), pady=2, ipady=3)

    tk.Label(form_grid, text="Department *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
    dept_var = tk.StringVar(value="CSE")
    dept_combo = ttk.Combobox(
        form_grid, textvariable=dept_var, width=12,
        values=DEPARTMENTS, state="readonly"
    )
    dept_combo.grid(row=0, column=3, sticky="w", padx=(0, 14), pady=2)

    tk.Label(form_grid, text="Card ID *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=0, column=4, sticky="w", padx=(0, 4), pady=2)

    card_box = tk.Frame(form_grid, bg=COLORS["card"])
    card_box.grid(row=0, column=5, sticky="w", padx=(0, 4), pady=2)

    card_entry = styled_entry(card_box, width=12)
    card_entry.pack(side="left", ipady=3, padx=(0, 4))
    card_entry.insert(0, get_next_card_id("CSE"))

    # Auto-generate button for Card ID
    def generate_next_card():
        d = dept_var.get().split("/")[0].strip()
        card_entry.delete(0, tk.END)
        card_entry.insert(0, get_next_card_id(d))

    neutral_button(card_box, "⚡ Auto", generate_next_card, width=6).pack(side="left")

    def on_dept_change(event=None):
        generate_next_card()

    dept_combo.bind("<<ComboboxSelected>>", on_dept_change)

    # Row 1: Member Type, Phone, Email
    tk.Label(form_grid, text="Category *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    type_var = tk.StringVar(value="STUDENT")
    type_combo = ttk.Combobox(
        form_grid, textvariable=type_var, width=16,
        values=MEMBER_TYPES, state="readonly"
    )
    type_combo.grid(row=1, column=1, sticky="w", padx=(0, 14), pady=2)

    tk.Label(form_grid, text="Phone *", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)
    phone_entry = styled_entry(form_grid, width=18)
    phone_entry.grid(row=1, column=3, sticky="w", padx=(0, 14), pady=2, ipady=3)

    tk.Label(form_grid, text="Email", bg=COLORS["card"],
             fg=COLORS["text_secondary"], font=FONTS["small_b"]
             ).grid(row=1, column=4, sticky="w", padx=(0, 4), pady=2)
    email_entry = styled_entry(form_grid, width=22)
    email_entry.grid(row=1, column=5, sticky="w", padx=(0, 4), pady=2, ipady=3)

    # ---------- Action Toolbar (PACKED BEFORE TABLE FOR IMMEDIATE ACCESS) ----------
    button_row = tk.Frame(form_card, bg=COLORS["card_alt"], height=38)
    button_row.pack(fill="x", padx=1, pady=(4, 0), ipady=3)

    tk.Label(button_row, text=" Dept:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(8, 2))
    filter_dept_var = tk.StringVar(value="ALL")
    filter_dept_combo = ttk.Combobox(
        button_row, textvariable=filter_dept_var, width=7,
        values=["ALL", "CSE", "ME", "AE", "EE"], state="readonly"
    )
    filter_dept_combo.pack(side="left", padx=(0, 8))

    tk.Label(button_row, text="Search:", bg=COLORS["card_alt"],
             fg=COLORS["text_muted"], font=FONTS["small_b"]).pack(side="left", padx=(0, 2))
    search_entry = styled_entry(button_row, width=15)
    search_entry.pack(side="left", ipady=2, padx=(0, 10))

    success_button(button_row, "➕ Add Member",  lambda: add_member(),    width=13).pack(side="left", padx=2)
    primary_button(button_row, "💾 Update",      lambda: update_member(), width=10).pack(side="left", padx=2)
    danger_button (button_row, "🗑️ Delete",      lambda: delete_member(), width=10).pack(side="left", padx=2)
    neutral_button(button_row, "🔄 Clear",       lambda: clear_form(),    width=9).pack(side="left", padx=2)
    neutral_button(button_row, "🔁 Refresh",     lambda: refresh_table(), width=9).pack(side="left", padx=2)

    # ---------- Table Setup (AT BOTTOM) ----------
    columns = ("id", "card_id", "name", "dept", "mtype", "phone", "email")
    headings = ("ID", "Card ID", "Full Name", "Department", "Category", "Phone", "Email Address")
    widths = (45, 90, 190, 95, 85, 120, 200)

    tree = make_table(parent, columns, headings, widths, height=8)

    # ---------- Action Functions ----------
    def refresh_table():
        kw = search_entry.get().strip()
        dept_f = filter_dept_var.get()

        sql = """
            SELECT member_id, COALESCE(card_id, '-'), name,
                   COALESCE(dept, '-'), COALESCE(member_type, 'STUDENT'),
                   phone, COALESCE(email, '-')
            FROM members
            WHERE 1=1
        """
        params = []

        if dept_f != "ALL":
            sql += " AND dept = ?"
            params.append(dept_f)

        if kw:
            sql += " AND (name LIKE ? OR card_id LIKE ? OR phone LIKE ? OR email LIKE ? OR dept LIKE ?)"
            params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%", f"%{kw}%", f"%{kw}%"])

        sql += " ORDER BY member_id DESC"

        rows = get_rows(sql, tuple(params))
        populate_tree_with_striping(tree, rows)
        refresh_stats()

    search_entry.bind("<KeyRelease>", lambda e: refresh_table())
    filter_dept_combo.bind("<<ComboboxSelected>>", lambda e: refresh_table())

    def clear_form():
        name_entry.delete(0, tk.END)
        phone_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        dept_var.set("CSE")
        type_var.set("STUDENT")
        generate_next_card()
        tree.selection_remove(tree.selection())

    def add_member():
        name = name_entry.get().strip()
        card_id = card_entry.get().strip()
        dept = dept_var.get().split("/")[0].strip()
        mtype = type_var.get().split("/")[0].strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()

        if not name or not phone:
            show_warning("Required Fields", "Student name and phone number are required.")
            return

        if not card_id:
            card_id = get_next_card_id(dept)

        # Check unique card_id
        clash_card = get_one("SELECT member_id, name FROM members WHERE card_id = ?", (card_id,))
        if clash_card:
            show_error("Card ID Conflict", f"Card ID '{card_id}' is already assigned to {clash_card[1]}.")
            return

        if email:
            existing = get_one("SELECT member_id FROM members WHERE email = ?", (email,))
            if existing is not None:
                show_error("Duplicate Email", "This email address is already registered.")
                return
        else:
            email = None

        run_query(
            "INSERT INTO members (name, card_id, dept, member_type, phone, email) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, card_id, dept, mtype, phone, email)
        )
        show_success(
            "Registration Successful",
            f"Registered '{name}' successfully.\n\nAssigned Card ID: {card_id}\nDepartment: {dept}"
        )
        clear_form()
        refresh_table()

    def update_member():
        selected = tree.selection()
        if not selected:
            show_warning("Selection Required", "Select a student or member from the table to update.")
            return

        member_id = tree.item(selected[0])["values"][0]
        name = name_entry.get().strip()
        card_id = card_entry.get().strip()
        dept = dept_var.get().split("/")[0].strip()
        mtype = type_var.get().split("/")[0].strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()

        if not name or not phone or not card_id:
            show_warning("Required Fields", "Name, Card ID, and phone number are required.")
            return

        # Check unique card_id
        clash_card = get_one(
            "SELECT member_id FROM members WHERE card_id = ? AND member_id != ?",
            (card_id, member_id)
        )
        if clash_card:
            show_error("Card ID Conflict", f"Card ID '{card_id}' is already held by another student.")
            return

        if email:
            clash = get_one(
                "SELECT member_id FROM members WHERE email = ? AND member_id != ?",
                (email, member_id)
            )
            if clash is not None:
                show_error("Email Conflict", "This email belongs to another registered member.")
                return
        else:
            email = None

        run_query(
            "UPDATE members SET name = ?, card_id = ?, dept = ?, member_type = ?, phone = ?, email = ? "
            "WHERE member_id = ?",
            (name, card_id, dept, mtype, phone, email, member_id)
        )
        show_success("Updated", f"Member #{member_id} ({card_id}) updated successfully.")
        clear_form()
        refresh_table()

    def delete_member():
        selected = tree.selection()
        if not selected:
            show_warning("Selection Required", "Select a member from the table to delete.")
            return

        values = tree.item(selected[0])["values"]
        member_id = values[0]
        card_id = values[1]
        member_name = values[2]

        history = get_one("SELECT COUNT(*) FROM issue_return WHERE member_id = ?", (member_id,))
        if history[0] > 0:
            show_error(
                "Cannot Delete",
                "Cannot delete this member: active or historic book borrowing records exist on file."
            )
            return

        if not ask_confirm("Confirm Deletion", f"Permanently remove student '{member_name}' (Card: {card_id})?"):
            return

        run_query("DELETE FROM members WHERE member_id = ?", (member_id,))
        show_success("Deleted", "Record removed from registry.")
        clear_form()
        refresh_table()

    def on_row_select(event):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0])["values"]
        card_val = values[1] if values[1] != "-" else ""
        card_entry.delete(0, tk.END)
        card_entry.insert(0, card_val)

        name_entry.delete(0, tk.END)
        name_entry.insert(0, values[2])

        d_val = values[3] if values[3] in DEPARTMENTS else "CSE"
        dept_var.set(d_val)

        t_val = values[4] if values[4] in MEMBER_TYPES else "STUDENT"
        type_var.set(t_val)

        phone_entry.delete(0, tk.END)
        phone_entry.insert(0, values[5])

        email_entry.delete(0, tk.END)
        if values[6] and values[6] != "-":
            email_entry.insert(0, values[6])

    tree.bind("<<TreeviewSelect>>", on_row_select)

    refresh_table()