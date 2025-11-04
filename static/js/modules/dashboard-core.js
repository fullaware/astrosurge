// Core dashboard module - initialization and main rendering

// Dashboard data - stored on window for global access
if (!window.dashboardData) {
    window.dashboardData = null;
}

// Initialize dashboard
async function initDashboard() {
    // Load persisted notifications first
    if (typeof loadNotificationsFromStorage === 'function') {
        loadNotificationsFromStorage();
    }
    
    // Initial load with visual feedback
    if (typeof showRefreshIndicator === 'function') {
        showRefreshIndicator('refreshing');
    }
    
    const success = await loadDashboardData();
    renderDashboard();
    
    if (typeof setupCharts === 'function') {
        setupCharts();
    }
    
    if (success) {
        if (typeof showRefreshIndicator === 'function') {
            showRefreshIndicator('updated');
        }
        if (typeof updateRefreshIndicator === 'function') {
            setTimeout(() => updateRefreshIndicator(), 2000);
        }
    } else {
        if (typeof showRefreshIndicator === 'function') {
            showRefreshIndicator('error');
        }
        if (typeof updateRefreshIndicator === 'function') {
            setTimeout(() => updateRefreshIndicator(), 2000);
        }
    }
    
    // Start mission polling
    if (typeof startMissionPolling === 'function') {
        startMissionPolling();
    }
    
    if (typeof startAutoRefresh === 'function') {
        startAutoRefresh();
    }
}

// Mock data for demo purposes
function getMockData() {
    return {
        overview: {
            total_missions: 15,
            active_missions: 3,
            completed_missions: 12,
            fleet_size: 8,
            total_revenue: 1250000000,
            net_profit: 400000000,
            success_rate: 0.85
        },
        missions: {
            missions: [
                {
                    id: 'M001',
                    name: 'Ceres Mining Expedition',
                    asteroid: 'Ceres',
                    status: 'active',
                    progress: 0.65,
                    start_date: '2024-01-15',
                    estimated_completion: '2024-07-15',
                    crew_size: 12,
                    ship: 'Mining Vessel Alpha',
                    distance_au: 1.59478,
                    fuel_remaining: 0.78,
                    cargo_loaded: 0.45,
                    risk_level: 'medium',
                    estimated_revenue: 250000000,
                    current_costs: 180000000
                },
                {
                    id: 'M002',
                    name: 'Pallas Survey Mission',
                    asteroid: 'Pallas',
                    status: 'planning',
                    progress: 0.0,
                    start_date: '2024-03-01',
                    estimated_completion: '2024-09-01',
                    crew_size: 8,
                    ship: 'Explorer Beta',
                    distance_au: 1.23429,
                    fuel_remaining: 1.0,
                    cargo_loaded: 0.0,
                    risk_level: 'low',
                    estimated_revenue: 150000000,
                    current_costs: 0
                },
                {
                    id: 'M003',
                    name: 'Juno Resource Extraction',
                    asteroid: 'Juno',
                    status: 'returning',
                    progress: 0.95,
                    start_date: '2023-08-01',
                    estimated_completion: '2024-02-15',
                    crew_size: 15,
                    ship: 'Heavy Miner Gamma',
                    distance_au: 1.03429,
                    fuel_remaining: 0.15,
                    cargo_loaded: 0.92,
                    risk_level: 'low',
                    estimated_revenue: 300000000,
                    current_costs: 220000000
                }
            ]
        },
        asteroids: {
            asteroids: [
                {
                    name: 'Ceres',
                    moid_au: 1.59478,
                    size_km: 939.4,
                    composition: ['Water Ice', 'Silicates', 'Carbon'],
                    mining_difficulty: 'medium',
                    estimated_value: 5000000000,
                    travel_time_days: 359,
                    risk_level: 'medium'
                },
                {
                    name: 'Pallas',
                    moid_au: 1.23429,
                    size_km: 512,
                    composition: ['Silicates', 'Metals', 'Water Ice'],
                    mining_difficulty: 'easy',
                    estimated_value: 3000000000,
                    travel_time_days: 285,
                    risk_level: 'low'
                },
                {
                    name: 'Juno',
                    moid_au: 1.03429,
                    size_km: 267,
                    composition: ['Metals', 'Silicates', 'Rare Earths'],
                    mining_difficulty: 'hard',
                    estimated_value: 8000000000,
                    travel_time_days: 243,
                    risk_level: 'low'
                }
            ]
        },
        alerts: [
            {
                type: 'warning',
                title: 'Low Fuel Warning',
                message: 'Mining Vessel Alpha fuel below 20%'
            },
            {
                type: 'info',
                title: 'Mission Update',
                message: 'Juno mission 95% complete'
            },
            {
                type: 'success',
                title: 'Mission Completed',
                message: 'Vesta survey mission successful'
            }
        ],
        charts: {
            mission_status: {
                labels: ['Planning', 'Active', 'Returning', 'Completed'],
                data: [2, 3, 1, 12]
            },
            revenue_trend: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                data: [100, 120, 110, 140, 130, 150]
            },
            fleet_utilization: {
                labels: ['Active', 'Docked', 'Maintenance'],
                data: [3, 4, 1]
            },
            commodity_prices: {
                labels: ['Gold', 'Platinum', 'Silver', 'Copper', 'Palladium'],
                data: [2000, 950, 25, 4, 1000]
            }
        }
    };
}

// Render dashboard
function renderDashboard() {
    if (!window.dashboardData) return;

    // Update overview metrics
    const totalMissionsEl = document.getElementById('total-missions');
    const activeMissionsEl = document.getElementById('active-missions');
    const fleetSizeEl = document.getElementById('fleet-size');
    const totalRevenueEl = document.getElementById('total-revenue');
    const netProfitEl = document.getElementById('net-profit');
    const successRateEl = document.getElementById('success-rate');
    
    if (totalMissionsEl) totalMissionsEl.textContent = window.dashboardData.overview.total_missions;
    if (activeMissionsEl) activeMissionsEl.textContent = window.dashboardData.overview.active_missions;
    if (fleetSizeEl) fleetSizeEl.textContent = window.dashboardData.overview.fleet_size;
    if (totalRevenueEl && typeof formatCurrency === 'function') {
        totalRevenueEl.textContent = formatCurrency(window.dashboardData.overview.total_revenue);
    }
    if (netProfitEl && typeof formatCurrency === 'function') {
        netProfitEl.textContent = formatCurrency(window.dashboardData.overview.net_profit);
    }
    if (successRateEl) {
        successRateEl.textContent = Math.round(window.dashboardData.overview.success_rate * 100) + '%';
    }

    // Render missions (if function exists)
    if (typeof renderMissions === 'function') {
        renderMissions();
    }
    
    // Render asteroids (if function exists)
    if (typeof renderAsteroids === 'function') {
        renderAsteroids();
    }
    
    // Render alerts (if function exists)
    if (typeof renderAlerts === 'function') {
        renderAlerts();
    }
}

// Render missions (simple overview render)
function renderMissions() {
    if (!window.dashboardData || !window.dashboardData.missions) return;
    
    const container = document.getElementById('missions-container');
    if (!container) return;
    
    container.innerHTML = '';

    window.dashboardData.missions.missions.forEach(mission => {
        const missionCard = document.createElement('div');
        missionCard.className = 'mission-card';
        missionCard.innerHTML = `
            <div class="mission-header">
                <div class="mission-name">${mission.name}</div>
                <div class="mission-status status-${mission.status}">${mission.status}</div>
            </div>
            <div class="mission-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${mission.progress * 100}%"></div>
                </div>
            </div>
            <div class="mission-details">
                <div class="detail-item">
                    <div class="detail-label">Asteroid</div>
                    <div class="detail-value">${mission.asteroid}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Ship</div>
                    <div class="detail-value">${mission.ship}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Distance</div>
                    <div class="detail-value">${mission.distance_au} AU</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Fuel</div>
                    <div class="detail-value">${Math.round(mission.fuel_remaining * 100)}%</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Cargo</div>
                    <div class="detail-value">${Math.round(mission.cargo_loaded * 100)}%</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Risk</div>
                    <div class="detail-value">
                        <span class="risk-indicator risk-${mission.risk_level}">${mission.risk_level}</span>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(missionCard);
    });
}

// Render asteroids (simple overview render)
function renderAsteroids() {
    if (!window.dashboardData || !window.dashboardData.asteroids) return;
    
    const container = document.getElementById('asteroids-container');
    if (!container) return;
    
    container.innerHTML = '';

    window.dashboardData.asteroids.asteroids.forEach(asteroid => {
        const asteroidCard = document.createElement('div');
        asteroidCard.className = 'asteroid-card';
        const formattedValue = typeof formatCurrency === 'function' 
            ? formatCurrency(asteroid.estimated_value) 
            : asteroid.estimated_value;
        asteroidCard.innerHTML = `
            <div class="asteroid-name">${asteroid.name}</div>
            <div class="asteroid-details">
                <div class="detail-item">
                    <div class="detail-label">Distance</div>
                    <div class="detail-value">${asteroid.moid_au} AU</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Size</div>
                    <div class="detail-value">${asteroid.size_km} km</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Travel Time</div>
                    <div class="detail-value">${asteroid.travel_time_days} days</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Difficulty</div>
                    <div class="detail-value">${asteroid.mining_difficulty}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Value</div>
                    <div class="detail-value">${formattedValue}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Risk</div>
                    <div class="detail-value">
                        <span class="risk-indicator risk-${asteroid.risk_level}">${asteroid.risk_level}</span>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(asteroidCard);
    });
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    if (typeof initNavigation === 'function') {
        initNavigation();
    }
    // Poll active missions for updates every 8 seconds
    setInterval(() => {
        try { 
            if (typeof loadAllMissions === 'function') {
                loadAllMissions();
            }
        } catch(e) {
            console.error('Error in mission polling:', e);
        }
    }, 8000);
});

