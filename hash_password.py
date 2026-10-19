from werkzeug.security import generate_password_hash

password = "123456"

print(
    generate_password_hash(password)
)