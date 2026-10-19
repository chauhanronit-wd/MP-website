import sqlite3

conn = sqlite3.connect("industrial.db")

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS turnkey_projects(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    project_title TEXT,

    client_name TEXT,

    location TEXT,

    project_type TEXT,

    description TEXT,

    image TEXT,

    youtube_url TEXT,

    completed_date TEXT

)

""")

conn.commit()

print("Turnkey Projects Table Created Successfully.")

conn.close()