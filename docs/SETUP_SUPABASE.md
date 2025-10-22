#  Configuración de Supabase para MIAPPBORA

## Paso 1: Crear Proyecto en Supabase

1. Ve a https://supabase.com
2. Haz clic en "Start your project"
3. Crea una cuenta o inicia sesión
4. Crea un nuevo proyecto:
   - **Name**: `miappbora`
   - **Database Password**: Guarda esta contraseña (la necesitarás)
   - **Region**: Selecciona la más cercana (ej: `South America (São Paulo)`)
5. Espera 2-3 minutos mientras se crea el proyecto

## Paso 2: Obtener Credenciales

1. En tu proyecto, ve a **Settings** ()  **API**
2. Copia estos valores:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGc...` (es largo, cópialo completo)

## Paso 3: Configurar Variables de Entorno

Abre el archivo `.env` en la carpeta `backend/` y completa:

```env
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...tu_key_completa
```

## Paso 4: Habilitar pgvector en Supabase

1. En Supabase, ve a **SQL Editor**
2. Ejecuta este comando:

```sql
-- Habilitar extensión pgvector para búsqueda semántica
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Haz clic en **RUN** ()

## Paso 5: Crear Esquema de Base de Datos

Ejecuta este script SQL en **SQL Editor**:

```sql
-- ============================================
-- MIAPPBORA - Esquema de Base de Datos Completo
-- ============================================

-- ============================================
-- TABLA: USUARIOS
-- ============================================
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    full_name VARCHAR(255),
    hashed_password TEXT NOT NULL,
    avatar_url TEXT DEFAULT 'https://ui-avatars.com/api/?name=User',
    level INTEGER DEFAULT 1,
    total_points INTEGER DEFAULT 0,
    current_title VARCHAR(100) DEFAULT 'Entusiasta',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- ============================================
-- TABLA: FRASES EN BORA
-- ============================================
CREATE TABLE IF NOT EXISTS bora_phrases (
    id SERIAL PRIMARY KEY,
    bora_text TEXT NOT NULL,
    spanish_translation TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    difficulty_level INTEGER DEFAULT 1,
    usage_context TEXT,
    pronunciation_guide TEXT,
    audio_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: EMBEDDINGS DE FRASES (RAG)
-- ============================================
CREATE TABLE IF NOT EXISTS phrase_embeddings (
    id SERIAL PRIMARY KEY,
    phrase_id INTEGER REFERENCES bora_phrases(id) ON DELETE CASCADE,
    embedding vector(384),
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: CONVERSACIONES DE CHAT (Mentor Bora)
-- ============================================
CREATE TABLE IF NOT EXISTS chat_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) DEFAULT 'Nueva conversación',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: MENSAJES DE CHAT
-- ============================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' o 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: HISTORIAL DE MINIJUEGOS
-- ============================================
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL,  -- 'complete_phrase' o 'context_match'
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    incorrect_answers INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    is_perfect BOOLEAN DEFAULT FALSE,
    time_spent_seconds INTEGER,
    completed_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: RESPUESTAS DE MINIJUEGOS
-- ============================================
CREATE TABLE IF NOT EXISTS game_answers (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES game_sessions(id) ON DELETE CASCADE,
    phrase_id INTEGER REFERENCES bora_phrases(id),
    user_answer TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    points_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: MISIONES DIARIAS
-- ============================================
CREATE TABLE IF NOT EXISTS daily_missions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mission_date DATE NOT NULL DEFAULT CURRENT_DATE,
    mission_type VARCHAR(50) NOT NULL,  -- 'chat_questions', 'game_plays', 'perfect_games'
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

-- ============================================
-- TABLA: RECOMPENSAS
-- ============================================
CREATE TABLE IF NOT EXISTS rewards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon_url TEXT,
    points_required INTEGER NOT NULL,
    reward_type VARCHAR(50) NOT NULL,  -- 'badge', 'avatar', 'title', 'achievement'
    reward_value TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: RECOMPENSAS DE USUARIOS
-- ============================================
CREATE TABLE IF NOT EXISTS user_rewards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    reward_id INTEGER REFERENCES rewards(id) ON DELETE CASCADE,
    claimed_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, reward_id)
);

-- ============================================
-- TABLA: PROGRESO DE NIVEL
-- ============================================
CREATE TABLE IF NOT EXISTS level_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    current_points INTEGER DEFAULT 0,
    points_to_next_level INTEGER DEFAULT 100,
    level INTEGER DEFAULT 1,
    title VARCHAR(100) DEFAULT 'Entusiasta',
    phrases_learned INTEGER DEFAULT 0,
    games_completed INTEGER DEFAULT 0,
    perfect_games INTEGER DEFAULT 0,
    chat_interactions INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLA: FEEDBACK DE APLICACIÓN
-- ============================================
CREATE TABLE IF NOT EXISTS app_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mentor_rating INTEGER CHECK (mentor_rating >= 1 AND mentor_rating <= 5),
    games_rating INTEGER CHECK (games_rating >= 1 AND games_rating <= 5),
    general_rating INTEGER CHECK (general_rating >= 1 AND general_rating <= 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- REFERENCIAS
-- ============================================

-- CHAT CONVERSATIONS → USERS
ALTER TABLE chat_conversations
ADD CONSTRAINT fk_chat_conversations_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- GAME SESSIONS → USERS
ALTER TABLE game_sessions
ADD CONSTRAINT fk_game_sessions_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- DAILY MISSIONS → USERS
ALTER TABLE daily_missions
ADD CONSTRAINT fk_daily_missions_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- USER REWARDS → USERS
ALTER TABLE user_rewards
ADD CONSTRAINT fk_user_rewards_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- LEVEL PROGRESS → USERS
ALTER TABLE level_progress
ADD CONSTRAINT fk_level_progress_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- APP FEEDBACK → USERS
ALTER TABLE app_feedback
ADD CONSTRAINT fk_app_feedback_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- ============================================
-- ÍNDICES PARA MEJOR RENDIMIENTO
-- ============================================

-- Índice para búsqueda semántica de vectores
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON phrase_embeddings 
USING ivfflat (embedding vector_cosine_ops);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_bora_phrases_category ON bora_phrases(category);
CREATE INDEX IF NOT EXISTS idx_bora_phrases_difficulty ON bora_phrases(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_user ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_missions_user_date ON daily_missions(user_id, mission_date);
CREATE INDEX IF NOT EXISTS idx_user_rewards_user ON user_rewards(user_id);

-- ============================================
-- DATOS INICIALES
-- ============================================

-- Insertar frases de ejemplo (Categoría: Saludos)
"""INSERT INTO bora_phrases (bora_text, spanish_translation, category, difficulty_level, usage_context, pronunciation_guide) VALUES
('Mɨɨchaajúne', '¿Cómo estás?', 'Saludos y Presentaciones', 1, 'Saludo informal cotidiano', 'mii-chaa-JU-ne'),
('Tsani', 'Bien', 'Saludos y Presentaciones', 1, 'Respuesta común a saludos', 'TSA-ni'),
('Aahjíba mɨɨchaajúne', '¿Y tú cómo estás?', 'Saludos y Presentaciones', 1, 'Reciprocar el saludo', 'aa-JI-ba mii-chaa-JU-ne'),
('Tsanípɨjíba', 'También estoy bien', 'Saludos y Presentaciones', 1, 'Respuesta recíproca', 'tsa-NI-pɨ-JI-ba'),
('Tsúudi ajchyé', 'Hasta luego', 'Saludos y Presentaciones', 1, 'Despedida informal', 'TSUU-di aj-CHY-e');"""

-- Insertar recompensas por defecto (actualizado a 4 niveles)
INSERT INTO rewards (name, description, points_required, reward_type, reward_value, icon_url) VALUES
('Entusiasta', 'Entusiasta - Primeros pasos en Bora', 0, 'badge', 'entusiasta', 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-entusiasta.png'),
('Hablante', 'Hablante - Buen progreso', 50, 'badge', 'hablante', 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-hablante.png'),
('Nativo', 'Nativo - Excelente desempeño', 300, 'badge', 'nativo', 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-nativo.png'),
('Maestro Bora', 'Maestro Bora - Dominio completo', 600, 'badge', 'maestro_bora', 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-maestro-bora.png'),
('Primer Chat', 'Completaste tu primera conversación', 10, 'achievement', 'first_chat', ''),
('Juego Perfecto', 'Completaste un juego sin errores', 50, 'achievement', 'perfect_game', ''),
('Aprendiz Dedicado', 'Completaste 3 misiones diarias', 30, 'achievement', 'daily_streak', '');

-- Crear misiones diarias por defecto para nuevos usuarios (se crearán automáticamente)
-- Esto será manejado por el backend cuando un usuario se registre

-- ============================================
-- FUNCIONES ÚTILES
-- ============================================

-- Función para actualizar el nivel del usuario automáticamente
CREATE OR REPLACE FUNCTION update_user_level()
RETURNS TRIGGER AS $$
BEGIN
    -- Actualizar nivel basado en puntos (4 niveles estandarizados)
    UPDATE users SET 
        level = CASE
            WHEN NEW.current_points >= 600 THEN 4
            WHEN NEW.current_points >= 300 THEN 3
            WHEN NEW.current_points >= 50 THEN 2
            ELSE 1
        END,
        current_title = CASE
            WHEN NEW.current_points >= 600 THEN 'Maestro Bora'
            WHEN NEW.current_points >= 300 THEN 'Nativo'
            WHEN NEW.current_points >= 50 THEN 'Hablante'
            ELSE 'Entusiasta'
        END,
        total_points = NEW.current_points,
        avatar_url = CASE
            -- Solo actualizar avatar si el usuario sube de nivel y tiene avatar por defecto
            WHEN OLD.level IS NULL OR NEW.current_points >= 50 AND OLD.level < CASE
                WHEN NEW.current_points >= 600 THEN 4
                WHEN NEW.current_points >= 300 THEN 3
                WHEN NEW.current_points >= 50 THEN 2
                ELSE 1
            END THEN
                CASE
                    WHEN NEW.current_points >= 600 THEN 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-maestro-bora.png'
                    WHEN NEW.current_points >= 300 THEN 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-nativo.png'
                    WHEN NEW.current_points >= 50 THEN 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-hablante.png'
                    ELSE 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-entusiasta.png'
                END
            ELSE avatar_url
        END
    WHERE id = NEW.user_id;
    
    RETURN NEW;
END;$$ LANGUAGE plpgsql;


-- remove old trigger
DROP TRIGGER IF EXISTS trigger_update_user_level ON level_progress;

-- Trigger para actualizar nivel automáticamente
CREATE TRIGGER trigger_update_user_level
AFTER UPDATE ON level_progress
FOR EACH ROW
WHEN (OLD.current_points IS DISTINCT FROM NEW.current_points)
EXECUTE FUNCTION update_user_level();

-- ============================================
-- VERIFICACIÓN
-- ============================================

SELECT ' Esquema creado exitosamente!' as status;

-- Mostrar todas las tablas creadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

## Paso 6: Verificar Conexión

1. Reinicia el backend (si está corriendo, presiona Ctrl+C y vuelve a iniciarlo)
2. Ve a http://localhost:8000/health
3. Deberías ver `Supabase: connected `

## Paso 7: Instalar Dependencias de Supabase

En la carpeta `backend/`, ejecuta:

```bash
pip install supabase langchain langchain-community sentence-transformers
```

Luego reinicia el servidor.

---

##  Estructura de Tablas

###  users
- Autenticación y perfil de usuario
- Incluye: email, username, phone, avatar, level, points, title

###  bora_phrases
- Corpus de frases Bora-Español
- Incluye: texto, traducción, categoría, dificultad, contexto

###  phrase_embeddings
- Vectores semánticos para RAG (384 dimensiones)
- Relación con bora_phrases

###  chat_conversations & chat_messages
- Historial de conversaciones con Mentor Bora
- Mensajes por conversación (user/assistant)

###  game_sessions & game_answers
- Historial de minijuegos completados
- Respuestas individuales por sesión

###  daily_missions
- Misiones diarias del usuario
- 3 tipos: chat_questions, game_plays, perfect_games

###  rewards & user_rewards
- Recompensas disponibles (badges, achievements)
- Recompensas reclamadas por usuario

###  level_progress
- Progreso de nivel del usuario
- Puntos, nivel, título, estadísticas

###  app_feedback
- Calificaciones de la aplicación
- Mentor Bora, Minijuegos, General (1-5)

---

##  Troubleshooting

### Error: "Connection failed"
- Verifica que el SUPABASE_URL y SUPABASE_ANON_KEY estén correctos
- Asegúrate de no tener espacios extra en el .env

### Error: "Table not found"
- Ejecuta el script SQL del Paso 5 en Supabase SQL Editor
- Verifica que todas las tablas se crearon en la pestaña "Table Editor"

### Error: "vector extension not found"
- Ejecuta el comando del Paso 4 para habilitar pgvector
- Algunos planes de Supabase requieren habilitarlo manualmente

### Error: "Could not find column"
- Verifica que ejecutaste el script SQL completo
- Revisa en Table Editor que todas las columnas existen
- Si falta alguna columna, ejecuta ALTER TABLE para agregarla

---

##  Notas Importantes

1. **Tabla users actualizada**: Ahora incluye `phone` para autenticación y recuperación de contraseña
2. **Misiones diarias**: Se crean automáticamente para cada usuario al registrarse
3. **Sistema de niveles**: Se actualiza automáticamente con trigger cuando cambian los puntos
4. **Recompensas**: 7 recompensas por defecto (4 badges + 3 achievements)
5. **Feedback**: Sistema de calificación de 1-5 estrellas para cada componente

---

##  Próximos Pasos

Una vez que Supabase esté configurado:

1.  Ejecutar el script SQL
2.  Verificar conexión en /health
3.  Cargar el corpus completo de frases Bora
4.  Generar embeddings con sentence-transformers
5.  Implementar endpoints de minijuegos
6.  Implementar sistema de misiones diarias
7.  Implementar sistema de recompensas
8.  Implementar interfaz de perfil
9.  Implementar feedback flotante
