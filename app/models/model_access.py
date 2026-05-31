from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


ModelAccessRequestStatus = Literal[
    "pendente",
    "aprovado",
    "negado",
    "revogacao_solicitada",
    "revogado",
    "cancelado",
]


def normalize_application_name(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_public_headers(value: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, header_value in value.items():
        header_name = key.strip()
        if not header_name:
            raise ValueError("Os nomes dos public_headers não podem ser vazios")
        if "\n" in header_name or "\r" in header_name:
            raise ValueError("Os nomes dos public_headers não podem conter quebras de linha")
        header_content = header_value.strip()
        if "\n" in header_content or "\r" in header_content:
            raise ValueError("Os valores dos public_headers não podem conter quebras de linha")
        normalized[header_name] = header_content
    return normalized


class ModelAccessRequestCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: UUID
    application_name: str = Field(min_length=3, max_length=200)
    justification: str = Field(min_length=30, max_length=10_000)
    intended_use: str | None = Field(default=None, max_length=10_000)

    @field_validator("application_name")
    @classmethod
    def validate_application_name(cls, value: str) -> str:
        normalized = normalize_application_name(value)
        if len(normalized) < 3:
            raise ValueError("Aplicação deve ter ao menos 3 caracteres")
        return normalized


class ModelAccessDecision(BaseModel):
    action: Literal["aprovar", "negar"]
    review_notes: str | None = Field(default=None, max_length=10_000)
    endpoint_base: str | None = Field(default=None, max_length=500)
    access_key: str | None = Field(default=None, max_length=4000)
    access_secret: str | None = Field(default=None, max_length=4000)
    public_headers: dict[str, str] = Field(default_factory=dict)
    usage_notes: str | None = Field(default=None, max_length=10_000)

    @field_validator("public_headers")
    @classmethod
    def validate_public_headers(cls, value: dict[str, str]) -> dict[str, str]:
        return normalize_public_headers(value)


class ModelAccessRevoke(BaseModel):
    review_notes: str | None = Field(default=None, max_length=10_000)


class ModelAccessRevocationRequest(BaseModel):
    review_notes: str | None = Field(default=None, max_length=10_000)


class ModelAccessRevocationDecision(BaseModel):
    action: Literal["confirmar", "rejeitar"]
    review_notes: str | None = Field(default=None, max_length=10_000)


class ModelAccessCredentialsUpdate(BaseModel):
    endpoint_base: str | None = Field(default=None, max_length=500)
    access_key: str | None = Field(default=None, max_length=4000)
    access_secret: str | None = Field(default=None, max_length=4000)
    public_headers: dict[str, str] | None = None
    usage_notes: str | None = Field(default=None, max_length=10_000)

    @field_validator("public_headers")
    @classmethod
    def validate_public_headers(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return value
        return normalize_public_headers(value)


class ModelAccessRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    model_id: UUID
    user_id: UUID
    application_name: str
    status: ModelAccessRequestStatus
    justification: str
    intended_use: str | None = None
    request_context: dict = Field(default_factory=dict)
    review_notes: str | None = None
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_name: str | None = None
    model_slug: str | None = None
    user_name: str | None = None
    user_organ: str | None = None
    has_credentials: bool = False
    endpoint_base: str | None = None
    access_key: str | None = None
    access_secret_masked: str | None = None
    public_headers: dict[str, str] = Field(default_factory=dict)
    usage_notes: str | None = None

class ModelAccessCredentialsResponse(BaseModel):
    endpoint_base: str
    access_key: str
    access_secret_masked: str
    public_headers: dict[str, str] = Field(default_factory=dict)
    usage_notes: str | None = None


class ModelAccessSecretRevealResponse(BaseModel):
    access_secret: str


class ModelAccessCountsResponse(BaseModel):
    pendentes: int
    revogacao_solicitada: int
    aprovados: int
    negados: int
    revogados: int
    total: int
