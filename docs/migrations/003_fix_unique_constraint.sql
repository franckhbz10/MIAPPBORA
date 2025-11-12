-- =============================================================================
-- MIGRACIÓN 003: Ajustar Constraint Único para Lemmas Bidireccionales
-- =============================================================================
-- 
-- PROBLEMA:
--   El constraint único actual es (lemma, source), lo que impide tener
--   el mismo lemma en ambas direcciones.
--   
--   Ejemplo: "a" existe en Bora→ES y en ES→Bora, ambos con source diferente
--   pero el constraint actual lo trata como duplicado.
--
-- SOLUCIÓN:
--   Cambiar constraint de (lemma, source) a (lemma, source, direction)
--   Esto permite el mismo lemma si tiene diferente dirección.
--
-- DEBE EJECUTARSE DESPUÉS DE: 001_bidirectional_schema.sql
-- =============================================================================

-- 1. Eliminar constraint antiguo
ALTER TABLE lexicon_lemmas 
DROP CONSTRAINT IF EXISTS lexicon_lemmas_lemma_source_key;

-- 2. Crear nuevo constraint que incluya direction
ALTER TABLE lexicon_lemmas 
ADD CONSTRAINT lexicon_lemmas_lemma_source_direction_key 
UNIQUE (lemma, source, direction);

-- Comentario explicativo
COMMENT ON CONSTRAINT lexicon_lemmas_lemma_source_direction_key ON lexicon_lemmas IS 
'Permite el mismo lemma en diferentes direcciones (bora_es vs es_bora) incluso con diferente source';

-- =============================================================================
-- VERIFICACIÓN
-- =============================================================================
-- Ver constraints actuales:
-- 
-- SELECT constraint_name, constraint_type 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'lexicon_lemmas' AND constraint_type = 'UNIQUE';
--
-- =============================================================================
-- ROLLBACK (si es necesario)
-- =============================================================================
-- Para revertir:
--
-- ALTER TABLE lexicon_lemmas 
-- DROP CONSTRAINT IF EXISTS lexicon_lemmas_lemma_source_direction_key;
--
-- ALTER TABLE lexicon_lemmas 
-- ADD CONSTRAINT lexicon_lemmas_lemma_source_key 
-- UNIQUE (lemma, source);
-- =============================================================================
