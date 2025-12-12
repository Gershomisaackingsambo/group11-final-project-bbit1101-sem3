import psycopg2

class Librarian:
    def __init__(self, db_config, librarian_id, librarian_name):
        self.db_config = db_config
        self.librarian_id = librarian_id
        self.librarian_name = librarian_name

    def connect(self):
        return psycopg2.connect(**self.db_config)

    # AUTHOR
    def add_author(self, full_name):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO author (full_name) VALUES (%s) RETURNING author_id;", (full_name,))
            author_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            print(f"Author '{full_name}' added with ID = {author_id}")
        except Exception as e:
            print("Error adding author:", e)

    # BOOK
    def add_book(self, title, category, isbn, copies_available, author_id):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO book (title, category, isbn, copies_available, author_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING book_id;
            """, (title, category, isbn, copies_available, author_id))
            book_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            print(f"Book '{title}' added with ID = {book_id}")
        except Exception as e:
            print("Error adding book:", e)

    def update_book_stock(self, book_id, new_stock):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("UPDATE book SET copies_available=%s WHERE book_id=%s;", (new_stock, book_id))
            conn.commit()
            cur.close()
            conn.close()
            print("Book stock updated successfully!")
        except Exception as e:
            print("Error updating book stock:", e)

    def delete_book(self, book_id):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("DELETE FROM book WHERE book_id=%s;", (book_id,))
            conn.commit()
            cur.close()
            conn.close()
            print("Book deleted successfully.")
        except Exception as e:
            print("Error deleting book:", e)

    # MEMBERS
    def view_all_members(self):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute('SELECT user_id, full_name, username, email FROM "user" WHERE role_id=2;')
            rows = cur.fetchall()
            cur.close()
            conn.close()

            print("\n--- Members ---")
            for row in rows:
                print(f"ID: {row[0]}, Name: {row[1]}, Username: {row[2]}, Email: {row[3]}")
        except Exception as e:
            print("Error loading members:", e)

    # BOOK CLUB
    def create_book_club(self, club_name, moderator_id):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO bookclub (club_name, moderator_id) VALUES (%s, %s) RETURNING club_id;", (club_name, moderator_id))
            club_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            print(f"Book Club '{club_name}' created with ID = {club_id}")
        except Exception as e:
            print("Error creating book club:", e)

    def add_member_to_club(self, club_id, member_id):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO bookclubmembers (club_id, member_id) VALUES (%s, %s);", (club_id, member_id))
            conn.commit()
            cur.close()
            conn.close()
            print(f"Member {member_id} added to club {club_id}")
        except Exception as e:
            print("Error adding member to club:", e)

    def view_club_members(self, club_id):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("""
                SELECT u.user_id, u.full_name
                FROM bookclubmembers bcm
                JOIN "user" u ON bcm.member_id = u.user_id
                WHERE bcm.club_id = %s;
            """, (club_id,))
            members = cur.fetchall()
            cur.close()
            conn.close()

            print(f"\n--- Members in Club {club_id} ---")
            for m in members:
                print(f"ID: {m[0]}, Name: {m[1]}")
        except Exception as e:
            print("Error viewing club members:", e)