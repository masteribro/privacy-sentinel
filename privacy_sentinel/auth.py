import hashlib
import os


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except (ValueError, AttributeError):
        return False


def get_user(conn, email: str):
    """Returns (id, name, email, password_hash) or None."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (email.strip().lower(),),
    )
    return cur.fetchone()


def email_exists(conn, email: str) -> bool:
    return get_user(conn, email) is not None


def create_user(conn, name: str, email: str, password: str) -> bool:
    """Insert a new user. Returns False if the email is already taken."""
    if email_exists(conn, email):
        return False
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name.strip(), email.strip().lower(), hash_password(password)),
    )
    conn.commit()
    return True


def authenticate(conn, email: str, password: str):
    """Returns the user row (id, name, email, password_hash) on success, else None."""
    user = get_user(conn, email)
    if not user:
        return None
    if verify_password(password, user[3]):
        return user
    return None
