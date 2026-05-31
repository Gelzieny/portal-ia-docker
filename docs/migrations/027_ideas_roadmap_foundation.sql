-- NO_TRANSACTION

    ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'gestor_produto';
  


    DO $$ BEGIN
    CREATE TYPE idea_moderation_status AS ENUM (
      'aguardando_curadoria',
      'publicada',
      'rejeitada',
      'exclusao_solicitada',
      'excluida'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    DO $$ BEGIN
    CREATE TYPE idea_status AS ENUM (
      'planejada',
      'em_desenvolvimento',
      'concluida'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    DO $$ BEGIN
    CREATE TYPE idea_comment_moderation_status AS ENUM (
      'publicado',
      'oculto'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    CREATE TABLE IF NOT EXISTS idea_topics (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      name        VARCHAR(120) NOT NULL UNIQUE,
      slug        VARCHAR(140) NOT NULL UNIQUE,
      color       VARCHAR(20) NOT NULL,
      icon        VARCHAR(80),
      description TEXT,
      sort_order  INTEGER NOT NULL DEFAULT 0,
      is_active   BOOLEAN NOT NULL DEFAULT TRUE,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS idea_versions (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      name        VARCHAR(120) NOT NULL UNIQUE,
      description TEXT,
      forecast    VARCHAR(80),
      sort_order  INTEGER NOT NULL DEFAULT 0,
      is_active   BOOLEAN NOT NULL DEFAULT TRUE,
      created_by  UUID REFERENCES users(id) ON DELETE SET NULL,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS ideas (
      id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      title                    VARCHAR(240) NOT NULL,
      description              TEXT NOT NULL,
      author_id                UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      moderation_status        idea_moderation_status NOT NULL DEFAULT 'aguardando_curadoria',
      idea_status              idea_status,
      version_id               UUID REFERENCES idea_versions(id) ON DELETE SET NULL,
      curation_notes           TEXT,
      rejection_reason         TEXT,
      deletion_requested_at    TIMESTAMPTZ,
      deletion_request_reason  TEXT,
      deleted_at               TIMESTAMPTZ,
      published_at             TIMESTAMPTZ,
      reviewed_by              UUID REFERENCES users(id) ON DELETE SET NULL,
      reviewed_at              TIMESTAMPTZ,
      created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT chk_ideas_roadmap_version_required
        CHECK (idea_status IS NULL OR version_id IS NOT NULL),
      CONSTRAINT chk_ideas_deleted_when_excluded
        CHECK (moderation_status <> 'excluida' OR deleted_at IS NOT NULL)
    );

    CREATE TABLE IF NOT EXISTS idea_topic_links (
      idea_id  UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
      topic_id UUID NOT NULL REFERENCES idea_topics(id) ON DELETE RESTRICT,
      PRIMARY KEY (idea_id, topic_id)
    );

    CREATE TABLE IF NOT EXISTS idea_votes (
      idea_id    UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
      user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (idea_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS idea_comments (
      id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      idea_id           UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
      parent_id         UUID REFERENCES idea_comments(id) ON DELETE CASCADE,
      author_id         UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      content           TEXT NOT NULL,
      moderation_status idea_comment_moderation_status NOT NULL DEFAULT 'publicado',
      moderation_reason TEXT,
      moderated_by      UUID REFERENCES users(id) ON DELETE SET NULL,
      moderated_at      TIMESTAMPTZ,
      created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS idea_comment_reactions (
      comment_id UUID NOT NULL REFERENCES idea_comments(id) ON DELETE CASCADE,
      user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      reaction   VARCHAR(40) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (comment_id, user_id)
    );

    DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_idea_comment_reaction_allowed'
          AND conrelid = 'idea_comment_reactions'::regclass
      ) THEN
        ALTER TABLE idea_comment_reactions
          ADD CONSTRAINT chk_idea_comment_reaction_allowed
          CHECK (reaction IN ('thumbs_up', 'heart', 'rocket', 'eyes', 'idea'));
      END IF;
    END $$;

    CREATE INDEX IF NOT EXISTS idx_idea_topics_active_sort
      ON idea_topics(is_active, sort_order, name);
    CREATE INDEX IF NOT EXISTS idx_idea_versions_active_sort
      ON idea_versions(is_active, sort_order, name);
    CREATE INDEX IF NOT EXISTS idx_ideas_moderation_created
      ON ideas(moderation_status, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_ideas_public
      ON ideas(published_at DESC)
      WHERE moderation_status = 'publicada';
    CREATE INDEX IF NOT EXISTS idx_ideas_status_version
      ON ideas(version_id, idea_status)
      WHERE idea_status IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_ideas_author_created
      ON ideas(author_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_ideas_title_trgm
      ON ideas USING GIN (title gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_ideas_description_trgm
      ON ideas USING GIN (description gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_idea_topic_links_topic
      ON idea_topic_links(topic_id, idea_id);
    CREATE INDEX IF NOT EXISTS idx_idea_votes_user
      ON idea_votes(user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_idea_comments_idea_parent
      ON idea_comments(idea_id, parent_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_idea_comment_reactions_user
      ON idea_comment_reactions(user_id, created_at DESC);

    DROP TRIGGER IF EXISTS idea_topics_updated_at ON idea_topics;
    CREATE TRIGGER idea_topics_updated_at
      BEFORE UPDATE ON idea_topics
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    DROP TRIGGER IF EXISTS idea_versions_updated_at ON idea_versions;
    CREATE TRIGGER idea_versions_updated_at
      BEFORE UPDATE ON idea_versions
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    DROP TRIGGER IF EXISTS ideas_updated_at ON ideas;
    CREATE TRIGGER ideas_updated_at
      BEFORE UPDATE ON ideas
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    DROP TRIGGER IF EXISTS idea_comments_updated_at ON idea_comments;
    CREATE TRIGGER idea_comments_updated_at
      BEFORE UPDATE ON idea_comments
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();

    CREATE OR REPLACE FUNCTION prevent_nested_idea_comment_replies()
    RETURNS TRIGGER AS $$
    DECLARE
      parent_parent_id UUID;
    BEGIN
      IF NEW.parent_id IS NULL THEN
        RETURN NEW;
      END IF;

      SELECT parent_id INTO parent_parent_id
      FROM idea_comments
      WHERE id = NEW.parent_id;

      IF parent_parent_id IS NOT NULL THEN
        RAISE EXCEPTION 'Idea comments support only one reply level';
      END IF;

      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS idea_comments_prevent_nested_replies ON idea_comments;
    CREATE TRIGGER idea_comments_prevent_nested_replies
      BEFORE INSERT OR UPDATE OF parent_id ON idea_comments
      FOR EACH ROW EXECUTE FUNCTION prevent_nested_idea_comment_replies();

    INSERT INTO idea_topics (name, slug, color, icon, description, sort_order)
    VALUES
      ('Modelos', 'modelos', '#2563eb', 'BrainCircuit', 'Modelos de IA e políticas de acesso', '10'),
      ('Prompts', 'prompts', '#d97706', 'Sparkles', 'Biblioteca, criacao e uso de prompts', '20'),
      ('MCP', 'mcp', '#7c3aed', 'Plug', 'Catálogo e operação de servidores MCP', '30'),
      ('Documentação', 'documentacao', '#0f766e', 'BookOpen', 'Documentação e base de conhecimento', '40'),
      ('Notícias', 'noticias', '#be123c', 'Newspaper', 'Comunicação e notícias da plataforma', '50'),
      ('Interface', 'interface', '#0284c7', 'PanelTop', 'Experiencia de uso e navegacao', '60'),
      ('Segurança', 'seguranca', '#b91c1c', 'ShieldCheck', 'Segurança, privacidade e auditoria', '70'),
      ('Integrações', 'integracoes', '#4f46e5', 'Workflow', 'Integrações com sistemas e ferramentas', '80'),
      ('Administração', 'administracao', '#475569', 'Settings', 'Governança administrativa da plataforma', '90'),
      ('Plataforma', 'plataforma', '#1a5e38', 'LayoutDashboard', 'Infraestrutura e recursos gerais', '100'),
      ('Governança', 'governanca', '#ca8a04', 'Scale', 'Regras, papéis, permissões e processos', '110'),
      ('Outra', 'outra', '#64748b', 'CircleHelp', 'Ideias que não se encaixam nos demais tópicos', '120')
    ON CONFLICT (slug) DO UPDATE SET
      name = EXCLUDED.name,
      color = EXCLUDED.color,
      icon = EXCLUDED.icon,
      description = EXCLUDED.description,
      sort_order = EXCLUDED.sort_order,
      updated_at = NOW();

    INSERT INTO app_features (key, name, area, description, menu_label, menu_path, sort_order)
    VALUES
      ('ideas.portal.view', 'Compartilhe sua Ideia', 'Ideias', 'Portal colaborativo de ideias', 'Compartilhe sua Ideia', '/ideias', '600'),
      ('ideas.create', 'Criar ideias', 'Ideias', 'Envio de novas ideias para curadoria', NULL, '/ideias/nova', '610'),
      ('ideas.vote', 'Votar em ideias', 'Ideias', 'Apoio positivo em ideias publicadas', NULL, '/ideias', '620'),
      ('ideas.comment', 'Comentar em ideias', 'Ideias', 'Comentários e respostas em ideias publicadas', NULL, '/ideias/:id', '630'),
      ('ideas.comment.react', 'Reagir a comentários', 'Ideias', 'Reações em comentários e respostas de ideias', NULL, '/ideias/:id', '640'),
      ('ideas.own.manage', 'Gerenciar próprias ideias', 'Ideias', 'Acompanhamento, edição e solicitação de exclusão das próprias ideias', 'Minhas Ideias', '/minhas-ideias', '650'),
      ('roadmap.view', 'Roadmap', 'Roadmap', 'Visualização pública do roadmap por versão', 'Roadmap', '/roadmap', '700'),
      ('ideas.curation.manage', 'Curadoria de ideias', 'Administração', 'Aprovação, rejeição e moderação de ideias', 'Curadoria de Ideias', '/admin/ideias', '1120'),
      ('ideas.roadmap.manage', 'Gerenciar status e roadmap', 'Administração', 'Gestão de status da ideia e versão de entrega', 'Roadmap', '/admin/roadmap', '1130'),
      ('admin.idea_versions.manage', 'Versões do Roadmap', 'Administração', 'Cadastro simples de versões do roadmap', 'Versões do Roadmap', '/admin/roadmap/versoes', '1140')
    ON CONFLICT (key) DO UPDATE SET
      name = EXCLUDED.name,
      area = EXCLUDED.area,
      description = EXCLUDED.description,
      menu_label = EXCLUDED.menu_label,
      menu_path = EXCLUDED.menu_path,
      sort_order = EXCLUDED.sort_order,
      is_active = TRUE,
      updated_at = NOW();

    INSERT INTO role_feature_permissions (role, feature_key, is_enabled)
    VALUES
      ('admin'::user_role, 'ideas.portal.view', true),
      ('admin'::user_role, 'ideas.create', true),
      ('admin'::user_role, 'ideas.vote', true),
      ('admin'::user_role, 'ideas.comment', true),
      ('admin'::user_role, 'ideas.comment.react', true),
      ('admin'::user_role, 'ideas.own.manage', true),
      ('admin'::user_role, 'roadmap.view', true),
      ('admin'::user_role, 'ideas.curation.manage', true),
      ('admin'::user_role, 'ideas.roadmap.manage', true),
      ('admin'::user_role, 'admin.idea_versions.manage', true),
      ('gestor_produto'::user_role, 'app.home.view', TRUE),
      ('gestor_produto'::user_role, 'models.catalog.view', TRUE),
      ('gestor_produto'::user_role, 'models.my_access.view', TRUE),
      ('gestor_produto'::user_role, 'prompts.library.view', TRUE),
      ('gestor_produto'::user_role, 'prompts.my.view', TRUE),
      ('gestor_produto'::user_role, 'mcp.catalog.view', TRUE),
      ('gestor_produto'::user_role, 'docs.portal.view', TRUE),
      ('gestor_produto'::user_role, 'news.portal.view', TRUE),
      ('gestor_produto'::user_role, 'ideas.portal.view', TRUE),
      ('gestor_produto'::user_role, 'ideas.create', TRUE),
      ('gestor_produto'::user_role, 'ideas.vote', TRUE),
      ('gestor_produto'::user_role, 'ideas.comment', TRUE),
      ('gestor_produto'::user_role, 'ideas.comment.react', TRUE),
      ('gestor_produto'::user_role, 'ideas.own.manage', TRUE),
      ('gestor_produto'::user_role, 'ideas.curation.manage', TRUE),
      ('gestor_produto'::user_role, 'ideas.roadmap.manage', TRUE),
      ('gestor_produto'::user_role, 'roadmap.view', TRUE),
      ('gestor_produto'::user_role, 'admin.idea_versions.manage', TRUE),
      ('gestor'::user_role, 'ideas.portal.view', true),
      ('gestor'::user_role, 'ideas.create', true),
      ('gestor'::user_role, 'ideas.vote', true),
      ('gestor'::user_role, 'ideas.comment', true),
      ('gestor'::user_role, 'ideas.comment.react', true),
      ('gestor'::user_role, 'ideas.own.manage', true),
      ('gestor'::user_role, 'roadmap.view', true),
      ('gestor'::user_role, 'ideas.curation.manage', false),
      ('gestor'::user_role, 'ideas.roadmap.manage', false),
      ('gestor'::user_role, 'admin.idea_versions.manage', false),
      ('curador'::user_role, 'ideas.portal.view', true),
      ('curador'::user_role, 'ideas.create', true),
      ('curador'::user_role, 'ideas.vote', true),
      ('curador'::user_role, 'ideas.comment', true),
      ('curador'::user_role, 'ideas.comment.react', true),
      ('curador'::user_role, 'ideas.own.manage', true),
      ('curador'::user_role, 'roadmap.view', true),
      ('curador'::user_role, 'ideas.curation.manage', false),
      ('curador'::user_role, 'ideas.roadmap.manage', false),
      ('curador'::user_role, 'admin.idea_versions.manage', false),
      ('curador_modelos'::user_role, 'ideas.portal.view', true),
      ('curador_modelos'::user_role, 'ideas.create', true),
      ('curador_modelos'::user_role, 'ideas.vote', true),
      ('curador_modelos'::user_role, 'ideas.comment', true),
      ('curador_modelos'::user_role, 'ideas.comment.react', true),
      ('curador_modelos'::user_role, 'ideas.own.manage', true),
      ('curador_modelos'::user_role, 'roadmap.view', true),
      ('curador_modelos'::user_role, 'ideas.curation.manage', false),
      ('curador_modelos'::user_role, 'ideas.roadmap.manage', false),
      ('curador_modelos'::user_role, 'admin.idea_versions.manage', false),
      ('servidor'::user_role, 'ideas.portal.view', true),
      ('servidor'::user_role, 'ideas.create', true),
      ('servidor'::user_role, 'ideas.vote', true),
      ('servidor'::user_role, 'ideas.comment', true),
      ('servidor'::user_role, 'ideas.comment.react', true),
      ('servidor'::user_role, 'ideas.own.manage', true),
      ('servidor'::user_role, 'roadmap.view', true),
      ('servidor'::user_role, 'ideas.curation.manage', false),
      ('servidor'::user_role, 'ideas.roadmap.manage', false),
      ('servidor'::user_role, 'admin.idea_versions.manage', false)
    ON CONFLICT (role, feature_key) DO UPDATE SET
      is_enabled = EXCLUDED.is_enabled,
      updated_at = NOW();
  
