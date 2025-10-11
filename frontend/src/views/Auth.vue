<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">
          MIAPPBORA
        </h1>
        <p class="auth-subtitle">
          {{ isLogin ? 'Inicia Sesión' : 'Registrarse' }}
        </p>
        <p class="auth-description">
          {{ isLogin ? 'Bienvenido de vuelta' : 'Únete y aprende el idioma Bora' }}
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <!-- Email -->
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-envelope"></i>
            Correo Electrónico
          </label>
          <input
            v-model="formData.email"
            type="email"
            class="form-input"
            placeholder="tu@email.com"
            required
          />
        </div>

        <!-- Nombre Completo (solo registro) -->
        <div v-if="!isLogin" class="form-group">
          <label class="form-label">
            <i class="fas fa-user"></i>
            Nombre Completo
          </label>
          <input
            v-model="formData.full_name"
            type="text"
            class="form-input"
            placeholder="Juan Pérez"
            maxlength="255"
            required
          />
        </div>

        <!-- Teléfono (solo registro) -->
        <div v-if="!isLogin" class="form-group">
          <label class="form-label">
            <i class="fas fa-phone"></i>
            Número de Teléfono
          </label>
          <input
            v-model="formData.phone"
            type="tel"
            class="form-input"
            placeholder="+51 999 999 999"
            required
          />
        </div>

        <!-- Contraseña -->
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-lock"></i>
            Contraseña
          </label>
          <div class="password-input">
            <input
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              placeholder="Mínimo 6 caracteres"
              required
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="password-toggle"
            >
              <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
          <div v-if="!isLogin" class="password-hint">
            La contraseña debe tener al menos 6 caracteres
          </div>
          <div v-if="isLogin" class="forgot-password">
            <button type="button" @click="showForgotPassword = true" class="forgot-link">
              Olvidé mi contraseña
            </button>
          </div>
        </div>

        <!-- Error/Success message -->
        <div v-if="error" :class="error.includes('✅') ? 'success-message' : 'error-message'">
          <i :class="error.includes('✅') ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle'"></i>
          {{ error }}
        </div>

        <!-- Submit button -->
        <button 
          type="submit" 
          class="btn btn-primary btn-full"
          :disabled="isLoading"
        >
          <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
          <i v-else :class="isLogin ? 'fas fa-sign-in-alt' : 'fas fa-user-plus'"></i>
          {{ isLogin ? 'Iniciar Sesión' : 'Registrarse' }}
        </button>
      </form>

      <div class="auth-footer">
        <p>
          {{ isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?' }}
          <button @click="toggleMode" class="link-button">
            {{ isLogin ? 'Regístrate aquí' : 'Inicia sesión' }}
          </button>
        </p>
      </div>
    </div>
  </div>

  <!-- Modal Recuperar Contraseña - Validación -->
  <div v-if="showForgotPassword" class="modal-overlay" @click="closeForgotPassword">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Recuperar Contraseña</h3>
        <button @click="closeForgotPassword" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <p class="modal-description">
          Ingresa tu email y los últimos 4 dígitos de tu teléfono:
        </p>
        
        <div class="form-group">
          <label>Email</label>
          <input 
            type="email" 
            v-model="recoveryEmail"
            placeholder="tu@email.com"
            class="form-input"
          >
        </div>
        
        <div class="form-group">
          <label>Últimos 4 dígitos del teléfono</label>
          <input 
            type="text" 
            v-model="recoveryPhone"
            placeholder="9999"
            maxlength="4"
            class="form-input"
          >
        </div>
        
        <div v-if="recoveryError" class="error-message">
          <i class="fas fa-exclamation-triangle"></i>
          {{ recoveryError }}
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="closeForgotPassword" class="btn btn-secondary">
          Cancelar
        </button>
        <button 
          @click="validateRecovery" 
          class="btn btn-primary"
          :disabled="isRecoveryLoading"
        >
          <i v-if="isRecoveryLoading" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-check"></i>
          Validar
        </button>
      </div>
    </div>
  </div>

  <!-- Modal Nueva Contraseña -->
  <div v-if="showNewPassword" class="modal-overlay" @click="closeNewPassword">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Nueva Contraseña</h3>
        <button @click="closeNewPassword" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <p class="modal-description">
          Ingresa tu nueva contraseña:
        </p>
        
        <div class="form-group">
          <label>Nueva Contraseña</label>
          <input 
            type="password" 
            v-model="newPassword"
            placeholder="Mínimo 6 caracteres"
            class="form-input"
          >
        </div>
        
        <div class="form-group">
          <label>Confirmar Contraseña</label>
          <input 
            type="password" 
            v-model="confirmNewPassword"
            placeholder="Repite la contraseña"
            class="form-input"
          >
        </div>
        
        <div v-if="recoveryError" class="error-message">
          <i class="fas fa-exclamation-triangle"></i>
          {{ recoveryError }}
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="closeNewPassword" class="btn btn-secondary">
          Cancelar
        </button>
        <button 
          @click="resetPassword" 
          class="btn btn-primary"
          :disabled="isRecoveryLoading"
        >
          <i v-if="isRecoveryLoading" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-save"></i>
          Cambiar Contraseña
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

export default {
  name: 'AuthView',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const isLogin = ref(true)
    const showPassword = ref(false)
    const isLoading = ref(false)
    const error = ref('')
    
    // Recuperación de contraseña
    const showForgotPassword = ref(false)
    const showNewPassword = ref(false)
    const recoveryEmail = ref('')
    const recoveryPhone = ref('')
    const newPassword = ref('')
    const confirmNewPassword = ref('')
    const recoveryError = ref('')
    const isRecoveryLoading = ref(false)
    
    const formData = reactive({
      email: '',
      full_name: '',
      phone: '',
      password: ''
    })

    // Generar username desde primer nombre + teléfono
    const generateUsername = (fullName, phone) => {

      const formattedPhone = phone.replace(/^\+\d{1,3}/, '').slice(1, 3)

      if (!fullName || !fullName.trim()) {
        // Si no hay nombre, usar email
        const emailPrefix = formData.email.split('@')[0]
          .toLowerCase()
          .replace(/[^a-z0-9]/g, '')
        return `${emailPrefix}-${formattedPhone}`
      }
      
      // Tomar primer nombre, quitar acentos y caracteres especiales
      const firstName = fullName.trim().split(' ')[0]
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '')
      
      return `${firstName}-${formattedPhone}`
    }

    const toggleMode = () => {
      isLogin.value = !isLogin.value
      error.value = ''
      Object.keys(formData).forEach(key => {
        formData[key] = ''
      })
    }
    
    const handleSubmit = async () => {
      error.value = ''
      isLoading.value = true
      
      try {
        const endpoint = isLogin.value ? '/auth/login' : '/auth/register'
        const payload = isLogin.value
          ? {
              email: formData.email,
              password: formData.password
            }
          : {
              email: formData.email,
              username: generateUsername(formData.full_name, formData.phone),
              phone: formData.phone,
              password: formData.password,
              full_name: formData.full_name || null
            }

        const response = await fetch(`http://localhost:8000${endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Error en la solicitud')
        }

        if (isLogin.value) {
          // LOGIN: Guardar token y usuario, luego redirigir al home
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('user', JSON.stringify(data.user))
          
          // Actualizar authStore
          authStore.setUser(data.user, data.access_token)
          
          // Redirigir al home
          router.push('/home')
        } else {
          // REGISTRO: Cambiar a modo login y limpiar formulario
          error.value = ''
          
          // Guardar email para prellenar el formulario de login
          const registeredEmail = formData.email
          
          // Limpiar formulario
          Object.keys(formData).forEach(key => {
            formData[key] = ''
          })
          
          // Prellenar email en login
          formData.email = registeredEmail
          
          // Cambiar a modo login
          isLogin.value = true
          
          // Mostrar mensaje de éxito
          error.value = '✅ Registro exitoso! Ahora inicia sesión'
          
          // Limpiar mensaje después de 3 segundos
          setTimeout(() => {
            if (error.value.includes('✅')) {
              error.value = ''
            }
          }, 3000)
        }
        
      } catch (err) {
        error.value = err.message || 'Error al procesar la solicitud'
      } finally {
        isLoading.value = false
      }
    }
    
    const validateRecovery = async () => {
      recoveryError.value = ''
      
      if (!recoveryEmail.value || !recoveryPhone.value) {
        recoveryError.value = 'Debes completar ambos campos'
        return
      }
      
      if (!recoveryEmail.value.includes('@')) {
        recoveryError.value = 'El email no es válido'
        return
      }
      
      if (recoveryPhone.value.length !== 4) {
        recoveryError.value = 'Debes ingresar exactamente 4 dÃ­gitos'
        return
      }
      
      isRecoveryLoading.value = true
      
      try {
        // TODO: Llamar al backend para validar
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Cerrar primer modal y abrir segundo
        showForgotPassword.value = false
        showNewPassword.value = true
        
      } catch (err) {
        recoveryError.value = 'Error al validar los datos'
      } finally {
        isRecoveryLoading.value = false
      }
    }
    
    const resetPassword = async () => {
      recoveryError.value = ''
      
      if (!newPassword.value || !confirmNewPassword.value) {
        recoveryError.value = 'Debes completar ambos campos'
        return
      }
      
      if (newPassword.value.length < 6) {
        recoveryError.value = 'La contraseña debe tener al menos 6 caracteres'
        return
      }
      
      if (newPassword.value !== confirmNewPassword.value) {
        recoveryError.value = 'Las contraseñas no coinciden'
        return
      }
      
      isRecoveryLoading.value = true
      
      try {
        // TODO: Llamar al backend para cambiar contraseña
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        showNewPassword.value = false
        error.value = ''
        alert('Contraseña cambiada exitosamente')
        
        // Limpiar campos
        recoveryEmail.value = ''
        recoveryPhone.value = ''
        newPassword.value = ''
        confirmNewPassword.value = ''
        
      } catch (err) {
        recoveryError.value = 'Error al cambiar la contraseña'
      } finally {
        isRecoveryLoading.value = false
      }
    }
    
    const closeForgotPassword = () => {
      showForgotPassword.value = false
      recoveryEmail.value = ''
      recoveryPhone.value = ''
      recoveryError.value = ''
    }
    
    const closeNewPassword = () => {
      showNewPassword.value = false
      newPassword.value = ''
      confirmNewPassword.value = ''
      recoveryError.value = ''
    }

    return {
      isLogin,
      showPassword,
      isLoading,
      error,
      formData,
      toggleMode,
      handleSubmit,
      showForgotPassword,
      showNewPassword,
      recoveryEmail,
      recoveryPhone,
      newPassword,
      confirmNewPassword,
      recoveryError,
      isRecoveryLoading,
      validateRecovery,
      resetPassword,
      closeForgotPassword,
      closeNewPassword
    }
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  padding: 2rem;
}

.auth-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  padding: 3rem;
  width: 100%;
  max-width: 450px;
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #059669;
  margin-bottom: 0.5rem;
}

.auth-subtitle {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.auth-description {
  color: #7f8c8d;
  font-size: 0.95rem;
}

.auth-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.form-label i {
  margin-right: 0.5rem;
  color: #10b981;
  width: 16px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #10b981;
}

.password-input {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #7f8c8d;
  cursor: pointer;
  padding: 4px;
}

.password-hint {
  font-size: 0.8rem;
  color: #7f8c8d;
  margin-top: 0.25rem;
}

.forgot-password {
  margin-top: 0.5rem;
  text-align: right;
}

.forgot-link {
  background: none;
  border: none;
  color: #10b981;
  cursor: pointer;
  font-size: 0.875rem;
  text-decoration: underline;
  padding: 0;
}

.forgot-link:hover {
  color: #059669;
}

.error-message {
  background: #ffe6e6;
  color: #e74c3c;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #e74c3c;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.error-message i {
  margin-right: 0.5rem;
}

.success-message {
  background: #d1fae5;
  color: #059669;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #10b981;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.success-message i {
  margin-right: 0.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.btn-primary {
  background: #10b981;
  color: white;
}

.btn-primary:hover {
  background: #059669;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-full {
  width: 100%;
  padding: 14px;
  font-size: 1.05rem;
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.link-button {
  background: none;
  border: none;
  color: #10b981;
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
}

.link-button:hover {
  color: #059669;
}

/* Modales */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 1.5rem 0 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1.5rem;
}

.modal-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 0 1.5rem;
}

.modal-description {
  color: #6b7280;
  margin-bottom: 1.5rem;
  line-height: 1.5;
  font-size: 0.95rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
  margin-top: 1.5rem;
}

@media (max-width: 768px) {
  .auth-container {
    padding: 1rem;
  }
  
  .auth-card {
    padding: 2rem;
  }
  
  .auth-title {
    font-size: 2rem;
  }
}
</style>


