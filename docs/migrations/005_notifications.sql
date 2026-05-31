
    DO $$ BEGIN
    CREATE TYPE notification_type AS ENUM ('info', 'warning', 'success', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

    CREATE TABLE IF NOT EXISTS notifications (
      id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      type        notification_type NOT NULL DEFAULT 'info',
      title       VARCHAR(300) NOT NULL,
      message     TEXT NOT NULL,
      link        VARCHAR(500),
      is_global   BOOLEAN NOT NULL DEFAULT TRUE,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      expires_at  TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS notification_reads (
      user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
      notification_id UUID REFERENCES notifications(id) ON DELETE CASCADE,
      read_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (user_id, notification_id)
    );

    CREATE INDEX IF NOT EXISTS idx_notifications_global ON notifications(is_global, created_at DESC);
  