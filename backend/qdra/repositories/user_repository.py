import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from models.user import User
from infrastructure.security.password_hasher import hash_password, verify_password


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, login_name: str, password: str, display_name: str) -> User:
        """Create a new user with hashed password."""
        password_hash = hash_password(password)
        user = User(
            login_name=login_name,
            password_hash=password_hash,
            display_name=display_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_login_name(self, login_name: str) -> Optional[User]:
        """Get a user by login name (case-insensitive)."""
        return self.db.query(User).filter(User.login_name.ilike(login_name)).first()

    def list_all(self, include_inactive: bool = False) -> List[User]:
        """List all users, optionally including inactive ones."""
        query = self.db.query(User)
        if not include_inactive:
            query = query.filter(User.is_active == True)
        return query.all()

    def update(
        self,
        user_id: uuid.UUID,
        login_name: Optional[str] = None,
        display_name: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        """Update a user's fields."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        if login_name is not None:
            user.login_name = login_name
        if display_name is not None:
            user.display_name = display_name
        if password is not None:
            user.password_hash = hash_password(password)
        if is_active is not None:
            user.is_active = is_active

        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate(self, user_id: uuid.UUID) -> Optional[User]:
        """Deactivate a user (set is_active to False)."""
        return self.update(user_id, is_active=False)

    def set_last_login_at(self, user_id: uuid.UUID, timestamp: datetime) -> None:
        """Set the last login timestamp for a user."""
        user = self.get_by_id(user_id)
        if user:
            user.last_login_at = timestamp
            self.db.commit()

    def count_all(self) -> int:
        """Count total users in the database."""
        return self.db.query(User).count()
