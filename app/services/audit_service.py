import json
from uuid import UUID
from typing import Any
from fastapi import Request

from app.core import database

SENSITIVE_METADATA_KEYS = {
  "access_key",
  "access_secret",
  "consumer_key",
  "consumer_secret",
  "password",
  "new_password",
  "current_password",
  "refresh_token",
  "token",
}


def _client_ip(request: Request | None) -> str | None:
  if request is None or request.client is None:
    return None
  
  forwarded_for = request.headers.get("X-Forwarded-For")

  if forwarded_for:
    return forwarded_for.split(",")[0].strip()
  
  return request.client.host


def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
  if not metadata:
    return {}
  
  sanitized: dict[str, Any] = {}

  for key, value in metadata.items():
    if key.lower() in SENSITIVE_METADATA_KEYS:
      sanitized[key] = "[redacted]"
    else:
      sanitized[key] = value

  return sanitized

async def log_audit(
  *,
  user_id: UUID | str | None,
  action: str,
  entity: str,
  entity_id: UUID | str | None = None,
  metadata: dict[str, Any] | None = None,
  request: Request | None = None,
) -> None:
  await database.execute(
    """
    INSERT INTO audit_logs (user_id, action, entity, entity_id, metadata, ip_address, user_agent)
    VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
    """,
    user_id,
    action,
    entity,
    entity_id,
    json.dumps(_sanitize_metadata(metadata)),
    _client_ip(request),
    request.headers.get("User-Agent") if request else None,
  )
