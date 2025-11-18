// ==========================================
// USERS - GESTIÓN DE USUARIOS
// ==========================================

let allUsers = [];
let filteredUsers = [];
let currentPage = 1;
const itemsPerPage = PAGINATION.itemsPerPage;

// Cargar listado de usuarios
async function loadUsers() {
    showLoading();
    
    try {
        // Usar endpoint de profile para obtener todos los usuarios
        const response = await api.get(API_ENDPOINTS.profile);
        
        // Si la respuesta es un solo usuario, necesitamos cargar todos
        // Por ahora, simularemos con datos del dashboard
        const dashboardStats = await api.get(API_ENDPOINTS.dashboardStats);
        
        // Obtener lista de usuarios (placeholder - necesita endpoint específico)
        allUsers = await fetchAllUsers();
        filteredUsers = [...allUsers];
        
        currentPage = 1;
        renderUsersTable();
        
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Error al cargar usuarios');
    }
}

// Obtener todos los usuarios (simulado)
async function fetchAllUsers() {
    try {
        // Usar endpoint de admin
        const users = await api.get(API_ENDPOINTS.adminUsers);
        
        if (users && Array.isArray(users)) {
            return users;
        }
        
        // Si no existe el endpoint, generar datos de ejemplo
        return generateSampleUsers();
        
    } catch (error) {
        console.error('Error fetching users:', error);
        return generateSampleUsers();
    }
}

// Generar usuarios de ejemplo
function generateSampleUsers() {
    const sampleUsers = [];
    const usernames = ['juan_perez', 'maria_garcia', 'carlos_lopez', 'ana_martinez', 'luis_rodriguez'];
    const levels = [1, 2, 3, 4, 5];
    
    for (let i = 0; i < 15; i++) {
        sampleUsers.push({
            id: `user_${i + 1}`,
            email: `user${i + 1}@example.com`,
            username: usernames[i % usernames.length] + (i > 4 ? i : ''),
            full_name: `Usuario ${i + 1}`,
            phone: `+51 ${900000000 + i}`,
            points: Math.floor(Math.random() * 2000),
            level: levels[Math.floor(Math.random() * levels.length)],
            is_active: Math.random() > 0.2,
            created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
        });
    }
    
    return sampleUsers;
}

// Renderizar tabla de usuarios
function renderUsersTable() {
    const content = `
        <!-- Filtros -->
        <div class="filters-section">
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input 
                    type="text" 
                    id="searchInput" 
                    placeholder="Buscar por nombre, email o username..."
                    onkeyup="filterUsers()"
                >
            </div>
            
            <div class="filter-group">
                <select id="statusFilter" onchange="filterUsers()">
                    <option value="">Todos los estados</option>
                    <option value="active">Activos</option>
                    <option value="inactive">Inactivos</option>
                </select>
                
                <select id="levelFilter" onchange="filterUsers()">
                    <option value="">Todos los niveles</option>
                    <option value="1">Nivel 1</option>
                    <option value="2">Nivel 2</option>
                    <option value="3">Nivel 3</option>
                    <option value="4">Nivel 4</option>
                    <option value="5">Nivel 5</option>
                </select>
            </div>
        </div>
        
        <!-- Tabla de usuarios -->
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Usuario</th>
                        <th>Email</th>
                        <th>Teléfono</th>
                        <th>Puntos</th>
                        <th>Nivel</th>
                        <th>Estado</th>
                        <th>Fecha de Registro</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    ${renderUsersRows()}
                </tbody>
            </table>
        </div>
        
        <!-- Paginación -->
        <div class="pagination">
            ${renderPagination()}
        </div>
    `;
    
    document.getElementById('pageContent').innerHTML = content;
    
    // Adjuntar event listeners después de renderizar el HTML
    attachUserActionListeners();
}

// Renderizar filas de usuarios
function renderUsersRows() {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageUsers = filteredUsers.slice(startIndex, endIndex);
    
    if (pageUsers.length === 0) {
        return `
            <tr>
                <td colspan="8" class="no-data">
                    <i class="fas fa-inbox"></i>
                    <p>No se encontraron usuarios</p>
                </td>
            </tr>
        `;
    }
    
    return pageUsers.map(user => `
        <tr>
            <td>
                <div class="user-info">
                    <div class="user-avatar">
                        ${user.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="user-name">${user.full_name || user.username}</div>
                        <div class="user-username">@${user.username}</div>
                    </div>
                </div>
            </td>
            <td>${user.email}</td>
            <td>${user.phone || 'N/A'}</td>
            <td>
                <span class="badge badge-points">${user.total_points || user.points || 0} pts</span>
            </td>
            <td>
                <span class="badge badge-level">Nivel ${user.level}</span>
            </td>
            <td>
                <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                    ${user.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <div class="action-buttons">
                    <button 
                        class="btn-icon btn-edit" 
                        data-user-id="${user.id}"
                        title="Editar"
                    >
                        <i class="fas fa-edit"></i>
                    </button>
                    <button 
                        class="btn-icon btn-delete" 
                        data-user-id="${user.id}"
                        title="Eliminar"
                    >
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Renderizar paginación
function renderPagination() {
    const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
    
    if (totalPages <= 1) return '';
    
    let pages = '';
    for (let i = 1; i <= totalPages; i++) {
        pages += `
            <button 
                class="page-btn ${i === currentPage ? 'active' : ''}"
                onclick="goToPage(${i})"
            >
                ${i}
            </button>
        `;
    }
    
    return `
        <button 
            class="page-btn" 
            onclick="goToPage(${currentPage - 1})"
            ${currentPage === 1 ? 'disabled' : ''}
        >
            <i class="fas fa-chevron-left"></i>
        </button>
        ${pages}
        <button 
            class="page-btn" 
            onclick="goToPage(${currentPage + 1})"
            ${currentPage === totalPages ? 'disabled' : ''}
        >
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
}

// Filtrar usuarios
function filterUsers() {
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const levelFilter = document.getElementById('levelFilter')?.value || '';
    
    filteredUsers = allUsers.filter(user => {
        // Filtro de búsqueda
        const matchesSearch = 
            user.username.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm) ||
            (user.full_name && user.full_name.toLowerCase().includes(searchTerm));
        
        // Filtro de estado
        const matchesStatus = 
            !statusFilter || 
            (statusFilter === 'active' && user.is_active) ||
            (statusFilter === 'inactive' && !user.is_active);
        
        // Filtro de nivel
        const matchesLevel = !levelFilter || user.level === parseInt(levelFilter);
        
        return matchesSearch && matchesStatus && matchesLevel;
    });
    
    currentPage = 1;
    renderUsersTable();
}

// Ir a página
function goToPage(page) {
    const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        renderUsersTable();
    }
}

// Adjuntar event listeners a los botones de acción
function attachUserActionListeners() {
    console.log('Attaching user action listeners...');
    
    // Event listeners para botones de editar
    const editButtons = document.querySelectorAll('.btn-edit');
    console.log(`Found ${editButtons.length} edit buttons`);
    
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = parseInt(this.getAttribute('data-user-id'));
            console.log('Edit button clicked for user ID:', userId);
            openEditModal(userId);
        });
    });
    
    // Event listeners para botones de eliminar
    const deleteButtons = document.querySelectorAll('.btn-delete');
    console.log(`Found ${deleteButtons.length} delete buttons`);
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = parseInt(this.getAttribute('data-user-id'));
            console.log('Delete button clicked for user ID:', userId);
            openDeleteModal(userId);
        });
    });
}

// Abrir modal de edición
function openEditModal(userId) {
    console.log('Opening edit modal for user ID:', userId);
    const user = allUsers.find(u => u.id === userId);
    
    if (!user) {
        console.error('User not found:', userId);
        showError('Usuario no encontrado');
        return;
    }
    
    console.log('User found:', user);
    
    // Rellenar formulario
    document.getElementById('editUserId').value = user.id;
    document.getElementById('editEmail').value = user.email;
    document.getElementById('editUsername').value = user.username;
    document.getElementById('editFullName').value = user.full_name || '';
    document.getElementById('editPhone').value = user.phone || '';
    document.getElementById('editPoints').value = user.total_points || user.points || 0;
    document.getElementById('editLevel').value = user.level;
    document.getElementById('editIsActive').checked = user.is_active;
    
    // Mostrar modal
    document.getElementById('editModal').style.display = 'flex';
}

// Cerrar modal de edición
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

// Guardar cambios de usuario
async function saveUserChanges() {
    const userId = document.getElementById('editUserId').value;
    const userData = {
        email: document.getElementById('editEmail').value,
        username: document.getElementById('editUsername').value,
        full_name: document.getElementById('editFullName').value,
        phone: document.getElementById('editPhone').value,
        points: parseInt(document.getElementById('editPoints').value),
        level: parseInt(document.getElementById('editLevel').value),
        is_active: document.getElementById('editIsActive').checked
    };
    
    try {
        showLoading();
        
        // Actualizar en el backend
        await api.put(`${API_ENDPOINTS.adminUsers}/${userId}`, userData);
        
        closeEditModal();
        await loadUsers();
        showSuccess('Usuario actualizado correctamente');
        
    } catch (error) {
        console.error('Error saving user:', error);
        showError('Error al guardar cambios');
    }
}

// Abrir modal de eliminación
function openDeleteModal(userId) {
    console.log('Opening delete modal for user ID:', userId);
    const user = allUsers.find(u => u.id === userId);
    
    if (!user) {
        console.error('User not found:', userId);
        showError('Usuario no encontrado');
        return;
    }
    
    console.log('User found:', user);
    
    document.getElementById('deleteUserId').value = user.id;
    document.getElementById('deleteUserName').textContent = user.username;
    document.getElementById('deleteModal').style.display = 'flex';
}

// Cerrar modal de eliminación
function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

// Confirmar eliminación de usuario
async function confirmDeleteUser() {
    const userId = document.getElementById('deleteUserId').value;
    
    try {
        showLoading();
        
        // Eliminar en el backend
        await api.delete(`${API_ENDPOINTS.adminUsers}/${userId}`);
        
        closeDeleteModal();
        await loadUsers();
        showSuccess('Usuario eliminado correctamente');
        
    } catch (error) {
        console.error('Error deleting user:', error);
        showError('Error al eliminar usuario');
    }
}

// Formatear fecha
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ==========================================
// EXPONER FUNCIONES AL SCOPE GLOBAL
// ==========================================
// Necesario para que los eventos onclick del HTML funcionen
// Las funciones openEditModal y openDeleteModal ahora usan event listeners
window.closeEditModal = closeEditModal;
window.saveUserChanges = saveUserChanges;
window.closeDeleteModal = closeDeleteModal;
window.confirmDeleteUser = confirmDeleteUser;
window.filterUsers = filterUsers;
window.goToPage = goToPage;
