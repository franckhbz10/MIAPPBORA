<template>
  <div class="chat-view">
    <div class="chat-container">
      <div class="chat-header">
        <h1 class="chat-title">
          <i class="fas fa-robot"></i>
          Mentor Bora
        </h1>
        <p class="chat-subtitle">Haz una pregunta y el Mentor te responderá usando el lexicón Bora</p>
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
            <label>Top K</label>
            <input type="number" v-model.number="topK" min="1" max="50" />
          </div>
          <div class="option">
            <label>Similitud mínima</label>
            <input type="number" step="0.05" v-model.number="minSimilarity" min="0" max="1" />
          </div>
          <div class="option flex-2">
            <label>Categoría (opcional)</label>
            <input type="text" v-model="category" placeholder="p.ej. Saludos" />
          </div>
          <div class="option">
            <label>
              <input type="checkbox" v-model="fastMode" /> Respuesta rápida
            </label>
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

      <div v-if="results.length" class="results-section">
        <h3 class="section-title">Frases recuperadas</h3>
        <div class="results-grid">
          <div v-for="(r, idx) in results" :key="idx" class="result-card">
            <div class="result-badge">{{ (r.similarity ?? 0).toFixed(2) }}</div>
            <div class="result-content">
              <div class="result-row">
                <span class="label">Bora</span>
                <span class="value">{{ r.bora_text }}</span>
              </div>
              <div class="result-row">
                <span class="label">Español</span>
                <span class="value">{{ r.spanish_text }}</span>
              </div>
              <div class="result-meta">
                <span class="chip"><i class="fas fa-tag"></i> {{ r.category || 'General' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { searchLexicon } from '@/services/lexiconService'

export default {
  name: 'Chat',
  setup() {
    const query = ref('')
    const topK = ref(10)
    const minSimilarity = ref(0.7)
    const category = ref('')
  const answer = ref('')
    const results = ref([])
    const isLoading = ref(false)
    const error = ref('')
  const fastMode = ref(false)

    const onSearch = async () => {
      error.value = ''
      answer.value = ''
      results.value = []
      const q = query.value.trim()
      if (!q) return

      try {
        isLoading.value = true
        const data = await searchLexicon({
          q,
          topK: topK.value,
          minSimilarity: minSimilarity.value,
          category: category.value,
          fast: fastMode.value
        })
        console.debug('Lexicon search result:', data)
        answer.value = data?.answer || ''
        results.value = data?.results || []
      } catch (e) {
        console.error(e)
        error.value = 'Ocurrió un error al consultar el Mentor. Intenta nuevamente.'
      } finally {
        isLoading.value = false
      }
    }

  return { query, topK, minSimilarity, category, fastMode, answer, results, isLoading, error, onSearch }
  }
}
</script>

<style scoped>
.chat-view { min-height: 100vh; }
.chat-container {
  max-width: 900px;
  margin: 0 auto;
}
.chat-header { text-align: center; margin-bottom: 2rem; }
.chat-title {
  font-size: 2.2rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
}
.chat-subtitle { color: #6b7280; }

.chat-form { background: #fff; padding: 1.5rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); margin-bottom: 1.5rem; }
.input-row { display: flex; gap: 0.75rem; }
.text-input { flex: 1; padding: 0.9rem 1rem; border: 1px solid #e5e7eb; border-radius: 10px; font-size: 1rem; }
.btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.2rem; border-radius: 10px; font-weight: 600; border: none; cursor: pointer; }
.btn-primary { background: #10b981; color: #fff; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.options-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem; }
.option { display: flex; flex-direction: column; gap: 0.4rem; }
.option.flex-2 { grid-column: span 1; }
.option input { padding: 0.6rem 0.8rem; border: 1px solid #e5e7eb; border-radius: 10px; }

.alert { display: flex; align-items: center; gap: 0.5rem; padding: 0.9rem 1rem; border-radius: 10px; margin-bottom: 1rem; }
.alert-error { background: #fee2e2; color: #991b1b; }

.answer-card { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 1rem 1.25rem; border-radius: 12px; margin-bottom: 1.5rem; }
.answer-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; }
.answer-icon { width: 34px; height: 34px; background: #10b981; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.answer-text { white-space: pre-wrap; color: #065f46; }

.results-section { margin-bottom: 2rem; }
.results-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
.result-card { position: relative; background: #fff; border-radius: 12px; padding: 1rem; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
.result-badge { position: absolute; top: 10px; right: 10px; background: #10b981; color: #fff; border-radius: 999px; padding: 0.2rem 0.6rem; font-size: 0.85rem; }
.result-row { display: flex; gap: 0.5rem; margin-bottom: 0.25rem; }
.label { min-width: 70px; font-weight: 600; color: #6b7280; }
.value { color: #111827; }
.result-meta { margin-top: 0.5rem; }
.chip { display: inline-flex; align-items: center; gap: 0.35rem; background: #f3f4f6; padding: 0.25rem 0.6rem; border-radius: 999px; color: #374151; font-size: 0.85rem; }

@media (max-width: 768px) {
  .input-row { flex-direction: column; }
  .options-row { grid-template-columns: 1fr; }
}
</style>
