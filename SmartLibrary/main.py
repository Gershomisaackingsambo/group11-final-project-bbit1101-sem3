from backend.user import User
from backend.member import Member
from backend.librarian import Librarian

db_config = {
    "host": "localhost",
    "database": "smartlibrary",
    "user": "postgres",
    "password": "Pes@2022"
}

print("===== SMART LIBRARY LOGIN =====")
username = input("Username: ")
password = input("Password: ")

user = User(db_config)
user_data = user.login(username, password)

if user_data is None:
    print("Login failed! Invalid username or password.")
    exit()

user_id, full_name, role_id = user_data
print(f"\nLogin successful! Welcome {full_name}. Role ID = {role_id}")

# LIBRARIAN MENU
if role_id == 1:
    librarian = Librarian(db_config, user_id, full_name)
    while True:
        print("\n===== LIBRARIAN MENU =====")
        print("1. Add Author\n2. Add Book\n3. Update Book Stock\n4. Delete Book\n5. View All Members")
        print("6. Create Book Club\n7. Add Member to Club\n8. View Members in Club\n9. Logout")
        choice = input("Enter choice: ")

        if choice == "1":
            name = input("Author Name: ")
            librarian.add_author(name)
        elif choice == "2":
            title = input("Title: ")
            category = input("Category: ")
            isbn = input("ISBN: ")
            stock = int(input("Copies Available: "))
            author_id = int(input("Author ID: "))
            librarian.add_book(title, category, isbn, stock, author_id)
        elif choice == "3":
            book_id = int(input("Book ID: "))
            new_stock = int(input("New Stock: "))
            librarian.update_book_stock(book_id, new_stock)
        elif choice == "4":
            book_id = int(input("Book ID to delete: "))
            librarian.delete_book(book_id)
        elif choice == "5":
            librarian.view_all_members()
        elif choice == "6":
            club_name = input("Club Name: ")
            moderator = int(input("Moderator ID: "))
            librarian.create_book_club(club_name, moderator)
        elif choice == "7":
            club = int(input("Club ID: "))
            member_id = int(input("Member ID: "))
            librarian.add_member_to_club(club, member_id)
        elif choice == "8":
            club = int(input("Club ID: "))
            librarian.view_club_members(club)
        elif choice == "9":
            print("Logged out.")
            break
        else:
            print("Invalid choice.")

# MEMBER MENU
elif role_id == 2:
    member = Member(db_config, user_id, full_name)
    while True:
        print("\n===== MEMBER MENU =====")
        print("1. Borrow Book\n2. Return Book\n3. View Active Loans\n4. Logout")
        choice = input("Enter choice: ")

        if choice == "1":
            book_id = int(input("Book ID: "))
            member.borrow_book(book_id)
        elif choice == "2":
            loan_id = int(input("Loan ID: "))
            member.return_book(loan_id)
        elif choice == "3":
            member.view_active_loans()
        elif choice == "4":
            print("Logged out.")
            break
        else:
            print("Invalid choice.")