<template>
  <div class="home-view">
    <!-- Hero Section -->
    <div class="hero-section fade-in">
      <div class="hero-content">
        <h1 class="hero-title">
          🌿 Aprende Bora de Forma Divertida
        </h1>
        <p class="hero-subtitle">
          Descubre el idioma indígena amazónico con nuestro mentor inteligente y minijuegos
        </p>
        
        <div class="hero-buttons">
          <router-link to="/chat" class="btn btn-primary btn-lg">
            <i class="fas fa-robot"></i>
            Mentor Bora
          </router-link>
          <router-link to="/game" class="btn btn-secondary btn-lg">
            <i class="fas fa-gamepad"></i>
            Minijuegos
          </router-link>
        </div>
      </div>
    </div>
    
    <!-- Features Section -->
    <div class="features-section">
      <div class="container">
        <h2 class="section-title">Características Principales</h2>
        
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-robot"></i>
            </div>
            <h3>Mentor Bora</h3>
            <p>Aprende a comunicarte con nuestro Mentor Bora que te enseña frases cotidianas en Bora</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-puzzle-piece"></i>
            </div>
            <h3>Minijuegos Interactivos</h3>
            <p>Practica vocabulario Bora con juegos divertidos y desafiantes</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-trophy"></i>
            </div>
            <h3>Sistema de Recompensas</h3>
            <p>Gana puntos, sube de nivel y desbloquea logros mientras aprendes</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-book-open"></i>
            </div>
            <h3>Frases Cotidianas</h3>
            <p>Más de 52 frases útiles para situaciones del día a día</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Categories Section -->
    <div class="categories-section">
      <div class="container">
        <h2 class="section-title">Categorías de Aprendizaje</h2>
        
        <div class="categories-grid">
          <div class="category-card">
            <div class="category-icon">
              <i class="fas fa-handshake"></i>
            </div>
            <h4>Saludos y Presentaciones</h4>
            <p>Aprende a presentarte y saludar en Bora</p>
          </div>
          
          <div class="category-card">
            <div class="category-icon">
              <i class="fas fa-user-friends"></i>
            </div>
            <h4>Conversación General</h4>
            <p>Frases para el día a día y situaciones comunes</p>
          </div>
          
          <div class="category-card">
            <div class="category-icon">
              <i class="fas fa-map-marker-alt"></i>
            </div>
            <h4>Ubicación</h4>
            <p>Orientación y desplazamientos</p>
          </div>
          
          <div class="category-card">
            <div class="category-icon">
              <i class="fas fa-heart"></i>
            </div>
            <h4>Relaciones Cotidianas</h4>
            <p>Vocabulario sobre familia y amistades</p>
          </div>
          
          <div class="category-card">
            <div class="category-icon">
              <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h4>Emergencias</h4>
            <p>Frases importantes para situaciones urgentes</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Rewards Section -->
    <div class="rewards-section">
      <div class="container">
        <h2 class="section-title">Recompensas Disponibles</h2>
        
        <div class="rewards-grid">
          <div class="reward-card">
            <div class="reward-icon bronze">
              <i class="fas fa-medal"></i>
            </div>
            <h4>Nivel Estusiasta</h4>
            <p>0 - 50 puntos</p>
          </div>
          
          <div class="reward-card">
            <div class="reward-icon silver">
              <i class="fas fa-medal"></i>
            </div>
            <h4>Nivel Hablante</h4>
            <p>50 - 300 puntos</p>
          </div>
          
          <div class="reward-card">
            <div class="reward-icon gold">
              <i class="fas fa-medal"></i>
            </div>
            <h4>Nivel Nativo</h4>
            <p>300 - 600 puntos</p>
          </div>
          
          <div class="reward-card">
            <div class="reward-icon diamond">
              <i class="fas fa-crown"></i>
            </div>
            <h4>Nivel Maestro Bora</h4>
            <p>600+ puntos</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Widget de Feedback -->
    <FeedbackWidget />
  </div>
</template>

<script>
import FeedbackWidget from '@/components/FeedbackWidget.vue'

export default {
  name: 'Home',
  components: {
    FeedbackWidget
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
}

.hero-section {
  text-align: center;
  padding: 5rem 2rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  margin-bottom: 4rem;
}

.hero-content {
  max-width: 900px;
  margin: 0 auto;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  color: white;
  margin-bottom: 1.5rem;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.hero-subtitle {
  font-size: 1.4rem;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 3rem;
  line-height: 1.7;
}

.hero-buttons {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.btn-lg {
  padding: 1.2rem 2.5rem;
  font-size: 1.2rem;
}

.btn-primary {
  background: white;
  color: #059669;
}

.btn-primary:hover {
  background: #f0fdf4;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 600;
  color: #1f2937;
  text-align: center;
  margin-bottom: 3rem;
}

/* Features */
.features-section {
  margin-bottom: 5rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

.feature-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, #6bffa6, #8fff00);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: white;
}

.feature-card h3 {
  font-size: 1.4rem;
  color: #1f2937;
  margin-bottom: 1rem;
}

.feature-card p {
  color: #6b7280;
  line-height: 1.6;
}

/* Categories */
.categories-section {
  margin-bottom: 5rem;
  background: #f9fafb;
  padding: 5rem 0;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.category-card {
  background: white;
  border-radius: 50%;
  padding: 2rem;
  text-align: center;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
  aspect-ratio: 1 / 1;
}


.category-card:hover {
  border-color: #10b981;
  transform: translateY(-4px);
}

.category-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 1rem;
  background: #c1ff72;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #059669;
}

.category-card h4 {
  font-size: 1.1rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.category-card p {
  color: #6b7280;
  font-size: 0.9rem;
}

/* Rewards */
.rewards-section {
  margin-bottom: 5rem;
}

.rewards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 2rem;
}

.reward-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.reward-card:hover {
  transform: scale(1.05);
}

.reward-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: white;
}

.reward-icon.bronze {
  background: linear-gradient(135deg, #cd7f32, #a65a1e);
}

.reward-icon.silver {
  background: linear-gradient(135deg, #c0c0c0, #a8a8a8);
}

.reward-icon.gold {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
}

.reward-icon.diamond {
  background: linear-gradient(135deg, #b9f2ff, #1e90ff);
}

.reward-card h4 {
  font-size: 1.2rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.reward-card p {
  color: #6b7280;
  margin-bottom: 1rem;
}

.reward-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #10b981;
  color: white;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.fade-in {
  animation: fadeIn 1s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.1rem;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .hero-buttons {
    flex-direction: column;
    gap: 1rem;
  }
  
  .btn-lg {
    width: 100%;
    justify-content: center;
  }
}
</style>
