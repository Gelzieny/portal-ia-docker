from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user_prompt import AuthorInfo, PromptSource, PromptVersionResponse, PublicationStatus


class PromptVariable(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    example: str = Field(default="", max_length=1000)


class PromptBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    content: str = Field(max_length=50_000)
    category_id: UUID | None = None
    model_id: UUID | None = None
    tags: list[str] = Field(default=[], max_length=20)
    difficulty: Literal["iniciante", "intermediario", "avancado"] = "iniciante"
    variables: list[dict[str, Any]] = []
    is_public: bool = True


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    content: str | None = Field(default=None, max_length=50_000)
    category_id: UUID | None = None
    model_id: UUID | None = None
    tags: list[str] | None = None
    difficulty: Literal["iniciante", "intermediario", "avancado"] | None = None
    variables: list[dict[str, Any]] | None = None
    is_public: bool | None = None
    is_active: bool | None = None


class PromptCategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    color: str
    icon: str = "FileText"
    description: str = ""
    sort_order: int
    prompt_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PromptResponse(PromptBase):
    id: UUID
    usage_count: int
    rating_avg: float = 0.0
    rating_count: int = 0
    is_active: bool
    is_favorite: bool = False
    user_has_used: bool = False
    author_id: UUID | None
    created_at: datetime
    updated_at: datetime
    category: PromptCategoryResponse | None = None
    # ── Campos de publicação e curadoria (UP-2) ──────────────────────────────
    publication_status: PublicationStatus = PublicationStatus.publico
    source: PromptSource = PromptSource.oficial
    version: int = 1
    report_count: int = 0
    submitted_at: datetime | None = None
    submission_notes: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    original_author_name: str | None = None
    is_owner: bool = False
    user_has_reported: bool = False
    author: AuthorInfo | None = None
    versions: list[PromptVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PromptReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    used_before: bool = False

    @field_validator("rating", mode="before")
    @classmethod
    def coerce_rating(cls, v: object) -> int:
        return int(v)


class PromptReviewResponse(BaseModel):
    id: UUID
    prompt_id: UUID
    user_id: UUID
    rating: int
    comment: str | None
    used_before: bool
    is_approved: bool
    user_name: str | None = None
    user_organ: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
