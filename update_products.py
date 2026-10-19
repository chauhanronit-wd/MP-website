import sqlite3

conn = sqlite3.connect("industrial.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE featured_products
        ADD COLUMN product_id INTEGER
    """)
    print("Done")
except:
    print("Already Exists")

conn.commit()
conn.close()