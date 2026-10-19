import sqlite3

conn = sqlite3.connect("industrial.db")
cursor = conn.cursor()

columns = [

    ("status", "TEXT DEFAULT 'New'"),

    ("reply_message", "TEXT"),

    ("quotation_file", "TEXT")

]

for name, datatype in columns:

    try:

        cursor.execute(f"""

        ALTER TABLE price_requests

        ADD COLUMN {name} {datatype}

        """)

        print(name, "Added")

    except:

        print(name, "Already Exists")

conn.commit()
conn.close()

print("Done")