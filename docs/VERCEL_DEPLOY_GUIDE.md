# 🚀 Deploy Frontend en Vercel - Guía Rápida

## ✅ Pre-requisitos Completados

- ✅ Backend desplegado en Railway: https://miappbora-production.up.railway.app
- ✅ Frontend configurado para usar API de Railway
- ✅ Build exitoso (196.74 KB gzip)
- ✅ URLs dinámicas implementadas (config/api.js)

---

## 📝 Paso 1: Deploy en Vercel

### 1.1 Ir a Vercel
1. Ve a **[vercel.com](https://vercel.com)**
2. Haz click en **"New Project"**
3. Si no has conectado GitHub, haz click en **"Connect Git Provider"** → GitHub

### 1.2 Importar Repositorio
1. Busca **`franckhbz10/MIAPPBORA`**
2. Haz click en **"Import"**

### 1.3 Configurar Proyecto
```
Project Name:        miappbora-frontend (o el que prefieras)
Framework Preset:    Vite
Root Directory:      frontend
Build Command:       npm run build
Output Directory:    dist
Install Command:     npm install
```

### 1.4 Configurar Variables de Entorno
⚠️ **CRÍTICO**: Antes de hacer click en "Deploy", agrega esta variable:

1. Click en **"Environment Variables"** (expandir sección)
2. Agregar:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://miappbora-production.up.railway.app`
   - **Environment**: Production ✅ (debe estar marcado)

3. Click en **"Add"**

### 1.5 Deploy
1. Click en **"Deploy"**
2. Espera ~2-3 minutos
3. ✅ Vercel mostrará: **"Your project has been deployed"**

---

## 🔗 Paso 2: Configurar CORS en Railway

Una vez que Vercel termine el deploy, te dará una URL como:
```
https://miappbora-frontend-xxxx.vercel.app
```

Copia esa URL y:

### 2.1 Ir a Railway Dashboard
1. Ve a [railway.app](https://railway.app)
2. Abre tu proyecto **miappbora-production**
3. Click en el servicio (backend)
4. Click en **"Variables"** (en el menú lateral)

### 2.2 Agregar Variables de CORS
Agrega o actualiza estas variables:

**FRONTEND_URL**:
```
https://miappbora-frontend-xxxx.vercel.app
```
(Reemplaza con tu URL real de Vercel, **sin trailing slash**)

**CORS_ORIGINS**:
```json
["https://miappbora-frontend-xxxx.vercel.app"]
```
(⚠️ Debe ser un **array JSON válido** con la URL entre comillas)

### 2.3 Redeploy Automático
Railway detectará los cambios y hará redeploy automáticamente (~2 min).

---

## ✅ Paso 3: Verificar Integración

### 3.1 Abrir Frontend en Vercel
1. Ve a tu URL de Vercel: `https://miappbora-frontend-xxxx.vercel.app`
2. Abre **DevTools del navegador** (F12)
3. Ve a la pestaña **"Console"**

### 3.2 Verificar que NO haya errores CORS
✅ **Correcto**: Sin mensajes de error CORS
❌ **Incorrecto**: Errores como "blocked by CORS policy"

Si hay errores CORS:
- Verifica que CORS_ORIGINS en Railway tenga la URL exacta de Vercel
- Verifica que FRONTEND_URL esté configurada
- Espera 2-3 min para que Railway termine el redeploy

### 3.3 Probar Funcionalidades

1. **Healthcheck**:
   - Abre: `https://tu-vercel-app.vercel.app`
   - La app debe cargar sin errores

2. **Registro**:
   - Click en "Registrarse"
   - Llena el formulario
   - Submit
   - ✅ Debe registrar exitosamente

3. **Login**:
   - Ingresa credenciales
   - ✅ Debe iniciar sesión

4. **Mentor Bora**:
   - Ve a la sección Mentor
   - Escribe: "¿Cómo se dice hola en Bora?"
   - ✅ Debe responder con contexto Bora (búsqueda vectorial 1536 dims)

5. **Lexicón**:
   - Ve a la sección Lexicón
   - Busca: "agua"
   - ✅ Debe mostrar resultados de búsqueda semántica

---

## 🐛 Troubleshooting

### Error: "Network Error" o "Failed to fetch"

**Causa**: Frontend no puede conectarse al backend

**Solución**:
1. Verifica que VITE_API_URL esté configurada en Vercel
2. Ve a Vercel → Settings → Environment Variables
3. Confirma que existe: `VITE_API_URL = https://miappbora-production.up.railway.app`
4. Si falta o está mal, agrégala/corrígela
5. Redeploy: Vercel → Deployments → Menú (•••) → Redeploy

### Error: CORS "Access-Control-Allow-Origin"

**Causa**: Railway no tiene configurado el dominio de Vercel en CORS

**Solución**:
1. Ve a Railway → Variables
2. Verifica CORS_ORIGINS: debe ser un array JSON válido
3. Correcto: `["https://tu-app.vercel.app"]`
4. Incorrecto: `https://tu-app.vercel.app` (sin corchetes)
5. Railway hará redeploy automático

### Frontend carga pero muestra localhost:8000

**Causa**: Build del frontend no tomó VITE_API_URL

**Solución**:
1. Vercel → Settings → Environment Variables
2. Confirma que VITE_API_URL esté en "Production"
3. Vercel → Deployments → Redeploy (para rebuild con la variable)

---

## 📊 Monitoreo Post-Deploy

### Railway Logs
```bash
# Deberías ver peticiones desde Vercel:
INFO: "POST /auth/login HTTP/1.1" 200 OK
INFO: "GET /game/phrases HTTP/1.1" 200 OK
INFO: "POST /game/chat HTTP/1.1" 200 OK
```

### Vercel Analytics
- Ve a Vercel → Analytics
- Monitorea: Request rate, Error rate, P95 latency

### Métricas Esperadas
- **P95 Latency**: < 2 segundos
- **Error Rate**: < 1%
- **Mentor Bora Response**: 5-15 segundos
- **Búsqueda Lexicón**: 1-5 segundos

---

## 🎯 URLs Finales

Una vez completado el deploy:

| Servicio | URL |
|----------|-----|
| **Frontend (Vercel)** | https://miappbora-frontend-xxxx.vercel.app |
| **Backend (Railway)** | https://miappbora-production.up.railway.app |
| **API Docs** | https://miappbora-production.up.railway.app/docs |
| **Healthcheck** | https://miappbora-production.up.railway.app/health |

---

## ✅ Checklist Final

- [ ] Deploy en Vercel completado
- [ ] VITE_API_URL configurada en Vercel
- [ ] URL de Vercel copiada
- [ ] CORS_ORIGINS actualizada en Railway
- [ ] FRONTEND_URL actualizada en Railway
- [ ] Railway redeploy completado
- [ ] Frontend abre sin errores CORS
- [ ] Registro funciona
- [ ] Login funciona
- [ ] Mentor Bora responde con contexto
- [ ] Búsqueda lexicón funciona
- [ ] Logs de Railway muestran peticiones desde Vercel

---

## 🎉 ¡Listo!

Tu aplicación MIAPPBORA está ahora **100% en producción**:
- ✅ Backend en Railway (FastAPI + OpenAI + Supabase)
- ✅ Frontend en Vercel (Vue 3 + Vite)
- ✅ Búsqueda vectorial 1536 dimensiones
- ✅ RAG con OpenAI text-embedding-3-small
- ✅ LLM con OpenAI Responses API

**Próximos pasos sugeridos:**
1. Configurar dominio personalizado en Vercel
2. Configurar monitoring (Sentry, LogRocket)
3. Agregar Google Analytics
4. Optimizar images (lazy loading)
5. Implementar caché de respuestas frecuentes
