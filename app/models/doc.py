from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocSectionCreate(BaseModel):
    title: str
    slug: str
    sort_order: int = 0
    parent_id: UUID | None = None


class DocSectionUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class DocSectionResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    sort_order: int
    parent_id: UUID | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DocArticleCreate(BaseModel):
    section_id: UUID
    title: str
    slug: str
    content: str = ""
    reading_time: int = 1
    sort_order: int = 0
    is_published: bool = False


class DocArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    reading_time: int | None = None
    sort_order: int | None = None
    is_published: bool | None = None
    is_active: bool | None = None


class DocArticleResponse(BaseModel):
    id: UUID
    section_id: UUID
    title: str
    slug: str
    content: str
    reading_time: int
    sort_order: int
    is_published: bool
    is_active: bool
    author_id: UUID | None
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocSearchResult(BaseModel):
    id: UUID
    title: str
    slug: str
    section_title: str
    excerpt: str


class DocSectionWithArticles(DocSectionResponse):
    articles: list[DocArticleResponse] = []
