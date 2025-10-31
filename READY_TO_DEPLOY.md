# ✅ PREPARACIÓN COMPLETADA - Listo para Deploy

**Fecha**: 2025-10-30  
**Commit**: `a9b65e9` - feat: preparar para deploy en Railway y Vercel  
**Estado**: 🟢 TODO LISTO PARA PRODUCCIÓN

---

## 📦 Archivos Creados/Modificados

### Backend (Railway Ready)
```
✅ backend/Procfile                  ← Railway sabe cómo arrancar el servidor
✅ backend/.env.railway.example      ← Template con TODAS las variables
✅ backend/main.py                   ← CORS dinámico con FRONTEND_URL
✅ .gitignore                        ← Actualizado (no sube .env)
```

### Frontend (Vercel Ready)
```
✅ frontend/vercel.json              ← SPA routing + cache headers
✅ frontend/.env.production          ← Template con VITE_API_URL
✅ frontend/src/services/api.js      ← Usa variable dinámica
✅ frontend/dist/                    ← Build exitoso (196KB gzip)
```

### Documentación
```
✅ PLAN_DESPLIEGUE.md               ← Plan completo con troubleshooting
✅ DEPLOY_QUICKSTART.md             ← Guía paso a paso
```

---

## 🔐 Credenciales Generadas

### SECRET_KEY (Producción)
```bash
SECRET_KEY=9nGZrlntgpRBGhw0IP33c1byLvwGBTzBulHyuxwDYcHIMNjiTEyDUyqsgZEUg9-THXdgcNZy38CtG6NLV9P2qA
```

⚠️ **IMPORTANTE**: Usa esta nueva clave en Railway (NO uses la de desarrollo)

---

## 🎯 Variables CRÍTICAS para Railway

**COPIAR estas 10 variables al Railway Dashboard:**

```bash
# 1. CORE
DEBUG=false
SECRET_KEY=9nGZrlntgpRBGhw0IP33c1byLvwGBTzBulHyuxwDYcHIMNjiTEyDUyqsgZEUg9-THXdgcNZy38CtG6NLV9P2qA

# 2. DATABASE (Supabase)
DATABASE_URL=postgresql://postgres.[TU-PROYECTO]:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
POSTGRES_URL=postgresql://postgres.[TU-PROYECTO]:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# 3. SUPABASE
SUPABASE_URL=https://[TU-PROYECTO].supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_KEY=eyJhbGci...

# 4. OPENAI (SIN ESTO EL APP NO ARRANCA)
OPENAI_API_KEY=sk-proj-...
OPENAI_ENABLED=true

# 5. VECTORES 1536 (SIN ESTO USA VECTORES VIEJOS 384)
USE_EMBEDDING_API=true
USE_VECTOR_1536=true
EMBEDDING_DIMENSION=1536

# 6. LLM
LLM_PROVIDER=openai
ALLOW_HF_LLM_FALLBACK=false

# 7. JWT
JWT_SECRET=9nGZrlntgpRBGhw0IP33c1byLvwGBTzBulHyuxwDYcHIMNjiTEyDUyqsgZEUg9-THXdgcNZy38CtG6NLV9P2qA

# 8. CORS (actualizar después con URL de Vercel)
CORS_ORIGINS=["http://localhost:3000"]

# 9. FRONTEND (actualizar después de Vercel)
FRONTEND_URL=https://miappbora.vercel.app
```

---

## 📝 Checklist Pre-Deploy

### ✅ Completado
- [x] Repositorio actualizado en GitHub
- [x] Procfile para Railway
- [x] CORS dinámico configurado
- [x] Frontend build exitoso
- [x] Variables de entorno documentadas
- [x] .gitignore actualizado (no sube secretos)
- [x] Documentación completa

### 🔜 Siguiente: Deploy Backend
- [ ] Ir a https://railway.app/
- [ ] Login con GitHub
- [ ] New Project → Deploy from GitHub
- [ ] Seleccionar `franckhbz10/MIAPPBORA`
- [ ] Root Directory: `backend`
- [ ] Copiar las 10 variables críticas
- [ ] Esperar build (~3-5 min)
- [ ] Validar: `https://[tu-proyecto].railway.app/health/connections`
- [ ] **COPIAR URL de Railway** para siguiente paso

### 🔜 Siguiente: Deploy Frontend
- [ ] Ir a https://vercel.com/
- [ ] Login con GitHub
- [ ] New Project → Import
- [ ] Seleccionar `franckhbz10/MIAPPBORA`
- [ ] Root Directory: `frontend`
- [ ] Framework: Vite (autodetectado)
- [ ] Variable: `VITE_API_URL=https://[tu-backend].railway.app`
- [ ] Deploy
- [ ] **COPIAR URL de Vercel** para siguiente paso

### 🔜 Configurar CORS
- [ ] Volver a Railway
- [ ] Variables → Editar `CORS_ORIGINS`
- [ ] Agregar: `["https://tu-app.vercel.app"]`
- [ ] Agregar variable: `FRONTEND_URL=https://tu-app.vercel.app`
- [ ] Railway redesplegará automáticamente

---

## 🎯 Criterios de Éxito

### Backend (Railway)
```
✅ Status 200 en /health/connections
✅ Logs: "Servidor listo en modo PRODUCCIÓN"
✅ Logs: "✓ OpenAI disponible (gpt-5-nano-2025-08-07)"
✅ Logs: "✓ Frontend de producción configurado: https://..."
✅ Memory < 512MB
✅ No errores en logs
```

### Frontend (Vercel)
```
✅ Build exitoso < 60s
✅ App carga sin errores
✅ Console (F12) sin errores CORS
✅ Network: requests van a Railway
✅ First Load < 3s
```

### Integración
```
✅ Login/Registro funcional
✅ Mentor Bora responde con contexto Bora
✅ Búsqueda lexicón retorna resultados
✅ Railway logs: "match_lexicon_v2" (vectores 1536)
✅ Latencias < 15s para Mentor
✅ Latencias < 5s para búsquedas
```

---

## 🚨 Troubleshooting Común

### Railway
**"Application failed to respond"**
→ Verificar `Procfile` existe en `backend/`
→ Verificar logs: posible error en variables

**"OpenAI API key not configured"**
→ Falta `OPENAI_API_KEY` en Variables

**"Database connection failed"**
→ Verificar formato `DATABASE_URL` (debe ser pooler de Supabase)

### Vercel
**"Failed to fetch"**
→ Verificar `VITE_API_URL` apunta a Railway (sin `/api` al final)

**Build falla**
→ Verificar Node version (debe usar 18+)

**404 en rutas Vue**
→ Verificar `vercel.json` existe en `frontend/`

### CORS
**"CORS policy blocked"**
→ Actualizar `CORS_ORIGINS` en Railway con dominio de Vercel
→ Agregar variable `FRONTEND_URL`

---

## 💰 Costos Estimados

| Servicio | Plan | Costo/mes |
|----------|------|-----------|
| Railway | Hobby | $5 |
| Vercel | Hobby | Gratis |
| OpenAI API | Pay-as-go | $5-15 |
| **TOTAL** | | **$10-30** |

Para 1000 usuarios activos/mes

---

## 📚 Documentos de Referencia

- `DEPLOY_QUICKSTART.md` - Pasos específicos con capturas
- `PLAN_DESPLIEGUE.md` - Plan completo con troubleshooting
- `backend/.env.railway.example` - Template de variables

---

## 🎉 SIGUIENTE PASO

**Abre en tu navegador**: https://railway.app/

Y sigue la guía en `DEPLOY_QUICKSTART.md` 🚀

---

**¿Necesitas ayuda?**
- Railway Docs: https://docs.railway.app/
- Vercel Docs: https://vercel.com/docs
- GitHub Repo: https://github.com/franckhbz10/MIAPPBORA
