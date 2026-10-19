import sqlite3
from werkzeug.security import generate_password_hash

# New Password
new_password = "123456"

password_hash = generate_password_hash(new_password)

conn = sqlite3.connect("industrial.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE users
SET password=?
WHERE username=?
""", (password_hash, "admin"))

conn.commit()
conn.close()

print("=" * 40)
print("Admin Password Reset Successfully")
print("Username : admin")
print("Password : 123456")
print("=" * 40)