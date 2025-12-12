-- =====================
-- 2. Create Role table
-- =====================
CREATE TABLE Role (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

-- Insert default roles
INSERT INTO Role (role_name) VALUES ('Librarian'), ('Member');

-- =====================
-- 3. Create User table
-- =====================
CREATE TABLE "User" (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role_id INT NOT NULL REFERENCES Role(role_id),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

-- =====================
-- 4. Create Book table
-- =====================
CREATE TABLE Book (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    isbn VARCHAR(20) UNIQUE,
    copies_available INT NOT NULL
);

-- =====================
-- 5. Create Author table
-- =====================
CREATE TABLE Author (
    author_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL
);

-- =====================
-- 6. Create BookAuthors table (many-to-many)
-- =====================
CREATE TABLE BookAuthors (
    book_id INT REFERENCES Book(book_id) ON DELETE CASCADE,
    author_id INT REFERENCES Author(author_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- =====================
-- 7. Create Member table
-- =====================
CREATE TABLE Member (
    member_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES "User"(user_id) ON DELETE CASCADE,
    membership_date DATE DEFAULT CURRENT_DATE,
    active BOOLEAN DEFAULT TRUE
);

-- =====================
-- 8. Create Loan table
-- =====================
CREATE TABLE Loan (
    loan_id SERIAL PRIMARY KEY,
    book_id INT REFERENCES Book(book_id),
    member_id INT REFERENCES Member(member_id),
    borrow_date DATE DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    returned BOOLEAN DEFAULT FALSE
);

-- =====================
-- 9. Create BookClub table
-- =====================
CREATE TABLE BookClub (
    club_id SERIAL PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL,
    moderator_id INT REFERENCES Member(member_id)
);

-- =====================
-- 10. Create BookClubMembers table (many-to-many)
-- =====================
CREATE TABLE BookClubMembers (
    club_id INT REFERENCES BookClub(club_id) ON DELETE CASCADE,
    member_id INT REFERENCES Member(member_id) ON DELETE CASCADE,
    PRIMARY KEY (club_id, member_id)
);

-- =====================
-- 11. Sample Data
-- =====================

-- Users
INSERT INTO "User" (username, password, role_id, full_name, email)
VALUES
('librarian1', 'password123', 1, 'Alice Librarian', 'alice@library.com'),
('member1', 'password123', 2, 'Gershom Kingsambo', 'gershom@student.com'),
('member2', 'password123', 2, 'Daniel Amara', 'daniel@student.com');

-- Members
INSERT INTO Member (user_id) VALUES (2), (3);

-- Authors
INSERT INTO Author (full_name) VALUES ('J.K. Rowling'), ('George Orwell');

-- Books
INSERT INTO Book (title, category, isbn, copies_available)
VALUES
('Harry Potter and the Sorcerer''s Stone', 'Fantasy', '9780747532699', 5),
('1984', 'Dystopian', '9780451524935', 3);

-- BookAuthors
INSERT INTO BookAuthors (book_id, author_id) VALUES (1, 1), (2, 2);

-- Book Clubs
INSERT INTO BookClub (club_name, moderator_id) VALUES ('Fantasy Lovers', 2);

-- Book Club Members
INSERT INTO BookClubMembers (club_id, member_id) VALUES (1, 1), (1, 2);

-- Loans
INSERT INTO Loan (book_id, member_id, due_date)
VALUES (1, 2, CURRENT_DATE + INTERVAL '7 days');