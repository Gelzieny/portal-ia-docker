from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

NewsCategory = Literal["ATUALIZAÇÃO", "MANUTENÇÃO", "AVISO", "NOVO RECURSO", "SEGURANÇA"]


class NewsCreate(BaseModel):
    category: NewsCategory = "AVISO"
    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=1, max_length=1000)
    content: str = Field(default="", max_length=50000)
    link: str | None = Field(default=None, max_length=500)
    reading_time: int = Field(default=3, ge=1, le=120)
    is_published: bool = False
    published_at: datetime | None = None


class NewsUpdate(BaseModel):
    category: NewsCategory | None = None
    title: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=1000)
    content: str | None = Field(default=None, max_length=50000)
    link: str | None = Field(default=None, max_length=500)
    reading_time: int | None = Field(default=None, ge=1, le=120)
    is_published: bool | None = None
    published_at: datetime | None = None


class NewsResponse(BaseModel):
    id: UUID
    category: str
    title: str
    summary: str
    content: str
    link: str | None
    reading_time: int
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
