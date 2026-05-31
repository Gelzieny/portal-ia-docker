from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    user_name: str | None = None
    user_email: str | None = None
    action: str
    entity: str
    entity_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)
    details: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
