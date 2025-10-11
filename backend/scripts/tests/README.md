# Tests de Autenticación - MIAPPBORA

Este directorio contiene scripts de prueba para el sistema de autenticación de MIAPPBORA.

## 📋 Scripts Disponibles

### 1. `test_register.py`
Prueba exhaustiva del endpoint de registro `/auth/register`.

**Tests incluidos:**
- ✅ Registro exitoso con datos válidos
- ✅ Rechazo de email duplicado
- ✅ Rechazo de username duplicado
- ✅ Validación de formato de email
- ✅ Validación de longitud de contraseña (mínimo 6 caracteres)
- ✅ Validación de campos requeridos

**Uso:**
```bash
cd backend/scripts/tests
python test_register.py
```

### 2. `test_login.py`
Prueba exhaustiva del endpoint de login `/auth/login` y endpoint protegido `/auth/me`.

**Tests incluidos:**
- ✅ Login exitoso con credenciales válidas
- ✅ Rechazo de contraseña incorrecta
- ✅ Rechazo de usuario inexistente
- ✅ Validación de formato de email
- ✅ Validación de campos requeridos
- ✅ Acceso a endpoint protegido con token válido
- ✅ Rechazo de token inválido
- ✅ Rechazo de peticiones sin token

**Uso:**
```bash
cd backend/scripts/tests
python test_login.py
```

### 3. `test_auth_complete.py` ⭐ Recomendado
Flujo completo de autenticación que ejecuta todos los pasos en secuencia.

**Flujo del test:**
1. ✅ Verificación de conexión al servidor
2. ✅ Registro de nuevo usuario
3. ✅ Login con las credenciales creadas
4. ✅ Acceso a endpoint protegido (/auth/me)
5. ✅ Prueba de seguridad - credenciales incorrectas
6. ✅ Prueba de seguridad - token inválido

**Uso:**
```bash
cd backend/scripts/tests
python test_auth_complete.py
```

### 4. `debug_login.py`
Script de debugging para identificar problemas con el login.

**Uso:**
```bash
cd backend/scripts/tests
python debug_login.py
```

## 🚀 Prerequisitos

### 1. Servidor Backend Corriendo
Asegúrate de que el backend esté corriendo en `http://localhost:8000`:

```bash
cd backend
uvicorn main:app --reload
```

O usa el script de PowerShell:
```powershell
cd backend
.\start-backend.ps1
```

### 2. Dependencias Instaladas
Los scripts requieren la librería `requests`:

```bash
pip install requests
```

## 📊 Ejemplo de Salida Exitosa

```
================================================================================
                    🚀 TEST COMPLETO DE AUTENTICACIÓN
================================================================================

🔗 Servidor: http://localhost:8000
🕐 Fecha: 2025-10-04 23:50:39

✅ Servidor corriendo en http://localhost:8000

================================================================================
PASO 1: REGISTRO DE USUARIO
================================================================================

✅ REGISTRO EXITOSO!

👤 Usuario creado:
   ID: 8
   Email: testauth20251004235041@example.com
   Username: testauth20251004235041
   Level: 1
   Points: 0
   Title: Principiante

🔑 Token JWT generado

================================================================================
PASO 2: LOGIN DE USUARIO
================================================================================

✅ LOGIN EXITOSO!

================================================================================
                             ✅ TEST COMPLETADO EXITOSAMENTE
================================================================================

📊 RESUMEN:
   ✅ Registro de usuario - OK
   ✅ Login de usuario - OK
   ✅ Acceso a endpoint protegido - OK
   ✅ Rechazo de credenciales incorrectas - OK
   ✅ Rechazo de token inválido - OK
```

## 🔧 Configuración

Los scripts usan la siguiente configuración por defecto:

```python
BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
ME_URL = f"{BASE_URL}/auth/me"
```

Si tu servidor corre en otro puerto o host, modifica la variable `BASE_URL` en cada script.

## 📝 Estructura de Datos

### Registro de Usuario
```json
{
  "email": "user@example.com",
  "username": "username",
  "phone": "987654321",
  "password": "securepass123",
  "full_name": "Full Name"
}
```

### Login
```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

### Respuesta de Autenticación
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "level": 1,
    "total_points": 0,
    "current_title": "Principiante",
    "is_active": true,
    "created_at": "2025-10-04T15:30:45",
    "last_login": null
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## 🛠️ Troubleshooting

### Error: No se puede conectar al servidor
```
❌ No se puede conectar al servidor en http://localhost:8000
```
**Solución:** Verifica que el backend esté corriendo:
```bash
cd backend
uvicorn main:app --reload
```

### Error: ModuleNotFoundError: No module named 'requests'
**Solución:** Instala la dependencia:
```bash
pip install requests
```

### Error 422: Validation Error
**Solución:** Verifica que los datos cumplan con las validaciones:
- Email debe ser válido
- Password mínimo 6 caracteres
- Username entre 3-100 caracteres
- Phone entre 9-20 caracteres

### Error 400: Email ya está registrado
**Solución:** Esto es esperado si ejecutas el mismo test múltiples veces. Los scripts usan timestamps para generar emails únicos.

## 🔍 Verificación Manual

También puedes probar los endpoints manualmente:

### Con cURL:
```bash
# Registro
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","phone":"987654321","password":"pass123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# Endpoint protegido
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Con PowerShell:
```powershell
# Registro
$body = @{
    email = "test@example.com"
    username = "testuser"
    phone = "987654321"
    password = "pass123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/auth/register" -Method Post -Body $body -ContentType "application/json"

# Login
$loginBody = @{
    email = "test@example.com"
    password = "pass123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
```

## 📚 Más Información

- Ver documentación de la API: http://localhost:8000/docs
- Ver documentación del sistema de auth: `../../docs/AUTH_SYSTEM.md`
- Ver esquemas de datos: `../schemas/schemas.py`
- Ver routers: `../routers/auth_router.py`
- Ver servicios: `../services/auth_service.py`

## 🧹 Limpieza de Datos de Prueba

Para limpiar usuarios de prueba de la base de datos, consulta:
- `../../docs/CLEANUP_SCRIPTS.sql` - Scripts SQL para limpiar datos

O ejecuta la OPCIÓN 2 del archivo CLEANUP_SCRIPTS.sql que elimina usuarios con emails que contienen 'test':

```sql
DELETE FROM users 
WHERE email LIKE '%test%' OR email LIKE '%usuario%';
```

## ✅ Checklist de Tests

Antes de considerar el sistema de autenticación como completo, verifica:

- [ ] ✅ Registro de usuario funciona
- [ ] ✅ Email duplicado se rechaza
- [ ] ✅ Username duplicado se rechaza
- [ ] ✅ Validaciones de campos funcionan
- [ ] ✅ Login funciona con credenciales correctas
- [ ] ✅ Login rechaza credenciales incorrectas
- [ ] ✅ Tokens JWT se generan correctamente
- [ ] ✅ Endpoint protegido requiere autenticación
- [ ] ✅ Tokens inválidos se rechazan
- [ ] ✅ Campo last_login se actualiza en login
- [ ] ✅ Manejo de errores funciona correctamente

**Estado actual: ✅ TODOS LOS TESTS PASANDO**
