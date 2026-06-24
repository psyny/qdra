import bcrypt


def hash_password(raw_password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(raw_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(raw_password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(raw_password.encode('utf-8'), password_hash.encode('utf-8'))
