import sqlite3

conn=sqlite3.connect("industrial.db")

cursor=conn.cursor()

cursor.execute("""

UPDATE price_requests

SET request_type='price'

WHERE request_type IS NULL

""")

conn.commit()

conn.close()

print("Done")