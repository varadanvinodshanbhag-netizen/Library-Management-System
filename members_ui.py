# ============================================================
# members_ui.py
# Member Management screen: add / update / delete / display.
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from db import run_query, get_rows, get_one


def show_members_screen(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    tk.Label(parent, text="Member Management", font=("Arial", 16, "bold"), bg="white").pack(pady=8)

    # ---------- Form ----------
    form = tk.Frame(parent, bg="white")
    form.pack(pady=5)

    tk.Label(form, text="Name", bg="white").grid(row=0, column=0, padx=6, pady=4, sticky="e")
    name_entry = tk.Entry(form, width=28)
    name_entry.grid(row=0, column=1, padx=6, pady=4)

    tk.Label(form, text="Phone", bg="white").grid(row=0, column=2, padx=6, pady=4, sticky="e")
    phone_entry = tk.Entry(form, width=28)
    phone_entry.grid(row=0, column=3, padx=6, pady=4)

    tk.Label(form, text="Email", bg="white").grid(row=1, column=0, padx=6, pady=4, sticky="e")
    email_entry = tk.Entry(form, width=28)
    email_entry.grid(row=1, column=1, padx=6, pady=4)

    # ---------- Table ----------
    table_frame = tk.Frame(parent, bg="white")
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    columns = ("id", "name", "phone", "email")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

    tree.heading("id", text="ID")
    tree.heading("name", text="Name")
    tree.heading("phone", text="Phone")
    tree.heading("email", text="Email")

    tree.column("id", width=60, anchor="center")
    tree.column("name", width=220)
    tree.column("phone", width=160)
    tree.column("email", width=260)

    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)

    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)
        rows = get_rows("SELECT member_id, name, phone, email FROM members ORDER BY member_id")
        for row in rows:
            tree.insert("", tk.END, values=row)

    def clear_form():
        name_entry.delete(0, tk.END)
        phone_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        tree.selection_remove(tree.selection())

    def add_member():
        name = name_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()

        if name == "" or phone == "":
            messagebox.showwarning("Warning", "Name and phone are required.")
            return

        if email != "":
            existing = get_one("SELECT member_id FROM members WHERE email = ?", (email,))
            if existing is not None:
                messagebox.showerror("Error", "This email is already registered.")
                return
        else:
            email = None

        run_query(
            "INSERT INTO members (name, phone, email) VALUES (?, ?, ?)",
            (name, phone, email)
        )
        messagebox.showinfo("Success", "Member added.")
        clear_form()
        refresh_table()

    def update_member():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a member from the table first.")
            return

        member_id = tree.item(selected[0])["values"][0]
        name = name_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()

        if name == "" or phone == "":
            messagebox.showwarning("Warning", "Name and phone are required.")
            return

        if email != "":
            clash = get_one(
                "SELECT member_id FROM members WHERE email = ? AND member_id != ?",
                (email, member_id)
            )
            if clash is not None:
                messagebox.showerror("Error", "This email belongs to another member.")
                return
        else:
            email = None

        run_query(
            "UPDATE members SET name = ?, phone = ?, email = ? WHERE member_id = ?",
            (name, phone, email, member_id)
        )
        messagebox.showinfo("Success", "Member updated.")
        clear_form()
        refresh_table()

    def delete_member():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a member from the table first.")
            return

        values = tree.item(selected[0])["values"]
        member_id = values[0]
        member_name = values[1]

        history = get_one("SELECT COUNT(*) FROM issue_return WHERE member_id = ?", (member_id,))
        if history[0] > 0:
            messagebox.showerror("Error", "Cannot delete: this member has issue/return history.")
            return

        if not messagebox.askyesno("Confirm", f"Delete member '{member_name}' ?"):
            return

        run_query("DELETE FROM members WHERE member_id = ?", (member_id,))
        messagebox.showinfo("Success", "Member deleted.")
        clear_form()
        refresh_table()

    def on_row_select(event):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0])["values"]
        name_entry.delete(0, tk.END);  name_entry.insert(0, values[1])
        phone_entry.delete(0, tk.END); phone_entry.insert(0, values[2])
        email_entry.delete(0, tk.END)
        if values[3] is not None:
            email_entry.insert(0, values[3])

    tree.bind("<<TreeviewSelect>>", on_row_select)

    button_row = tk.Frame(parent, bg="white")
    button_row.pack(pady=6)

    tk.Button(button_row, text="Add Member",  width=12, command=add_member).grid(row=0, column=0, padx=5)
    tk.Button(button_row, text="Update",      width=12, command=update_member).grid(row=0, column=1, padx=5)
    tk.Button(button_row, text="Delete",      width=12, command=delete_member).grid(row=0, column=2, padx=5)
    tk.Button(button_row, text="Clear Form",  width=12, command=clear_form).grid(row=0, column=3, padx=5)
    tk.Button(button_row, text="Refresh",     width=12, command=refresh_table).grid(row=0, column=4, padx=5)

    refresh_table()