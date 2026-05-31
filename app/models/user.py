from typing import Literal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


UserRole = Literal["admin", "gestor", "curador", "curador_modelos", "gestor_produto", "servidor"]


class UserBase(BaseModel):
    name: str = Field(max_length=120)
    email: str | None = Field(default=None, max_length=320)
    organ: str = Field(max_length=200)
    role: UserRole = "servidor"


class UserCreate(UserBase):
    codg_usuario: str = Field(max_length=120)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    organ: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=500)


class UserUpdateAdmin(UserUpdate):
    email: str | None = Field(default=None, max_length=320)
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: UUID
    codg_usuario: str | None = None
    avatar_url: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
