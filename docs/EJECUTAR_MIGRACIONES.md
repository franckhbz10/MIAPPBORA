# 🚀 Guía de Ejecución de Migraciones SQL

## 📋 Instrucciones

**IMPORTANTE:** El cliente Python de Supabase no permite ejecutar SQL DDL directamente. Debes ejecutar estas migraciones manualmente en el SQL Editor de Supabase.

### Paso 1: Acceder al SQL Editor

1. Abre tu proyecto en Supabase Dashboard
2. Ve a: **SQL Editor** (menú lateral izquierdo)
3. Haz clic en **"New query"**

O accede directamente:
```
https://supabase.com/dashboard/project/TU_PROJECT_ID/sql/new
```

---

## 📄 MIGRACIÓN 001: Schema Bidireccional

**Archivo:** `docs/migrations/001_bidirectional_schema.sql`

### Copiar y Pegar en SQL Editor:

```sql
-- ============================================
-- Migración: Schema Bidireccional (Bora↔ES)
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
ADD CONSTRAINT check_has_gloss
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
'Traducción al Bora (solo para direction=es_bora)';


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

-- 4. Constraint: al menos uno debe existir
ALTER TABLE lexicon_subentries
ADD CONSTRAINT check_subentry_has_gloss
CHECK (gloss_es IS NOT NULL OR gloss_bora IS NOT NULL);

-- 5. Índice
CREATE INDEX IF NOT EXISTS idx_subentries_direction 
ON lexicon_subentries(direction);
```

### ✅ Verificación Migración 001:

Después de ejecutar, verifica con:

```sql
-- Verificar columnas creadas
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'lexicon_lemmas'
  AND column_name IN ('direction', 'gloss_bora');

-- Verificar datos existentes
SELECT direction, COUNT(*)
FROM lexicon_lemmas
GROUP BY direction;
-- Esperado: Todos con direction='bora_es' (default)
```

---

## 📄 MIGRACIÓN 002: match_bora_docs_v2 Bidireccional

**Archivo:** `docs/migrations/002_match_bora_docs_v2_bidirectional.sql`

### Copiar y Pegar en SQL Editor:

```sql
-- ============================================
-- Actualización: match_bora_docs_v2 Bidireccional
-- ============================================

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
  gloss_bora TEXT,      -- ✅ NUEVO
  direction TEXT,       -- ✅ NUEVO
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
    COALESCE(s.gloss_bora, l.gloss_bora) AS gloss_bora,  -- ✅ NUEVO
    l.direction,                                          -- ✅ NUEVO
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

-- Mantener permisos
GRANT EXECUTE ON FUNCTION match_bora_docs_v2(vector(1536), double precision, integer, text[], text)
  TO anon, authenticated, service_role;
```

### ✅ Verificación Migración 002:

```sql
-- Verificar que la función acepta los parámetros correctos
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_name = 'match_bora_docs_v2';
-- Esperado: 1 fila con routine_type='FUNCTION'
```

---

## 🎯 Checklist de Ejecución

### ☐ Migración 001
- [ ] Copiar SQL de migración 001
- [ ] Pegar en SQL Editor de Supabase
- [ ] Ejecutar con "Run" o Ctrl+Enter
- [ ] Verificar que no hay errores
- [ ] Ejecutar query de verificación
- [ ] Confirmar que `direction` y `gloss_bora` existen

### ☐ Migración 002
- [ ] Copiar SQL de migración 002
- [ ] Pegar en SQL Editor de Supabase
- [ ] Ejecutar con "Run" o Ctrl+Enter
- [ ] Verificar que no hay errores
- [ ] Ejecutar query de verificación

### ☐ Post-Migraciones
- [ ] Commit de cambios en código
- [ ] Test con subset: `python backend/scripts/ingest_es_bora_docs.py --path ../salida_es_bora_final.json --limit 100 --reset`
- [ ] Validar búsqueda bidireccional en frontend

---

## 🚨 Troubleshooting

### Error: "constraint already exists"
Si ya ejecutaste parcialmente las migraciones, algunos constraints pueden existir.
Usa `IF NOT EXISTS` o DROP antes de CREATE:

```sql
ALTER TABLE lexicon_lemmas DROP CONSTRAINT IF EXISTS check_has_gloss;
ALTER TABLE lexicon_lemmas ADD CONSTRAINT check_has_gloss 
CHECK (gloss_es IS NOT NULL OR gloss_bora IS NOT NULL);
```

### Error: "column already exists"
Las migraciones usan `IF NOT EXISTS`, así que deberían ser idempotentes.
Si da error, verifica que la columna no tenga otro tipo de dato:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='lexicon_lemmas' AND column_name='direction';
```

---

## 📞 Confirmación

Después de ejecutar ambas migraciones, responde:

1. ✅ ¿Migración 001 ejecutada sin errores?
2. ✅ ¿Migración 002 ejecutada sin errores?
3. ✅ ¿Queries de verificación retornan resultados esperados?

Si todo está OK, procedemos con el test de ingesta (--limit 100).
