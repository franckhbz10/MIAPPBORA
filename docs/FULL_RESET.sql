-- ============================================================
-- RESETEO COMPLETO DE BASE DE DATOS
-- ============================================================
-- ⚠️ PELIGRO: Este script elimina TODOS los datos
-- Solo usar en ambiente de desarrollo
-- ============================================================

-- 🔍 VER ESTADO ACTUAL
-- ============================================================

SELECT 'ESTADO ACTUAL DE LA BASE DE DATOS' AS info;

SELECT 
    'users' AS tabla,
    COUNT(*) AS registros
FROM users
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
SELECT 'user_rewards', COUNT(*) FROM user_rewards
UNION ALL
SELECT 'level_progress', COUNT(*) FROM level_progress
UNION ALL
SELECT 'app_feedback', COUNT(*) FROM app_feedback;


-- 🧹 RESETEO COMPLETO
-- ============================================================
-- ⚠️ DESCOMENTA SOLO SI ESTÁS 100% SEGURO

/*
BEGIN;

-- Desactivar restricciones
SET session_replication_role = 'replica';

-- Vaciar todas las tablas
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

-- Resetear secuencias (IDs empiezan desde 1)
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

-- Reactivar restricciones
SET session_replication_role = 'origin';

COMMIT;

SELECT '✅ Base de datos reseteada completamente' AS resultado;
*/


-- 🔍 VERIFICAR LIMPIEZA
-- ============================================================

SELECT 'VERIFICACIÓN POST-LIMPIEZA' AS info;

SELECT 
    'users' AS tabla,
    COUNT(*) AS registros_restantes
FROM users
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
SELECT 'user_rewards', COUNT(*) FROM user_rewards
UNION ALL
SELECT 'level_progress', COUNT(*) FROM level_progress
UNION ALL
SELECT 'app_feedback', COUNT(*) FROM app_feedback;

-- Todos deberían mostrar 0 registros
