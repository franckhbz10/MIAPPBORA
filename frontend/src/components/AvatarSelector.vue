<template>
  <div class="avatar-selector-modal" v-if="show" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h2><i class="fas fa-images"></i> Selecciona tu Avatar</h2>
        <button class="close-btn" @click="close">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i>
          <p>Cargando avatares...</p>
        </div>
        
        <!-- Avatar Grid -->
        <div v-else class="avatars-grid">
          <!-- Sección: Avatares de Nivel -->
          <div v-if="levelAvatars.length > 0" class="section">
            <h3><i class="fas fa-trophy"></i> Avatares de Nivel</h3>
            <div class="avatars-row">
              <div 
                v-for="avatar in levelAvatars" 
                :key="avatar.id"
                class="avatar-card"
                :class="{ 
                  'selected': avatar.avatar_url === selectedAvatar,
                  'current': avatar.avatar_url === currentAvatar,
                  'current-level': avatar.is_current_level
                }"
                @click="selectAvatar(avatar.avatar_url)"
              >
                <div class="avatar-image-container">
                  <img :src="avatar.avatar_url" :alt="avatar.name" @error="handleImageError" />
                  
                  <!-- Badge de nivel actual -->
                  <div v-if="avatar.is_current_level" class="level-badge">
                    <i class="fas fa-star"></i>
                  </div>
                  
                  <!-- Indicador de seleccionado -->
                  <div v-if="avatar.avatar_url === currentAvatar" class="current-badge">
                    <i class="fas fa-check-circle"></i>
                    <span>Actual</span>
                  </div>
                </div>
                
                <div class="avatar-info">
                  <h4>{{ avatar.name }}</h4>
                  <p class="avatar-level">Nivel {{ avatar.level }}</p>
                  <p class="avatar-description">{{ avatar.description }}</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Sección: Avatares de Recompensas -->
          <div v-if="rewardAvatars.length > 0" class="section">
            <h3><i class="fas fa-gift"></i> Avatares Especiales</h3>
            <div class="avatars-row">
              <div 
                v-for="avatar in rewardAvatars" 
                :key="avatar.id"
                class="avatar-card special"
                :class="{ 
                  'selected': avatar.avatar_url === selectedAvatar,
                  'current': avatar.avatar_url === currentAvatar
                }"
                @click="selectAvatar(avatar.avatar_url)"
              >
                <div class="avatar-image-container">
                  <img :src="avatar.avatar_url" :alt="avatar.name" @error="handleImageError" />
                  
                  <!-- Indicador de especial -->
                  <div class="special-badge">
                    <i class="fas fa-crown"></i>
                  </div>
                  
                  <!-- Indicador de seleccionado -->
                  <div v-if="avatar.avatar_url === currentAvatar" class="current-badge">
                    <i class="fas fa-check-circle"></i>
                    <span>Actual</span>
                  </div>
                </div>
                
                <div class="avatar-info">
                  <h4>{{ avatar.name }}</h4>
                  <p class="avatar-description">{{ avatar.description }}</p>
                  <p class="unlock-date">Desbloqueado: {{ avatar.unlocked_at }}</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Empty State -->
          <div v-if="totalAvatars === 0" class="empty-state">
            <i class="fas fa-image"></i>
            <p>No hay avatares disponibles</p>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button 
          @click="confirmSelection" 
          class="btn btn-primary"
          :disabled="!selectedAvatar || selectedAvatar === currentAvatar || saving"
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
import { ref, computed, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  currentAvatar: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'avatar-selected'])

const loading = ref(false)
const saving = ref(false)
const selectedAvatar = ref('')
const levelAvatars = ref([])
const rewardAvatars = ref([])

const totalAvatars = computed(() => levelAvatars.value.length + rewardAvatars.value.length)

const loadAvailableAvatars = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await api.get('/profile/avatars/available', {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.success) {
      const avatars = response.data.unlocked_avatars
      
      // Separar por tipo
      levelAvatars.value = avatars.filter(a => a.type === 'level')
      rewardAvatars.value = avatars.filter(a => a.type === 'reward')
      
      // Seleccionar el avatar actual por defecto
      selectedAvatar.value = response.data.current_avatar
    }
  } catch (error) {
    console.error('Error loading avatars:', error)
    alert('Error al cargar avatares disponibles')
  } finally {
    loading.value = false
  }
}

const selectAvatar = (avatarUrl) => {
  selectedAvatar.value = avatarUrl
}

const confirmSelection = async () => {
  if (!selectedAvatar.value || selectedAvatar.value === props.currentAvatar) return
  
  saving.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await api.put(
      '/profile/avatar/select',
      { avatar_url: selectedAvatar.value },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    
    if (response.data.success) {
      emit('avatar-selected', selectedAvatar.value)
      alert('¡Avatar actualizado exitosamente!')
      close()
    }
  } catch (error) {
    console.error('Error selecting avatar:', error)
    alert(error.response?.data?.detail || 'Error al seleccionar avatar')
  } finally {
    saving.value = false
  }
}

const handleImageError = (event) => {
  // Fallback si la imagen no carga
  event.target.src = 'https://ui-avatars.com/api/?name=Avatar&background=10b981&color=fff'
}

const close = () => {
  emit('close')
}

// Watch para cargar avatares cuando se abre el modal
watch(() => props.show, (newValue) => {
  if (newValue) {
    loadAvailableAvatars()
  }
})
</script>

<style scoped>
.avatar-selector-modal {
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

.avatars-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

.avatar-card {
  border: 3px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.avatar-card:hover {
  border-color: #10b981;
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.2);
}

.avatar-card.selected {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.avatar-card.current-level {
  border-color: #f59e0b;
}

.avatar-card.special {
  border-color: #8b5cf6;
}

.avatar-image-container {
  position: relative;
  width: 100%;
  padding-top: 100%;
  margin-bottom: 1rem;
}

.avatar-image-container img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #10b981;
}

.level-badge,
.special-badge {
  position: absolute;
  top: -8px;
  right: -8px;
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

.special-badge {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.current-badge {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
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

.avatar-info {
  text-align: center;
}

.avatar-info h4 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.1rem;
}

.avatar-level {
  color: #f59e0b;
  font-weight: 600;
  font-size: 0.9rem;
  margin: 0.25rem 0;
}

.avatar-description {
  color: #718096;
  font-size: 0.85rem;
  margin: 0.25rem 0;
}

.unlock-date {
  color: #8b5cf6;
  font-size: 0.8rem;
  font-weight: 600;
  margin-top: 0.5rem;
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
  .avatars-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .avatars-row {
    grid-template-columns: 1fr;
  }
}
</style>
