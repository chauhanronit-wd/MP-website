import sqlite3
from werkzeug.security import generate_password_hash

# ==========================================
# DATABASE CONNECTION
# ==========================================

conn = sqlite3.connect("industrial.db")
cursor = conn.cursor()

# Enable Foreign Key
cursor.execute("PRAGMA foreign_keys = ON")

# ==========================================
# DEPARTMENTS TABLE
# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT UNIQUE NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ==========================================
# ROLES TABLE
# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE NOT NULL,
    description TEXT
)
""")

# ==========================================
# USERS TABLE
# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    full_name TEXT NOT NULL,

    username TEXT UNIQUE NOT NULL,

    email TEXT UNIQUE NOT NULL,

    mobile TEXT,

    password TEXT NOT NULL,

    department_id INTEGER,

    role_id INTEGER,

    profile_image TEXT DEFAULT 'default.png',

    is_verified INTEGER DEFAULT 0,

    account_status TEXT DEFAULT 'Pending',

    last_login DATETIME,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(department_id)
    REFERENCES departments(id),

    FOREIGN KEY(role_id)
    REFERENCES roles(id)

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS otp_verification (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    email TEXT NOT NULL,

    otp TEXT NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP

)
""")


# ==========================================
# DEFAULT DEPARTMENTS
# ==========================================

departments = [

    ("Administration", "System Administrator"),

    ("Sales", "Sales Department"),

    ("Purchase", "Purchase Department"),

    ("Machine Inquiry", "Machine Inquiry Department"),

    ("Installation", "Installation Department"),

    ("Service", "Service Department"),

    ("Accounts", "Accounts Department"),

    ("HR", "Human Resource Department")

]

cursor.executemany("""

INSERT OR IGNORE INTO departments
(department_name, description)

VALUES (?,?)

""", departments)

# ==========================================
# DEFAULT ROLES
# ==========================================

roles = [

    ("Admin", "Full System Access"),

    ("Manager", "Department Manager"),

    ("Employee", "Department Employee")

]

cursor.executemany("""

INSERT OR IGNORE INTO roles
(role_name, description)

VALUES (?,?)

""", roles)

# ==========================================
# CREATE DEFAULT ADMIN
# ==========================================

admin_password = generate_password_hash("123456")

cursor.execute("""

SELECT id FROM departments
WHERE department_name='Administration'

""")

department_id = cursor.fetchone()[0]

cursor.execute("""

SELECT id FROM roles
WHERE role_name='Admin'

""")

role_id = cursor.fetchone()[0]

cursor.execute("""

INSERT OR IGNORE INTO users
(

full_name,
username,
email,
mobile,
password,
department_id,
role_id,
is_verified,
account_status

)

VALUES
(

?,
?,
?,
?,
?,
?,
?,
?,
?

)

""",

(

"System Administrator",

"admin",

"ronitchauhan2507@gmail.com",

"9999999999",

admin_password,

department_id,

role_id,

1,

"Active"

)

)

# ==========================================
# SAVE DATABASE
# ==========================================

conn.commit()

conn.close()

print("=" * 45)
print("Industrial CRM Database Created Successfully")
print("=" * 45)
print("Default Username : Admin")
print("Default Password : 123456")
print("=" * 45)