
    ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'curador_modelos';



    ALTER TABLE modelos
      ADD COLUMN IF NOT EXISTS requires_access_approval BOOLEAN NOT NULL DEFAULT FALSE,
      ADD COLUMN IF NOT EXISTS access_summary TEXT NOT NULL DEFAULT '',
      ADD COLUMN IF NOT EXISTS access_documentation TEXT NOT NULL DEFAULT '',
      ADD COLUMN IF NOT EXISTS default_endpoint_base VARCHAR(500),
      ADD COLUMN IF NOT EXISTS default_auth_scheme VARCHAR(50) NOT NULL DEFAULT 'api_key';

    DO $$ BEGIN
    CREATE TYPE model_access_request_status AS ENUM (
      'pendente',
      'aprovado',
      'negado',
      'revogacao_solicitada',
      'revogado',
      'cancelado'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    CREATE TABLE IF NOT EXISTS model_access_requests (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      model_id UUID NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      application_name VARCHAR(200) NOT NULL,
      status model_access_request_status NOT NULL DEFAULT 'pendente',
      justification TEXT NOT NULL,
      intended_use TEXT,
      request_context JSONB NOT NULL DEFAULT '{}',
      reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
      reviewed_at TIMESTAMPTZ,
      review_notes TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_model_access_requests_model
      ON model_access_requests(model_id);
    CREATE INDEX IF NOT EXISTS idx_model_access_requests_user
      ON model_access_requests(user_id);
    CREATE INDEX IF NOT EXISTS idx_model_access_requests_application_name
      ON model_access_requests(application_name);
    CREATE INDEX IF NOT EXISTS idx_model_access_requests_status
      ON model_access_requests(status);
    CREATE INDEX IF NOT EXISTS idx_model_access_requests_pending
      ON model_access_requests(status, created_at)
      WHERE status = 'pendente';

    CREATE UNIQUE INDEX IF NOT EXISTS uq_model_access_requests_active_application_name
      ON model_access_requests(model_id, user_id, LOWER(BTRIM(application_name)))
      WHERE status IN ('pendente', 'aprovado', 'revogacao_solicitada');

    CREATE TABLE IF NOT EXISTS model_access_credentials (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      request_id UUID UNIQUE NOT NULL REFERENCES model_access_requests(id) ON DELETE CASCADE,
      endpoint_base VARCHAR(500) NOT NULL,
      access_key_encrypted TEXT NOT NULL,
      access_secret_encrypted TEXT NOT NULL,
      public_headers JSONB NOT NULL DEFAULT '{}',
      usage_notes TEXT NOT NULL DEFAULT '',
      is_active BOOLEAN NOT NULL DEFAULT TRUE,
      created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TRIGGER model_access_requests_updated_at
      BEFORE UPDATE ON model_access_requests
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();

    CREATE TRIGGER model_access_credentials_updated_at
      BEFORE UPDATE ON model_access_credentials
      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
