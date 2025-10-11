# 🔄 Flujos de Funcionalidades - MIAPPBORA

Este documento detalla el flujo de archivos y la lógica de cada funcionalidad principal de la aplicación.

---

## 📑 Índice de Funcionalidades

1. [Autenticación (Registro/Login)](#1-autenticación-registrologin)
2. [Health Check](#2-health-check)
3. [Sistema de Perfil con Gamificación](#3-sistema-de-perfil-con-gamificación)
4. [Minijuegos (en desarrollo)](#4-minijuegos-en-desarrollo)
5. [Mentor Bora Chat (en desarrollo)](#5-mentor-bora-chat-en-desarrollo)

---

## 1. Autenticación (Registro/Login)

### 📋 Descripción
Sistema completo de autenticación con JWT tokens. Permite registro de nuevos usuarios, login, logout y recuperación de sesión.

### 🔄 Flujo de Registro

```
FRONTEND
--------
1. Usuario llena formulario
   📄 views/Auth.vue (líneas 1-500)
   - Inputs: email, username, phone, full_name, password

2. Click en "Registrarse"
   📄 stores/authStore.js → register()
   ├─ Validación de campos
   ├─ Verificación de contraseña
   └─ Llamada a API

3. Petición HTTP
   📄 services/api.js → post('/auth/register')
   └─ Envía JSON con datos del usuario

BACKEND
-------
4. Router recibe petición
   📄 routers/auth_router.py → @router.post("/register")
   ├─ Valida schema con Pydantic
   └─ Llama a servicio

5. Servicio de autenticación
   📄 services/auth_service.py → register_user()
   ├─ Valida email/username/phone únicos
   ├─ Hash de password con bcrypt
   ├─ Crea usuario en DB
   ├─ Crea level_progress inicial
   └─ Genera misiones diarias

6. Modelo de base de datos
   📄 models/database.py → User, LevelProgress
   └─ SQLAlchemy ORM inserta en Supabase

7. Respuesta al frontend
   📄 routers/auth_router.py
   ├─ Genera JWT token
   ├─ Retorna access_token + user_data
   └─ Status 201 Created

FRONTEND (continuación)
-----------------------
8. Store recibe respuesta
   📄 stores/authStore.js
   ├─ Guarda token en localStorage
   ├─ Guarda user data en state
   └─ Establece isAuthenticated = true

9. Redirección
   📄 views/Auth.vue
   └─ router.push({ name: 'Home' })
```

**Archivos involucrados:**
- Frontend: `views/Auth.vue`, `stores/authStore.js`, `services/api.js`
- Backend: `routers/auth_router.py`, `services/auth_service.py`, `models/database.py`
- DB: Tabla `users`, `level_progress`, `daily_missions`

---

### 🔄 Flujo de Login

```
FRONTEND
--------
1. Usuario ingresa credenciales
   📄 views/Auth.vue
   - Input: username/email + password

2. Click en "Iniciar Sesión"
   📄 stores/authStore.js → login()
   └─ Llamada a API

3. Petición HTTP
   📄 services/api.js → post('/auth/login')
   └─ Envía username + password

BACKEND
-------
4. Router recibe petición
   📄 routers/auth_router.py → @router.post("/login")
   └─ Llama a servicio

5. Servicio de autenticación
   📄 services/auth_service.py → login_user()
   ├─ Busca usuario por username/email
   ├─ Verifica password con bcrypt
   ├─ Actualiza last_login
   └─ Genera JWT token

6. Generación de token
   📄 services/auth_service.py → create_access_token()
   ├─ Payload: user_id, username, email
   ├─ Firma con SECRET_KEY
   └─ Expiración en 30 minutos

7. Respuesta al frontend
   └─ Retorna access_token + user_data

FRONTEND (continuación)
-----------------------
8. Store recibe respuesta
   📄 stores/authStore.js
   ├─ localStorage.setItem('token', access_token)
   ├─ user = userData
   └─ isAuthenticated = true

9. Interceptor de Axios
   📄 services/api.js (líneas 10-15)
   └─ Agrega header: Authorization: Bearer {token}
```

**Archivos involucrados:**
- Frontend: `views/Auth.vue`, `stores/authStore.js`, `services/api.js`
- Backend: `routers/auth_router.py`, `services/auth_service.py`
- DB: Tabla `users`

---

### 🔄 Flujo de Logout

```
FRONTEND
--------
1. Usuario click en "Cerrar Sesión"
   📄 components/Navigation.vue → logout()

2. Store limpia estado
   📄 stores/authStore.js → logout()
   ├─ localStorage.removeItem('token')
   ├─ user = null
   ├─ isAuthenticated = false
   └─ router.push('/auth')

3. Redirección a login
   📄 views/Auth.vue
```

**Archivos involucrados:**
- Frontend: `components/Navigation.vue`, `stores/authStore.js`
- Backend: N/A (logout es solo frontend)

---

### 🔄 Flujo de Recuperación de Sesión

```
FRONTEND
--------
1. App inicia
   📄 main.js → app.mount('#app')

2. Router verifica autenticación
   📄 router/index.js → beforeEach()
   ├─ Lee token de localStorage
   └─ Si existe token → continúa
       Si NO → redirect /auth

3. Recarga datos de usuario (opcional)
   📄 stores/authStore.js → checkAuth()
   ├─ GET /auth/me con token
   └─ Actualiza user data

BACKEND
-------
4. Middleware de autenticación
   📄 routers/auth_router.py → get_current_user()
   ├─ Extrae token del header
   ├─ Verifica firma JWT
   ├─ Valida expiración
   └─ Retorna user_id
```

**Archivos involucrados:**
- Frontend: `main.js`, `stores/authStore.js`, `services/api.js`
- Backend: `routers/auth_router.py`, `services/auth_service.py`

---

## 2. Health Check

### 📋 Descripción
Sistema de verificación de conectividad con servicios externos (Supabase, Hugging Face) y estado general del backend.

### 🔄 Flujo de Health Check

```
FRONTEND
--------
1. Usuario navega a Health Check
   📄 router → /health → views/HealthCheck.vue

2. Componente monta
   📄 views/HealthCheck.vue → onMounted()
   └─ checkHealth()

3. Llamada a servicio
   📄 services/healthService.js → checkHealth()
   └─ GET /health

BACKEND
-------
4. Router recibe petición
   📄 routers/health_router.py → @router.get("/health")
   └─ Ejecuta verificaciones

5. Verificación de Supabase
   📄 adapters/supabase_adapter.py → get_supabase_client()
   ├─ Intenta query simple: SELECT 1
   ├─ Si éxito → "connected"
   └─ Si error → "disconnected"

6. Verificación de Hugging Face
   📄 adapters/huggingface_adapter.py
   ├─ Intenta cargar modelo
   ├─ Si éxito → "connected"
   └─ Si error → "disconnected"

7. Respuesta al frontend
   📄 routers/health_router.py
   └─ JSON: {
       status: "ok",
       database: "connected",
       supabase: "connected",
       huggingface: "connected",
       timestamp: "2025-10-05T..."
     }

FRONTEND (continuación)
-----------------------
8. Componente recibe respuesta
   📄 views/HealthCheck.vue
   ├─ Actualiza healthStatus
   └─ Renderiza iconos ✅ o ❌

9. Renderizado condicional
   📄 views/HealthCheck.vue (template)
   └─ v-if para cada servicio
       ├─ ✅ si status === "connected"
       └─ ❌ si status === "disconnected"
```

**Archivos involucrados:**
- Frontend: `views/HealthCheck.vue`, `services/healthService.js`
- Backend: `routers/health_router.py`, `adapters/supabase_adapter.py`, `adapters/huggingface_adapter.py`
- DB: N/A (solo verifica conexión)

---

## 3. Sistema de Perfil con Gamificación

### 📋 Descripción
Sistema completo de perfil de usuario con gamificación: nivel, puntos, misiones diarias, recompensas, progreso y estadísticas.

### 🔄 Flujo de Carga de Perfil Completo

```
FRONTEND
--------
1. Usuario navega a "Mi Perfil"
   📄 router → /profile → views/Profile.vue

2. Componente monta
   📄 views/Profile.vue → onMounted()
   └─ loadProfile()

3. Store carga perfil
   📄 stores/profileStore.js → loadCompleteProfile()
   └─ Llamada a servicio

4. Petición HTTP
   📄 services/profileService.js → getCompleteProfile()
   └─ GET /profile/complete

BACKEND
-------
5. Router recibe petición
   📄 routers/profile_router.py → @router.get("/profile/complete")
   ├─ Extrae user_id del token JWT
   └─ Llama a servicio

6. Servicio de perfil
   📄 services/profile_service.py → get_complete_profile(user_id)
   
   A) Obtiene datos del usuario
      📄 models/database.py → User
      └─ Query: SELECT * FROM users WHERE id = user_id

   B) Obtiene/Crea level_progress
      📄 models/database.py → LevelProgress
      ├─ Query: SELECT * FROM level_progress WHERE user_id = ...
      └─ Si no existe → Crea uno nuevo

   C) Genera/Obtiene misiones diarias
      📄 services/profile_service.py → generate_daily_missions()
      ├─ Verifica si existen misiones para HOY
      ├─ Si NO existen → Crea 3 nuevas:
      │   1. "Pregunta a Bora" (chat_questions)
      │   2. "Juega y Aprende" (game_plays)
      │   3. "Perfección Total" (perfect_games)
      └─ Query: INSERT INTO daily_missions (...)

   D) Obtiene recompensas disponibles
      📄 models/database.py → Reward
      └─ Query: SELECT * FROM rewards WHERE is_active = true

   E) Obtiene recompensas del usuario
      📄 models/database.py → UserReward
      └─ Query: SELECT * FROM user_rewards WHERE user_id = ...

   F) Calcula estadísticas
      - Total de partidas jugadas
      - Partidas perfectas
      - Interacciones en chat
      - Frases aprendidas

7. Respuesta al frontend
   📄 routers/profile_router.py
   └─ JSON: {
       user: { id, username, email, full_name, ... },
       level_progress: { level, current_points, ... },
       daily_missions: [ { mission_name, current_value, ... } ],
       available_rewards: [ { name, points_required, ... } ],
       claimed_rewards: [ { reward_id, claimed_at, ... } ],
       stats: { games_played, perfect_games, ... }
     }

FRONTEND (continuación)
-----------------------
8. Store recibe respuesta
   📄 stores/profileStore.js
   ├─ userProfile = response.user
   ├─ levelProgress = response.level_progress
   ├─ dailyMissions = response.daily_missions
   ├─ availableRewards = response.available_rewards
   └─ claimedRewards = response.claimed_rewards

9. Componente renderiza
   📄 views/Profile.vue (template)
   
   A) Sección Usuario
      - Avatar (imagen circular)
      - Nombre completo
      - Username
      - Email

   B) Sección Nivel y Progreso
      - Nivel actual
      - Título ("Principiante", "Intermedio", etc.)
      - Barra de progreso
      - Puntos actuales / Puntos necesarios

   C) Sección Misiones Diarias
      - Lista de 3 misiones
      - Para cada misión:
        ├─ Icono (🎯 💬 🎮 ⭐)
        ├─ Nombre
        ├─ Progreso (current_value / target_value)
        └─ Checkbox ✅ si completada

   D) Sección Recompensas
      - Grid de recompensas disponibles
      - Para cada recompensa:
        ├─ Imagen/icono
        ├─ Nombre
        ├─ Puntos requeridos
        └─ Botón "Reclamar" (si tiene puntos suficientes)

   E) Sección Estadísticas
      - Partidas jugadas
      - Partidas perfectas
      - Frases aprendidas
      - Interacciones en chat
```

**Archivos involucrados:**
- Frontend: `views/Profile.vue`, `stores/profileStore.js`, `services/profileService.js`
- Backend: `routers/profile_router.py`, `services/profile_service.py`, `models/database.py`
- DB: Tablas `users`, `level_progress`, `daily_missions`, `rewards`, `user_rewards`, `game_sessions`

---

### 🔄 Flujo de Actualización de Misión Diaria

```
FRONTEND
--------
1. Usuario completa una acción (ej: juega un minijuego)
   📄 stores/gameStore.js → completeGame()
   └─ Trigger: updateMissionProgress()

2. Store actualiza misión
   📄 stores/profileStore.js → updateMissionProgress(type)
   └─ Llamada a servicio

3. Petición HTTP
   📄 services/profileService.js → updateMissionProgress()
   └─ POST /profile/missions/progress
       Body: { mission_type: "game_plays" }

BACKEND
-------
4. Router recibe petición
   📄 routers/profile_router.py → @router.post("/missions/progress")
   └─ Llama a servicio

5. Servicio actualiza misión
   📄 services/profile_service.py → update_mission_progress()
   
   A) Busca misión de HOY
      Query: SELECT * FROM daily_missions
             WHERE user_id = ... AND mission_date = TODAY
             AND mission_type = 'game_plays'
   
   B) Incrementa current_value
      current_value = current_value + 1
   
   C) Verifica si se completó
      IF current_value >= target_value:
         is_completed = True
         completed_at = NOW()
   
   D) Si se completó → Otorga puntos
      📄 services/profile_service.py → award_points()
      ├─ UPDATE level_progress
      │   SET current_points = current_points + points_reward
      ├─ Verifica si sube de nivel
      └─ Actualiza título si corresponde

6. Respuesta al frontend
   └─ JSON: {
       mission: { current_value, is_completed, ... },
       points_awarded: 10,
       level_up: false
     }

FRONTEND (continuación)
-----------------------
7. Store recibe respuesta
   📄 stores/profileStore.js
   ├─ Actualiza misión en array
   ├─ Si level_up → Muestra notificación
   └─ Recarga perfil completo
```

**Archivos involucrados:**
- Frontend: `stores/profileStore.js`, `services/profileService.js`
- Backend: `routers/profile_router.py`, `services/profile_service.py`
- DB: Tablas `daily_missions`, `level_progress`

---

### 🔄 Flujo de Reclamar Recompensa

```
FRONTEND
--------
1. Usuario click en "Reclamar"
   📄 views/Profile.vue → claimReward(rewardId)

2. Store reclama recompensa
   📄 stores/profileStore.js → claimReward(rewardId)
   └─ Llamada a servicio

3. Petición HTTP
   📄 services/profileService.js → claimReward(rewardId)
   └─ POST /profile/rewards/claim
       Body: { reward_id: 5 }

BACKEND
-------
4. Router recibe petición
   📄 routers/profile_router.py → @router.post("/rewards/claim")
   └─ Llama a servicio

5. Servicio procesa recompensa
   📄 services/profile_service.py → claim_reward()
   
   A) Verifica que recompensa existe
      Query: SELECT * FROM rewards WHERE id = 5
   
   B) Verifica que usuario tiene puntos suficientes
      Query: SELECT current_points FROM level_progress
             WHERE user_id = ...
      IF current_points < points_required:
         → Error 400 "Puntos insuficientes"
   
   C) Verifica que no la tiene ya
      Query: SELECT * FROM user_rewards
             WHERE user_id = ... AND reward_id = 5
      IF exists:
         → Error 400 "Ya reclamada"
   
   D) Descuenta puntos
      UPDATE level_progress
      SET current_points = current_points - points_required
   
   E) Registra recompensa
      INSERT INTO user_rewards (user_id, reward_id)
      VALUES (user_id, 5)
   
   F) Si es avatar o título → Actualiza usuario
      IF reward_type == 'avatar':
         UPDATE users SET avatar_url = reward_value
      IF reward_type == 'title':
         UPDATE users SET current_title = reward_value

6. Respuesta al frontend
   └─ JSON: {
       success: true,
       reward: { name, reward_type, ... },
       new_points: 450
     }

FRONTEND (continuación)
-----------------------
7. Store recibe respuesta
   📄 stores/profileStore.js
   ├─ Agrega recompensa a claimedRewards
   ├─ Actualiza current_points
   ├─ Muestra notificación de éxito
   └─ Recarga perfil
```

**Archivos involucrados:**
- Frontend: `views/Profile.vue`, `stores/profileStore.js`, `services/profileService.js`
- Backend: `routers/profile_router.py`, `services/profile_service.py`
- DB: Tablas `rewards`, `user_rewards`, `level_progress`, `users`

---

## 4. Minijuegos (en desarrollo)

### 📋 Descripción
Sistema de minijuegos educativos para aprender Bora. Dos tipos principales:
1. **Completar la frase**: Rellenar espacios en blanco
2. **Emparejar contexto**: Relacionar situaciones con frases

### 🔄 Flujo de Inicio de Juego

```
FRONTEND
--------
1. Usuario click en "Jugar"
   📄 views/Game.vue → startGame(gameType)

2. Store inicia sesión
   📄 stores/gameStore.js → startNewGame()
   └─ Llamada a servicio

3. Petición HTTP
   📄 services/gameService.js → startGame()
   └─ POST /games/start
       Body: { game_type: "complete_phrase" }

BACKEND
-------
4. Router recibe petición
   📄 routers/game_router.py → @router.post("/start")
   └─ Llama a servicio

5. Servicio crea sesión
   📄 services/game_service.py → create_game_session()
   
   A) Crea registro en DB
      INSERT INTO game_sessions (user_id, game_type)
      VALUES (user_id, 'complete_phrase')
   
   B) Selecciona 5 frases aleatorias
      Query: SELECT * FROM bora_phrases
             WHERE difficulty_level <= user_level
             ORDER BY RANDOM()
             LIMIT 5
   
   C) Prepara preguntas
      Para cada frase:
      ├─ Genera opciones incorrectas
      └─ Mezcla opciones

6. Respuesta al frontend
   └─ JSON: {
       session_id: 123,
       questions: [
         {
           id: 1,
           bora_text: "Mɨɨchaajúne",
           options: ["¿Cómo estás?", "Buenos días", ...],
           correct_index: 0
         },
         ...
       ]
     }

FRONTEND (continuación)
-----------------------
7. Store recibe respuesta
   📄 stores/gameStore.js
   ├─ sessionId = 123
   ├─ questions = [...]
   ├─ currentQuestionIndex = 0
   └─ answers = []

8. Componente renderiza
   📄 views/Game.vue
   └─ Muestra pregunta actual con opciones
```

---

### 🔄 Flujo de Responder Pregunta

```
FRONTEND
--------
1. Usuario selecciona opción
   📄 views/Game.vue → answerQuestion(optionIndex)

2. Store registra respuesta
   📄 stores/gameStore.js → submitAnswer()
   ├─ Verifica si es correcta
   ├─ Actualiza score
   └─ Llamada a servicio

3. Petición HTTP
   📄 services/gameService.js → submitAnswer()
   └─ POST /games/answer
       Body: {
         session_id: 123,
         phrase_id: 1,
         user_answer: "¿Cómo estás?",
         is_correct: true
       }

BACKEND
-------
4. Router recibe petición
   📄 routers/game_router.py → @router.post("/answer")
   └─ Llama a servicio

5. Servicio registra respuesta
   📄 services/game_service.py → record_answer()
   
   A) Inserta respuesta
      INSERT INTO game_answers (
        session_id, phrase_id, user_answer, is_correct, points_earned
      ) VALUES (123, 1, "¿Cómo estás?", true, 10)
   
   B) Actualiza sesión
      UPDATE game_sessions
      SET correct_answers = correct_answers + 1,
          total_score = total_score + 10
      WHERE id = 123

6. Respuesta al frontend
   └─ JSON: { success: true, points_earned: 10 }

FRONTEND (continuación)
-----------------------
7. Store avanza a siguiente pregunta
   📄 stores/gameStore.js
   ├─ currentQuestionIndex++
   └─ Si es última pregunta → completeGame()
```

---

### 🔄 Flujo de Completar Juego

```
FRONTEND
--------
1. Usuario responde última pregunta
   📄 stores/gameStore.js → completeGame()

2. Petición HTTP
   📄 services/gameService.js → completeGame()
   └─ POST /games/complete
       Body: { session_id: 123 }

BACKEND
-------
3. Servicio completa sesión
   📄 services/game_service.py → complete_game()
   
   A) Calcula estadísticas
      - Total questions: 5
      - Correct answers: 4
      - Incorrect answers: 1
      - Total score: 40
      - Is perfect: false
   
   B) Actualiza sesión
      UPDATE game_sessions
      SET completed_at = NOW(),
          is_perfect = false
   
   C) Actualiza misión diaria
      📄 services/profile_service.py → update_mission_progress()
      ├─ Incrementa "game_plays"
      └─ Si is_perfect → Incrementa "perfect_games"
   
   D) Otorga puntos
      UPDATE level_progress
      SET current_points = current_points + 40

4. Respuesta al frontend
   └─ JSON: {
       final_score: 40,
       correct: 4,
       incorrect: 1,
       is_perfect: false,
       level_up: false
     }

FRONTEND (continuación)
-----------------------
5. Store recibe respuesta
   📄 stores/gameStore.js
   └─ Muestra pantalla de resultados

6. Vista muestra resumen
   📄 views/Game.vue
   ├─ Puntaje final
   ├─ Estadísticas
   └─ Botón "Jugar de nuevo"
```

**Archivos involucrados:**
- Frontend: `views/Game.vue`, `stores/gameStore.js`, `services/gameService.js`
- Backend: `routers/game_router.py`, `services/game_service.py`
- DB: Tablas `game_sessions`, `game_answers`, `bora_phrases`, `daily_missions`, `level_progress`

---

## 5. Mentor Bora Chat (en desarrollo)

### 📋 Descripción
Sistema de chat inteligente con RAG (Retrieval-Augmented Generation) para responder preguntas sobre el idioma Bora usando frases del corpus.

### 🔄 Flujo de Conversación con Mentor Bora

```
FRONTEND
--------
1. Usuario abre chat
   📄 views/Chat.vue → mounted()
   └─ Carga conversaciones previas

2. Usuario escribe mensaje
   📄 views/Chat.vue → sendMessage()
   └─ Input: "¿Cómo se dice 'hola' en Bora?"

3. Store envía mensaje
   📄 stores/chatStore.js → sendMessage()
   └─ Llamada a servicio

4. Petición HTTP
   📄 services/chatService.js → sendMessage()
   └─ POST /chat/message
       Body: {
         conversation_id: 5,
         message: "¿Cómo se dice 'hola' en Bora?"
       }

BACKEND
-------
5. Router recibe petición
   📄 routers/chat_router.py → @router.post("/message")
   └─ Llama a servicio

6. Servicio de RAG procesa
   📄 services/rag_service.py → process_message()
   
   A) Guarda mensaje del usuario
      INSERT INTO chat_messages (
        conversation_id, role, content
      ) VALUES (5, 'user', "¿Cómo se dice 'hola' en Bora?")
   
   B) Genera embedding de la pregunta
      📄 adapters/huggingface_adapter.py → get_embedding()
      ├─ Modelo: sentence-transformers/all-MiniLM-L6-v2
      └─ Vector de 384 dimensiones
   
   C) Búsqueda semántica en Supabase
      📄 adapters/supabase_adapter.py → semantic_search()
      Query: SELECT p.*, 
             (e.embedding <=> '[0.123, ...]') as distance
             FROM bora_phrases p
             JOIN phrase_embeddings e ON p.id = e.phrase_id
             ORDER BY distance
             LIMIT 5
   
   D) Construye contexto
      context = """
      Frases relevantes:
      1. Mɨɨchaajúne - ¿Cómo estás? (Saludos)
      2. Tsani - Bien (Respuestas)
      ...
      """
   
   E) Genera respuesta con LLM
      📄 adapters/huggingface_adapter.py → generate_response()
      ├─ Modelo: Qwen/Qwen2.5-Coder-32B-Instruct (vía API)
      ├─ Prompt: f"""
      │   Eres un mentor del idioma Bora.
      │   Contexto: {context}
      │   Pregunta: {user_message}
      │   Responde de manera educativa...
      │   """
      └─ Respuesta generada
   
   F) Guarda respuesta del asistente
      INSERT INTO chat_messages (
        conversation_id, role, content
      ) VALUES (5, 'assistant', "En Bora, 'hola' se dice...")
   
   G) Actualiza misión diaria
      📄 services/profile_service.py → update_mission_progress()
      └─ Incrementa "chat_questions"

7. Respuesta al frontend
   └─ JSON: {
       conversation_id: 5,
       response: "En Bora, 'hola' se dice...",
       relevant_phrases: [
         { bora_text: "Mɨɨchaajúne", ... }
       ]
     }

FRONTEND (continuación)
-----------------------
8. Store recibe respuesta
   📄 stores/chatStore.js
   ├─ Agrega mensaje del usuario al array
   ├─ Agrega respuesta del asistente
   └─ Actualiza UI

9. Componente renderiza
   📄 views/Chat.vue
   ├─ Mensaje del usuario (derecha, azul)
   ├─ Mensaje del asistente (izquierda, gris)
   └─ Frases relevantes (cards con audio)
```

**Archivos involucrados:**
- Frontend: `views/Chat.vue`, `stores/chatStore.js`, `services/chatService.js`
- Backend: `routers/chat_router.py`, `services/rag_service.py`, `adapters/huggingface_adapter.py`, `adapters/supabase_adapter.py`
- DB: Tablas `chat_conversations`, `chat_messages`, `bora_phrases`, `phrase_embeddings`, `daily_missions`

---

## 📊 Diagrama de Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue 3)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Auth    │  │  Home    │  │  Profile │  │   Game   │    │
│  │  View    │  │  View    │  │  View    │  │   View   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│  ┌────▼─────────────▼─────────────▼─────────────▼─────┐    │
│  │              Pinia Stores                           │    │
│  │  (authStore, profileStore, gameStore, chatStore)    │    │
│  └────┬─────────────────────────────────────────┬──────┘    │
│       │                                         │           │
│  ┌────▼─────────────────────────────────────────▼──────┐    │
│  │              API Services                           │    │
│  │  (api.js con Axios + JWT interceptor)               │    │
│  └────┬────────────────────────────────────────────────┘    │
│       │                                                     │
└───────┼─────────────────────────────────────────────────────┘
        │
        │ HTTP/JSON (REST API)
        │
┌───────▼─────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Auth   │  │ Profile  │  │   Game   │  │   Chat   │    │
│  │  Router  │  │  Router  │  │  Router  │  │  Router  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│  ┌────▼─────────────▼─────────────▼─────────────▼─────┐    │
│  │                   Services                          │    │
│  │  (auth_service, profile_service, game_service, RAG) │    │
│  └────┬─────────────────────────────────────────┬──────┘    │
│       │                                         │           │
│  ┌────▼─────────────────────────────────────────▼──────┐    │
│  │            SQLAlchemy Models                        │    │
│  │  (User, LevelProgress, DailyMission, Reward, ...)  │    │
│  └────┬─────────────────────────────────────────┬──────┘    │
│       │                                         │           │
│  ┌────▼─────────────┐           ┌───────────────▼──────┐    │
│  │  Supabase        │           │  Hugging Face        │    │
│  │  Adapter         │           │  Adapter             │    │
│  └────┬─────────────┘           └───────────────┬──────┘    │
│       │                                         │           │
└───────┼─────────────────────────────────────────┼───────────┘
        │                                         │
        │                                         │
┌───────▼─────────────────────────┐   ┌───────────▼──────────┐
│     Supabase PostgreSQL          │   │  Hugging Face API    │
│  (14 tablas + pgvector)          │   │  (LLM + Embeddings)  │
└──────────────────────────────────┘   └──────────────────────┘
```

---

## 📁 Mapa de Archivos por Funcionalidad

### Autenticación
```
frontend/
  ├── views/Auth.vue ................................. Vista de login/registro
  ├── stores/authStore.js ............................ Estado de autenticación
  └── services/api.js ................................ Cliente HTTP con JWT

backend/
  ├── routers/auth_router.py ......................... Endpoints REST
  ├── services/auth_service.py ....................... Lógica de autenticación
  └── models/database.py ............................. Modelo User
```

### Perfil y Gamificación
```
frontend/
  ├── views/Profile.vue .............................. Vista de perfil
  ├── stores/profileStore.js ......................... Estado de perfil
  └── services/profileService.js ..................... Cliente API perfil

backend/
  ├── routers/profile_router.py ...................... 8 endpoints REST
  ├── services/profile_service.py .................... Lógica de gamificación
  └── models/database.py ............................. Modelos: LevelProgress,
                                                       DailyMission, Reward,
                                                       UserReward
```

### Minijuegos
```
frontend/
  ├── views/Game.vue ................................. Vista de juegos
  ├── stores/gameStore.js ............................ Estado de juego
  └── services/gameService.js ........................ Cliente API juegos

backend/
  ├── routers/game_router.py ......................... Endpoints de juegos
  ├── services/game_service.py ....................... Lógica de juegos
  └── models/database.py ............................. Modelos: GameSession,
                                                       GameAnswer, BoraPhrase
```

### Chat con RAG
```
frontend/
  ├── views/Chat.vue ................................. Vista de chat
  ├── stores/chatStore.js ............................ Estado de chat
  └── services/chatService.js ........................ Cliente API chat

backend/
  ├── routers/chat_router.py ......................... Endpoints de chat
  ├── services/rag_service.py ........................ Lógica RAG
  ├── adapters/huggingface_adapter.py ................ LLM + Embeddings
  ├── adapters/supabase_adapter.py ................... Búsqueda semántica
  └── models/database.py ............................. Modelos: ChatConversation,
                                                       ChatMessage,
                                                       PhraseEmbedding
```

---

## 🔐 Sistema de Seguridad

### JWT Token Flow
```
1. Login exitoso → Backend genera JWT
2. JWT contiene: { user_id, username, email, exp }
3. Frontend guarda en localStorage
4. Todas las peticiones incluyen: Authorization: Bearer {token}
5. Backend valida token en cada request
6. Si expira (30 min) → Logout automático
```

### Encriptación de Contraseñas
```
1. Usuario ingresa password → Frontend envía texto plano (HTTPS)
2. Backend recibe password → bcrypt.hash(password, salt_rounds=10)
3. Se guarda hash en DB (nunca texto plano)
4. Login → bcrypt.verify(password_ingresada, hash_guardado)
```

---

## 🎯 Estado Actual del Proyecto

### ✅ Completado (100%)
- Sistema de autenticación completo
- Health check funcional
- Backend de perfil con gamificación (8 endpoints)
- Frontend de perfil con diseño verde
- Sistema de misiones diarias
- Sistema de recompensas
- Scripts de población de datos
- Documentación completa

### 🚧 En Desarrollo
- Minijuegos (frontend + backend parcial)
- Chat con Mentor Bora (backend parcial)
- Carga de corpus completo de frases

### ⚠️ Pendiente de Corrección
- **CRÍTICO**: Ejecutar ALTER TABLE en Supabase para agregar columnas faltantes:
  ```sql
  ALTER TABLE daily_missions 
  ADD COLUMN IF NOT EXISTS mission_name VARCHAR(200) NOT NULL DEFAULT 'Misión';
  ALTER TABLE daily_missions 
  ADD COLUMN IF NOT EXISTS mission_description TEXT;
  ```

### 📝 Por Implementar
- Sistema de feedback flotante
- Recuperación de contraseña por SMS
- Perfiles públicos de usuarios
- Rankings globales
- Más minijuegos (traducción, audio matching)

---

## 📞 Contacto y Soporte

Para cualquier duda sobre el código o la arquitectura, revisar:
- `docs/AUTH_SYSTEM.md` - Detalles de autenticación
- `docs/DATABASE_INFO.md` - Esquema completo de BD
- `docs/SETUP_SUPABASE.md` - Configuración de Supabase
- `docs/SETUP_HUGGINGFACE.md` - Configuración de HuggingFace

---

**¡Éxito con el proyecto!** 🚀
