import { defineStore } from 'pinia'
import { gameService } from '../services/gameService'

export const useGameStore = defineStore('game', {
  state: () => ({
    // Estadísticas de la sesión actual (se reinician cada juego)
    sessionScore: 0,
    sessionTotalQuestions: 0,
    sessionCorrectAnswers: 0,
    
    // Estadísticas globales del usuario (acumuladas)
    score: 0,
    totalQuestions: 0,
    correctAnswers: 0,
    
    streak: 0,
    currentQuestion: null,
    isLoading: false,
    // Estadísticas del nivel actual
    currentLevelQuestions: 0,
    currentLevelCorrect: 0,
    currentGameType: null,
    maxQuestionsPerLevel: {
      completion: 5,
      translation: 5
    },
    // Datos de sesión del backend
    currentSessionId: null,
    sessionStartTime: null
  }),

  getters: {
    accuracy: (state) => {
      if (state.sessionTotalQuestions === 0) return 0
      return Math.round((state.sessionCorrectAnswers / state.sessionTotalQuestions) * 100)
    },
    
    level: (state) => {
      return Math.floor(state.score / 100) + 1
    },
    
    isLevelComplete: (state) => {
      if (!state.currentGameType) return false
      const maxQuestions = state.maxQuestionsPerLevel[state.currentGameType] || 10
      return state.currentLevelQuestions >= maxQuestions
    },
    
    currentLevelIncorrect: (state) => {
      return state.currentLevelQuestions - state.currentLevelCorrect
    },
    
    currentLevelScore: (state) => {
      return state.currentLevelCorrect * 10
    }
  },

  actions: {
    // Iniciar nuevo juego (crear sesión en backend)
    async startNewGame(gameType = 'completion') {
      try {
        this.isLoading = true
        
        // Crear sesión en el backend
        const session = await gameService.createSession(gameType)
        this.currentSessionId = session.id
        this.sessionStartTime = Date.now()
        
        // ✅ Resetear estadísticas de la sesión actual
        this.sessionScore = 0
        this.sessionTotalQuestions = 0
        this.sessionCorrectAnswers = 0
        
        // Resetear nivel actual
        this.resetLevel()
        this.currentGameType = gameType
        
        // Cargar stats globales del usuario desde backend (solo para referencia)
        await this.loadStats()
        
        this.isLoading = false
      } catch (error) {
        console.error('Error starting new game:', error)
        this.isLoading = false
        throw error
      }
    },

    // Cargar estadísticas desde el backend
    async loadStats() {
      try {
        const stats = await gameService.getStats()
        this.score = stats.score
        this.totalQuestions = stats.totalQuestions
        this.correctAnswers = stats.correctAnswers
      } catch (error) {
        console.error('Error loading stats:', error)
      }
    },

    async fetchQuestion(gameType = 'completion') {
      this.isLoading = true
      
      // Verificar si se alcanzó el límite de preguntas
      const maxQuestions = this.maxQuestionsPerLevel[gameType] || 10
      if (this.currentLevelQuestions >= maxQuestions) {
        this.isLoading = false
        return
      }
      
      try {
        this.currentQuestion = await gameService.getQuestion(gameType)
      } catch (error) {
        console.error('Error fetching question:', error)
      } finally {
        this.isLoading = false
      }
    },

    async submitAnswer(questionData, selectedOption) {
      if (!this.currentQuestion || !this.currentSessionId) return null
      
      try {
        // Enviar respuesta al backend
        const result = await gameService.submitAnswer(
          this.currentSessionId,
          questionData,
          selectedOption
        )
        
        // ✅ Actualizar estadísticas de la SESIÓN ACTUAL (para UI)
        this.currentLevelQuestions++
        this.sessionTotalQuestions++
        
        if (result.correct) {
          this.currentLevelCorrect++
          this.sessionCorrectAnswers++
          this.sessionScore += (result.points || 10)
          this.streak++
        } else {
          this.streak = 0
        }
        
        return result
      } catch (error) {
        console.error('Error submitting answer:', error)
        return null
      }
    },

    // Finalizar juego (completar sesión en backend)
    async finishGame() {
      if (!this.currentSessionId) {
        console.warn('No session to finish')
        return
      }
      
      try {
        const timeSpent = this.sessionStartTime 
          ? Math.floor((Date.now() - this.sessionStartTime) / 1000)
          : 0
        
        const stats = {
          totalQuestions: this.currentLevelQuestions,
          correctAnswers: this.currentLevelCorrect,
          incorrectAnswers: this.currentLevelIncorrect,
          totalScore: this.currentLevelScore,
          isPerfect: this.currentLevelIncorrect === 0 && this.currentLevelQuestions > 0,
          timeSpent: timeSpent
        }
        
        // Enviar resultados al backend
        await gameService.completeSession(this.currentSessionId, stats)
        
        // Recargar estadísticas actualizadas
        await this.loadStats()
        
        // Limpiar sesión actual
        this.currentSessionId = null
        this.sessionStartTime = null
        
      } catch (error) {
        console.error('Error finishing game:', error)
      }
    },

    // Ya no necesitamos guardar en localStorage (datos en backend)
    saveToLocalStorage() {
      // Método legacy - ahora los datos están en el backend
      // Mantener por compatibilidad pero no hace nada
    },

    resetStats() {
      // Ya no resetea datos porque están en el backend
      // Solo resetea UI local
      this.streak = 0
    },
    
    resetLevel() {
      this.currentLevelQuestions = 0
      this.currentLevelCorrect = 0
      this.currentGameType = null
      this.currentQuestion = null
    },

    // Limpiar datos al cerrar sesión
    clearUserData() {
      this.score = 0
      this.totalQuestions = 0
      this.correctAnswers = 0
      this.sessionScore = 0
      this.sessionTotalQuestions = 0
      this.sessionCorrectAnswers = 0
      this.streak = 0
      this.currentSessionId = null
      this.sessionStartTime = null
      this.resetLevel()
    }
  }
})

