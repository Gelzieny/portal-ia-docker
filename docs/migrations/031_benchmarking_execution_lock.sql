DO $$ BEGIN
    CREATE TYPE benchmarking_run_status AS ENUM (
        'pending',
        'running',
        'completed',
        'failed'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS benchmarking_runs (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id     UUID NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
    status       benchmarking_run_status NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error        TEXT,

    CONSTRAINT uq_benchmarking_runs_model UNIQUE (model_id)
);

CREATE INDEX IF NOT EXISTS idx_benchmarking_runs_status
    ON benchmarking_runs(status);
