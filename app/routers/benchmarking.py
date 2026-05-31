from decimal import Decimal
from uuid import UUID

from asyncpg import Record
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.core import database
from app.models.benchmarking import (
    ChatRequest,
    ProcessModelRequest,
    ProcessQuestionRequest,
    ProcessResultRequest,
    VectorSearchRequest,
)
from app.services.benchmarking_service import (
    BenchmarkingAlreadyRegistered,
    BenchmarkingNotConfigured,
    BenchmarkingService,
)

router = APIRouter(tags=["benchmarking"])


def _plain(value):
    if isinstance(value, Record):
        return {key: _plain(value[key]) for key in value.keys()}
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def _rows(rows: list[Record]) -> list[dict]:
    return [_plain(row) for row in rows]


@router.get("/providers")
async def list_providers():
    rows = await database.fetch(
        """
        SELECT row_number() OVER (ORDER BY provider) AS id, provider AS nome
        FROM (SELECT DISTINCT provider FROM modelos WHERE provider <> '') p
        ORDER BY provider
        """
    )
    return _rows(rows)


@router.get("/tests")
async def list_unprocessed_questions():
    return _plain(await BenchmarkingService.map_unprocessed_questions())


@router.get("/benchmarking-runs")
async def list_benchmarking_runs():
    return _plain(await BenchmarkingService.list_runs())


@router.get("/benchmarking-runs/{model_id}")
async def get_benchmarking_run(model_id: UUID):
    row = await BenchmarkingService.get_run(model_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analise nao registrada para este modelo.")
    return _plain(row)


@router.get("/indicadores")
async def list_indicators():
    rows = await database.fetch(
        """
        SELECT
            i.*,
            jsonb_build_object(
                'id', m.id,
                'nome', m.name,
                'name', m.name,
                'provider', m.provider
            ) AS modelo
        FROM indicadores i
        JOIN modelos m ON m.id = i.model_id
        ORDER BY i.created_at DESC
        """
    )
    return _rows(rows)


@router.get("/resultados-indicadores")
async def list_results_with_indicators():
    rows = await database.fetch(
        """
        SELECT
            r.*,
            jsonb_build_object(
                'id', m.id,
                'nome', m.name,
                'name', m.name,
                'Indicadores', COALESCE(ind.indicadores, '[]'::jsonb)
            ) AS modelo
        FROM resultados r
        JOIN modelos m ON m.id = r.model_id
        LEFT JOIN LATERAL (
            SELECT jsonb_agg(to_jsonb(i.*) ORDER BY i.created_at DESC) AS indicadores
            FROM indicadores i
            WHERE i.model_id = m.id
        ) ind ON TRUE
        ORDER BY r.created_at DESC
        """
    )
    return _rows(rows)


@router.get("/contar-indicadores")
async def count_textual_comprehension_indicators():
    rows = await database.fetch(
        """
        WITH agregados_por_modelo AS (
            SELECT
                ind.model_id,
                COUNT(*) AS total_indicadores,
                AVG(ind.indicador)::DECIMAL(10,2) AS media_indicador,
                COUNT(*) AS contagem
            FROM indicadores ind
            INNER JOIN metricas met ON met.id = ind.metrica_id
            WHERE met.tipo = 'CompreensaoTextual'
            GROUP BY ind.model_id
        ),
        tokens AS (
            SELECT
                res.model_id,
                ROUND(AVG(res.input_tokens), 2) AS tokensentradas,
                ROUND(AVG(res.output_tokens), 2) AS tokensaida,
                ROUND(AVG(res.total_tokens), 2) AS tokenstotais
            FROM resultados res
            WHERE res.tipo_resultado = 'CompreensaoTextual'
            GROUP BY res.model_id
        )
        SELECT
            ag.model_id AS "modeloId",
            t.tokensentradas,
            t.tokensaida,
            t.tokenstotais,
            mdl.name AS "modeloNome",
            ag.media_indicador AS "totalIndicadores",
            ag.media_indicador AS "mediaIndicadores",
            ag.media_indicador,
            ag.contagem::INT,
            ROUND((ag.contagem::DECIMAL / NULLIF(ag.total_indicadores, 0)), 4) AS proporcao
        FROM agregados_por_modelo ag
        INNER JOIN modelos mdl ON mdl.id = ag.model_id
        LEFT JOIN tokens t ON t.model_id = ag.model_id
        ORDER BY mdl.name
        """
    )
    return _rows(rows)


@router.get("/contar-clareza")
async def count_clarity_results():
    rows = await database.fetch(
        """
        SELECT
            m.name AS modelo,
            COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'value', jsonb_build_array(
                            bq.gabarito->>'resposta',
                            left(COALESCE(r.json_resultado->>'resposta', ''), 1)
                        ),
                        'tokenstotal', r.total_tokens,
                        'tokensinput', r.input_tokens,
                        'tokensoutput', r.output_tokens
                    )
                    ORDER BY r.created_at
                ) FILTER (WHERE r.id IS NOT NULL),
                '[]'::jsonb
            ) AS valores
        FROM modelos m
        LEFT JOIN resultados r
            ON r.model_id = m.id
           AND r.tipo_resultado = 'ClarezaResposta'
        LEFT JOIN banco_questoes bq ON bq.id = r.id_banco_questoes
        WHERE m.is_active = TRUE
        GROUP BY m.id, m.name
        ORDER BY m.name
        """
    )
    return _rows(rows)


async def _metric_score(metric_type: str) -> list[dict]:
    rows = await database.fetch(
        """
        SELECT
            m.id AS modelo_id,
            m.name AS nome_modelo,
            SUM(CASE ind.indicador
                WHEN 1 THEN 1.0
                WHEN 2 THEN 0.5
                WHEN 0 THEN 0.0
                WHEN 3 THEN -1.0
                ELSE ind.indicador::NUMERIC
            END) AS soma_ponderada,
            COUNT(ind.indicador) AS total_perguntas,
            ROUND(
                SUM(CASE ind.indicador
                    WHEN 1 THEN 1.0
                    WHEN 2 THEN 0.5
                    WHEN 0 THEN 0.0
                    WHEN 3 THEN -1.0
                    ELSE ind.indicador::NUMERIC
                END) / NULLIF(COUNT(ind.indicador), 0),
                2
            ) AS metrica
        FROM indicadores ind
        JOIN modelos m ON m.id = ind.model_id
        JOIN metricas met ON met.id = ind.metrica_id
        WHERE met.tipo = $1::benchmark_tipo_metrica
        GROUP BY m.id, m.name
        ORDER BY m.name
        """,
        metric_type,
    )
    return _rows(rows)


@router.get("/direito-adm")
async def administrative_law_score():
    return await _metric_score("DireitoAdministrativo")


@router.get("/matematica")
async def math_score():
    return await _metric_score("Matematica")


@router.get("/raciociniologico")
async def logical_reasoning_score():
    return await _metric_score("RaciocinioLogico")


@router.get("/vibe-coding")
async def vibe_coding_score():
    return await _metric_score("VibeCoding")


@router.get("/embedtest")
async def embed_test_score():
    rows = await database.fetch(
        """
        SELECT
            m.id AS modelo_id,
            m.name AS nome_modelo,
            SUM(CASE ind.indicador
                WHEN 5 THEN 5.0
                WHEN 4 THEN 4.0
                WHEN 3 THEN 2.0
                WHEN 6 THEN 2.5
                WHEN 2 THEN 0.5
                WHEN 1 THEN -2.0
                WHEN 0 THEN -10.0
                ELSE 0.0
            END) AS soma_ponderada_qualidade,
            COUNT(ind.indicador) AS total_perguntas,
            ROUND(
                SUM(CASE ind.indicador
                    WHEN 5 THEN 5.0
                    WHEN 4 THEN 4.0
                    WHEN 3 THEN 2.0
                    WHEN 6 THEN 2.5
                    WHEN 2 THEN 0.5
                    WHEN 1 THEN -2.0
                    WHEN 0 THEN -10.0
                    ELSE 0.0
                END) / NULLIF(COUNT(ind.indicador), 0),
                3
            ) AS qualidaderesposta
        FROM indicadores ind
        JOIN modelos m ON m.id = ind.model_id
        JOIN metricas met ON met.id = ind.metrica_id
        WHERE met.tipo = 'TesteDoEmbed'
        GROUP BY m.id, m.name
        ORDER BY m.name
        """
    )
    return _rows(rows)


@router.get("/alucinacao")
async def hallucination_summary():
    rows = await database.fetch(
        """
        SELECT
            m.id AS modelo_id,
            m.name AS nome_modelo,
            r.tipo_resultado,
            COUNT(*) FILTER (WHERE r.erro) AS total_erro,
            COUNT(*) FILTER (
                WHERE r.tipo_resultado = 'CompreensaoTextual'
                  AND NOT regexp_replace(lower(trim(r.json_resultado->>'resposta')), '[^a-z0-9]', '', 'g')
                      IN ('contradio', 'implicao')
            ) AS total_alucinacao_compreensao,
            COUNT(*) FILTER (
                WHERE r.tipo_resultado = 'ClarezaResposta'
                  AND NOT lower(trim(r.json_resultado->>'resposta')) IN ('1', '2', '3', '4', '5')
            ) AS total_alucinacao_clareza
        FROM resultados r
        JOIN modelos m ON m.id = r.model_id
        GROUP BY m.id, m.name, r.tipo_resultado
        ORDER BY m.name, r.tipo_resultado
        """
    )
    return _rows(rows)


@router.get("/tabela")
async def consolidated_table():
    rows = await database.fetch(
        """
        WITH metric_scores AS (
            SELECT
                ind.model_id,
                met.tipo,
                CASE
                    WHEN met.tipo = 'TesteDoEmbed' THEN ROUND(SUM(CASE ind.indicador
                        WHEN 5 THEN 5.0 WHEN 4 THEN 4.0 WHEN 3 THEN 2.0
                        WHEN 6 THEN 2.5 WHEN 2 THEN 0.5 WHEN 1 THEN -2.0
                        WHEN 0 THEN -10.0 ELSE 0.0 END) / NULLIF(COUNT(*), 0), 3)
                    WHEN met.tipo IN ('CompreensaoTextual', 'ClarezaResposta') THEN
                        ROUND(AVG(ind.indicador)::NUMERIC / 100, 2)
                    ELSE ROUND(SUM(CASE ind.indicador
                        WHEN 1 THEN 1.0 WHEN 2 THEN 0.5 WHEN 0 THEN 0.0
                        WHEN 3 THEN -1.0 ELSE 0.0 END) / NULLIF(COUNT(*), 0), 2)
                END AS score
            FROM indicadores ind
            JOIN metricas met ON met.id = ind.metrica_id
            GROUP BY ind.model_id, met.tipo
        ),
        tokens AS (
            SELECT
                model_id,
                SUM(input_tokens)::FLOAT AS tokensentradas,
                SUM(output_tokens)::FLOAT AS tokensaida,
                SUM(total_tokens)::FLOAT AS tokenstotais
            FROM resultados
            GROUP BY model_id
        )
        SELECT
            m.id,
            m.name AS nome_modelo,
            MAX(score) FILTER (WHERE tipo = 'DireitoAdministrativo')::FLOAT AS direitometrica,
            MAX(score) FILTER (WHERE tipo = 'Matematica')::FLOAT AS matematica,
            MAX(score) FILTER (WHERE tipo = 'RaciocinioLogico')::FLOAT AS raciociniometrica,
            MAX(score) FILTER (WHERE tipo = 'CompreensaoTextual')::FLOAT AS compreensaotextualmetrica,
            MAX(score) FILTER (WHERE tipo = 'ClarezaResposta')::FLOAT AS clarezarespostametrica,
            MAX(score) FILTER (WHERE tipo = 'TesteDoEmbed')::FLOAT AS qualidaderesposta,
            MAX(score) FILTER (WHERE tipo = 'VibeCoding')::FLOAT AS vibecode,
            t.tokensentradas,
            t.tokensaida,
            t.tokenstotais
        FROM modelos m
        LEFT JOIN metric_scores ms ON ms.model_id = m.id
        LEFT JOIN tokens t ON t.model_id = m.id
        WHERE m.is_active = TRUE
        GROUP BY m.id, m.name, t.tokensentradas, t.tokensaida, t.tokenstotais
        ORDER BY m.name
        """
    )
    return _rows(rows)


@router.post("/processar-modelo")
async def process_model(body: ProcessModelRequest):
    if not body.ids:
        raise HTTPException(
            status_code=400,
            detail="Informe os modelos que devem ser processados.",
        )

    processed = []
    for model_id in body.ids:
        try:
            processed.append(await BenchmarkingService.run_model_once(model_id))
        except BenchmarkingAlreadyRegistered as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BenchmarkingNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return processed


@router.post("/processar-questao")
async def process_question(body: ProcessQuestionRequest):
    try:
        return await BenchmarkingService.process_question(body.questaoId, body.modeloId)
    except BenchmarkingAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except BenchmarkingNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/processar-resultado")
async def process_result(body: ProcessResultRequest):
    result = await BenchmarkingService.process_result(body.resultadoId)
    if result is None:
        raise HTTPException(status_code=404, detail="Resultado nao encontrado ou com erro.")
    return _plain(result)


@router.post("/trigger-start")
async def trigger_start():
    rows = await database.fetch(
        """
        SELECT m.provider, m.name AS modelo, mt.tipo AS metrica, q.id AS questao
        FROM modelos m
        CROSS JOIN banco_questoes q
        JOIN metricas mt ON mt.id = q.metrica_id
        WHERE m.is_active = TRUE
        ORDER BY m.provider, m.name, mt.tipo, q.id
        """
    )
    return {"success": True, "items": _rows(rows)}


@router.post("/test-vector-search")
async def vector_search(body: VectorSearchRequest):
    if not body.embedding:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Informe embedding no corpo da requisicao. "
                "A geracao automatica de embeddings do Nuxt ainda nao existe no backend Python."
            ),
        )

    vector_query = "[" + ",".join(str(value) for value in body.embedding) + "]"
    rows = await database.fetch(
        """
        SELECT
            id,
            content,
            metadata,
            1 - (embedding <=> $1::vector) AS similarity
        FROM cartas_servico
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT $2
        """,
        vector_query,
        body.limit,
    )
    return {"query": body.query, "results": _rows(rows)}


@router.post("/chat")
async def chat(_: ChatRequest):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Chat LLM depende de provedor/model adapter Python ainda nao configurado no portal.",
    )


@router.get("/test")
async def sandbox_test():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Sandbox Python do teste Vibe Coding ainda nao foi conectado ao runner seguro.",
    )


@router.websocket("/socket")
async def benchmark_socket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"user": "server", "message": "Welcome"})
    try:
        while True:
            message = await websocket.receive_text()
            if "ping" in message:
                await websocket.send_json({"user": "server", "message": "pong"})
            else:
                await websocket.send_json({"user": "client", "message": message})
    except WebSocketDisconnect:
        return
