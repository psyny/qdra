import uuid
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    token: str
    user: dict


class CurrentUserResponse(BaseModel):
    id: uuid.UUID
    login: str
    display_name: str
    app_permissions: dict
