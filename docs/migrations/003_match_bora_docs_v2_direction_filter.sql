-- =============================================================================
-- MIAPPBORA — match_bora_docs_v2 con filtro opcional por dirección
-- =============================================================================
-- 
-- PROPÓSITO:
--   Añadir parámetro direction_filter a match_bora_docs_v2 para filtrar
--   búsquedas por dirección específica (Bora→ES o ES→Bora)
--
-- USO:
--   - direction_filter = 'es_bora': Solo busca traducciones ES→Bora
--   - direction_filter = 'bora_es': Solo busca traducciones Bora→ES
--   - direction_filter = NULL: Busca en ambas direcciones (default)
--
-- PROBLEMA QUE RESUELVE:
--   Cuando se pregunta "Como se dice cantar en bora", se necesita buscar
--   solo en ES→Bora para evitar que resultados Bora→ES dominen por cantidad.
--
-- DEBE EJECUTARSE DESPUÉS DE: 002_match_bora_docs_v2_bidirectional.sql
-- =============================================================================

-- Reemplazar función existente añadiendo direction_filter
CREATE OR REPLACE FUNCTION match_bora_docs_v2 (
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10,
  kind_filter TEXT[] DEFAULT NULL,
  pos_filter TEXT DEFAULT NULL,
  direction_filter TEXT DEFAULT NULL  -- ✅ NUEVO: 'es_bora', 'bora_es', o NULL
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
  gloss_bora TEXT,
  direction TEXT,
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
    COALESCE(s.gloss_bora, l.gloss_bora) AS gloss_bora,
    l.direction,
    1 - (d.embedding_1536 <=> query_embedding) AS similarity
  FROM bora_docs d
  JOIN lexicon_lemmas l ON d.parent_lemma_id = l.id
  LEFT JOIN lexicon_subentries s ON d.subentry_id = s.id
  LEFT JOIN lexicon_examples e ON d.example_id = e.id
  WHERE (kind_filter IS NULL OR d.kind = ANY(kind_filter))
    AND (pos_filter IS NULL OR l.pos_full = pos_filter)
    AND (direction_filter IS NULL OR l.direction = direction_filter)  -- ✅ NUEVO FILTRO
    AND (1 - (d.embedding_1536 <=> query_embedding)) > match_threshold
  ORDER BY d.embedding_1536 <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Actualizar permisos (ahora con 6 parámetros)
GRANT EXECUTE ON FUNCTION match_bora_docs_v2(vector(1536), double precision, integer, text[], text, text)
  TO anon, authenticated, service_role;

-- =============================================================================
-- TESTS DE VERIFICACIÓN
-- =============================================================================
-- Test 1: Buscar solo ES→Bora (español a Bora)
-- SELECT lemma, gloss_bora, direction, similarity
-- FROM match_bora_docs_v2(
--   (SELECT embedding_1536 FROM bora_docs WHERE id = 1),  -- embedding de prueba
--   0.5,  -- threshold
--   10,   -- limit
--   NULL, -- kind_filter
--   NULL, -- pos_filter
--   'es_bora'  -- solo ES→Bora
-- );
--
-- Test 2: Buscar solo Bora→ES (Bora a español)
-- SELECT lemma, gloss_es, direction, similarity
-- FROM match_bora_docs_v2(
--   (SELECT embedding_1536 FROM bora_docs WHERE id = 1),
--   0.5, 10, NULL, NULL, 'bora_es'  -- solo Bora→ES
-- );
--
-- Test 3: Buscar en ambas direcciones (default)
-- SELECT lemma, gloss_es, gloss_bora, direction, similarity
-- FROM match_bora_docs_v2(
--   (SELECT embedding_1536 FROM bora_docs WHERE id = 1),
--   0.5, 10, NULL, NULL, NULL  -- ambas direcciones
-- );
-- =============================================================================
