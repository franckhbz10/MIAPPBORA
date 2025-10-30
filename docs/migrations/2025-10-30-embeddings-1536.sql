-- =============================================================================
-- MIAPPBORA — Migración a embeddings de 1536 dimensiones (OpenAI)
-- Crea columnas paralelas vector(1536), índices e introduce RPCs v2 que usan
-- las nuevas columnas. Mantiene las columnas de 384 para una migración segura.
-- =============================================================================

-- 0) Extensión vector
CREATE EXTENSION IF NOT EXISTS vector;

-- 1) Columnas nuevas para 1536 dims
-- Frases (phrase_embeddings)
ALTER TABLE phrase_embeddings
  ADD COLUMN IF NOT EXISTS embedding_1536 vector(1536);

-- Lexicón (lexicon_embeddings)
ALTER TABLE lexicon_embeddings
  ADD COLUMN IF NOT EXISTS embedding_1536 vector(1536);

-- (Opcional) Documentos unificados — si manejas otra tabla con embeddings
-- ALTER TABLE IF NOT EXISTS bora_docs
--   ADD COLUMN IF NOT EXISTS embedding_1536 vector(1536);

-- 2) Índices para 1536 (elige ivfflat u hnsw según tu preferencia/volumen)
-- HNSW (rápido para recall, buena opción general)
CREATE INDEX IF NOT EXISTS phrase_embeddings_embedding_1536_hnsw
  ON phrase_embeddings USING hnsw (embedding_1536 vector_cosine_ops);

CREATE INDEX IF NOT EXISTS lexicon_embeddings_embedding_1536_hnsw
  ON lexicon_embeddings USING hnsw (embedding_1536 vector_cosine_ops);

-- (Opcional) Para bora_docs
-- CREATE INDEX IF NOT EXISTS bora_docs_embedding_1536_hnsw
--   ON bora_docs USING hnsw (embedding_1536 vector_cosine_ops);

-- 3) RPCs v2 (1536)

-- 3.1) match_phrases_v2 — usa embedding_1536
CREATE OR REPLACE FUNCTION match_phrases_v2 (
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5,
  category_filter text DEFAULT NULL
)
RETURNS TABLE (
  id int,
  phrase_id int,
  bora_text text,
  spanish_translation text,
  category varchar(100),
  difficulty_level int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    pe.id,
    pe.phrase_id,
    bp.bora_text,
    bp.spanish_translation,
    bp.category,
    bp.difficulty_level,
    1 - (pe.embedding_1536 <=> query_embedding) AS similarity
  FROM phrase_embeddings pe
  INNER JOIN bora_phrases bp ON pe.phrase_id = bp.id
  WHERE 
    (category_filter IS NULL OR bp.category = category_filter)
    AND (1 - (pe.embedding_1536 <=> query_embedding)) > match_threshold
  ORDER BY pe.embedding_1536 <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 3.2) match_lexicon_v2 — usa embedding_1536
-- Ajusta nombres de columnas de lexicon_entries si difieren en tu esquema
CREATE OR REPLACE FUNCTION match_lexicon_v2 (
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5,
  category_filter text DEFAULT NULL
)
RETURNS TABLE (
  id int,
  entry_id int,
  bora_text text,
  spanish_text text,
  category text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    le.id,
    le.entry_id,
    e.bora_text,
    e.spanish_text,
    e.category,
    1 - (le.embedding_1536 <=> query_embedding) AS similarity
  FROM lexicon_embeddings le
  INNER JOIN lexicon_entries e ON le.entry_id = e.id
  WHERE 
    (category_filter IS NULL OR e.category = category_filter)
    AND (1 - (le.embedding_1536 <=> query_embedding)) > match_threshold
  ORDER BY le.embedding_1536 <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 3.3) (Opcional) match_bora_docs_v2 — si tienes una tabla bora_docs
-- con embedding_1536.
-- CREATE OR REPLACE FUNCTION match_bora_docs_v2 (
--   query_embedding vector(1536),
--   match_threshold float DEFAULT 0.5,
--   match_count int DEFAULT 10,
--   kind_filter text[] DEFAULT NULL,
--   pos_filter text DEFAULT NULL
-- )
-- RETURNS TABLE (... define campos relevantes ...)
-- LANGUAGE plpgsql AS $$
-- BEGIN
--   RETURN QUERY
--   SELECT ... , 1 - (bd.embedding_1536 <=> query_embedding) AS similarity
--   FROM bora_docs bd
--   WHERE (kind_filter IS NULL OR bd.kind = ANY(kind_filter))
--     AND (pos_filter IS NULL OR bd.pos_full = pos_filter)
--     AND (1 - (bd.embedding_1536 <=> query_embedding)) > match_threshold
--   ORDER BY bd.embedding_1536 <=> query_embedding
--   LIMIT match_count;
-- END; $$;

-- 4) Verificaciones rápidas
SELECT 'match_phrases_v2 creada' WHERE EXISTS (
  SELECT 1 FROM information_schema.routines WHERE routine_name = 'match_phrases_v2'
);

SELECT 'match_lexicon_v2 creada' WHERE EXISTS (
  SELECT 1 FROM information_schema.routines WHERE routine_name = 'match_lexicon_v2'
);
