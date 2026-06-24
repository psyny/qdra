import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from infrastructure.config.settings import settings


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a JWT access token for a user."""
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[uuid.UUID]:
    """Verify a JWT token and return the user ID if valid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return uuid.UUID(user_id)
    except JWTError:
        return None
