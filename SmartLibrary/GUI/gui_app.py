# gui_app.py
import sys
from datetime import datetime, timedelta
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QFormLayout, QSpinBox, QComboBox
)
from PyQt5.QtCore import Qt

# If you already have backend/*.py files and want to use them, they'll still be used for convenience.
# But this file is self-contained for GUI+DB operations.
try:
    from backend.user import User  # optional, used if available
except Exception:
    User = None

try:
    from backend.member import Member  # optional wrapper class
except Exception:
    Member = None

try:
    from backend.librarian import Librarian  # optional wrapper class
except Exception:
    Librarian = None

# ---------------- Database Config ----------------
db_config = {
    "host": "localhost",
    "database": "smartlibrary",
    "user": "postgres",
    "password": "Pes@2022"
}

# ---------------- Utility: detect user table ----------------
def detect_user_table():
    """
    Return a safe table identifier to use for queries that need the users table.
    It tries several common names and falls back to searching information_schema.
    The return value is the table identifier to insert directly into SQL (e.g. user_account or "User").
    """
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        # Try some common names in order
        candidates = ['user', 'user_account', 'users', 'User']
        for name in candidates:
            cur.execute("SELECT to_regclass(%s);", (f'public.{name}',))
            res = cur.fetchone()
            if res and res[0]:
                # if name contains uppercase letters, we need to quote it in SQL
                if any(c.isupper() for c in name):
                    return f'"{name}"'
                else:
                    return name

        # fallback: find any table name starting with user (case-insensitive)
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_name ILIKE 'user%'
            LIMIT 1;
        """)
        r = cur.fetchone()
        if r:
            t = r[0]
            if any(c.isupper() for c in t):
                return f'"{t}"'
            else:
                return t

        # if none found, return plain user (will likely error)
        return 'user'
    except Exception:
        # fallback
        return 'user'
    finally:
        if conn:
            conn.close()

# Detect once at module load
USER_TABLE_IDENTIFIER = detect_user_table()


# ---------------- Helper Functions ----------------
def get_conn_cursor():
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    return conn, cur

def get_books():
    conn, cur = get_conn_cursor()
    try:
        cur.execute("SELECT book_id, title, category, isbn, copies_available FROM book ORDER BY book_id;")
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()

def get_authors():
    conn, cur = get_conn_cursor()
    try:
        cur.execute("SELECT author_id, full_name FROM author ORDER BY author_id;")
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()

def get_most_borrowed(limit=5):
    conn, cur = get_conn_cursor()
    try:
        cur.execute("""
            SELECT b.book_id, b.title, COUNT(*) as cnt
            FROM loan l JOIN book b ON l.book_id = b.book_id
            GROUP BY b.book_id, b.title
            ORDER BY cnt DESC
            LIMIT %s;
        """, (limit,))
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()

def get_active_loans_for_member(member_id):
    conn, cur = get_conn_cursor()
    try:
        cur.execute("""
            SELECT l.loan_id, b.book_id, b.title, l.borrow_date, l.due_date
            FROM loan l JOIN book b ON l.book_id = b.book_id
            WHERE l.member_id=%s AND l.returned=FALSE;
        """, (member_id,))
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()

def get_members_count():
    conn, cur = get_conn_cursor()
    try:
        # Use detected user table identifier
        cur.execute(f"SELECT COUNT(*) FROM {USER_TABLE_IDENTIFIER} WHERE role_id=2;")
        count = cur.fetchone()[0]
        return count
    finally:
        cur.close()
        conn.close()

def get_active_loans_count():
    conn, cur = get_conn_cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM loan WHERE returned=FALSE;")
        count = cur.fetchone()[0]
        return count
    finally:
        cur.close()
        conn.close()

def get_bookclubs():
    conn, cur = get_conn_cursor()
    try:
        cur.execute("SELECT club_id, club_name, moderator_id FROM bookclub ORDER BY club_id;")
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()

def get_bookclub_members(club_id):
    conn, cur = get_conn_cursor()
    try:
        # use detected user table identifier
        cur.execute(f"""
            SELECT u.user_id, u.full_name
            FROM bookclubmembers bcm
            JOIN {USER_TABLE_IDENTIFIER} u ON bcm.member_id = u.user_id
            WHERE bcm.club_id = %s;
        """, (club_id,))
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()

# ---------------- Pages / Widgets ----------------
class LoginPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("SmartLibrary Login")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addRow("Username:", self.username)
        form.addRow("Password:", self.password)
        layout.addLayout(form)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.do_login)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def do_login(self):
        uname = self.username.text().strip()
        pwd = self.password.text().strip()
        if not uname or not pwd:
            QMessageBox.warning(self, "Login", "Enter username and password")
            return

        # Prefer using backend.User if available (you said your previous login works)
        if User:
            try:
                row = User(db_config).login(uname, pwd)
            except Exception as e:
                row = None
        else:
            # fallback: direct DB query using detected table
            conn, cur = None, None
            try:
                conn = psycopg2.connect(**db_config)
                cur = conn.cursor()
                # Make safe query using detected table
                # some user tables may have more columns; we select first three expected ones
                query = f"SELECT user_id, full_name, role_id FROM {USER_TABLE_IDENTIFIER} WHERE username = %s AND password = %s;"
                cur.execute(query, (uname, pwd))
                row = cur.fetchone()
            except Exception as e:
                QMessageBox.critical(self, "Login error", f"Login query failed: {e}")
                row = None
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()

        if not row:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")
            return

        # row may contain 3 or more columns; handle robustly
        try:
            user_id = row[0]
            full_name = row[1]
            role_id = row[2]
        except Exception:
            QMessageBox.critical(self, "Login Failed", "Unexpected user row format from database")
            return

        QMessageBox.information(self, "Welcome", f"Welcome {full_name}!")

        if role_id == 1:
            self.parent.current_user = {'id': user_id, 'name': full_name, 'role': 'librarian'}
            # use backend librarian if available
            if Librarian:
                try:
                    self.parent.backend_user = Librarian(db_config, user_id, full_name)
                except Exception:
                    self.parent.backend_user = None
            else:
                self.parent.backend_user = None
            self.parent.setup_for_librarian()
        else:
            self.parent.current_user = {'id': user_id, 'name': full_name, 'role': 'member'}
            if Member:
                try:
                    self.parent.backend_user = Member(db_config, user_id, full_name)
                except Exception:
                    self.parent.backend_user = None
            else:
                self.parent.backend_user = None
            self.parent.setup_for_member()

        self.parent.switch_to_main()

class Sidebar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(6,6,6,6)

        self.lbl_user = QLabel("Not logged in")
        self.lbl_user.setStyleSheet("font-weight:bold;")
        layout.addWidget(self.lbl_user)
        layout.addSpacing(10)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_catalog = QPushButton("Catalog")
        self.btn_loans = QPushButton("Loans")
        self.btn_books = QPushButton("Manage Books")
        self.btn_authors = QPushButton("Manage Authors")
        self.btn_clubs = QPushButton("Book Clubs")
        self.btn_logout = QPushButton("Logout")

        for b in (self.btn_dashboard, self.btn_catalog, self.btn_loans,
                  self.btn_books, self.btn_authors, self.btn_clubs, self.btn_logout):
            b.setFixedHeight(36)
            layout.addWidget(b)

        layout.addStretch()
        self.setLayout(layout)

        self.btn_dashboard.clicked.connect(lambda: self.parent.show_page("dashboard"))
        self.btn_catalog.clicked.connect(lambda: self.parent.show_page("catalog"))
        self.btn_loans.clicked.connect(lambda: self.parent.show_page("loans"))
        self.btn_books.clicked.connect(lambda: self.parent.show_page("books"))
        self.btn_authors.clicked.connect(lambda: self.parent.show_page("authors"))
        self.btn_clubs.clicked.connect(lambda: self.parent.show_page("clubs"))
        self.btn_logout.clicked.connect(self.parent.logout)

class DashboardPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        self.lbl_summary = QLabel("")
        layout.addWidget(self.lbl_summary)

        self.tbl_most = QTableWidget(0,3)
        self.tbl_most.setHorizontalHeaderLabels(["Book ID","Title","Borrowed Count"])
        layout.addWidget(QLabel("Most Borrowed Books"))
        layout.addWidget(self.tbl_most)

        layout.addStretch()
        self.setLayout(layout)

    def refresh(self):
        books = get_books()
        members = get_members_count()
        active_loans = get_active_loans_count()
        self.lbl_summary.setText(f"Books: {len(books)}    Members: {members}    Active Loans: {active_loans}")

        rows = get_most_borrowed()
        self.tbl_most.setRowCount(0)
        for r in rows:
            row_idx = self.tbl_most.rowCount()
            self.tbl_most.insertRow(row_idx)
            for c, val in enumerate(r):
                self.tbl_most.setItem(row_idx, c, QTableWidgetItem(str(val)))

class CatalogPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        title = QLabel("Book Catalog")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title or category")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search)
        hl = QHBoxLayout()
        hl.addWidget(self.search_input)
        hl.addWidget(self.search_btn)
        layout.addLayout(hl)

        self.tbl = QTableWidget(0,5)
        self.tbl.setHorizontalHeaderLabels(["ID","Title","Category","ISBN","Available"])
        layout.addWidget(self.tbl)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_all)
        self.btn_borrow = QPushButton("Borrow Selected")
        self.btn_borrow.clicked.connect(self.borrow_selected)
        hl2 = QHBoxLayout()
        hl2.addWidget(self.btn_refresh)
        hl2.addWidget(self.btn_borrow)
        layout.addLayout(hl2)

        self.setLayout(layout)
        self.load_all()

    def load_all(self):
        rows = get_books()
        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            for c, val in enumerate(r):
                self.tbl.setItem(i,c,QTableWidgetItem(str(val)))

    def search(self):
        term = self.search_input.text().strip()
        conn, cur = get_conn_cursor()
        try:
            cur.execute("""
                SELECT book_id, title, category, isbn, copies_available
                FROM book
                WHERE title ILIKE %s OR category ILIKE %s
                ORDER BY book_id
            """, (f"%{term}%", f"%{term}%"))
            rows = cur.fetchall()
        except Exception as e:
            QMessageBox.critical(self, "Search error", f"Failed to search books: {e}")
            rows = []
        finally:
            cur.close(); conn.close()
        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            for c, val in enumerate(r):
                self.tbl.setItem(i,c,QTableWidgetItem(str(val)))

    def borrow_selected(self):
        sel = self.tbl.currentRow()
        if sel < 0:
            QMessageBox.warning(self,"Borrow","Select a row first")
            return
        book_id = int(self.tbl.item(sel,0).text())
        if self.parent.current_user['role'] != 'member':
            QMessageBox.information(self,"Borrow","Only members can borrow")
            return
        try:
            # call backend if available
            if self.parent.backend_user and hasattr(self.parent.backend_user, 'borrow_book'):
                res = self.parent.backend_user.borrow_book(book_id)
                # Expect backend to print/return status; we'll refresh regardless
            else:
                # Direct DB actions: enforce max 3 loans, copies_available, insert loan, decrement copies
                conn, cur = get_conn_cursor()
                try:
                    # Check active loans
                    cur.execute("SELECT COUNT(*) FROM loan WHERE member_id=%s AND returned=FALSE;", (self.parent.current_user['id'],))
                    active_loans = cur.fetchone()[0]
                    if active_loans >= 3:
                        QMessageBox.warning(self, "Borrow", "Cannot borrow more than 3 books.")
                        cur.close(); conn.close()
                        return
                    # Check stock
                    cur.execute("SELECT copies_available FROM book WHERE book_id=%s;", (book_id,))
                    s = cur.fetchone()
                    if not s or s[0] <= 0:
                        QMessageBox.warning(self,"Borrow","Book not available.")
                        cur.close(); conn.close()
                        return
                    borrow_date = datetime.now()
                    due_date = borrow_date + timedelta(days=7)  # 7 day loans
                    cur.execute("INSERT INTO loan (book_id, member_id, borrow_date, due_date, returned) VALUES (%s, %s, %s, %s, FALSE)",
                                (book_id, self.parent.current_user['id'], borrow_date, due_date))
                    cur.execute("UPDATE book SET copies_available = copies_available - 1 WHERE book_id=%s;", (book_id,))
                    conn.commit()
                    QMessageBox.information(self,"Borrow","Book borrowed successfully.")
                except Exception as e:
                    conn.rollback()
                    QMessageBox.critical(self,"Borrow error", f"Failed to borrow book: {e}")
                finally:
                    cur.close(); conn.close()
        except Exception as e:
            QMessageBox.critical(self,"Borrow error", f"Failed: {e}")
        # refresh
        self.load_all()
        if hasattr(self.parent, 'dashboard') and self.parent.dashboard:
            self.parent.dashboard.refresh()

class LoansPage(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        title = QLabel("Active Loans")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        self.tbl = QTableWidget(0,5)
        self.tbl.setHorizontalHeaderLabels(["Loan ID","Book ID","Title","Borrowed","Due"])
        layout.addWidget(self.tbl)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_loans)
        self.btn_return = QPushButton("Return Selected")
        self.btn_return.clicked.connect(self.return_selected)
        hl = QHBoxLayout()
        hl.addWidget(self.btn_refresh)
        hl.addWidget(self.btn_return)
        layout.addLayout(hl)
        self.setLayout(layout)

    def load_loans(self):
        if self.parent.current_user['role'] != 'member':
            self.tbl.setRowCount(0)
            return
        member_id = self.parent.current_user['id']
        rows = get_active_loans_for_member(member_id)
        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            for c, val in enumerate(r):
                self.tbl.setItem(i,c,QTableWidgetItem(str(val)))

    def return_selected(self):
        sel = self.tbl.currentRow()
        if sel < 0:
            QMessageBox.warning(self,"Return","Select a loan first")
            return
        loan_id = int(self.tbl.item(sel,0).text())
        if self.parent.current_user['role'] != 'member':
            QMessageBox.information(self,"Return","Only members can return")
            return
        try:
            if self.parent.backend_user and hasattr(self.parent.backend_user, 'return_book'):
                self.parent.backend_user.return_book(loan_id)
            else:
                conn, cur = get_conn_cursor()
                try:
                    # get book id
                    cur.execute("SELECT book_id FROM loan WHERE loan_id=%s AND returned=FALSE;", (loan_id,))
                    row = cur.fetchone()
                    if not row:
                        QMessageBox.warning(self,"Return","Loan not found or already returned")
                        cur.close(); conn.close()
                        return
                    book_id = row[0]
                    cur.execute("UPDATE loan SET returned=TRUE WHERE loan_id=%s;", (loan_id,))
                    cur.execute("UPDATE book SET copies_available = copies_available + 1 WHERE book_id=%s;", (book_id,))
                    conn.commit()
                    QMessageBox.information(self,"Return","Book returned successfully.")
                except Exception as e:
                    conn.rollback()
                    QMessageBox.critical(self,"Return error", f"Failed to return book: {e}")
                finally:
                    cur.close(); conn.close()
        except Exception as e:
            QMessageBox.critical(self,"Return error", f"Failed: {e}")

        self.load_loans()
        if hasattr(self.parent, 'catalog'):
            self.parent.catalog.load_all()
        if hasattr(self.parent, 'dashboard'):
            self.parent.dashboard.refresh()

# ---------------- Librarian CRUD Pages ----------------
class BooksPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        title = QLabel("Manage Books")
        title.setStyleSheet("font-size:18px;font-weight:bold;")
        layout.addWidget(title)

        self.tbl = QTableWidget(0,5)
        self.tbl.setHorizontalHeaderLabels(["ID","Title","Category","ISBN","Available"])
        layout.addWidget(self.tbl)

        form = QFormLayout()
        self.input_title = QLineEdit()
        self.input_category = QLineEdit()
        self.input_isbn = QLineEdit()
        self.input_copies = QSpinBox()
        self.input_copies.setMinimum(0)
        form.addRow("Title:", self.input_title)
        form.addRow("Category:", self.input_category)
        form.addRow("ISBN:", self.input_isbn)
        form.addRow("Copies:", self.input_copies)
        layout.addLayout(form)

        hl = QHBoxLayout()
        self.btn_add = QPushButton("Add Book")
        self.btn_update = QPushButton("Update Selected")
        self.btn_delete = QPushButton("Delete Selected")
        hl.addWidget(self.btn_add)
        hl.addWidget(self.btn_update)
        hl.addWidget(self.btn_delete)
        layout.addLayout(hl)

        self.setLayout(layout)
        self.load_books()

        self.tbl.cellClicked.connect(self.on_select)
        self.btn_add.clicked.connect(self.add_book)
        self.btn_update.clicked.connect(self.update_book)
        self.btn_delete.clicked.connect(self.delete_book)
        self.selected_book_id = None

    def load_books(self):
        rows = get_books()
        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            for c, val in enumerate(r):
                self.tbl.setItem(i,c,QTableWidgetItem(str(val)))

    def on_select(self, row, col):
        try:
            self.selected_book_id = int(self.tbl.item(row,0).text())
            self.input_title.setText(self.tbl.item(row,1).text())
            self.input_category.setText(self.tbl.item(row,2).text())
            self.input_isbn.setText(self.tbl.item(row,3).text())
            self.input_copies.setValue(int(self.tbl.item(row,4).text()))
        except Exception:
            pass

    def add_book(self):
        title = self.input_title.text().strip()
        if not title:
            QMessageBox.warning(self,"Error","Title required")
            return
        category = self.input_category.text().strip()
        isbn = self.input_isbn.text().strip()
        copies = self.input_copies.value()
        conn, cur = get_conn_cursor()
        try:
            cur.execute("""
                INSERT INTO book (title, category, isbn, copies_available)
                VALUES (%s, %s, %s, %s)
            """, (title, category, isbn, copies))
            conn.commit()
            QMessageBox.information(self,"Success","Book added")
            self.load_books()
            if hasattr(self.parent, 'dashboard'):
                self.parent.dashboard.refresh()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to add book: " + str(e))
        finally:
            cur.close(); conn.close()

    def update_book(self):
        if not self.selected_book_id:
            QMessageBox.warning(self,"Error","Select a book first")
            return
        title = self.input_title.text().strip()
        category = self.input_category.text().strip()
        isbn = self.input_isbn.text().strip()
        copies = self.input_copies.value()
        conn, cur = get_conn_cursor()
        try:
            cur.execute("""
                UPDATE book SET title=%s, category=%s, isbn=%s, copies_available=%s
                WHERE book_id=%s
            """, (title, category, isbn, copies, self.selected_book_id))
            conn.commit()
            QMessageBox.information(self,"Success","Book updated")
            self.load_books()
            if hasattr(self.parent, 'dashboard'):
                self.parent.dashboard.refresh()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to update book: " + str(e))
        finally:
            cur.close(); conn.close()

    def delete_book(self):
        if not self.selected_book_id:
            QMessageBox.warning(self,"Error","Select a book first")
            return
        conn, cur = get_conn_cursor()
        try:
            cur.execute("DELETE FROM book WHERE book_id=%s", (self.selected_book_id,))
            conn.commit()
            QMessageBox.information(self,"Success","Book deleted")
            self.load_books()
            if hasattr(self.parent, 'dashboard'):
                self.parent.dashboard.refresh()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to delete book: " + str(e))
        finally:
            cur.close(); conn.close()

class AuthorsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        title = QLabel("Manage Authors")
        title.setStyleSheet("font-size:18px;font-weight:bold;")
        layout.addWidget(title)

        self.tbl = QTableWidget(0,2)
        self.tbl.setHorizontalHeaderLabels(["ID","Full Name"])
        layout.addWidget(self.tbl)

        self.input_name = QLineEdit()
        layout.addWidget(QLabel("Author Name:"))
        layout.addWidget(self.input_name)

        hl = QHBoxLayout()
        self.btn_add = QPushButton("Add Author")
        self.btn_update = QPushButton("Update Selected")
        self.btn_delete = QPushButton("Delete Selected")
        hl.addWidget(self.btn_add)
        hl.addWidget(self.btn_update)
        hl.addWidget(self.btn_delete)
        layout.addLayout(hl)

        self.setLayout(layout)
        self.load_authors()

        self.tbl.cellClicked.connect(self.on_select)
        self.btn_add.clicked.connect(self.add_author)
        self.btn_update.clicked.connect(self.update_author)
        self.btn_delete.clicked.connect(self.delete_author)
        self.selected_author_id = None

    def load_authors(self):
        rows = get_authors()
        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            for c, val in enumerate(r):
                self.tbl.setItem(i,c,QTableWidgetItem(str(val)))

    def on_select(self, row, col):
        try:
            self.selected_author_id = int(self.tbl.item(row,0).text())
            self.input_name.setText(self.tbl.item(row,1).text())
        except Exception:
            pass

    def add_author(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self,"Error","Name required")
            return
        conn, cur = get_conn_cursor()
        try:
            cur.execute("INSERT INTO author (full_name) VALUES (%s)", (name,))
            conn.commit()
            QMessageBox.information(self,"Success","Author added")
            self.load_authors()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to add author: " + str(e))
        finally:
            cur.close(); conn.close()

    def update_author(self):
        if not self.selected_author_id:
            QMessageBox.warning(self,"Error","Select an author first")
            return
        name = self.input_name.text().strip()
        conn, cur = get_conn_cursor()
        try:
            cur.execute("UPDATE author SET full_name=%s WHERE author_id=%s", (name, self.selected_author_id))
            conn.commit()
            QMessageBox.information(self,"Success","Author updated")
            self.load_authors()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to update author: " + str(e))
        finally:
            cur.close(); conn.close()

    def delete_author(self):
        if not self.selected_author_id:
            QMessageBox.warning(self,"Error","Select an author first")
            return
        conn, cur = get_conn_cursor()
        try:
            cur.execute("DELETE FROM author WHERE author_id=%s", (self.selected_author_id,))
            conn.commit()
            QMessageBox.information(self,"Success","Author deleted")
            self.load_authors()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to delete author: " + str(e))
        finally:
            cur.close(); conn.close()

class BookClubsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        title = QLabel("Manage Book Clubs")
        title.setStyleSheet("font-size:18px;font-weight:bold;")
        layout.addWidget(title)

        self.tbl = QTableWidget(0,3)
        self.tbl.setHorizontalHeaderLabels(["Club ID","Name","Moderator ID"])
        layout.addWidget(self.tbl)

        form = QFormLayout()
        self.input_name = QLineEdit()
        self.input_mod = QSpinBox()
        self.input_mod.setMinimum(1)
        form.addRow("Club Name:",self.input_name)
        form.addRow("Moderator User ID:",self.input_mod)
        layout.addLayout(form)

        hl = QHBoxLayout()
        self.btn_add = QPushButton("Add Club")
        self.btn_del = QPushButton("Delete Selected")
        hl.addWidget(self.btn_add)
        hl.addWidget(self.btn_del)
        layout.addLayout(hl)

        self.tbl_members = QTableWidget(0,2)
        self.tbl_members.setHorizontalHeaderLabels(["Member ID","Full Name"])
        layout.addWidget(QLabel("Club Members"))
        layout.addWidget(self.tbl_members)

        hl2 = QHBoxLayout()
        self.input_member = QSpinBox()
        self.input_member.setMinimum(1)
        self.btn_add_member = QPushButton("Add Member")
        self.btn_remove_member = QPushButton("Remove Member")
        hl2.addWidget(QLabel("Member ID:"))
        hl2.addWidget(self.input_member)
        hl2.addWidget(self.btn_add_member)
        hl2.addWidget(self.btn_remove_member)
        layout.addLayout(hl2)

        self.setLayout(layout)
        self.load_clubs()

        self.tbl.cellClicked.connect(self.load_members)
        self.btn_add.clicked.connect(self.add_club)
        self.btn_del.clicked.connect(self.delete_club)
        self.btn_add_member.clicked.connect(self.add_member)
        self.btn_remove_member.clicked.connect(self.remove_member)

        self.selected_club_id = None

    def load_clubs(self):
        rows = get_bookclubs()
        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            for c,val in enumerate(r):
                self.tbl.setItem(i,c,QTableWidgetItem(str(val)))
        self.tbl_members.setRowCount(0)

    def load_members(self, row, col):
        try:
            club_id = int(self.tbl.item(row,0).text())
            self.selected_club_id = club_id
            members = get_bookclub_members(club_id)
            self.tbl_members.setRowCount(0)
            for r in members:
                i = self.tbl_members.rowCount()
                self.tbl_members.insertRow(i)
                for c,val in enumerate(r):
                    self.tbl_members.setItem(i,c,QTableWidgetItem(str(val)))
        except Exception:
            pass

    def add_club(self):
        name = self.input_name.text().strip()
        mod = self.input_mod.value()
        if not name:
            QMessageBox.warning(self,"Error","Name required")
            return
        conn, cur = get_conn_cursor()
        try:
            cur.execute("INSERT INTO bookclub(club_name, moderator_id) VALUES(%s,%s)",(name,mod))
            conn.commit()
            QMessageBox.information(self,"Success","Club added")
            self.load_clubs()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to add club: "+str(e))
        finally:
            cur.close(); conn.close()

    def delete_club(self):
        sel = self.tbl.currentRow()
        if sel<0:
            QMessageBox.warning(self,"Error","Select a club")
            return
        club_id = int(self.tbl.item(sel,0).text())
        conn, cur = get_conn_cursor()
        try:
            cur.execute("DELETE FROM bookclub WHERE club_id=%s",(club_id,))
            conn.commit()
            QMessageBox.information(self,"Success","Club deleted")
            self.load_clubs()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to delete club: "+str(e))
        finally:
            cur.close(); conn.close()

    def add_member(self):
        if not self.selected_club_id:
            QMessageBox.warning(self,"Error","Select a club first")
            return
        member_id = self.input_member.value()
        conn, cur = get_conn_cursor()
        try:
            cur.execute("INSERT INTO bookclubmembers(club_id, member_id) VALUES(%s,%s)",(self.selected_club_id,member_id))
            conn.commit()
            QMessageBox.information(self,"Success","Member added")
            self.load_members(self.tbl.currentRow(),0)
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to add member: "+str(e))
        finally:
            cur.close(); conn.close()

    def remove_member(self):
        if not self.selected_club_id:
            QMessageBox.warning(self,"Error","Select a club first")
            return
        sel = self.tbl_members.currentRow()
        if sel<0:
            QMessageBox.warning(self,"Error","Select a member")
            return
        member_id = int(self.tbl_members.item(sel,0).text())
        conn, cur = get_conn_cursor()
        try:
            cur.execute("DELETE FROM bookclubmembers WHERE club_id=%s AND member_id=%s",(self.selected_club_id,member_id))
            conn.commit()
            QMessageBox.information(self,"Success","Member removed")
            self.load_members(self.tbl.currentRow(),0)
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self,"Error","Failed to remove member: "+str(e))
        finally:
            cur.close(); conn.close()

# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartLibrary")
        self.resize(1200,700)
        self.current_user = None
        self.backend_user = None

        central = QWidget()
        layout = QHBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.sidebar = Sidebar(self)
        self.sidebar.setFixedWidth(200)
        layout.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        layout.addWidget(self.pages)

        # Pages
        self.login_page = LoginPage(self)
        self.dashboard = DashboardPage(self)
        self.catalog = CatalogPage(self)
        self.loans = LoansPage(self)
        self.books_page = BooksPage(self)
        self.authors_page = AuthorsPage(self)
        self.bookclubs_page = BookClubsPage(self)

        self.pages.addWidget(self.login_page)
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.catalog)
        self.pages.addWidget(self.loans)
        self.pages.addWidget(self.books_page)
        self.pages.addWidget(self.authors_page)
        self.pages.addWidget(self.bookclubs_page)

        self.pages.setCurrentWidget(self.login_page)
        self.sidebar.hide()

    def switch_to_main(self):
        self.sidebar.lbl_user.setText(f"{self.current_user['name']} ({self.current_user['role']})")
        self.sidebar.show()
        self.pages.setCurrentWidget(self.dashboard)
        self.dashboard.refresh()

    def show_page(self,name):
        mapping = {
            "dashboard": self.dashboard,
            "catalog": self.catalog,
            "loans": self.loans,
            "books": self.books_page,
            "authors": self.authors_page,
            "clubs": self.bookclubs_page
        }
        page = mapping.get(name, self.dashboard)
        self.pages.setCurrentWidget(page)
        if name=="dashboard":
            self.dashboard.refresh()
        if name=="catalog":
            self.catalog.load_all()
        if name=="loans":
            self.loans.load_loans()
        if name=="books":
            self.books_page.load_books()
        if name=="authors":
            self.authors_page.load_authors()
        if name=="clubs":
            self.bookclubs_page.load_clubs()

    def logout(self):
        self.current_user=None
        self.backend_user=None
        self.sidebar.hide()
        self.pages.setCurrentWidget(self.login_page)

    def setup_for_member(self):
        self.sidebar.show()
        # Hide librarian buttons
        self.sidebar.btn_books.hide()
        self.sidebar.btn_authors.hide()
        self.sidebar.btn_clubs.hide()

    def setup_for_librarian(self):
        self.sidebar.show()
        # Show all buttons
        self.sidebar.btn_books.show()
        self.sidebar.btn_authors.show()
        self.sidebar.btn_clubs.show()

# ---------------- Run App ----------------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__=="__main__":
    main()