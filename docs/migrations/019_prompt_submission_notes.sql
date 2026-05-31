
    ALTER TABLE prompts
      ADD COLUMN IF NOT EXISTS submission_notes TEXT;

    UPDATE prompts
    SET submission_notes = review_notes
    WHERE submission_notes IS NULL
      AND submitted_at IS NOT NULL
      AND reviewed_at IS NULL
      AND publication_status IN ('aguardando', 'em_revisao');
  