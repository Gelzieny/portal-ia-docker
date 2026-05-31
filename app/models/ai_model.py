from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIModelBase(BaseModel):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=100)
    provider: str = Field(max_length=100)
    category: Literal["texto", "codigo", "visao", "multimodal", "embeddings"]
    description: str = Field(default="", max_length=2000)
    capabilities: list[str] = Field(default=[], max_length=30)
    status: Literal["disponivel", "beta", "manutencao"] = "disponivel"
    context_window: int | None = None
    usage_limit: str | None = Field(default=None, max_length=200)
    tags: list[str] = Field(default=[], max_length=20)
    is_new: bool = False
    is_featured: bool = False
    sort_order: int = 0
    requires_access_approval: bool = False
    access_summary: str = Field(default="", max_length=2000)
    access_documentation: str = Field(default="", max_length=20_000)
    default_endpoint_base: str | None = Field(default=None, max_length=500)
    default_auth_scheme: Literal["api_key", "bearer", "custom"] = "api_key"


class AIModelCreate(AIModelBase):
    pass


class AIModelUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    category: Literal["texto", "codigo", "visao", "multimodal", "embeddings"] | None = None
    description: str | None = None
    capabilities: list[str] | None = None
    status: Literal["disponivel", "beta", "manutencao"] | None = None
    context_window: int | None = None
    usage_limit: str | None = None
    tags: list[str] | None = None
    is_new: bool | None = None
    is_featured: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    requires_access_approval: bool | None = None
    access_summary: str | None = Field(default=None, max_length=2000)
    access_documentation: str | None = Field(default=None, max_length=20_000)
    default_endpoint_base: str | None = Field(default=None, max_length=500)
    default_auth_scheme: Literal["api_key", "bearer", "custom"] | None = None


class AIModelResponse(AIModelBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_has_any_access_request: bool = False
    user_pending_requests_count: int = 0
    user_approved_requests_count: int = 0
    user_revocation_requested_count: int = 0

    model_config = ConfigDict(from_attributes=True)
