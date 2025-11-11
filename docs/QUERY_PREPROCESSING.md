# Preprocesamiento de Queries con LLM

## 🎯 Objetivo

Mejorar la precisión de la búsqueda vectorial en el **Mentor Bora** eliminando el ruido conversacional de las queries de usuarios antes de generar los embeddings.

## ❌ Problema Identificado

### Antes del Preprocesamiento

Cuando un usuario hace una pregunta con contexto conversacional:

```
"hola soy pablito, estoy estudiando y no se como saludar en la lengua bora"
```

El sistema **vectorizaba la query completa**, incluyendo:
- Saludos ("hola")
- Presentaciones ("soy pablito")
- Contexto personal ("estoy estudiando")
- La pregunta real ("como saludar en la lengua bora")

**Problema**: El embedding resultante contenía demasiado ruido, reduciendo la precisión de la búsqueda semántica.

## ✅ Solución Implementada

### Pipeline de Preprocesamiento

```
┌─────────────────────────────────────────────────────────────┐
│ 1. QUERY ORIGINAL (con ruido)                               │
│    "hola soy pablito, estoy estudiando y no se como         │
│     saludar en la lengua bora"                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. EXTRACCIÓN DE KEYWORDS (gpt-4o-mini)                     │
│    Prompt especializado extrae términos clave               │
│    Resultado: "saludar"                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. EMBEDDING (OpenAI text-embedding-3-small)                │
│    Solo vectoriza la query limpia                           │
│    Vector 1536 dims de "saludar"                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. BÚSQUEDA VECTORIAL (pgvector)                            │
│    Busca top-k documentos similares a "saludar"             │
│    Mayor precisión sin ruido conversacional                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. RESPUESTA FINAL (gpt-4o-mini)                            │
│    Usa QUERY ORIGINAL completa + contexto recuperado        │
│    Responde de forma conversacional y natural               │
└─────────────────────────────────────────────────────────────┘
```

### Componente Clave: `_extract_search_keywords()`

Ubicación: `backend/services/rag_service.py`

```python
async def _extract_search_keywords(self, query: str) -> str:
    """
    Extrae keywords/frases relevantes usando gpt-4o-mini.
    
    Ejemplos:
    - Input:  "hola soy pablito, estoy estudiando y no se como saludar en la lengua bora"
      Output: "saludar"
    
    - Input:  "oye amigo, necesito saber como se dice casa en bora"
      Output: "casa"
    
    - Input:  "que significa áábukɨ en español"
      Output: "áábukɨ"
    """
```

## 🔧 Implementación Técnica

### Configuración del Modelo

- **Modelo**: `gpt-4o-mini`
- **Temperatura**: `0.1` (baja para consistencia)
- **Max tokens**: `50` (keywords cortas)
- **Timeout**: Hereda de `settings.OPENAI_TIMEOUT`

### Prompt de Extracción

El prompt está diseñado con **few-shot learning** para entrenar al modelo:

```
Eres un asistente que extrae palabras o frases clave de consultas de traducción.

Tu tarea: Identificar QUÉ palabra o frase en español el usuario quiere 
traducir al idioma Bora, ignorando todo el ruido conversacional.

Reglas:
1. Extrae SOLO la palabra/frase que necesita traducción
2. Ignora saludos, presentaciones, contexto personal
3. Si hay múltiples términos relacionados, mantén la frase completa
4. Responde ÚNICAMENTE con la palabra/frase extraída, sin explicaciones

Ejemplos:
Usuario: "hola soy pablito, estoy estudiando y no se como saludar en la lengua bora"
Asistente: saludar

Usuario: "como digo yo soy estudiante en bora"
Asistente: yo soy estudiante
```

### Validación y Fallbacks

```python
# Validación básica
if not extracted or len(extracted) > len(query) * 1.5:
    logger.warning(f"Keyword extraction inválida, usando query original")
    return query

# Fallback si OpenAI no disponible
if not self.openai_adapter:
    logger.warning("OpenAI adapter no disponible, usando query original")
    return query

# Fallback en caso de error
except Exception as e:
    logger.error(f"Error en keyword extraction: {e}")
    return query  # Siempre retorna la query original como fallback seguro
```

## 📊 Beneficios

### 1. **Mayor Precisión en Búsqueda Vectorial**

- ✅ Embeddings más enfocados en términos relevantes
- ✅ Reducción de falsos positivos por ruido conversacional
- ✅ Mejora en ranking de resultados relevantes

### 2. **Respuestas Más Naturales**

- ✅ Query original se mantiene para el LLM final
- ✅ El LLM puede responder con contexto conversacional
- ✅ No se pierde información del usuario

### 3. **Manejo de Frases Complejas**

El sistema detecta y mantiene frases completas cuando es necesario:

```
Input:  "como se dice yo soy estudiante en bora"
Output: "yo soy estudiante"  ← Mantiene la frase completa
```

### 4. **Dirección Agnóstica**

El preprocesamiento funciona para ambas direcciones de traducción:

- **Español → Bora**: `"como se dice casa"` → `"casa"`
- **Bora → Español**: `"que significa áábukɨ"` → `"áábukɨ"`

## 🧪 Testing

### Script de Prueba

```bash
cd backend
python -m scripts.test_query_preprocessing
```

Prueba casos como:
- Queries con ruido conversacional
- Queries inversas (Bora → Español)
- Queries con frases complejas
- Queries cortas/directas

### Casos de Prueba

```python
TEST_QUERIES = [
    "hola soy pablito, estoy estudiando y no se como saludar en la lengua bora",
    "oye amigo, necesito saber como se dice casa en bora",
    "que significa áábukɨ en español",
    "necesito ayuda para traducir la frase me gusta aprender idiomas",
    "casa",  # Query directa
]
```

## ⏱️ Impacto en Performance

### Latencia Adicional

El preprocesamiento agrega una llamada a gpt-4o-mini:

```
Timings típicos:
- preprocessing_ms: ~200-400ms (llamada LLM)
- embedding_ms: ~100-200ms (OpenAI embeddings)
- vector_search_ms: ~50-100ms (pgvector)
- llm_ms: ~800-1500ms (respuesta final)

Total: ~1200-2200ms (preprocesamiento = ~15-20% del total)
```

### Tradeoff

- ❌ **Costo**: +200-400ms de latencia
- ✅ **Beneficio**: Mejora significativa en precisión de resultados
- ✅ **ROI**: Vale la pena para mejor experiencia de usuario

## 🚀 Deploy

### Variables de Entorno Requeridas

```bash
# .env o Railway Variables
OPENAI_ENABLED=true
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=500
```

### Verificación Post-Deploy

```bash
# Railway Logs - buscar este patrón
🔍 Query preprocessing | Original: '...' → Cleaned: '...'
```

## 📝 Notas Importantes

### ⚠️ No Interfiere con Respuesta Final

El preprocesamiento **solo afecta la recuperación** (búsqueda vectorial). El LLM final siempre recibe la **query original completa** para poder:

- Entender el contexto conversacional
- Responder de forma natural
- Usar información adicional del usuario si es relevante

### ⚠️ Fallback Seguro

Si el preprocesamiento falla por cualquier razón:
- OpenAI no disponible
- Error de red
- Respuesta inválida

El sistema **automáticamente usa la query original** sin romper la funcionalidad.

### ⚠️ Caché No Afectado

El caché sigue usando la query original como key, así que:
- Queries idénticas usan caché
- El preprocesamiento solo ocurre en cache misses

## 🔮 Mejoras Futuras

### 1. **Modelo Local Opcional**

Usar un modelo pequeño local (Phi-3, Qwen) para reducir latencia y costos:

```python
# Fallback a modelo local si OpenAI no disponible
if not self.openai_adapter:
    return self._extract_keywords_local(query)  # TODO
```

### 2. **Caché de Keywords Extraídas**

Cachear keywords para queries frecuentes:

```python
_keyword_cache: Dict[str, str] = {}  # query -> cleaned_query
```

### 3. **Regex Patterns para Casos Simples**

Usar regex para casos triviales antes de llamar al LLM:

```python
# Patrón: "como se dice X"
match = re.search(r'como se dice (.+?)(?:\s+en\s+bora)?$', query)
if match:
    return match.group(1)  # Skip LLM call
```

## 📚 Referencias

- **Código**: `backend/services/rag_service.py` (línea ~87)
- **Tests**: `backend/scripts/test_query_preprocessing.py`
- **Modelo**: OpenAI gpt-4o-mini
- **Prompting**: Few-shot learning con ejemplos
