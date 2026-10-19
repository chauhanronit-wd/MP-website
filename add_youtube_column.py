import sqlite3

conn = sqlite3.connect("industrial.db")

cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE products
        ADD COLUMN youtube_url TEXT
    """)
    print("youtube_url column added successfully.")

except sqlite3.OperationalError:
    print("youtube_url column already exists.")

conn.commit()
conn.close()