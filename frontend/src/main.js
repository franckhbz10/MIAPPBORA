import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from './App.vue'
import Home from './views/Home.vue'
import Auth from './views/Auth.vue'
import Game from './views/Game.vue'
import HealthCheck from './views/HealthCheck.vue'
import Profile from './views/Profile.vue'
import { useAuthStore } from './stores/authStore'

// Configurar router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Auth',
      component: Auth
    },
    {
      path: '/home',
      name: 'Home',
      component: Home
    },
    {
      path: '/game',
      name: 'Game',
      component: Game
    },
    {
      path: '/profile',
      name: 'Profile',
      component: Profile,
      meta: { requiresAuth: true }
    },
    {
      path: '/health',
      name: 'HealthCheck',
      component: HealthCheck
    }
  ]
})

// Crear app
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Inicializar autenticación desde localStorage
const authStore = useAuthStore()
authStore.initialize()

app.mount('#app')
