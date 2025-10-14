# MIAPPBORA - Aplicación de Aprendizaje del Idioma Bora 🌿

Aplicación web gamificada para aprender frases cotidianas en Bora, una lengua indígena de la Amazonía peruana.

## 🚀 Inicio Rápido

### Verificar Conexiones con Supabase

Esta guía te ayudará a verificar que todo esté configurado correctamente.

## 📋 Pre-requisitos

- Python 3.8+ < 3.13 instalado
- Node.js 16+ instalado
- Cuenta en [Supabase](https://supabase.com) (gratis)
- Cuenta en [HuggingFace](https://huggingface.co) (gratis)

## 🔧 Configuración del Backend

### 1. Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# Supabase (obtener en https://supabase.com)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-anon-key-aqui
SUPABASE_SERVICE_KEY=tu-service-role-key-aqui

# HuggingFace (obtener en https://huggingface.co/settings/tokens)
HUGGINGFACE_API_KEY=hf_tu_token_aqui
```

### 3. Obtener Credenciales de Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Crea un nuevo proyecto llamado "miappbora"
3. Ve a **Settings** → **API**
4. Copia:
   - **URL** del proyecto
   - **anon/public** key
   - **service_role** key (opcional, para admin)

### 4. Obtener Token de HuggingFace

1. Ve a [huggingface.co](https://huggingface.co)
2. Crea cuenta o inicia sesión
3. Ve a **Settings** → **Access Tokens**
4. Crea nuevo token con permiso de **Read**
5. Copia el token

### 5. Iniciar el Backend

```bash
cd backend
python main.py
```

O con uvicorn:

```bash
uvicorn main:app --reload
```

El servidor estará en: **http://localhost:8000**

## 🎨 Configuración del Frontend

### 1. Instalar Dependencias

```bash
cd frontend
npm install
```

### 2. Iniciar el Frontend

```bash
npm run dev
```

El frontend estará en: **http://localhost:3000**

## ✅ Verificar Conexiones

### Opción 1: Desde el Frontend

1. Abre **http://localhost:3000**
2. Verás una página con el estado de todos los servicios
3. Haz clic en "Verificar Estado" para refrescar

### Opción 2: Desde el Backend (API)

Visita en tu navegador:

- **Health básico**: http://localhost:8000/health/
- **Todas las conexiones**: http://localhost:8000/health/connections
- **Solo Supabase**: http://localhost:8000/health/supabase
- **Solo HuggingFace**: http://localhost:8000/health/huggingface

### Opción 3: Documentación Interactiva

Visita: **http://localhost:8000/docs**

Podrás probar todos los endpoints directamente.

## 🎯 Interpretación de Resultados

### Estados Posibles

- ✅ **connected/ok**: Servicio funcionando correctamente
- ⚠️ **degraded**: Servicio con advertencias
- ❌ **error/disconnected**: Servicio no disponible

### Problemas Comunes

#### Supabase No Configurado

```
status: "disconnected"
message: "Supabase no configurado. Revisa .env"
```

**Solución**: Verifica que `.env` tiene `SUPABASE_URL` y `SUPABASE_ANON_KEY`

#### HuggingFace Error al Cargar Modelo

```
status: "error"
message: "Modelo de embeddings no cargado"
```

**Solución**: 
- Verifica conexión a internet
- Puede tardar en la primera carga (descarga el modelo)
- Revisa espacio en disco

#### Error de Conexión

```
"No se pudo conectar con el servidor"
```

**Solución**: Verifica que el backend esté corriendo en puerto 8000

## 📊 Estructura del Proyecto

```
miappbora/
├── backend/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── config/
│   │   ├── settings.py      # Configuración central
│   │   └── database_connection.py
│   ├── models/              # Modelos ORM
│   ├── schemas/             # Validación Pydantic
│   ├── routers/             # Endpoints API
│   │   ├── health_router.py    # ✅ Verificación de servicios
│   │   └── auth_router.py      # Autenticación
│   ├── services/            # Lógica de negocio
│   │   ├── auth_service.py
│   │   └── rag_service.py
│   ├── adapters/            # Integraciones externas
│   │   ├── supabase_adapter.py  # ✅ Conexión Supabase
│   │   └── huggingface_adapter.py # ✅ Modelos IA
│   ├── requirements.txt     # Dependencias Python
│   └── .env.example         # Plantilla configuración
│
└── frontend/
    ├── src/
    │   ├── views/
    │   │   └── HealthCheck.vue  # ✅ Vista de verificación
    │   ├── services/
    │   │   ├── api.js
    │   │   └── healthService.js # ✅ Servicio de health check
    │   ├── App.vue
    │   └── main.js
    ├── package.json
    └── vite.config.js
```

## 🔍 Endpoints Disponibles

### Health Check

- `GET /` - Información básica
- `GET /health/` - Estado del servidor
- `GET /health/connections` - Todas las conexiones
- `GET /health/supabase` - Solo Supabase
- `GET /health/huggingface` - Solo HuggingFace

### Autenticación (Próximamente)

- `POST /auth/register` - Registro
- `POST /auth/login` - Login
- `GET /auth/me` - Usuario actual

## 📝 Próximos Pasos

Una vez que veas ✅ en Supabase y HuggingFace:

1. **Crear tablas en Supabase** (siguiente paso)
2. **Cargar corpus Bora** en la base de datos
3. **Implementar RAG** para el chat
4. **Desarrollar minijuegos**
5. **Sistema de gamificación**

## 🆘 Soporte

Si tienes problemas:

1. Revisa los logs del backend en la terminal
2. Verifica que todas las variables de entorno estén configuradas
3. Consulta la documentación interactiva en `/docs`
4. Revisa el estado detallado en `/health/connections`

## 📄 Licencia

Proyecto educativo para el aprendizaje del idioma Bora.
