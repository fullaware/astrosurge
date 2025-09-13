// Dashboard functionality for AstroSurge

// Tab switching
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    initTabs();
    
    // Load initial data
    loadCompanyStats();
    loadMissions();
    loadShips();
    loadAsteroids();
    
    // Set up form handlers
    setupFormHandlers();
});

function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetTab) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// Company statistics
async function loadCompanyStats() {
    try {
        const response = await fetch('/api/company/stats');
        if (!response.ok) {
            throw new Error('Failed to load company stats');
        }
        const stats = await response.json();
        
        document.getElementById('totalMissions').textContent = stats.totalMissions || 0;
        document.getElementById('activeMissions').textContent = stats.activeMissions || 0;
        document.getElementById('completedMissions').textContent = stats.completedMissions || 0;
        document.getElementById('totalShips').textContent = stats.totalShips || 0;
        document.getElementById('totalRevenue').textContent = formatCurrency(stats.totalRevenue || 0);
        document.getElementById('totalCosts').textContent = formatCurrency(stats.totalCosts || 0);
        document.getElementById('netProfit').textContent = formatCurrency(stats.netProfit || 0);
        
        // Update net profit color
        const netProfitElement = document.getElementById('netProfit');
        if (stats.netProfit >= 0) {
            netProfitElement.className = 'financial-value positive';
        } else {
            netProfitElement.className = 'financial-value negative';
        }
    } catch (error) {
        console.error('Error loading company stats:', error);
        alert('Failed to load company statistics. Please try again later.');
    }
}

// Missions
async function loadMissions() {
    try {
        const response = await fetch('/api/missions');
        if (!response.ok) {
            throw new Error('Failed to load missions');
        }
        const missions = await response.json();
        
        const missionsGrid = document.getElementById('missionsGrid');
        missionsGrid.innerHTML = '';
        
        if (missions.length === 0) {
            missionsGrid.innerHTML = '<p class="no-data">No missions yet. Create your first mission!</p>';
            return;
        }
        
        missions.forEach(mission => {
            const missionCard = createMissionCard(mission);
            missionsGrid.appendChild(missionCard);
        });
    } catch (error) {
        console.error('Error loading missions:', error);
        alert('Failed to load missions. Please try again later.');
    }
}

function createMissionCard(mission) {
    const card = document.createElement('div');
    card.className = 'mission-card';
    
    const phaseColor = getPhaseColor(mission.current_phase);
    const cargoWeight = calculateCargoWeight(mission.cargo);
    
    card.innerHTML = `
        <div class="card-header">
            <h3>${mission.name}</h3>
            <span class="phase-badge ${phaseColor}">${mission.current_phase}</span>
        </div>
        <div class="card-content">
            <div class="info-row">
                <span class="label">Asteroid:</span>
                <span class="value">${mission.asteroid_name}</span>
            </div>
            <div class="info-row">
                <span class="label">Ship:</span>
                <span class="value">${mission.ship_name}</span>
            </div>
            <div class="info-row">
                <span class="label">Day:</span>
                <span class="value">${mission.current_day}</span>
            </div>
            <div class="info-row">
                <span class="label">Costs:</span>
                <span class="value cost">${formatCurrency(mission.costs?.total || 0)}</span>
            </div>
            <div class="info-row">
                <span class="label">Cargo Weight:</span>
                <span class="value">${cargoWeight.toFixed(1)} kg</span>
            </div>
            ${mission.final_results ? `
                <div class="info-row">
                    <span class="label">Cargo Value:</span>
                    <span class="value revenue">${formatCurrency(mission.final_results.cargo_value || 0)}</span>
                </div>
                <div class="info-row">
                    <span class="label">Net Profit:</span>
                    <span class="value ${mission.final_results.net_profit >= 0 ? 'revenue' : 'cost'}">${formatCurrency(mission.final_results.net_profit || 0)}</span>
                </div>
            ` : ''}
        </div>
    `
    
    return card;
}

// Ships
async function loadShips() {
    try {
        const response = await fetch('/api/ships');
        if (!response.ok) {
            throw new Error('Failed to load ships');
        }
        const ships = await response.json();
        
        const shipsGrid = document.getElementById('shipsGrid');
        shipsGrid.innerHTML = '';
        
        if (ships.length === 0) {
            shipsGrid.innerHTML = '<p class="no-data">No ships yet. Purchase your first ship!</p>';
            return;
        }
        
        ships.forEach(ship => {
            const shipCard = createShipCard(ship);
            shipsGrid.appendChild(shipCard);
        });
    } catch (error) {
        console.error('Error loading ships:', error);
        alert('Failed to load ships. Please try again later.');
    }
}

function createShipCard(ship) {
    const card = document.createElement('div');
    card.className = 'ship-card';
    
    const repairCost = calculateRepairCost(ship.hull_damage);
    
    card.innerHTML = `
        <div class="card-header">
            <h3>${ship.name}</h3>
            <div class="ship-status">
                ${ship.veteran_status ? '<span class="veteran-badge" title="Veteran Ship - 15% Event Resistance">⭐</span>' : ''}
                <span class="status-badge ${ship.status === 'available' ? 'available' : 'in-use'}">${ship.status}</span>
            </div>
        </div>
        <div class="card-content">
            <div class="info-row">
                <span class="label">Missions Completed:</span>
                <span class="value">${ship.missions_completed}</span>
            </div>
            <div class="info-row">
                <span class="label">Distance Traveled:</span>
                <span class="value">${ship.total_distance_traveled} days</span>
            </div>
            <div class="info-row">
                <span class="label">Hull Damage:</span>
                <span class="value damage">${ship.hull_damage}</span>
            </div>
            <div class="info-row">
                <span class="label">Repair Cost:</span>
                <span class="value cost">${formatCurrency(repairCost)}</span>
            </div>
            <div class="info-row">
                <span class="label">Veteran Bonus:</span>
                <span class="value bonus">+${(ship.veteran_bonus * 100)}%</span>
            </div>
        </div>
        <div class="card-actions">
            <button class="btn ${ship.veteran_status ? 'btn-warning' : 'btn-secondary'}" 
                    onclick="toggleVeteranStatus('${ship.id}', ${ship.veteran_status})">
                ${ship.veteran_status ? '⭐ Veteran Ship' : 'Make Veteran'}
            </button>
        </div>
    `
    
    return card;
}

// Asteroids
async function loadAsteroids() {
    try {
        const response = await fetch('/api/asteroids');
        if (!response.ok) {
            throw new Error('Failed to load asteroids');
        }
        const asteroids = await response.json();
        
        const asteroidSelect = document.getElementById('asteroidSelect');
        asteroidSelect.innerHTML = '<option value="">Select Asteroid</option>';
        
        asteroids.forEach(asteroid => {
            const option = document.createElement('option');
            option.value = asteroid.id;
            option.textContent = `${asteroid.name} (${asteroid.distance} days)`;
            asteroidSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading asteroids:', error);
        alert('Failed to load asteroid data. Please try again later.');
    }
}

// Form handlers
function setupFormHandlers() {
    // Create mission form
    document.getElementById('createMissionForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('missionName').value,
            asteroid_id: document.getElementById('asteroidSelect').value,
            ship_id: document.getElementById('shipSelect').value
        };
        
        try {
            const response = await fetch('/api/missions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                hideCreateMissionModal();
                loadMissions();
                loadCompanyStats();
            } else {
                console.error('Failed to create mission');
                alert('Failed to create mission. Please try again.');
            }
        } catch (error) {
            console.error('Error creating mission:', error);
            alert('Failed to create mission. Please try again later.');
        }
    });
    
    // Create ship form
    document.getElementById('createShipForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('shipName').value
        };
        
        try {
            const response = await fetch('/api/ships', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                hideCreateShipModal();
                loadShips();
                loadCompanyStats();
            } else {
                console.error('Failed to create ship');
                alert('Failed to create ship. Please try again.');
            }
        } catch (error) {
            console.error('Error creating ship:', error);
            alert('Failed to create ship. Please try again later.');
        }
    });
}

// Modal functions
function showCreateMissionModal() {
    document.getElementById('createMissionModal').classList.add('active');
    loadAsteroids();
    loadShips();
}

function hideCreateMissionModal() {
    document.getElementById('createMissionModal').classList.remove('active');
    document.getElementById('createMissionForm').reset();
}

function showCreateShipModal() {
    document.getElementById('createShipModal').classList.add('active');
}

function hideCreateShipModal() {
    document.getElementById('createShipModal').classList.remove('active');
    document.getElementById('createShipForm').reset();
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
}

function getPhaseColor(phase) {
    switch (phase) {
        case 'planning': return 'blue';
        case 'launched': return 'yellow';
        case 'traveling': return 'orange';
        case 'mining': return 'purple';
        case 'returning': return 'indigo';
        case 'completed': return 'green';
        default: return 'gray';
    }
}

function calculateCargoWeight(cargo) {
    return Object.values(cargo || {}).reduce((total, amount) => total + (amount || 0), 0);
}

function calculateRepairCost(hullDamage) {
    const repairCostPerDamage = 1000000; // $1M per damage point
    return Math.min(hullDamage * repairCostPerDamage, 25000000); // Max $25M
}

async function toggleVeteranStatus(shipId, currentStatus) {
    try {
        const response = await fetch(`/api/ships/${shipId}/veteran`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ veteran_status: !currentStatus })
        });
        
        if (response.ok) {
            loadShips();
        } else {
            console.error('Failed to update veteran status');
            alert('Failed to update ship status. Please try again later.');
        }
    } catch (error) {
        console.error('Error updating veteran status:', error);
        alert('Failed to update ship status. Please try again later.');
    }
}

// Close modals when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});
