from flask import Flask, render_template, request
import sqlite3
from datetime import date, datetime

app = Flask(__name__)


def create_database():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            author TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issued_books (
            book_id TEXT,
            student_name TEXT,
            usn TEXT,
            branch TEXT,
            year TEXT,
            issue_date TEXT,
            return_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fine_records (
            student_name TEXT,
            book_id TEXT,
            book_name TEXT,
            late_days INTEGER,
            fine INTEGER
        )
    """)

    for column in ["usn", "branch", "year", "issue_date", "return_date"]:
        try:
            cursor.execute(
                f"ALTER TABLE issued_books ADD COLUMN {column} TEXT"
            )
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


create_database()


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "group13" and password == "1234":
            return render_template("index.html")
        else:
            return render_template(
                "login.html",
                message="Invalid username or password!"
            )

    return render_template("login.html")


# Home
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/home")
def library_home():
    return render_template("index.html")


# Add Book
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        book_name = request.form["book_name"]
        author = request.form["author"]
        book_id = request.form["book_id"]

        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO books (id, name, author) VALUES (?, ?, ?)",
            (book_id, book_name, author)
        )

        conn.commit()
        conn.close()

        return render_template(
            "add.html",
            message="Book Added Successfully!"
        )

    return render_template("add.html")


# View Books
@app.route("/view")
def view():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, author FROM books")
    books_data = cursor.fetchall()

    books = []

    for book in books_data:
        book_id = book[0]

        cursor.execute(
            "SELECT * FROM issued_books WHERE book_id = ?",
            (book_id,)
        )

        if cursor.fetchone():
            status = "Issued"
        else:
            status = "Available"

        books.append(
            (book[0], book[1], book[2], status)
        )

    conn.close()

    return render_template("view.html", books=books)


# Issue Book
@app.route("/issue", methods=["GET", "POST"])
def issue():
    if request.method == "POST":
        book_id = request.form["book_id"]
        student_name = request.form["student_name"]
        usn = request.form["usn"]
        branch = request.form["branch"]
        year = request.form["year"]
        issue_date = request.form["issue_date"]
        return_date = request.form["return_date"]

        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM books WHERE id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if not book:
            conn.close()
            return render_template(
                "issue.html",
                message="Book ID not found!"
            )

        cursor.execute(
            "SELECT * FROM issued_books WHERE book_id = ?",
            (book_id,)
        )

        if cursor.fetchone():
            conn.close()
            return render_template(
                "issue.html",
                message="Book is already issued!"
            )

        cursor.execute(
            """INSERT INTO issued_books
            (book_id, student_name, usn, branch, year, issue_date, return_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                book_id,
                student_name,
                usn,
                branch,
                year,
                issue_date,
                return_date
            )
        )

        conn.commit()
        conn.close()

        return render_template(
            "issue.html",
            message="Book " + book_id + " issued successfully!"
        )

    return render_template("issue.html")


# Return Book
@app.route("/return", methods=["GET", "POST"])
def return_book():
    if request.method == "POST":
        book_id = request.form["book_id"]

        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()

        cursor.execute(
            """SELECT student_name, return_date
               FROM issued_books
               WHERE book_id = ?""",
            (book_id,)
        )

        record = cursor.fetchone()

        if record:
            student_name = record[0]
            due_date = record[1]

            cursor.execute(
                "SELECT name FROM books WHERE id = ?",
                (book_id,)
            )

            book_record = cursor.fetchone()

            if book_record:
                book_name = book_record[0]
            else:
                book_name = book_id

            today = date.today()
            due = datetime.strptime(due_date, "%Y-%m-%d").date()

            late_days = (today - due).days

            if late_days < 0:
                late_days = 0

            fine = late_days * 5

            cursor.execute(
                """INSERT INTO fine_records
                (student_name, book_id, book_name, late_days, fine)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    student_name,
                    book_id,
                    book_name,
                    late_days,
                    fine
                )
            )

            cursor.execute(
                "DELETE FROM issued_books WHERE book_id = ?",
                (book_id,)
            )

            conn.commit()
            conn.close()

            return render_template(
                "return.html",
                student_name=student_name,
                book_id=book_id,
                late_days=late_days,
                fine=fine
            )

        conn.close()

        return render_template(
            "return.html",
            message="Book ID not found!"
        )

    return render_template("return.html")


# Issued Books
@app.route("/issued")
def issued():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT book_id, student_name, usn, branch, year,
               issue_date, return_date
        FROM issued_books
    """)

    issued_books = cursor.fetchall()

    conn.close()

    return render_template(
        "issued.html",
        issued_books=issued_books
    )


# Fine Records
@app.route("/fine")
def fine():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student_name, book_id, book_name, late_days, fine
        FROM fine_records
    """)

    fine_records = cursor.fetchall()

    conn.close()

    return render_template(
        "fine.html",
        fine_records=fine_records
    )


# Student Details
@app.route("/student")
def student():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student_name, usn, branch, year,
               book_id, issue_date, return_date
        FROM issued_books
    """)

    students = cursor.fetchall()

    conn.close()

    return render_template(
        "student.html",
        students=students
    )


# Search Books
@app.route("/search", methods=["GET", "POST"])
def search():
    books = []

    if request.method == "POST":
        search_text = request.form["search_text"]

        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, author
            FROM books
            WHERE id LIKE ? OR name LIKE ?
        """, (f"%{search_text}%", f"%{search_text}%"))

        books_data = cursor.fetchall()

        for book in books_data:
            cursor.execute(
                "SELECT * FROM issued_books WHERE book_id = ?",
                (book[0],)
            )

            if cursor.fetchone():
                status = "Issued"
            else:
                status = "Available"

            books.append(
                (book[0], book[1], book[2], status)
            )

        conn.close()

    return render_template("search.html", books=books)


# Delete Book
@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == "POST":
        book_id = request.form["book_id"]

        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if not book:
            conn.close()
            return render_template(
                "delete.html",
                message="Book ID not found!"
            )

        cursor.execute(
            "SELECT * FROM issued_books WHERE book_id = ?",
            (book_id,)
        )

        if cursor.fetchone():
            conn.close()
            return render_template(
                "delete.html",
                message="Cannot delete an issued book!"
            )

        cursor.execute(
            "DELETE FROM books WHERE id = ?",
            (book_id,)
        )

        conn.commit()
        conn.close()

        return render_template(
            "delete.html",
            message="Book deleted successfully!"
        )

    return render_template("delete.html")

# Clear Fine Records
@app.route("/clear_fines", methods=["POST"])
def clear_fines():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM fine_records")

    conn.commit()
    conn.close()

    return render_template(
        "fine.html",
        fine_records=[],
        message="All fine records cleared successfully!"
    )

if __name__ == "__main__":
    app.run(debug=True)