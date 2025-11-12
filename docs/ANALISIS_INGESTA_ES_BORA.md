# 📊 Análisis: Ingesta de Diccionario Español→Bora

## 🎯 Objetivo
Diseñar estrategia óptima para ingestar `salida_es_bora_final.json` (diccionario ES→Bora) complementando el existente `salida.json` (Bora→ES).

---

## 📁 Comparación de Estructuras JSON

### **salida.json** (Bora→ES) - ACTUAL
```json
{
  "lemma": "aábukɨ",           // Palabra en BORA
  "gloss_es": "sol",            // Traducción al español
  "pos": "s",
  "pos_full": "sustantivo",
  "page": 1,
  "variants": ["aábukɨɨ"],
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
      "examples": [...]
    }
  ]
}
```

### **salida_es_bora_final.json** (ES→Bora) - NUEVO
```json
{
  "lemma": "a",                 // Palabra en ESPAÑOL
  "gloss_bora": "ri; vu",       // Traducción(es) al Bora
  "pos": "prep.",
  "pos_full": "preposición",
  "variants": [],
  "synonyms": [],
  "subentries": [
    {
      "lemma": "a cambio",      // Frase en ESPAÑOL
      "gloss_bora": "hallúvu",  // Traducción al Bora
      "pos": "prep.",
      "examples": [
        {
          "es": "Recibí dos ollas a cambio de mi gallina.",
          "bora": "Tácáracá hallúvú ó ujcú llíyihllócu."
        }
      ]
    }
  ]
}
```

---

## 🔍 Diferencias Clave

| Aspecto | salida.json (Bora→ES) | salida_es_bora_final.json (ES→Bora) |
|---------|----------------------|-------------------------------------|
| **Lemma** | Palabra en Bora | Palabra en Español |
| **Gloss** | `gloss_es` (1 traducción) | `gloss_bora` (múltiples: "ri; vu") |
| **Dirección** | Bora → Español | Español → Bora |
| **Múltiples traducciones** | No | Sí (separadas por ";") |
| **Sinónimos** | No usado | Campo presente (vacío) |
| **Subentries** | Frases derivadas en Bora | Frases compuestas en Español |

---

## ⚠️ Desafíos Identificados

### 1. **Múltiples Traducciones en `gloss_bora`**
```json
"gloss_bora": "ri; vu"  // ¿Cómo vectorizar esto?
```

**Opciones**:
- ✅ **A) Crear un documento por traducción**
  ```
  "[LEMMA_ES] a | DEF_BORA: ri | POS: preposición"
  "[LEMMA_ES] a | DEF_BORA: vu | POS: preposición"
  ```
  
- ❌ **B) Concatenar todas**
  ```
  "[LEMMA_ES] a | DEF_BORA: ri; vu | POS: preposición"
  ```
  **Problema**: Vectorización menos precisa

**Recomendación**: **Opción A** - Split por ";" y generar documentos separados

---

### 2. **Esquema de Base de Datos**

#### Opción 1: **Reusar tablas existentes** (⚠️ Problemático)
```sql
-- lexicon_lemmas
lemma: "a"          -- ¿Español o Bora?
gloss_es: NULL      -- No aplica para ES→Bora
gloss_bora: "ri"    -- ❌ Campo no existe
```

**Problemas**:
- `gloss_es` es NOT NULL en schema actual
- Confusión: ¿el lemma es ES o Bora?
- Mixing de direcciones en misma tabla

#### Opción 2: **Tablas espejo para ES→Bora** (✅ Limpio)
```sql
-- Nuevas tablas:
CREATE TABLE lexicon_lemmas_es_bora (
  id BIGSERIAL PRIMARY KEY,
  lemma TEXT NOT NULL,          -- Palabra en español
  gloss_bora TEXT NOT NULL,     -- Traducción(es) al Bora
  pos TEXT,
  pos_full TEXT,
  variants TEXT[],
  synonyms TEXT[],
  source TEXT DEFAULT 'salida_es_bora_final.json',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE lexicon_subentries_es_bora (...);
CREATE TABLE lexicon_examples_es_bora (...);
```

**Ventajas**:
- ✅ Separación clara de direcciones
- ✅ Schema específico para cada diccionario
- ✅ Queries no confusas

**Desventajas**:
- ❌ Duplicación de estructura
- ❌ Más tablas para mantener

#### Opción 3: **Columnas adicionales en tablas existentes** (✅ Flexible)
```sql
-- Modificar tablas existentes:
ALTER TABLE lexicon_lemmas
  ADD COLUMN direction TEXT DEFAULT 'bora_es',  -- 'bora_es' | 'es_bora'
  ADD COLUMN gloss_bora TEXT,                   -- Para ES→Bora
  ALTER COLUMN gloss_es DROP NOT NULL;          -- Permitir NULL

-- Constraint: al menos uno de los dos debe existir
ALTER TABLE lexicon_lemmas
  ADD CONSTRAINT check_has_gloss 
  CHECK (gloss_es IS NOT NULL OR gloss_bora IS NOT NULL);
```

**Ventajas**:
- ✅ Una sola tabla para ambas direcciones
- ✅ Fácil filtrar por `direction`
- ✅ Reutilización de infraestructura

---

### 3. **Formato de Documentos para `bora_docs`**

#### Documentos tipo LEMMA (ES→Bora)
```python
# ANTES (Bora→ES):
"[LEMMA] aábukɨ | DEF_ES: sol | POS: sustantivo | PAG: 1"

# NUEVO (ES→Bora):
"[LEMMA_ES] a | DEF_BORA: ri | POS: preposición | PAG: 15"
"[LEMMA_ES] a | DEF_BORA: vu | POS: preposición | PAG: 15"  # Si hay múltiples
```

#### Documentos tipo SUBENTRY
```python
# ANTES (Bora→ES):
"[SUBLEMMA] aábukɨ tsúúhne | DEF_ES: mediodía | POS: locución"

# NUEVO (ES→Bora):
"[SUBLEMMA_ES] a cambio | DEF_BORA: hallúvu | POS: preposición"
```

#### Documentos tipo EXAMPLE (mantener formato)
```python
# Mismo formato para ambas direcciones:
"BORA: Tácáracá hallúvú ó ujcú llíyihllócu. [SEP] ES: Recibí dos ollas a cambio de mi gallina. [SEP] LEMMA: a cambio POS: preposición"
```

---

## 📊 Estadísticas Estimadas

### salida.json (Bora→ES)
```
Entradas: ~2,450
Lemmas: ~2,180
Subentries: ~450
Examples: ~3,200
Documentos vectorizados: ~5,830
```

### salida_es_bora_final.json (ES→Bora)
```json
// Archivo: 101,060 líneas
// Análisis necesario:
- Contar entradas únicas
- Contar subentries
- Contar examples
- Estimar documentos finales
```

**Estimación conservadora** (basada en ratio):
```
Entradas: ~8,000-12,000 (más palabras en ES que en Bora)
Subentries: ~2,000-3,000
Examples: ~10,000-15,000
Documentos vectorizados: ~20,000-30,000

Embeddings a generar: ~25,000 vectores (1536 dims)
Llamadas a OpenAI: ~400 batches (64 cada uno)
Costo estimado: ~$0.50-1.00 USD
Tiempo estimado: ~15-20 minutos
```

---

## 🚀 Estrategia Recomendada

### **Opción Preferida: Esquema Bidireccional Unificado**

#### 1. **Modificar Schema SQL**
```sql
-- Agregar columnas para ambas direcciones
ALTER TABLE lexicon_lemmas
  ADD COLUMN direction TEXT DEFAULT 'bora_es' CHECK (direction IN ('bora_es', 'es_bora')),
  ADD COLUMN gloss_bora TEXT,
  ALTER COLUMN gloss_es DROP NOT NULL,
  ADD CONSTRAINT check_has_gloss CHECK (gloss_es IS NOT NULL OR gloss_bora IS NOT NULL);

ALTER TABLE lexicon_subentries
  ADD COLUMN direction TEXT DEFAULT 'bora_es' CHECK (direction IN ('bora_es', 'es_bora')),
  ADD COLUMN gloss_bora TEXT,
  ALTER COLUMN gloss_es DROP NOT NULL,
  ADD CONSTRAINT check_has_gloss CHECK (gloss_es IS NOT NULL OR gloss_bora IS NOT NULL);

-- Índices para búsqueda por dirección
CREATE INDEX idx_lemmas_direction ON lexicon_lemmas(direction);
CREATE INDEX idx_subentries_direction ON lexicon_subentries(direction);
```

#### 2. **Script de Ingesta: `ingest_es_bora_docs.py`**

```python
def build_lemmas_es_bora(data: List[Dict]) -> List[Dict]:
    """
    Construye lemmas desde salida_es_bora_final.json
    
    DIFERENCIA CLAVE: Split de gloss_bora si tiene múltiples traducciones
    """
    out = []
    seen = set()
    
    for e in data:
        lemma_es = e.get('lemma')  # Palabra en español
        gloss_bora = e.get('gloss_bora', '')  # Traducción(es) al Bora
        
        if not lemma_es or not gloss_bora:
            continue
        
        # Split por ";" para manejar múltiples traducciones
        translations = [t.strip() for t in gloss_bora.split(';') if t.strip()]
        
        for translation in translations:
            key = (lemma_es, translation, 'salida_es_bora_final.json')
            if key in seen:
                continue
            seen.add(key)
            
            out.append({
                'lemma': lemma_es,              # Palabra en español
                'gloss_bora': translation,       # UNA traducción al Bora
                'gloss_es': None,                # NULL para ES→Bora
                'direction': 'es_bora',          # Marcador de dirección
                'pos': e.get('pos'),
                'pos_full': e.get('pos_full'),
                'variants': e.get('variants'),
                'synonyms': e.get('synonyms'),
                'source': 'salida_es_bora_final.json',
            })
    
    return out


def build_bora_docs_texts_es_bora(
    kind: str,
    items: List[Dict],
    lemma_meta: Dict[int, Dict],
) -> Tuple[List[str], List[Dict]]:
    """
    Genera textos para vectorización (ES→Bora)
    """
    texts = []
    records = []
    
    if kind == 'lemma':
        for it in items:
            lemma_id = it['id']
            meta = lemma_meta[lemma_id]
            
            # Formato: [LEMMA_ES] palabra_español | DEF_BORA: traducción_bora | POS: categoría
            content = f"[LEMMA_ES] {meta['lemma']} | DEF_BORA: {meta['gloss_bora']} | POS: {meta.get('pos_full') or meta.get('pos')}"
            
            texts.append(content)
            records.append({
                'kind': 'lemma',
                'parent_lemma_id': lemma_id,
                'content': content,
                'metadata': {
                    'source': 'salida_es_bora_final.json',
                    'direction': 'es_bora',
                    'lemma': meta['lemma'],
                    'gloss_bora': meta['gloss_bora'],
                    'pos': meta.get('pos'),
                    'pos_full': meta.get('pos_full'),
                }
            })
    
    elif kind == 'example':
        # MISMO formato que Bora→ES (bidireccional)
        for it in items:
            meta = lemma_meta[it['lemma_id']]
            content = f"BORA: {it['bora_text']} [SEP] ES: {it['spanish_text']} [SEP] LEMMA: {meta['lemma']} POS: {meta.get('pos_full')}"
            
            texts.append(content)
            records.append({
                'kind': 'example',
                'parent_lemma_id': it['lemma_id'],
                'example_id': it['id'],
                'content': content,
                'metadata': {
                    'source': 'salida_es_bora_final.json',
                    'direction': 'es_bora',
                    'bora_text': it['bora_text'],
                    'spanish_text': it['spanish_text'],
                }
            })
    
    return texts, records
```

#### 3. **Procesamiento en Batches**
```python
# Mismo enfoque que salida.json
python backend/scripts/ingest_es_bora_docs.py \
  --path ../salida_es_bora_final.json \
  --batch-size 400 \          # Insert en batches de 400
  --embed-batch-size 64 \     # OpenAI embeddings: 64 por llamada
  --reset                      # Limpia ES→Bora previos
```

---

## 📋 Información a Almacenar

### ✅ **Datos a Incluir**

1. **Lemmas ES→Bora**:
   - Palabra en español (`lemma`)
   - **CADA traducción al Bora** (`gloss_bora`) - split por ";"
   - Categoría gramatical (`pos`, `pos_full`)
   - Variantes (si existen)
   - Sinónimos (campo presente en JSON)

2. **Subentries**:
   - Frases compuestas en español (`lemma` de subentry)
   - Traducción(es) al Bora (`gloss_bora`)
   - Categoría gramatical

3. **Examples**:
   - Par completo Bora-Español (igual que Bora→ES)
   - Relación con lemma padre
   - Categoría contextual

4. **Embeddings**:
   - Vector 1536 dims para cada documento
   - Metadata completa (dirección, source, etc.)

### ❌ **Datos a Omitir**

1. **Sinónimos vacíos** (`synonyms: []`)
2. **Variantes vacías** (`variants: []`)
3. **Duplicados** (misma palabra ES + traducción Bora)
4. **Examples incompletos** (falta `bora` o `es`)

---

## 🎯 Ventajas de Este Enfoque

### 1. **Búsqueda Bidireccional Nativa**
```python
# Usuario pregunta en español:
query = "como se dice casa en bora"
# Encuentra documentos de AMBOS diccionarios:
# - [LEMMA] kátyi | DEF_ES: casa (Bora→ES)
# - [LEMMA_ES] casa | DEF_BORA: kátyi (ES→Bora)
```

### 2. **Redundancia Positiva**
- Ejemplos duplicados refuerzan búsqueda semántica
- Mayor cobertura de variantes lingüísticas

### 3. **Filtrado Flexible**
```sql
-- Solo Bora→ES:
SELECT * FROM bora_docs 
WHERE metadata->>'direction' = 'bora_es';

-- Solo ES→Bora:
SELECT * FROM bora_docs 
WHERE metadata->>'direction' = 'es_bora';

-- Ambas direcciones (default):
SELECT * FROM bora_docs;
```

---

## 📊 Próximos Pasos

### 1. **Análisis Exploratorio** ✅
- [x] Comparar estructuras JSON
- [ ] Contar entradas únicas en `salida_es_bora_final.json`
- [ ] Validar calidad de datos (campos faltantes, duplicados)

### 2. **Migración de Schema** 🔄
- [ ] Escribir SQL para agregar columnas `direction` y `gloss_bora`
- [ ] Aplicar migraciones en Supabase
- [ ] Validar constraints

### 3. **Script de Ingesta** 🔄
- [ ] Adaptar `ingest_bora_docs.py` → `ingest_es_bora_docs.py`
- [ ] Implementar split de `gloss_bora` por ";"
- [ ] Ajustar formato de documentos (LEMMA_ES, etc.)

### 4. **Ejecución** 🚀
- [ ] Dry-run con `--limit 100`
- [ ] Validar embeddings generados
- [ ] Ingesta completa (~25,000 documentos)

### 5. **Validación** ✅
- [ ] Queries de prueba ES→Bora
- [ ] Comparar resultados con/sin ES→Bora
- [ ] Ajustar prompts si es necesario

---

## 💡 Consideraciones Finales

### Costos OpenAI
```
~25,000 embeddings × $0.00002/embedding = ~$0.50 USD
Total con Bora→ES: ~$1.00-1.50 USD
```

### Tiempo de Ejecución
```
~25,000 embeddings ÷ 64/batch = ~391 batches
~391 batches × 2s/batch = ~13 minutos
```

### Storage Supabase
```
~30,000 documentos × 1536 dims × 4 bytes = ~184 MB de vectores
Total con Bora→ES: ~250 MB
```

---

## 🔗 Referencias

- **Script base**: `backend/scripts/ingest_bora_docs.py`
- **Schema actual**: `docs/SETUP_SUPABASE.md`
- **JSON Bora→ES**: `salida.json`
- **JSON ES→Bora**: `salida_es_bora_final.json`
- **Embeddings**: OpenAI text-embedding-3-small (1536 dims)
