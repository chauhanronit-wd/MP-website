import sqlite3

conn = sqlite3.connect("industrial.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM gallery")
print("Gallery:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM machine_photos")
print("Machine Photos:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM installation_photos")
print("Installation Photos:", cursor.fetchone()[0])

conn.close()