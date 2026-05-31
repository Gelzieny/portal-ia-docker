CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

DO $$ BEGIN
    CREATE TYPE benchmark_tipo_metrica AS ENUM (
        'CompreensaoTextual',
        'ClarezaResposta',
        'TesteDoEmbed',
        'DireitoAdministrativo',
        'Matematica',
        'RaciocinioLogico',
        'VibeCoding'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS metricas (
    id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metricas  TEXT NOT NULL,
    tipo      benchmark_tipo_metrica NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS banco_questoes (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metrica_id UUID NOT NULL REFERENCES metricas(id) ON DELETE CASCADE,
    pergunta   JSONB NOT NULL,
    gabarito   JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_banco_questoes_metrica ON banco_questoes(metrica_id);

CREATE TABLE IF NOT EXISTS indicadores (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    indicador  INTEGER NOT NULL,
    model_id   UUID NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
    metrica_id UUID NOT NULL REFERENCES metricas(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_indicadores_modelo_metrica
    ON indicadores(model_id, metrica_id);

CREATE TABLE IF NOT EXISTS resultados (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tipo_resultado    benchmark_tipo_metrica NOT NULL,
    json_resultado    JSONB NOT NULL DEFAULT '{}'::jsonb,
    erro              BOOLEAN NOT NULL DEFAULT FALSE,
    json_erro         JSONB,
    id_banco_questoes UUID NOT NULL REFERENCES banco_questoes(id) ON DELETE CASCADE,
    model_id          UUID NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
    input_tokens      INTEGER NOT NULL DEFAULT 0,
    output_tokens     INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_resultados_banco_modelo
    ON resultados(id_banco_questoes, model_id);

CREATE INDEX IF NOT EXISTS idx_resultados_tipo ON resultados(tipo_resultado);
CREATE INDEX IF NOT EXISTS idx_resultados_modelo ON resultados(model_id);

CREATE TABLE IF NOT EXISTS cartas_servico (
    id        TEXT PRIMARY KEY,
    content   TEXT NOT NULL,
    metadata  JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1536)
);

CREATE INDEX IF NOT EXISTS idx_cartas_servico_embedding
    ON cartas_servico USING hnsw (embedding vector_cosine_ops);
