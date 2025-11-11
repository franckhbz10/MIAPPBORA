# 📊 Lógica de Ingesta de `salida.json` a Base de Datos Vectorial

## 🎯 Objetivo
Explicar cómo se procesa el archivo `salida.json` (lexicón Bora-Español) para poblar la base de datos Supabase con embeddings vectoriales para búsqueda semántica.

---

## 📁 Archivo Fuente: `salida.json`

### Estructura Original del JSON
```json
[
  {
    "lemma": "aábukɨ",
    "gloss_es": "sol",
    "pos": "s",
    "pos_full": "sustantivo",
    "page": 1,
    "variants": ["aábukɨɨ"],
    "raw": "...",
    "examples": [
      {
        "bora": "Aábukɨ tsaallé",
        "es": "El sol brilla"
      }
    ],
    "subentries": [
      {
        "sublemma": "aábukɨ tsúúhne",
        "gloss_es": "mediodía",
        "pos": "loc",
        "examples": [...]
      }
    ]
  },
  ...
]
```

---

## 🔄 Pipeline de Ingesta

### Script Principal: `ingest_bora_docs.py`

```bash
python backend/scripts/ingest_bora_docs.py \
  --path ../salida.json \
  --batch-size 400 \
  --embed-batch-size 64 \
  --reset
```

---

## 📊 Tablas de Destino en Supabase

### 1. **`lexicon_lemmas`** (Palabras base)
- **Qué se guarda**: Cada palabra/lemma única del diccionario
- **Información extraída**:
  ```python
  {
    'lemma': e.get('lemma'),              # Palabra en Bora (ej: "aábukɨ")
    'gloss_es': e.get('gloss_es'),        # Definición en español (ej: "sol")
    'pos': e.get('pos'),                   # Part of speech (ej: "s" = sustantivo)
    'pos_full': e.get('pos_full'),        # Categoría completa (ej: "sustantivo")
    'page': e.get('page'),                 # Página del diccionario original
    'variants': e.get('variants'),         # Variantes ortográficas
    'raw': e.get('raw'),                   # Texto crudo original
    'source': 'salida.json'
  }
  ```

### 2. **`lexicon_subentries`** (Subentradas/frases derivadas)
- **Qué se guarda**: Frases compuestas o acepciones adicionales
- **Información extraída**:
  ```python
  {
    'lemma_id': lemma_id,                  # FK al lemma padre
    'sublemma': sub.get('sublemma'),       # Frase derivada (ej: "aábukɨ tsúúhne")
    'gloss_es': sub.get('gloss_es'),       # Traducción (ej: "mediodía")
    'pos': sub.get('pos'),                 # Categoría gramatical
    'page': sub.get('page'),
    'variants': sub.get('variants'),
    'raw': sub.get('raw')
  }
  ```

### 3. **`lexicon_examples`** (Ejemplos de uso)
- **Qué se guarda**: Pares de oraciones Bora-Español
- **Información extraída**:
  ```python
  {
    'lemma_id': lemma_id,                  # FK al lemma
    'subentry_id': subentry_id,            # FK a subentrada (si aplica)
    'bora_text': ex.get('bora'),           # Oración en Bora
    'spanish_text': ex.get('es'),          # Traducción al español
    'category': pos_full or pos,           # Categoría gramatical
    'page': page,
    'source': 'salida.json'
  }
  ```

### 4. **`bora_docs`** (Documentos para búsqueda vectorial)
- **Qué se guarda**: Textos estructurados para generar embeddings
- **3 tipos de documentos**:

#### **Tipo 1: LEMMA** (Definiciones de palabras)
```python
# Formato del texto:
"[LEMMA] {palabra} | DEF_ES: {definición} | POS: {categoría} | PAG: {página}"

# Ejemplo real:
"[LEMMA] aábukɨ | DEF_ES: sol | POS: sustantivo | PAG: 1"
```

#### **Tipo 2: SUBENTRY** (Frases compuestas)
```python
# Formato del texto:
"[SUBLEMMA] {frase} | DEF_ES: {definición} | POS: {categoría} | PAG: {página}"

# Ejemplo real:
"[SUBLEMMA] aábukɨ tsúúhne | DEF_ES: mediodía | POS: locución | PAG: 1"
```

#### **Tipo 3: EXAMPLE** (Oraciones completas)
```python
# Formato del texto:
"BORA: {oración_bora} [SEP] ES: {oración_español} [SEP] LEMMA: {palabra_base} POS: {categoría}"

# Ejemplo real:
"BORA: Aábukɨ tsaallé [SEP] ES: El sol brilla [SEP] LEMMA: aábukɨ POS: sustantivo"
```

---

## 🧮 Generación de Embeddings Vectoriales

### Modelo Usado: OpenAI `text-embedding-3-small`
- **Dimensionalidad**: 1536 dimensiones
- **API**: OpenAI Embeddings API
- **Configuración**: `USE_EMBEDDING_API=true` en `.env`

### Proceso de Vectorización

```python
# 1. Para cada documento en bora_docs, se genera su embedding:
texts = [
    "[LEMMA] aábukɨ | DEF_ES: sol | POS: sustantivo | PAG: 1",
    "BORA: Aábukɨ tsaallé [SEP] ES: El sol brilla [SEP] LEMMA: aábukɨ POS: sustantivo",
    ...
]

# 2. Llamada a OpenAI en batches de 64:
embeddings = openai.embeddings.create(
    model="text-embedding-3-small",
    input=texts
)

# 3. Se guarda el vector de 1536 dimensiones:
{
  'doc_id': doc_id,
  'embedding_1536': [0.023, -0.145, 0.678, ...],  # 1536 floats
  'model': 'text-embedding-3-small',
  'created_at': datetime.now()
}
```

---

## 📋 Información que SÍ se Almacena

### ✅ **Datos Incluidos**:
1. **Lemmas (palabras base)**:
   - Palabra en Bora (`lemma`)
   - Definición en español (`gloss_es`)
   - Categoría gramatical (`pos`, `pos_full`)
   - Página del diccionario (`page`)
   - Variantes ortográficas (`variants`)

2. **Subentries (frases derivadas)**:
   - Frase completa en Bora (`sublemma`)
   - Traducción al español (`gloss_es`)
   - Categoría gramatical
   - Relación con lemma padre

3. **Examples (oraciones de ejemplo)**:
   - Oración en Bora (`bora_text`)
   - Traducción al español (`spanish_text`)
   - Relación con lemma/subentry
   - Categoría contextual

4. **Embeddings vectoriales** (para búsqueda semántica):
   - Vector de 1536 dimensiones para cada documento
   - Metadata completa del lemma/ejemplo

---

## ❌ Información que NO se Almacena / Se Omite

### 🚫 **Datos Excluidos**:

1. **Campos sin valor (`None`, `""`, `[]`)**:
   ```python
   # Si gloss_es está vacío, se descarta esa entrada:
   if not lemma or not gloss:
       continue  # ❌ No se guarda
   ```

2. **Duplicados exactos**:
   ```python
   # Se valida unicidad con claves compuestas:
   key = (lemma, 'salida.json')
   if key in seen:
       continue  # ❌ Ya existe, se omite
   ```

3. **Ejemplos sin par completo Bora-Español**:
   ```python
   bora = ex.get('bora').strip()
   es = ex.get('es').strip()
   if not (bora and es):
       continue  # ❌ Si falta uno de los dos, se omite
   ```

4. **Sinónimos** (fuera de alcance):
   ```python
   'synonyms': None  # ❌ Campo reservado pero no usado
   ```

5. **Información redundante en `raw`**:
   - Se guarda el campo `raw` completo
   - Pero NO se usa para embeddings (solo los campos estructurados)

6. **Metadata adicional del JSON original** que no esté en el schema:
   - Solo se extraen los campos definidos explícitamente
   - Campos custom del JSON se ignoran

---

## 📊 Estadísticas Típicas de Ingesta

Basado en un corpus promedio de `salida.json`:

```
📄 Entradas en JSON: 2,450
📝 Lemmas únicos: 2,180
📑 Subentradas: 450
💬 Ejemplos totales: 3,200
🎯 Documentos con embeddings (bora_docs): ~5,830
   - Lemmas: 2,180
   - Subentries: 450
   - Examples: 3,200
```

---

## 🔍 Búsqueda Semántica (Cómo se Usa)

### Query del Usuario:
```python
query = "¿Cómo digo hola en Bora?"
```

### Proceso:
1. **Generar embedding de la query** (1536 dims con OpenAI):
   ```python
   query_embedding = openai.embeddings.create(
       model="text-embedding-3-small",
       input=query
   )
   ```

2. **Buscar en Supabase con pgvector**:
   ```sql
   SELECT 
     bd.content,
     bd.metadata,
     bd.embedding_1536 <=> query_vector AS distance
   FROM bora_docs bd
   WHERE bd.embedding_1536 IS NOT NULL
   ORDER BY bd.embedding_1536 <=> query_vector
   LIMIT 5;
   ```

3. **Resultados ordenados por similitud**:
   ```
   1. "[LEMMA] kóhtsapa | DEF_ES: hola, buenos días | POS: interjección"
   2. "BORA: Kóhtsapa, ¿kóje tsaa? [SEP] ES: Hola, ¿cómo estás?"
   3. "[SUBLEMMA] kóhtsapa ímɨɨné | DEF_ES: buenos días"
   ...
   ```

---

## 🛠️ Scripts de Mantenimiento

### Backfill de Embeddings (Migración a 1536 dims)
```bash
# Para actualizar embeddings existentes a OpenAI 1536:
python backend/scripts/backfill_embeddings_1536.py \
  --target lexicon \
  --batch 64 \
  --limit 0
```

### Validación de Integridad
```bash
# Verificar que todos los ejemplos tengan embeddings:
SELECT COUNT(*) 
FROM lexicon_examples le 
LEFT JOIN bora_docs bd ON bd.example_id = le.id
WHERE bd.id IS NULL;
```

---

## 📌 Puntos Clave

1. **Deduplicación**: Se evitan registros duplicados con claves compuestas
2. **Validación**: Solo se guardan entradas con datos completos y válidos
3. **Embeddings contextuales**: Cada tipo de documento tiene formato específico
4. **Búsqueda semántica**: Usa similitud coseno en espacio vectorial de 1536 dims
5. **Escalabilidad**: Procesamiento en batches (64-400 registros)
6. **Trazabilidad**: Campo `source` siempre registra origen (`salida.json`)

---

## 🔗 Referencias

- **Script principal**: `backend/scripts/ingest_bora_docs.py`
- **Backfill embeddings**: `backend/scripts/backfill_embeddings_1536.py`
- **Modelo embedding**: OpenAI `text-embedding-3-small` (1536 dims)
- **Vector DB**: Supabase con pgvector extension
- **SQL Schemas**: `docs/SETUP_SUPABASE.md`
