# 📋 Plan de Despliegue - MIAPPBORA
## Backend (Railway) + Frontend (Vercel)

---

## 🎯 Objetivo
Desplegar exitosamente MIAPPBORA con:
- **Backend** en Railway (Python/FastAPI)
- **Frontend** en Vercel (Vue.js/Vite)
- Migración a vectores 1536 dimensiones activa
- Conexión segura entre servicios

---

## ⚠️ CAMBIOS CRÍTICOS IDENTIFICADOS

### 🔴 **BACKEND - Railway**

#### 1. **Variables de Entorno (.env → Railway)**
**Problema**: Railway necesita todas las variables configuradas en su panel.

**Acción**: Copiar TODAS estas variables desde tu `.env` local:
```bash
# Core
DEBUG=false                              # ⚠️ CAMBIAR a false en producción
SECRET_KEY=<generar-nuevo-token-seguro>  # ⚠️ CAMBIAR por uno nuevo

# Database (Supabase)
DATABASE_URL=<tu-postgres-url-de-supabase>
POSTGRES_URL=<tu-postgres-url-de-supabase>  # mismo valor

# Supabase
SUPABASE_URL=<tu-supabase-url>
SUPABASE_ANON_KEY=<tu-anon-key>
SUPABASE_SERVICE_KEY=<tu-service-role-key>  # ⚠️ IMPORTANTE para backfills

# OpenAI (REQUERIDO para 1536 dims)
OPENAI_API_KEY=<tu-openai-api-key>       # ⚠️ CRÍTICO
OPENAI_ENABLED=true
OPENAI_MODEL=gpt-5-nano-2025-08-07
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=500

# Embeddings 1536 dims (NUEVA MIGRACIÓN)
USE_EMBEDDING_API=true                    # ⚠️ ACTIVAR para OpenAI
USE_VECTOR_1536=true                      # ⚠️ ACTIVAR para usar RPCs v2
EMBEDDING_API_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536                  # ⚠️ CAMBIAR de 384 a 1536

# LLM Provider
LLM_PROVIDER=openai                       # ⚠️ IMPORTANTE
ALLOW_HF_LLM_FALLBACK=false              # sin fallback a HF en prod

# CORS (permitir Vercel)
CORS_ORIGINS=["https://tu-app.vercel.app","http://localhost:3000","http://localhost:5173"]
# ⚠️ ACTUALIZAR con tu dominio de Vercel después del primer deploy

# Otros
JWT_SECRET=<usar-mismo-SECRET_KEY-o-generar-otro>
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

#### 2. **Archivo `Procfile` (CREAR)**
**Problema**: Railway necesita saber cómo iniciar la app.

**Archivo**: `backend/Procfile`
```procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```
- Railway asigna dinámicamente `$PORT`
- Uvicorn escucha en todas las interfaces (`0.0.0.0`)

#### 3. **CORS Dinámico en Producción**
**Problema**: El dominio de Vercel no está hardcodeado en `settings.py`.

**Solución**: Actualizar `CORS_ORIGINS` en Railway después del deploy de Vercel.

**Alternativa (Código)**: Agregar validación dinámica en `main.py`:
```python
# En main.py, línea ~135
import os

# Añadir dominio de Vercel dinámicamente
vercel_url = os.getenv("FRONTEND_URL")
if vercel_url and vercel_url not in allowed_origins:
    allowed_origins.append(vercel_url)
    logger.info(f"Añadiendo frontend de producción: {vercel_url}")
```

Luego agregar en Railway:
```bash
FRONTEND_URL=https://tu-app.vercel.app
```

#### 4. **Optimización de Dependencias**
**Problema**: `torch==2.1.0` es muy pesado (~800MB) y solo se usa para HuggingFace local.

**Acción**: Como ahora usas OpenAI embeddings, puedes:
- **Opción A** (Segura): Dejarlo por si necesitas fallback
- **Opción B** (Optimizada): Comentar en `requirements.txt`:
```txt
# torch==2.1.0  # Solo necesario para HF local (deshabilitado en prod)
```

⚠️ **RIESGO**: Si falla OpenAI y `ALLOW_HF_LLM_FALLBACK=true`, el app crasheará.

**Recomendación**: Dejarlo y monitorear uso de memoria en Railway.

#### 5. **Verificar `runtime.txt`**
**Estado**: ✅ Ya existe con `python-3.11.9`

#### 6. **Health Check Endpoint**
**Estado**: ✅ Ya existe en `/health/connections`

Railway lo usará para validar despliegue exitoso.

---

### 🔵 **FRONTEND - Vercel**

#### 1. **Variable de Entorno para API**
**Problema**: Hardcoded `baseURL: '/api'` no funciona en producción.

**Archivo**: `frontend/.env.production` (CREAR)
```bash
VITE_API_URL=https://tu-backend.up.railway.app/api
```

**Cambio en código**: `frontend/src/services/api.js`
```javascript
// Línea 8-9
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',  // ⚠️ CAMBIAR
  timeout: 30000,
  // ...
})
```

Esto permite:
- **Desarrollo**: usa proxy local (`/api` → `http://127.0.0.1:8000`)
- **Producción**: usa URL completa de Railway

#### 2. **Configuración de Build**
**Estado**: ✅ Ya configurado en `vite.config.js`:
```javascript
build: {
  target: 'es2022'  // Fix para Top-Level Await
}
```

#### 3. **Vercel Settings** (en dashboard)
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm ci` (recomendado sobre `npm install`)

#### 4. **Variables de Entorno en Vercel**
Agregar en Vercel Dashboard → Settings → Environment Variables:
```bash
VITE_API_URL=https://tu-backend.up.railway.app
```

⚠️ Actualizar después de obtener URL de Railway.

---

## 📝 CHECKLIST DE DESPLIEGUE

### **Fase 1: Preparación Backend**
- [ ] 1.1. Crear `backend/Procfile`
- [ ] 1.2. Revisar `.gitignore` (no subir `.env`)
- [ ] 1.3. Generar nuevo `SECRET_KEY` seguro
- [ ] 1.4. (Opcional) Optimizar `requirements.txt` (comentar torch)
- [ ] 1.5. Commit y push a GitHub

### **Fase 2: Deploy Backend en Railway**
- [ ] 2.1. Crear proyecto en Railway
- [ ] 2.2. Conectar repositorio GitHub
- [ ] 2.3. Configurar "Root Directory" = `backend`
- [ ] 2.4. Configurar TODAS las variables de entorno (ver lista arriba)
- [ ] 2.5. Validar que `USE_VECTOR_1536=true` y `USE_EMBEDDING_API=true`
- [ ] 2.6. Deploy inicial
- [ ] 2.7. Verificar logs: "Servidor listo en modo PRODUCCIÓN"
- [ ] 2.8. Probar endpoint: `https://tu-backend.railway.app/health/connections`
- [ ] 2.9. Copiar URL de Railway (ejemplo: `miappbora-production.up.railway.app`)

### **Fase 3: Preparación Frontend**
- [ ] 3.1. Crear `frontend/.env.production`
- [ ] 3.2. Actualizar `api.js` con fallback dinámico
- [ ] 3.3. Build local para validar: `cd frontend && npm run build`
- [ ] 3.4. Verificar no hay errores de TypeScript/ESLint
- [ ] 3.5. Commit y push a GitHub

### **Fase 4: Deploy Frontend en Vercel**
- [ ] 4.1. Crear proyecto en Vercel
- [ ] 4.2. Conectar repositorio GitHub
- [ ] 4.3. Configurar "Root Directory" = `frontend`
- [ ] 4.4. Framework Preset = Vite
- [ ] 4.5. Agregar variable: `VITE_API_URL=https://tu-backend.railway.app`
- [ ] 4.6. Deploy inicial
- [ ] 4.7. Verificar build exitoso
- [ ] 4.8. Copiar URL de Vercel (ejemplo: `miappbora.vercel.app`)

### **Fase 5: Integración CORS**
- [ ] 5.1. Volver a Railway
- [ ] 5.2. Actualizar variable `CORS_ORIGINS`:
```json
["https://miappbora.vercel.app","https://www.miappbora.vercel.app"]
```
- [ ] 5.3. Redeploy backend (Railway detecta cambio automáticamente)
- [ ] 5.4. Verificar logs: CORS incluye dominio de Vercel

### **Fase 6: Pruebas End-to-End**
- [ ] 6.1. Abrir `https://tu-app.vercel.app`
- [ ] 6.2. Verificar Network tab: peticiones van a Railway
- [ ] 6.3. Probar registro/login
- [ ] 6.4. Probar Mentor Bora (chat con RAG)
- [ ] 6.5. Verificar búsqueda lexicón usa vectores 1536
- [ ] 6.6. Probar minijuegos
- [ ] 6.7. Validar no hay errores CORS en consola

### **Fase 7: Monitoreo Post-Deploy**
- [ ] 7.1. Railway Metrics: CPU, Memoria, Request rate
- [ ] 7.2. Vercel Analytics: Page loads, API calls
- [ ] 7.3. Logs de Railway: errores OpenAI, timeouts
- [ ] 7.4. Costos OpenAI: embedding calls (~1000 tokens por query)

---

## 🚨 PROBLEMAS COMUNES Y SOLUCIONES

### Backend (Railway)

#### Error: "OpenAI API key not configured"
**Causa**: Variable `OPENAI_API_KEY` no está en Railway.
**Fix**: Agregar en Variables de Entorno.

#### Error: "No module named 'sentence-transformers'"
**Causa**: `requirements.txt` no se instaló correctamente.
**Fix**: Verificar logs de build, reiniciar deploy.

#### Error: "CORS policy blocked"
**Causa**: Dominio de Vercel no está en `CORS_ORIGINS`.
**Fix**: Actualizar variable en Railway.

#### Error: "Connection refused" (DATABASE_URL)
**Causa**: Formato incorrecto de `DATABASE_URL`.
**Fix**: Debe ser `postgresql://postgres.[project]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`

#### Timeout en requests RAG
**Causa**: OpenAI + búsqueda vectorial puede tomar >10s.
**Fix**: Ya configurado en `api.js` (timeout: 30000ms).

### Frontend (Vercel)

#### Error: "Failed to fetch" en producción
**Causa**: `VITE_API_URL` apunta a localhost.
**Fix**: Verificar variable en Vercel apunta a Railway.

#### Build falla con "Top-level await"
**Causa**: Target ES2020 no soporta TLA.
**Fix**: Ya configurado (`target: 'es2022'` en `vite.config.js`).

#### 404 en rutas Vue Router
**Causa**: Vercel no redirige SPAs correctamente.
**Fix**: Crear `frontend/vercel.json`:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 📊 MÉTRICAS ESPERADAS (Producción)

### Backend
- **Startup time**: 15-25 segundos (con OpenAI check)
- **Memory**: 250-400 MB (con torch), 80-150 MB (sin torch)
- **Request latency**:
  - `/health`: <100ms
  - `/api/lexicon/search`: 2-5s (OpenAI + vector search)
  - Mentor Bora: 5-15s (RAG + LLM generation)

### Frontend
- **Build time**: 30-60 segundos
- **Bundle size**: ~500KB gzip
- **First Contentful Paint**: <1.5s
- **Time to Interactive**: <3s

### Costos Estimados (OpenAI)
- **Embeddings** (text-embedding-3-small):
  - $0.020 por 1M tokens
  - ~100 tokens por query
  - **≈ $0.002 por búsqueda**
  
- **LLM** (gpt-5-nano-2025-08-07):
  - Depende del contexto RAG
  - ~500-1500 tokens por respuesta
  - **≈ $0.0005-0.0015 por mensaje**

**Proyección**: 1000 usuarios/mes activos → $5-15/mes OpenAI

---

## 🔄 ROLLBACK PLAN (Si falla en producción)

### Backend
1. Railway Dashboard → Deployments
2. Seleccionar deploy anterior estable
3. Click "Redeploy"
4. Downtime: ~30 segundos

### Frontend
1. Vercel Dashboard → Deployments
2. Hover sobre deploy anterior
3. Click "..." → Promote to Production
4. Downtime: instantáneo (Vercel Edge)

### Migración Vectores
Si `USE_VECTOR_1536=true` causa problemas:
1. Railway Variables → `USE_VECTOR_1536=false`
2. Redeploy automático
3. Volverá a usar RPCs v1 (384 dims)

**⚠️ NOTA**: Los datos 1536 ya están en BD, no se pierden.

---

## ✅ CRITERIOS DE ÉXITO

- [x] Backend responde en `/health/connections` con status 200
- [x] Frontend carga sin errores CORS en consola
- [x] Login/Registro funcional
- [x] Mentor Bora genera respuestas con contexto Bora
- [x] Búsqueda lexicón retorna resultados relevantes
- [x] Logs Railway muestran uso de `match_lexicon_v2` (1536 dims)
- [x] No hay errores OpenAI (401, 429, timeout)
- [x] Latencia < 5s para búsquedas lexicón
- [x] Latencia < 15s para Mentor Bora
- [x] Memory usage < 512MB Railway (plan Hobby)

---

## 📞 SOPORTE

- **Railway Docs**: https://docs.railway.app/
- **Vercel Docs**: https://vercel.com/docs
- **OpenAI Status**: https://status.openai.com/
- **Supabase Status**: https://status.supabase.com/

---

**Última actualización**: 2025-10-30  
**Versión del plan**: 1.0  
**Migración activa**: Vectores 1536 dims + OpenAI Embeddings API
