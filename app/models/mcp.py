from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from enum import Enum


class MCPServerStatus(str, Enum):
    disponivel = "disponivel"
    beta = "beta"
    experimental = "experimental"
    descontinuado = "descontinuado"


class MCPClientType(str, Enum):
    claude_desktop = "claude_desktop"
    vscode = "vscode"
    cursor = "cursor"
    terminal = "terminal"
    custom = "custom"


# ── Sub-schemas ───────────────────────────────────────────────────────────────

class MCPToolParam(BaseModel):
    name: str
    type: str
    required: bool = False
    description: str
    example: str | None = None

    @field_validator("example", mode="before")
    @classmethod
    def coerce_example_to_str(cls, v: object) -> str | None:
        if v is None:
            return None
        return str(v)


class MCPToolResponse(BaseModel):
    id: UUID
    name: str
    description: str
    parameters: list[MCPToolParam]
    return_type: str | None
    example_call: str | None
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class MCPToolCreate(BaseModel):
    name: str
    description: str = ""
    parameters: list[MCPToolParam] = []
    return_type: str | None = None
    example_call: str | None = None
    sort_order: int = 0


class MCPToolUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parameters: list[MCPToolParam] | None = None
    return_type: str | None = None
    example_call: str | None = None
    sort_order: int | None = None


class MCPAgentResponse(BaseModel):
    id: UUID
    name: str
    description: str
    capabilities: list[str]
    base_model: str | None
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class MCPAgentCreate(BaseModel):
    name: str
    description: str = ""
    capabilities: list[str] = []
    base_model: str | None = None
    system_prompt: str | None = None
    sort_order: int = 0


class MCPAgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    capabilities: list[str] | None = None
    base_model: str | None = None
    system_prompt: str | None = None
    sort_order: int | None = None


class MCPResourceResponse(BaseModel):
    id: UUID
    name: str
    uri_template: str
    description: str
    mime_type: str | None
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class MCPResourceCreate(BaseModel):
    name: str
    uri_template: str
    description: str = ""
    mime_type: str | None = None
    sort_order: int = 0


class MCPResourceUpdate(BaseModel):
    name: str | None = None
    uri_template: str | None = None
    description: str | None = None
    mime_type: str | None = None
    sort_order: int | None = None


class MCPConfigSnippetResponse(BaseModel):
    id: UUID
    client_type: MCPClientType
    label: str
    config_json: str
    notes: str | None
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class MCPConfigSnippetCreate(BaseModel):
    client_type: MCPClientType
    label: str
    config_json: str
    notes: str | None = None
    sort_order: int = 0


class MCPConfigSnippetUpdate(BaseModel):
    client_type: MCPClientType | None = None
    label: str | None = None
    config_json: str | None = None
    notes: str | None = None
    sort_order: int | None = None


class MCPCategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str
    icon: str
    color: str
    server_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class MCPCategoryCreate(BaseModel):
    name: str
    slug: str | None = None
    description: str = ""
    icon: str = "Plug"
    color: str = "#1a5e38"
    sort_order: int = 0


class MCPCategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


# ── Server schemas ────────────────────────────────────────────────────────────

class MCPServerListResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    tagline: str
    status: MCPServerStatus
    is_verified: bool
    is_featured: bool
    is_official: bool
    category: MCPCategoryResponse | None
    tags: list[str]
    rating_avg: float
    rating_count: int
    install_count: int
    tool_count: int = 0
    agent_count: int = 0
    compatible_models: list[str]
    is_active: bool = True
    is_favorite: bool = False
    is_installed: bool = False
    model_config = ConfigDict(from_attributes=True)


class MCPServerDetailResponse(MCPServerListResponse):
    description: str
    repository_url: str | None
    docs_url: str | None
    homepage_url: str | None
    version: str | None
    license: str | None
    author_name: str | None
    author_org: str | None
    tools: list[MCPToolResponse] = []
    agents: list[MCPAgentResponse] = []
    resources: list[MCPResourceResponse] = []
    config_snippets: list[MCPConfigSnippetResponse] = []
    model_config = ConfigDict(from_attributes=True)


class MCPServerCreate(BaseModel):
    name: str
    slug: str | None = None
    tagline: str
    description: str
    category_id: UUID | None = None
    status: MCPServerStatus = MCPServerStatus.experimental
    is_verified: bool = False
    is_featured: bool = False
    is_official: bool = False
    repository_url: str | None = None
    docs_url: str | None = None
    homepage_url: str | None = None
    version: str | None = None
    license: str | None = None
    compatible_models: list[str] = []
    author_name: str | None = None
    author_org: str | None = None
    tags: list[str] = []


class MCPServerUpdate(BaseModel):
    name: str | None = None
    tagline: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    status: MCPServerStatus | None = None
    is_verified: bool | None = None
    is_featured: bool | None = None
    is_official: bool | None = None
    repository_url: str | None = None
    docs_url: str | None = None
    homepage_url: str | None = None
    version: str | None = None
    license: str | None = None
    compatible_models: list[str] | None = None
    author_name: str | None = None
    author_org: str | None = None
    tags: list[str] | None = None
    sort_order: int | None = None
    is_active: bool | None = None


# ── Review schemas ────────────────────────────────────────────────────────────

class MCPReviewCreate(BaseModel):
    rating: int  # 1-5
    comment: str | None = None


class MCPReviewResponse(BaseModel):
    id: UUID
    rating: int
    comment: str | None
    user_name: str
    user_organ: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Install schema ────────────────────────────────────────────────────────────

class MCPInstallCreate(BaseModel):
    client_type: MCPClientType | None = None
