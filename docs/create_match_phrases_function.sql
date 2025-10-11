-- ============================================================================
-- FUNCIÓN DE BÚSQUEDA VECTORIAL PARA MIAPPBORA
-- ============================================================================

-- Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear función de búsqueda de similitud
CREATE OR REPLACE FUNCTION match_phrases (
  query_embedding vector(384),
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
    1 - (pe.embedding <=> query_embedding) AS similarity
  FROM phrase_embeddings pe
  INNER JOIN bora_phrases bp ON pe.phrase_id = bp.id
  WHERE 
    (category_filter IS NULL OR bp.category = category_filter)
    AND (1 - (pe.embedding <=> query_embedding)) > match_threshold
  ORDER BY pe.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Crear índice HNSW para búsquedas rápidas
CREATE INDEX IF NOT EXISTS phrase_embeddings_embedding_idx 
ON phrase_embeddings 
USING hnsw (embedding vector_cosine_ops);

-- Verificar creación
SELECT 
  'Función creada exitosamente: ' || routine_name AS mensaje
FROM information_schema.routines 
WHERE routine_name = 'match_phrases';
