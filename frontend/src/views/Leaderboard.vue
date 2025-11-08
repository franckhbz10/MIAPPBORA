<template>
  <div class="leaderboard-view">
    <div class="leaderboard-container">
      
      <!-- Header -->
      <div class="header">
        <h1>
          <i class="fas fa-trophy"></i>
          Tabla de Clasificación
        </h1>
        <p class="subtitle">Top {{ limit }} usuarios con más puntos</p>
        <button @click="refreshLeaderboard" class="btn-refresh" :disabled="loading">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          Actualizar
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading && !leaderboardData" class="loading-section">
        <i class="fas fa-spinner fa-spin"></i>
        <p>Cargando clasificación...</p>
      </div>

      <!-- Leaderboard Content -->
      <div v-else class="leaderboard-content">
        
        <!-- Top 3 Podium -->
        <div v-if="topThree.length > 0" class="podium">
          <!-- 2nd Place -->
          <div v-if="topThree[1]" class="podium-place second">
            <div class="rank-badge silver">
              <i class="fas fa-medal"></i>
              <span>2</span>
            </div>
            <div class="user-card">
              <img :src="topThree[1].avatar_url || defaultAvatar" :alt="topThree[1].username" class="avatar" />
              <h3>{{ topThree[1].username }}</h3>
              <p class="points">{{ topThree[1].total_points }} pts</p>
              <p class="level">Nivel {{ topThree[1].level }}</p>
            </div>
          </div>

          <!-- 1st Place -->
          <div v-if="topThree[0]" class="podium-place first">
            <div class="crown">
              <i class="fas fa-crown"></i>
            </div>
            <div class="rank-badge gold">
              <i class="fas fa-medal"></i>
              <span>1</span>
            </div>
            <div class="user-card champion">
              <img :src="topThree[0].avatar_url || defaultAvatar" :alt="topThree[0].username" class="avatar" />
              <h3>{{ topThree[0].username }}</h3>
              <p class="points">{{ topThree[0].total_points }} pts</p>
              <p class="level">Nivel {{ topThree[0].level }}</p>
            </div>
          </div>

          <!-- 3rd Place -->
          <div v-if="topThree[2]" class="podium-place third">
            <div class="rank-badge bronze">
              <i class="fas fa-medal"></i>
              <span>3</span>
            </div>
            <div class="user-card">
              <img :src="topThree[2].avatar_url || defaultAvatar" :alt="topThree[2].username" class="avatar" />
              <h3>{{ topThree[2].username }}</h3>
              <p class="points">{{ topThree[2].total_points }} pts</p>
              <p class="level">Nivel {{ topThree[2].level }}</p>
            </div>
          </div>
        </div>

        <!-- Full Ranking Table -->
        <div class="ranking-table">
          <h2><i class="fas fa-list-ol"></i> Clasificación Completa</h2>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Posición</th>
                  <th>Usuario</th>
                  <th>Puntos</th>
                  <th>Nivel</th>
                  <th>Título</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in leaderboardData?.leaderboard" 
                    :key="user.user_id"
                    :class="{ 'current-user': user.is_current_user, 'top-three': user.position <= 3 }">
                  <td class="position">
                    <span class="rank-number" :class="getRankClass(user.position)">
                      {{ user.position }}
                    </span>
                  </td>
                  <td class="user-info">
                    <img :src="user.avatar_url || defaultAvatar" :alt="user.username" class="user-avatar" />
                    <div class="user-details">
                      <span class="username">{{ user.username }}</span>
                      <span v-if="user.is_current_user" class="you-badge">Tú</span>
                    </div>
                  </td>
                  <td class="points">
                    <i class="fas fa-star"></i>
                    {{ user.total_points }}
                  </td>
                  <td class="level">
                    <i class="fas fa-trophy"></i>
                    {{ user.level }}
                  </td>
                  <td class="title">{{ user.current_title || 'Sin título' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Current User Position (if not in top) -->
        <div v-if="leaderboardData?.current_user" class="current-user-card">
          <h3><i class="fas fa-user"></i> Tu Posición</h3>
          <div class="user-position">
            <div class="position-badge">
              <span class="rank">#{{ leaderboardData.current_user.position }}</span>
              <span class="total">de {{ leaderboardData.total_users }}</span>
            </div>
            <div class="user-stats">
              <img :src="leaderboardData.current_user.avatar_url || defaultAvatar" 
                   :alt="leaderboardData.current_user.username" 
                   class="avatar" />
              <div class="stats">
                <h4>{{ leaderboardData.current_user.username }}</h4>
                <p><i class="fas fa-star"></i> {{ leaderboardData.current_user.total_points }} puntos</p>
                <p><i class="fas fa-trophy"></i> Nivel {{ leaderboardData.current_user.level }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats Footer -->
        <div class="stats-footer">
          <p><i class="fas fa-users"></i> Total de usuarios activos: {{ leaderboardData?.total_users || 0 }}</p>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import profileService from '../services/profileService'

const loading = ref(false)
const leaderboardData = ref(null)
const limit = ref(10)
const defaultAvatar = 'https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-entusiasta.png'

const topThree = computed(() => {
  if (!leaderboardData.value?.leaderboard) return []
  return leaderboardData.value.leaderboard.slice(0, 3)
})

const loadLeaderboard = async () => {
  loading.value = true
  try {
    leaderboardData.value = await profileService.getLeaderboard(limit.value)
  } catch (error) {
    console.error('Error loading leaderboard:', error)
    alert('Error al cargar la tabla de clasificación')
  } finally {
    loading.value = false
  }
}

const refreshLeaderboard = () => {
  loadLeaderboard()
}

const getRankClass = (position) => {
  if (position === 1) return 'gold'
  if (position === 2) return 'silver'
  if (position === 3) return 'bronze'
  return ''
}

onMounted(() => {
  loadLeaderboard()
})
</script>

<style scoped>
.leaderboard-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  padding: 2rem 1rem;
}

.leaderboard-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* Header */
.header {
  text-align: center;
  color: white;
  margin-bottom: 3rem;
  position: relative;
}

.header h1 {
  font-size: 3rem;
  margin: 0 0 0.5rem 0;
  text-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.header h1 i {
  color: #fbbf24;
}

.subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  margin-bottom: 1rem;
}

.btn-refresh {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.4);
  color: white;
  padding: 0.7rem 1.5rem;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
  font-weight: 600;
}

.btn-refresh:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading */
.loading-section {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
  font-size: 1.5rem;
}

.loading-section i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* Podium */
.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 2rem;
  margin-bottom: 3rem;
  padding: 2rem;
}

.podium-place {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.podium-place.first {
  order: 2;
}

.podium-place.second {
  order: 1;
}

.podium-place.third {
  order: 3;
}

.crown {
  font-size: 3rem;
  color: #fbbf24;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.rank-badge {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  position: relative;
}

.rank-badge i {
  position: absolute;
  font-size: 2.5rem;
  opacity: 0.3;
}

.rank-badge span {
  position: relative;
  z-index: 1;
}

.rank-badge.gold {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.rank-badge.silver {
  background: linear-gradient(135deg, #e5e7eb, #9ca3af);
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #cd7f32, #a0522d);
}

.user-card {
  background: white;
  border-radius: 20px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  min-width: 200px;
  transition: transform 0.3s;
}

.user-card:hover {
  transform: translateY(-5px);
}

.user-card.champion {
  padding: 2rem;
  min-width: 250px;
  border: 3px solid #fbbf24;
}

.user-card .avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #10b981;
  margin-bottom: 1rem;
}

.user-card.champion .avatar {
  width: 120px;
  height: 120px;
  border-color: #fbbf24;
}

.user-card h3 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.2rem;
}

.user-card .points {
  color: #10b981;
  font-weight: bold;
  font-size: 1.3rem;
  margin: 0.5rem 0;
}

.user-card .level {
  color: #718096;
  font-size: 0.9rem;
}

/* Ranking Table */
.ranking-table {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  margin-bottom: 2rem;
}

.ranking-table h2 {
  color: #2d3748;
  margin: 0 0 1.5rem 0;
  font-size: 1.8rem;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 1rem;
}

tbody tr {
  border-bottom: 1px solid #e2e8f0;
  transition: background 0.3s;
}

tbody tr:hover {
  background: #f7fafc;
}

tbody tr.current-user {
  background: #d1fae5;
  font-weight: 600;
}

tbody tr.current-user:hover {
  background: #a7f3d0;
}

tbody tr.top-three {
  background: #fef3c7;
}

td {
  padding: 1rem;
}

.position {
  width: 100px;
  text-align: center;
}

.rank-number {
  display: inline-block;
  width: 40px;
  height: 40px;
  line-height: 40px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #2d3748;
  font-weight: bold;
  text-align: center;
}

.rank-number.gold {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: white;
}

.rank-number.silver {
  background: linear-gradient(135deg, #e5e7eb, #9ca3af);
  color: white;
}

.rank-number.bronze {
  background: linear-gradient(135deg, #cd7f32, #a0522d);
  color: white;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #10b981;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.username {
  font-weight: 600;
  color: #2d3748;
}

.you-badge {
  display: inline-block;
  background: #10b981;
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  width: fit-content;
}

.points {
  color: #10b981;
  font-weight: 600;
}

.points i {
  color: #fbbf24;
}

.level i {
  color: #fbbf24;
}

.title {
  color: #718096;
  font-style: italic;
}

/* Current User Card */
.current-user-card {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  margin-bottom: 2rem;
}

.current-user-card h3 {
  color: #2d3748;
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
}

.user-position {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.position-badge {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 1.5rem;
  border-radius: 15px;
  text-align: center;
  min-width: 150px;
}

.position-badge .rank {
  display: block;
  font-size: 2.5rem;
  font-weight: bold;
}

.position-badge .total {
  display: block;
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 0.5rem;
}

.user-stats {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex: 1;
}

.user-stats .avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #10b981;
}

.user-stats .stats h4 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 1.3rem;
}

.user-stats .stats p {
  margin: 0.25rem 0;
  color: #718096;
}

.user-stats .stats i {
  color: #10b981;
  margin-right: 0.5rem;
}

/* Stats Footer */
.stats-footer {
  text-align: center;
  padding: 1.5rem;
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.stats-footer p {
  margin: 0;
  color: #718096;
  font-size: 1rem;
}

.stats-footer i {
  color: #10b981;
  margin-right: 0.5rem;
}

/* Responsive */
@media (max-width: 768px) {
  .header h1 {
    font-size: 2rem;
  }

  .podium {
    flex-direction: column;
    align-items: center;
  }

  .podium-place.first,
  .podium-place.second,
  .podium-place.third {
    order: initial;
  }

  .ranking-table {
    padding: 1rem;
  }

  .user-position {
    flex-direction: column;
  }

  th, td {
    padding: 0.5rem;
    font-size: 0.9rem;
  }

  .user-avatar {
    width: 40px;
    height: 40px;
  }
}
</style>
