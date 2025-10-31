/**
 * Configuración de la URL base del backend
 * Funciona tanto en desarrollo (proxy) como en producción (URL completa)
 */

/**
 * Obtiene la URL base del backend según el entorno
 * @returns {string} URL base del backend
 */
export function getApiBaseUrl() {
  // En producción usa VITE_API_URL, en desarrollo usa URL relativa con proxy
  return import.meta.env.VITE_API_URL || ''
}

/**
 * Construye una URL completa del backend
 * @param {string} endpoint - Endpoint sin slash inicial (ej: 'auth/login')
 * @returns {string} URL completa
 */
export function getApiUrl(endpoint) {
  const baseUrl = getApiBaseUrl()
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  
  if (baseUrl) {
    // Producción: URL completa
    return `${baseUrl}/${cleanEndpoint}`
  } else {
    // Desarrollo: usar proxy de Vite
    return `/${cleanEndpoint}`
  }
}

export default {
  getApiBaseUrl,
  getApiUrl
}
