import { defineStore } from 'pinia'
import { profileService } from '../services/profileService'

export const useProfileStore = defineStore('profile', {
  state: () => ({
    user: null,
    levelProgress: null,
    dailyMissions: [],
    availableRewards: [],
    claimedRewards: [],
    dashboardStats: null,
    isLoading: false,
    lastUpdated: null
  }),

  getters: {
    // Progreso de nivel como porcentaje
    levelProgressPercentage: (state) => {
      if (!state.levelProgress) return 0
      const total = state.levelProgress.current_points + state.levelProgress.points_to_next_level
      if (total === 0) return 100 // Nivel máximo
      return Math.round((state.levelProgress.current_points / total) * 100)
    },

    // Misiones completadas
    completedMissions: (state) => {
      return state.dailyMissions.filter(m => m.is_completed)
    },

    // Misiones pendientes
    pendingMissions: (state) => {
      return state.dailyMissions.filter(m => !m.is_completed)
    },

    // Total de puntos de misiones completadas
    missionPointsEarned: (state) => {
      return state.dailyMissions
        .filter(m => m.is_completed)
        .reduce((sum, m) => sum + m.points_reward, 0)
    },

    // Recompensas por tipo
    rewardsByType: (state) => {
      const grouped = {}
      state.availableRewards.forEach(reward => {
        if (!grouped[reward.reward_type]) {
          grouped[reward.reward_type] = []
        }
        grouped[reward.reward_type].push(reward)
      })
      return grouped
    }
  },

  actions: {
    /**
     * Cargar perfil completo
     */
    async loadCompleteProfile() {
      this.isLoading = true
      try {
        const data = await profileService.getCompleteProfile()
        
        this.user = data.user
        this.levelProgress = data.level_progress
        this.dailyMissions = data.daily_missions
        this.availableRewards = data.available_rewards
        this.claimedRewards = data.claimed_rewards
        this.lastUpdated = new Date()
        
      } catch (error) {
        console.error('Error loading profile:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Actualizar información del perfil
     */
    async updateProfile(profileData) {
      this.isLoading = true
      try {
        const response = await profileService.updateProfile(profileData)
        this.user = response.user
        return response
      } catch (error) {
        console.error('Error updating profile:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Recargar solo el progreso de nivel
     */
    async refreshLevelProgress() {
      try {
        this.levelProgress = await profileService.getLevelProgress()
      } catch (error) {
        console.error('Error refreshing level progress:', error)
      }
    },

    /**
     * Recargar solo las misiones
     */
    async refreshMissions() {
      try {
        this.dailyMissions = await profileService.getDailyMissions()
      } catch (error) {
        console.error('Error refreshing missions:', error)
      }
    },

    /**
     * Recargar solo las recompensas
     */
    async refreshRewards() {
      try {
        this.availableRewards = await profileService.getAvailableRewards()
      } catch (error) {
        console.error('Error refreshing rewards:', error)
      }
    },

    /**
     * Reclamar una recompensa
     */
    async claimReward(rewardId) {
      this.isLoading = true
      try {
        const response = await profileService.claimReward(rewardId)
        
        // Actualizar estado
        await this.loadCompleteProfile()
        
        return response
      } catch (error) {
        console.error('Error claiming reward:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Cargar estadísticas del dashboard
     */
    async loadDashboardStats() {
      try {
        this.dashboardStats = await profileService.getDashboardStats()
      } catch (error) {
        console.error('Error loading dashboard stats:', error)
      }
    },

    /**
     * Limpiar datos del perfil (al cerrar sesión)
     */
    clearProfile() {
      this.user = null
      this.levelProgress = null
      this.dailyMissions = []
      this.availableRewards = []
      this.claimedRewards = []
      this.dashboardStats = null
      this.lastUpdated = null
    }
  }
})
