<template>
  <div class="chat-view">
    <div class="chat-container">
      <div class="chat-header">
        <div class="mentor-avatar-container">
          <img 
            :src="currentMentorImage" 
            alt="Mentor Bora" 
            class="mentor-avatar"
            :class="mentorState"
          />
        </div>
        <div class="header-text">
          <h1 class="chat-title">
            Mentor Bora
          </h1>
          <p class="chat-subtitle">Haz una pregunta y el Mentor te responderá usando el lexicón Bora</p>
          <p v-if="conversationId" class="conversation-indicator">
            Conversación activa #{{ conversationId }}
          </p>
        </div>
      </div>

      <div class="chat-form">
        <div class="input-row">
          <input
            v-model="query"
            type="text"
            class="text-input"
            placeholder="Ej: ¿Cómo saludo a alguien en Bora?"
            @keyup.enter="onSearch"
          />
          <button class="btn btn-primary" :disabled="isLoading || !query.trim()" @click="onSearch">
            <i v-if="!isLoading" class="fas fa-paper-plane"></i>
            <i v-else class="fas fa-spinner fa-spin"></i>
            <span>{{ isLoading ? 'Buscando...' : 'Preguntar' }}</span>
          </button>
        </div>

        <div class="options-row">
          <div class="option">
            <label>
              <input type="checkbox" v-model="fastMode" /> Respuesta rápida
            </label>
          </div>
          <div class="option flex-end">
            <button class="btn btn-secondary" :disabled="!conversationId" @click="startNewConversation">
              <i class="fas fa-redo-alt"></i>
              Nueva conversación
            </button>
          </div>
        </div>
      </div>

      <div v-if="error" class="alert alert-error">
        <i class="fas fa-exclamation-circle"></i>
        <span>{{ error }}</span>
      </div>

      <div v-if="answer" class="answer-card">
        <div class="answer-header">
          <div class="answer-icon"><i class="fas fa-comments"></i></div>
          <h2>Respuesta del Mentor</h2>
        </div>
        <p class="answer-text">{{ answer }}</p>
      </div>

      <div v-if="messagesToShow.length" class="history-section">
        <div class="history-header">
          <h3 class="section-title">Historial reciente con el Mentor</h3>
          <button
            v-if="canToggleHistory"
            class="btn btn-link"
            type="button"
            @click="toggleHistory"
          >
            {{ showFullHistory ? 'Ver menos' : 'Ver más' }}
          </button>
        </div>
        <div class="history-list">
          <div
            v-for="(m, idx) in messagesToShow"
            :key="idx"
            class="history-item"
            :class="m.role"
          >
            <div class="history-bubble">
              <span class="history-role" v-if="m.role === 'user'">Tú</span>
              <span class="history-role" v-else>Mentor</span>
              <p class="history-text">{{ m.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { chatWithLexicon } from '@/services/lexiconService'

// 🎨 CONFIGURACIÓN DE IMÁGENES DEL MENTOR BORA
// Reemplaza estos URLs con los links de tu bucket de Supabase
const MENTOR_IMAGES = {
  idle: 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/mentor/capibara-idle.png',      // Imagen cuando el usuario entra a la sección
  thinking: 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/mentor/capibara-thinking.png', // Imagen cuando está procesando la respuesta
  responding: 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/mentor/capibara-responding.png' // Imagen cuando ya tiene la respuesta
}

export default {
  name: 'Chat',
  setup() {
    const query = ref('')
    // Valores fijos para simplificar la interfaz
    const topK = 5
    const minSimilarity = 0.3
    const category = ''
    const answer = ref('')
    const results = ref([])
    const isLoading = ref(false)
    const error = ref('')
    const fastMode = ref(false)
    const conversationId = ref(null)
    const messages = ref([])
    const showFullHistory = ref(false)
    
    // 🎭 Estado del Mentor (idle, thinking, responding)
    const mentorState = ref('idle')
    
    // 🖼️ Imagen actual del Mentor según el estado
    const currentMentorImage = computed(() => {
      return MENTOR_IMAGES[mentorState.value] || MENTOR_IMAGES.idle
    })

    const visibleCount = computed(() => (showFullHistory.value ? 10 : 2))

    const messagesToShow = computed(() => {
      if (!messages.value.length) return []
      return messages.value.slice(-visibleCount.value)
    })

    const canToggleHistory = computed(() => messages.value.length > 2)
    
    // 👀 Observar cambios en isLoading y answer para cambiar el estado del Mentor
    watch(isLoading, (newValue) => {
      if (newValue) {
        mentorState.value = 'thinking'
      }
    })
    
    watch(answer, (newValue) => {
      if (newValue) {
        mentorState.value = 'responding'
      }
    })

    const startNewConversation = () => {
      conversationId.value = null
      answer.value = ''
      mentorState.value = 'idle'
      messages.value = []
      showFullHistory.value = false
    }

    const onSearch = async () => {
      error.value = ''
      answer.value = ''
      const q = query.value.trim()
      if (!q) return

      try {
        isLoading.value = true
        // Agregar mensaje del usuario al historial local
        messages.value.push({ role: 'user', content: q })
        // Mantener un límite razonable en memoria
        if (messages.value.length > 20) {
          messages.value = messages.value.slice(-20)
        }

        const data = await chatWithLexicon({
          q,
          topK: topK,
          minSimilarity: minSimilarity,
          category: category,
          fast: fastMode.value,
          conversationId: conversationId.value
        })
        console.debug('Lexicon search result:', data)
        answer.value = data?.answer || ''
        if (data?.answer) {
          messages.value.push({ role: 'assistant', content: data.answer })
          if (messages.value.length > 20) {
            messages.value = messages.value.slice(-20)
          }
        }
        if (data?.conversation_id) {
          conversationId.value = data.conversation_id
        }
      } catch (e) {
        console.error(e)
        error.value = 'Ocurrió un error al consultar el Mentor. Intenta nuevamente.'
        mentorState.value = 'idle' // Volver a idle si hay error
      } finally {
        isLoading.value = false
      }
    }

    const toggleHistory = () => {
      showFullHistory.value = !showFullHistory.value
    }

  return { 
    query, 
    topK, 
    minSimilarity, 
    category, 
    fastMode, 
    answer, 
    isLoading, 
    error, 
    onSearch,
    mentorState,
    currentMentorImage,
    conversationId,
    startNewConversation,
    messagesToShow,
    canToggleHistory,
    showFullHistory,
    toggleHistory
  }
  }
}
</script>

<style scoped>
.chat-view { min-height: 100vh; }
.chat-container {
  max-width: 900px;
  margin: 0 auto;
}

/* 🎨 Header con Mentor Avatar */
.chat-header { 
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}

.mentor-avatar-container {
  flex-shrink: 0;
}

.mentor-avatar {
  width: 180px;
  height: 180px;
  object-fit: cover;
  transition: all 0.5s ease;
  filter: drop-shadow(0 4px 12px rgba(16, 185, 129, 0.3));
}

/* Animaciones según el estado del Mentor */
.mentor-avatar.idle {
  animation: float 3s ease-in-out infinite;
}

.mentor-avatar.thinking {
  animation: pulse 1.5s ease-in-out infinite;
  filter: drop-shadow(0 4px 12px rgba(59, 130, 246, 0.5));
}

.mentor-avatar.responding {
  animation: glow 2s ease-in-out infinite;
  filter: drop-shadow(0 4px 12px rgba(16, 185, 129, 0.6));
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes glow {
  0%, 100% { 
    filter: drop-shadow(0 4px 12px rgba(16, 185, 129, 0.3));
  }
  50% { 
    filter: drop-shadow(0 8px 20px rgba(16, 185, 129, 0.8));
  }
}

.header-text {
  flex: 1;
  text-align: left;
}

.chat-title {
  font-size: 2.2rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
}
.chat-subtitle { color: #6b7280; }
.conversation-indicator {
  margin-top: 0.25rem;
  font-size: 0.95rem;
  color: #059669;
}

.chat-form { background: #fff; padding: 1.5rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); margin-bottom: 1.5rem; }
.input-row { display: flex; gap: 0.75rem; }
.text-input { flex: 1; padding: 0.9rem 1rem; border: 1px solid #e5e7eb; border-radius: 10px; font-size: 1rem; }
.btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.2rem; border-radius: 10px; font-weight: 600; border: none; cursor: pointer; }
.btn-primary { background: #10b981; color: #fff; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { background: #f3f4f6; color: #1f2937; border: 1px solid #d1d5db; }
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }

.options-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem; }
.option { display: flex; flex-direction: column; gap: 0.4rem; }
.option.flex-end { align-items: flex-end; justify-content: flex-end; }
.option.flex-2 { grid-column: span 1; }
.option input { padding: 0.6rem 0.8rem; border: 1px solid #e5e7eb; border-radius: 10px; }

.alert { display: flex; align-items: center; gap: 0.5rem; padding: 0.9rem 1rem; border-radius: 10px; margin-bottom: 1rem; }
.alert-error { background: #fee2e2; color: #991b1b; }

.answer-card { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 1rem 1.25rem; border-radius: 12px; margin-bottom: 1.5rem; }
.answer-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; }
.answer-icon { width: 34px; height: 34px; background: #10b981; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.answer-text { white-space: pre-wrap; color: #065f46; }

.history-section {
  margin-bottom: 2rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.04);
  padding: 1rem 1.25rem;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-item {
  display: flex;
}

.history-item.user {
  justify-content: flex-end;
}

.history-item.assistant {
  justify-content: flex-start;
}

.history-bubble {
  max-width: 80%;
  border-radius: 12px;
  padding: 0.6rem 0.8rem;
  background: #f3f4f6;
}

.history-item.user .history-bubble {
  background: #dcfce7;
}

.history-role {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 0.15rem;
}

.history-text {
  margin: 0;
  color: #111827;
  white-space: pre-wrap;
}

.btn-link {
  background: transparent;
  border: none;
  padding: 0;
  color: #10b981;
  font-size: 0.9rem;
  cursor: pointer;
}

.results-section { margin-bottom: 2rem; }
.results-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
.result-card { position: relative; background: #fff; border-radius: 12px; padding: 1rem; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
.result-badge { position: absolute; top: 10px; right: 10px; background: #10b981; color: #fff; border-radius: 999px; padding: 0.2rem 0.6rem; font-size: 0.85rem; }
.result-row { display: flex; gap: 0.5rem; margin-bottom: 0.25rem; }
.label { min-width: 70px; font-weight: 600; color: #6b7280; }
.value { color: #111827; }
.result-meta { margin-top: 0.5rem; }
.chip { display: inline-flex; align-items: center; gap: 0.35rem; background: #f3f4f6; padding: 0.25rem 0.6rem; border-radius: 999px; color: #374151; font-size: 0.85rem; }

/* 📱 Responsive */
@media (max-width: 768px) {
  .chat-header {
    flex-direction: column;
    text-align: center;
  }
  
  .header-text {
    text-align: center;
  }
  
  .mentor-avatar {
    width: 150px;
    height: 150px;
  }
  
  .input-row { flex-direction: column; }
  .options-row { grid-template-columns: 1fr; }
}
</style>
