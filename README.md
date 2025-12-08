


# SmartLibrary Management System

**Group 11**  
**Members:**  
- Gershom Isaac Kingsambo  
- Daniel Amara  
- Ramatu Bah  

---

## Description
SmartLibrary is a desktop-based library management system designed for Limkokwing University’s central library. It provides an intuitive GUI for managing books, authors, members, book clubs, and loans. The system supports role-based access for Librarians and Members, allowing secure and efficient library operations.

---

## Features

### Member Features:
- Login with username and password
- View and search book catalog
- Borrow and return books
- View active loans
- Join book clubs

### Librarian Features:
- Manage members (add, update, delete)
- Manage books (add, update, delete)
- Manage authors
- Manage book clubs and their members
- Dashboard with summary statistics
- View most borrowed books and active loans

---

## Technologies Used
- **Backend:** Python 3.x (OOP)  
- **Database:** PostgreSQL  
- **GUI:** PyQt5  
- **Database Connectivity:** psycopg2  

---

## Installation Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository_url>
   cd SmartLibrary

	2.	Set Up Python Environment

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows


	3.	Install Dependencies

pip install -r requirements.txt


	4.	Set Up PostgreSQL Database
	•	Create a database named smartlibrary
	•	Execute the provided database.sql script to create tables and insert sample data
	•	Update db_config in backend/user.py and gui_app.py with your PostgreSQL credentials
	5.	Run the Application

python gui_app.py



⸻

Usage
	•	Login: Use existing users:
	•	Librarian: librarian1 / password123
	•	Member: member1 / password123
	•	Navigate through the sidebar to access features
	•	Members can borrow/return books and view loans
	•	Librarians can manage books, members, authors, and book clubs



Database Setup
	•	Tables include:
	•	user (user_id, username, password, full_name, email, role_id)
	•	book (book_id, title, category, isbn, copies_available)
	•	author (author_id, full_name)
	•	loan (loan_id, book_id, member_id, borrow_date, due_date, returned)
	•	bookclub (club_id, club_name, moderator_id)
	•	bookclubmembers (club_id, member_id)
	•	Use database.sql to create and populate tables



Project Structure

SmartLibrary/
│
├─ backend/
│   ├─ user.py
│   ├─ member.py
│   ├─ librarian.py
│   ├─ role.py
│
├─ gui_app.py
├─ requirements.txt
├─ README.md




Contributors
	•	Gershom Isaac Kingsambo
	•	Daniel Amara
	•	Ramatu Bah


Notes
	•	Ensure PostgreSQL is running and accessible before launching the app
	•	Only members can borrow/return books; librarians have full management permissions
	•	Maximum 3 active loans per member; loan due date = 7 days


