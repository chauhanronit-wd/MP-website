import sqlite3

conn = sqlite3.connect(
    "industrial.db"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inquiries(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT,

    email TEXT,

    phone TEXT,

    product TEXT,

    message TEXT

)
""")

conn.commit()

conn.close()

print("Inquiry Table Created")