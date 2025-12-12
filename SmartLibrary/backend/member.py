import psycopg2
from datetime import datetime, timedelta

class Member:
    def __init__(self, db_config, member_id, full_name):
        self.db_config = db_config
        self.member_id = member_id
        self.full_name = full_name

    def connect(self):
        return psycopg2.connect(**self.db_config)

    def borrow_book(self, book_id):
        try:
            conn = self.connect()
            cur = conn.cursor()

            # Check active loans
            cur.execute("SELECT COUNT(*) FROM loan WHERE member_id=%s AND returned=FALSE;", (self.member_id,))
            active_loans = cur.fetchone()[0]
            if active_loans >= 3:
                print("Cannot borrow more than 3 books at a time.")
                cur.close()
                conn.close()
                return

            # Check stock
            cur.execute("SELECT copies_available FROM book WHERE book_id=%s;", (book_id,))
            stock = cur.fetchone()
            if stock is None or stock[0] <= 0:
                print("Book not available.")
                cur.close()
                conn.close()
                return

            # Borrow book
            borrow_date = datetime.now()
            due_date = borrow_date + timedelta(days=7)
            cur.execute("""
                INSERT INTO loan (book_id, member_id, borrow_date, due_date, returned)
                VALUES (%s, %s, %s, %s, FALSE);
            """, (book_id, self.member_id, borrow_date, due_date))

            # Update book stock
            cur.execute("UPDATE book SET copies_available = copies_available - 1 WHERE book_id=%s;", (book_id,))
            conn.commit()
            cur.close()
            conn.close()
            print("Book borrowed successfully! Due date:", due_date.strftime("%Y-%m-%d"))

        except Exception as e:
            print("Error borrowing book:", e)

    def return_book(self, loan_id):
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("SELECT book_id FROM loan WHERE loan_id=%s AND returned=FALSE;", (loan_id,))
            loan = cur.fetchone()
            if loan is None:
                print("Loan not found or already returned.")
                cur.close()
                conn.close()
                return

            book_id = loan[0]

            cur.execute("UPDATE loan SET returned=TRUE WHERE loan_id=%s;", (loan_id,))
            cur.execute("UPDATE book SET copies_available = copies_available + 1 WHERE book_id=%s;", (book_id,))
            conn.commit()
            cur.close()
            conn.close()
            print("Book returned successfully!")

        except Exception as e:
            print("Error returning book:", e)

    def view_active_loans(self):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("""
                SELECT l.loan_id, b.title, l.borrow_date, l.due_date
                FROM loan l
                JOIN book b ON l.book_id = b.book_id
                WHERE l.member_id=%s AND l.returned=FALSE;
            """, (self.member_id,))
            loans = cur.fetchall()
            cur.close()
            conn.close()

            print("\n--- Active Loans ---")
            for l in loans:
                print(f"Loan ID: {l[0]}, Book: {l[1]}, Borrowed: {l[2]}, Due: {l[3]}")

        except Exception as e:
            print("Error fetching active loans:", e)