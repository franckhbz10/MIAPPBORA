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
  const apiUrl = import.meta.env.VITE_API_URL
  
  // Debug: log en consola para verificar configuración
  // corregir typo DzEV -> DEV
  if (import.meta.env.DEV) {
    console.log('[API Config] Mode:', import.meta.env.MODE)
    console.log('[API Config] VITE_API_URL:', apiUrl)
  }
  
  // Fallback a Railway si no está configurado (temporal para testing)
  // TODO: Configurar VITE_API_URL en Vercel Environment Variables
  return apiUrl || (import.meta.env.PROD ? 'https://miappbora-production.up.railway.app' : '')
}

/**
 * Construye una URL completa del backend
 * @param {string} endpoint - Endpoint (puede empezar con o sin /)
 * @returns {string} URL completa
 */
export function getApiUrl(endpoint) {
  const baseUrl = getApiBaseUrl()
  // Limpiar endpoint: quitar / inicial y espacios
  const cleanEndpoint = endpoint.trim().replace(/^\/+/, '')
  
  if (baseUrl) {
    // Producción: URL completa (Railway/Vercel)
    // Asegurar que baseUrl no tenga trailing slash
    const cleanBase = baseUrl.replace(/\/+$/, '')
    const fullUrl = `${cleanBase}/${cleanEndpoint}`
    
    if (import.meta.env.DEV) {
      console.log('[API Config] Full URL:', fullUrl)
    }
    // En producción también loggeamos la URL elegida (solo para debugging inicial)
    if (import.meta.env.PROD) {
      // eslint-disable-next-line no-console
      console.log('[API Config] Using backend URL (production):', cleanBase)
    }
    
    return fullUrl
  } else {
    // Desarrollo: usar proxy de Vite /api -> http://localhost:8000
    const proxyUrl = `/api/${cleanEndpoint}`
    
    if (import.meta.env.DEV) {
      console.log('[API Config] Proxy URL:', proxyUrl)
    }
    
    return proxyUrl
  }
}

export default {
  getApiBaseUrl,
  getApiUrl
}
