
    CREATE TABLE IF NOT EXISTS doc_sections (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      title       VARCHAR(200) NOT NULL,
      slug        VARCHAR(200) NOT NULL UNIQUE,
      sort_order  INTEGER NOT NULL DEFAULT 0,
      parent_id   UUID REFERENCES doc_sections(id) ON DELETE CASCADE,
      is_active   BOOLEAN NOT NULL DEFAULT TRUE
    );

    CREATE TABLE IF NOT EXISTS doc_articles (
      id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      section_id      UUID REFERENCES doc_sections(id) ON DELETE CASCADE,
      title           VARCHAR(300) NOT NULL,
      slug            VARCHAR(300) NOT NULL UNIQUE,
      content         TEXT NOT NULL DEFAULT '',
      reading_time    INTEGER NOT NULL DEFAULT 1,
      sort_order      INTEGER NOT NULL DEFAULT 0,
      author_id       UUID REFERENCES users(id) ON DELETE SET NULL,
      is_published    BOOLEAN NOT NULL DEFAULT FALSE,
      is_active       BOOLEAN NOT NULL DEFAULT TRUE,
      created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_doc_articles_section ON doc_articles(section_id);
    CREATE INDEX IF NOT EXISTS idx_doc_articles_slug ON doc_articles(slug);
    CREATE INDEX IF NOT EXISTS idx_doc_articles_search ON doc_articles USING gin(
      to_tsvector('portuguese', title || ' ' || content)
    );

    CREATE TRIGGER doc_articles_updated_at
      BEFORE UPDATE ON doc_articles
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
  