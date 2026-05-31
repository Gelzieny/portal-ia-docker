import re
from uuid import UUID

from app.core import database


class BenchmarkingAlreadyRegistered(Exception):
    pass


class BenchmarkingNotConfigured(Exception):
    pass


def _normalize_answer(value: object) -> str:
    if value is None:
        return ""
    text = str(value).lower().strip()
    return re.sub(r"[^\w\s]", "", text).strip()


def _first_char(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return text[:1]


class BenchmarkingService:
    @staticmethod
    async def register_model_once(model_id: UUID) -> bool:
        row = await database.fetchrow(
            """
            INSERT INTO benchmarking_runs (model_id, status)
            VALUES ($1, 'pending')
            ON CONFLICT (model_id) DO NOTHING
            RETURNING id
            """,
            model_id,
        )
        return row is not None

    @staticmethod
    async def get_run(model_id: UUID):
        return await database.fetchrow(
            "SELECT * FROM benchmarking_runs WHERE model_id = $1",
            model_id,
        )

    @staticmethod
    async def list_runs() -> list[dict]:
        rows = await database.fetch(
            """
            SELECT
                br.*,
                m.name AS model_name,
                m.slug AS model_slug,
                m.provider AS model_provider
            FROM benchmarking_runs br
            JOIN modelos m ON m.id = br.model_id
            ORDER BY br.requested_at DESC
            """
        )
        return [dict(row) for row in rows]

    @staticmethod
    async def has_run(model_id: UUID) -> bool:
        return await database.fetchval(
            "SELECT EXISTS (SELECT 1 FROM benchmarking_runs WHERE model_id = $1)",
            model_id,
        )

    @staticmethod
    async def claim_pending_run(model_id: UUID):
        return await database.fetchrow(
            """
            UPDATE benchmarking_runs
            SET status = 'running',
                started_at = COALESCE(started_at, NOW()),
                error = NULL
            WHERE model_id = $1
              AND status = 'pending'
            RETURNING *
            """,
            model_id,
        )

    @staticmethod
    async def complete_run(model_id: UUID) -> None:
        await database.execute(
            """
            UPDATE benchmarking_runs
            SET status = 'completed',
                completed_at = NOW(),
                error = NULL
            WHERE model_id = $1
            """,
            model_id,
        )

    @staticmethod
    async def fail_run(model_id: UUID, error: str) -> None:
        await database.execute(
            """
            UPDATE benchmarking_runs
            SET status = 'failed',
                completed_at = NOW(),
                error = $2
            WHERE model_id = $1
            """,
            model_id,
            error[:4000],
        )

    @staticmethod
    async def map_unprocessed_questions(model_ids: list[UUID] | None = None) -> list[dict]:
        params: list = []
        model_filter = ""
        if model_ids:
            params.append(model_ids)
            model_filter = "AND m.id = ANY($1::uuid[])"

        rows = await database.fetch(
            f"""
            SELECT
                m.id AS model_id,
                m.name,
                m.provider,
                COALESCE(
                    array_agg(q.id ORDER BY q.id)
                        FILTER (WHERE q.id IS NOT NULL AND r.id IS NULL),
                    ARRAY[]::uuid[]
                ) AS pending_question_ids
            FROM modelos m
            CROSS JOIN banco_questoes q
            LEFT JOIN resultados r
                ON r.model_id = m.id
               AND r.id_banco_questoes = q.id
            WHERE m.is_active = TRUE
            {model_filter}
            GROUP BY m.id, m.name, m.provider
            ORDER BY m.name
            """,
            *params,
        )
        return [
            {
                "modelo": row["name"],
                "idModelo": row["model_id"],
                "provedor": row["provider"],
                "pendente": list(row["pending_question_ids"]),
            }
            for row in rows
        ]

    @staticmethod
    async def process_result(result_id: UUID) -> dict | None:
        result = await database.fetchrow(
            """
            SELECT
                r.id,
                r.tipo_resultado,
                r.json_resultado,
                r.erro,
                r.model_id,
                bq.metrica_id,
                bq.gabarito
            FROM resultados r
            JOIN banco_questoes bq ON bq.id = r.id_banco_questoes
            WHERE r.id = $1
            """,
            result_id,
        )
        if result is None or result["erro"]:
            return None

        indicator = BenchmarkingService.calculate_indicator(
            result["tipo_resultado"],
            result["json_resultado"] or {},
            result["gabarito"] or {},
        )
        row = await database.fetchrow(
            """
            INSERT INTO indicadores (indicador, model_id, metrica_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (model_id, metrica_id) DO UPDATE
            SET indicador = EXCLUDED.indicador,
                created_at = NOW()
            RETURNING *
            """,
            indicator,
            result["model_id"],
            result["metrica_id"],
        )
        return dict(row) if row else None

    @staticmethod
    def calculate_indicator(metric_type: str, output: dict, answer_key: dict) -> int:
        if metric_type == "CompreensaoTextual":
            return (
                100
                if _normalize_answer(output.get("resposta"))
                == _normalize_answer(answer_key.get("resposta"))
                else 0
            )
        if metric_type == "ClarezaResposta":
            return 100 if _first_char(output.get("resposta")) == str(answer_key.get("resposta")) else 0

        # Estas metricas ja retornam escala numerica no avaliador original.
        for field in ("pontuacaoGeral", "indicador", "score"):
            if field in output:
                try:
                    return int(output[field])
                except (TypeError, ValueError):
                    return 0
        return 0

    @staticmethod
    async def process_question(question_id: UUID, model_id: UUID) -> dict:
        run = await BenchmarkingService.get_run(model_id)
        if run and run["status"] not in ("pending", "running"):
            raise BenchmarkingAlreadyRegistered(
                "Analise de benchmarking ja registrada para este modelo."
            )
        if run is None:
            await BenchmarkingService.register_model_once(model_id)

        # O resultado LLM ainda depende da porta Python do provedor. A trava acima
        # impede que um fluxo externo reprocesse o mesmo modelo mais de uma vez.
        raise BenchmarkingNotConfigured(
            "Avaliacao LLM ainda nao foi configurada no backend Python."
        )

    @staticmethod
    async def run_model_once(model_id: UUID) -> dict:
        run = await BenchmarkingService.get_run(model_id)
        if run is None:
            await BenchmarkingService.register_model_once(model_id)
        elif run["status"] != "pending":
            raise BenchmarkingAlreadyRegistered(
                "Analise de benchmarking ja registrada para este modelo."
            )

        claimed = await BenchmarkingService.claim_pending_run(model_id)
        if claimed is None:
            raise BenchmarkingAlreadyRegistered(
                "Analise de benchmarking ja registrada para este modelo."
            )

        try:
            raise BenchmarkingNotConfigured(
                "Avaliacao LLM ainda nao foi configurada no backend Python."
            )
        except Exception as exc:
            await BenchmarkingService.fail_run(model_id, str(exc))
            raise

    @staticmethod
    async def ensure_registered_from_model_create(model_id: UUID) -> None:
        await BenchmarkingService.register_model_once(model_id)

    @staticmethod
    async def run_model_from_registration(model_id: UUID) -> None:
        try:
            await BenchmarkingService.run_model_once(model_id)
        except Exception:
            # A falha ja fica persistida em benchmarking_runs.error.
            return
