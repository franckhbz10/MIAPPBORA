<template>
  <div class="title-selector-modal" v-if="show" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h2><i class="fas fa-crown"></i> Selecciona tu Título</h2>
        <button class="close-btn" @click="close">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i>
          <p>Cargando títulos...</p>
        </div>
        
        <!-- Titles Grid -->
        <div v-else class="titles-grid">
          <!-- Sección: Títulos de Nivel -->
          <div v-if="levelTitles.length > 0" class="section">
            <h3><i class="fas fa-trophy"></i> Títulos de Nivel</h3>
            <div class="titles-row">
              <div 
                v-for="title in levelTitles" 
                :key="title.id"
                class="title-card"
                :class="{ 
                  'selected': title.title_value === selectedTitle,
                  'current': title.title_value === currentTitle,
                  'current-level': title.is_current_level
                }"
                @click="selectTitle(title.title_value)"
              >
                <div class="title-icon-container">
                  <div class="title-icon">
                    <i class="fas fa-star"></i>
                  </div>
                  
                  <!-- Badge de nivel actual -->
                  <div v-if="title.is_current_level" class="level-badge">
                    <i class="fas fa-arrow-up"></i>
                  </div>
                  
                  <!-- Indicador de seleccionado -->
                  <div v-if="title.title_value === currentTitle" class="current-badge">
                    <i class="fas fa-check-circle"></i>
                    <span>Actual</span>
                  </div>
                </div>
                
                <div class="title-info">
                  <h4>{{ title.name }}</h4>
                  <p class="title-level">Nivel {{ title.level }}</p>
                  <p class="title-description">{{ title.description }}</p>
                  <div class="title-preview">
                    <i class="fas fa-quote-left"></i>
                    <span>{{ title.title_value }}</span>
                    <i class="fas fa-quote-right"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Sección: Títulos de Recompensas -->
          <div v-if="rewardTitles.length > 0" class="section">
            <h3><i class="fas fa-gift"></i> Títulos Especiales</h3>
            <div class="titles-row">
              <div 
                v-for="title in rewardTitles" 
                :key="title.id"
                class="title-card special"
                :class="{ 
                  'selected': title.title_value === selectedTitle,
                  'current': title.title_value === currentTitle
                }"
                @click="selectTitle(title.title_value)"
              >
                <div class="title-icon-container">
                  <div class="title-icon special-icon">
                    <span class="icon-emoji">{{ title.icon }}</span>
                  </div>
                  
                  <!-- Indicador de seleccionado -->
                  <div v-if="title.title_value === currentTitle" class="current-badge">
                    <i class="fas fa-check-circle"></i>
                    <span>Actual</span>
                  </div>
                </div>
                
                <div class="title-info">
                  <h4>{{ title.name }}</h4>
                  <p class="title-description">{{ title.description }}</p>
                  <div class="title-preview special-preview">
                    <i class="fas fa-quote-left"></i>
                    <span>{{ title.title_value }}</span>
                    <i class="fas fa-quote-right"></i>
                  </div>
                  <p class="unlock-date">
                    <i class="fas fa-calendar-alt"></i>
                    Desbloqueado: {{ title.unlocked_at }}
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Empty State -->
          <div v-if="totalTitles === 0" class="empty-state">
            <i class="fas fa-crown"></i>
            <p>No hay títulos disponibles</p>
            <small>Sube de nivel o reclama recompensas para desbloquear títulos</small>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button 
          @click="confirmSelection" 
          class="btn btn-primary"
          :disabled="!selectedTitle || selectedTitle === currentTitle || saving"
        >
          <i class="fas fa-check"></i>
          {{ saving ? 'Guardando...' : 'Confirmar Selección' }}
        </button>
        <button @click="close" class="btn btn-outline">
          <i class="fas fa-times"></i>
          Cancelar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  currentTitle: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'title-selected'])

const loading = ref(false)
const saving = ref(false)
const selectedTitle = ref('')
const levelTitles = ref([])
const rewardTitles = ref([])

const totalTitles = computed(() => levelTitles.value.length + rewardTitles.value.length)

const loadAvailableTitles = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await api.get('/profile/titles/available', {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.success) {
      const titles = response.data.unlocked_titles
      
      // Separar por tipo
      levelTitles.value = titles.filter(t => t.type === 'level')
      rewardTitles.value = titles.filter(t => t.type === 'reward')
      
      // Seleccionar el título actual por defecto
      selectedTitle.value = response.data.current_title
    }
  } catch (error) {
    console.error('Error loading titles:', error)
    alert('Error al cargar títulos disponibles')
  } finally {
    loading.value = false
  }
}

const selectTitle = (titleValue) => {
  selectedTitle.value = titleValue
}

const confirmSelection = async () => {
  if (!selectedTitle.value || selectedTitle.value === props.currentTitle) return
  
  saving.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await api.put(
      '/profile/title/select',
      { title_value: selectedTitle.value },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    
    if (response.data.success) {
      emit('title-selected', selectedTitle.value)
      alert('¡Título actualizado exitosamente!')
      close()
    }
  } catch (error) {
    console.error('Error selecting title:', error)
    alert(error.response?.data?.detail || 'Error al seleccionar título')
  } finally {
    saving.value = false
  }
}

const close = () => {
  emit('close')
}

// Watch para cargar títulos cuando se abre el modal
watch(() => props.show, (newValue) => {
  if (newValue) {
    loadAvailableTitles()
  }
})

// Listener para evento de título desbloqueado
const handleTitleUnlocked = () => {
  if (props.show) {
    loadAvailableTitles()
  }
}

onMounted(() => {
  window.addEventListener('title-unlocked', handleTitleUnlocked)
})

onUnmounted(() => {
  window.removeEventListener('title-unlocked', handleTitleUnlocked)
})
</script>

<style scoped>
.title-selector-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 20px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 2px solid #e2e8f0;
}

.modal-header h2 {
  margin: 0;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #a0aec0;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #f7fafc;
  color: #10b981;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
  color: #718096;
}

.loading-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.section {
  margin-bottom: 2rem;
}

.section h3 {
  color: #2d3748;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.3rem;
}

.titles-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.title-card {
  border: 3px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.title-card:hover {
  border-color: #10b981;
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.2);
}

.title-card.selected {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.title-card.current-level {
  border-color: #f59e0b;
}

.title-card.special {
  border-color: #8b5cf6;
}

.title-icon-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 0.5rem;
}

.title-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.special-icon {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.icon-emoji {
  font-size: 2.5rem;
}

.level-badge {
  position: absolute;
  top: -8px;
  right: calc(50% - 50px);
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
  border: 3px solid white;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.current-badge {
  position: absolute;
  bottom: -12px;
  background: #10b981;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
}

.title-info {
  text-align: center;
}

.title-info h4 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.1rem;
}

.title-level {
  color: #f59e0b;
  font-weight: 600;
  font-size: 0.9rem;
  margin: 0.25rem 0;
}

.title-description {
  color: #718096;
  font-size: 0.85rem;
  margin: 0.5rem 0;
}

.title-preview {
  background: linear-gradient(135deg, #f7fafc, #edf2f7);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-weight: 600;
  color: #2d3748;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 1.1rem;
  border: 2px solid #e2e8f0;
}

.special-preview {
  background: linear-gradient(135deg, #faf5ff, #f3e8ff);
  border-color: #ddd6fe;
  color: #6b21a8;
}

.title-preview i {
  font-size: 0.7rem;
  opacity: 0.6;
}

.unlock-date {
  color: #8b5cf6;
  font-size: 0.8rem;
  font-weight: 600;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #a0aec0;
}

.empty-state i {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state small {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 2px solid #e2e8f0;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-outline {
  background: white;
  color: #10b981;
  border: 2px solid #10b981;
}

.btn-outline:hover {
  background: #ecfdf5;
}

@media (max-width: 768px) {
  .titles-row {
    grid-template-columns: 1fr;
  }
}
</style>
