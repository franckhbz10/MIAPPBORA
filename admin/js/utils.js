// ==========================================
// UTILIDADES - Funciones helper
// ==========================================

/**
 * Formatear número con separadores de miles
 */
function formatNumber(num) {
    return new Intl.NumberFormat('es-PE').format(num);
}

/**
 * Formatear fecha relativa (hace X tiempo)
 */
function formatRelativeDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'Hace un momento';
    if (diffMin < 60) return `Hace ${diffMin} min`;
    if (diffHour < 24) return `Hace ${diffHour}h`;
    if (diffDay === 1) return 'Ayer';
    if (diffDay < 7) return `Hace ${diffDay} días`;
    if (diffDay < 30) return `Hace ${Math.floor(diffDay / 7)} semanas`;
    if (diffDay < 365) return `Hace ${Math.floor(diffDay / 30)} meses`;
    return `Hace ${Math.floor(diffDay / 365)} años`;
}

/**
 * Formatear fecha completa
 */
function formatFullDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-PE', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Validar email
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Copiar al portapapeles
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showSuccess('Copiado al portapapeles');
        return true;
    } catch (err) {
        console.error('Error copying to clipboard:', err);
        showError('Error al copiar');
        return false;
    }
}

/**
 * Descargar datos como JSON
 */
function downloadJSON(data, filename = 'data.json') {
    const dataStr = JSON.stringify(data, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

/**
 * Descargar datos como CSV
 */
function downloadCSV(data, filename = 'data.csv') {
    if (!data || !data.length) return;
    
    // Obtener headers
    const headers = Object.keys(data[0]);
    
    // Crear filas CSV
    const csvRows = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header];
                // Escapar comillas y comas
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            }).join(',')
        )
    ];
    
    const csvStr = csvRows.join('\n');
    const blob = new Blob([csvStr], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

/**
 * Debounce function
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Truncar texto
 */
function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Obtener iniciales
 */
function getInitials(name) {
    if (!name) return '?';
    return name
        .split(' ')
        .map(word => word.charAt(0).toUpperCase())
        .slice(0, 2)
        .join('');
}

/**
 * Generar color aleatorio
 */
function randomColor() {
    const colors = [
        '#10b981', '#3b82f6', '#f59e0b', 
        '#ef4444', '#06b6d4', '#8b5cf6',
        '#ec4899', '#14b8a6'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

/**
 * Calcular porcentaje
 */
function calculatePercentage(value, total) {
    if (!total || total === 0) return 0;
    return ((value / total) * 100).toFixed(1);
}

/**
 * Confirmar acción
 */
function confirm(message) {
    return window.confirm(message);
}

/**
 * Scroll suave a elemento
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
}

/**
 * Detectar dispositivo móvil
 */
function isMobile() {
    return window.innerWidth <= 768;
}

/**
 * Parsear query params de URL
 */
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    for (const [key, value] of params) {
        result[key] = value;
    }
    return result;
}

/**
 * Actualizar query params en URL
 */
function updateQueryParams(params) {
    const url = new URL(window.location);
    Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === undefined) {
            url.searchParams.delete(key);
        } else {
            url.searchParams.set(key, params[key]);
        }
    });
    window.history.pushState({}, '', url);
}

// Exportar funciones
window.Utils = {
    formatNumber,
    formatRelativeDate,
    formatFullDate,
    isValidEmail,
    copyToClipboard,
    downloadJSON,
    downloadCSV,
    debounce,
    truncateText,
    getInitials,
    randomColor,
    calculatePercentage,
    confirm,
    scrollToElement,
    isMobile,
    getQueryParams,
    updateQueryParams
};
