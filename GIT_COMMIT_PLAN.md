# 📋 Plan de Commits para MIAPPBORA

## Estrategia de Commits
Subir el proyecto en 10 commits organizados por funcionalidad.

---

## ✅ Commit 1: Inicialización y Documentación
```bash
git init
git branch -M main
git add .gitignore README.md
git commit -m "docs: inicialización del proyecto MIAPPBORA con documentación base"
git remote add origin https://github.com/franckhbz10/MIAPPBORA.git
git push -u origin main
```

**Archivos:**
- `.gitignore`
- `README.md`

---

## ✅ Commit 2: Configuración del Backend
```bash
git add backend/.env.example backend/requirements.txt backend/dependencies.py
git commit -m "feat(backend): configuración inicial y dependencias del proyecto"
git push origin main
```

**Archivos:**
- `backend/.env.example`
- `backend/requirements.txt`
- `backend/dependencies.py`

---

## ✅ Commit 3: Modelos de Base de Datos
```bash
git add backend/models/ backend/schemas/
git commit -m "feat(backend): modelos ORM y esquemas Pydantic para base de datos"
git push origin main
```

**Archivos:**
- `backend/models/__init__.py`
- `backend/models/database.py`
- `backend/schemas/schemas.py`

---

## ✅ Commit 4: Configuración y Conexiones
```bash
git add backend/config/
git commit -m "feat(backend): configuración de settings y conexión a base de datos"
git push origin main
```

**Archivos:**
- `backend/config/settings.py`
- `backend/config/database_connection.py`

---

## ✅ Commit 5: Adaptadores Externos (Supabase & HuggingFace)
```bash
git add backend/adapters/
git commit -m "feat(backend): adaptadores para Supabase y HuggingFace embeddings"
git push origin main
```

**Archivos:**
- `backend/adapters/supabase_adapter.py`
- `backend/adapters/huggingface_adapter.py`
- `backend/adapters/huggingface_adapter_hybrid.py`

---

## ✅ Commit 6: Servicios de Negocio
```bash
git add backend/services/
git commit -m "feat(backend): servicios de autenticación, juego, perfil y RAG"
git push origin main
```

**Archivos:**
- `backend/services/auth_service.py`
- `backend/services/game_service.py`
- `backend/services/profile_service.py`
- `backend/services/rag_service.py`

---

## ✅ Commit 7: API Endpoints (Routers)
```bash
git add backend/routers/ backend/main.py
git commit -m "feat(backend): endpoints API REST con FastAPI"
git push origin main
```

**Archivos:**
- `backend/routers/__init__.py`
- `backend/routers/auth_router.py`
- `backend/routers/game_router.py`
- `backend/routers/health_router.py`
- `backend/routers/profile_router.py`
- `backend/main.py`

---

## ✅ Commit 8: Scripts de Inicialización y Población
```bash
git add backend/scripts/ backend/check_backend.py backend/start-backend.ps1
git commit -m "feat(backend): scripts para poblar base de datos y verificación"
git push origin main
```

**Archivos:**
- `backend/scripts/load_bora_corpus.py`
- `backend/scripts/load_game_phrases.py`
- `backend/scripts/populate_gamification_data.py`
- `backend/scripts/generate_embeddings_simple.py`
- `backend/scripts/setup_vector_search.py`
- `backend/scripts/test_hf_api.py`
- `backend/scripts/test_semantic_search.py`
- `backend/check_backend.py`
- `backend/start-backend.ps1`

---

## ✅ Commit 9: Frontend - Configuración y Estructura Base
```bash
git add frontend/package.json frontend/vite.config.js frontend/index.html frontend/src/main.js frontend/src/App.vue
git commit -m "feat(frontend): configuración de Vue.js con Vite y estructura base"
git push origin main
```

**Archivos:**
- `frontend/package.json`
- `frontend/vite.config.js`
- `frontend/index.html`
- `frontend/src/main.js`
- `frontend/src/App.vue`

---

## ✅ Commit 10: Frontend - Componentes, Vistas y Servicios
```bash
git add frontend/src/
git commit -m "feat(frontend): componentes Vue, vistas, servicios y stores completos"
git push origin main
```

**Archivos:**
- `frontend/src/components/`
- `frontend/src/views/`
- `frontend/src/services/`
- `frontend/src/stores/`
- `frontend/src/assets/`

---

## ✅ Commit 11 (Bonus): Documentación SQL y Guías
```bash
git add docs/
git commit -m "docs: documentación SQL, guías de instalación y configuración"
git push origin main
```

**Archivos:**
- `docs/CLEANUP_SCRIPTS.sql`
- `docs/FULL_RESET.sql`
- `docs/QUICK_CLEANUP.sql`
- `docs/README_CLEANUP.md`
- `docs/SETUP_HUGGINGFACE.md`
- `docs/SETUP_SUPABASE.md`
- `docs/FLUJOS_FUNCIONALIDADES.md`
- `docs/GUIA_INSTALACION.md`
- `docs/create_match_phrases_function.sql`

---

## 🎯 Resumen de Commits

1. **Inicialización** → `.gitignore`, `README.md`
2. **Config Backend** → `.env.example`, `requirements.txt`, `dependencies.py`
3. **Modelos** → `models/`, `schemas/`
4. **Configuración** → `config/`
5. **Adaptadores** → `adapters/`
6. **Servicios** → `services/`
7. **API Endpoints** → `routers/`, `main.py`
8. **Scripts** → `scripts/`, utilidades backend
9. **Frontend Base** → configuración Vue/Vite
10. **Frontend Completo** → componentes, vistas, servicios
11. **Docs** → documentación SQL y guías

---

## 📝 Notas Importantes

- ✅ El `.gitignore` excluye automáticamente:
  - `venv/`, `node_modules/`
  - `.env` (pero incluye `.env.example`)
  - `*.db`, `__pycache__/`
  - Archivos de IDEs y sistema operativo

- ✅ Cada commit es funcional y tiene un propósito claro
- ✅ Los mensajes siguen Conventional Commits (feat, docs, etc.)
- ✅ El orden permite entender la arquitectura progresivamente

---

## 🚀 Ejecución Rápida

Copia y pega cada bloque de comandos en orden.
Espera a que cada `git push` termine antes de continuar con el siguiente.
