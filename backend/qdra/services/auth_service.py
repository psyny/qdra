import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.security.password_hasher import verify_password
from infrastructure.security.jwt_handler import create_access_token
from schemas.user_schemas import UserRead, UserAppPermissionsRead
from services.user_service import UserService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)

    def authenticate_user(self, login_name: str, password: str) -> Optional[UserRead]:
        """Authenticate a user with login name and password."""
        print(f"Authenticating user: {login_name}")
        user = self.user_service.get_user_by_login_name(login_name)
        if not user:
            # Only auto-create if this is the first user in the system
            user_count = self.user_service.user_repo.count_all()
            if user_count == 0:
                print(f"No users in DB, creating first user: {login_name}")
                from schemas.user_schemas import UserCreate
                user_data = UserCreate(
                    login_name=login_name,
                    password=password,
                    display_name=login_name
                )
                self.user_service.create_user(user_data)
                # Fetch the actual User model with password_hash
                user = self.user_service.get_user_by_login_name(login_name)
                print(f"Created first user: {login_name}")
            else:
                return None
        if not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login timestamp
        self.user_service.set_last_login_at(user.id, datetime.utcnow())
        
        return UserRead.model_validate(user)

    def login(self, login_name: str, password: str) -> Optional[tuple[str, UserRead]]:
        """Login a user and return JWT token and user info."""
        user = self.authenticate_user(login_name, password)
        if not user:
            return None
        
        token = create_access_token(user.id)
        return token, user

    def get_current_user(self, user_id: uuid.UUID) -> Optional[tuple[UserRead, UserAppPermissionsRead]]:
        """Get current user with their app permissions."""
        user = self.user_service.get_user(user_id)
        if not user:
            return None
        if not user.is_active:
            return None
        
        app_permissions = self.user_service.get_app_permissions(user_id)
        return user, app_permissions
