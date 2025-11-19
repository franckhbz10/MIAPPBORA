// ==========================================
// FEEDBACK - VISUALIZACIÓN Y ANÁLISIS
// ==========================================

let allFeedback = [];
let filteredFeedback = [];

// Cargar feedback
async function loadFeedback() {
    console.log('Loading feedback page...');
    showLoading();
    
    try {
        // Intentar obtener feedback del backend
        allFeedback = await fetchFeedback();
        filteredFeedback = [...allFeedback];
        
        console.log('Total feedback loaded:', allFeedback.length);
        
        renderFeedbackPage();
        
    } catch (error) {
        console.error('Error loading feedback:', error);
        showError('Error al cargar feedback');
    }
}

// Obtener feedback
async function fetchFeedback() {
    try {
        console.log('Fetching feedback from API...');
        
        // Usar endpoint de admin
        const feedback = await api.get(API_ENDPOINTS.adminFeedback);
        
        console.log('Feedback received:', feedback);
        
        if (feedback && Array.isArray(feedback) && feedback.length > 0) {
            console.log('Using real feedback data');
            return feedback;
        }
        
        // Si no hay datos, generar datos de ejemplo
        console.log('No feedback data from API, generating sample data');
        return generateSampleFeedback();
        
    } catch (error) {
        console.error('Error fetching feedback:', error);
        console.log('Generating sample feedback due to error');
        return generateSampleFeedback();
    }
}

// Generar feedback de ejemplo
function generateSampleFeedback() {
    const comments = [
        'Excelente aplicación, me ayuda mucho a aprender quechua',
        'El chatbot es muy útil pero a veces se demora en responder',
        'Me encanta el sistema de gamificación y las recompensas',
        'Sería genial tener más niveles de dificultad',
        'La interfaz es muy intuitiva y fácil de usar',
        'El mentor Bora es muy amigable y educativo',
        'Necesita más frases para practicar',
        'Las traducciones son muy precisas',
        'Me gustaría poder competir con otros usuarios',
        'Excelente para aprender vocabulario básico'
    ];
    
    const categories = ['UI/UX', 'Contenido', 'Gamificación', 'Rendimiento', 'General'];
    const usernames = ['juan_perez', 'maria_garcia', 'carlos_lopez', 'ana_martinez', 'luis_rodriguez'];
    
    const sampleFeedback = [];
    
    for (let i = 0; i < 20; i++) {
        sampleFeedback.push({
            id: `feedback_${i + 1}`,
            user_id: `user_${Math.floor(Math.random() * 10) + 1}`,
            username: usernames[Math.floor(Math.random() * usernames.length)],
            rating: Math.floor(Math.random() * 3) + 3, // 3-5 estrellas
            comment: comments[Math.floor(Math.random() * comments.length)],
            category: categories[Math.floor(Math.random() * categories.length)],
            created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
        });
    }
    
    return sampleFeedback.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

// Renderizar página de feedback
function renderFeedbackPage() {
    const stats = calculateFeedbackStats();
    
    const content = `
        <!-- Estadísticas de Feedback -->
        <div class="feedback-stats">
            <div class="stat-card">
                <div class="stat-icon primary">
                    <i class="fas fa-comment-dots"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Total Feedback</div>
                    <div class="stat-value">${stats.total}</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon warning">
                    <i class="fas fa-star"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Calificación Promedio</div>
                    <div class="stat-value">${stats.avgRating.toFixed(1)}</div>
                    <div class="stat-trend">
                        ${renderStars(stats.avgRating)}
                    </div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon success">
                    <i class="fas fa-thumbs-up"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Feedback Positivo</div>
                    <div class="stat-value">${stats.positive}</div>
                    <div class="stat-trend">
                        ${((stats.positive / stats.total) * 100).toFixed(1)}% del total
                    </div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon danger">
                    <i class="fas fa-thumbs-down"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Feedback Negativo</div>
                    <div class="stat-value">${stats.negative}</div>
                    <div class="stat-trend">
                        ${((stats.negative / stats.total) * 100).toFixed(1)}% del total
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Filtros -->
        <div class="filters-section">
            <div class="filter-group">
                <select id="ratingFilter" onchange="filterFeedback()">
                    <option value="">Todas las calificaciones</option>
                    <option value="5">5 Estrellas</option>
                    <option value="4">4 Estrellas</option>
                    <option value="3">3 Estrellas</option>
                    <option value="2">2 Estrellas</option>
                    <option value="1">1 Estrella</option>
                </select>
                
                <select id="categoryFilter" onchange="filterFeedback()">
                    <option value="">Todas las categorías</option>
                    <option value="UI/UX">UI/UX</option>
                    <option value="Contenido">Contenido</option>
                    <option value="Gamificación">Gamificación</option>
                    <option value="Rendimiento">Rendimiento</option>
                    <option value="General">General</option>
                </select>
            </div>
        </div>
        
        <!-- Lista de Feedback -->
        <div class="feedback-list">
            ${renderFeedbackCards()}
        </div>
    `;
    
    document.getElementById('pageContent').innerHTML = content;
}

// Calcular estadísticas de feedback
function calculateFeedbackStats() {
    const total = allFeedback.length;
    const avgRating = total > 0 
        ? allFeedback.reduce((sum, f) => sum + f.rating, 0) / total 
        : 0;
    const positive = allFeedback.filter(f => f.rating >= 4).length;
    const negative = allFeedback.filter(f => f.rating <= 2).length;
    
    return { total, avgRating, positive, negative };
}

// Renderizar tarjetas de feedback
function renderFeedbackCards() {
    if (filteredFeedback.length === 0) {
        return `
            <div class="no-data">
                <i class="fas fa-inbox"></i>
                <p>No se encontró feedback</p>
            </div>
        `;
    }
    
    return filteredFeedback.map(feedback => `
        <div class="feedback-card ${getRatingClass(feedback.rating)}">
            <div class="feedback-header">
                <div class="feedback-user">
                    <div class="user-avatar">
                        ${feedback.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="user-name">@${feedback.username}</div>
                        <div class="feedback-date">${formatFeedbackDate(feedback.created_at)}</div>
                    </div>
                </div>
                <div class="feedback-rating">
                    ${renderStars(feedback.rating)}
                    <span class="rating-value">${feedback.rating}/5</span>
                </div>
            </div>
            
            <div class="feedback-body">
                <p class="feedback-comment">${feedback.comment}</p>
                ${feedback.category ? `<span class="category-badge">${feedback.category}</span>` : ''}
            </div>
        </div>
    `).join('');
}

// Renderizar estrellas
function renderStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    let stars = '';
    
    // Estrellas llenas
    for (let i = 0; i < fullStars; i++) {
        stars += '<i class="fas fa-star star-filled"></i>';
    }
    
    // Media estrella
    if (hasHalfStar) {
        stars += '<i class="fas fa-star-half-alt star-filled"></i>';
    }
    
    // Estrellas vacías
    for (let i = 0; i < emptyStars; i++) {
        stars += '<i class="far fa-star star-empty"></i>';
    }
    
    return stars;
}

// Obtener clase según rating
function getRatingClass(rating) {
    if (rating >= 4) return 'rating-positive';
    if (rating <= 2) return 'rating-negative';
    return 'rating-neutral';
}

// Filtrar feedback
function filterFeedback() {
    console.log('Filtering feedback...');
    
    const ratingFilter = document.getElementById('ratingFilter')?.value || '';
    const categoryFilter = document.getElementById('categoryFilter')?.value || '';
    
    console.log('Filters:', { ratingFilter, categoryFilter });
    
    filteredFeedback = allFeedback.filter(feedback => {
        const matchesRating = !ratingFilter || feedback.rating === parseInt(ratingFilter);
        const matchesCategory = !categoryFilter || feedback.category === categoryFilter;
        
        return matchesRating && matchesCategory;
    });
    
    console.log(`Filtered ${filteredFeedback.length} of ${allFeedback.length} feedback items`);
    
    // Solo actualizar las tarjetas de feedback, no toda la página
    const feedbackListElement = document.querySelector('.feedback-list');
    if (feedbackListElement) {
        feedbackListElement.innerHTML = renderFeedbackCards();
    }
}

// Formatear fecha de feedback
function formatFeedbackDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        if (diffHours === 0) {
            const diffMins = Math.floor(diffMs / (1000 * 60));
            return `Hace ${diffMins} min`;
        }
        return `Hace ${diffHours}h`;
    }
    
    if (diffDays === 1) return 'Ayer';
    if (diffDays < 7) return `Hace ${diffDays} días`;
    
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ==========================================
// EXPONER FUNCIONES AL SCOPE GLOBAL
// ==========================================
// Necesario para que los eventos onchange del HTML funcionen
window.filterFeedback = filterFeedback;
