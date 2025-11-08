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
                <img v-if="userAvatar" 
                     :src="userAvatar" 
                     :alt="authStore.getUsername"
                     class="avatar-img" />
                <i v-else class="fas fa-user-circle"></i>
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
import { useProfileStore } from '../stores/profileStore'
import { useRouter } from 'vue-router'
import { computed } from 'vue'

export default {
  name: 'Navigation',
  setup() {
    const authStore = useAuthStore()
    const profileStore = useProfileStore()
    const router = useRouter()
    
    // Cargar usuario desde localStorage al montar el componente
    authStore.loadUserFromStorage()
    
    // Computed para avatar que se actualiza automáticamente
    const userAvatar = computed(() => {
      return profileStore.user?.avatar_url || authStore.user?.avatar_url
    })
    
    const logout = () => {
      authStore.logout()
      router.push('/')
    }
    
    return {
      authStore,
      profileStore,
      userAvatar,
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
  padding: 0.5rem 2rem;
  gap: 2rem;
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
  height: 90px;
  transition: transform 0.3s ease;
}

.nav-logo:hover .nav-logo-image {
  transform: scale(1.05);
}

.nav-logo i {
  font-size: 1.8rem;
}

.nav-links {
  display: flex;
  gap: 2rem;
  flex: 1;
  justify-content: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: white;
  text-decoration: none;
  padding: 0.8rem 1.8rem;
  border-radius: 12px;
  transition: all 0.3s ease;
  font-weight: 600;
  font-size: 1.1rem;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.nav-link.active {
  background: rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.nav-link i {
  font-size: 1.3rem;
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
  gap: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 1.3rem;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  text-decoration: none;
  color: white;
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.8rem;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

.user-avatar .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.username {
  color: white;
  font-weight: 600;
  font-size: 1.05rem;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.6rem;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px) rotate(10deg);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.logout-btn i {
  font-size: 1.2rem;
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
