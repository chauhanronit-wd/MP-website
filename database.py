import sqlite3

conn = sqlite3.connect(
    "industrial.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    SELECT id,
           username,
           email
    FROM admin
    """
)

rows = cursor.fetchall()

for row in rows:

    print(row)

conn.close()