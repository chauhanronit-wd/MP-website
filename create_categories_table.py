import sqlite3

conn = sqlite3.connect(
    "industrial.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS
    categories
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        category_name TEXT
    )
    """
)

conn.commit()
conn.close()

print("Categories Table Created")