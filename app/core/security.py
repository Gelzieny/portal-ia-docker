import base64
import bcrypt
import hashlib
from functools import lru_cache
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

def _prepare(password: str) -> bytes:
  """Pre-hash com SHA-256 — garante entrada sempre <72 bytes para o bcrypt."""
  digest = hashlib.sha256(password.encode()).digest()
  return base64.b64encode(digest)

def hash_password(password: str) -> str:
  return bcrypt.hashpw(_prepare(password), bcrypt.gensalt(12)).decode()

def verify_password(plain: str, hashed: str) -> bool:
  return bcrypt.checkpw(_prepare(plain), hashed.encode())

@lru_cache(maxsize=1)
def _model_access_cipher() -> Fernet:
  key_material = hashlib.sha256(settings.MODEL_ACCESS_CREDENTIALS_SECRET_KEY.encode()).digest()
  return Fernet(base64.urlsafe_b64encode(key_material))

def encrypt_model_access_secret(raw: str) -> str:
  return _model_access_cipher().encrypt(raw.encode()).decode()

def decrypt_model_access_secret(token: str) -> str:
  try:
    return _model_access_cipher().decrypt(token.encode()).decode()
  except InvalidToken as exc:
    raise ValueError("Credencial criptografada inválida") from exc
