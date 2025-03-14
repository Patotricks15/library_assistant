import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("bookstore.db")
cursor = conn.cursor()

# Create a table for books
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
)
''')

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    book_id INTEGER,
    quantity INTEGER,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(book_id) REFERENCES books(id)
)
""")


# Insert some sample books
books = [
    ("The Pragmatic Programmer", "Andrew Hunt, David Thomas", "A classic guide to software development best practices.", 45.00, 10),
    ("Clean Code", "Robert C. Martin", "A must-read for writing maintainable and efficient code.", 50.00, 8),
    ("Python Crash Course", "Eric Matthes", "An introductory book for learning Python programming.", 35.00, 15),
]

cursor.executemany("INSERT INTO books (title, author, description, price, stock) VALUES (?, ?, ?, ?, ?)", books)
conn.commit()
conn.close()
