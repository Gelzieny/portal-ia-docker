
    DO $$ BEGIN
    CREATE TYPE model_status AS ENUM ('disponivel', 'beta', 'manutencao');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
    DO $$ BEGIN
    CREATE TYPE model_category AS ENUM ('texto', 'codigo', 'visao', 'multimodal', 'embeddings');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    CREATE TABLE IF NOT EXISTS modelos (
      id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      name            VARCHAR(200) NOT NULL,
      slug            VARCHAR(200) NOT NULL UNIQUE,
      provider        VARCHAR(100) NOT NULL,
      category        model_category NOT NULL,
      description     TEXT NOT NULL DEFAULT '',
      capabilities    TEXT[] NOT NULL DEFAULT '{}',
      status          model_status NOT NULL DEFAULT 'disponivel',
      context_window  INTEGER,
      usage_limit     VARCHAR(200),
      tags            TEXT[] NOT NULL DEFAULT '{}',
      is_new          BOOLEAN NOT NULL DEFAULT FALSE,
      is_featured     BOOLEAN NOT NULL DEFAULT FALSE,
      is_active       BOOLEAN NOT NULL DEFAULT TRUE,
      sort_order      INTEGER NOT NULL DEFAULT 0,
      created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_modelos_status ON modelos(status);
    CREATE INDEX IF NOT EXISTS idx_modelos_category ON modelos(category);
    CREATE INDEX IF NOT EXISTS idx_modelos_slug ON modelos(slug);

    CREATE TRIGGER modelos_updated_at
      BEFORE UPDATE ON modelos
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
