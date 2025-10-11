# 🤖 Configuración de HuggingFace para MIAPPBORA

## Paso 1: Crear Cuenta en HuggingFace

1. Ve a https://huggingface.co
2. Haz clic en **Sign Up** (esquina superior derecha)
3. Regístrate con email o GitHub
4. Verifica tu email

## Paso 2: Obtener Token de API

1. Una vez logueado, ve a tu perfil (esquina superior derecha)
2. Click en **Settings** → **Access Tokens**
3. O ve directamente a: https://huggingface.co/settings/tokens
4. Haz clic en **New token**
5. Configuración del token:
   - **Name**: `miappbora`
   - **Role**: `read` (solo lectura es suficiente)
6. Copia el token (empieza con `hf_...`)

⚠️ **IMPORTANTE**: Guarda el token inmediatamente, solo se muestra una vez

## Paso 3: Configurar Token en .env

Abre el archivo `backend/.env` y actualiza:

```env
HUGGINGFACE_API_KEY=hf_tu_token_real_aqui
```

## Paso 4: Instalar Dependencias

```bash
cd backend
pip install sentence-transformers transformers torch
```

**Nota sobre torch**: La descarga puede ser grande (~2GB), ten paciencia.

### Instalación alternativa (más ligera):

Si tienes problemas con torch, usa la versión CPU:
```bash
pip install sentence-transformers transformers torch --index-url https://download.pytorch.org/whl/cpu
```

## Paso 5: Verificar Instalación

```bash
python -c "from sentence_transformers import SentenceTransformer; print('✅ OK')"
```

## Paso 6: Generar Embeddings del Corpus

Una vez instaladas las dependencias, ejecuta:

```bash
python scripts/generate_embeddings.py
```

Este script:
- ✅ Carga el modelo `sentence-transformers/all-MiniLM-L6-v2`
- ✅ Genera vectores de 384 dimensiones para cada frase
- ✅ Guarda los embeddings en Supabase (tabla `phrase_embeddings`)
- ✅ Habilita búsqueda semántica para el chat RAG

---

## 📊 Modelos Utilizados

### Embedding Model
- **Modelo**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensión**: 384
- **Tamaño**: ~80MB
- **Uso**: Convertir texto a vectores para búsqueda semántica
- **Idioma**: Multilingüe (funciona con Bora y Español)

### LLM Model (Chat)
- **Modelo**: `microsoft/DialoGPT-medium`
- **Tamaño**: ~350MB
- **Uso**: Generar respuestas conversacionales
- **Nota**: Puedes cambiarlo por otros modelos según necesidad

---

## 🔧 Troubleshooting

### Error: "No module named 'torch'"
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Error: "Slow download speeds"
- HuggingFace descarga modelos la primera vez
- Los modelos se cachean localmente en `~/.cache/huggingface`
- Siguientes ejecuciones serán mucho más rápidas

### Error: "CUDA not available"
- Es normal si no tienes GPU NVIDIA
- Los modelos funcionarán en CPU (más lento pero funcional)
- Para esta app, CPU es suficiente

### Error: "Out of memory"
- Los modelos elegidos son ligeros (~500MB total)
- Si tienes problemas, cierra otras aplicaciones
- Mínimo recomendado: 4GB RAM

---

## ✅ Checklist

- [ ] Cuenta en HuggingFace creada
- [ ] Token de API generado
- [ ] Token agregado a `.env`
- [ ] `sentence-transformers` instalado
- [ ] `transformers` instalado
- [ ] `torch` instalado
- [ ] Test de importación exitoso
- [ ] Embeddings generados

---

## 🎯 Siguiente Paso

Una vez que tengas los embeddings generados, podrás:

1. **Probar el chat RAG** - Preguntar en español y recibir frases Bora relevantes
2. **Búsqueda semántica** - Encontrar frases por significado, no solo palabras exactas
3. **Minijuegos inteligentes** - Generar quizzes personalizados

**Tiempo estimado total**: 15-20 minutos (dependiendo de velocidad de descarga)
