// ==========================================
// CONFIGURACIÓN DE LA API
// ==========================================

// URL base del backend
const API_BASE_URL = 'http://localhost:8000'; // Cambiar en producción

// Email del administrador
const ADMIN_EMAIL = 'admin-bora@superadminbora.com';

// Endpoints
const API_ENDPOINTS = {
    // Auth
    login: '/auth/login',
    
    // Admin endpoints
    profile: '/profile/me',
    dashboardStats: '/admin/stats/dashboard',
    gameHistory: '/game/history',
    
    // Admin CRUD
    adminUsers: '/admin/users',
    adminFeedback: '/admin/feedback'
};

// Configuración de paginación
const PAGINATION = {
    itemsPerPage: 10,
    maxPages: 10
};

// Configuración de gráficos
const CHART_COLORS = {
    primary: '#10b981',
    secondary: '#3b82f6',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    success: '#10b981',
    purple: '#8b5cf6',
    pink: '#ec4899'
};
