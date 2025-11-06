<template>
  <div class="profile-view">
    <div class="profile-container">
      
      <!-- Loading State -->
      <div v-if="profileStore.isLoading && !profileStore.user" class="loading-section">
        <div class="loading-spinner">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
        <p>Cargando perfil...</p>
      </div>

      <!-- Profile Content -->
      <div v-else class="profile-content">
        
        <!-- Header del Perfil -->
        <div class="profile-header">
          <div class="avatar-section">
            <div class="avatar-container">
              <img :src="profileStore.user?.avatar_url || 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-entusiasta.png'" 
                   :alt="profileStore.user?.username" 
                   class="avatar-image" />
              <button class="edit-avatar-btn" @click="showAvatarSelector = true">
                <i class="fas fa-camera"></i>
              </button>
            </div>
          </div>
          
          <div class="header-info">
            <h1 class="username">{{ profileStore.user?.username }}</h1>
            <p class="user-number">Usuario #{{ profileStore.user?.id }}</p>
            <div class="level-badge">
              <i class="fas fa-trophy"></i>
              <span>Nivel {{ profileStore.levelProgress?.level || 1 }}</span>
            </div>
            <div class="title-badge">
              <i class="fas fa-star"></i>
              <span>{{ profileStore.levelProgress?.title || 'Entusiasta' }}</span>
            </div>
          </div>
          
          <div class="full-name-section">
            <h2 class="full-name">{{ profileStore.user?.full_name || 'Sin nombre' }}</h2>
          </div>
        </div>

        <!-- Información Personal -->
        <section class="info-section">
          <div class="section-header">
            <h2><i class="fas fa-user"></i> Información Personal</h2>
          </div>
          
          <div class="info-grid">
            <div class="info-field">
              <label>Nombre Completo</label>
              <input type="text" :value="profileStore.user?.full_name" disabled class="disabled-input" />
              <small class="help-text">No editable</small>
            </div>
            
            <div class="info-field">
              <label>Usuario</label>
              <input type="text" :value="profileStore.user?.username" disabled class="disabled-input" />
              <small class="help-text">No editable</small>
            </div>
            
            <div class="info-field">
              <label>Correo Electrónico</label>
              <input type="email" :value="profileStore.user?.email" disabled class="disabled-input" />
              <small class="help-text">No editable</small>
            </div>
            
            <div class="info-field">
              <label>Teléfono</label>
              <input type="tel" v-model="editablePhone" :disabled="!isEditingPhone" 
                     :class="{ 'editable-input': isEditingPhone }" />
              <small class="help-text">Editable</small>
            </div>
          </div>
          
          <div class="action-buttons">
            <button v-if="!isEditingPhone" @click="isEditingPhone = true" class="btn btn-secondary">
              <i class="fas fa-edit"></i> Editar Teléfono
            </button>
            <button v-else @click="savePhone" class="btn btn-primary" :disabled="savingPhone">
              <i class="fas fa-save"></i> {{ savingPhone ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
            <button v-if="isEditingPhone" @click="cancelEditPhone" class="btn btn-outline">
              <i class="fas fa-times"></i> Cancelar
            </button>
          </div>
        </section>

        <!-- Progreso de Nivel -->
        <section class="progress-section">
          <div class="section-header">
            <h2><i class="fas fa-chart-line"></i> Progreso de Nivel</h2>
          </div>
          
          <div class="progress-card">
            <div class="points-display">
              <div class="current-points">
                <span class="points-number">{{ profileStore.levelProgress?.current_points || 0 }}</span>
                <span class="points-label">Puntos Actuales</span>
              </div>
              <div class="divider">/</div>
              <div class="total-points">
                <span class="points-number">
                  {{ (profileStore.levelProgress?.current_points || 0)+(profileStore.levelProgress?.points_to_next_level || 0) }}
                </span>
                <span class="points-label">Próximo Nivel</span>
              </div>
            </div>
            
            <div class="title-display">
              <i class="fas fa-crown"></i>
              <span class="current-title">{{ profileStore.levelProgress?.title || 'Entusiasta' }}</span>
            </div>
            
            <div class="progress-bar-container">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: profileStore.levelProgressPercentage + '%' }"></div>
              </div>
              <span class="progress-percentage">{{ profileStore.levelProgressPercentage }}%</span>
            </div>
            
            <div class="progress-details">
              <p>
                <strong>{{ profileStore.levelProgress?.points_to_next_level || 0 }}</strong> 
                puntos para el siguiente nivel
              </p>
            </div>
            
            <button @click="showLeaderboard" class="btn btn-primary btn-block">
              <i class="fas fa-trophy"></i> Ver Tabla de Clasificación
            </button>
          </div>
        </section>

        <!-- Misiones Diarias -->
        <section class="missions-section">
          <div class="section-header">
            <h2><i class="fas fa-tasks"></i> Misiones Diarias</h2>
            <button @click="refreshMissions" class="btn-refresh" :disabled="refreshingMissions">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshingMissions }"></i>
            </button>
          </div>
          
          <div class="missions-grid">
            <div v-for="mission in profileStore.dailyMissions" :key="mission.id" class="mission-card"
                 :class="{ 'completed': mission.is_completed }">
              <div class="mission-header">
                <h3>{{ mission.mission_name }}</h3>
                <span v-if="mission.is_completed" class="completed-badge">
                  <i class="fas fa-check-circle"></i> Completada
                </span>
              </div>
              
              <p class="mission-description">{{ mission.mission_description }}</p>
              
              <div class="mission-progress">
                <div class="progress-bar-small">
                  <div class="progress-fill-small" 
                       :style="{ width: (mission.current_value / mission.target_value * 100) + '%' }">
                  </div>
                </div>
                <span class="progress-text">
                  {{ mission.current_value }} / {{ mission.target_value }}
                </span>
              </div>
              
              <div class="mission-reward">
                <i class="fas fa-star"></i>
                <span>+{{ mission.points_reward }} puntos</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Recompensas Obtenidas -->
        <section class="rewards-section">
          <div class="section-header">
            <h2><i class="fas fa-gift"></i> Recompensas Disponibles</h2>
            <button @click="refreshRewards" class="btn-refresh" :disabled="refreshingRewards">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshingRewards }"></i>
            </button>
          </div>
          
          <div v-if="profileStore.availableRewards.length === 0" class="empty-state">
            <i class="fas fa-trophy"></i>
            <p>No hay recompensas disponibles en este momento</p>
            <small>Sigue ganando puntos para desbloquear más recompensas</small>
          </div>
          
          <div v-else class="rewards-grid">
            <div v-for="reward in profileStore.availableRewards" :key="reward.id" class="reward-card">
              <div class="reward-icon">
                <span v-if="reward.icon_url">{{ reward.icon_url }}</span>
                <i v-else class="fas fa-gift"></i>
              </div>
              
              <div class="reward-info">
                <h3>{{ reward.name }}</h3>
                <p>{{ reward.description }}</p>
                
                <div class="reward-type">
                  <i class="fas fa-tag"></i>
                  <span>{{ getRewardTypeLabel(reward.reward_type) }}</span>
                </div>
                
                <div class="reward-cost">
                  <i class="fas fa-star"></i>
                  <span>{{ reward.points_required }} puntos</span>
                </div>
              </div>
              
              <button @click="claimReward(reward.id)" class="btn btn-primary btn-claim"
                      :disabled="claimingReward === reward.id">
                <i class="fas fa-download"></i>
                {{ claimingReward === reward.id ? 'Reclamando...' : 'Reclamar' }}
              </button>
            </div>
          </div>

          <!-- Recompensas ya reclamadas -->
          <div v-if="profileStore.claimedRewards.length > 0" class="claimed-section">
            <h3><i class="fas fa-check-double"></i> Recompensas Reclamadas</h3>
            <div class="claimed-grid">
              <div v-for="userReward in profileStore.claimedRewards" :key="userReward.id" class="claimed-card">
                <div class="claimed-icon">
                  <span v-if="userReward.reward.icon_url">{{ userReward.reward.icon_url }}</span>
                  <i v-else class="fas fa-trophy"></i>
                </div>
                <div class="claimed-info">
                  <h4>{{ userReward.reward.name }}</h4>
                  <small>Reclamada el {{ formatDate(userReward.claimed_at) }}</small>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>

    <!-- Modal para seleccionar avatar -->
    <AvatarSelector
      :show="showAvatarSelector"
      :currentAvatar="profileStore.user?.avatar_url"
      @close="showAvatarSelector = false"
      @avatar-selected="handleAvatarSelected"
    />

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProfileStore } from '../stores/profileStore'
import { useAuthStore } from '../stores/authStore'
import AvatarSelector from '../components/AvatarSelector.vue'

const router = useRouter()
const profileStore = useProfileStore()
const authStore = useAuthStore()

// Estados locales
const isEditingPhone = ref(false)
const editablePhone = ref('')
const savingPhone = ref(false)
const refreshingMissions = ref(false)
const refreshingRewards = ref(false)
const claimingReward = ref(null)
const showAvatarSelector = ref(false)

// Cargar datos al montar
onMounted(async () => {
  try {
    await profileStore.loadCompleteProfile()
    editablePhone.value = profileStore.user?.phone || ''
  } catch (error) {
    console.error('Error loading profile:', error)
    alert('Error al cargar el perfil. Por favor, recarga la página.')
  }
})

// Métodos
const savePhone = async () => {
  if (!editablePhone.value) {
    alert('Por favor ingresa un número de teléfono válido')
    return
  }
  
  savingPhone.value = true
  try {
    await profileStore.updateProfile({ phone: editablePhone.value })
    isEditingPhone.value = false
    alert('Teléfono actualizado exitosamente')
  } catch (error) {
    alert('Error al actualizar el teléfono')
  } finally {
    savingPhone.value = false
  }
}

const cancelEditPhone = () => {
  editablePhone.value = profileStore.user?.phone || ''
  isEditingPhone.value = false
}

const handleAvatarSelected = async (avatarUrl) => {
  // El componente AvatarSelector ya guardó el avatar
  // Aquí solo recargamos el perfil para actualizar la UI
  await profileStore.loadCompleteProfile()
}

const refreshMissions = async () => {
  refreshingMissions.value = true
  try {
    await profileStore.refreshMissions()
  } finally {
    refreshingMissions.value = false
  }
}

const refreshRewards = async () => {
  refreshingRewards.value = true
  try {
    await profileStore.refreshRewards()
  } finally {
    refreshingRewards.value = false
  }
}

const claimReward = async (rewardId) => {
  if (!confirm('¿Deseas reclamar esta recompensa?')) return
  
  claimingReward.value = rewardId
  try {
    const response = await profileStore.claimReward(rewardId)
    alert(`¡Recompensa reclamada! ${response.message}`)
  } catch (error) {
    alert(error.message || 'Error al reclamar la recompensa')
  } finally {
    claimingReward.value = null
  }
}

const showLeaderboard = () => {
  router.push('/leaderboard')
}

const getRewardTypeLabel = (type) => {
  const labels = {
    'avatar': 'Avatar',
    'badge': 'Insignia',
    'title': 'Título',
    'achievement': 'Logro'
  }
  return labels[type] || type
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('es-ES', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
}
</script>

<style scoped>
.profile-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  padding: 2rem 1rem;
}

.profile-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* Loading */
.loading-section {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
}

.loading-spinner {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* Profile Header */
.profile-header {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 2rem;
  align-items: center;
}

.avatar-container {
  position: relative;
  width: 120px;
  height: 120px;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #10b981;
}

.edit-avatar-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
}

.edit-avatar-btn:hover {
  background: #059669;
  transform: scale(1.1);
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.username {
  font-size: 2rem;
  font-weight: bold;
  color: #2d3748;
  margin: 0;
}

.user-number {
  color: #718096;
  margin: 0;
}

.level-badge, .title-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border-radius: 20px;
  font-weight: 600;
  width: fit-content;
}

.full-name-section {
  text-align: right;
}

.full-name {
  font-size: 1.5rem;
  color: #4a5568;
  margin: 0;
}

/* Sections */
.info-section, .progress-section, .missions-section, .rewards-section {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.section-header h2 {
  font-size: 1.5rem;
  color: #2d3748;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-refresh {
  background: none;
  border: none;
  color: #10b981;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.3s;
}

.btn-refresh:hover:not(:disabled) {
  background: #f7fafc;
  transform: rotate(180deg);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.info-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-field label {
  font-weight: 600;
  color: #4a5568;
  font-size: 0.9rem;
}

.info-field input {
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

.disabled-input {
  background: #f7fafc;
  color: #718096;
  cursor: not-allowed;
}

.editable-input {
  border-color: #10b981;
}

.help-text {
  color: #a0aec0;
  font-size: 0.85rem;
}

/* Progress Card */
.progress-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.points-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 15px;
  color: white;
}

.current-points, .total-points {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.points-number {
  font-size: 2.5rem;
  font-weight: bold;
}

.points-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.divider {
  font-size: 2rem;
  opacity: 0.6;
}

.title-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: #2d3748;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-bar {
  flex: 1;
  height: 20px;
  background: #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.5s ease;
}

.progress-percentage {
  font-weight: 600;
  color: #10b981;
  min-width: 50px;
  text-align: right;
}

.progress-details {
  text-align: center;
  color: #718096;
}

/* Missions Grid */
.missions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.mission-card {
  padding: 1.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.3s;
}

.mission-card:hover {
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}

.mission-card.completed {
  border-color: #48bb78;
  background: #f0fff4;
}

.mission-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 0.75rem;
}

.mission-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.1rem;
}

.completed-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  background: #48bb78;
  color: white;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.mission-description {
  color: #718096;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.mission-progress {
  margin-bottom: 1rem;
}

.progress-bar-small {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill-small {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.3s;
}

.progress-text {
  font-size: 0.9rem;
  color: #4a5568;
  font-weight: 600;
}

.mission-reward {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #f59e0b;
  font-weight: 600;
}

/* Rewards Grid */
.rewards-grid, .claimed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.reward-card, .claimed-card {
  padding: 1.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: all 0.3s;
}

.reward-card:hover {
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}

.reward-icon {
  font-size: 3rem;
  text-align: center;
}

.reward-info h3 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
}

.reward-info p {
  color: #718096;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.reward-type, .reward-cost {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #4a5568;
}

.btn-claim {
  margin-top: auto;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #a0aec0;
}

.empty-state i {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.claimed-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e2e8f0;
}

.claimed-section h3 {
  color: #2d3748;
  margin-bottom: 1rem;
}

.claimed-card {
  flex-direction: row;
  align-items: center;
  border-color: #48bb78;
  background: #f0fff4;
}

.claimed-icon {
  font-size: 2rem;
}

.claimed-info h4 {
  margin: 0;
  color: #2d3748;
}

.claimed-info small {
  color: #718096;
}

/* Buttons */
.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
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

.btn-secondary {
  background: #4a5568;
  color: white;
}

.btn-outline {
  background: white;
  color: #10b981;
  border: 2px solid #10b981;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
  justify-content: center;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 20px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 2px solid #e2e8f0;
}

.modal-header h2 {
  margin: 0;
  color: #2d3748;
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
  padding: 1.5rem;
}

.avatar-input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.avatar-preview {
  text-align: center;
  padding: 1rem;
}

.avatar-preview img {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #10b981;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 2px solid #e2e8f0;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

/* Responsive */
@media (max-width: 768px) {
  .profile-header {
    grid-template-columns: 1fr;
    text-align: center;
  }
  
  .avatar-container {
    margin: 0 auto;
  }
  
  .full-name-section {
    text-align: center;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .missions-grid, .rewards-grid {
    grid-template-columns: 1fr;
  }
}
</style>
