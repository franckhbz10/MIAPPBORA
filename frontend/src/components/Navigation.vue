<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link :to="authStore.isAuthenticated ? '/home' : '/'" class="nav-logo">
        <!-- <i class="fas fa-globe-americas"></i> -->
        <!-- <span>MIAPPBORA</span> -->
         <img src="../assets/logo/logo-white.png" alt="Logo MiAppBora" class="nav-logo-image">
      </router-link>
      
      <div class="nav-links">
        <template v-if="authStore.isAuthenticated">
          <!-- <router-link to="/home" class="nav-link" :class="{ active: $route.path === '/home' }">
            <i class="fas fa-home"></i>
            <span>Inicio</span>
          </router-link> -->
          <router-link to="/chat" class="nav-link" :class="{ active: $route.path === '/chat' }">
            <i class="fas fa-comments"></i>
            <span>Mentor Bora</span>
          </router-link>
          <router-link to="/game" class="nav-link" :class="{ active: $route.path === '/game' }">
            <i class="fas fa-gamepad"></i>
            <span>Minijuego</span>
          </router-link>
        </template>
      </div>
      
      <div class="nav-auth">
        <template v-if="authStore.isAuthenticated">
          <div class="user-menu">
            <router-link to="/profile" class="user-info">
              <div class="user-avatar">
                <i class="fas fa-user-circle"></i>
              </div>
              <span class="username">{{ authStore.getUsername }}</span>
            </router-link>
            <button @click="logout" class="logout-btn" title="Cerrar sesión">
              <i class="fas fa-sign-out-alt"></i>
            </button>
          </div>
        </template>
        
        <template v-else>
          <router-link to="/" class="nav-link auth-btn">
            <i class="fas fa-sign-in-alt"></i>
            <span>Ingresar</span>
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'

export default {
  name: 'Navigation',
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()
    
    // Cargar usuario desde localStorage al montar el componente
    authStore.loadUserFromStorage()
    
    const logout = () => {
      authStore.logout()
      router.push('/')
    }
    
    return {
      authStore,
      logout
    }
  }
}
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
}

/* .nav-logo {
  display: flex;
  align-items: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  gap: 0.5rem;
  text-decoration: none;
  transition: transform 0.3s ease;
} */
.nav-logo-image {
  height: 70px;
}

.nav-logo:hover {
  transform: scale(1.05);
}

.nav-logo i {
  font-size: 1.8rem;
}

.nav-links {
  display: flex;
  gap: 1rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  text-decoration: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 0.95rem;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.nav-link.active {
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.nav-link i {
  font-size: 1.1rem;
}

.nav-auth {
  display: flex;
  align-items: center;
}

.auth-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.3);
  padding: 0.6rem 1.5rem;
  border-radius: 25px;
  transition: all 0.3s ease;
}

.auth-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  border-radius: 25px;
  background: rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
  text-decoration: none;
  color: white;
  cursor: pointer;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
}

.username {
  color: white;
  font-weight: 500;
  font-size: 0.95rem;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.5rem;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .nav-container {
    padding: 1rem;
  }
  
  .nav-links {
    gap: 0.5rem;
  }
  
  .nav-link {
    padding: 0.5rem 0.8rem;
  }
  
  .nav-link span {
    display: none;
  }
  
  .username {
    display: none;
  }
  
  .nav-logo span {
    font-size: 1.2rem;
  }
}

@media (max-width: 480px) {
  .nav-logo span {
    display: none;
  }
}
</style>
