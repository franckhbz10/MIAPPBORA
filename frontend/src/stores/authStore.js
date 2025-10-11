import { defineStore } from 'pinia'

// Importar gameStore para limpiar datos al logout
let useGameStore = null
try {
  const gameStoreModule = await import('./gameStore')
  useGameStore = gameStoreModule.useGameStore
} catch (e) {
  console.warn('gameStore not available')
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('access_token') || null,
    isAuthenticated: !!localStorage.getItem('access_token')
  }),

  getters: {
    getCurrentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,
    getUserId: (state) => state.user?.id || null,
    getUsername: (state) => state.user?.username || 'Usuario'
  },

  actions: {
    setUser(user, token) {
      this.user = user
      this.token = token
      this.isAuthenticated = true
      
      // Guardar en localStorage
      localStorage.setItem('access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },

    updateUser(updatedUser) {
      this.user = { ...this.user, ...updatedUser }
      localStorage.setItem('user', JSON.stringify(this.user))
    },

    logout() {
      // Limpiar datos del juego antes de hacer logout
      const gameStore = useGameStore()
      if (gameStore) {
        gameStore.clearUserData()
      }
      
      this.user = null
      this.token = null
      this.isAuthenticated = false
      
      // Limpiar localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    },

    async loadUserFromStorage() {
      const token = localStorage.getItem('access_token')
      const userData = localStorage.getItem('user')
      
      if (token && userData) {
        try {
          this.user = JSON.parse(userData)
          this.token = token
          this.isAuthenticated = true
        } catch (error) {
          console.error('Error loading user from storage:', error)
          this.logout()
        }
      }
    },

    async validateSession() {
      try {
        const response = await fetch('http://localhost:8000/auth/me', {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        })
        
        if (response.ok) {
          const userData = await response.json()
          this.updateUser(userData)
        } else {
          this.logout()
        }
      } catch (error) {
        console.error('Session validation failed:', error)
        this.logout()
      }
    },

    async initialize() {
      const token = localStorage.getItem('access_token')
      const userData = localStorage.getItem('user')
      
      console.log('🔑 Initializing auth...')
      console.log('Token exists:', !!token)
      console.log('User data exists:', !!userData)
      
      if (token && userData) {
        try {
          this.user = JSON.parse(userData)
          this.token = token
          this.isAuthenticated = true
          
          console.log('✅ User loaded from localStorage:', this.user?.username)
          
          // Validar que el token aún sea válido
          await this.validateSession()
        } catch (error) {
          console.error('❌ Error initializing auth:', error)
          this.logout()
        }
      } else {
        console.log('⚠️ No token or user data found in localStorage')
      }
    }
  }
})
