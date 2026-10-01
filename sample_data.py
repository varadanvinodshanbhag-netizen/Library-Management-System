# sample_data.py
# Fill the database with realistic demo data. Safe to run multiple times.

import sqlite3
from datetime import date

DB = "library.db"


def get_or_create(cur, table, id_col, name_col, name):
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {name_col} = ?", (name,))
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute(f"INSERT INTO {table} ({name_col}) VALUES (?)", (name,))
    return cur.lastrowid


def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ---- Authors ----
    print("Inserting authors + categories...")
    authors = [
        "R. S. Aggarwal", "Yashavant Kanetkar", "E. Balagurusamy",
        "Sumita Arora", "Herbert Schildt", "Reema Thareja",
        "M. Morris Mano", "Andrew S. Tanenbaum", "Bjarne Stroustrup",
        "Cormen (CLRS)",
    ]
    categories = [
        "Programming", "Data Structures", "Algorithms",
        "Mathematics", "Operating Systems", "Networking",
        "Databases", "Electronics",
    ]
    for a in authors:
        get_or_create(cur, "authors", "author_id", "author_name", a)
    for c in categories:
        get_or_create(cur, "categories", "category_id", "category_name", c)

    # ---- Books ----
    print("Inserting books...")
    books = [
        ("Python Programming",           "R. S. Aggarwal",      "Programming",      3),
        ("Let Us C",                     "Yashavant Kanetkar",  "Programming",      4),
        ("Data Structures Made Easy",    "E. Balagurusamy",     "Data Structures",  3),
        ("Python for Beginners",         "Sumita Arora",        "Programming",      2),
        ("C++: The Complete Reference",  "Herbert Schildt",     "Programming",      2),
        ("Data Structures Using C",      "Reema Thareja",       "Data Structures",  5),
        ("Computer System Architecture", "M. Morris Mano",      "Electronics",      3),
        ("Modern Operating Systems",     "Andrew S. Tanenbaum", "Operating Systems",2),
        ("The C++ Programming Language", "Bjarne Stroustrup",   "Programming",      2),
        ("Introduction to Algorithms",   "Cormen (CLRS)",       "Algorithms",       3),
        ("Discrete Mathematics",         "R. S. Aggarwal",      "Mathematics",      4),
        ("Database System Concepts",     "Sumita Arora",        "Databases",        3),
        ("Computer Networks",            "Andrew S. Tanenbaum", "Networking",       2),
        ("Let Us C++",                   "Yashavant Kanetkar",  "Programming",      3),
        ("Operating System Concepts",    "M. Morris Mano",      "Operating Systems",2),
    ]
    for title, author, cat, total in books:
        aid = get_or_create(cur, "authors", "author_id", "author_name", author)
        cid = get_or_create(cur, "categories", "category_id", "category_name", cat)
        cur.execute("SELECT book_id FROM books WHERE title = ? AND author_id = ?", (title, aid))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO books
                (title, author_id, category_id, total_copies, available_copies)
                VALUES (?, ?, ?, ?, ?)
            """, (title, aid, cid, total, total))

    # ---- Members ----
    print("Inserting members...")
    members = [
        ("Rahul Sharma",   "rahul@example.com",   "9876543210"),
        ("Priya Verma",    "priya@example.com",   "9876501234"),
        ("Aarav Naik",     "aarav@example.com",   "9123456780"),
        ("Diya Shetty",    "diya@example.com",    "9123456781"),
        ("Kabir Gowda",    "kabir@example.com",   "9123456782"),
        ("Ananya Mesta",   "ananya@example.com",  "9123456783"),
        ("Rohan Hegde",    "rohan@example.com",   "9123456784"),
        ("Sneha Acharya",  "sneha@example.com",   "9123456785"),
        ("Arjun Bhat",     "arjun@example.com",   "9123456786"),
        ("Isha Kulkarni",  "isha@example.com",    "9123456787"),
    ]
    for name, email, phone in members:
        cur.execute("SELECT member_id FROM members WHERE email = ?", (email,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO members (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone)
            )

    # ---- Magazines ----
    print("Inserting magazines...")
    magazines = [
        ("India Today",         "Living Media", "October",   2026, "News",    5),
        ("Frontline",           "The Hindu",    "October",   2026, "News",    3),
        ("Digit",               "9.9 Group",    "September", 2026, "Tech",    4),
        ("Electronics For You", "EFY",          "October",   2026, "Tech",    3),
        ("National Geographic", "NatGeo",       "September", 2026, "Science", 2),
    ]
    for name, pub, month, year, cat, qty in magazines:
        cur.execute("SELECT magazine_id FROM magazines WHERE name = ? AND year = ?", (name, year))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO magazines
                (name, publisher, month, year, category, quantity, available, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, date('now'))
            """, (name, pub, month, year, cat, qty, qty))

    # ---- Newspapers ----
    print("Inserting newspapers...")
    newspapers = [
        ("The Hindu",        "The Hindu Group",  "English", 5),
        ("Times of India",   "Bennett Coleman",  "English", 4),
        ("Vijaya Karnataka", "Times Group",      "Kannada", 3),
        ("Deccan Herald",    "DH Group",         "English", 3),
    ]
    today = date.today().isoformat()
    for name, pub, lang, qty in newspapers:
        cur.execute("SELECT newspaper_id FROM newspapers WHERE name = ?", (name,))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO newspapers
                (name, publisher, pub_date, language, quantity, available, date_added)
                VALUES (?, ?, ?, ?, ?, ?, date('now'))
            """, (name, pub, today, lang, qty, qty))

    conn.commit()

    # ---- Summary ----
    b = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    m = cur.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    mag = cur.execute("SELECT COUNT(*) FROM magazines").fetchone()[0]
    n = cur.execute("SELECT COUNT(*) FROM newspapers").fetchone()[0]

    conn.close()
    print(f"\n✅ Sample data inserted:")
    print(f"   Books:      {b}")
    print(f"   Members:    {m}")
    print(f"   Magazines:  {mag}")
    print(f"   Newspapers: {n}")


if __name__ == "__main__":
    main()