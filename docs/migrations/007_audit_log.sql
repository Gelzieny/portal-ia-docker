
    CREATE TABLE IF NOT EXISTS audit_logs (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
      action      VARCHAR(50) NOT NULL,   -- ex: "CREATE", "UPDATE", "DELETE", "LOGIN"
      entity      VARCHAR(100) NOT NULL,  -- ex: "ai_model", "prompt", "user"
      entity_id   UUID,
      metadata    JSONB,
      ip_address  INET,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_audit_logs_user   ON audit_logs(user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity, entity_id);
  