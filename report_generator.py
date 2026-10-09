# ============================================================
# report_generator.py
# Data fetching for all report types + CSV export.
# reports_ui.py calls these functions.
# ============================================================

import csv
from datetime import datetime
from db import get_rows


# ------------------------------------------------------------
# Every report returns: (headings: list[str], rows: list[tuple])
# ------------------------------------------------------------

# ---------- Books ----------
def report_all_books():
    headings = ["ID", "Title", "Author", "Category", "Total", "Available"]
    rows = get_rows("""
        SELECT b.book_id, b.title, a.author_name, c.category_name,
               b.total_copies, b.available_copies
        FROM books b
        JOIN authors a    ON b.author_id    = a.author_id
        JOIN categories c ON b.category_id  = c.category_id
        ORDER BY b.book_id
    """)
    return headings, rows


def report_available_books():
    headings = ["ID", "Title", "Author", "Available"]
    rows = get_rows("""
        SELECT b.book_id, b.title, a.author_name, b.available_copies
        FROM books b
        JOIN authors a ON b.author_id = a.author_id
        WHERE b.available_copies > 0
        ORDER BY b.book_id
    """)
    return headings, rows


# ---------- Issue / Return ----------
def report_issued_books():
    headings = ["Issue ID", "Book", "Member", "Card ID", "Issue Date", "Due Date", "Status"]
    rows = get_rows("""
        SELECT ir.issue_id, b.title, m.name, COALESCE(m.card_id, '-'),
               ir.issue_date, ir.due_date, ir.status
        FROM issue_return ir
        JOIN books b   ON ir.book_id   = b.book_id
        JOIN members m ON ir.member_id = m.member_id
        WHERE ir.status = 'ISSUED'
        ORDER BY ir.issue_id DESC
    """)
    return headings, rows


def report_returned_books():
    headings = ["Issue ID", "Book", "Member", "Card ID", "Issue Date", "Returned On", "Overdue Days", "Fine"]
    rows = get_rows("""
        SELECT ir.issue_id, b.title, m.name, COALESCE(m.card_id, '-'), ir.issue_date,
               COALESCE(ir.actual_return_date, ir.return_date),
               ir.overdue_days, ir.fine_amount
        FROM issue_return ir
        JOIN books b   ON ir.book_id   = b.book_id
        JOIN members m ON ir.member_id = m.member_id
        WHERE ir.status = 'RETURNED'
        ORDER BY ir.issue_id DESC
    """)
    return headings, rows


def report_overdue_books():
    headings = ["Issue ID", "Book", "Member", "Card ID", "Due Date", "Days Overdue"]
    rows = get_rows("""
        SELECT ir.issue_id, b.title, m.name, COALESCE(m.card_id, '-'), ir.due_date,
               CAST(julianday('now') - julianday(ir.due_date) AS INTEGER) AS days_late
        FROM issue_return ir
        JOIN books b   ON ir.book_id   = b.book_id
        JOIN members m ON ir.member_id = m.member_id
        WHERE ir.status = 'ISSUED'
          AND ir.due_date IS NOT NULL
          AND date(ir.due_date) < date('now')
        ORDER BY days_late DESC
    """)
    return headings, rows


# ---------- Members ----------
def report_members():
    headings = ["ID", "Card ID", "Name", "Department", "Category", "Phone", "Email", "Portal Login"]
    rows = get_rows("""
        SELECT m.member_id, COALESCE(m.card_id, '-'), m.name,
               COALESCE(m.dept, 'CSE'), COALESCE(m.member_type, 'STUDENT'),
               m.phone, m.email,
               CASE
                   WHEN ma.account_id IS NULL THEN 'No Account'
                   WHEN ma.is_active = 1 THEN 'Active'
                   ELSE 'Disabled'
               END
        FROM members m
        LEFT JOIN member_accounts ma ON m.member_id = ma.member_id
        ORDER BY m.member_id
    """)
    return headings, rows


def report_member_borrowing(member_id=None):
    headings = ["Issue ID", "Member", "Card ID", "Book", "Issued", "Returned", "Status", "Fine"]
    sql = """
        SELECT ir.issue_id, m.name, COALESCE(m.card_id, '-'), b.title, ir.issue_date,
               COALESCE(ir.actual_return_date, ir.return_date),
               ir.status, ir.fine_amount
        FROM issue_return ir
        JOIN books b   ON ir.book_id   = b.book_id
        JOIN members m ON ir.member_id = m.member_id
    """
    params = []
    if member_id is not None:
        sql += " WHERE ir.member_id = ?"
        params.append(member_id)
    sql += " ORDER BY ir.issue_id DESC"

    rows = get_rows(sql, tuple(params))
    return headings, rows


# ---------- Fines ----------
def report_fines(status=None):
    headings = ["Fine ID", "Member", "Book", "Amount", "Status", "Generated", "Paid"]
    sql = """
        SELECT f.fine_id, m.name, b.title, f.amount,
               f.status, f.generated_on, f.paid_on
        FROM fines f
        JOIN issue_return ir ON f.issue_id = ir.issue_id
        JOIN books b ON ir.book_id = b.book_id
        JOIN members m ON f.member_id = m.member_id
    """
    params = []
    if status:
        sql += " WHERE f.status = ?"
        params.append(status)
    sql += " ORDER BY f.fine_id DESC"

    rows = get_rows(sql, tuple(params))
    return headings, rows


def report_fine_collection():
    headings = ["Status", "Count", "Total Amount"]
    rows = get_rows("""
        SELECT status, COUNT(*), COALESCE(SUM(amount), 0)
        FROM fines
        GROUP BY status
        ORDER BY status
    """)
    return headings, rows


# ---------- Magazines / Newspapers ----------
def report_magazines():
    headings = ["ID", "Name", "Publisher", "Month", "Year", "Category", "Qty", "Available"]
    rows = get_rows("""
        SELECT magazine_id, name, publisher, month, year,
               category, quantity, available
        FROM magazines
        ORDER BY magazine_id DESC
    """)
    return headings, rows


def report_newspapers():
    headings = ["ID", "Name", "Publisher", "Date", "Language", "Qty", "Available"]
    rows = get_rows("""
        SELECT newspaper_id, name, publisher, pub_date, language,
               quantity, available
        FROM newspapers
        ORDER BY newspaper_id DESC
    """)
    return headings, rows


# ------------------------------------------------------------
# Report registry (used by reports_ui.py)
# ------------------------------------------------------------
REPORTS = {
    "All Books":             report_all_books,
    "Available Books":       report_available_books,
    "Issued Books":          report_issued_books,
    "Returned Books":        report_returned_books,
    "Overdue Books":         report_overdue_books,
    "Members":               report_members,
    "Member Borrowing":      report_member_borrowing,
    "Fines (all)":           lambda: report_fines(None),
    "Fines (unpaid)":        lambda: report_fines("UNPAID"),
    "Fines (paid)":          lambda: report_fines("PAID"),
    "Fine Collection":       report_fine_collection,
    "Magazines":             report_magazines,
    "Newspapers":            report_newspapers,
}


# ------------------------------------------------------------
# Export rows to a CSV file
# ------------------------------------------------------------
def export_to_csv(headings, rows, filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headings)
        for r in rows:
            writer.writerow(r)


# ------------------------------------------------------------
# Quick self-test
# ------------------------------------------------------------
if __name__ == "__main__":
    for name, fn in REPORTS.items():
        try:
            h, r = fn()
            print(f"{name:25} -> {len(r)} rows")
        except Exception as e:
            print(f"{name:25} -> ERROR: {e}")