
    -- ── Enriquecer categorias de prompts ──────────────────────────────────────
    ALTER TABLE prompt_categories
      ADD COLUMN IF NOT EXISTS icon        VARCHAR(50)  NOT NULL DEFAULT 'FileText',
      ADD COLUMN IF NOT EXISTS description TEXT         NOT NULL DEFAULT '',
      ADD COLUMN IF NOT EXISTS is_active   BOOLEAN      NOT NULL DEFAULT TRUE;

    UPDATE prompt_categories SET icon = 'FileSignature' WHERE slug = 'redacao-oficial';
    UPDATE prompt_categories SET icon = 'BarChart2'     WHERE slug = 'analise-dados';
    UPDATE prompt_categories SET icon = 'MessageCircle' WHERE slug = 'atendimento';
    UPDATE prompt_categories SET icon = 'Scale'         WHERE slug = 'juridico';
    UPDATE prompt_categories SET icon = 'BookOpen'      WHERE slug = 'resumo';
    UPDATE prompt_categories SET icon = 'Kanban'        WHERE slug = 'gestao';

    -- ── Campos de rating agregado em prompts ──────────────────────────────────
    ALTER TABLE prompts
      ADD COLUMN IF NOT EXISTS rating_avg   DECIMAL(3,2) NOT NULL DEFAULT 0,
      ADD COLUMN IF NOT EXISTS rating_count INTEGER      NOT NULL DEFAULT 0;

    -- ── Avaliações de prompts ─────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS prompt_reviews (
      id          UUID     PRIMARY KEY DEFAULT uuid_generate_v4(),
      prompt_id   UUID     NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
      user_id     UUID     NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
      rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
      comment     TEXT,
      used_before BOOLEAN  NOT NULL DEFAULT FALSE,
      is_approved BOOLEAN  NOT NULL DEFAULT TRUE,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE (prompt_id, user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_prompt_reviews_prompt   ON prompt_reviews(prompt_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_reviews_user     ON prompt_reviews(user_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_reviews_approved ON prompt_reviews(prompt_id, is_approved)
      WHERE is_approved = TRUE;

    -- Trigger: recalcula rating_avg e rating_count após cada avaliação
    CREATE OR REPLACE FUNCTION update_prompt_rating()
    RETURNS TRIGGER AS $$
    BEGIN
      UPDATE prompts SET
        rating_avg = (
          SELECT COALESCE(AVG(rating)::DECIMAL(3,2), 0)
          FROM prompt_reviews
          WHERE prompt_id = COALESCE(NEW.prompt_id, OLD.prompt_id)
            AND is_approved = TRUE
        ),
        rating_count = (
          SELECT COUNT(*)
          FROM prompt_reviews
          WHERE prompt_id = COALESCE(NEW.prompt_id, OLD.prompt_id)
            AND is_approved = TRUE
        )
      WHERE id = COALESCE(NEW.prompt_id, OLD.prompt_id);
      RETURN COALESCE(NEW, OLD);
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER prompt_reviews_rating
      AFTER INSERT OR UPDATE OR DELETE ON prompt_reviews
      FOR EACH ROW EXECUTE FUNCTION update_prompt_rating();

    -- ── Usos de prompts (cópia/uso) ───────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS prompt_usages (
      id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
      user_id   UUID NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
      used_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_prompt_usages_prompt      ON prompt_usages(prompt_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_usages_user        ON prompt_usages(user_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_usages_user_prompt ON prompt_usages(user_id, prompt_id);

    -- Trigger: incrementa usage_count ao registrar um uso
    CREATE OR REPLACE FUNCTION increment_prompt_usage_count()
    RETURNS TRIGGER AS $$
    BEGIN
      UPDATE prompts
      SET usage_count = usage_count + 1
      WHERE id = NEW.prompt_id;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER prompt_usage_count
      AFTER INSERT ON prompt_usages
      FOR EACH ROW EXECUTE FUNCTION increment_prompt_usage_count();
  