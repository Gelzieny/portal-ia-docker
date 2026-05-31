
    -- Categorias de MCP Servers
    CREATE TABLE IF NOT EXISTS mcp_categories (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      name        VARCHAR(100) NOT NULL UNIQUE,
      slug        VARCHAR(100) NOT NULL UNIQUE,
      description TEXT NOT NULL DEFAULT '',
      icon        VARCHAR(50) NOT NULL DEFAULT 'Plug',
      color       VARCHAR(20) NOT NULL DEFAULT '#1a5e38',
      sort_order  INTEGER NOT NULL DEFAULT 0,
      is_active   BOOLEAN NOT NULL DEFAULT TRUE
    );

    -- Status do servidor MCP
    DO $$ BEGIN
    CREATE TYPE mcp_server_status AS ENUM (
      'disponivel',
      'beta',
      'experimental',
      'descontinuado'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    -- Tipo de cliente MCP
    DO $$ BEGIN
    CREATE TYPE mcp_client_type AS ENUM (
      'claude_desktop',
      'vscode',
      'cursor',
      'terminal',
      'custom'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    -- Servidores MCP
    CREATE TABLE IF NOT EXISTS mcp_servers (
      id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      name            VARCHAR(200) NOT NULL,
      slug            VARCHAR(200) NOT NULL UNIQUE,
      tagline         VARCHAR(300) NOT NULL DEFAULT '',
      description     TEXT NOT NULL DEFAULT '',
      category_id     UUID REFERENCES mcp_categories(id) ON DELETE SET NULL,
      status          mcp_server_status NOT NULL DEFAULT 'experimental',
      is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
      is_featured     BOOLEAN NOT NULL DEFAULT FALSE,
      is_official     BOOLEAN NOT NULL DEFAULT FALSE,
      repository_url  VARCHAR(500),
      docs_url        VARCHAR(500),
      homepage_url    VARCHAR(500),
      version         VARCHAR(50),
      license         VARCHAR(100),
      compatible_models TEXT[] NOT NULL DEFAULT '{}',
      rating_avg      DECIMAL(3,2) NOT NULL DEFAULT 0,
      rating_count    INTEGER NOT NULL DEFAULT 0,
      install_count   INTEGER NOT NULL DEFAULT 0,
      author_name     VARCHAR(200),
      author_org      VARCHAR(200),
      submitted_by    UUID REFERENCES users(id) ON DELETE SET NULL,
      tags            TEXT[] NOT NULL DEFAULT '{}',
      sort_order      INTEGER NOT NULL DEFAULT 0,
      is_active       BOOLEAN NOT NULL DEFAULT TRUE,
      created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_mcp_servers_category ON mcp_servers(category_id);
    CREATE INDEX IF NOT EXISTS idx_mcp_servers_status   ON mcp_servers(status);
    CREATE INDEX IF NOT EXISTS idx_mcp_servers_slug     ON mcp_servers(slug);
    CREATE INDEX IF NOT EXISTS idx_mcp_servers_featured ON mcp_servers(is_featured);
    CREATE INDEX IF NOT EXISTS idx_mcp_servers_tags     ON mcp_servers USING gin(tags);
    CREATE INDEX IF NOT EXISTS idx_mcp_servers_search   ON mcp_servers USING gin(
      to_tsvector('portuguese', name || ' ' || tagline || ' ' || description)
    );

    CREATE TRIGGER mcp_servers_updated_at
      BEFORE UPDATE ON mcp_servers
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();

    -- Tools expostas pelo servidor
    CREATE TABLE IF NOT EXISTS mcp_tools (
      id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      server_id     UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
      name          VARCHAR(200) NOT NULL,
      description   TEXT NOT NULL DEFAULT '',
      parameters    JSONB NOT NULL DEFAULT '[]',
      return_type   VARCHAR(100),
      example_call  TEXT,
      sort_order    INTEGER NOT NULL DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_mcp_tools_server ON mcp_tools(server_id);

    -- Agents pré-configurados que usam o servidor
    CREATE TABLE IF NOT EXISTS mcp_agents (
      id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      server_id     UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
      name          VARCHAR(200) NOT NULL,
      description   TEXT NOT NULL DEFAULT '',
      capabilities  TEXT[] NOT NULL DEFAULT '{}',
      base_model    VARCHAR(200),
      system_prompt TEXT,
      sort_order    INTEGER NOT NULL DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_mcp_agents_server ON mcp_agents(server_id);

    -- Resources (fontes de dados) expostos pelo servidor
    CREATE TABLE IF NOT EXISTS mcp_resources (
      id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      server_id     UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
      name          VARCHAR(200) NOT NULL,
      uri_template  VARCHAR(500) NOT NULL,
      description   TEXT NOT NULL DEFAULT '',
      mime_type     VARCHAR(100),
      sort_order    INTEGER NOT NULL DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_mcp_resources_server ON mcp_resources(server_id);

    -- Snippets de configuração por cliente
    CREATE TABLE IF NOT EXISTS mcp_config_snippets (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      server_id   UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
      client_type mcp_client_type NOT NULL,
      label       VARCHAR(100) NOT NULL,
      config_json TEXT NOT NULL,
      notes       TEXT,
      sort_order  INTEGER NOT NULL DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_mcp_snippets_server ON mcp_config_snippets(server_id);

    -- Avaliações de usuários
    CREATE TABLE IF NOT EXISTS mcp_reviews (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      server_id   UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
      user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
      comment     TEXT,
      is_approved BOOLEAN NOT NULL DEFAULT TRUE,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE (server_id, user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_mcp_reviews_server ON mcp_reviews(server_id);

    -- Trigger para recalcular rating_avg e rating_count
    CREATE OR REPLACE FUNCTION update_mcp_server_rating()
    RETURNS TRIGGER AS $$
    BEGIN
      UPDATE mcp_servers SET
        rating_avg = (
          SELECT COALESCE(AVG(rating), 0)
          FROM mcp_reviews
          WHERE server_id = COALESCE(NEW.server_id, OLD.server_id)
            AND is_approved = TRUE
        ),
        rating_count = (
          SELECT COUNT(*)
          FROM mcp_reviews
          WHERE server_id = COALESCE(NEW.server_id, OLD.server_id)
            AND is_approved = TRUE
        )
      WHERE id = COALESCE(NEW.server_id, OLD.server_id);
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER mcp_reviews_rating
      AFTER INSERT OR UPDATE OR DELETE ON mcp_reviews
      FOR EACH ROW EXECUTE FUNCTION update_mcp_server_rating();

    -- Instalações por usuário
    CREATE TABLE IF NOT EXISTS mcp_installations (
      id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      server_id    UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
      user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      client_type  mcp_client_type,
      installed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE (server_id, user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_mcp_installations_server ON mcp_installations(server_id);
    CREATE INDEX IF NOT EXISTS idx_mcp_installations_user   ON mcp_installations(user_id);

    -- Trigger para incrementar install_count
    CREATE OR REPLACE FUNCTION update_mcp_install_count()
    RETURNS TRIGGER AS $$
    BEGIN
      IF TG_OP = 'INSERT' THEN
        UPDATE mcp_servers SET install_count = install_count + 1
        WHERE id = NEW.server_id;
      ELSIF TG_OP = 'DELETE' THEN
        UPDATE mcp_servers SET install_count = GREATEST(install_count - 1, 0)
        WHERE id = OLD.server_id;
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER mcp_installations_count
      AFTER INSERT OR DELETE ON mcp_installations
      FOR EACH ROW EXECUTE FUNCTION update_mcp_install_count();

    -- Favoritos
    CREATE TABLE IF NOT EXISTS mcp_favorites (
      user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
      server_id  UUID REFERENCES mcp_servers(id) ON DELETE CASCADE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (user_id, server_id)
    );
  