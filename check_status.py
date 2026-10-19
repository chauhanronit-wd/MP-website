import sqlite3

conn = sqlite3.connect("industrial.db")

cursor = conn.cursor()

cursor.execute("""

SELECT id, customer_name, status

FROM price_requests

""")

rows = cursor.fetchall()

for row in rows:

    print(row)

conn.close()