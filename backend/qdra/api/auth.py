import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.user_schemas import UserRead, UserAppPermissionsRead
from services.auth_service import AuthService
from infrastructure.security.jwt_handler import verify_token


router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    login: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: UserRead


class CurrentUserResponse(BaseModel):
    id: uuid.UUID
    login: str
    display_name: str
    app_permissions: UserAppPermissionsRead


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> uuid.UUID:
    """Extract user_id from JWT token."""
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user_id


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint - returns JWT token and user info."""
    auth_service = AuthService(db)
    result = auth_service.login(request.login, request.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token, user = result
    return LoginResponse(token=token, user=user)


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user with their app permissions."""
    auth_service = AuthService(db)
    result = auth_service.get_current_user(user_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user, app_permissions = result
    return CurrentUserResponse(
        id=user.id,
        login=user.login_name,
        display_name=user.display_name,
        app_permissions=app_permissions
    )
