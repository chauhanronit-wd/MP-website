import sqlite3

conn = sqlite3.connect("industrial.db")

cursor = conn.cursor()

cursor.execute("""
SELECT id,title
FROM featured_products
""")

for row in cursor.fetchall():
    print(row)

conn.close()