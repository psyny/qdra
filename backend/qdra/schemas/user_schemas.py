import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    login_name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)


class UserUpdate(BaseModel):
    login_name: Optional[str] = Field(None, min_length=1)
    display_name: Optional[str] = Field(None, min_length=1)
    password: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    login_name: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class UserAppPermissionsUpdate(BaseModel):
    can_manage_users: Optional[bool] = None
    can_create_projects: Optional[bool] = None
    can_edit_projects: Optional[bool] = None
    can_delete_projects: Optional[bool] = None
    can_create_templates: Optional[bool] = None
    can_edit_templates: Optional[bool] = None
    can_delete_templates: Optional[bool] = None


class UserAppPermissionsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: uuid.UUID
    can_manage_users: bool
    can_create_projects: bool
    can_edit_projects: bool
    can_delete_projects: bool
    can_create_templates: bool
    can_edit_templates: bool
    can_delete_templates: bool
    created_at: datetime
    updated_at: datetime


class ProjectUserPermissionsUpdate(BaseModel):
    can_access: Optional[bool] = None
    can_manage_project_users: Optional[bool] = None
    can_create_material: Optional[bool] = None
    can_edit_material: Optional[bool] = None
    can_delete_material: Optional[bool] = None
    can_create_recipe: Optional[bool] = None
    can_edit_recipe: Optional[bool] = None
    can_delete_recipe: Optional[bool] = None
    can_run_plan: Optional[bool] = None


class ProjectUserPermissionsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    can_access: bool
    can_manage_project_users: bool
    can_create_material: bool
    can_edit_material: bool
    can_delete_material: bool
    can_create_recipe: bool
    can_edit_recipe: bool
    can_delete_recipe: bool
    can_run_plan: bool
    created_at: datetime
    updated_at: datetime
