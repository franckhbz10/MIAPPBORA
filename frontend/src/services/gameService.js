import api from './api'

export const gameService = {
  async createSession(gameType) {
    try {
      // Verificar que el usuario esté autenticado
      const token = localStorage.getItem('access_token')
      if (!token) {
        console.error('No authentication token found')
        throw new Error('Usuario no autenticado. Por favor, inicia sesión.')
      }

      // Validar y normalizar el tipo de juego
      let backendGameType = gameType
      if (gameType === 'completion') {
        backendGameType = 'complete_phrase'
      } else if (gameType !== 'complete_phrase' && gameType !== 'context_match') {
        console.warn(`Tipo de juego inválido: ${gameType}, usando 'complete_phrase'`)
        backendGameType = 'complete_phrase'
      }

      console.log('Creating session with game type:', backendGameType)
      const response = await api.post('/games/session', { game_type: backendGameType })
      console.log('Session created:', response.data)
      return response.data
    } catch (error) {
      console.error('Error creating game session:', error)
      if (error.response?.status === 401) {
        throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.')
      }
      throw new Error(error.response?.data?.detail || 'Error al crear la sesión de juego')
    }
  },

  async getQuestion(gameType = 'complete_phrase', difficulty = 1) {
    try {
      // Validar y normalizar el tipo de juego
      let backendGameType = gameType
      if (gameType === 'completion') {
        backendGameType = 'complete_phrase'
      } else if (gameType !== 'complete_phrase' && gameType !== 'context_match') {
        console.warn(`Tipo de juego inválido: ${gameType}, usando 'complete_phrase'`)
        backendGameType = 'complete_phrase'
      }

      console.log('Fetching question for game type:', backendGameType)
      const response = await api.get(`/games/question/${backendGameType}`, { params: { difficulty } })
      const question = response.data
      
      // Construir objeto de pregunta según el tipo de juego
      const questionData = {
        id: question.id,
        bora_text: question.bora_text,
        spanish_translation: question.spanish_translation,
        correct_answer: question.correct_answer,
        options: question.options,
        hint: question.hint || question.usage_context,
        category: question.category,
        correct_index: question.correct_index,
        pronunciation_guide: question.pronunciation_guide,
        usage_context: question.usage_context,
        motivational_phrase: this.getMotivationalPhrase(question.category)
      }

      // Para minijuego 2 (context_match), agregar el contexto completo
      if (backendGameType === 'context_match') {
        questionData.context = question.context || question.usage_context
      } else {
        // Para minijuego 1 (complete_phrase), usar bora_text como incomplete_sentence
        questionData.incomplete_sentence = question.spanish_translation
      }

      console.log('Question fetched:', questionData)
      return questionData
    } catch (error) {
      console.error('Error fetching question:', error)
      throw new Error(error.response?.data?.detail || 'Error al obtener la pregunta')
    }
  },

  async submitAnswer(sessionId, questionData, selectedOption) {
    try {
      const response = await api.post('/games/answer', {
        session_id: sessionId,
        phrase_id: questionData.id,
        selected_option: selectedOption
      })
      const result = response.data
      return {
        correct: result.correct,
        points: result.points,
        correct_answer: result.correct_answer,
        explanation: result.explanation,
        motivational_phrase: result.correct ? this.getMotivationalPhrase(questionData.category) : undefined
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
      throw new Error('Failed to submit answer')
    }
  },

  async completeSession(sessionId, stats) {
    try {
      console.log('Completing session with stats:', stats)
      const response = await api.put(`/games/session/${sessionId}`, {
        total_questions: stats.totalQuestions,
        correct_answers: stats.correctAnswers,
        incorrect_answers: stats.incorrectAnswers,
        total_score: stats.totalScore,
        is_perfect: stats.isPerfect,
        time_spent_seconds: stats.timeSpent || 0
      })
      return response.data
    } catch (error) {
      console.error('Error completing session:', error)
      console.error('Error details:', error.response?.data)
      throw new Error(`Failed to complete session: ${error.response?.data?.detail || error.message}`)
    }
  },

  async getStats() {
    try {
      const response = await api.get('/games/stats')
      return {
        score: response.data.total_score || 0,
        totalQuestions: response.data.total_questions || 0,
        correctAnswers: response.data.correct_answers || 0,
        accuracy: response.data.accuracy || 0,
        perfectGames: response.data.perfect_games || 0,
        totalSessions: response.data.total_sessions || 0,
        gamesByType: response.data.games_by_type || {},
        recentSessions: response.data.recent_sessions || []
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
      return {
        score: 0,
        totalQuestions: 0,
        correctAnswers: 0,
        accuracy: 0,
        perfectGames: 0,
        totalSessions: 0,
        gamesByType: {},
        recentSessions: []
      }
    }
  },

  getMotivationalPhrase(category) {
    const phrases = {
      'Saludos y Presentaciones': ['¡Excelente! Dominas los saludos en Bora ', '¡Fantástico! Sigues aprendiendo muy bien '],
      'Conversación General': ['¡Increíble! Ya puedes conversar en Bora ', '¡Muy bien! La cortesía es fundamental '],
      'Ubicación': ['¡Excelente! Dominas las ubicaciones '],
      'Emergencias': ['¡Muy bien! Las expresiones de emergencia son cruciales '],
      'Relaciones Cotidianas': ['¡Increíble! Ya puedes expresar sentimientos en Bora ']
    }
    const categoryPhrases = phrases[category] || ['¡Excelente! Sigue así ']
    return categoryPhrases[Math.floor(Math.random() * categoryPhrases.length)]
  }
}