-- ============================================
-- Migración: Schema Bidireccional (Bora↔ES)
-- ============================================
-- Objetivo: Permitir almacenar diccionarios en ambas direcciones
-- - Bora→ES (existente en salida.json)
-- - ES→Bora (nuevo en salida_es_bora_final.json)
--
-- Cambios:
-- 1. Agregar columna 'direction' para identificar dirección
-- 2. Agregar columna 'gloss_bora' para traducciones ES→Bora
-- 3. Permitir NULL en gloss_es (solo para ES→Bora)
-- 4. Constraint: al menos uno de los dos gloss debe existir
--
-- Uso:
--   Ejecutar en Supabase SQL Editor
-- ============================================

-- ===== lexicon_lemmas =====

-- 1. Agregar columna de dirección
ALTER TABLE lexicon_lemmas
ADD COLUMN IF NOT EXISTS direction TEXT DEFAULT 'bora_es'
CHECK (direction IN ('bora_es', 'es_bora'));

-- 2. Agregar columna para traducción al Bora
ALTER TABLE lexicon_lemmas
ADD COLUMN IF NOT EXISTS gloss_bora TEXT;

-- 3. Permitir NULL en gloss_es (antes era NOT NULL)
ALTER TABLE lexicon_lemmas
ALTER COLUMN gloss_es DROP NOT NULL;

-- 4. Constraint: al menos uno de los dos debe existir
ALTER TABLE lexicon_lemmas
ADD CONSTRAINT IF NOT EXISTS check_has_gloss
CHECK (gloss_es IS NOT NULL OR gloss_bora IS NOT NULL);

-- 5. Índice para búsqueda por dirección
CREATE INDEX IF NOT EXISTS idx_lemmas_direction 
ON lexicon_lemmas(direction);

-- 6. Índice compuesto para búsquedas filtradas
CREATE INDEX IF NOT EXISTS idx_lemmas_direction_source 
ON lexicon_lemmas(direction, source);

COMMENT ON COLUMN lexicon_lemmas.direction IS 
'Dirección del diccionario: bora_es (Bora→Español) o es_bora (Español→Bora)';

COMMENT ON COLUMN lexicon_lemmas.gloss_bora IS 
'Traducción al Bora (solo para direction=es_bora). Puede tener múltiples valores separados por ";" en el JSON original, pero aquí se almacena UNA traducción por fila.';


-- ===== lexicon_subentries =====

-- 1. Agregar columna de dirección
ALTER TABLE lexicon_subentries
ADD COLUMN IF NOT EXISTS direction TEXT DEFAULT 'bora_es'
CHECK (direction IN ('bora_es', 'es_bora'));

-- 2. Agregar columna para traducción al Bora
ALTER TABLE lexicon_subentries
ADD COLUMN IF NOT EXISTS gloss_bora TEXT;

-- 3. Permitir NULL en gloss_es
ALTER TABLE lexicon_subentries
ALTER COLUMN gloss_es DROP NOT NULL;

-- 4. Constraint: al menos uno de los dos debe existir
ALTER TABLE lexicon_subentries
ADD CONSTRAINT IF NOT EXISTS check_has_gloss
CHECK (gloss_es IS NOT NULL OR gloss_bora IS NOT NULL);

-- 5. Índice para búsqueda por dirección
CREATE INDEX IF NOT EXISTS idx_subentries_direction 
ON lexicon_subentries(direction);

COMMENT ON COLUMN lexicon_subentries.direction IS 
'Dirección del diccionario: bora_es (Bora→Español) o es_bora (Español→Bora)';

COMMENT ON COLUMN lexicon_subentries.gloss_bora IS 
'Traducción al Bora (solo para direction=es_bora)';


-- ===== lexicon_examples =====

-- No necesita cambios estructurales, solo usaremos metadata en bora_docs
-- para distinguir la dirección del ejemplo


-- ===== Actualizar registros existentes =====

-- Marcar todos los registros existentes como 'bora_es' (default ya lo hace)
-- Esto es redundante pero explícito para claridad
UPDATE lexicon_lemmas 
SET direction = 'bora_es' 
WHERE direction IS NULL OR source = 'salida.json';

UPDATE lexicon_subentries 
SET direction = 'bora_es' 
WHERE direction IS NULL;


-- ===== Verificación =====

-- Contar registros por dirección
SELECT 
  direction,
  COUNT(*) as count,
  COUNT(DISTINCT source) as sources
FROM lexicon_lemmas
GROUP BY direction;

-- Verificar que no haya lemmas sin gloss
SELECT COUNT(*) as lemmas_sin_gloss
FROM lexicon_lemmas
WHERE gloss_es IS NULL AND gloss_bora IS NULL;
-- Resultado esperado: 0


-- ===== Rollback (si es necesario) =====
/*
-- Solo ejecutar si necesitas deshacer la migración

ALTER TABLE lexicon_lemmas DROP CONSTRAINT IF EXISTS check_has_gloss;
ALTER TABLE lexicon_lemmas DROP COLUMN IF EXISTS direction;
ALTER TABLE lexicon_lemmas DROP COLUMN IF EXISTS gloss_bora;
ALTER TABLE lexicon_lemmas ALTER COLUMN gloss_es SET NOT NULL;
DROP INDEX IF EXISTS idx_lemmas_direction;
DROP INDEX IF EXISTS idx_lemmas_direction_source;

ALTER TABLE lexicon_subentries DROP CONSTRAINT IF EXISTS check_has_gloss;
ALTER TABLE lexicon_subentries DROP COLUMN IF EXISTS direction;
ALTER TABLE lexicon_subentries DROP COLUMN IF EXISTS gloss_bora;
ALTER TABLE lexicon_subentries ALTER COLUMN gloss_es SET NOT NULL;
DROP INDEX IF EXISTS idx_subentries_direction;
*/


-- ============================================
-- ✅ Migración completada
-- ============================================
-- Próximo paso: Ejecutar script ingest_es_bora_docs.py
