-- Runs once when the PostgreSQL data volume is first initialized.
-- Django migrations also ensure this extension exists (apps/core/migrations).
CREATE EXTENSION IF NOT EXISTS vector;
