-- Hotfix: corrige tipos de retorno en RPCs v2 (INT → BIGINT)

-- Drop existentes
DROP FUNCTION IF EXISTS match_phrases_v2(vector(1536), double precision, integer, text);
DROP FUNCTION IF EXISTS match_lexicon_v2(vector(1536), double precision, integer, text);

CREATE OR REPLACE FUNCTION match_phrases_v2 (
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5,
  category_filter text DEFAULT NULL
)
RETURNS TABLE (
  id bigint,
  phrase_id bigint,
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

CREATE OR REPLACE FUNCTION match_lexicon_v2 (
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5,
  category_filter text DEFAULT NULL
)
RETURNS TABLE (
  id bigint,
  entry_id bigint,
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
