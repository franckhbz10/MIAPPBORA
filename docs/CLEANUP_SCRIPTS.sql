-- ============================================================
-- SCRIPTS DE LIMPIEZA PARA MIAPPBORA - SUPABASE
-- ============================================================
-- Fecha: 2025-10-04
-- Descripción: Scripts para limpiar y resetear tablas de la base de datos
-- ============================================================

-- ============================================================
-- OPCIÓN 1: ELIMINAR TODOS LOS DATOS (MANTENER ESTRUCTURA)
-- ============================================================
-- Ejecuta estos comandos para vaciar todas las tablas manteniendo la estructura

-- Desactivar temporalmente las restricciones de clave foránea
SET session_replication_role = 'replica';

-- Limpiar tablas en orden inverso de dependencias
TRUNCATE TABLE app_feedback CASCADE;
TRUNCATE TABLE level_progress CASCADE;
TRUNCATE TABLE user_rewards CASCADE;
TRUNCATE TABLE rewards CASCADE;
TRUNCATE TABLE daily_missions CASCADE;
TRUNCATE TABLE game_answers CASCADE;
TRUNCATE TABLE game_sessions CASCADE;
TRUNCATE TABLE chat_messages CASCADE;
TRUNCATE TABLE chat_conversations CASCADE;
TRUNCATE TABLE phrase_embeddings CASCADE;
TRUNCATE TABLE bora_phrases CASCADE;
TRUNCATE TABLE users CASCADE;

-- Reactivar las restricciones de clave foránea
SET session_replication_role = 'origin';

-- Resetear secuencias de IDs (empezar desde 1)
ALTER SEQUENCE users_id_seq RESTART WITH 1;
ALTER SEQUENCE bora_phrases_id_seq RESTART WITH 1;
ALTER SEQUENCE phrase_embeddings_id_seq RESTART WITH 1;
ALTER SEQUENCE chat_conversations_id_seq RESTART WITH 1;
ALTER SEQUENCE chat_messages_id_seq RESTART WITH 1;
ALTER SEQUENCE game_sessions_id_seq RESTART WITH 1;
ALTER SEQUENCE game_answers_id_seq RESTART WITH 1;
ALTER SEQUENCE daily_missions_id_seq RESTART WITH 1;
ALTER SEQUENCE rewards_id_seq RESTART WITH 1;
ALTER SEQUENCE user_rewards_id_seq RESTART WITH 1;
ALTER SEQUENCE level_progress_id_seq RESTART WITH 1;
ALTER SEQUENCE app_feedback_id_seq RESTART WITH 1;

SELECT 'Todas las tablas han sido limpiadas exitosamente' AS status;


-- ============================================================
-- OPCIÓN 2: ELIMINAR SOLO DATOS DE USUARIOS DE PRUEBA
-- ============================================================
-- Mantiene datos de producción, elimina solo usuarios de prueba

-- Eliminar usuarios de prueba (emails que contienen 'test' o 'usuario')
DELETE FROM app_feedback 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%'
);

DELETE FROM level_progress 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%'
);

DELETE FROM user_rewards 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%'
);

DELETE FROM daily_missions 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%'
);

DELETE FROM game_answers 
WHERE game_session_id IN (
    SELECT id FROM game_sessions 
    WHERE user_id IN (
        SELECT id FROM users 
        WHERE email LIKE '%test%' OR email LIKE '%usuario%'
    )
);

DELETE FROM game_sessions 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%'
);

DELETE FROM chat_messages 
WHERE conversation_id IN (
    SELECT id FROM chat_conversations 
    WHERE user_id IN (
        SELECT id FROM users 
        WHERE email LIKE '%test%' OR email LIKE '%usuario%'
    )
);

DELETE FROM chat_conversations 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%'
);

DELETE FROM users 
WHERE email LIKE '%test%' OR email LIKE '%usuario%';

SELECT 'Usuarios de prueba eliminados exitosamente' AS status;


-- ============================================================
-- OPCIÓN 3: ELIMINAR USUARIOS ESPECÍFICOS POR EMAIL
-- ============================================================
-- Reemplaza 'email_a_eliminar@example.com' con el email real

-- Ejemplo para eliminar usuario específico
DO $$
DECLARE
    target_email TEXT := 'usuario8990@miappbora.com'; -- CAMBIAR ESTE EMAIL
    target_user_id INTEGER;
BEGIN
    -- Obtener el ID del usuario
    SELECT id INTO target_user_id FROM users WHERE email = target_email;
    
    IF target_user_id IS NOT NULL THEN
        -- Eliminar en orden de dependencias
        DELETE FROM app_feedback WHERE user_id = target_user_id;
        DELETE FROM level_progress WHERE user_id = target_user_id;
        DELETE FROM user_rewards WHERE user_id = target_user_id;
        DELETE FROM daily_missions WHERE user_id = target_user_id;
        DELETE FROM game_answers 
        WHERE game_session_id IN (
            SELECT id FROM game_sessions WHERE user_id = target_user_id
        );
        DELETE FROM game_sessions WHERE user_id = target_user_id;
        DELETE FROM chat_messages 
        WHERE conversation_id IN (
            SELECT id FROM chat_conversations WHERE user_id = target_user_id
        );
        DELETE FROM chat_conversations WHERE user_id = target_user_id;
        DELETE FROM users WHERE id = target_user_id;
        
        RAISE NOTICE 'Usuario % (ID: %) eliminado exitosamente', target_email, target_user_id;
    ELSE
        RAISE NOTICE 'Usuario % no encontrado', target_email;
    END IF;
END $$;


-- ============================================================
-- OPCIÓN 4: ELIMINAR DATOS ANTIGUOS (MÁS DE 30 DÍAS)
-- ============================================================

-- Eliminar sesiones de juego antiguas
DELETE FROM game_answers 
WHERE game_session_id IN (
    SELECT id FROM game_sessions 
    WHERE created_at < NOW() - INTERVAL '30 days'
);

DELETE FROM game_sessions 
WHERE created_at < NOW() - INTERVAL '30 days';

-- Eliminar conversaciones antiguas
DELETE FROM chat_messages 
WHERE conversation_id IN (
    SELECT id FROM chat_conversations 
    WHERE created_at < NOW() - INTERVAL '30 days'
);

DELETE FROM chat_conversations 
WHERE created_at < NOW() - INTERVAL '30 days';

-- Eliminar misiones expiradas
DELETE FROM daily_missions 
WHERE expires_at < NOW() - INTERVAL '30 days';

-- Eliminar feedback antiguo
DELETE FROM app_feedback 
WHERE created_at < NOW() - INTERVAL '30 days';

SELECT 'Datos antiguos eliminados exitosamente' AS status;


-- ============================================================
-- OPCIÓN 5: VERIFICAR DATOS ANTES DE ELIMINAR
-- ============================================================
-- Ejecuta estos queries para ver qué datos tienes

-- Contar registros en cada tabla
SELECT 
    'users' AS tabla,
    COUNT(*) AS total_registros
FROM users
UNION ALL
SELECT 'bora_phrases', COUNT(*) FROM bora_phrases
UNION ALL
SELECT 'phrase_embeddings', COUNT(*) FROM phrase_embeddings
UNION ALL
SELECT 'chat_conversations', COUNT(*) FROM chat_conversations
UNION ALL
SELECT 'chat_messages', COUNT(*) FROM chat_messages
UNION ALL
SELECT 'game_sessions', COUNT(*) FROM game_sessions
UNION ALL
SELECT 'game_answers', COUNT(*) FROM game_answers
UNION ALL
SELECT 'daily_missions', COUNT(*) FROM daily_missions
UNION ALL
SELECT 'rewards', COUNT(*) FROM rewards
UNION ALL
SELECT 'user_rewards', COUNT(*) FROM user_rewards
UNION ALL
SELECT 'level_progress', COUNT(*) FROM level_progress
UNION ALL
SELECT 'app_feedback', COUNT(*) FROM app_feedback
ORDER BY tabla;

-- Ver todos los usuarios
SELECT 
    id,
    email,
    username,
    full_name,
    phone,
    level,
    total_points,
    created_at,
    last_login
FROM users
ORDER BY created_at DESC;

-- Ver usuarios de prueba
SELECT 
    id,
    email,
    username,
    created_at
FROM users
WHERE email LIKE '%test%' OR email LIKE '%usuario%'
ORDER BY created_at DESC;


-- ============================================================
-- OPCIÓN 6: RESETEAR SOLO DATOS DE GAMIFICACIÓN
-- ============================================================
-- Mantiene usuarios pero resetea progreso, misiones y recompensas

-- Limpiar progreso de nivel
DELETE FROM level_progress;

-- Limpiar recompensas de usuarios
DELETE FROM user_rewards;

-- Limpiar misiones
DELETE FROM daily_missions;

-- Limpiar sesiones de juego
DELETE FROM game_answers;
DELETE FROM game_sessions;

-- Resetear puntos y nivel de usuarios
UPDATE users SET 
    level = 1,
    total_points = 0,
    current_title = 'Principiante'
WHERE id > 0;

SELECT 'Datos de gamificación reseteados' AS status;


-- ============================================================
-- OPCIÓN 7: ELIMINAR SOLO CONVERSACIONES DE CHAT
-- ============================================================

DELETE FROM chat_messages;
DELETE FROM chat_conversations;

SELECT 'Conversaciones de chat eliminadas' AS status;


-- ============================================================
-- OPCIÓN 8: BACKUP ANTES DE LIMPIAR
-- ============================================================
-- Crea tablas de respaldo antes de eliminar datos

-- Backup de usuarios
CREATE TABLE IF NOT EXISTS users_backup AS 
SELECT * FROM users;

-- Backup de sesiones de juego
CREATE TABLE IF NOT EXISTS game_sessions_backup AS 
SELECT * FROM game_sessions;

-- Backup de conversaciones
CREATE TABLE IF NOT EXISTS chat_conversations_backup AS 
SELECT * FROM chat_conversations;

SELECT 'Backup creado exitosamente' AS status;

-- Para restaurar desde backup:
-- INSERT INTO users SELECT * FROM users_backup;


-- ============================================================
-- OPCIÓN 9: ELIMINAR TABLAS DE BACKUP
-- ============================================================

DROP TABLE IF EXISTS users_backup CASCADE;
DROP TABLE IF EXISTS game_sessions_backup CASCADE;
DROP TABLE IF EXISTS chat_conversations_backup CASCADE;

SELECT 'Tablas de backup eliminadas' AS status;


-- ============================================================
-- OPCIÓN 10: ESTADÍSTICAS DE LA BASE DE DATOS
-- ============================================================

SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;


-- ============================================================
-- SCRIPT RECOMENDADO PARA DESARROLLO
-- ============================================================
-- Este es el script que deberías usar regularmente en desarrollo

BEGIN;

-- Verificar qué se va a eliminar
SELECT 'Usuarios a eliminar:' AS info, COUNT(*) AS total 
FROM users 
WHERE email LIKE '%test%' OR email LIKE '%usuario%';

-- Eliminar datos de prueba (descomenta las siguientes líneas cuando estés seguro)
/*
SET session_replication_role = 'replica';

-- Eliminar usuarios de prueba y sus datos relacionados
DELETE FROM app_feedback 
WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%');

DELETE FROM level_progress 
WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%');

DELETE FROM user_rewards 
WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%');

DELETE FROM daily_missions 
WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%');

DELETE FROM game_answers 
WHERE game_session_id IN (
    SELECT id FROM game_sessions 
    WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%')
);

DELETE FROM game_sessions 
WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%');

DELETE FROM chat_messages 
WHERE conversation_id IN (
    SELECT id FROM chat_conversations 
    WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%')
);

DELETE FROM chat_conversations 
WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%' OR email LIKE '%usuario%');

DELETE FROM users 
WHERE email LIKE '%test%' OR email LIKE '%usuario%';

SET session_replication_role = 'origin';
*/

-- Si todo se ve bien, ejecuta COMMIT. Si no, ejecuta ROLLBACK
-- COMMIT;
ROLLBACK;


-- ============================================================
-- NOTAS IMPORTANTES
-- ============================================================
/*
1. SIEMPRE hacer backup antes de eliminar datos en producción
2. Usar transacciones (BEGIN/COMMIT/ROLLBACK) para operaciones seguras
3. Verificar los datos con SELECT antes de DELETE
4. Las secuencias solo se resetean con ALTER SEQUENCE
5. CASCADE elimina datos relacionados automáticamente
6. session_replication_role = 'replica' desactiva triggers temporalmente
7. Para producción, NUNCA uses TRUNCATE sin backup

ORDEN DE EJECUCIÓN RECOMENDADO:
1. Ejecutar OPCIÓN 5 para ver qué datos tienes
2. Ejecutar OPCIÓN 8 para crear backup (opcional pero recomendado)
3. Ejecutar la opción de limpieza que necesites
4. Verificar con OPCIÓN 5 que se eliminó correctamente
5. Si usaste backup y algo salió mal, restaurar desde las tablas _backup
*/
