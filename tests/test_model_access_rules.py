import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4


os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from fastapi import HTTPException, Response

from app.core.deps import require_model_access_curation
from app.models.model_access import (
    ModelAccessCredentialsUpdate,
    ModelAccessDecision,
    ModelAccessRequestCreate,
    ModelAccessRevocationDecision,
)
from app.routers.model_access import (
    _build_request_response,
    admin_decide_request,
    admin_review_revocation,
    admin_update_credentials,
    create_request,
    get_my_credentials,
)


class ModelAccessRulesTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_request_normalizes_application_name_before_persisting(self):
        user_id = str(uuid4())
        model_id = uuid4()
        request_id = uuid4()
        request_row = {
            "id": request_id,
            "model_id": model_id,
            "user_id": user_id,
            "application_name": "SIGRH Portal",
            "status": "pendente",
            "justification": "Justificativa institucional suficientemente longa para passar na validacao.",
            "intended_use": None,
            "request_context": {},
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "model_name": "Modelo X",
            "model_slug": "modelo-x",
            "user_name": "Ana",
            "user_organ": "SGG",
            "credential_id": None,
            "default_endpoint_base": None,
            "public_headers": {},
            "usage_notes": None,
            "credential_is_active": False,
        }

        with patch("app.routers.model_access._ensure_model_requires_request", new=AsyncMock()), \
             patch("app.routers.model_access._ensure_active_unique", new=AsyncMock()) as ensure_unique, \
             patch("app.routers.model_access.database.fetchrow", new=AsyncMock(return_value={"id": request_id})) as fetchrow, \
             patch("app.routers.model_access._get_request_row", new=AsyncMock(return_value=request_row)), \
             patch("app.routers.model_access._log_audit", new=AsyncMock()):
            result = await create_request(
                ModelAccessRequestCreate(
                    model_id=model_id,
                    application_name="  SIGRH   Portal  ",
                    justification="Justificativa institucional suficientemente longa para passar na validacao.",
                ),
                {"id": user_id},
            )

        ensure_unique.assert_awaited_once_with(user_id, model_id, "SIGRH Portal")
        insert_args = fetchrow.await_args.args
        self.assertEqual(insert_args[3], "SIGRH Portal")
        self.assertEqual(result.application_name, "SIGRH Portal")

    async def test_get_my_credentials_sets_no_store_and_returns_masked_secret(self):
        request_id = uuid4()
        user_id = str(uuid4())
        row = {
            "id": request_id,
            "user_id": user_id,
            "status": "aprovado",
            "credential_id": uuid4(),
            "credential_is_active": True,
            "endpoint_base": "https://api.exemplo.gov.br/v1/chat",
            "default_endpoint_base": None,
            "access_key_encrypted": "enc-key",
            "access_secret_encrypted": "enc-secret",
            "public_headers": {"X-Env": "prod"},
            "usage_notes": "Uso interno",
        }
        response = Response()

        with patch("app.routers.model_access._get_request_row", new=AsyncMock(return_value=row)), \
             patch("app.routers.model_access.decrypt_model_access_secret", side_effect=["abcd1234", "segredo-super-seguro"]):
            result = await get_my_credentials(request_id, response, {"id": user_id})

        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        self.assertEqual(result.access_key, "abcd1234")
        self.assertIn("•", result.access_secret_masked)
        self.assertEqual(result.public_headers["X-Env"], "prod")

    async def test_get_my_credentials_accepts_public_headers_as_json_string(self):
        request_id = uuid4()
        user_id = str(uuid4())
        row = {
            "id": request_id,
            "user_id": user_id,
            "status": "aprovado",
            "credential_id": uuid4(),
            "credential_is_active": True,
            "endpoint_base": "https://api.exemplo.gov.br/v1/chat",
            "default_endpoint_base": None,
            "access_key_encrypted": "enc-key",
            "access_secret_encrypted": "enc-secret",
            "public_headers": "{\"X-App\":\"portal\"}",
            "usage_notes": "Uso interno",
        }
        response = Response()

        with patch("app.routers.model_access._get_request_row", new=AsyncMock(return_value=row)), \
             patch("app.routers.model_access.decrypt_model_access_secret", side_effect=["abcd1234", "segredo-super-seguro"]):
            result = await get_my_credentials(request_id, response, {"id": user_id})

        self.assertEqual(result.public_headers, {"X-App": "portal"})

    async def test_build_request_response_accepts_json_fields_as_strings(self):
        row = {
            "id": uuid4(),
            "model_id": uuid4(),
            "user_id": str(uuid4()),
            "application_name": "SIGRH Portal",
            "status": "pendente",
            "justification": "Justificativa institucional suficientemente longa para passar na validacao.",
            "intended_use": None,
            "request_context": "{}",
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "model_name": "Modelo X",
            "model_slug": "modelo-x",
            "user_name": "Ana",
            "user_organ": "SGG",
            "credential_id": None,
            "endpoint_base": None,
            "default_endpoint_base": None,
            "access_key_encrypted": None,
            "access_secret_encrypted": None,
            "public_headers": "{\"X-App\":\"portal\"}",
            "usage_notes": None,
            "credential_is_active": False,
        }

        result = _build_request_response(row)

        self.assertEqual(result.request_context, {})
        self.assertEqual(result.public_headers, {"X-App": "portal"})

    async def test_review_revocation_reject_requires_notes(self):
        request_id = uuid4()
        row = {
            "id": request_id,
            "status": "revogacao_solicitada",
            "model_id": uuid4(),
            "user_id": uuid4(),
        }
        with patch("app.routers.model_access._get_request_row", new=AsyncMock(return_value=row)):
            with self.assertRaises(HTTPException) as ctx:
                await admin_review_revocation(
                    request_id,
                    ModelAccessRevocationDecision(action="rejeitar", review_notes=None),
                    {"id": str(uuid4()), "role": "curador_modelos"},
                )
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_admin_decide_request_rejects_blank_credentials_after_trim(self):
        request_id = uuid4()
        row = {
            "id": request_id,
            "status": "pendente",
            "model_id": uuid4(),
            "user_id": uuid4(),
        }
        with patch("app.routers.model_access._get_request_row", new=AsyncMock(return_value=row)):
            with self.assertRaises(HTTPException) as ctx:
                await admin_decide_request(
                    request_id,
                    ModelAccessDecision(
                        action="aprovar",
                        endpoint_base="   ",
                        access_key="  chave  ",
                        access_secret="  segredo  ",
                    ),
                    {"id": str(uuid4()), "role": "admin"},
                )
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_model_access_headers_validation_blocks_newlines(self):
        with self.assertRaises(ValueError):
            ModelAccessDecision(
                action="aprovar",
                endpoint_base="https://api.exemplo.gov.br",
                access_key="key",
                access_secret="secret",
                public_headers={"X-App\nName": "portal"},
            )

        with self.assertRaises(ValueError):
            ModelAccessCredentialsUpdate(
                endpoint_base="https://api.exemplo.gov.br",
                access_key="key",
                access_secret="secret",
                public_headers={"X-App": "portal\r\ninterno"},
            )

    async def test_review_revocation_reject_restores_approved_status(self):
        request_id = uuid4()
        current_row = {
            "id": request_id,
            "status": "revogacao_solicitada",
            "model_id": uuid4(),
            "user_id": uuid4(),
        }
        updated_row = {
            **current_row,
            "status": "aprovado",
            "application_name": "SIGRH Portal",
            "justification": "Justificativa institucional suficientemente longa para passar na validacao.",
            "intended_use": None,
            "request_context": {},
            "review_notes": "Revogação rejeitada com manutenção do acesso.",
            "reviewed_by": uuid4(),
            "reviewed_at": "2026-01-01T00:00:00+00:00",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "model_name": "Modelo X",
            "model_slug": "modelo-x",
            "user_name": "Ana",
            "user_organ": "SGG",
            "credential_id": uuid4(),
            "credential_is_active": True,
            "default_endpoint_base": "https://api.exemplo.gov.br",
            "endpoint_base": "https://api.exemplo.gov.br",
            "access_key_encrypted": "enc-key",
            "access_secret_encrypted": "enc-secret",
            "public_headers": {},
            "usage_notes": None,
        }

        with patch("app.routers.model_access._get_request_row", new=AsyncMock(side_effect=[current_row, updated_row])), \
             patch("app.routers.model_access.database.execute", new=AsyncMock()) as execute, \
             patch("app.routers.model_access._log_audit", new=AsyncMock()), \
             patch("app.routers.model_access.create_notification", new=AsyncMock()), \
             patch("app.routers.model_access.decrypt_model_access_secret", side_effect=["abc12345", "segredo123"]):
            result = await admin_review_revocation(
                request_id,
                ModelAccessRevocationDecision(
                    action="rejeitar",
                    review_notes="Revogação rejeitada com manutenção do acesso.",
                ),
                {"id": str(uuid4()), "role": "curador_modelos"},
            )

        self.assertEqual(result.status, "aprovado")
        self.assertEqual(execute.await_count, 2)

    async def test_admin_update_credentials_reactivates_request_credentials(self):
        request_id = uuid4()
        current_row = {
            "id": request_id,
            "status": "revogacao_solicitada",
            "model_id": uuid4(),
            "user_id": uuid4(),
        }
        updated_row = {
            **current_row,
            "status": "revogacao_solicitada",
            "application_name": "Chat Institucional",
            "justification": "Justificativa institucional suficientemente longa para passar na validacao.",
            "intended_use": None,
            "request_context": {},
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "model_name": "Modelo Y",
            "model_slug": "modelo-y",
            "user_name": "João",
            "user_organ": "SEAD",
            "credential_id": uuid4(),
            "credential_is_active": True,
            "default_endpoint_base": "https://api.exemplo.gov.br",
            "endpoint_base": "https://api.exemplo.gov.br/v2",
            "access_key_encrypted": "enc-key",
            "access_secret_encrypted": "enc-secret",
            "public_headers": {"X-App": "chat"},
            "usage_notes": "Atualizado",
        }

        with patch("app.routers.model_access._get_request_row", new=AsyncMock(side_effect=[current_row, updated_row])), \
             patch("app.routers.model_access._upsert_credentials", new=AsyncMock()) as upsert_credentials, \
             patch("app.routers.model_access._log_audit", new=AsyncMock()), \
             patch("app.routers.model_access.decrypt_model_access_secret", side_effect=["abc12345", "segredo123"]):
            result = await admin_update_credentials(
                request_id,
                ModelAccessCredentialsUpdate(
                    endpoint_base="https://api.exemplo.gov.br/v2",
                    access_key="nova-chave",
                    access_secret="novo-segredo",
                    public_headers={"X-App": "chat"},
                    usage_notes="Atualizado",
                ),
                {"id": str(uuid4()), "role": "admin"},
            )

        self.assertEqual(result.status, "revogacao_solicitada")
        upsert_credentials.assert_awaited_once()

    async def test_admin_update_credentials_allows_updating_headers_and_notes_without_new_secrets(self):
        request_id = uuid4()
        current_row = {
            "id": request_id,
            "status": "aprovado",
            "model_id": uuid4(),
            "user_id": uuid4(),
            "credential_id": uuid4(),
            "credential_is_active": True,
            "default_endpoint_base": "https://api.exemplo.gov.br",
            "endpoint_base": "https://api.exemplo.gov.br/v1",
            "access_key_encrypted": "enc-key",
            "access_secret_encrypted": "enc-secret",
            "public_headers": {"X-App": "anterior"},
            "usage_notes": "Nota anterior",
        }
        updated_row = {
            **current_row,
            "application_name": "Painel Executivo",
            "justification": "Justificativa institucional suficientemente longa para passar na validacao.",
            "intended_use": None,
            "request_context": {},
            "review_notes": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "model_name": "Modelo Z",
            "model_slug": "modelo-z",
            "user_name": "Maria",
            "user_organ": "SEINFRA",
            "public_headers": {"X-App": "novo"},
            "usage_notes": "Notas revisadas",
        }

        with patch("app.routers.model_access._get_request_row", new=AsyncMock(side_effect=[current_row, updated_row])), \
             patch("app.routers.model_access._upsert_credentials", new=AsyncMock()) as upsert_credentials, \
             patch("app.routers.model_access._log_audit", new=AsyncMock()), \
             patch("app.routers.model_access.decrypt_model_access_secret", side_effect=["chave-atual", "segredo-atual", "chave-atual", "segredo-atual"]):
            result = await admin_update_credentials(
                request_id,
                ModelAccessCredentialsUpdate(
                    public_headers={"X-App": "novo"},
                    usage_notes="Notas revisadas",
                ),
                {"id": str(uuid4()), "role": "admin"},
            )

        self.assertEqual(result.usage_notes, "Notas revisadas")
        upsert_credentials.assert_awaited_once()
        kwargs = upsert_credentials.await_args.kwargs
        self.assertEqual(kwargs["endpoint_base"], "https://api.exemplo.gov.br/v1")
        self.assertEqual(kwargs["access_key"], "chave-atual")
        self.assertEqual(kwargs["access_secret"], "segredo-atual")
        self.assertEqual(kwargs["public_headers"], {"X-App": "novo"})
        self.assertEqual(kwargs["usage_notes"], "Notas revisadas")

    async def test_require_model_access_curation_allows_only_admin_and_curador_modelos(self):
        checker = require_model_access_curation()
        admin = await checker({"id": str(uuid4()), "role": "admin"})
        curator = await checker({"id": str(uuid4()), "role": "curador_modelos"})

        self.assertEqual(admin["role"], "admin")
        self.assertEqual(curator["role"], "curador_modelos")

        with self.assertRaises(HTTPException) as ctx:
            await checker({"id": str(uuid4()), "role": "gestor"})
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
