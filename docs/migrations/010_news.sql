
    DO $$ BEGIN
    CREATE TYPE news_category AS ENUM (
      'ATUALIZAÇÃO',
      'MANUTENÇÃO',
      'AVISO',
      'NOVO RECURSO',
      'SEGURANÇA'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    CREATE TABLE IF NOT EXISTS news (
      id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      category     news_category NOT NULL DEFAULT 'AVISO',
      title        VARCHAR(300) NOT NULL,
      summary      TEXT NOT NULL,
      content      TEXT NOT NULL DEFAULT '',
      link         VARCHAR(500),
      reading_time INTEGER NOT NULL DEFAULT 3,
      is_published BOOLEAN NOT NULL DEFAULT FALSE,
      published_at TIMESTAMPTZ,
      created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_news_published ON news(is_published, published_at DESC);
  