import api from './api'

export const gameService = {
  async createSession(gameType) {
    try {
      const backendGameType = gameType === 'completion' ? 'complete_phrase' : 'context_match'
      const response = await api.post('/games/session', { game_type: backendGameType })
      return response.data
    } catch (error) {
      console.error('Error creating game session:', error)
      throw new Error('Failed to create game session')
    }
  },

  async getQuestion(gameType = 'completion', difficulty = 1) {
    try {
      const backendGameType = gameType === 'completion' ? 'complete_phrase' : 'context_match'
      const response = await api.get(`/games/question/${backendGameType}`, { params: { difficulty } })
      const question = response.data
      return {
        id: question.id,
        incomplete_sentence: question.bora_text,
        correct_answer: question.correct_answer,
        options: question.options,
        hint: question.hint || question.usage_context,
        category: question.category,
        correct_index: question.correct_index,
        translation: question.spanish_translation,
        pronunciation_guide: question.pronunciation_guide,
        motivational_phrase: this.getMotivationalPhrase(question.category)
      }
    } catch (error) {
      console.error('Error fetching question:', error)
      throw new Error('Failed to get game question')
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