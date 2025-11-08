<template>
  <div class="feedback-widget" v-if="authStore.isAuthenticated">
    <!-- Botón flotante -->
    <button 
      v-if="!showModal" 
      @click="openModal" 
      class="feedback-button"
      title="Dar feedback"
    >
      <span class="icon">💬</span>
      <span class="text">Feedback</span>
    </button>

    <!-- Modal de feedback -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <!-- Header -->
        <div class="modal-header">
          <h2>📝 Tu opinión nos importa</h2>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>

        <!-- Body -->
        <div class="modal-body">
          <p class="subtitle">Ayúdanos a mejorar MIAPPBORA con tu feedback</p>

          <form @submit.prevent="submitFeedback">
            <!-- Mentor Bora Rating -->
            <div class="rating-section">
              <label>
                <span class="label-icon">🤖</span>
                <span class="label-text">Mentor Bora</span>
              </label>
              <div class="stars">
                <button
                  v-for="star in 5"
                  :key="`mentor-${star}`"
                  type="button"
                  @click="form.mentor_rating = star"
                  class="star"
                  :class="{ active: star <= (form.mentor_rating || 0) }"
                >
                  ★
                </button>
              </div>
            </div>

            <!-- Minijuegos Rating -->
            <div class="rating-section">
              <label>
                <span class="label-icon">🎮</span>
                <span class="label-text">Minijuegos</span>
              </label>
              <div class="stars">
                <button
                  v-for="star in 5"
                  :key="`games-${star}`"
                  type="button"
                  @click="form.games_rating = star"
                  class="star"
                  :class="{ active: star <= (form.games_rating || 0) }"
                >
                  ★
                </button>
              </div>
            </div>

            <!-- App General Rating -->
            <div class="rating-section">
              <label>
                <span class="label-icon">📱</span>
                <span class="label-text">Aplicación General</span>
              </label>
              <div class="stars">
                <button
                  v-for="star in 5"
                  :key="`general-${star}`"
                  type="button"
                  @click="form.general_rating = star"
                  class="star"
                  :class="{ active: star <= (form.general_rating || 0) }"
                >
                  ★
                </button>
              </div>
            </div>

            <!-- Comentarios -->
            <div class="comments-section">
              <label for="comments">
                <span class="label-icon">💭</span>
                <span class="label-text">Comentarios (opcional)</span>
              </label>
              <textarea
                id="comments"
                v-model="form.comments"
                placeholder="Cuéntanos qué te gusta, qué mejorarías, o cualquier sugerencia..."
                rows="4"
                maxlength="1000"
              ></textarea>
              <div class="char-count">{{ form.comments?.length || 0 }}/1000</div>
            </div>

            <!-- Acciones -->
            <div class="modal-actions">
              <button 
                type="button" 
                @click="closeModal" 
                class="btn-cancel"
                :disabled="loading"
              >
                Cancelar
              </button>
              <button 
                type="submit" 
                class="btn-submit"
                :disabled="!isFormValid || loading"
              >
                <span v-if="!loading">{{ existingFeedback ? 'Actualizar' : 'Enviar' }} (+10 pts)</span>
                <span v-else>Enviando...</span>
              </button>
            </div>
          </form>

          <!-- Mensaje de éxito -->
          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>

          <!-- Mensaje de error -->
          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { getApiUrl } from '@/config/api'
import axios from 'axios'

const authStore = useAuthStore()
const showModal = ref(false)
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const existingFeedback = ref(null)

const form = ref({
  mentor_rating: null,
  games_rating: null,
  general_rating: null,
  comments: ''
})

// Validar que al menos un rating esté seleccionado
const isFormValid = computed(() => {
  return form.value.mentor_rating || form.value.games_rating || form.value.general_rating
})

const openModal = async () => {
  // Verificar autenticación antes de abrir
  if (!authStore.isAuthenticated) {
    errorMessage.value = 'Debes iniciar sesión para enviar feedback'
    return
  }
  
  showModal.value = true
  await loadExistingFeedback()
}

const closeModal = () => {
  showModal.value = false
  successMessage.value = ''
  errorMessage.value = ''
}

// Cargar feedback existente si hay
const loadExistingFeedback = async () => {
  try {
    if (!authStore.token) return

    const response = await axios.get(getApiUrl('feedback/my-feedback'), {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })

    if (response.data) {
      existingFeedback.value = response.data
      form.value = {
        mentor_rating: response.data.mentor_rating,
        games_rating: response.data.games_rating,
        general_rating: response.data.general_rating,
        comments: response.data.comments || ''
      }
    }
  } catch (error) {
    console.error('Error al cargar feedback existente:', error)
  }
}

const submitFeedback = async () => {
  if (!isFormValid.value) return

  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    if (!authStore.isAuthenticated || !authStore.token) {
      throw new Error('Debes iniciar sesión para enviar feedback')
    }

    const response = await axios.post(
      getApiUrl('feedback/submit'),
      form.value,
      {
        headers: { Authorization: `Bearer ${authStore.token}` }
      }
    )

    const isFirstTime = !existingFeedback.value
    successMessage.value = isFirstTime 
      ? '¡Gracias por tu feedback! 🎉 Has ganado +10 puntos' 
      : '¡Feedback actualizado correctamente! ✅'
    
    existingFeedback.value = response.data

    // Cerrar modal después de 2 segundos
    setTimeout(() => {
      closeModal()
      // Recargar perfil para actualizar puntos
      window.location.reload()
    }, 2000)

  } catch (error) {
    console.error('Error al enviar feedback:', error)
    errorMessage.value = error.response?.data?.detail || error.message || 'Error al enviar el feedback. Intenta nuevamente.'
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.feedback-widget {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 999;
}

.feedback-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.feedback-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.feedback-button .icon {
  font-size: 20px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.subtitle {
  margin: 0 0 24px 0;
  color: #666;
  font-size: 14px;
}

.rating-section {
  margin-bottom: 24px;
}

.rating-section label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.label-icon {
  font-size: 20px;
}

.label-text {
  font-size: 16px;
}

.stars {
  display: flex;
  gap: 8px;
}

.star {
  background: none;
  border: none;
  font-size: 32px;
  cursor: pointer;
  color: #ddd;
  transition: all 0.2s;
  padding: 0;
}

.star:hover,
.star.active {
  color: #ffd700;
  transform: scale(1.1);
}

.comments-section {
  margin-bottom: 24px;
}

.comments-section label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.comments-section textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  transition: border-color 0.2s;
}

.comments-section textarea:focus {
  outline: none;
  border-color: #667eea;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel,
.btn-submit {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-cancel:hover:not(:disabled) {
  background: #e0e0e0;
}

.btn-submit {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-submit:disabled,
.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-message {
  margin-top: 16px;
  padding: 12px;
  background: #d4edda;
  color: #155724;
  border-radius: 8px;
  border: 1px solid #c3e6cb;
  text-align: center;
  font-weight: 600;
}

.error-message {
  margin-top: 16px;
  padding: 12px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  border: 1px solid #f5c6cb;
  text-align: center;
}
</style>
