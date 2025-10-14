<template>
  <div class="game-view">
    <div class="game-container">
      <div class="game-header">
        <h1 class="game-title">
          <i class="fas fa-puzzle-piece"></i>
          Minijuego Bora
        </h1>
        <p class="game-subtitle">
          Aprende el idioma Bora jugando y divirtiéndote
        </p>
      </div>
      
      <div v-if="!gameStore.currentQuestion && !gameStore.isLoading" class="start-section">
        <div class="game-selector">
          <h2 class="selector-title">Elige tu Minijuego</h2>
          <p class="selector-subtitle">Selecciona el tipo de práctica que deseas realizar</p>
          
          <div class="game-cards">
            <!-- Minijuego 1: Completar frases -->
            <div class="game-card" @click="selectGame('complete_phrase')">
              <div class="game-card-icon">
                <i class="fas fa-puzzle-piece"></i>
              </div>
              <h3 class="game-card-title">Minijuego 1</h3>
              <h4 class="game-card-subtitle">Completar Frases</h4>
              <p class="game-card-description">
                Completa frases en Bora seleccionando la traducción correcta entre 4 opciones
              </p>
              <div class="game-card-features">
                <div class="feature">
                  <i class="fas fa-list-ol"></i>
                  <span>5 preguntas</span>
                </div>
                <div class="feature">
                  <i class="fas fa-star"></i>
                  <span>10 puntos/respuesta</span>
                </div>
              </div>
              <button class="btn btn-card">
                <i class="fas fa-play"></i>
                Jugar
              </button>
            </div>
            
            <!-- Minijuego 2: Contexto y selección -->
            <div class="game-card" @click="selectGame('context_match')">
              <div class="game-card-icon context">
                <i class="fas fa-comments"></i>
              </div>
              <h3 class="game-card-title">Minijuego 2</h3>
              <h4 class="game-card-subtitle">Contexto y Selección</h4>
              <p class="game-card-description">
                Lee una situación cotidiana y elige la frase en Bora que mejor se adapte al contexto
              </p>
              <div class="game-card-features">
                <div class="feature">
                  <i class="fas fa-list-ol"></i>
                  <span>5 preguntas</span>
                </div>
                <div class="feature">
                  <i class="fas fa-star"></i>
                  <span>10 puntos/respuesta</span>
                </div>
              </div>
              <button class="btn btn-card">
                <i class="fas fa-play"></i>
                Jugar
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else-if="gameStore.isLoading" class="loading-section">
        <div class="loading-spinner">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
        <p>Cargando pregunta...</p>
      </div>
      
      <!-- Pantalla de resumen final -->
      <div v-else-if="gameStore.isLevelComplete" class="summary-section">
        <div class="summary-card">
          <div class="summary-header">
            <div class="summary-icon">
              <i class="fas fa-trophy"></i>
            </div>
            <h2>¡Juego Completado!</h2>
            <p class="summary-subtitle">Has terminado esta partida de Bora</p>
          </div>

          <div class="summary-stats">
            <div class="stat-card stat-correct">
              <div class="stat-icon">
                <i class="fas fa-check-circle"></i>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ gameStore.currentLevelCorrect }}</span>
                <span class="stat-label">Correctas</span>
              </div>
            </div>

            <div class="stat-card stat-incorrect">
              <div class="stat-icon">
                <i class="fas fa-times-circle"></i>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ gameStore.currentLevelIncorrect }}</span>
                <span class="stat-label">Incorrectas</span>
              </div>
            </div>

            <div class="stat-card stat-accuracy">
              <div class="stat-icon">
                <i class="fas fa-bullseye"></i>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ Math.round((gameStore.currentLevelCorrect / gameStore.currentLevelQuestions) * 100) }}%</span>
                <span class="stat-label">Precisión</span>
              </div>
            </div>

            <div class="stat-card stat-points">
              <div class="stat-icon">
                <i class="fas fa-star"></i>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ gameStore.currentLevelScore }}</span>
                <span class="stat-label">Puntos Totales</span>
              </div>
            </div>
          </div>

          <div class="summary-message">
            <div v-if="gameStore.currentLevelIncorrect === 0" class="perfect-game">
              <i class="fas fa-gem"></i>
              <h3>¡Juego Perfecto!</h3>
              <p>No tuviste ningún error. ¡Increíble!</p>
            </div>
            <div v-else-if="gameStore.currentLevelCorrect >= gameStore.currentLevelQuestions * 0.8" class="great-game">
              <i class="fas fa-smile-beam"></i>
              <h3>¡Excelente Trabajo!</h3>
              <p>Tienes un gran dominio del Bora</p>
            </div>
            <div v-else-if="gameStore.currentLevelCorrect >= gameStore.currentLevelQuestions * 0.5" class="good-game">
              <i class="fas fa-thumbs-up"></i>
              <h3>¡Buen Trabajo!</h3>
              <p>Sigue practicando para mejorar</p>
            </div>
            <div v-else class="keep-learning">
              <i class="fas fa-book-reader"></i>
              <h3>¡Sigue Aprendiendo!</h3>
              <p>La práctica hace al maestro</p>
            </div>
          </div>

          <div class="summary-actions">
            <button @click="startGame(gameStore.currentGameType)" class="btn btn-primary btn-lg">
              <i class="fas fa-redo"></i>
              Jugar de Nuevo
            </button>
            <button @click="selectedGameType = null; gameStore.resetLevel()" class="btn btn-secondary btn-lg">
              <i class="fas fa-th-large"></i>
              Cambiar Minijuego
            </button>
            <button @click="$router.push('/home')" class="btn btn-secondary btn-lg">
              <i class="fas fa-home"></i>
              Volver al Inicio
            </button>
          </div>
        </div>
      </div>

      <div v-else-if="gameStore.currentQuestion" class="question-section">
        <!-- Progress Section Arriba -->
        <div class="progress-section-top">
          <div class="progress-stats-simple">
            <div class="stat-simple">
              <i class="fas fa-check-circle"></i>
              <span><strong>{{ gameStore.sessionCorrectAnswers }}</strong> Correctos</span>
            </div>
            <div class="stat-simple">
              <i class="fas fa-times-circle"></i>
              <span><strong>{{ gameStore.sessionTotalQuestions - gameStore.sessionCorrectAnswers }}</strong> Incorrectos</span>
            </div>
            <div class="stat-simple stat-score">
              <i class="fas fa-star"></i>
              <span><strong>{{ gameStore.sessionScore }}</strong> Puntos</span>
            </div>
          </div>
        </div>
        
        <div class="question-card">
          <div class="question-header">
            <span class="question-number">
              <i class="fas fa-list-ol"></i>
              Pregunta {{ gameStore.currentLevelQuestions + 1 }}/{{ gameStore.maxQuestionsPerLevel[gameStore.currentGameType] || 5 }}
            </span>
            <span class="question-category">
              <i class="fas fa-tag"></i>
              {{ gameStore.currentQuestion.category }}
            </span>
          </div>
          
          <!-- MINIJUEGO 1: Completar frases -->
          <div v-if="gameStore.currentGameType === 'complete_phrase'" class="question-content">
            <h2 class="question-text">
              {{ gameStore.currentQuestion.spanish_translation }}
            </h2>
            <p class="question-hint" v-if="gameStore.currentQuestion.hint">
              <i class="fas fa-lightbulb"></i>
              {{ gameStore.currentQuestion.hint }}
            </p>
            <p class="question-instruction">Selecciona la traducción correcta en Bora:</p>
          </div>
          
          <!-- MINIJUEGO 2: Contexto y selección -->
          <div v-else-if="gameStore.currentGameType === 'context_match'" class="question-content">
            <div class="context-box">
              <i class="fas fa-book-open"></i>
              <h3 class="context-title">Situación:</h3>
              <p class="context-description">{{ gameStore.currentQuestion.context }}</p>
            </div>
            <h3 class="context-question">¿Qué frase en Bora usarías en esta situación?</h3>
          </div>
          
          <div class="options-container">
            <button
              v-for="(option, index) in gameStore.currentQuestion.options"
              :key="index"
              @click="selectOption(index)"
              :class="['option-btn', {
                'selected': selectedOption === index,
                'disabled': isAnswering
              }]"
              :disabled="isAnswering"
            >
              <span class="option-letter">{{ String.fromCharCode(65 + index) }}</span>
              <span class="option-text">{{ option }}</span>
              <!-- Agregar guía de pronunciación solo para minijuego 2 -->
              <span v-if="gameStore.currentGameType === 'context_match' && gameStore.currentQuestion.pronunciation_guide && index === 0" class="option-pronunciation">
                {{ gameStore.currentQuestion.pronunciation_guide }}
              </span>
            </button>
          </div>
          
          <div class="action-buttons">
            <button
              v-if="selectedOption !== null && !isAnswering"
              @click="submitAnswer"
              class="btn btn-primary btn-lg"
            >
              <i class="fas fa-check"></i>
              Confirmar Respuesta
            </button>
          </div>
        </div>
        
        <div v-if="lastResult" class="result-section fade-in">
          <div :class="['result-card', lastResult.correct ? 'correct' : 'incorrect']">
            <div class="result-icon">
              <i :class="lastResult.correct ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
            </div>
            
            <h3>{{ lastResult.correct ? '¡Correcto!' : 'Incorrecto' }}</h3>
            
            <div v-if="lastResult.correct" class="success-content">
              <p class="points-earned">+{{ lastResult.points }} puntos</p>
              <p class="encouragement">{{ lastResult.motivational_phrase || lastResult.explanation }}</p>
            </div>
            
            <div v-else class="error-content">
              <p>La respuesta correcta era:</p>
              <p class="correct-answer">{{ lastResult.correct_answer }}</p>
              <p class="explanation" v-if="lastResult.explanation">
                {{ lastResult.explanation }}
              </p>
            </div>
            
            <button @click="nextQuestion" class="btn btn-primary">
              <i class="fas fa-arrow-right"></i>
              Siguiente Pregunta
            </button>
          </div>
        </div>
      </div>
      

    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useGameStore } from '../stores/gameStore'

export default {
  name: 'Game',
  setup() {
    const gameStore = useGameStore()
    const selectedOption = ref(null)
    const isAnswering = ref(false)
    const lastResult = ref(null)
    const selectedGameType = ref(null) // null hasta que el usuario seleccione
    
    const encouragements = [
      '¡Excelente trabajo!',
      '¡Sigue así!',
      '¡Fantástico!',
      '¡Muy bien!',
      '¡Increíble!',
      '¡Perfecto!',
      '¡Genial!',
      '¡Magnífico!',
      '¡Eres un maestro del Bora!',
      '¡Sigue aprendiendo!'
    ]
    
    const selectGame = async (gameType) => {
      selectedGameType.value = gameType
      await startGame(gameType)
    }
    
    const startGame = async (gameType = null) => {
      lastResult.value = null
      selectedOption.value = null
      
      // Usar el tipo seleccionado o el del store
      const typeToUse = gameType || selectedGameType.value || 'complete_phrase'
      
      try {
        // Crear nueva sesión en el backend
        await gameStore.startNewGame(typeToUse)
        // Obtener primera pregunta
        await gameStore.fetchQuestion(typeToUse)
      } catch (error) {
        console.error('Error starting game:', error)
        alert('Error al iniciar el juego. Por favor, inicia sesión nuevamente.')
      }
    }
    
    const selectOption = (index) => {
      if (!isAnswering.value) {
        selectedOption.value = index
      }
    }
    
    const submitAnswer = async () => {
      if (selectedOption.value === null || isAnswering.value) return
      
      isAnswering.value = true
      
      try {
        // Convertir índice a texto de la opción
        const selectedText = gameStore.currentQuestion.options[selectedOption.value]
        
        const result = await gameStore.submitAnswer(
          gameStore.currentQuestion, 
          selectedText  // Enviar texto en lugar de índice
        )
        lastResult.value = result
      } catch (error) {
        console.error('Error submitting answer:', error)
      } finally {
        isAnswering.value = false
      }
    }
    
    const nextQuestion = async () => {
      lastResult.value = null
      selectedOption.value = null
      
      // Verificar si el nivel se completó
      if (gameStore.isLevelComplete) {
        // Finalizar sesión en el backend
        await gameStore.finishGame()
        // El juego mostrará las estadísticas finales
        return
      }
      
      await gameStore.fetchQuestion(gameStore.currentGameType)
    }
    
    const getRandomEncouragement = () => {
      return encouragements[Math.floor(Math.random() * encouragements.length)]
    }
    
    return {
      gameStore,
      selectedOption,
      isAnswering,
      lastResult,
      selectedGameType,
      selectGame,
      startGame,
      selectOption,
      submitAnswer,
      nextQuestion,
      getRandomEncouragement
    }
  }
}
</script>

<style scoped>
.game-view {
  min-height: calc(100vh - 80px);
  background: #c1ff72;
  padding: 2rem 1rem;
}

.game-container {
  max-width: 900px;
  margin: 0 auto;
}

.game-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 2.5rem 2rem;
  border-radius: 20px;
  text-align: center;
  margin-bottom: 2rem;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
}

.game-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.game-title i {
  color: #ffd700;
  margin-right: 0.75rem;
}

.game-subtitle {
  font-size: 1.1rem;
  opacity: 0.95;
  margin-bottom: 0;
  line-height: 1.5;
}

.start-section, .loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

/* Game Selector Styles */
.game-selector {
  width: 100%;
  max-width: 1100px;
  text-align: center;
}

.selector-title {
  font-size: 2.5rem;
  color: #1f2937;
  margin-bottom: 0.75rem;
  font-weight: 700;
}

.selector-subtitle {
  color: #6b7280;
  font-size: 1.2rem;
  margin-bottom: 3rem;
}

.game-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.game-card {
  background: white;
  border-radius: 20px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 3px solid transparent;
}

.game-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  border-color: #10b981;
}

.game-card-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  color: white;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}

.game-card-icon.context {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

.game-card-title {
  font-size: 1.1rem;
  color: #10b981;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.game-card:nth-child(2) .game-card-title {
  color: #3b82f6;
}

.game-card-subtitle {
  font-size: 1.5rem;
  color: #1f2937;
  font-weight: 700;
  margin-bottom: 1rem;
}

.game-card-description {
  color: #6b7280;
  font-size: 1rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  min-height: 60px;
}

.game-card-features {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 10px;
}

.feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #374151;
  font-size: 0.95rem;
  font-weight: 600;
}

.feature i {
  color: #10b981;
  font-size: 1.2rem;
}

.btn-card {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 0.875rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1.05rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.game-card:nth-child(2) .btn-card {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.btn-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.game-card:nth-child(2) .btn-card:hover {
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.loading-section {
  color: #10b981;
  text-align: center;
}

.loading-spinner {
  font-size: 3.5rem;
  margin-bottom: 1rem;
}

.question-section {
  margin-bottom: 2rem;
}

.progress-section-top {
  background: white;
  border-radius: 15px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.progress-stats-simple {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.stat-simple {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #374151;
  font-size: 1rem;
}

.stat-simple i {
  font-size: 1.5rem;
}

.stat-simple:nth-child(1) i {
  color: #10b981;
}

.stat-simple:nth-child(2) i {
  color: #ef4444;
}

.stat-simple.stat-score i {
  color: #f59e0b;
}

.stat-simple strong {
  font-size: 1.25rem;
  margin-right: 0.25rem;
}

.question-card {
  background: white;
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
  margin-bottom: 2rem;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
  gap: 1rem;
}

.question-number {
  padding: 0.6rem 1.25rem;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: 600;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.question-number i {
  font-size: 0.9rem;
}

.question-category {
  padding: 0.6rem 1.25rem;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: 600;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.question-content {
  margin-bottom: 2rem;
}

.question-text {
  font-size: 1.75rem;
  color: #1f2937;
  margin-bottom: 1.25rem;
  line-height: 1.5;
  font-weight: 600;
}

.question-hint {
  background: #ecfdf5;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  color: #059669;
  border-left: 4px solid #10b981;
  font-size: 1rem;
}

.question-hint i {
  margin-right: 0.5rem;
}

.context-box {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  border-radius: 15px;
  padding: 2rem;
  border-left: 5px solid #3b82f6;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1);
}

.context-box i {
  color: #2563eb;
  font-size: 2rem;
  margin-bottom: 1rem;
  display: block;
}

.context-title {
  color: #1e40af;
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.context-description {
  color: #1e40af;
  font-size: 1.2rem;
  line-height: 1.8;
  margin: 0;
  font-weight: 500;
}

.context-question {
  text-align: center;
  color: #1f2937;
  font-size: 1.4rem;
  margin-bottom: 1.5rem;
  font-weight: 700;
  padding: 1rem;
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  border-radius: 12px;
  border: 2px solid #10b981;
}

.question-instruction {
  text-align: center;
  color: #6b7280;
  font-size: 1.1rem;
  margin-top: 1rem;
  font-weight: 500;
  font-style: italic;
}

.option-pronunciation {
  display: block;
  font-size: 0.85rem;
  color: #6b7280;
  font-style: italic;
  margin-top: 0.25rem;
}

.options-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.option-btn {
  display: flex;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.option-btn:hover:not(.disabled) {
  border-color: #10b981;
  transform: translateX(5px);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
}

.option-btn.selected {
  border-color: #10b981;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  transform: translateX(10px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}

.option-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.option-letter {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  margin-right: 1rem;
  color: #374151;
  font-size: 1.1rem;
}

.option-btn.selected .option-letter {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

.option-text {
  flex: 1;
  font-size: 1.05rem;
  font-weight: 500;
}

.action-buttons {
  text-align: center;
}

.btn {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.btn-primary {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.btn-secondary {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
  box-shadow: 0 4px 15px rgba(107, 114, 128, 0.3);
}

.btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(107, 114, 128, 0.4);
}

.btn-lg {
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
}

.result-section {
  margin-bottom: 2rem;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-card {
  background: white;
  border-radius: 20px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

.result-card.correct {
  border-top: 6px solid #10b981;
}

.result-card.incorrect {
  border-top: 6px solid #ef4444;
}

.result-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.result-card.correct .result-icon {
  color: #10b981;
}

.result-card.incorrect .result-icon {
  color: #ef4444;
}

.result-card h3 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: #1f2937;
}

.points-earned {
  font-size: 1.5rem;
  font-weight: 700;
  color: #10b981;
  margin-bottom: 0.75rem;
}

.encouragement {
  color: #6b7280;
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  font-style: italic;
}

.error-content p {
  margin-bottom: 0.75rem;
  color: #6b7280;
}

.correct-answer {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.explanation {
  color: #6b7280;
  font-style: italic;
  margin-bottom: 1.5rem;
  font-size: 1rem;
}

@media (max-width: 768px) {
  .game-header {
    padding: 2rem 1.5rem;
  }
  
  .game-title {
    font-size: 2rem;
  }
  
  .question-card {
    padding: 1.5rem;
  }
  
  .question-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .question-text {
    font-size: 1.4rem;
  }
}

/* Nivel Completado */
.level-complete-section {
  padding: 2rem 0;
}

.level-complete-card {
  background: white;
  border-radius: 20px;
  padding: 3rem 2rem;
  text-align: center;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
  border-top: 6px solid #10b981;
}

.complete-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
  animation: bounce 1s ease-in-out;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.level-complete-card h1 {
  font-size: 2.5rem;
  color: #1f2937;
  margin-bottom: 2rem;
  font-weight: 700;
}

.level-summary {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 3rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  border-radius: 15px;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.summary-stat i {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.summary-stat:nth-child(1) i {
  color: #10b981;
}

.summary-stat:nth-child(2) i {
  color: #ef4444;
}

.summary-stat:nth-child(3) i {
  color: #f59e0b;
}

.summary-stat .value {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  display: block;
}

.summary-stat .label {
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.accuracy-display {
  margin: 2rem 0;
}

.accuracy-circle {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
}

.accuracy-circle .percentage {
  font-size: 2.5rem;
  font-weight: 700;
  color: white;
}

.accuracy-label {
  color: #6b7280;
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Estilos para pantalla de resumen final */
.summary-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 500px;
}

.summary-card {
  background: white;
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
  max-width: 700px;
  width: 100%;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.summary-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.summary-icon {
  font-size: 5rem;
  color: #ffd700;
  margin-bottom: 1rem;
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.summary-header h2 {
  font-size: 2.5rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.summary-subtitle {
  color: #6b7280;
  font-size: 1.1rem;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.stat-card {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 15px;
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.stat-correct {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
}

.stat-incorrect {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
}

.stat-accuracy {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
}

.stat-points {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-correct .stat-icon {
  color: #10b981;
}

.stat-incorrect .stat-icon {
  color: #ef4444;
}

.stat-accuracy .stat-icon {
  color: #f59e0b;
}

.stat-points .stat-icon {
  color: #8b5cf6;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 600;
  margin-top: 0.25rem;
}

.summary-message {
  text-align: center;
  padding: 2rem;
  border-radius: 15px;
  margin-bottom: 2rem;
}

.perfect-game {
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  color: #059669;
}

.great-game {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #2563eb;
}

.good-game {
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  color: #d97706;
}

.keep-learning {
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
  color: #dc2626;
}

.summary-message i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.summary-message h3 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.summary-message p {
  font-size: 1.1rem;
  opacity: 0.9;
}

.summary-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.summary-actions .btn {
  flex: 1;
  min-width: 180px;
  max-width: 250px;
}
</style>

