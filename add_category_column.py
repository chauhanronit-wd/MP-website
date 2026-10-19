import sqlite3

conn = sqlite3.connect(
    "industrial.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    ALTER TABLE products

    ADD COLUMN category_id INTEGER
    """
)

conn.commit()
conn.close()

print("Category Column Added")