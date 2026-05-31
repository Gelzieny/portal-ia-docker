from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    type: Literal["info", "warning", "success", "error"] = "info"
    title: str
    message: str
    link: str | None = None
    is_global: bool = True
    expires_at: datetime | None = None
    target_user_ids: list[UUID] = Field(default_factory=list)


class NotificationUpdate(BaseModel):
    title: str | None = None
    message: str | None = None
    link: str | None = None
    expires_at: datetime | None = None


class NotificationResponse(BaseModel):
    id: UUID
    type: Literal["info", "warning", "success", "error"]
    title: str
    message: str
    link: str | None
    is_global: bool
    is_read: bool = False
    created_at: datetime
    expires_at: datetime | None
    target_user_ids: list[UUID] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
