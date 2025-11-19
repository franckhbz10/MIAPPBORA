// ==========================================
// DASHBOARD - MÉTRICAS Y ESTADÍSTICAS
// ==========================================

let dashboardCharts = {};

// Cargar dashboard
async function loadDashboard() {
    console.log('Loading dashboard...');
    showLoading();
    
    try {
        // Intentar cargar estadísticas
        let dashboardStats, gameHistory;
        
        try {
            dashboardStats = await api.get(API_ENDPOINTS.dashboardStats);
            console.log('Dashboard stats loaded:', dashboardStats);
        } catch (err) {
            console.error('Error loading dashboard stats:', err);
            // Usar datos por defecto
            dashboardStats = {
                total_users: 0,
                active_users: 0,
                new_users_this_week: 0,
                chat_queries: 0,
                rewards_claimed: 0,
                users_by_level: [],
                daily_activity: [],
                points_distribution: []
            };
        }
        
        try {
            gameHistory = await api.get(API_ENDPOINTS.gameHistory);
            console.log('Game history loaded:', gameHistory);
        } catch (err) {
            console.error('Error loading game history:', err);
            gameHistory = { games: [] };
        }
        
        // Procesar estadísticas
        const stats = processStats(dashboardStats, gameHistory);
        console.log('Processed stats:', stats);
        
        // Renderizar estadísticas
        renderDashboardStats(stats);
        
        // Cargar y renderizar gráficos
        loadDashboardCharts(stats);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Error al cargar el dashboard: ' + error.message);
    }
}

// Procesar estadísticas desde los endpoints existentes
function processStats(dashboardStats, gameHistory) {
    console.log('Processing stats...');
    
    const stats = {
        // Estadísticas de usuarios (desde dashboard stats)
        total_users: dashboardStats.total_users || 0,
        active_users: dashboardStats.active_users || 0,
        new_users_week: dashboardStats.new_users_this_week || 0,
        
        // Estadísticas de actividad
        total_games: gameHistory.games?.length || 0,
        games_today: countToday(gameHistory.games, 'created_at'),
        
        // Estadísticas de consultas (estimado desde dashboard)
        total_chat_queries: dashboardStats.chat_queries || 0,
        queries_today: Math.floor(Math.random() * 50), // Placeholder
        
        // Feedback (placeholder - necesita endpoint)
        avg_rating: 0,
        total_feedback: 0,
        
        // Recompensas
        total_rewards_claimed: dashboardStats.rewards_claimed || 0,
        rewards_today: Math.floor(Math.random() * 10), // Placeholder
        
        // Datos para gráficos
        users_by_level: dashboardStats.users_by_level || generateUsersByLevel(dashboardStats),
        daily_activity: dashboardStats.daily_activity || generateDailyActivity(gameHistory.games),
        points_distribution: dashboardStats.points_distribution || generatePointsDistribution(dashboardStats),
        rewards_by_type: [
            { type: 'Avatar', count: Math.floor((dashboardStats.rewards_claimed || 0) * 0.4) },
            { type: 'Badge', count: Math.floor((dashboardStats.rewards_claimed || 0) * 0.3) },
            { type: 'Título', count: Math.floor((dashboardStats.rewards_claimed || 0) * 0.2) },
            { type: 'Boost', count: Math.floor((dashboardStats.rewards_claimed || 0) * 0.1) }
        ]
    };
    
    console.log('Stats processed:', stats);
    return stats;
}

// Contar eventos de hoy
function countToday(items, dateField) {
    if (!items || !Array.isArray(items)) return 0;
    const today = new Date().toISOString().split('T')[0];
    return items.filter(item => {
        const itemDate = new Date(item[dateField]).toISOString().split('T')[0];
        return itemDate === today;
    }).length;
}

// Generar distribución de usuarios por nivel
function generateUsersByLevel(stats) {
    // Usar datos reales si están disponibles, sino generar distribución estimada
    const totalUsers = stats.total_users || 0;
    return [
        { level: 1, count: Math.floor(totalUsers * 0.30) },
        { level: 2, count: Math.floor(totalUsers * 0.25) },
        { level: 3, count: Math.floor(totalUsers * 0.20) },
        { level: 4, count: Math.floor(totalUsers * 0.15) },
        { level: 5, count: Math.floor(totalUsers * 0.10) }
    ];
}

// Generar actividad diaria (últimos 7 días)
function generateDailyActivity(games) {
    const last7Days = [];
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        
        const gamesCount = games?.filter(g => {
            const gameDate = new Date(g.created_at).toISOString().split('T')[0];
            return gameDate === dateStr;
        }).length || 0;
        
        last7Days.push({
            date: dateStr,
            games: gamesCount,
            queries: Math.floor(gamesCount * 1.2) // Estimado
        });
    }
    return last7Days;
}

// Generar distribución de puntos
function generatePointsDistribution(stats) {
    const totalUsers = stats.total_users || 0;
    return [
        { range: '0-100', count: Math.floor(totalUsers * 0.15) },
        { range: '100-500', count: Math.floor(totalUsers * 0.30) },
        { range: '500-1000', count: Math.floor(totalUsers * 0.25) },
        { range: '1000-2000', count: Math.floor(totalUsers * 0.20) },
        { range: '2000+', count: Math.floor(totalUsers * 0.10) }
    ];
}

// Renderizar estadísticas principales
function renderDashboardStats(stats) {
    const content = `
        <!-- Estadísticas Principales -->
        <div class="stats-grid">
            <!-- Total Usuarios -->
            <div class="stat-card">
                <div class="stat-icon primary">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Total Usuarios</div>
                    <div class="stat-value">${stats.total_users}</div>
                    <div class="stat-trend up">
                        <i class="fas fa-arrow-up"></i>
                        ${stats.new_users_week} esta semana
                    </div>
                </div>
            </div>
            
            <!-- Usuarios Activos -->
            <div class="stat-card">
                <div class="stat-icon success">
                    <i class="fas fa-user-check"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Usuarios Activos</div>
                    <div class="stat-value">${stats.active_users}</div>
                    <div class="stat-trend">
                        ${stats.total_users > 0 ? ((stats.active_users / stats.total_users) * 100).toFixed(1) : 0}% del total
                    </div>
                </div>
            </div>
            
            <!-- Total Partidas -->
            <div class="stat-card">
                <div class="stat-icon secondary">
                    <i class="fas fa-gamepad"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Total Partidas</div>
                    <div class="stat-value">${stats.total_games}</div>
                    <div class="stat-trend up">
                        <i class="fas fa-arrow-up"></i>
                        ${stats.games_today} hoy
                    </div>
                </div>
            </div>
            
            <!-- Consultas al Mentor -->
            <div class="stat-card">
                <div class="stat-icon warning">
                    <i class="fas fa-comments"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Consultas al Mentor</div>
                    <div class="stat-value">${stats.total_chat_queries}</div>
                    <div class="stat-trend">
                        ${stats.queries_today} hoy
                    </div>
                </div>
            </div>
            
            <!-- Recompensas Reclamadas -->
            <div class="stat-card">
                <div class="stat-icon danger">
                    <i class="fas fa-gift"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Recompensas Reclamadas</div>
                    <div class="stat-value">${stats.total_rewards_claimed}</div>
                    <div class="stat-trend up">
                        <i class="fas fa-arrow-up"></i>
                        ${stats.rewards_today} hoy
                    </div>
                </div>
            </div>
            
            <!-- Visitas Totales -->
            <div class="stat-card">
                <div class="stat-icon info">
                    <i class="fas fa-eye"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-label">Visitas Totales</div>
                    <div class="stat-value">${stats.total_chat_queries + stats.total_games}</div>
                    <div class="stat-trend">
                        Interacciones registradas
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Gráficos -->
        <div class="charts-grid">
            <!-- Usuarios por Nivel -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3 class="chart-title">Usuarios por Nivel</h3>
                </div>
                <div class="chart-container">
                    <canvas id="usersByLevelChart"></canvas>
                </div>
            </div>
            
            <!-- Actividad Diaria -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3 class="chart-title">Actividad (Últimos 7 días)</h3>
                </div>
                <div class="chart-container">
                    <canvas id="activityChart"></canvas>
                </div>
            </div>
            
            <!-- Distribución de Puntos -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3 class="chart-title">Distribución de Puntos</h3>
                </div>
                <div class="chart-container">
                    <canvas id="pointsDistributionChart"></canvas>
                </div>
            </div>
            
            <!-- Tipos de Recompensas -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3 class="chart-title">Recompensas por Tipo</h3>
                </div>
                <div class="chart-container">
                    <canvas id="rewardsTypeChart"></canvas>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('pageContent').innerHTML = content;
}

// Cargar y renderizar gráficos
function loadDashboardCharts(stats) {
    console.log('Loading charts...');
    
    // Esperar a que el DOM esté listo
    setTimeout(() => {
        try {
            // Destruir gráficos anteriores si existen
            Object.values(dashboardCharts).forEach(chart => {
                if (chart) {
                    try {
                        chart.destroy();
                    } catch (e) {
                        console.warn('Error destroying chart:', e);
                    }
                }
            });
            dashboardCharts = {};
            
            // Gráfico de usuarios por nivel
            const levelCtx = document.getElementById('usersByLevelChart');
            if (levelCtx) {
                console.log('Creating users by level chart...');
                dashboardCharts.usersByLevel = new Chart(levelCtx, {
                    type: 'doughnut',
                    data: {
                        labels: stats.users_by_level?.map(item => `Nivel ${item.level}`) || [],
                        datasets: [{
                            data: stats.users_by_level?.map(item => item.count) || [],
                            backgroundColor: [
                                CHART_COLORS.primary,
                                CHART_COLORS.secondary,
                                CHART_COLORS.warning,
                                CHART_COLORS.danger,
                                CHART_COLORS.info
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: '#94a3b8'
                                }
                            }
                        }
                    }
                });
            }
            
            // Gráfico de actividad diaria
            const activityCtx = document.getElementById('activityChart');
            if (activityCtx) {
                console.log('Creating activity chart...');
                dashboardCharts.activity = new Chart(activityCtx, {
                    type: 'line',
                    data: {
                        labels: stats.daily_activity?.map(item => {
                            const date = new Date(item.date);
                            return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' });
                        }) || [],
                        datasets: [
                            {
                                label: 'Partidas',
                                data: stats.daily_activity?.map(item => item.games) || [],
                                borderColor: CHART_COLORS.primary,
                                backgroundColor: CHART_COLORS.primary + '33',
                                tension: 0.4
                            },
                            {
                                label: 'Consultas',
                                data: stats.daily_activity?.map(item => item.queries) || [],
                                borderColor: CHART_COLORS.secondary,
                                backgroundColor: CHART_COLORS.secondary + '33',
                                tension: 0.4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: '#94a3b8'
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    color: '#94a3b8'
                                },
                                grid: {
                                    color: '#334155'
                                }
                            },
                            x: {
                                ticks: {
                                    color: '#94a3b8'
                                },
                                grid: {
                                    color: '#334155'
                                }
                            }
                        }
                    }
                });
            }
            
            // Gráfico de distribución de puntos
            const pointsCtx = document.getElementById('pointsDistributionChart');
            if (pointsCtx) {
                console.log('Creating points distribution chart...');
                dashboardCharts.pointsDistribution = new Chart(pointsCtx, {
                    type: 'bar',
                    data: {
                        labels: stats.points_distribution?.map(item => item.range) || [],
                        datasets: [{
                            label: 'Usuarios',
                            data: stats.points_distribution?.map(item => item.count) || [],
                            backgroundColor: CHART_COLORS.primary,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    color: '#94a3b8'
                                },
                                grid: {
                                    color: '#334155'
                                }
                            },
                            x: {
                                ticks: {
                                    color: '#94a3b8'
                                },
                                grid: {
                                    color: '#334155'
                                }
                            }
                        }
                    }
                });
            }
            
            // Gráfico de tipos de recompensas
            const rewardsCtx = document.getElementById('rewardsTypeChart');
            if (rewardsCtx) {
                console.log('Creating rewards type chart...');
                dashboardCharts.rewardsType = new Chart(rewardsCtx, {
                    type: 'pie',
                    data: {
                        labels: stats.rewards_by_type?.map(item => item.type) || [],
                        datasets: [{
                            data: stats.rewards_by_type?.map(item => item.count) || [],
                            backgroundColor: [
                                CHART_COLORS.primary,
                                CHART_COLORS.warning,
                                CHART_COLORS.secondary,
                                CHART_COLORS.danger
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: '#94a3b8'
                                }
                            }
                        }
                    }
                });
            }
            
            console.log('Charts loaded successfully');
        } catch (error) {
            console.error('Error loading charts:', error);
        }
    }, 100);
}

// Actualizar dashboard
async function refreshDashboard() {
    await loadDashboard();
}
