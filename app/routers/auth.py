from fastapi import APIRouter

from app.models.auth import TokenInfoRequest, TokenInfoResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token-info", response_model=TokenInfoResponse)
async def get_token_info(body: TokenInfoRequest):
    return TokenInfoResponse(claims=AuthService.decode_access_token(body.token))
