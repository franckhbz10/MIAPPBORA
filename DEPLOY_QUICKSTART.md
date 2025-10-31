# 🚀 Guía Rápida de Despliegue

## ✅ Archivos Preparados

### Backend
- ✅ `Procfile` - Railway ejecutará `uvicorn main:app`
- ✅ `runtime.txt` - Python 3.11.9
- ✅ `.env.railway.example` - Template de variables
- ✅ `main.py` - CORS dinámico con `FRONTEND_URL`
- ✅ Nuevo SECRET_KEY generado

### Frontend
- ✅ `.env.production` - Template para Vercel
- ✅ `vercel.json` - Configuración SPA routing
- ✅ `api.js` - Usa `VITE_API_URL` dinámico
- ✅ Build exitoso verificado

---

## 🎯 Siguiente: Deploy en Railway (Backend)

### Paso 1: Preparar repositorio
```bash
git add .
git commit -m "feat: preparar para deploy en Railway y Vercel"
git push origin main
```

### Paso 2: Crear proyecto en Railway

1. Ve a https://railway.app/ → Login con GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Selecciona `franckhbz10/MIAPPBORA`
4. Click "Deploy Now"

### Paso 3: Configurar Backend

**Settings → General:**
- Root Directory: `backend`
- Watch Paths: `backend/**`

**Variables → Add Variables:**

Copiar TODAS estas variables (reemplazar valores con los tuyos):

```bash
DEBUG=false
SECRET_KEY=9nGZrlntgpRBGhw0IP33c1byLvwGBTzBulHyuxwDYcHIMNjiTEyDUyqsgZEUg9-THXdgcNZy38CtG6NLV9P2qA

# Database
DATABASE_URL=postgresql://postgres.[TU-PROYECTO]:[TU-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
POSTGRES_URL=postgresql://postgres.[TU-PROYECTO]:[TU-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Supabase
SUPABASE_URL=https://[TU-PROYECTO].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI (CRÍTICO)
OPENAI_API_KEY=sk-proj-...
OPENAI_ENABLED=true
OPENAI_MODEL=gpt-5-nano-2025-08-07

# Vectores 1536 (CRÍTICO)
USE_EMBEDDING_API=true
USE_VECTOR_1536=true
EMBEDDING_DIMENSION=1536
EMBEDDING_API_MODEL=text-embedding-3-small

# LLM
LLM_PROVIDER=openai
ALLOW_HF_LLM_FALLBACK=false

# JWT
JWT_SECRET=9nGZrlntgpRBGhw0IP33c1byLvwGBTzBulHyuxwDYcHIMNjiTEyDUyqsgZEUg9-THXdgcNZy38CtG6NLV9P2qA
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS (actualizar después con URL de Vercel)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### Paso 4: Validar Deploy

1. Esperar que termine el build (~3-5 min)
2. Click en el dominio generado (ej: `miappbora-production.up.railway.app`)
3. Agregar `/health/connections` a la URL
4. Deberías ver JSON con status "healthy"

**URL del backend**: `https://[tu-proyecto].up.railway.app`

⚠️ **COPIAR esta URL**, la necesitas para Vercel.

---

## 🎯 Siguiente: Deploy en Vercel (Frontend)

### Paso 1: Crear proyecto en Vercel

1. Ve a https://vercel.com/ → Login con GitHub
2. Click "Add New..." → "Project"
3. Import `franckhbz10/MIAPPBORA`
4. Click "Import"

### Paso 2: Configurar Frontend

**Configure Project:**
- Framework Preset: `Vite`
- Root Directory: `frontend`
- Build Command: `npm run build` (autodetectado)
- Output Directory: `dist` (autodetectado)
- Install Command: `npm ci`

**Environment Variables → Add:**
```bash
VITE_API_URL=https://[TU-BACKEND].up.railway.app
```

⚠️ Reemplazar `[TU-BACKEND]` con la URL de Railway (SIN `/api` al final)

Ejemplo: `https://miappbora-production.up.railway.app`

**Nota**: El frontend ya está configurado para usar URLs dinámicas. No necesitas modificar código.

### Paso 3: Deploy

1. Click "Deploy"
2. Esperar build (~1-2 min)
3. Vercel generará URL: `https://miappbora.vercel.app`

---

## 🔗 Conectar Backend + Frontend (CORS)

### Volver a Railway

1. Variables → Editar `CORS_ORIGINS`
2. Cambiar a:
```json
["https://miappbora.vercel.app","https://www.miappbora.vercel.app","http://localhost:3000","http://localhost:5173"]
```

3. Agregar nueva variable:
```bash
FRONTEND_URL=https://miappbora.vercel.app
```

4. Railway redeplegará automáticamente

---

## ✅ Verificar Todo Funciona

### Backend
- [ ] `https://[backend].railway.app/health/connections` → 200 OK
- [ ] Logs muestran: "Servidor listo en modo PRODUCCIÓN"
- [ ] Logs muestran: "✓ OpenAI disponible"
- [ ] Logs muestran: "✓ Frontend de producción configurado"

### Frontend
- [ ] `https://[tu-app].vercel.app` carga correctamente
- [ ] Console (F12) sin errores CORS
- [ ] Network tab: requests van a Railway
- [ ] Login funciona
- [ ] Mentor Bora responde

### Integración
- [ ] Búsqueda lexicón retorna resultados
- [ ] Mentor Bora usa contexto Bora
- [ ] Railway logs muestran `match_lexicon_v2` (vectores 1536)

---

## 🚨 Si algo falla

### Error: "OpenAI API key not configured"
→ Verificar `OPENAI_API_KEY` en Railway Variables

### Error: "CORS policy blocked"
→ Verificar `CORS_ORIGINS` incluye dominio de Vercel

### Error: "Failed to fetch"
→ Verificar `VITE_API_URL` en Vercel apunta a Railway

### Build falla en Railway
→ Revisar logs, posiblemente falta variable crítica

### Timeout en RAG queries
→ Normal, OpenAI puede demorar 5-15s

---

## 📊 Monitoreo Post-Deploy

### Railway
- Dashboard → Metrics: CPU, Memory, Requests
- Logs: errores OpenAI, queries lentas

### Vercel
- Analytics: pageviews, API calls
- Logs: errores frontend

### Costos
- Railway Hobby: $5/mes (primeros 500 hrs)
- Vercel Hobby: Gratis
- OpenAI: ~$0.002 por búsqueda + ~$0.001 por mensaje

**Total**: ~$10-30/mes para 1000 usuarios activos

---

## 🎉 ¡Listo!

Tu app está en producción:
- Frontend: `https://tu-app.vercel.app`
- Backend: `https://tu-backend.railway.app`
- Database: Supabase (ya configurado)
- Embeddings: OpenAI 1536 dims activo

**Próximos pasos:**
1. Configurar dominio custom en Vercel (opcional)
2. Monitorear métricas primeras 24h
3. Ajustar timeouts si es necesario
4. Considerar upgrade Railway si excedes 512MB RAM
