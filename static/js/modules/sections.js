// Load fleet data
async function loadFleetData() {
    try {
        const response = await fetch('/api/fleet');
        const fleetData = await response.json();
        
        // Update metrics
        document.getElementById('fleet-total').textContent = fleetData.total_ships || 0;
        document.getElementById('fleet-available').textContent = fleetData.status_counts?.docked || 0;
        document.getElementById('fleet-in-mission').textContent = fleetData.status_counts?.active || 0;
        document.getElementById('fleet-maintenance').textContent = fleetData.status_counts?.maintenance || 0;
        
        // Render ships
        const container = document.getElementById('fleet-ships-container');
        container.innerHTML = '';
        
        if (fleetData.ships && fleetData.ships.length > 0) {
            fleetData.ships.forEach(ship => {
                const card = createFleetShipCard(ship);
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No ships in fleet yet.</p>';
        }
    } catch (error) {
        console.error('Error loading fleet data:', error);
    }
}

// Create fleet ship card
function createFleetShipCard(ship) {
    const card = document.createElement('div');
    card.className = 'mission-card';
    const repairCost = Math.min((ship.hull_damage || 0) * 1000000, 25000000);
    card.innerHTML = `
        <div class="mission-header">
            <div class="mission-name">${ship.name || 'Unnamed Ship'}</div>
            <div class="mission-status ${ship.status === 'available' ? 'status-active' : 'status-planning'}">${ship.status || 'unknown'}</div>
        </div>
        <div class="mission-details">
            <div class="detail-item">
                <div class="detail-label">Capacity</div>
                <div class="detail-value">${(ship.capacity || 0).toLocaleString()} kg</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Mining Power</div>
                <div class="detail-value">${ship.mining_power || 0}/100</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Hull</div>
                <div class="detail-value">${ship.hull || 0}/100</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Hull Damage</div>
                <div class="detail-value">${ship.hull_damage || 0}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Repair Cost</div>
                <div class="detail-value">${formatCurrency(repairCost)}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Veteran</div>
                <div class="detail-value">${ship.veteran_status ? '⭐ Yes' : 'No'}</div>
            </div>
        </div>
    `;
    return card;
}

function showCreateShipForm() {
    alert('Create Ship form will be implemented');
}

// Load asteroid browser
async function loadAsteroidBrowser() {
    try {
        const response = await fetch('/api/asteroids?limit=20');
        const data = await response.json();
        const container = document.getElementById('asteroids-browser-container');
        container.innerHTML = '';
        
        if (data.asteroids && data.asteroids.length > 0) {
            data.asteroids.forEach(asteroid => {
                const card = createAsteroidBrowserCard(asteroid);
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No asteroids found.</p>';
        }
        
        // Setup search
        document.getElementById('asteroid-search').addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const cards = container.querySelectorAll('.asteroid-card');
            cards.forEach(card => {
                const name = card.querySelector('.asteroid-name').textContent.toLowerCase();
                card.style.display = name.includes(searchTerm) ? 'block' : 'none';
            });
        });
    } catch (error) {
        console.error('Error loading asteroids:', error);
    }
}

// Create asteroid browser card
function createAsteroidBrowserCard(asteroid) {
    const card = document.createElement('div');
    card.className = 'asteroid-card';
    const moid = asteroid.moid || 1.0;
    const travelDays = Math.ceil((moid * 149597870.7) / (72537 * 24));
    card.innerHTML = `
        <div class="asteroid-name">${asteroid.name || asteroid.full_name || 'Unknown'}</div>
        <div class="asteroid-details">
            <div class="detail-item">
                <div class="detail-label">MOID</div>
                <div class="detail-value">${moid.toFixed(4)} AU</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Travel Time</div>
                <div class="detail-value">~${travelDays} days</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">SPK-ID</div>
                <div class="detail-value">${asteroid.spkid || 'N/A'}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Classification</div>
                <div class="detail-value">${asteroid.neo || 'NEO'}</div>
            </div>
        </div>
    `;
    return card;
}

// Load economics data
async function loadEconomicsData() {
    try {
        const response = await fetch('/api/economics/analytics');
        const analytics = await response.json();
        
        // Update metrics
        const historical = analytics.historical_performance || {};
        const trends = analytics.profit_loss_trends || {};
        const roi = analytics.roi_analysis || {};
        
        document.getElementById('eco-total-revenue').textContent = formatCurrency(historical.total_revenue || 0);
        document.getElementById('eco-total-costs').textContent = formatCurrency(historical.total_costs || 0);
        document.getElementById('eco-net-profit').textContent = formatCurrency(historical.total_profit || 0);
        document.getElementById('eco-avg-roi').textContent = (roi.average_roi || 0).toFixed(1) + '%';
        
        // Render profit/loss chart
        renderProfitLossChart(trends.monthly_trend || []);
        
        // Render ROI distribution chart
        renderROIDistributionChart(roi.roi_distribution || {});
        
        // Render commodity history chart
        const priceHistory = analytics.commodity_price_history || {};
        renderCommodityHistoryChart(priceHistory);
        
    } catch (error) {
        console.error('Error loading economics data:', error);
    }
}

// Render profit/loss chart
function renderProfitLossChart(monthlyData) {
    const ctx = document.getElementById('profitLossChart');
    if (!ctx) return;
    
    if (charts.profitLoss) charts.profitLoss.destroy();
    
    const labels = monthlyData.map(d => d.period || '');
    charts.profitLoss = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Revenue',
                    data: monthlyData.map(d => d.revenue / 1000000),
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    fill: true
                },
                {
                    label: 'Costs',
                    data: monthlyData.map(d => d.costs / 1000000),
                    borderColor: '#ff4444',
                    backgroundColor: 'rgba(255, 68, 68, 0.1)',
                    fill: true
                },
                {
                    label: 'Profit',
                    data: monthlyData.map(d => d.profit / 1000000),
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            },
            scales: {
                x: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                y: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
            }
        }
    });
}

// Render ROI distribution chart
function renderROIDistributionChart(roiDist) {
    const ctx = document.getElementById('roiDistributionChart');
    if (!ctx) return;
    
    if (charts.roiDistribution) charts.roiDistribution.destroy();
    
    charts.roiDistribution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(roiDist),
            datasets: [{
                label: 'Missions',
                data: Object.values(roiDist),
                backgroundColor: '#00d4ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            },
            scales: {
                x: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                y: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
            }
        }
    });
}

// Render commodity history chart
function renderCommodityHistoryChart(priceHistory) {
    const ctx = document.getElementById('commodityHistoryChart');
    if (!ctx) return;
    
    if (charts.commodityHistory) charts.commodityHistory.destroy();
    
    const commodities = priceHistory.commodities || {};
    const labels = [];
    const datasets = [];
    
    Object.keys(commodities).forEach((commodity, idx) => {
        const data = commodities[commodity];
        const history = data.history || [];
        if (history.length > 0) {
            if (labels.length === 0) {
                labels.push(...history.map(h => new Date(h.date).toLocaleDateString()));
            }
            const colors = ['#00d4ff', '#00ff88', '#ffaa00', '#ff4444', '#4488ff'];
            datasets.push({
                label: commodity,
                data: history.map(h => h.price / 1000), // Convert to thousands
                borderColor: colors[idx % colors.length],
                backgroundColor: 'transparent'
            });
        }
    });
    
    charts.commodityHistory = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            },
            scales: {
                x: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                y: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
            }
        }
    });
}

// Load orbital data
async function loadOrbitalData() {
    try {
        const response = await fetch('/api/missions');
        let missions = await response.json();
        
        // Handle different response formats
        if (!Array.isArray(missions)) {
            missions = missions.missions || missions.data || [];
        }
        
        const container = document.getElementById('active-trajectories-container');
        container.innerHTML = '';
        
        if (!missions || missions.length === 0) {
            container.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No missions found</p>';
            return;
        }
        
        const activeMissions = missions.filter(m => {
            const phase = m.current_phase || m.status;
            return phase === 'traveling' || phase === 'mining' || phase === 'returning' || 
                   m.status === 'active' || phase === 'active';
        });
        
        if (activeMissions.length > 0) {
            activeMissions.forEach(mission => {
                const card = document.createElement('div');
                card.className = 'mission-card';
                const phase = mission.current_phase || mission.status || 'unknown';
                card.innerHTML = `
                    <div class="mission-header">
                        <div class="mission-name">${mission.name || 'Unnamed Mission'}</div>
                        <div class="mission-status status-active">${phase}</div>
                    </div>
                    <div class="mission-details">
                        <div class="detail-item">
                            <div class="detail-label">Asteroid</div>
                            <div class="detail-value">${mission.asteroid_name || mission.asteroid || 'Unknown'}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Travel Days</div>
                            <div class="detail-value">${mission.asteroid_moid_days || mission.travel_time_days || 'N/A'} days</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Current Day</div>
                            <div class="detail-value">${mission.current_day || 0}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Progress</div>
                            <div class="detail-value">${calculateMissionProgress(mission)}%</div>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No active missions</p>';
        }
    } catch (error) {
        console.error('Error loading orbital data:', error);
        const container = document.getElementById('active-trajectories-container');
        container.innerHTML = '<p style="color: #ff4444; text-align: center; padding: 2rem;">Error loading orbital data</p>';
    }
}

// Calculate travel time
async function calculateTravelTime() {
    const distance = parseFloat(document.getElementById('trajectory-distance').value);
    const type = document.getElementById('trajectory-type').value;
    
    if (!distance || distance <= 0) {
        alert('Please enter a valid distance');
        return;
    }
    
    try {
        const response = await fetch(`/api/orbital/travel-time?moid_au=${distance}&mission_type=${type}`);
        const result = await response.json();
        
        const resultDiv = document.getElementById('travel-time-result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <h4 style="color: #00d4ff; margin-bottom: 0.5rem;">Travel Time Calculation</h4>
            <div class="detail-item" style="margin-bottom: 0.5rem;">
                <div class="detail-label">One-way Time</div>
                <div class="detail-value">${result.one_way_time_days?.toFixed(1) || 'N/A'} days (${(result.one_way_time_days / 365).toFixed(2)} years)</div>
            </div>
            <div class="detail-item" style="margin-bottom: 0.5rem;">
                <div class="detail-label">Total Time</div>
                <div class="detail-value">${result.total_time_days?.toFixed(1) || 'N/A'} days (${(result.total_time_days / 365).toFixed(2)} years)</div>
            </div>
            <div class="detail-item" style="margin-bottom: 0.5rem;">
                <div class="detail-label">Distance</div>
                <div class="detail-value">${result.distance_km?.toLocaleString() || 'N/A'} km</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Fuel Required</div>
                <div class="detail-value">${result.fuel_requirements?.total_fuel_kg?.toFixed(0) || 'N/A'} kg</div>
            </div>
        `;
    } catch (error) {
        console.error('Error calculating travel time:', error);
        alert('Error calculating travel time');
    }
}

// Load risk data
async function loadRiskData() {
    try {
        const response = await fetch('/api/missions');
        let missions = await response.json();
        
        // Handle different response formats
        if (!Array.isArray(missions)) {
            missions = missions.missions || missions.data || [];
        }
        
        if (!missions) missions = [];
        
        // Calculate risk metrics
        let totalHullDamage = 0;
        let activeHazards = 0;
        missions.forEach(mission => {
            if (mission.events && Array.isArray(mission.events) && mission.events.length > 0) {
                activeHazards += mission.events.filter(e => 
                    e.event_type && ['solar_flare', 'micrometeorite', 'power_failure'].includes(e.event_type)
                ).length;
            }
            totalHullDamage += parseFloat(mission.hull_damage || 0);
        });
        
        document.getElementById('risk-active').textContent = activeHazards;
        const activeMissionCount = missions.filter(m => {
            const phase = m.current_phase || m.status;
            return phase === 'traveling' || phase === 'mining' || m.status === 'active';
        }).length;
        document.getElementById('risk-missions').textContent = activeMissionCount;
        document.getElementById('risk-damage').textContent = totalHullDamage;
        
        // Render risk charts
        renderRiskDistributionChart(missions);
        renderHazardTimelineChart(missions);
        renderRiskRecommendations(missions);
        
    } catch (error) {
        console.error('Error loading risk data:', error);
    }
}

// Render risk distribution chart
function renderRiskDistributionChart(missions) {
    const ctx = document.getElementById('riskDistributionChart');
    if (!ctx) return;
    
    if (charts.riskDistribution) charts.riskDistribution.destroy();
    
    const riskCounts = { low: 0, medium: 0, high: 0 };
    missions.forEach(mission => {
        // Simple risk calculation based on mission phase and events
        let risk = 'medium';
        if (mission.current_phase === 'planning') risk = 'low';
        if (mission.events && mission.events.length > 5) risk = 'high';
        riskCounts[risk] = (riskCounts[risk] || 0) + 1;
    });
    
    charts.riskDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low', 'Medium', 'High'],
            datasets: [{
                data: [riskCounts.low, riskCounts.medium, riskCounts.high],
                backgroundColor: ['#00ff88', '#ffaa00', '#ff4444']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            }
        }
    });
}

// Render hazard timeline chart
function renderHazardTimelineChart(missions) {
    const ctx = document.getElementById('hazardTimelineChart');
    if (!ctx) return;
    
    if (charts.hazardTimeline) charts.hazardTimeline.destroy();
    
    // Collect all hazard events
    const hazardEvents = [];
    missions.forEach(mission => {
        if (mission.events) {
            mission.events.forEach(event => {
                if (event.event_type && ['solar_flare', 'micrometeorite', 'power_failure'].includes(event.event_type)) {
                    hazardEvents.push({ day: event.day || 0, type: event.event_type });
                }
            });
        }
    });
    
    // Group by day
    const dayCounts = {};
    hazardEvents.forEach(event => {
        dayCounts[event.day] = (dayCounts[event.day] || 0) + 1;
    });
    
    const days = Object.keys(dayCounts).sort((a, b) => a - b).slice(-30);
    
    charts.hazardTimeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days,
            datasets: [{
                label: 'Hazard Events',
                data: days.map(d => dayCounts[d]),
                borderColor: '#ff4444',
                backgroundColor: 'rgba(255, 68, 68, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            },
            scales: {
                x: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                y: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
            }
        }
    });
}

// Render risk recommendations
function renderRiskRecommendations(missions) {
    const container = document.getElementById('risk-recommendations-container');
    container.innerHTML = '';
    
    const recommendations = [];
    
    // Check for high hull damage
    const highDamageMissions = missions.filter(m => (m.hull_damage || 0) > 10);
    if (highDamageMissions.length > 0) {
        recommendations.push({
            type: 'warning',
            title: 'High Hull Damage Detected',
            message: `${highDamageMissions.length} mission(s) have significant hull damage. Consider repairs before next mission.`
        });
    }
    
    // Check for long missions
    const longMissions = missions.filter(m => (m.current_day || 0) > 200);
    if (longMissions.length > 0) {
        recommendations.push({
            type: 'info',
            title: 'Extended Missions',
            message: `${longMissions.length} mission(s) have been active for over 200 days. Monitor closely.`
        });
    }
    
    if (recommendations.length === 0) {
        recommendations.push({
            type: 'success',
            title: 'All Systems Normal',
            message: 'No immediate risk concerns detected.'
        });
    }
    
    recommendations.forEach(rec => {
        const alert = document.createElement('div');
        alert.className = `alert alert-${rec.type}`;
        alert.innerHTML = `
            <div class="alert-title">${rec.title}</div>
            <div class="alert-message">${rec.message}</div>
        `;
        container.appendChild(alert);
    });
}

// Load market data
async function loadMarketData() {
    try {
        const response = await fetch('/api/commodity-prices');
        const prices = await response.json();
        
        // Update price displays
        if (prices.prices_per_kg) {
            document.getElementById('market-gold').textContent = formatCurrency(prices.prices_per_kg.Gold || 0) + '/kg';
            document.getElementById('market-platinum').textContent = formatCurrency(prices.prices_per_kg.Platinum || 0) + '/kg';
            document.getElementById('market-silver').textContent = formatCurrency(prices.prices_per_kg.Silver || 0) + '/kg';
            document.getElementById('market-copper').textContent = formatCurrency(prices.prices_per_kg.Copper || 0) + '/kg';
        }
        
        // Load price history
        const analyticsResponse = await fetch('/api/economics/analytics');
        const analytics = await analyticsResponse.json();
        const priceHistory = analytics.commodity_price_history || {};
        
        renderMarketTrendsChart(priceHistory);
        renderPriceHistoryTable(priceHistory);
        
    } catch (error) {
        console.error('Error loading market data:', error);
    }
}

// Render market trends chart
function renderMarketTrendsChart(priceHistory) {
    const ctx = document.getElementById('marketTrendsChart');
    if (!ctx) return;
    
    if (charts.marketTrends) charts.marketTrends.destroy();
    
    const commodities = priceHistory.commodities || {};
    const datasets = [];
    const colors = ['#00d4ff', '#00ff88', '#ffaa00', '#ff4444', '#4488ff'];
    let labels = [];
    
    Object.keys(commodities).forEach((commodity, idx) => {
        const history = commodities[commodity].history || [];
        if (history.length > 0 && labels.length === 0) {
            labels = history.map(h => new Date(h.date).toLocaleDateString());
        }
        if (history.length > 0) {
            datasets.push({
                label: commodity,
                data: history.map(h => h.price),
                borderColor: colors[idx % colors.length],
                backgroundColor: 'transparent'
            });
        }
    });
    
    if (labels.length === 0) labels = ['No data'];
    
    charts.marketTrends = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            },
            scales: {
                x: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                y: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
            }
        }
    });
}

// Render price history table
function renderPriceHistoryTable(priceHistory) {
    const container = document.getElementById('price-history-container');
    const changes = priceHistory.price_changes || {};
    
    let html = '<table style="width: 100%; border-collapse: collapse; color: white;">';
    html += '<tr style="border-bottom: 1px solid #00d4ff;"><th style="padding: 0.75rem; text-align: left; color: #00d4ff;">Commodity</th><th style="padding: 0.75rem; text-align: right; color: #00d4ff;">Current Price</th><th style="padding: 0.75rem; text-align: right; color: #00d4ff;">Change</th></tr>';
    
    Object.keys(priceHistory.commodities || {}).forEach(commodity => {
        const data = priceHistory.commodities[commodity];
        const change = changes[commodity] || {};
        const changePercent = change.change_percent || 0;
        const changeColor = changePercent >= 0 ? '#00ff88' : '#ff4444';
        
        html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
            <td style="padding: 0.75rem;">${commodity}</td>
            <td style="padding: 0.75rem; text-align: right;">${formatCurrency(data.current_price || 0)}/kg</td>
            <td style="padding: 0.75rem; text-align: right; color: ${changeColor};">${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%</td>
        </tr>`;
    });
    
    html += '</table>';
    container.innerHTML = html;
}
