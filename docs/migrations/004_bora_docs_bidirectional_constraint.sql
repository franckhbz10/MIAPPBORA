-- ============================================================================
-- Migración: Modificar bora_docs_unique_idx para permitir documentos bidireccionales
-- ============================================================================
-- Problema:
--   El constraint actual solo verifica (kind, parent_lemma_id, subentry_id, example_id)
--   Esto impide tener DOS documentos para el mismo lemma con diferentes direcciones:
--     - Uno Bora→ES: "[LEMMA] majtsíva | DEF_ES: cantar"
--     - Uno ES→Bora: "[LEMMA_ES] cantar | DEF_BORA: majtsíva"
--
-- Solución:
--   Incluir `metadata->>'source'` en el constraint para diferenciar por fuente
--   (salida.json vs salida_es_bora_final.json)
--
-- Uso:
--   Ejecutar en Supabase SQL Editor
-- ============================================================================

-- 1. Dropar el constraint único actual
DROP INDEX IF EXISTS bora_docs_unique_idx;

-- 2. Crear nuevo constraint que incluya 'source' desde metadata
-- NOTA: Usamos (metadata->>'source') para extraer el campo 'source' del JSON
CREATE UNIQUE INDEX IF NOT EXISTS bora_docs_unique_idx_v2
ON bora_docs (
  kind,
  parent_lemma_id,
  COALESCE(subentry_id, -1),
  COALESCE(example_id, -1),
  (metadata->>'source')  -- ✨ NUEVO: Diferencia por source
);

COMMENT ON INDEX bora_docs_unique_idx_v2 IS 
'Constraint único que permite múltiples documentos para el mismo lemma/subentry/example 
si provienen de diferentes fuentes (salida.json vs salida_es_bora_final.json). 
Esto habilita el diccionario bidireccional donde un mismo lemma puede tener:
- Un documento Bora→ES (source=salida.json)
- Un documento ES→Bora (source=salida_es_bora_final.json)';
