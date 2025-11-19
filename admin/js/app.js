// ==========================================
// APP - APLICACIÓN PRINCIPAL
// ==========================================

// Variables globales
let currentPageName = 'dashboard';
let api = null;

// Inicializar aplicación
document.addEventListener('DOMContentLoaded', async function() {
    console.log('App initializing...');
    
    // Verificar autenticación
    if (!checkAuth()) {
        console.log('Auth check failed, redirecting to login');
        return;
    }
    
    console.log('Auth check passed');
    
    // Inicializar cliente API
    api = new ApiClient();
    console.log('API client initialized');
    
    // Cargar información del usuario
    loadUserInfo();
    
    // Configurar navegación
    setupNavigation();
    
    // Configurar botón de actualizar
    setupRefreshButton();
    
    // Configurar sidebar toggle
    setupSidebarToggle();
    
    console.log('Loading initial page: dashboard');
    // Cargar página inicial
    changePage('dashboard');
});

// Cargar información del usuario
function loadUserInfo() {
    try {
        const userData = JSON.parse(localStorage.getItem('admin_user'));
        
        if (userData) {
            document.getElementById('adminName').textContent = userData.username || 'Admin';
            document.getElementById('adminEmail').textContent = userData.email;
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Configurar navegación
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.dataset.page;
            changePage(page);
        });
    });
}

// Cambiar de página
async function changePage(pageName) {
    console.log('Changing page to:', pageName);
    
    // Actualizar estado activo en navegación
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === pageName) {
            link.classList.add('active');
        }
    });
    
    // Actualizar título y subtítulo
    updatePageHeader(pageName);
    
    // Limpiar contenido actual
    document.getElementById('pageContent').innerHTML = '<div class="loading-container"><div class="loading-spinner"></div><p>Cargando...</p></div>';
    
    // Cargar nueva página
    currentPageName = pageName;
    
    try {
        console.log('Loading page content for:', pageName);
        switch(pageName) {
            case 'dashboard':
                await loadDashboard();
                break;
            case 'users':
                await loadUsers();
                break;
            case 'feedback':
                await loadFeedback();
                break;
            default:
                showError('Página no encontrada');
        }
        console.log('Page loaded successfully');
    } catch (error) {
        console.error('Error loading page:', error);
        showError('Error al cargar la página: ' + error.message);
    }
}

// Actualizar encabezado de página
function updatePageHeader(pageName) {
    const titles = {
        dashboard: {
            title: 'Dashboard',
            subtitle: 'Resumen general del sistema'
        },
        users: {
            title: 'Gestión de Usuarios',
            subtitle: 'Administrar usuarios registrados'
        },
        feedback: {
            title: 'Feedback',
            subtitle: 'Opiniones y calificaciones de usuarios'
        }
    };
    
    const pageInfo = titles[pageName] || { title: 'Panel Admin', subtitle: '' };
    
    document.getElementById('pageTitle').textContent = pageInfo.title;
    document.getElementById('pageSubtitle').textContent = pageInfo.subtitle;
}

// Configurar botón de actualizar
function setupRefreshButton() {
    const refreshBtn = document.getElementById('refreshBtn');
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async function() {
            this.classList.add('spinning');
            
            try {
                // Recargar página actual
                await changePage(currentPageName);
            } catch (error) {
                console.error('Error refreshing:', error);
            } finally {
                setTimeout(() => {
                    this.classList.remove('spinning');
                }, 500);
            }
        });
    }
}

// Configurar toggle del sidebar
function setupSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    // Crear botón de toggle (para móviles)
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'sidebar-toggle';
    toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
    });
    
    document.querySelector('.header').prepend(toggleBtn);
}

// Mostrar loading
function showLoading() {
    const content = document.getElementById('pageContent');
    if (content) {
        content.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p>Cargando...</p>
            </div>
        `;
    }
}

// Mostrar error
function showError(message) {
    const content = document.getElementById('pageContent');
    if (content) {
        content.innerHTML = `
            <div class="error-container">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error</h3>
                <p>${message}</p>
                <button onclick="changePage(currentPageName)" class="btn btn-primary">
                    Reintentar
                </button>
            </div>
        `;
    }
}

// Mostrar mensaje de éxito
function showSuccess(message) {
    // Crear toast de éxito
    const toast = document.createElement('div');
    toast.className = 'toast toast-success';
    toast.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Mostrar con animación
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Ocultar después de 3 segundos
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Cerrar modales al hacer clic fuera
window.addEventListener('click', function(event) {
    const editModal = document.getElementById('editModal');
    const deleteModal = document.getElementById('deleteModal');
    
    if (event.target === editModal) {
        closeEditModal();
    }
    
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
});

// Manejar tecla ESC para cerrar modales
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeEditModal();
        closeDeleteModal();
    }
});

// Exportar funciones globales
window.changePage = changePage;
window.showLoading = showLoading;
window.showError = showError;
window.showSuccess = showSuccess;
