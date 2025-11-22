import { defineStore } from 'pinia'
import { gameService } from '../services/gameService'
import { useProfileStore } from './profileStore'

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
      complete_phrase: 5,  // Minijuego 1: Completar frases
      context_match: 5     // Minijuego 2: Contexto y selección
    },
    // Datos de sesión del backend
    currentSessionId: null,
    sessionStartTime: null,
    // Control de juego activo para evitar reinicio al cambiar de pestaña
    isGameActive: false,
    answeredPhraseIds: []  // IDs de frases ya respondidas en esta sesión
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
    async startNewGame(gameType = 'complete_phrase') {
      try {
        this.isLoading = true
        
        // Validar tipo de juego
        const validTypes = ['complete_phrase', 'context_match']
        if (!validTypes.includes(gameType)) {
          console.warn(`Tipo de juego inválido: ${gameType}, usando 'complete_phrase'`)
          gameType = 'complete_phrase'
        }
        
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
        
        // Marcar juego como activo
        this.isGameActive = true
        this.answeredPhraseIds = []
        
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

    async fetchQuestion(gameType = 'complete_phrase') {
      this.isLoading = true
      
      // Usar el tipo de juego actual si no se especifica
      const actualGameType = gameType || this.currentGameType || 'complete_phrase'
      
      // Verificar si se alcanzó el límite de preguntas
      const maxQuestions = this.maxQuestionsPerLevel[actualGameType] || 5
      if (this.currentLevelQuestions >= maxQuestions) {
        this.isLoading = false
        return
      }
      
      try {
        this.currentQuestion = await gameService.getQuestion(actualGameType)
      } catch (error) {
        console.error('Error fetching question:', error)
      } finally {
        this.isLoading = false
      }
    },

    async submitAnswer(questionData, selectedOption) {
      if (!this.currentQuestion || !this.currentSessionId) return null
      
      // Verificar si esta pregunta ya fue respondida
      if (this.answeredPhraseIds.includes(questionData.id)) {
        console.warn('Esta pregunta ya fue respondida en esta sesión')
        return { error: 'Pregunta ya respondida', alreadyAnswered: true }
      }
      
      try {
        // Enviar respuesta al backend
        const result = await gameService.submitAnswer(
          this.currentSessionId,
          questionData,
          selectedOption
        )
        
        // Marcar pregunta como respondida
        this.answeredPhraseIds.push(questionData.id)
        
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
        
        const maxQuestions = this.maxQuestionsPerLevel[this.currentGameType] || 5
        let sessionFinished = false
        if (this.currentLevelQuestions >= maxQuestions) {
          await this.finishGame()
          sessionFinished = true
        }
        
        return { ...result, sessionFinished }
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
        const completion = await gameService.completeSession(this.currentSessionId, stats)
        
        // Recargar estadísticas actualizadas
        await this.loadStats()
        
        // Refrescar perfil para mostrar puntos actuales
        try {
          const profileStore = useProfileStore()
          await profileStore.loadCompleteProfile()
        } catch (profileError) {
          console.error('Error refreshing profile after finishing game:', profileError)
        }
        
        // Limpiar sesión actual y marcar juego como inactivo
        this.currentSessionId = null
        this.sessionStartTime = null
        this.isGameActive = false
        this.answeredPhraseIds = []
        
        return completion
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
      this.isGameActive = false
      this.answeredPhraseIds = []
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
      this.isGameActive = false
      this.answeredPhraseIds = []
      this.resetLevel()
    }
  }
})

