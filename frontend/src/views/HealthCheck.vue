<template>
  <div class="health-check">
    <div class="container">
      <div class="header">
        <h1>
          <i class="fas fa-heartbeat"></i>
          Estado de Servicios - MIAPPBORA
        </h1>
        <p class="subtitle">Verificación de conexiones con servicios externos</p>
      </div>

      <!-- Botón de recarga -->
      <div class="actions">
        <button 
          @click="checkStatus" 
          class="btn btn-primary"
          :disabled="isLoading"
        >
          <i :class="isLoading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"></i>
          {{ isLoading ? 'Verificando...' : 'Verificar Estado' }}
        </button>
      </div>

      <!-- Estado general -->
      <div v-if="statusData" class="status-overview">
        <div :class="['status-badge', getStatusClass(statusData.overall_status)]">
          <i :class="getStatusIcon(statusData.overall_status)"></i>
          {{ getStatusText(statusData.overall_status) }}
        </div>
        
        <div class="app-info">
          <h3>{{ statusData.app_info?.name }}</h3>
          <span class="version">v{{ statusData.app_info?.version }}</span>
          <span :class="['mode', statusData.app_info?.debug_mode ? 'debug' : 'prod']">
            {{ statusData.app_info?.debug_mode ? 'DEBUG' : 'PRODUCCIÓN' }}
          </span>
        </div>
      </div>

      <!-- Servicios -->
      <div v-if="statusData?.services" class="services-grid">
        <!-- Supabase -->
        <div class="service-card">
          <div class="service-header">
            <i class="fas fa-database"></i>
            <h3>Supabase</h3>
            <span :class="['badge', getBadgeClass(statusData.services.supabase?.status)]">
              {{ statusData.services.supabase?.status }}
            </span>
          </div>
          
          <div class="service-body">
            <p>{{ statusData.services.supabase?.message }}</p>
            
            <div v-if="statusData.services.supabase?.url !== 'not_configured'" class="service-details">
              <div class="detail-item">
                <span class="label">URL:</span>
                <span class="value">{{ truncateUrl(statusData.services.supabase?.url) }}</span>
              </div>
            </div>
            
            <div v-else class="warning-box">
              <i class="fas fa-exclamation-triangle"></i>
              <div>
                <strong>Configuración necesaria:</strong>
                <ol>
                  <li>Crear proyecto en <a href="https://supabase.com" target="_blank">supabase.com</a></li>
                  <li>Copiar URL y API Key</li>
                  <li>Configurar en archivo .env del backend</li>
                </ol>
              </div>
            </div>
          </div>
        </div>

        <!-- HuggingFace -->
        <div class="service-card">
          <div class="service-header">
            <i class="fas fa-brain"></i>
            <h3>HuggingFace</h3>
            <span :class="['badge', getBadgeClass(statusData.services.huggingface?.status)]">
              {{ statusData.services.huggingface?.status }}
            </span>
          </div>
          
          <div class="service-body">
            <p>{{ statusData.services.huggingface?.message }}</p>
            
            <div v-if="statusData.services.huggingface?.status === 'connected'" class="service-details">
              <div class="detail-item">
                <span class="label">Modelo de Embeddings:</span>
                <span class="value">{{ statusData.services.huggingface?.embedding_model }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Modelo LLM:</span>
                <span class="value">{{ statusData.services.huggingface?.llm_model }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Dimensión:</span>
                <span class="value">{{ statusData.services.huggingface?.embedding_dimension }}d</span>
              </div>
              <div class="detail-item">
                <span class="label">Test de Embedding:</span>
                <span :class="['value', statusData.services.huggingface?.test_embedding === 'success' ? 'success' : 'error']">
                  {{ statusData.services.huggingface?.test_embedding }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Configuración -->
      <div v-if="statusData?.configuration" class="configuration-section">
        <h3>
          <i class="fas fa-cog"></i>
          Configuración
        </h3>
        
        <div class="config-grid">
          <div class="config-item">
            <i :class="['fas', statusData.configuration.supabase_url === 'configured' ? 'fa-check-circle success' : 'fa-times-circle error']"></i>
            <span>Supabase URL</span>
            <span class="value">{{ statusData.configuration.supabase_url }}</span>
          </div>
          
          <div class="config-item">
            <i :class="['fas', statusData.configuration.supabase_key === 'configured' ? 'fa-check-circle success' : 'fa-times-circle error']"></i>
            <span>Supabase Key</span>
            <span class="value">{{ statusData.configuration.supabase_key }}</span>
          </div>
          
          <div class="config-item">
            <i :class="['fas', statusData.configuration.huggingface_key === 'configured' ? 'fa-check-circle success' : 'fa-times-circle error']"></i>
            <span>HuggingFace Key</span>
            <span class="value">{{ statusData.configuration.huggingface_key }}</span>
          </div>
        </div>
      </div>

      <!-- Issues y Recomendaciones -->
      <div v-if="statusData?.issues && statusData.issues.length > 0" class="issues-section">
        <h3>
          <i class="fas fa-exclamation-triangle"></i>
          Problemas Detectados
        </h3>
        <ul class="issues-list">
          <li v-for="(issue, index) in statusData.issues" :key="index">
            {{ issue }}
          </li>
        </ul>
        
        <div v-if="statusData.recommendations" class="recommendations">
          <h4>Recomendaciones:</h4>
          <ul>
            <li v-for="(rec, index) in statusData.recommendations" :key="index">
              {{ rec }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="error-box">
        <i class="fas fa-exclamation-circle"></i>
        <div>
          <strong>Error al conectar con el servidor</strong>
          <p>{{ error }}</p>
          <p class="hint">Asegúrate de que el backend esté corriendo y sea accesible</p>
          <p class="hint">En desarrollo: verifica el proxy de Vite | En producción: verifica VITE_API_URL</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { healthService } from '../services/healthService'

export default {
  name: 'HealthCheck',
  setup() {
    const statusData = ref(null)
    const isLoading = ref(false)
    const error = ref(null)

    const checkStatus = async () => {
      isLoading.value = true
      error.value = null

      try {
        const data = await healthService.checkConnections()
        statusData.value = data
      } catch (err) {
        error.value = err.message || 'No se pudo conectar con el servidor'
        console.error('Error:', err)
      } finally {
        isLoading.value = false
      }
    }

    const getStatusClass = (status) => {
      const classes = {
        'ok': 'status-ok',
        'degraded': 'status-warning',
        'error': 'status-error'
      }
      return classes[status] || 'status-unknown'
    }

    const getStatusIcon = (status) => {
      const icons = {
        'ok': 'fas fa-check-circle',
        'degraded': 'fas fa-exclamation-triangle',
        'error': 'fas fa-times-circle'
      }
      return icons[status] || 'fas fa-question-circle'
    }

    const getStatusText = (status) => {
      const texts = {
        'ok': 'Todos los servicios operativos',
        'degraded': 'Servicios con advertencias',
        'error': 'Servicios con errores'
      }
      return texts[status] || 'Estado desconocido'
    }

    const getBadgeClass = (status) => {
      const classes = {
        'connected': 'badge-success',
        'disconnected': 'badge-warning',
        'error': 'badge-error',
        'ok': 'badge-success'
      }
      return classes[status] || 'badge-unknown'
    }

    const truncateUrl = (url) => {
      if (!url || url === 'not_configured') return 'No configurado'
      if (url.length > 40) {
        return url.substring(0, 40) + '...'
      }
      return url
    }

    onMounted(() => {
      checkStatus()
    })

    return {
      statusData,
      isLoading,
      error,
      checkStatus,
      getStatusClass,
      getStatusIcon,
      getStatusText,
      getBadgeClass,
      truncateUrl
    }
  }
}
</script>

<style scoped>
.health-check {
  min-height: 100vh;
  background: linear-gradient(135deg, #2d5016 0%, #4a7c2c 50%, #6a994e 100%);
  padding: 2rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.header h1 i {
  color: #a7c957;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
}

.actions {
  text-align: center;
  margin-bottom: 2rem;
}

.btn {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #a7c957;
  color: #2d5016;
}

.btn-primary:hover:not(:disabled) {
  background: #bcdb74;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(167, 201, 87, 0.4);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status-overview {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 25px;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.status-ok {
  background: #d4edda;
  color: #155724;
}

.status-warning {
  background: #fff3cd;
  color: #856404;
}

.status-error {
  background: #f8d7da;
  color: #721c24;
}

.app-info {
  margin-top: 1rem;
}

.app-info h3 {
  font-size: 1.5rem;
  color: #2d5016;
  margin-bottom: 0.5rem;
}

.version {
  background: #e9ecef;
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.9rem;
  margin: 0 0.5rem;
}

.mode {
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.9rem;
  font-weight: 600;
}

.mode.debug {
  background: #fff3cd;
  color: #856404;
}

.mode.prod {
  background: #d4edda;
  color: #155724;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.service-card {
  background: white;
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.service-header {
  background: linear-gradient(135deg, #4a7c2c, #6a994e);
  color: white;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.service-header i {
  font-size: 2rem;
}

.service-header h3 {
  flex: 1;
  margin: 0;
  font-size: 1.3rem;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-success {
  background: #a7c957;
  color: #2d5016;
}

.badge-warning {
  background: #ffd166;
  color: #663d00;
}

.badge-error {
  background: #ef476f;
  color: white;
}

.service-body {
  padding: 1.5rem;
}

.service-body > p {
  margin-bottom: 1rem;
  color: #495057;
}

.service-details {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #dee2e6;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  font-weight: 600;
  color: #495057;
}

.detail-item .value {
  color: #6c757d;
  font-family: monospace;
}

.detail-item .value.success {
  color: #28a745;
}

.detail-item .value.error {
  color: #dc3545;
}

.warning-box {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  gap: 1rem;
}

.warning-box i {
  color: #856404;
  font-size: 1.5rem;
}

.warning-box ol {
  margin: 0.5rem 0 0 1.5rem;
}

.warning-box a {
  color: #4a7c2c;
  font-weight: 600;
}

.configuration-section {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.configuration-section h3 {
  color: #2d5016;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.config-item i {
  font-size: 1.2rem;
}

.config-item i.success {
  color: #28a745;
}

.config-item i.error {
  color: #dc3545;
}

.config-item .value {
  margin-left: auto;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.issues-section {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.issues-section h3 {
  color: #856404;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.issues-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem 0;
}

.issues-list li {
  padding: 0.5rem 0;
  color: #856404;
}

.issues-list li:before {
  content: "⚠️ ";
  margin-right: 0.5rem;
}

.recommendations {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.recommendations h4 {
  color: #2d5016;
  margin-bottom: 0.5rem;
}

.recommendations ul {
  margin: 0.5rem 0 0 1.5rem;
  color: #495057;
}

.error-box {
  background: #f8d7da;
  border-left: 4px solid #dc3545;
  padding: 1.5rem;
  border-radius: 8px;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.error-box i {
  color: #721c24;
  font-size: 1.5rem;
}

.error-box strong {
  color: #721c24;
  display: block;
  margin-bottom: 0.5rem;
}

.error-box p {
  color: #721c24;
  margin: 0.25rem 0;
}

.error-box .hint {
  font-size: 0.9rem;
  opacity: 0.8;
}

@media (max-width: 768px) {
  .health-check {
    padding: 1rem;
  }

  .header h1 {
    font-size: 1.8rem;
  }

  .services-grid {
    grid-template-columns: 1fr;
  }

  .config-grid {
    grid-template-columns: 1fr;
  }
}
</style>
