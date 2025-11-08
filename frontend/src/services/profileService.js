import api from './api'

export const profileService = {
  /**
   * Obtener perfil básico del usuario actual
   */
  async getMyProfile() {
    try {
      const response = await api.get('/profile/me')
      return response.data
    } catch (error) {
      console.error('Error fetching profile:', error)
      throw new Error('Failed to get profile')
    }
  },

  /**
   * Actualizar perfil del usuario
   */
  async updateProfile(profileData) {
    try {
      const response = await api.put('/profile/me', profileData)
      return response.data
    } catch (error) {
      console.error('Error updating profile:', error)
      throw new Error('Failed to update profile')
    }
  },

  /**
   * Obtener perfil completo con gamificación
   */
  async getCompleteProfile() {
    try {
      const response = await api.get('/profile/complete')
      return response.data
    } catch (error) {
      console.error('Error fetching complete profile:', error)
      console.error('Status:', error.response?.status)
      console.error('Data:', error.response?.data)
      console.error('Headers:', error.config?.headers)
      throw new Error(`Failed to get complete profile: ${error.response?.status || error.message}`)
    }
  },

  /**
   * Obtener progreso de nivel
   */
  async getLevelProgress() {
    try {
      const response = await api.get('/profile/progress')
      return response.data
    } catch (error) {
      console.error('Error fetching level progress:', error)
      throw new Error('Failed to get level progress')
    }
  },

  /**
   * Obtener misiones diarias
   */
  async getDailyMissions() {
    try {
      const response = await api.get('/profile/missions')
      return response.data
    } catch (error) {
      console.error('Error fetching missions:', error)
      throw new Error('Failed to get missions')
    }
  },

  /**
   * Obtener recompensas disponibles
   */
  async getAvailableRewards() {
    try {
      const response = await api.get('/profile/rewards/available')
      // El backend ahora retorna { success, user_points, rewards }
      return response.data.rewards || []
    } catch (error) {
      console.error('Error fetching rewards:', error)
      throw new Error('Failed to get rewards')
    }
  },

  /**
   * Reclamar una recompensa
   */
  async claimReward(rewardId) {
    try {
      const response = await api.post('/profile/rewards/claim', { reward_id: rewardId })
      return response.data
    } catch (error) {
      console.error('Error claiming reward:', error)
      throw new Error(error.response?.data?.detail || 'Failed to claim reward')
    }
  },

  /**
   * Obtener estadísticas del dashboard
   */
  async getDashboardStats() {
    try {
      const response = await api.get('/profile/stats/dashboard')
      return response.data
    } catch (error) {
      console.error('Error fetching dashboard stats:', error)
      return {
        total_visits: 0,
        home_visits: 0,
        phrases_visits: 0,
        games_visits: 0,
        chat_queries: 0,
        games_played: 0,
        perfect_games: 0
      }
    }
  }
}
