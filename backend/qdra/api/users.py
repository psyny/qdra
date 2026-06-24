import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.user_schemas import (
    UserCreate, UserUpdate, UserRead, 
    UserAppPermissionsUpdate, UserAppPermissionsRead,
    ProjectUserPermissionsUpdate, ProjectUserPermissionsRead
)
from services.user_service import UserService


router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreateRequest(BaseModel):
    login_name: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserUpdateRequest(BaseModel):
    display_name: str = Field(None, min_length=1)
    is_active: bool = None


class PasswordResetRequest(BaseModel):
    current_password: str = Field(None, min_length=1)
    new_password: str = Field(..., min_length=1)


@router.get("", response_model=List[UserRead])
def list_users(include_inactive: bool = False, db: Session = Depends(get_db)):
    """List all users."""
    user_service = UserService(db)
    return user_service.list_users(include_inactive=include_inactive)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a user by ID."""
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    """Create a new user."""
    user_service = UserService(db)
    user_data = UserCreate(
        login_name=request.login_name,
        password=request.password,
        display_name=request.display_name
    )
    return user_service.create_user(user_data)


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: uuid.UUID, request: UserUpdateRequest, db: Session = Depends(get_db)):
    """Update a user."""
    user_service = UserService(db)
    update_data = UserUpdate(
        display_name=request.display_name,
        is_active=request.is_active
    )
    user = user_service.update_user(user_id, update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/{user_id}/reset-password", response_model=UserRead)
def reset_password(user_id: uuid.UUID, request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Reset a user's password (requires current password verification)."""
    from infrastructure.security.password_hasher import verify_password
    from repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password if provided (for self password reset)
    if request.current_password and not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    user_service = UserService(db)
    update_data = UserUpdate(password=request.new_password)
    user = user_service.update_user(user_id, update_data)
    return user


@router.get("/{user_id}/permissions", response_model=UserAppPermissionsRead)
def get_user_permissions(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a user's app-level permissions."""
    user_service = UserService(db)
    return user_service.get_app_permissions(user_id)


@router.put("/{user_id}/permissions", response_model=UserAppPermissionsRead)
def update_user_permissions(
    user_id: uuid.UUID, 
    request: UserAppPermissionsUpdate, 
    db: Session = Depends(get_db)
):
    """Update a user's app-level permissions."""
    user_service = UserService(db)
    return user_service.update_app_permissions(user_id, request)


@router.get("/{user_id}/projects", response_model=List[ProjectUserPermissionsRead])
def list_user_projects(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """List all projects a user has permissions for."""
    user_service = UserService(db)
    return user_service.list_user_projects(user_id)


@router.get("/{user_id}/projects/{project_id}/permissions", response_model=ProjectUserPermissionsRead)
def get_user_project_permissions(user_id: uuid.UUID, project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a user's permissions for a specific project."""
    user_service = UserService(db)
    permissions = user_service.get_project_permissions(user_id, project_id)
    if not permissions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project permissions not found"
        )
    return permissions


@router.put("/{user_id}/projects/{project_id}/permissions", response_model=ProjectUserPermissionsRead)
def update_user_project_permissions(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    request: ProjectUserPermissionsUpdate,
    db: Session = Depends(get_db)
):
    """Update a user's permissions for a specific project."""
    user_service = UserService(db)
    return user_service.upsert_project_permissions(user_id, project_id, request)
