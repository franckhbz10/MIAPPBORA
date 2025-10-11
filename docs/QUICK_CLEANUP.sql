-- ============================================================
-- LIMPIEZA RÁPIDA - USUARIOS DE PRUEBA
-- ============================================================
-- Script simple para eliminar usuarios de prueba en desarrollo
-- Ejecutar en: Supabase SQL Editor
-- ============================================================

-- 🔍 PASO 1: VER QUÉ SE VA A ELIMINAR
-- ============================================================

SELECT 
    'USUARIOS A ELIMINAR' AS info,
    id,
    email,
    username,
    full_name,
    created_at
FROM users
WHERE 
    email LIKE '%test%' 
    OR email LIKE '%usuario%'
    OR email LIKE '%example%'
    OR email LIKE '%demo%'
ORDER BY created_at DESC;


-- 🧹 PASO 2: ELIMINAR USUARIOS DE PRUEBA
-- ============================================================
-- ⚠️ DESCOMENTA LAS LÍNEAS SIGUIENTES SOLO SI ESTÁS SEGURO

/*
BEGIN;

-- Desactivar restricciones temporalmente
SET session_replication_role = 'replica';

-- Eliminar todos los datos relacionados
DELETE FROM app_feedback 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
);

DELETE FROM level_progress 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
);

DELETE FROM user_rewards 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
);

DELETE FROM daily_missions 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
);

DELETE FROM game_answers 
WHERE game_session_id IN (
    SELECT id FROM game_sessions 
    WHERE user_id IN (
        SELECT id FROM users 
        WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
    )
);

DELETE FROM game_sessions 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
);

DELETE FROM chat_messages 
WHERE conversation_id IN (
    SELECT id FROM chat_conversations 
    WHERE user_id IN (
        SELECT id FROM users 
        WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
    )
);

DELETE FROM chat_conversations 
WHERE user_id IN (
    SELECT id FROM users 
    WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%'
);

DELETE FROM users 
WHERE email LIKE '%test%' OR email LIKE '%usuario%' OR email LIKE '%example%' OR email LIKE '%demo%';

-- Reactivar restricciones
SET session_replication_role = 'origin';

COMMIT;

SELECT 'Usuarios de prueba eliminados exitosamente' AS resultado;
*/


-- 🔍 PASO 3: VERIFICAR QUE SE ELIMINARON
-- ============================================================

SELECT 
    'USUARIOS RESTANTES' AS info,
    COUNT(*) AS total
FROM users;

SELECT 
    'DETALLE DE USUARIOS RESTANTES' AS info,
    id,
    email,
    username,
    created_at
FROM users
ORDER BY created_at DESC;
