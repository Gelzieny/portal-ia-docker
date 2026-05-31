
    DO $$ BEGIN
    CREATE TYPE prompt_difficulty AS ENUM ('iniciante', 'intermediario', 'avancado');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    CREATE TABLE IF NOT EXISTS prompt_categories (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      name        VARCHAR(100) NOT NULL UNIQUE,
      slug        VARCHAR(100) NOT NULL UNIQUE,
      color       VARCHAR(20) NOT NULL DEFAULT '#1a5e38',
      sort_order  INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS prompts (
      id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      title           VARCHAR(300) NOT NULL,
      description     TEXT NOT NULL DEFAULT '',
      content         TEXT NOT NULL,
      category_id     UUID REFERENCES prompt_categories(id) ON DELETE SET NULL,
      model_id        UUID REFERENCES modelos(id) ON DELETE SET NULL,
      tags            TEXT[] NOT NULL DEFAULT '{}',
      difficulty      prompt_difficulty NOT NULL DEFAULT 'iniciante',
      usage_count     INTEGER NOT NULL DEFAULT 0,
      variables       JSONB NOT NULL DEFAULT '[]',
      author_id       UUID REFERENCES users(id) ON DELETE SET NULL,
      is_public       BOOLEAN NOT NULL DEFAULT TRUE,
      is_active       BOOLEAN NOT NULL DEFAULT TRUE,
      created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category_id);
    CREATE INDEX IF NOT EXISTS idx_prompts_difficulty ON prompts(difficulty);
    CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts USING gin(tags);
    CREATE INDEX IF NOT EXISTS idx_prompts_search ON prompts USING gin(
      to_tsvector('portuguese', title || ' ' || description)
    );

    CREATE TABLE IF NOT EXISTS prompt_favorites (
      user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
      prompt_id   UUID REFERENCES prompts(id) ON DELETE CASCADE,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (user_id, prompt_id)
    );

    CREATE TRIGGER prompts_updated_at
      BEFORE UPDATE ON prompts
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
