from pydantic import BaseModel, Field


class TokenInfoRequest(BaseModel):
    token: str = Field(min_length=1)


class TokenInfoResponse(BaseModel):
    claims: dict
