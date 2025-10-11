# 🚀 Guía de Instalación - MIAPPBORA

## 📋 Requisitos Previos

### Software Necesario
- **Node.js** v18 o superior → [Descargar](https://nodejs.org/)
- **Python** 3.11 o superior → [Descargar](https://www.python.org/)
- **Git** → [Descargar](https://git-scm.com/)
- **Visual Studio Code** (recomendado) → [Descargar](https://code.visualstudio.com/)

### Cuentas Necesarias
- **Supabase** (gratuita) → [Registrarse](https://supabase.com)
- **Hugging Face** (gratuita) → [Registrarse](https://huggingface.co)

---

## 📦 Paso 1: Clonar/Descargar el Proyecto

```powershell
# Si tienes el proyecto en Git
git clone <url-del-repositorio>
cd miappbora

# O simplemente navega a la carpeta del proyecto
cd d:\documents\UPC\Ciclo IX\TP1\miappbora
```

---

## 🔧 Paso 2: Configurar Backend (Python/FastAPI)

### 2.1 Navegar a la carpeta backend
```powershell
cd backend
```

### 2.2 Crear entorno virtual
```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Si hay error de permisos, ejecutar primero:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2.3 Instalar dependencias
```powershell
pip install -r requirements.txt
```

**Dependencias principales:**
- `fastapi` - Framework web
- `uvicorn` - Servidor ASGI
- `supabase` - Cliente de Supabase
- `sentence-transformers` - Embeddings para RAG
- `passlib`, `bcrypt` - Encriptación de contraseñas
- `python-jose` - Tokens JWT
- `sqlalchemy` - ORM para base de datos

### 2.4 Configurar variables de entorno

Crea un archivo `.env` en la carpeta `backend/`:

```env
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Hugging Face Configuration (para RAG)
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# JWT Configuration
SECRET_KEY=tu-clave-secreta-super-segura-aqui-cambiar-esto
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://postgres:[TU-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

**¿Cómo obtener las credenciales?**

#### Supabase:
1. Ve a https://supabase.com/dashboard
2. Selecciona tu proyecto (o crea uno nuevo)
3. Ve a **Settings** → **API**
4. Copia:
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_ANON_KEY`
5. Ve a **Settings** → **Database**
6. Copia el **Connection string** → `DATABASE_URL` (reemplaza `[YOUR-PASSWORD]` con tu contraseña)

#### Hugging Face:
1. Ve a https://huggingface.co/settings/tokens
2. Crea un nuevo token (Read access es suficiente)
3. Copia el token → `HUGGINGFACE_API_KEY`

#### SECRET_KEY:
Genera una clave segura aleatoria:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🗄️ Paso 3: Configurar Base de Datos (Supabase)

### 3.1 Habilitar pgvector
En Supabase SQL Editor, ejecuta:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3.2 Crear esquema completo
Copia y ejecuta el script SQL completo que está en:
- `docs/SETUP_SUPABASE.md` (sección "Paso 5: Crear Esquema de Base de Datos")

O ejecuta directamente este comando resumido:

**⚠️ IMPORTANTE - Corrección de la tabla daily_missions:**
Si ya ejecutaste el script pero tienes errores con `daily_missions`, ejecuta:

```sql
-- Opción A: Agregar columnas faltantes (si la tabla ya existe)
ALTER TABLE daily_missions 
ADD COLUMN IF NOT EXISTS mission_name VARCHAR(200) NOT NULL DEFAULT 'Misión';

ALTER TABLE daily_missions 
ADD COLUMN IF NOT EXISTS mission_description TEXT;
```

O:

```sql
-- Opción B: Recrear la tabla completa
DROP TABLE IF EXISTS daily_missions CASCADE;

CREATE TABLE daily_missions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mission_date DATE NOT NULL DEFAULT CURRENT_DATE,
    mission_type VARCHAR(50) NOT NULL,
    mission_name VARCHAR(200) NOT NULL,
    mission_description TEXT,
    target_value INTEGER NOT NULL,
    current_value INTEGER DEFAULT 0,
    points_reward INTEGER DEFAULT 10,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, mission_date, mission_type)
);
```

### 3.3 Poblar datos iniciales (Recompensas)
```powershell
# Desde la carpeta backend/
python scripts/populate_rewards.py
```

Esto creará 16 recompensas predefinidas (badges, avatares, títulos, logros).

### 3.4 Cargar corpus de frases Bora (opcional)
```powershell
python scripts/load_bora_corpus.py
python scripts/generate_embeddings.py
```

---

## 🎨 Paso 4: Configurar Frontend (Vue.js)

### 4.1 Navegar a la carpeta frontend
```powershell
cd ..\frontend
```

### 4.2 Instalar dependencias
```powershell
npm install
```

**Dependencias principales:**
- `vue` v3.4 - Framework frontend
- `vue-router` - Navegación
- `pinia` - State management
- `axios` - Cliente HTTP
- `vite` - Build tool

### 4.3 Configurar variables de entorno (opcional)

El frontend está configurado para conectarse a `http://localhost:8000` por defecto.

Si necesitas cambiar la URL del backend, edita `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

---

## ▶️ Paso 5: Iniciar la Aplicación

### 5.1 Iniciar Backend
```powershell
# Desde la carpeta backend/ (con entorno virtual activado)
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O usa el script PowerShell:
```powershell
.\start-backend.ps1
```

**Verificar que funciona:**
- Abre http://localhost:8000/health
- Deberías ver: `{"status": "ok", "database": "connected", "supabase": "connected"}`

### 5.2 Iniciar Frontend (en otra terminal)
```powershell
# Desde la carpeta frontend/
cd frontend
npm run dev
```

**Verificar que funciona:**
- Abre http://localhost:5173
- Deberías ver la pantalla de login/registro

---

## ✅ Paso 6: Verificar Instalación

### 6.1 Probar Autenticación
1. Registra un nuevo usuario
2. Verifica que te redirija a Home
3. Cierra sesión y vuelve a iniciar

### 6.2 Probar Health Check
1. Ve a la vista "Health Check" (en navegación)
2. Verifica que todos los servicios estén ✅ conectados

### 6.3 Probar Perfil
1. Ve a "Mi Perfil"
2. Verifica que cargue tu información
3. Verifica que aparezcan las misiones diarias
4. Verifica que aparezcan las recompensas

---

## 🐛 Solución de Problemas Comunes

### Error: "ModuleNotFoundError"
```powershell
# Asegúrate de tener el entorno virtual activado
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Error: "Connection to Supabase failed"
- Verifica que las variables `SUPABASE_URL` y `SUPABASE_ANON_KEY` sean correctas
- No dejes espacios extra en el archivo `.env`
- Reinicia el servidor backend

### Error: "column daily_missions.mission_name does not exist"
- Ejecuta el script de corrección del Paso 3.2 (ALTER TABLE)
- Reinicia el backend

### Error: "CORS policy blocking requests"
- El backend ya tiene CORS configurado para `localhost:5173`
- Si usas otro puerto, edita `main.py` línea ~20

### Error: "npm ERR! code ELIFECYCLE"
```powershell
# Limpia cache y reinstala
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Backend no se reinicia automáticamente
- Asegúrate de usar la flag `--reload`:
  ```powershell
  uvicorn main:app --reload
  ```

---

## 📂 Estructura del Proyecto

```
miappbora/
├── backend/                    # API FastAPI
│   ├── main.py                # Punto de entrada
│   ├── requirements.txt       # Dependencias Python
│   ├── .env                   # Variables de entorno (CREAR)
│   ├── adapters/              # Conexiones externas
│   ├── api/                   # (legacy, no usado)
│   ├── config/                # Configuración DB
│   ├── models/                # Modelos SQLAlchemy
│   ├── routers/               # Endpoints REST
│   ├── schemas/               # Pydantic schemas
│   ├── scripts/               # Scripts de utilidad
│   ├── services/              # Lógica de negocio
│   └── sql/                   # Scripts SQL
├── frontend/                  # Aplicación Vue.js
│   ├── src/
│   │   ├── main.js           # Punto de entrada
│   │   ├── App.vue           # Componente raíz
│   │   ├── components/       # Componentes reutilizables
│   │   ├── services/         # API clients
│   │   ├── stores/           # Pinia stores
│   │   └── views/            # Páginas/vistas
│   ├── package.json          # Dependencias Node
│   └── vite.config.js        # Configuración Vite
├── docs/                      # Documentación
└── README.md                  # Documentación principal
```

---

## 🔑 Credenciales de Prueba

Después de instalar, puedes crear un usuario de prueba:

**Registro:**
- Email: `test@miappbora.com`
- Username: `testuser`
- Teléfono: `+51 999 999 999`
- Nombre: `Usuario Prueba`
- Contraseña: `Test123!`

---

## 📚 Documentación Adicional

- **SETUP_SUPABASE.md** - Guía detallada de Supabase
- **SETUP_HUGGINGFACE.md** - Configuración de HuggingFace
- **AUTH_SYSTEM.md** - Sistema de autenticación
- **DATABASE_INFO.md** - Esquema de base de datos
- **FLUJOS_FUNCIONALIDADES.md** - Flujos de cada feature

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs del backend (terminal donde corre uvicorn)
2. Revisa la consola del navegador (F12 → Console)
3. Verifica que Supabase esté activo en el dashboard
4. Consulta la documentación en `docs/`

---

## ✨ Próximos Pasos

Una vez instalado todo:
1. ✅ Registra un usuario
2. ✅ Verifica Health Check
3. ✅ Explora el perfil y misiones
4. 🎮 Prueba los minijuegos (en desarrollo)
5. 💬 Prueba el Mentor Bora (en desarrollo)

---

**¡Listo!** Tu aplicación MIAPPBORA debería estar funcionando correctamente. 🎉
