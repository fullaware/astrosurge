// Mining Operations Functions
let cargoAccumulationChart = null;
let cargoBreakdownChart = null;

// Load mining operations data
async function loadMiningOperationsData() {
    try {
        const response = await fetch('/api/mining/operations');
        const data = await response.json();
        
        if (!data || !data.active_mining_missions) {
            console.warn('No mining data available');
            return;
        }
        
        // Update metrics
        document.getElementById('mining-active-count').textContent = data.total_active || 0;
        document.getElementById('mining-total-cargo').textContent = (data.total_cargo || 0).toLocaleString();
        
        // Calculate average daily yield
        const avgYield = data.active_mining_missions.length > 0
            ? data.active_mining_missions.reduce((sum, m) => sum + (m.daily_yield || 0), 0) / data.active_mining_missions.length
            : 0;
        document.getElementById('mining-avg-yield').textContent = avgYield.toFixed(1);
        
        // Calculate overall efficiency (average progress percentage)
        const avgEfficiency = data.active_mining_missions.length > 0
            ? data.active_mining_missions.reduce((sum, m) => sum + (m.progress_percentage || 0), 0) / data.active_mining_missions.length
            : 0;
        document.getElementById('mining-efficiency').textContent = avgEfficiency.toFixed(1) + '%';
        
        // Update active missions text
        const activeText = data.total_active === 1 ? 'mission mining' : 'missions mining';
        document.getElementById('mining-active-text').textContent = `${data.total_active} ${activeText}`;
        
        // Render mining mission cards
        renderMiningMissionCards(data.active_mining_missions);
        
        // Render charts
        renderCargoAccumulationChart(data.active_mining_missions);
        renderCargoBreakdownChart(data.active_mining_missions);
        
    } catch (error) {
        console.error('Error loading mining operations:', error);
        document.getElementById('mining-missions-container').innerHTML = 
            '<p style="color: #ff4444; text-align: center; padding: 2rem;">Error loading mining operations. Please try again later.</p>';
    }
}

// Render mining mission cards
function renderMiningMissionCards(missions) {
    const container = document.getElementById('mining-missions-container');
    container.innerHTML = '';
    
    if (missions.length === 0) {
        container.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No active mining missions</p>';
        return;
    }
    
    missions.forEach(mission => {
        const card = document.createElement('div');
        card.className = 'mission-card';
        
        const classBadge = getAsteroidClassBadge(mission.asteroid_class);
        const progressColor = getProgressColor(mission.progress_percentage);
        
        // Build cargo breakdown
        let cargoBreakdownHTML = '';
        if (mission.cargo_breakdown && Object.keys(mission.cargo_breakdown).length > 0) {
            cargoBreakdownHTML = '<div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(0,212,255,0.3);">';
            cargoBreakdownHTML += '<div style="font-size: 0.85rem; color: #888; margin-bottom: 0.25rem;">Elements Mined:</div>';
            const sortedCargo = Object.entries(mission.cargo_breakdown)
                .sort(([_, a], [__, b]) => b - a);
            
            sortedCargo.forEach(([element, weight]) => {
                const percentage = ((weight / mission.current_cargo_kg) * 100).toFixed(1);
                cargoBreakdownHTML += `<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 0.2rem;">
                    <span>${element}:</span>
                    <span>${weight.toFixed(1)} kg (${percentage}%)</span>
                </div>`;
            });
            cargoBreakdownHTML += '</div>';
        }
        
        card.innerHTML = `
        <div class="mission-header">
            <div class="mission-name">${mission.name}</div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                ${classBadge}
                <div class="mission-status status-active" title="Active">⏱️ Mining</div>
            </div>
        </div>
            <div class="mission-controls" style="display:flex; gap:0.5rem; margin: 0.25rem 0;">
                <button onclick="launchMission('${mission.mission_id || mission._id || ''}')" style="padding:0.25rem 0.5rem; background:#00d4ff; border:none; color:#000; border-radius:4px; cursor:pointer;">Launch</button>
                <button onclick="toggleMissionAutoProgress('${mission.mission_id || mission._id || ''}', this)" style="padding:0.25rem 0.5rem; background:#0b1220; border:1px solid rgba(0,212,255,0.5); color:#00d4ff; border-radius:4px; cursor:pointer;">Pause/Resume</button>
                <button onclick="advanceMissionDay('${mission.mission_id || mission._id || ''}')" style="padding:0.25rem 0.5rem; background:#0b1220; border:1px solid rgba(0,212,255,0.5); color:#00d4ff; border-radius:4px; cursor:pointer;">Advance Day</button>
                <button onclick="sellMissionCargo('${mission.mission_id || mission._id || ''}')" style="padding:0.25rem 0.5rem; background:#00ff88; border:none; color:#000; border-radius:4px; cursor:pointer;">Sell Cargo</button>
            </div>
            <div style="margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem;">
                    <span>Mining Progress:</span>
                    <span>${mission.progress_percentage.toFixed(1)}%</span>
                </div>
                <div class="progress-bar" style="height: 8px;">
                <div class="progress-fill" style="width: ${mission.progress_percentage}%; background: ${progressColor}; transition: width 0.6s ease;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888; margin-top: 0.25rem;">
                    <span>${mission.current_cargo_kg.toLocaleString()} kg</span>
                    <span>${mission.ship_capacity_kg.toLocaleString()} kg</span>
                </div>
            </div>
            <div class="mission-details">
                <div class="detail-item">
                    <div class="detail-label">Asteroid</div>
                    <div class="detail-value">${mission.asteroid_name}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Mining Days</div>
                    <div class="detail-value">${mission.mining_days}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Daily Yield</div>
                    <div class="detail-value">${mission.daily_yield.toFixed(1)} kg/day</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Remaining Capacity</div>
                    <div class="detail-value">${(mission.ship_capacity_kg - mission.current_cargo_kg).toLocaleString()} kg</div>
                </div>
            </div>
            ${cargoBreakdownHTML}
        `;
        container.appendChild(card);
    });
}

// Render cargo accumulation chart
function renderCargoAccumulationChart(missions) {
    const ctx = document.getElementById('cargoAccumulationChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (cargoAccumulationChart) {
        cargoAccumulationChart.destroy();
    }
    
    if (missions.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No mining data available</p>';
        return;
    }
    
    // Prepare data for chart
    const datasets = missions.map((mission, index) => {
        const colors = ['#00d4ff', '#00ff88', '#ff6b35', '#ffaa00', '#4488ff'];
        const color = colors[index % colors.length];
        
        // Generate data points for each day of mining
        const dataPoints = [];
        for (let day = 0; day <= mission.mining_days; day++) {
            // Approximate cargo accumulation (linear for now)
            const estimatedCargo = (mission.current_cargo_kg / mission.mining_days) * day;
            dataPoints.push({ x: day, y: estimatedCargo });
        }
        
        return {
            label: mission.name,
            data: dataPoints,
            borderColor: color,
            backgroundColor: color + '40',
            borderWidth: 2,
            fill: true,
            tension: 0.4
        };
    });
    
    cargoAccumulationChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Mining Days'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Cargo Weight (kg)'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: missions.length <= 5,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
}

// Render cargo breakdown chart
function renderCargoBreakdownChart(missions) {
    const ctx = document.getElementById('cargoBreakdownChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (cargoBreakdownChart) {
        cargoBreakdownChart.destroy();
    }
    
    if (missions.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No mining data available</p>';
        return;
    }
    
    // Aggregate cargo breakdown across all missions
    const totalCargo = {};
    missions.forEach(mission => {
        if (mission.cargo_breakdown) {
            Object.entries(mission.cargo_breakdown).forEach(([element, weight]) => {
                totalCargo[element] = (totalCargo[element] || 0) + weight;
            });
        }
    });
    
    const labels = Object.keys(totalCargo).sort((a, b) => totalCargo[b] - totalCargo[a]);
    const data = labels.map(label => totalCargo[label]);
    
    if (labels.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No cargo data available</p>';
        return;
    }
    
    // Color palette for elements
    const elementColors = {
        'Gold': '#ffd700',
        'Platinum': '#e5e4e2',
        'Silver': '#c0c0c0',
        'Copper': '#b87333',
        'Palladium': '#ffaa00',
        'Lithium': '#ff6b35',
        'Cobalt': '#0047ab'
    };
    
    const colors = labels.map(label => elementColors[label] || '#00d4ff');
    
    cargoBreakdownChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Cargo (kg)',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c + 'CC'),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Weight (kg)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Element'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                            return `${context.parsed.y.toFixed(1)} kg (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}
