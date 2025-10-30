-- =============================================================================
-- MIAPPBORA — Bora Docs a 1536 dimensiones (OpenAI)
-- Añade columna paralela vector(1536) en bora_docs e implementa match_bora_docs_v2
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- 1) Columna 1536
ALTER TABLE bora_docs
  ADD COLUMN IF NOT EXISTS embedding_1536 vector(1536);

-- 2) Índice HNSW para 1536
CREATE INDEX IF NOT EXISTS bora_docs_embedding_1536_hnsw
  ON bora_docs USING hnsw (embedding_1536 vector_cosine_ops);

-- 3) RPC v2 (usa embedding_1536)
CREATE OR REPLACE FUNCTION match_bora_docs_v2 (
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10,
  kind_filter TEXT[] DEFAULT NULL,
  pos_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
  id BIGINT,
  kind TEXT,
  parent_lemma_id BIGINT,
  subentry_id BIGINT,
  example_id BIGINT,
  lemma TEXT,
  pos_full TEXT,
  bora_text TEXT,
  spanish_text TEXT,
  gloss_es TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.kind,
    d.parent_lemma_id,
    d.subentry_id,
    d.example_id,
    l.lemma,
    l.pos_full,
    e.bora_text,
    e.spanish_text,
    COALESCE(s.gloss_es, l.gloss_es) AS gloss_es,
    1 - (d.embedding_1536 <=> query_embedding) AS similarity
  FROM bora_docs d
  JOIN lexicon_lemmas l ON d.parent_lemma_id = l.id
  LEFT JOIN lexicon_subentries s ON d.subentry_id = s.id
  LEFT JOIN lexicon_examples e ON d.example_id = e.id
  WHERE (kind_filter IS NULL OR d.kind = ANY(kind_filter))
    AND (pos_filter IS NULL OR l.pos_full = pos_filter)
    AND (1 - (d.embedding_1536 <=> query_embedding)) > match_threshold
  ORDER BY d.embedding_1536 <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 4) Permisos de ejecución
GRANT EXECUTE ON FUNCTION match_bora_docs_v2(vector(1536), double precision, integer, text[], text)
  TO anon, authenticated, service_role;
