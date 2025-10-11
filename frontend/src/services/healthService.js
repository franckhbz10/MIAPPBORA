/**
 * Servicio de Health Check
 * Verificación de conexiones con servicios externos
 */
import api from './api'

export const healthService = {
  /**
   * Verifica el estado general del servidor
   */
  async checkHealth() {
    try {
      const response = await api.get('/health/')
      return response.data
    } catch (error) {
      throw new Error('No se pudo conectar con el servidor')
    }
  },

  /**
   * Verifica el estado de todas las conexiones
   * Incluye Supabase, HuggingFace y configuración
   */
  async checkConnections() {
    try {
      const response = await api.get('/health/connections')
      return response.data
    } catch (error) {
      console.error('Error al verificar conexiones:', error)
      throw error
    }
  },

  /**
   * Verifica solo la conexión con Supabase
   */
  async checkSupabase() {
    try {
      const response = await api.get('/health/supabase')
      return response.data
    } catch (error) {
      console.error('Error al verificar Supabase:', error)
      throw error
    }
  },

  /**
   * Verifica solo HuggingFace
   */
  async checkHuggingFace() {
    try {
      const response = await api.get('/health/huggingface')
      return response.data
    } catch (error) {
      console.error('Error al verificar HuggingFace:', error)
      throw error
    }
  }
}
