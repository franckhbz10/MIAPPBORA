# 🧹 Scripts de Limpieza de Base de Datos - MIAPPBORA

## 📋 Descripción

Este directorio contiene scripts SQL para limpiar y mantener la base de datos de Supabase del proyecto MIAPPBORA.

## 📁 Archivos Disponibles

### 1. `CLEANUP_SCRIPTS.sql` (Completo)
**Descripción**: Colección completa de 10 opciones diferentes de limpieza  
**Uso**: Para casos específicos y avanzados  
**Opciones incluidas**:
- ✅ Limpieza completa (mantener estructura)
- ✅ Eliminar solo usuarios de prueba
- ✅ Eliminar usuarios específicos por email
- ✅ Eliminar datos antiguos (>30 días)
- ✅ Verificar datos antes de eliminar
- ✅ Resetear solo gamificación
- ✅ Eliminar solo conversaciones de chat
- ✅ Crear backups
- ✅ Estadísticas de BD
- ✅ Script recomendado para desarrollo

### 2. `QUICK_CLEANUP.sql` (Recomendado)
**Descripción**: Script simple y rápido para desarrollo  
**Uso**: Eliminar usuarios de prueba (test, usuario, example, demo)  
**Características**:
- 🔍 Paso 1: Ver qué se eliminará
- 🧹 Paso 2: Ejecutar limpieza (comentado por seguridad)
- ✅ Paso 3: Verificar resultado

### 3. `FULL_RESET.sql` (⚠️ Peligroso)
**Descripción**: Reseteo completo de todas las tablas  
**Uso**: Solo en desarrollo, cuando necesitas empezar desde cero  
**Características**:
- 🔍 Ver estado actual
- 🧹 Vaciar todas las tablas
- 🔄 Resetear IDs a 1
- ✅ Verificar limpieza

## 🚀 Cómo Usar

### Opción A: Supabase Dashboard (Recomendado)

1. **Acceder a Supabase**
   - Ir a [https://app.supabase.com](https://app.supabase.com)
   - Seleccionar tu proyecto MIAPPBORA

2. **Abrir SQL Editor**
   - En el menú lateral: `SQL Editor`
   - Clic en `New query`

3. **Ejecutar Script**
   - Copiar el contenido del archivo que necesites
   - Pegar en el editor
   - Para scripts con código comentado (`/* ... */`):
     - Primero ejecutar la parte NO comentada (para verificar)
     - Si todo está bien, descomentar y ejecutar
   - Clic en `Run` o `Ctrl + Enter`

### Opción B: Cliente PostgreSQL

```bash
# Conectar a Supabase
psql "postgresql://postgres:[TU-PASSWORD]@[TU-HOST]:5432/postgres"

# Ejecutar archivo
\i docs/QUICK_CLEANUP.sql
```

### Opción C: Desde Python (psycopg2)

```python
import psycopg2
from config.database_connection import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

with open('docs/QUICK_CLEANUP.sql', 'r') as f:
    sql = f.read()
    cursor.execute(sql)

conn.commit()
conn.close()
```

## ⚠️ Precauciones

### Antes de Ejecutar Cualquier Script

1. **✅ Verificar Ambiente**
   ```sql
   -- Asegúrate de NO estar en producción
   SELECT current_database();
   ```

2. **✅ Hacer Backup** (Producción)
   ```sql
   -- Ejecutar OPCIÓN 8 de CLEANUP_SCRIPTS.sql
   CREATE TABLE users_backup AS SELECT * FROM users;
   ```

3. **✅ Usar Transacciones**
   ```sql
   BEGIN;
   -- Tu código de limpieza
   -- Si algo sale mal: ROLLBACK
   -- Si todo está bien: COMMIT
   ```

## 📊 Casos de Uso Comunes

### Caso 1: Limpiar después de probar registro
```sql
-- Usar: QUICK_CLEANUP.sql
-- Elimina usuarios con emails: test, usuario, example, demo
```

### Caso 2: Eliminar un usuario específico
```sql
-- Usar: CLEANUP_SCRIPTS.sql - OPCIÓN 3
-- Cambiar el email en la variable target_email
```

### Caso 3: Resetear todo en desarrollo
```sql
-- Usar: FULL_RESET.sql
-- ⚠️ Solo si quieres empezar desde cero
```

### Caso 4: Limpiar datos antiguos (producción)
```sql
-- Usar: CLEANUP_SCRIPTS.sql - OPCIÓN 4
-- Elimina registros con más de 30 días
```

### Caso 5: Ver estadísticas antes de decidir
```sql
-- Usar: CLEANUP_SCRIPTS.sql - OPCIÓN 5
-- Muestra conteo de registros en todas las tablas
```

## 🎯 Workflow Recomendado

### Durante Desarrollo

```sql
-- 1. Ver qué usuarios de prueba existen
SELECT id, email, username, created_at 
FROM users 
WHERE email LIKE '%test%' OR email LIKE '%usuario%';

-- 2. Ejecutar QUICK_CLEANUP.sql
-- (Descomentar la sección de DELETE)

-- 3. Verificar
SELECT COUNT(*) FROM users;
```

### Antes de Deployment

```sql
-- 1. Verificar datos
SELECT tabla, COUNT(*) FROM CLEANUP_SCRIPTS.sql - OPCIÓN 5;

-- 2. Limpiar usuarios de prueba
-- Ejecutar QUICK_CLEANUP.sql

-- 3. Limpiar datos antiguos (opcional)
-- Ejecutar CLEANUP_SCRIPTS.sql - OPCIÓN 4
```

## 🔧 Personalización

### Eliminar usuarios con patrón específico

```sql
DELETE FROM users 
WHERE email LIKE '%@midominio.com';
```

### Mantener solo últimos N usuarios

```sql
DELETE FROM users 
WHERE id NOT IN (
    SELECT id FROM users 
    ORDER BY created_at DESC 
    LIMIT 100
);
```

### Eliminar sesiones de un usuario

```sql
DELETE FROM game_sessions 
WHERE user_id = 123;
```

## 📝 Notas Importantes

1. **CASCADE**: Elimina datos relacionados automáticamente
2. **TRUNCATE vs DELETE**: 
   - `TRUNCATE`: Más rápido, resetea secuencias
   - `DELETE`: Más lento, mantiene secuencias
3. **Secuencias**: Solo se resetean con `ALTER SEQUENCE`
4. **session_replication_role**: Desactiva triggers temporalmente
5. **Transacciones**: Siempre usar `BEGIN/COMMIT/ROLLBACK` en producción

## 🆘 Problemas Comunes

### Error: "permission denied"
```sql
-- Solución: Usar role correcto
SET ROLE postgres;
```

### Error: "violates foreign key constraint"
```sql
-- Solución: Usar CASCADE o session_replication_role
SET session_replication_role = 'replica';
-- Tu DELETE aquí
SET session_replication_role = 'origin';
```

### Error: "cannot truncate a table referenced in a foreign key constraint"
```sql
-- Solución: Agregar CASCADE
TRUNCATE TABLE users CASCADE;
```

## 📞 Contacto

Si tienes dudas o problemas:
1. Revisar logs de Supabase
2. Verificar permisos de usuario
3. Consultar documentación oficial: [Supabase SQL](https://supabase.com/docs/guides/database)

---

**Última actualización**: 2025-10-04  
**Versión**: 1.0.0  
**Proyecto**: MIAPPBORA
