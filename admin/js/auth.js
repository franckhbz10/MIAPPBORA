// ==========================================
// AUTENTICACIÓN
// ==========================================

// Verificar si el usuario es administrador (basado en email)
function checkAuth() {
    const token = localStorage.getItem('admin_token');
    const user = localStorage.getItem('admin_user');
    
    if (!token || !user) {
        // Redirigir a login si no está autenticado
        window.location.href = 'login.html';
        return false;
    }
    
    try {
        const userData = JSON.parse(user);
        
        // Verificar que sea el email de administrador
        if (userData.email !== ADMIN_EMAIL) {
            alert('No tienes permisos de administrador');
            logout();
            return false;
        }
        
        // Mostrar nombre del admin
        const adminNameEl = document.getElementById('adminName');
        if (adminNameEl) {
            adminNameEl.textContent = userData.username || 'Admin';
        }
        
        return true;
    } catch (error) {
        console.error('Error parsing user data:', error);
        logout();
        return false;
    }
}

// Cerrar sesión
function logout() {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    window.location.href = 'login.html';
}

// Event listener para el botón de logout
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});
