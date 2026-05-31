from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

UserRole = Literal["admin", "gestor", "curador", "curador_modelos", "gestor_produto", "servidor"]


class FeatureResponse(BaseModel):
    key: str
    name: str
    description: str | None = None
    area: str
    menu_label: str | None = None
    menu_path: str | None = None
    sort_order: int
    is_active: bool = True
    is_system: bool = True


class MyPermissionsResponse(BaseModel):
    role: UserRole
    permissions: list[str]
    features: list[FeatureResponse]


class RoleFeatureGrant(BaseModel):
    key: str
    name: str
    description: str | None = None
    area: str
    menu_label: str | None = None
    menu_path: str | None = None
    sort_order: int
    is_required: bool = False
    grants: dict[UserRole, bool]
    updated_at_by_role: dict[UserRole, datetime | None] = Field(default_factory=dict)


class RolePermissionsMatrixResponse(BaseModel):
    roles: list[UserRole]
    features: list[RoleFeatureGrant]


class RolePermissionsUpdate(BaseModel):
    permissions: list[str]
