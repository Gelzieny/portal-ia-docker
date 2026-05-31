from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IdeaModerationStatus(str, Enum):
    aguardando_curadoria = "aguardando_curadoria"
    publicada = "publicada"
    rejeitada = "rejeitada"
    exclusao_solicitada = "exclusao_solicitada"
    excluida = "excluida"


class IdeaStatus(str, Enum):
    planejada = "planejada"
    em_desenvolvimento = "em_desenvolvimento"
    concluida = "concluida"


class IdeaCommentModerationStatus(str, Enum):
    publicado = "publicado"
    oculto = "oculto"


class IdeaReaction(str, Enum):
    thumbs_up = "thumbs_up"
    heart = "heart"
    rocket = "rocket"
    eyes = "eyes"
    idea = "idea"


class IdeaTopicResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    color: str
    icon: str | None = None
    description: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IdeaVersionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    forecast: str | None = None
    sort_order: int
    is_active: bool
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IdeaVersionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    forecast: str | None = Field(default=None, max_length=80)
    sort_order: int = 0
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class IdeaVersionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    forecast: str | None = Field(default=None, max_length=80)
    sort_order: int | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class IdeaRoadmapUpdate(BaseModel):
    idea_status: IdeaStatus | None = None
    version_id: UUID | None = None


class IdeaCreate(BaseModel):
    title: str = Field(min_length=8, max_length=240)
    description: str = Field(min_length=20)
    topic_ids: list[UUID] = Field(default_factory=list, max_length=3)

    @field_validator("title", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class IdeaUpdate(BaseModel):
    title: str = Field(min_length=8, max_length=240)
    description: str = Field(min_length=20)
    topic_ids: list[UUID] = Field(default_factory=list, max_length=3)

    @field_validator("title", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class IdeaCurationDecision(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class IdeaCommentCreate(BaseModel):
    content: str = Field(min_length=2, max_length=5000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        return value.strip()


class IdeaCommentModerationDecision(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class IdeaSimilarResponse(BaseModel):
    id: UUID
    title: str
    description: str
    moderation_status: IdeaModerationStatus
    idea_status: IdeaStatus | None = None
    vote_count: int = 0
    comment_count: int = 0
    similarity_score: float
    topic_match_count: int = 0
    published_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IdeaResponse(BaseModel):
    id: UUID
    title: str
    description: str
    author_id: UUID
    moderation_status: IdeaModerationStatus
    idea_status: IdeaStatus | None
    version_id: UUID | None
    curation_notes: str | None
    rejection_reason: str | None
    deletion_requested_at: datetime | None
    deletion_request_reason: str | None
    deleted_at: datetime | None
    published_at: datetime | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    author_name: str | None = None
    author_organ: str | None = None
    version_name: str | None = None
    version_forecast: str | None = None

    model_config = ConfigDict(from_attributes=True)


class IdeaDetailResponse(IdeaResponse):
    topics: list[IdeaTopicResponse] = Field(default_factory=list)
    vote_count: int = 0
    comment_count: int = 0
    user_has_voted: bool = False
    can_edit: bool = False
    can_delete: bool = False


class RoadmapVersionResponse(BaseModel):
    version: IdeaVersionResponse
    ideas: list[IdeaDetailResponse] = Field(default_factory=list)


class IdeaCommentResponse(BaseModel):
    id: UUID
    idea_id: UUID
    parent_id: UUID | None
    author_id: UUID
    author_name: str | None = None
    author_organ: str | None = None
    content: str
    moderation_status: IdeaCommentModerationStatus
    moderation_reason: str | None
    moderated_by: UUID | None
    moderated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    reactions: dict[IdeaReaction, int] = Field(default_factory=dict)
    user_reaction: IdeaReaction | None = None
    replies: list["IdeaCommentResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
