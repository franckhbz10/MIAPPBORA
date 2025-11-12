# 🔄 Fix: Búsqueda Bidireccional Bora↔ES

## 📋 Problema Identificado

Al agregar el diccionario ES→Bora, el código de búsqueda NO estaba preparado para manejar ambas direcciones:

### ❌ Problemas Detectados:

1. **`find_lemma_by_text()` solo retornaba `gloss_es`**
   - Documentos ES→Bora tienen `gloss_es=NULL` y `gloss_bora` con valor
   - Query solo recuperaba columnas de dirección Bora→ES

2. **`match_bora_docs_v2` SQL solo retornaba `gloss_es`**
   - Función PostgreSQL no incluía columnas `gloss_bora` ni `direction`
   - Imposible diferenciar entre Bora→ES y ES→Bora en resultados

3. **Contexto RAG solo mostraba `DEF_ES:`**
   - Para documentos ES→Bora mostraría vacío: `DEF_ES: `
   - No había lógica para elegir traducción según dirección

## ✅ Solución Implementada

### 1. **Actualización de `supabase_adapter.py`**

**Archivo:** `backend/adapters/supabase_adapter.py`

```python
# ANTES (línea 502):
.select('id, lemma, gloss_es, pos, pos_full, page')

# DESPUÉS:
.select('id, lemma, gloss_es, gloss_bora, direction, pos, pos_full, page')
```

**Impacto:** `find_lemma_by_text()` ahora retorna todos los campos necesarios para búsqueda bidireccional.

---

### 2. **Nueva Migración SQL: `002_match_bora_docs_v2_bidirectional.sql`**

**Archivo:** `docs/migrations/002_match_bora_docs_v2_bidirectional.sql`

**Cambios en la función PostgreSQL:**

```sql
-- ANTES:
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
  gloss_es TEXT,           -- ❌ Solo gloss_es
  similarity FLOAT
)

-- DESPUÉS:
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
  gloss_es TEXT,           -- ✅ Para Bora→ES
  gloss_bora TEXT,         -- ✅ Para ES→Bora (NUEVO)
  direction TEXT,          -- ✅ 'bora_es' | 'es_bora' (NUEVO)
  similarity FLOAT
)
```

**SELECT actualizado:**

```sql
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
  COALESCE(s.gloss_es, l.gloss_es) AS gloss_es,         -- NULL para ES→Bora
  COALESCE(s.gloss_bora, l.gloss_bora) AS gloss_bora,   -- ✅ NUEVO
  l.direction,                                           -- ✅ NUEVO
  1 - (d.embedding_1536 <=> query_embedding) AS similarity
FROM bora_docs d
JOIN lexicon_lemmas l ON d.parent_lemma_id = l.id
-- ...resto igual
```

---

### 3. **Actualización de `rag_service.py`**

**Archivo:** `backend/services/rag_service.py`

#### 3.1. Boost de Lemma Exacto (líneas ~255-280)

```python
# ANTES:
boosted = {
    'id': -1,
    'kind': 'lemma',
    'parent_lemma_id': lemma_row['id'],
    'lemma': lemma_row['lemma'],
    'pos_full': lemma_row.get('pos_full'),
    'gloss_es': lemma_row['gloss_es'],  # ❌ Siempre gloss_es
    'similarity': 1.0,
}

# DESPUÉS:
direction = lemma_row.get('direction', 'bora_es')
translation = (
    lemma_row.get('gloss_bora') if direction == 'es_bora' 
    else lemma_row.get('gloss_es')
)

boosted = {
    'id': -1,
    'kind': 'lemma',
    'parent_lemma_id': lemma_row['id'],
    'lemma': lemma_row['lemma'],
    'pos_full': lemma_row.get('pos_full'),
    'gloss_es': lemma_row.get('gloss_es'),      # ✅ Ambos campos
    'gloss_bora': lemma_row.get('gloss_bora'),  # ✅ Ambos campos
    'direction': direction,
    'translation': translation,  # ✅ Helper con traducción correcta
    'similarity': 1.0,
}
```

#### 3.2. Agrupación de Resultados (líneas ~283-300)

```python
# ANTES:
g = groups.setdefault(lemma, {
    'lemma': lemma,
    'pos_full': h.get('pos_full'),
    'gloss_es': h.get('gloss_es'),  # ❌ Solo gloss_es
    'best_similarity': h.get('similarity', 0.0),
    'items': [],
    'examples': [],
})

# DESPUÉS:
direction = h.get('direction', 'bora_es')
translation = (
    h.get('gloss_bora') if direction == 'es_bora'
    else h.get('gloss_es')
)

g = groups.setdefault(lemma, {
    'lemma': lemma,
    'pos_full': h.get('pos_full'),
    'gloss_es': h.get('gloss_es'),      # ✅ Ambos campos
    'gloss_bora': h.get('gloss_bora'),  # ✅ Ambos campos
    'direction': direction,
    'translation': translation,  # ✅ Helper field
    'best_similarity': h.get('similarity', 0.0),
    'items': [],
    'examples': [],
})
```

#### 3.3. Construcción del Contexto (líneas ~333-350)

```python
# ANTES:
for i, g in enumerate(ordered, 1):
    sim = g['best_similarity']
    line = f"{i}. [Lemma | sim {sim:.2f}] {g['lemma']} — DEF_ES: {g.get('gloss_es') or ''} — POS: {g.get('pos_full') or ''}"
    context_lines.append(line)

# DESPUÉS:
for i, g in enumerate(ordered, 1):
    sim = g['best_similarity']
    direction = g.get('direction', 'bora_es')
    translation = g.get('translation') or ''
    
    # Formato adaptado según dirección
    if direction == 'es_bora':
        # ES→Bora: lemma es español, traducción es Bora
        line = f"{i}. [Lemma ES→Bora | sim {sim:.2f}] {g['lemma']} — DEF_BORA: {translation} — POS: {g.get('pos_full') or ''}"
    else:
        # Bora→ES: lemma es Bora, traducción es español (default)
        line = f"{i}. [Lemma | sim {sim:.2f}] {g['lemma']} — DEF_ES: {translation} — POS: {g.get('pos_full') or ''}"
    
    context_lines.append(line)
```

---

## 🎯 Resultado Esperado

### Ejemplo de Contexto ANTES del Fix:

```
[CONTEXTO (no lo repitas en la respuesta)]
1. [Lemma | sim 0.95] casa — DEF_ES:  — POS: sustantivo
   • Ejemplo: BORA: "kátyi" — ES: "casa"
```
❌ **Problema:** `DEF_ES:` vacío para documentos ES→Bora

### Ejemplo de Contexto DESPUÉS del Fix:

```
[CONTEXTO (no lo repitas en la respuesta)]
1. [Lemma ES→Bora | sim 0.95] casa — DEF_BORA: kátyi — POS: masculino
   • Ejemplo: BORA: "kátyi" — ES: "casa"
2. [Lemma | sim 0.92] aábukɨ — DEF_ES: sol — POS: sustantivo
   • Ejemplo: BORA: "aábukɨ túbe" — ES: "brilla el sol"
```
✅ **Solución:** Muestra la traducción correcta según dirección del diccionario

---

## 📝 Orden de Ejecución

### 1. Migraciones SQL en Supabase (en orden):

```sql
-- Paso 1: Agregar columnas bidireccionales
\i docs/migrations/001_bidirectional_schema.sql

-- Paso 2: Actualizar función match_bora_docs_v2
\i docs/migrations/002_match_bora_docs_v2_bidirectional.sql
```

### 2. Verificación:

```sql
-- Verificar que columnas existen
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'lexicon_lemmas'
  AND column_name IN ('direction', 'gloss_bora');

-- Verificar datos existentes marcados como 'bora_es'
SELECT direction, COUNT(*)
FROM lexicon_lemmas
GROUP BY direction;
```

### 3. Deploy del Backend:

```bash
# Los cambios en supabase_adapter.py y rag_service.py
# ya están listos para deploy
git add backend/adapters/supabase_adapter.py
git add backend/services/rag_service.py
git add docs/migrations/*.sql
git commit -m "feat: soporte bidireccional Bora↔ES en búsqueda"
git push
```

---

## ✅ Validación

### Tests Manuales Post-Deploy:

1. **Query Bora→ES** (existente):
   - Input: `"como se dice aábukɨ en español"`
   - Esperado: Contexto muestra `[Lemma | sim X.XX] aábukɨ — DEF_ES: sol`

2. **Query ES→Bora** (nuevo):
   - Input: `"como se dice casa en bora"`
   - Esperado: Contexto muestra `[Lemma ES→Bora | sim X.XX] casa — DEF_BORA: kátyi`

3. **Query Mixta**:
   - Input: `"palabras sobre familia"`
   - Esperado: Resultados de AMBOS diccionarios con formato correcto

---

## 🚀 Estado Actual

- ✅ **Código actualizado** (supabase_adapter.py, rag_service.py)
- ✅ **Migraciones SQL creadas** (001, 002)
- ⚠️ **Pendiente:** Ejecutar migraciones en Supabase
- ⚠️ **Pendiente:** Testing con subset (--limit 100)
- ⚠️ **Pendiente:** Ingesta completa ES→Bora

---

## 📚 Referencias

- **Schema Design:** `docs/ANALISIS_INGESTA_ES_BORA.md`
- **Script Ingesta:** `backend/scripts/ingest_es_bora_docs.py`
- **Estadísticas:** `backend/scripts/analyze_es_bora_json.py`

---

**Fecha:** 2025-11-10  
**Issue Reportado por:** @franckhbz10  
**Fix Implementado por:** GitHub Copilot
