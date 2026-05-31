import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


class AuthService:
    @staticmethod
    def decode_access_token(token: str) -> dict:
        normalized_token = token.strip()
        if normalized_token.lower().startswith("bearer "):
            normalized_token = normalized_token[7:].strip()

        try:
            decoded = jwt.decode(normalized_token, options={"verify_signature": False})
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
            ) from exc

        if not decoded.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
            )

        return decoded

    @staticmethod
    def verify_login(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict:
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )

        return AuthService.decode_access_token(credentials.credentials)
