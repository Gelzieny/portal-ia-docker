
    ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'curador';
  



    -- Status de publicação
    DO $$ BEGIN
    CREATE TYPE prompt_publication_status AS ENUM (
      'rascunho',    -- sendo criado, incompleto
      'privado',     -- finalizado, só o criador vê
      'aguardando',  -- submetido para aprovação
      'publico',     -- aprovado e visível na galeria
      'em_revisao',  -- público mas sob investigação por denúncias
      'arquivado'    -- oculto, preservado
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    ALTER TABLE prompts
      -- status de publicação (substitui logicamente is_public)
      ADD COLUMN IF NOT EXISTS publication_status
          prompt_publication_status NOT NULL DEFAULT 'privado',

      -- origem do prompt
      ADD COLUMN IF NOT EXISTS source
          VARCHAR(20) NOT NULL DEFAULT 'oficial',
          -- 'oficial'    = criado pela equipe GO.IA (comportamento atual)
          -- 'comunidade' = criado por usuário servidor

      -- controle de aprovação
      ADD COLUMN IF NOT EXISTS submitted_at  TIMESTAMPTZ,
      ADD COLUMN IF NOT EXISTS reviewed_by   UUID REFERENCES users(id) ON DELETE SET NULL,
      ADD COLUMN IF NOT EXISTS reviewed_at   TIMESTAMPTZ,
      ADD COLUMN IF NOT EXISTS review_notes  TEXT,

      -- preserva nome do autor original caso a conta seja desativada
      ADD COLUMN IF NOT EXISTS original_author_name VARCHAR(200),

      -- contagem de denúncias ativas (atualizada por trigger)
      ADD COLUMN IF NOT EXISTS report_count  INTEGER NOT NULL DEFAULT 0,

      -- versão atual (incrementa a cada aprovação)
      ADD COLUMN IF NOT EXISTS version       INTEGER NOT NULL DEFAULT 1;

    -- Migrar dados existentes: todos os prompts atuais são 'oficiais'
    UPDATE prompts SET
      source = 'oficial',
      publication_status = CASE
        WHEN is_public = TRUE AND is_active = TRUE THEN 'publico'::prompt_publication_status
        WHEN is_active = FALSE                     THEN 'arquivado'::prompt_publication_status
        ELSE                                            'privado'::prompt_publication_status
      END;

    -- Índices para queries comuns
    CREATE INDEX IF NOT EXISTS idx_prompts_publication_status
        ON prompts(publication_status);

    CREATE INDEX IF NOT EXISTS idx_prompts_source
        ON prompts(source);

    CREATE INDEX IF NOT EXISTS idx_prompts_author_source
        ON prompts(author_id, source);

    CREATE INDEX IF NOT EXISTS idx_prompts_awaiting
        ON prompts(publication_status, submitted_at)
        WHERE publication_status = 'aguardando';

    CREATE INDEX IF NOT EXISTS idx_prompts_in_review
        ON prompts(publication_status, report_count)
        WHERE publication_status = 'em_revisao';


    -- ── 3. Histórico de versões ──────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS prompt_versions (
      id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
      prompt_id      UUID        NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
      version_number INTEGER     NOT NULL,
      -- snapshot do conteúdo no momento da aprovação
      title          VARCHAR(300) NOT NULL,
      description    TEXT         NOT NULL DEFAULT '',
      content        TEXT         NOT NULL,
      variables      JSONB        NOT NULL DEFAULT '[]',
      tags           TEXT[]       NOT NULL DEFAULT '{}',
      -- quem aprovou esta versão
      approved_by    UUID         REFERENCES users(id) ON DELETE SET NULL,
      approved_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
      UNIQUE (prompt_id, version_number)
    );

    CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt
        ON prompt_versions(prompt_id, version_number DESC);


    -- ── 4. Denúncias de prompts ──────────────────────────────────────────────
    DO $$ BEGIN
    CREATE TYPE report_reason AS ENUM (
      'conteudo_inapropriado',  -- ofensivo, discriminatório
      'informacao_incorreta',   -- dado falso ou desatualizado
      'violacao_lgpd',          -- expõe dados pessoais
      'uso_indevido',           -- fora do contexto governamental
      'duplicado',              -- já existe prompt similar
      'outro'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    DO $$ BEGIN
    CREATE TYPE report_status AS ENUM (
      'pendente',    -- aguardando análise
      'analisado',   -- curador/admin tomou decisão
      'descartado'   -- denúncia inválida
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    CREATE TABLE IF NOT EXISTS prompt_reports (
      id               UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
      prompt_id        UUID          NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
      reporter_id      UUID          NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
      reason           report_reason NOT NULL,
      description      TEXT,                       -- detalhamento opcional
      status           report_status NOT NULL DEFAULT 'pendente',
      resolved_by      UUID          REFERENCES users(id) ON DELETE SET NULL,
      resolved_at      TIMESTAMPTZ,
      resolution_notes TEXT,
      created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
      UNIQUE (prompt_id, reporter_id)   -- um usuário, uma denúncia por prompt
    );

    CREATE INDEX IF NOT EXISTS idx_prompt_reports_prompt
        ON prompt_reports(prompt_id);

    CREATE INDEX IF NOT EXISTS idx_prompt_reports_pending
        ON prompt_reports(status)
        WHERE status = 'pendente';

    CREATE INDEX IF NOT EXISTS idx_prompt_reports_reporter
        ON prompt_reports(reporter_id);

    -- Trigger: atualizar report_count e mover para em_revisao se >= 3 denúncias
    CREATE OR REPLACE FUNCTION handle_prompt_report()
    RETURNS TRIGGER AS $$
    DECLARE
      v_count     INTEGER;
      v_threshold INTEGER := 3;
    BEGIN
      SELECT COUNT(*) INTO v_count
      FROM prompt_reports
      WHERE prompt_id = NEW.prompt_id
        AND status = 'pendente';

      UPDATE prompts
      SET report_count = v_count
      WHERE id = NEW.prompt_id;

      -- Atingiu threshold e está público → move para em_revisao
      IF v_count >= v_threshold THEN
        UPDATE prompts
        SET publication_status = 'em_revisao'
        WHERE id = NEW.prompt_id
          AND publication_status = 'publico';
      END IF;

      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER prompt_report_handler
      AFTER INSERT OR UPDATE ON prompt_reports
      FOR EACH ROW EXECUTE FUNCTION handle_prompt_report();


    -- ── 5. Forks de prompts (sugestão de melhoria) ──────────────────────────
    CREATE TABLE IF NOT EXISTS prompt_forks (
      id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
      original_id  UUID        NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
      fork_id      UUID        NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
      fork_message TEXT,
      created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE (original_id, fork_id)
    );

    CREATE INDEX IF NOT EXISTS idx_prompt_forks_original ON prompt_forks(original_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_forks_fork     ON prompt_forks(fork_id);


    -- ── 6. Trigger: desativação de usuário ──────────────────────────────────
    CREATE OR REPLACE FUNCTION handle_user_deactivation()
    RETURNS TRIGGER AS $$
    BEGIN
      -- Só age quando is_active muda de TRUE para FALSE
      IF OLD.is_active = TRUE AND NEW.is_active = FALSE THEN

        -- Preservar nome do autor em prompts públicos/em moderação
        UPDATE prompts
        SET original_author_name = OLD.name
        WHERE author_id = OLD.id
          AND source = 'comunidade'
          AND publication_status IN ('publico', 'em_revisao', 'aguardando')
          AND original_author_name IS NULL;

        -- Arquivar rascunhos e privados do usuário desativado
        UPDATE prompts
        SET publication_status = 'arquivado',
            is_active = FALSE
        WHERE author_id = OLD.id
          AND source = 'comunidade'
          AND publication_status IN ('privado', 'rascunho');

      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS user_deactivation_handler ON users;
    CREATE TRIGGER user_deactivation_handler
      AFTER UPDATE OF is_active ON users
      FOR EACH ROW EXECUTE FUNCTION handle_user_deactivation();

  