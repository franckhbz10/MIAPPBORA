# Organización del Proyecto - Decisiones de Arquitectura

## Estado actual del proyecto (limpiado)

```
miappbora/
├── .git/
├── .gitignore
├── README.md
├── salida.json                     # Diccionario Bora (fuente de datos)
│
├── backend/                        # Backend principal FastAPI
│   ├── .env
│   ├── .env.example
│   ├── main.py                     # Puerto 8000
│   ├── requirements.txt            # Dependencias estables (transformers 4.45.2)
│   ├── start-backend.ps1
│   ├── venv/                       # Entorno virtual
│   ├── adapters/                   # HuggingFace, Supabase
│   ├── config/                     # Settings, DB connection
│   ├── models/                     # SQLAlchemy models
│   ├── routers/                    # Auth, Game, Health, Profile, Lexicon
│   ├── schemas/                    # Pydantic schemas
│   ├── scripts/                    # Ingesta, setup, tests
│   └── services/                   # Auth, Game, Profile, RAG
│
├── docs/                           # Documentación
│   ├── CLEANUP_SCRIPTS.sql
│   ├── FLUJOS_FUNCIONALIDADES.md
│   ├── FULL_RESET.sql
│   ├── GUIA_INSTALACION.md
│   ├── LLM_MICROSERVICE.md         # Plan B: microservicio LLM
│   ├── README_CLEANUP.md
│   ├── SETUP_HUGGINGFACE.md
│   └── SETUP_SUPABASE.md
│
└── frontend/                       # Vue 3 + Vite
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── App.vue
    │   ├── main.js
    │   ├── assets/
    │   ├── components/
    │   ├── services/
    │   ├── stores/
    │   └── views/
    └── ...
```

---

## Decisión: Ubicación del microservicio LLM

### Opción A: Raíz del proyecto (mismo nivel que `backend/`)

```
miappbora/
├── backend/                        # Backend principal (puerto 8000)
├── llm_service/                    # Microservicio LLM (puerto 8001)
│   ├── .env
│   ├── main.py
│   ├── requirements.txt
│   ├── venv_llm/
│   ├── config/
│   ├── routers/
│   └── services/
├── frontend/
└── docs/
```

**Ventajas:**
- ✅ **Independencia total:** Cada servicio es autónomo (código, deps, venv, config)
- ✅ **Despliegue separado:** Fácil de dockerizar en contenedores distintos o deployar en máquinas diferentes (ej. backend en CPU, LLM en GPU)
- ✅ **Escalabilidad:** Se puede replicar `llm_service/` N veces sin tocar `backend/`
- ✅ **Claridad semántica:** A nivel de repo, se ve inmediatamente que son servicios de primera clase independientes
- ✅ **CI/CD independiente:** Pipelines separados para cada servicio (build, test, deploy)
- ✅ **Versionado separado:** Cada servicio puede tener su propio `CHANGELOG`, versión semántica, y release cycle

**Desventajas:**
- ⚠️ Dos `main.py`, dos `requirements.txt`, dos `.env` en raíz (puede ser verboso)
- ⚠️ Si compartes código (ej. schemas), necesitas un paquete común o duplicarlo

---

### Opción B: Dentro del backend (`backend/llm_service/`)

```
miappbora/
├── backend/
│   ├── main.py                     # Backend principal (puerto 8000)
│   ├── requirements.txt
│   ├── venv/
│   ├── adapters/
│   ├── config/
│   ├── routers/
│   ├── services/
│   └── llm_service/                # Microservicio LLM anidado
│       ├── main.py                 # Puerto 8001
│       ├── requirements.txt
│       ├── venv_llm/
│       ├── config/
│       ├── routers/
│       └── services/
├── frontend/
└── docs/
```

**Ventajas:**
- ✅ **Cohesión de dominio:** Si consideras al LLM como "parte del backend", queda agrupado
- ✅ **Menos carpetas en raíz:** Mantiene la estructura plana del proyecto
- ✅ **Compartir código más fácil:** Acceso directo a `backend/schemas/` o `backend/config/` si es necesario (con imports relativos)

**Desventajas:**
- ❌ **Acoplamiento implícito:** Da la impresión de que `llm_service` depende del backend principal (aunque no sea cierto)
- ❌ **Despliegue más complejo:** Docker/CI necesita distinguir qué parte del `backend/` es cada servicio
- ❌ **Confusión de responsabilidades:** `backend/` tiene dos `main.py`, dos venvs, dificulta entender qué es qué
- ❌ **Escalado horizontal menos claro:** Si quieres replicar solo el LLM, tienes que extraer la subcarpeta

---

## **Recomendación final: Opción A (raíz del proyecto)**

```
miappbora/
├── backend/                        # Backend principal (puerto 8000)
├── llm_service/                    # Microservicio LLM (puerto 8001) ⭐
├── frontend/
└── docs/
```

### Justificación

1. **Principio de separación de responsabilidades:**
   - `backend/` → API REST, autenticación, gamificación, Supabase, PostgreSQL
   - `llm_service/` → Solo generación LLM y embeddings (sin DB, sin auth, sin lógica de negocio)
   - Cada uno con su stack tecnológico y dependencias aisladas

2. **Futuro deployment en producción:**
   - Backend en contenedor ligero (CPU, sin GPU)
   - LLM en contenedor con GPU (NVIDIA, CUDA, optimizaciones específicas)
   - Posibilidad de escalar horizontalmente solo el LLM (load balancer + N réplicas)

3. **Mantenibilidad:**
   - Si cambia el modelo (ej. de Qwen3 a LLaMA, Mistral, etc.), solo tocas `llm_service/`
   - Si cambias framework del backend (ej. FastAPI → Flask), no afectas al LLM
   - Equipos separados pueden trabajar en cada servicio sin conflictos

4. **Compatibilidad con Plan B:**
   - El doc `LLM_MICROSERVICE.md` ya asume esta estructura
   - Los ejemplos de Docker Compose también

---

## Estructura propuesta final (con microservicio)

```
miappbora/
├── .git/
├── .gitignore
├── README.md
├── salida.json
│
├── backend/                        # Backend principal FastAPI (puerto 8000)
│   ├── .env
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt            # Sin transformers/torch pesados
│   ├── venv/
│   ├── adapters/
│   │   └── supabase_adapter.py     # Solo Supabase
│   ├── config/
│   ├── models/
│   ├── routers/
│   │   ├── auth_router.py
│   │   ├── game_router.py
│   │   ├── health_router.py
│   │   ├── profile_router.py
│   │   └── lexicon_router.py       # Llama a llm_service via HTTP
│   ├── schemas/
│   ├── scripts/
│   └── services/
│       ├── auth_service.py
│       ├── game_service.py
│       ├── profile_service.py
│       └── rag_service.py          # httpx → llm_service:8001
│
├── llm_service/                    # Microservicio LLM (puerto 8001) ⭐ NUEVO
│   ├── .env
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt            # transformers>=4.48, torch>=2.2, accelerate, etc.
│   ├── start-llm.ps1
│   ├── venv_llm/                   # Python 3.10+ con libs actualizadas
│   ├── config/
│   │   └── settings.py
│   ├── routers/
│   │   └── llm_router.py           # POST /generate, POST /embed
│   └── services/
│       └── llm_service.py          # Carga modelo, genera respuestas
│
├── docs/
│   ├── LLM_MICROSERVICE.md
│   ├── ORGANIZACION_PROYECTO.md    # Este archivo
│   └── ...
│
└── frontend/
    └── ...
```

---

## Flujo de comunicación (con microservicio)

```
[Usuario]
   ↓
[Frontend Vue:3000]
   ↓ GET /api/lexicon/search?q=hola
[Backend FastAPI:8000]
   ├─→ Supabase (búsqueda semántica) → resultados
   ├─→ POST http://localhost:8001/api/llm/generate
   │     ↓
   │  [LLM Service:8001]
   │     ├─→ Tokenizer + Qwen3-1.7B
   │     └─→ respuesta generada
   │
   └─→ POST-procesar respuesta
   └─→ JSON respuesta al frontend
```

---

## Alternativa conservadora (mantener actual sin microservicio)

Si decides **NO** implementar el microservicio por ahora:

```
miappbora/
├── backend/                        # Backend único (puerto 8000)
│   ├── venv/                       # transformers 4.45.2 (estable)
│   ├── adapters/
│   │   ├── huggingface_adapter.py  # LLM local + fallback Inference API
│   │   └── supabase_adapter.py
│   └── services/
│       └── rag_service.py          # Llama HuggingFaceAdapter directamente
├── frontend/
└── docs/
```

**Ventajas:**
- ✅ Simplicidad: un solo servidor, un solo venv, un solo `uvicorn`
- ✅ Sin overhead HTTP entre servicios
- ✅ Menos complejidad operacional

**Desventajas:**
- ❌ Atrapado en transformers 4.45.2 (actualizar es complejo)
- ❌ No escalable horizontalmente (LLM + backend van juntos)
- ❌ En producción con GPU, todo el backend necesita recursos GPU innecesariamente

---

## Recomendación inmediata

1. **Por ahora (corto plazo):**
   - Mantén la estructura actual (backend único) con transformers 4.45.2 estable
   - El sistema funciona y no hay urgencia de actualizar

2. **Si necesitas actualizar transformers o escalar (mediano plazo):**
   - Implementa el microservicio LLM en `llm_service/` (raíz del proyecto)
   - Usa el código de `docs/LLM_MICROSERVICE.md` como base
   - Migra gradualmente: primero endpoints `/generate` y `/embed`, luego adapta `rag_service.py`

3. **Preparación futura:**
   - Ya documentamos el Plan B en `docs/LLM_MICROSERVICE.md`
   - README actualizado explica por qué usamos versiones estables
   - Cuando decidas migrar, tienes la arquitectura lista

---

## Conclusión

**Mejor ubicación para el microservicio LLM: raíz del proyecto (`llm_service/`)**

Razones principales:
- Independencia total (código, deps, venv, deployment)
- Escalabilidad horizontal (replica solo el LLM)
- Claridad arquitectónica (servicios de primera clase)
- Compatibilidad con Docker Compose y orquestación
- Facilita equipos separados y ciclos de desarrollo independientes

Si implementas el microservicio, sigue la estructura propuesta en este documento y el código de ejemplo en `docs/LLM_MICROSERVICE.md`.
