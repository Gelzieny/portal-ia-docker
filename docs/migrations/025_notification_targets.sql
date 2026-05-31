
    CREATE TABLE IF NOT EXISTS notification_targets (
      notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
      user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (notification_id, user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_notification_targets_user ON notification_targets(user_id, notification_id);
  