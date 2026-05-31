from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class PublicationStatus(str, Enum):
    rascunho   = "rascunho"
    privado    = "privado"
    aguardando = "aguardando"
    publico    = "publico"
    em_revisao = "em_revisao"
    arquivado  = "arquivado"


class PromptSource(str, Enum):
    oficial    = "oficial"
    comunidade = "comunidade"


class ReportReason(str, Enum):
    conteudo_inapropriado = "conteudo_inapropriado"
    informacao_incorreta  = "informacao_incorreta"
    violacao_lgpd         = "violacao_lgpd"
    uso_indevido          = "uso_indevido"
    duplicado             = "duplicado"
    outro                 = "outro"


# ── Nested response models (usados em PromptResponse) ─────────────────────────

class AuthorInfo(BaseModel):
    id: UUID | None
    name: str            # usa original_author_name se autor desativado
    organ: str

    model_config = ConfigDict(from_attributes=True)


class PromptVersionResponse(BaseModel):
    version_number: int
    title: str
    approved_at: datetime
    approved_by_name: str | None

    model_config = ConfigDict(from_attributes=True)


# ── Criação e edição de prompts pelo usuário ──────────────────────────────────

class UserPromptSave(BaseModel):
    """Salvar rascunho ou prompt privado."""
    title: str
    description: str = ""
    content: str
    category_id: UUID | None = None
    difficulty: Literal["iniciante", "intermediario", "avancado"] = "iniciante"
    tags: list[str] = []
    variables: list[dict] = []
    model_id: UUID | None = None
    save_as: Literal["rascunho", "privado"] = "privado"

    @field_validator("title")
    @classmethod
    def title_min_length(cls, v: str) -> str:
        if len(v.strip()) < 5:
            raise ValueError("Título deve ter ao menos 5 caracteres")
        return v.strip()

    @field_validator("content")
    @classmethod
    def content_min_length(cls, v: str) -> str:
        if len(v.strip()) < 20:
            raise ValueError("Conteúdo deve ter ao menos 20 caracteres")
        return v.strip()


class UserPromptSubmit(BaseModel):
    """Solicitar publicação de um prompt privado."""
    submission_notes: str | None = None


# ── Decisão do curador/admin/gestor ───────────────────────────────────────────

class PromptPublicationDecision(BaseModel):
    action: Literal["aprovar", "negar"]
    review_notes: str | None = None

    @model_validator(mode="after")
    def notes_required_for_denial(self) -> "PromptPublicationDecision":
        if self.action == "negar" and not self.review_notes:
            raise ValueError("Motivo obrigatório ao negar publicação")
        return self


class PromptArchiveBody(BaseModel):
    reason: str


# ── Reatribuição de autoria ───────────────────────────────────────────────────

class PromptReassign(BaseModel):
    new_author_id: UUID
    reason: str | None = None


# ── Denúncia ─────────────────────────────────────────────────────────────────

class PromptReportCreate(BaseModel):
    reason: ReportReason
    description: str | None = None


class PromptReportResponse(BaseModel):
    id: UUID
    prompt_id: UUID
    reason: ReportReason
    description: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptReportDecision(BaseModel):
    action: Literal["analisado", "descartado"]
    resolution_notes: str | None = None


# ── Fork ─────────────────────────────────────────────────────────────────────

class PromptForkCreate(BaseModel):
    fork_message: str | None = None


class PromptForkResponse(BaseModel):
    fork_id: UUID
    message: str
