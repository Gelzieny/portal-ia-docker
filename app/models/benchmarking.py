from uuid import UUID

from pydantic import BaseModel, Field


class ProcessQuestionRequest(BaseModel):
    questaoId: UUID
    modeloId: UUID


class ProcessModelRequest(BaseModel):
    ids: list[UUID] | None = None


class ProcessResultRequest(BaseModel):
    resultadoId: UUID


class VectorSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    embedding: list[float] | None = None
    limit: int = Field(default=5, ge=1, le=20)


class ChatRequest(BaseModel):
    modelProvider: str | None = None
    model: str | None = None
    messages: list[dict] = Field(default_factory=list)
