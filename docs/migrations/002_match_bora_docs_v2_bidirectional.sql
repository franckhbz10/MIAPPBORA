-- =============================================================================
-- MIAPPBORA — Actualización de match_bora_docs_v2 para soporte bidireccional
-- =============================================================================
-- 
-- PROPÓSITO:
--   Modificar match_bora_docs_v2 para que retorne gloss_bora y direction
--   además de gloss_es, permitiendo que búsquedas funcionen con ambas
--   direcciones del diccionario (Bora→ES y ES→Bora)
--
-- CAMBIOS:
--   - Añadir columna gloss_bora al RETURNS TABLE
--   - Añadir columna direction al RETURNS TABLE  
--   - Modificar SELECT para incluir COALESCE de gloss_bora
--   - Modificar SELECT para incluir direction
--
-- DEBE EJECUTARSE DESPUÉS DE: 001_bidirectional_schema.sql
-- =============================================================================

-- 1. Eliminar función existente (necesario cuando cambia el tipo de retorno)
DROP FUNCTION IF EXISTS match_bora_docs_v2(vector(1536), double precision, integer, text[], text);

-- 2. Crear función con soporte bidireccional
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
  gloss_bora TEXT,      -- ✅ NUEVO: Traducción al Bora (ES→Bora)
  direction TEXT,       -- ✅ NUEVO: Dirección del diccionario
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
    -- gloss_es: Para ES→Bora usar lemma, para Bora→ES usar gloss_es
    CASE 
      WHEN l.direction = 'es_bora' THEN COALESCE(s.gloss_es, l.lemma)
      ELSE COALESCE(s.gloss_es, l.gloss_es)
    END AS gloss_es,
    -- gloss_bora: Para ES→Bora usar gloss_bora, para Bora→ES usar lemma
    CASE
      WHEN l.direction = 'bora_es' THEN COALESCE(s.gloss_bora, l.lemma)
      ELSE COALESCE(s.gloss_bora, l.gloss_bora)
    END AS gloss_bora,
    -- direction: 'bora_es' o 'es_bora'
    l.direction,
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

-- Mantener permisos existentes
GRANT EXECUTE ON FUNCTION match_bora_docs_v2(vector(1536), double precision, integer, text[], text)
  TO anon, authenticated, service_role;

-- =============================================================================
-- VERIFICACIÓN
-- =============================================================================
-- Verificar que la función retorna las columnas correctas:
-- 
-- SELECT 
--   column_name, 
--   data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'match_bora_docs_v2';
--
-- =============================================================================
-- ROLLBACK (si es necesario)
-- =============================================================================
-- Para revertir a la versión anterior (sin gloss_bora/direction):
-- 
-- CREATE OR REPLACE FUNCTION match_bora_docs_v2 (
--   query_embedding VECTOR(1536),
--   match_threshold FLOAT DEFAULT 0.5,
--   match_count INT DEFAULT 10,
--   kind_filter TEXT[] DEFAULT NULL,
--   pos_filter TEXT DEFAULT NULL
-- )
-- RETURNS TABLE (
--   id BIGINT,
--   kind TEXT,
--   parent_lemma_id BIGINT,
--   subentry_id BIGINT,
--   example_id BIGINT,
--   lemma TEXT,
--   pos_full TEXT,
--   bora_text TEXT,
--   spanish_text TEXT,
--   gloss_es TEXT,
--   similarity FLOAT
-- )
-- LANGUAGE plpgsql
-- SECURITY DEFINER
-- SET search_path = public, pg_temp
-- AS $$
-- BEGIN
--   RETURN QUERY
--   SELECT
--     d.id,
--     d.kind,
--     d.parent_lemma_id,
--     d.subentry_id,
--     d.example_id,
--     l.lemma,
--     l.pos_full,
--     e.bora_text,
--     e.spanish_text,
--     COALESCE(s.gloss_es, l.gloss_es) AS gloss_es,
--     1 - (d.embedding_1536 <=> query_embedding) AS similarity
--   FROM bora_docs d
--   JOIN lexicon_lemmas l ON d.parent_lemma_id = l.id
--   LEFT JOIN lexicon_subentries s ON d.subentry_id = s.id
--   LEFT JOIN lexicon_examples e ON d.example_id = e.id
--   WHERE (kind_filter IS NULL OR d.kind = ANY(kind_filter))
--     AND (pos_filter IS NULL OR l.pos_full = pos_filter)
--     AND (1 - (d.embedding_1536 <=> query_embedding)) > match_threshold
--   ORDER BY d.embedding_1536 <=> query_embedding
--   LIMIT match_count;
-- END;
-- $$;
