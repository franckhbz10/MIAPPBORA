# MIAPPBORA - Aprende Bora 🌿

Aplicación web (FastAPI + Vue 3) con Mentor conversacional y minijuegos para aprender frases en Bora.

Esta versión unifica el diccionario en un esquema único (bora_docs) con búsqueda semántica (pgvector) y ejecuta un LLM local por defecto (Qwen/Qwen3-1.7B con Transformers).

## � Inicio rápido (Windows PowerShell)

1) Clona el repositorio y entra al backend

```powershell
git clone https://github.com/franckhbz10/MIAPPBORA.git
cd MIAPPBORA/backend
```

2) Crea y activa el entorno virtual del backend

```powershell
python -m venv .\venv
& .\venv\Scripts\Activate.ps1
```

3) Instala dependencias del backend

Recomendado (lista unificada):

```powershell
pip install -r ..\backend\requirements.merged.txt
```

Alternativa mínima (solo backend):

```powershell
pip install -r requirements.txt
```

4) Copia y edita variables de entorno

```powershell
Copy-Item .env.example .env
# Edita .env y completa: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, POSTGRES_URL/DATABASE_URL
```

5) Prepara la base de datos en Supabase (esquema unificado + RPC)

Opción A (GUI): abre tu proyecto en Supabase → SQL Editor → pega el SQL de `docs/create_bora_docs_and_match.sql` y ejecútalo.

Opción B (script local usando POSTGRES_URL):

```powershell
& .\venv\Scripts\python.exe ..\backend\scripts\setup_bora_docs.py
```

6) Ingresa el diccionario (salida.json) y crea embeddings

Requiere en `.env`: SUPABASE_SERVICE_KEY (service_role) para escritura bajo RLS.

```powershell
# Ajusta la ruta a tu archivo salida.json
& .\venv\Scripts\python.exe ..\backend\scripts\ingest_bora_docs.py --path ..\salida.json --batch-size 400 --embed-batch-size 64
```

7) Arranca el backend

```powershell
uvicorn main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

8) Arranca el frontend en otra terminal

```powershell
cd ..\frontend
npm install
npm run dev
# Front: http://localhost:3000 (proxy /api → http://127.0.0.1:8000)
```

## 📦 Prerrequisitos

- Python 3.10/3.11 (recomendado 3.10)
- Node.js 18+
- Cuenta en Supabase (gratis)
- (Opcional) Cuenta en Hugging Face si usas Inference API

## 🔧 Configuración importante

### Backend (.env)

Campos clave (ver `backend/.env.example`):

- Supabase:
    - SUPABASE_URL, SUPABASE_ANON_KEY (lectura)
    - SUPABASE_SERVICE_KEY (service_role para ingesta)
    - POSTGRES_URL o DATABASE_URL (cadena de conexión para aplicar SQL desde script)
- LLM/Embeddings:
    - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 (384d)
    - LLM_BACKEND=transformers
    - LLM_MODEL=Qwen/Qwen3-1.7B
    - LLM_DEVICE_MAP=auto, LLM_DTYPE=auto (usa GPU si disponible)
    - LLM_MAX_NEW_TOKENS, LLM_TEMPERATURE, LLM_TOP_P
    - HUGGINGFACE_API_KEY (solo si usas Inference API como fallback)

### Frontend (Vite)

`frontend/vite.config.js` ya configura un proxy:

- Dev server: http://localhost:3000
- Proxy: `/api` → `http://127.0.0.1:8000`

## 🔍 Endpoints clave

- Health:
    - GET `http://localhost:8000/health/`
    - GET `http://localhost:8000/health/connections`
- Mentor (lexicón unificado):
    - GET `http://localhost:8000/api/lexicon/search?q=hola&top_k=10&min_similarity=0.7`
    - Parámetros: q (string), top_k (1–50), min_similarity (0–1), category (opcional)

En el frontend, abre la vista “Mentor Bora” (ruta `/chat`) y prueba consultas.

## 🧠 LLM local (Qwen/Qwen3-1.7B)

- Se descarga la primera vez (puede tardar). Requiere RAM/VRAM acorde.
- Usa Transformers local. Si deseas forzar CPU, define `LLM_DEVICE_MAP=cpu`.
- Para GPU con FP16/BF16, puedes usar: `LLM_DTYPE=float16` o `bfloat16` (si tu HW lo soporta).
- Fallback opcional a Hugging Face Inference API si configuras `HUGGINGFACE_API_KEY` y/o `LLM_BACKEND=inference-api`.

### ¿Por qué usamos transformers 4.45.2 (y no la última)?

Las versiones están **congeladas intencionalmente** para estabilidad en Windows con CPU:
- **transformers 4.45.2**, **accelerate 0.33.0**, **torch 2.1.0**: conjunto probado y estable
- **tokenizers 0.20.3**: compatible con el resto del stack (LangChain, Supabase, sentence-transformers)
- Actualizar a `transformers >= 4.48` requiere `torch >= 2.2.0`, lo que genera conflictos en cascada con `torchvision`, `langchain-core` y módulos del sistema en Windows

Si necesitas versiones más recientes de transformers (por ej., para Qwen3 nativo sin `trust_remote_code`), consulta:
- **Plan B - Microservicio LLM:** `docs/LLM_MICROSERVICE.md`
- **Organización del proyecto:** `docs/ORGANIZACION_PROYECTO.md`

Estos documentos explican cómo separar el LLM en un microservicio independiente con su propio venv y versiones actualizadas, comunicándose por HTTP con el backend principal.

## 🧪 Verificación rápida

1) Import sanity (ya dentro del venv del backend):

```powershell
& .\venv\Scripts\python.exe -c "import transformers,tokenizers,PIL,torch; print('ok')"
```

2) Health API:

- http://localhost:8000/health
- http://localhost:8000/health/connections

3) Mentor (API):

- http://localhost:8000/api/lexicon/search?q=saludo

## 🧰 Estructura del proyecto (resumen)

```
miappbora/
├── backend/
│   ├── main.py
│   ├── config/
│   │   ├── settings.py
│   │   └── database_connection.py
│   ├── adapters/
│   │   ├── huggingface_adapter.py          # Embeddings + LLM (Transformers local + fallback)
│   │   └── supabase_adapter.py             # Inserciones/búsquedas, RPC match_bora_docs
│   ├── routers/
│   │   ├── health_router.py
│   │   ├── auth_router.py
│   │   ├── profile_router.py
│   │   ├── game_router.py
│   │   └── lexicon_router.py               # GET /api/lexicon/search
│   ├── services/
│   │   └── rag_service.py                  # Pipeline RAG unificado
│   ├── scripts/
│   │   ├── setup_bora_docs.py              # Aplica docs/create_bora_docs_and_match.sql
│   │   └── ingest_bora_docs.py             # Ingesta salida.json + embeddings → bora_docs
│   ├── requirements.txt
│   ├── requirements.merged.txt             # Incluye extras ya validados
│   └── .env.example
└── frontend/
        ├── src/views/Chat.vue                  # Mentor Bora
        ├── src/views/HealthCheck.vue
        ├── src/services/lexiconService.js
        └── vite.config.js
```

## � Problemas comunes (Windows)

- “invalid distribution -okenizers/-illow”: archivos en uso o instalación corrupta.
    - Solución: parar el servidor; luego `pip install --force-reinstall --no-cache-dir tokenizers==0.20.3 pillow`.
- Descargas lentas del modelo Qwen: primera vez puede tardar; verifica conexión y espacio en disco.
- Error de Supabase / permisos: para ingesta usa `SUPABASE_SERVICE_KEY` (service_role) en `.env`.

## 📄 Licencia

Proyecto educativo para el aprendizaje del idioma Bora.
