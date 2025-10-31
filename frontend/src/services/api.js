/**
 * Servicio de API para MIAPPBORA
 * Cliente HTTP para comunicación con el backend
 */
import axios from 'axios'

// Configuración base de axios
const api = axios.create({
  // En producción usa VITE_API_URL, en desarrollo usa proxy local
  baseURL: import.meta.env.VITE_API_URL || '/api',
  // Algunas consultas (RAG + OpenAI) pueden demorar >10s.
  // Subimos el timeout global a 30s para evitar ECONNABORTED en casos legítimos.
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para agregar token de autenticación
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/auth'
    }
    return Promise.reject(error)
  }
)

export default api
