import sqlite3

conn = sqlite3.connect(
    "industrial.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    UPDATE admin
    SET password=?
    WHERE username=?
    """,
    (
    "scrypt:32768:8:1$mBgxuNRGBD9A4Brv$80587a55e461345a3ffde6d4d552735c8133aef84f8df930b49c11adca82338df7efa53cf6a75ad8cc88f1121ddf5ba32d7f59b6a83d3139a7aeba2c1b39f9c2",
        "Ronit"
    )
)

conn.commit()

conn.close()

print(
    "Password Updated Successfully"
)