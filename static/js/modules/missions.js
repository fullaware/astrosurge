// Missions module: mission list, controls, detail modal, and planning wizard

// Utility helpers (depend on utils.js if present)
function getAsteroidClassBadge(asteroidClass) {
    const classColors = {
        'C': { bg: 'rgba(0, 212, 255, 0.2)', border: '#00d4ff', label: 'C-Type' },
        'S': { bg: 'rgba(0, 255, 136, 0.2)', border: '#00ff88', label: 'S-Type' },
        'M': { bg: 'rgba(255, 170, 0, 0.2)', border: '#ffaa00', label: 'M-Type' }
    };
    const style = classColors[asteroidClass] || classColors['C'];
    return `<span style="padding: 0.2rem 0.5rem; background: ${style.bg}; border: 1px solid ${style.border}; border-radius: 4px; font-size: 0.7rem; color: ${style.border}; font-weight: bold;">${style.label}</span>`;
}

function getProgressColor(percentage) {
    const pct = parseFloat(percentage);
    if (pct < 50) return '#00ff88';
    if (pct < 80) return '#ffaa00';
    return '#ff4444';
}

// Mission list
async function loadAllMissions() {
    try {
        const response = await fetch('/api/missions');
        let missions = await response.json();
        if (!Array.isArray(missions)) {
            missions = missions.missions || missions.data || [];
        }
        const container = document.getElementById('all-missions-container');
        if (!container) return;
        container.innerHTML = '';
        if (!missions || missions.length === 0) {
            container.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No missions yet. Create your first mission!</p>';
            return;
        }
        missions.forEach(mission => container.appendChild(createMissionCard(mission)));
    } catch (error) {
        console.error('Error loading missions:', error);
        const container = document.getElementById('all-missions-container');
        if (container) container.innerHTML = '<p style="color: #ff4444; text-align: center; padding: 2rem;">Error loading missions. Please try again later.</p>';
    }
}

function createMissionCard(mission) {
    const card = document.createElement('div');
    card.className = 'mission-card';
    card.setAttribute('data-mission-id', mission._id || mission.id);
    const phase = mission.current_phase || mission.status || 'unknown';
    if (['launched', 'traveling', 'mining_setup', 'mining', 'cargo_loading', 'returning'].includes(phase)) {
        card.classList.add('mission-active');
    }
    const statusClass = mission.status === 'active' || mission.status === 'traveling' || mission.status === 'mining' ? 'status-active' : (mission.status === 'planning' ? 'status-planning' : 'status-returning');
    const isMining = phase === 'mining';
    const cargo = mission.cargo || {};
    const cargoWeight = (Object.values(cargo).reduce((s, v) => s + (parseFloat(v) || 0), 0));
    const shipCapacity = mission.ship_capacity || 50000;
    const cargoProgress = (shipCapacity ? (cargoWeight / shipCapacity * 100) : 0).toFixed(1);
    const asteroidClass = mission.asteroid_class || 'C';
    const classBadge = getAsteroidClassBadge(asteroidClass);
    let cargoBreakdownHTML = '';
    if (isMining && cargo && Object.keys(cargo).length > 0) {
        cargoBreakdownHTML = '<div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(0,212,255,0.3);">';
        cargoBreakdownHTML += '<div style="font-size: 0.85rem; color: #888; margin-bottom: 0.25rem;">Cargo Breakdown:</div>';
        Object.entries(cargo)
            .filter(([, w]) => w > 0)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 5)
            .forEach(([element, weight]) => {
                const percentage = cargoWeight ? ((weight / cargoWeight) * 100).toFixed(1) : '0.0';
                cargoBreakdownHTML += `<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 0.2rem;">
                    <span>${element}:</span>
                    <span>${Number(weight).toFixed(1)} kg (${percentage}%)</span>
                </div>`;
            });
        cargoBreakdownHTML += '</div>';
    }
    card.innerHTML = `
        <div class="mission-header">
            <div class="mission-name">${mission.name || 'Unnamed Mission'}</div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                ${classBadge}
                <div class="mission-status ${statusClass}">${phase}</div>
            </div>
        </div>
        <div class="mission-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${calculateMissionProgress(mission)}%"></div>
            </div>
        </div>
        ${isMining ? `
        <div style="margin: 0.5rem 0;">
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem;">
                <span>Mining Progress:</span>
                <span>${cargoProgress}%</span>
            </div>
            <div class="progress-bar" style="height: 6px;">
                <div class="progress-fill" style="width: ${cargoProgress}%; background: ${getProgressColor(cargoProgress)};"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888; margin-top: 0.25rem;">
                <span>${cargoWeight.toFixed(1)} kg</span>
                <span>${shipCapacity.toLocaleString()} kg</span>
            </div>
        </div>
        ` : ''}
        <div class="mission-details">
            <div class="detail-item">
                <div class="detail-label">Asteroid</div>
                <div class="detail-value">${mission.asteroid_name || 'Unknown'}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Day</div>
                <div class="detail-value">${mission.current_day || 0}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Costs</div>
                <div class="detail-value">${formatCurrency(mission.costs?.total || 0)}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Cargo</div>
                <div class="detail-value">${cargoWeight.toFixed(1)} kg</div>
            </div>
            ${mission.final_results ? `
                <div class="detail-item">
                    <div class="detail-label">Profit</div>
                    <div class="detail-value">${formatCurrency(mission.final_results.net_profit || 0)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">ROI</div>
                    <div class="detail-value">${(mission.final_results.roi_percentage || 0).toFixed(1)}%</div>
                </div>
            ` : ''}
        </div>
        ${cargoBreakdownHTML}
        ${renderMissionControls(mission)}
    `;
    card.onclick = () => { showMissionDetail(mission._id || mission.id); };
    return card;
}

function renderMissionControls(mission) {
    const phase = mission.current_phase || mission.status || 'unknown';
    const autoProgress = mission.auto_progress !== false;
    const missionId = mission._id || mission.id;
    if (!missionId) return '';
    let controlsHTML = '<div class="mission-controls" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0,212,255,0.3); display: flex; gap: 0.5rem; flex-wrap: wrap;" onclick="event.stopPropagation();">';
    if (phase === 'launch_ready') {
        controlsHTML += `
            <button onclick="launchMission('${missionId}')" class="mission-control-btn" style="background: #00ff88; color: #000; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                🚀 Launch Mission
            </button>`;
    }
    if (['launched', 'traveling', 'mining_setup', 'mining', 'cargo_loading', 'returning'].includes(phase)) {
        if (autoProgress) {
            controlsHTML += `
                <button onclick="toggleMissionAutoProgress('${missionId}', false)" class="mission-control-btn" style="background: #ffaa00; color: #000; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer;">
                    ⏸️ Pause
                </button>`;
        } else {
            controlsHTML += `
                <button onclick="toggleMissionAutoProgress('${missionId}', true)" class="mission-control-btn" style="background: #00d4ff; color: #fff; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer;">
                    ▶️ Resume
                </button>`;
        }
    }
    if (!autoProgress && ['launched', 'traveling', 'mining_setup', 'mining', 'cargo_loading', 'returning'].includes(phase)) {
        controlsHTML += `
            <button onclick="advanceMissionDay('${missionId}')" class="mission-control-btn" style="background: rgba(0,212,255,0.2); color: #00d4ff; padding: 0.5rem 1rem; border: 1px solid #00d4ff; border-radius: 4px; cursor: pointer;">
                ⏩ Advance Day
            </button>`;
    }
    if (['launched', 'traveling', 'mining_setup', 'mining', 'cargo_loading', 'returning'].includes(phase)) {
        controlsHTML += `
            <span style="padding: 0.5rem; font-size: 0.85rem; color: ${autoProgress ? '#00ff88' : '#ffaa00'};">
                ${autoProgress ? '⏩ Auto-progress: ON' : '⏸️ Auto-progress: OFF'}
            </span>`;
    }
    controlsHTML += '</div>';
    return controlsHTML;
}

// Mission control actions
async function launchMission(missionId) {
    try {
        const response = await fetch(`/api/missions/${missionId}/launch`, { method: 'POST' });
        if (response.ok) {
            const result = await response.json();
            showToastNotification({ type: 'success', title: 'Mission Launched', message: result.message || 'Mission has been launched successfully!' });
            loadAllMissions();
        } else {
            const error = await response.json();
            showToastNotification({ type: 'error', title: 'Launch Failed', message: error.detail || 'Failed to launch mission' });
        }
    } catch (e) {
        console.error('Error launching mission:', e);
        showToastNotification({ type: 'error', title: 'Launch Failed', message: 'Failed to launch mission. Please try again.' });
    }
}

async function toggleMissionAutoProgress(missionId, enable) {
    try {
        const endpoint = enable ? 'resume' : 'pause';
        const response = await fetch(`/api/missions/${missionId}/${endpoint}`, { method: 'POST' });
        if (response.ok) {
            const result = await response.json();
            showToastNotification({ type: 'success', title: enable ? 'Mission Resumed' : 'Mission Paused', message: result.message || `Mission auto-progression ${enable ? 'resumed' : 'paused'}` });
            loadAllMissions();
            if (document.getElementById('missionDetailModal').classList.contains('active')) {
                showMissionDetail(missionId);
            }
        } else {
            const error = await response.json();
            showToastNotification({ type: 'error', title: 'Operation Failed', message: error.detail || `Failed to ${enable ? 'resume' : 'pause'} mission` });
        }
    } catch (e) {
        console.error('Error toggling mission:', e);
        showToastNotification({ type: 'error', title: 'Operation Failed', message: `Failed to ${enable ? 'resume' : 'pause'} mission. Please try again.` });
    }
}

async function advanceMissionDay(missionId) {
    try {
        const response = await fetch(`/api/missions/${missionId}/advance-day`, { method: 'POST' });
        if (response.ok) {
            const result = await response.json();
            showToastNotification({ type: 'success', title: 'Mission Advanced', message: result.message || 'Mission advanced by one day' });
            loadAllMissions();
            if (document.getElementById('missionDetailModal').classList.contains('active')) {
                showMissionDetail(missionId);
            }
        } else {
            const error = await response.json();
            showToastNotification({ type: 'error', title: 'Advance Failed', message: error.detail || 'Failed to advance mission day' });
        }
    } catch (e) {
        console.error('Error advancing mission day:', e);
        showToastNotification({ type: 'error', title: 'Advance Failed', message: 'Failed to advance mission day. Please try again.' });
    }
}

async function sellMissionCargo(missionId) {
    if (!missionId) return;
    try {
        const res = await fetch(`/api/missions/${missionId}/sell-cargo`, { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            const netProfit = data.net_profit || 0;
            const loanPayoff = data.loan_payoff || 0;
            let message = `Cargo Value: ${formatCurrency(data.cargo_value || 0)} | Net Profit: ${formatCurrency(netProfit)}`;
            if (loanPayoff > 0) {
                message += ` | Loan Repaid: ${formatCurrency(loanPayoff)}`;
            }
            
            if (data.needs_financing) {
                message += `\n⚠️ Negative profit detected. Suggested loan: ${formatCurrency(data.suggested_loan_amount || 0)}`;
                showToastNotification({ type: 'warning', title: 'Cargo Sold - Financing Needed', message: message });
            } else {
                showToastNotification({ type: 'success', title: 'Cargo Sold', message: message });
            }
            loadAllMissions();
            if (document.getElementById('missionDetailModal').classList.contains('active')) {
                showMissionDetail(missionId);
            }
        } else {
            const err = await res.json();
            showToastNotification({ type: 'error', title: 'Settlement Failed', message: err.detail || 'Try again later.' });
        }
    } catch (e) { 
        console.error(e);
        showToastNotification({ type: 'error', title: 'Settlement Failed', message: 'Failed to sell cargo. Please try again.' });
    }
}

// Mission detail modal
async function showMissionDetail(missionId) {
    try {
        const response = await fetch(`/api/missions/${missionId}/results`);
        if (!response.ok) throw new Error('Failed to load mission details');
        const mission = await response.json();
        document.getElementById('missionDetailModal').classList.add('active');
        renderMissionDetail(mission);
    } catch (e) {
        console.error('Error loading mission details:', e);
        showToastNotification({ type: 'error', title: 'Error', message: 'Failed to load mission details' });
    }
}

function hideMissionDetail() {
    document.getElementById('missionDetailModal').classList.remove('active');
}

function renderMissionDetail(mission) {
    const container = document.getElementById('missionDetailContent');
    const phases = [
        { id: 'planning', label: 'Planning', icon: '📋' },
        { id: 'launch_ready', label: 'Launch Ready', icon: '🚀' },
        { id: 'launched', label: 'Launched', icon: '🚀' },
        { id: 'traveling', label: 'Traveling', icon: '🌌' },
        { id: 'mining_setup', label: 'Mining Setup', icon: '🔧' },
        { id: 'mining', label: 'Mining', icon: '⛏️' },
        { id: 'cargo_loading', label: 'Cargo Loading', icon: '📦' },
        { id: 'returning', label: 'Returning', icon: '🏠' },
        { id: 'completed', label: 'Completed', icon: '✅' }
    ];
    const currentPhase = mission.current_phase || 'planning';
    const currentPhaseIndex = phases.findIndex(p => p.id === currentPhase);
    let timelineHTML = '<div class="mission-phase-timeline">';
    phases.forEach((phase, index) => {
        const isActive = phase.id === currentPhase;
        const isCompleted = index < currentPhaseIndex;
        const isUpcoming = index > currentPhaseIndex;
        timelineHTML += `
            <div class="phase-timeline-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${isUpcoming ? 'upcoming' : ''}">
                <div class="phase-timeline-icon">${phase.icon}</div>
                <div class="phase-timeline-label">${phase.label}</div>
                ${index < phases.length - 1 ? '<div class="phase-timeline-connector"></div>' : ''}
            </div>`;
    });
    timelineHTML += '</div>';
    const phaseDetails = renderMissionPhaseDetails(currentPhase, mission);
    const dailyEvents = renderDailyEvents(mission);
    const trackingHTML = renderMissionTracking(mission);
    const cargoSellingHTML = (mission.status === 'completed' || mission.current_phase === 'completed') && !mission.final_results ? renderCargoSellingInterface(mission) : '';
    const controlPanel = renderMissionControlPanel(mission);
    container.innerHTML = `
        <div class="mission-detail-header">
            <h2>${mission.name || 'Mission Details'}</h2>
            <button class="mission-detail-close" onclick="hideMissionDetail()">×</button>
        </div>
        <div class="mission-detail-body">
            ${controlPanel}
            ${timelineHTML}
            ${phaseDetails}
            ${trackingHTML}
            ${dailyEvents}
            ${cargoSellingHTML}
        </div>`;
}

function renderMissionControlPanel(mission) {
    const missionId = mission.mission_id || mission._id;
    const currentPhase = mission.current_phase || 'planning';
    const autoProgress = mission.auto_progress !== false;
    const canLaunch = currentPhase === 'launch_ready';
    const isActive = ['launched', 'traveling', 'mining_setup', 'mining', 'cargo_loading', 'returning'].includes(currentPhase);
    const isPaused = !autoProgress && isActive;
    let controlsHTML = '<div class="mission-control-panel">';
    controlsHTML += '<h3>Mission Controls</h3>';
    controlsHTML += '<div class="control-panel-grid">';
    if (canLaunch) {
        controlsHTML += `
            <button onclick="launchMission('${missionId}')" class="control-btn control-btn-primary" style="grid-column: 1 / -1;">🚀 Launch Mission</button>`;
    }
    if (isActive) {
        controlsHTML += `
            <button onclick="toggleMissionAutoProgress('${missionId}', ${!autoProgress})" class="control-btn ${autoProgress ? 'control-btn-warning' : 'control-btn-success'}">${autoProgress ? '⏸️ Pause' : '▶️ Resume'} Auto-Progress</button>`;
    }
    if (isPaused) {
        controlsHTML += `
            <button onclick="advanceMissionDay('${missionId}')" class="control-btn control-btn-secondary">⏭️ Advance Day</button>`;
    }
    controlsHTML += `
        <div class="control-status">
            <span class="status-label">Auto-Progress:</span>
            <span class="status-value ${autoProgress ? 'status-on' : 'status-off'}">${autoProgress ? 'ON' : 'OFF'}</span>
        </div>`;
    controlsHTML += '</div></div>';
    return controlsHTML;
}

function renderMissionPhaseDetails(phase, mission) {
    let detailsHTML = `<div class="mission-phase-details">
        <h3>Current Phase: ${phase.replace('_', ' ').toUpperCase()}</h3>
        <div class="phase-info-grid">
            <div class="phase-info-item"><div class="phase-info-label">Mission Day</div><div class="phase-info-value">${mission.current_day || 0}</div></div>
            <div class="phase-info-item"><div class="phase-info-label">Total Days</div><div class="phase-info-value">${mission.total_days || 0}</div></div>
            <div class="phase-info-item"><div class="phase-info-label">Status</div><div class="phase-info-value">${mission.status || 'unknown'}</div></div>
            <div class="phase-info-item"><div class="phase-info-label">Auto-Progress</div><div class="phase-info-value">${mission.auto_progress !== false ? 'ON' : 'OFF'}</div></div>
        </div>
    </div>`;
    if (phase === 'mining') {
        const cargo = mission.cargo || {};
        const cargoWeight = Object.values(cargo).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
        const shipCapacity = mission.ship_capacity || 50000;
        const progress = (shipCapacity ? (cargoWeight / shipCapacity * 100) : 0).toFixed(1);
        detailsHTML += `
            <div class="phase-mining-details">
                <h4>Mining Progress</h4>
                <div class="mining-progress-bar"><div class="mining-progress-fill" style="width: ${progress}%"></div></div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                    <span>${cargoWeight.toFixed(1)} kg</span>
                    <span>${shipCapacity.toLocaleString()} kg (${progress}%)</span>
                </div>
            </div>`;
    }
    return detailsHTML;
}

function renderMissionTracking(mission) {
    const cargo = mission.cargo || {};
    const cargoWeight = Object.values(cargo).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
    const costs = mission.costs || {};
    const finalResults = mission.final_results || {};
    const loanId = mission.loan_id;
    let financingHTML = '';
    if (loanId || finalResults.loan_payoff) {
        financingHTML = `
            <div class="tracking-card">
                <div class="tracking-label">Loan Status</div>
                <div class="tracking-value">${finalResults.loans_repaid && finalResults.loans_repaid.length > 0 ? '✅ Repaid' : '📋 Active'}</div>
            </div>`;
        if (finalResults.loan_payoff) {
            financingHTML += `
                <div class="tracking-card">
                    <div class="tracking-label">Loan Payoff</div>
                    <div class="tracking-value">${formatCurrency(finalResults.loan_payoff || 0)}</div>
                </div>`;
        }
    }
    return `
        <div class="mission-tracking">
            <h3>Mission Tracking</h3>
            <div class="tracking-grid">
                <div class="tracking-card"><div class="tracking-label">Cargo Weight</div><div class="tracking-value">${cargoWeight.toFixed(1)} kg</div></div>
                <div class="tracking-card"><div class="tracking-label">Total Costs</div><div class="tracking-value">${formatCurrency(costs.total || 0)}</div></div>
                ${financingHTML}
                <div class="tracking-card"><div class="tracking-label">Ground Control</div><div class="tracking-value">${formatCurrency(costs.ground_control || 0)}</div></div>
                <div class="tracking-card"><div class="tracking-label">Operations</div><div class="tracking-value">${formatCurrency(costs.space_events || 0)}</div></div>
            </div>
        </div>`;
}

function renderDailyEvents(mission) {
    const events = mission.events || [];
    if (events.length === 0) {
        return '<div class="mission-daily-events"><h3>Daily Events</h3><p style="color: #888; text-align: center; padding: 2rem;">No events recorded yet.</p></div>';
    }
    const eventsByDay = {};
    events.forEach(event => {
        const day = event.day || event.current_day || 0;
        (eventsByDay[day] = eventsByDay[day] || []).push(event);
    });
    const days = Object.keys(eventsByDay).sort((a, b) => parseInt(a) - parseInt(b));
    let eventsHTML = '<div class="mission-daily-events"><h3>Daily Events</h3>';
    days.forEach(day => {
        const dayEvents = eventsByDay[day];
        eventsHTML += `
            <div class="daily-events-day">
                <div class="daily-events-day-header" onclick="toggleDayEvents(${day})">
                    <span>Day ${day}</span>
                    <span>${dayEvents.length} event(s)</span>
                    <span class="day-toggle">▼</span>
                </div>
                <div class="daily-events-day-content" id="dayEvents${day}" style="display: none;">
                    ${dayEvents.map(event => `
                        <div class="daily-event-item">
                            <div class="event-type">${event.event_type || 'Unknown'}</div>
                            <div class="event-description">${event.description || ''}</div>
                            ${event.cost ? `<div class="event-cost">Cost: ${formatCurrency(event.cost)}</div>` : ''}
                            ${event.impact_days ? `<div class="event-impact">Impact: ${event.impact_days} days</div>` : ''}
                        </div>`).join('')}
                </div>
            </div>`;
    });
    eventsHTML += '</div>';
    return eventsHTML;
}

function toggleDayEvents(day) {
    const content = document.getElementById(`dayEvents${day}`);
    if (content) {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
    }
}

async function renderCargoSellingInterface(mission) {
    try {
        const response = await fetch('/api/commodity-prices');
        const prices = await response.json();
        const cargo = mission.cargo || {};
        const cargoBreakdown = {};
        let totalValue = 0;
        Object.entries(cargo).forEach(([element, weight]) => {
            const pricePerKg = prices[element]?.current_price || 0;
            const elementValue = weight * (pricePerKg / 1000);
            totalValue += elementValue;
            cargoBreakdown[element] = { weight: weight, pricePerKg: pricePerKg / 1000, value: elementValue };
        });
        const missionCosts = mission.costs?.total || 0;
        const estimatedProfit = totalValue - missionCosts;
        const estimatedROI = missionCosts > 0 ? (estimatedProfit / missionCosts * 100) : 0;
        return `
            <div class="mission-cargo-selling">
                <h3>Cargo Sale</h3>
                <div class="cargo-sale-summary">
                    <div class="cargo-breakdown-table">
                        <h4>Cargo Breakdown</h4>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <th style="padding: 0.75rem; text-align: left;">Element</th>
                                    <th style="padding: 0.75rem; text-align: right;">Weight (kg)</th>
                                    <th style="padding: 0.75rem; text-align: right;">Price/kg</th>
                                    <th style="padding: 0.75rem; text-align: right;">Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Object.entries(cargoBreakdown).map(([element, data]) => `
                                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                        <td style="padding: 0.75rem;">${element}</td>
                                        <td style="padding: 0.75rem; text-align: right;">${data.weight.toFixed(1)}</td>
                                        <td style="padding: 0.75rem; text-align: right;">${formatCurrency(data.pricePerKg)}</td>
                                        <td style="padding: 0.75rem; text-align: right; color: #00ff88;">${formatCurrency(data.value)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                            <tfoot>
                                <tr style="border-top: 2px solid rgba(255,255,255,0.2); font-weight: bold;">
                                    <td style="padding: 0.75rem;">Total</td>
                                    <td style="padding: 0.75rem; text-align: right;">${Object.values(cargoBreakdown).reduce((sum, d) => sum + d.weight, 0).toFixed(1)} kg</td>
                                    <td style="padding: 0.75rem;"></td>
                                    <td style="padding: 0.75rem; text-align: right; color: #00ff88;">${formatCurrency(totalValue)}</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                    <div class="cargo-sale-financials">
                        <div class="financial-item">
                            <span>Total Cargo Value:</span>
                            <span style="color: #00ff88; font-weight: bold;">${formatCurrency(totalValue)}</span>
                        </div>
                        <div class="financial-item">
                            <span>Mission Costs:</span>
                            <span style="color: #ff4444;">-${formatCurrency(missionCosts)}</span>
                        </div>
                        <div class="financial-item">
                            <span>Estimated Net Profit:</span>
                            <span style="color: ${estimatedProfit >= 0 ? '#00ff88' : '#ff4444'}; font-weight: bold;">${formatCurrency(estimatedProfit)}</span>
                        </div>
                        <div class="financial-item">
                            <span>Estimated ROI:</span>
                            <span style="color: ${estimatedROI >= 0 ? '#00ff88' : '#ff4444'}; font-weight: bold;">${estimatedROI.toFixed(1)}%</span>
                        </div>
                    </div>
                    <button onclick="sellMissionCargo('${mission._id || mission.mission_id}')" 
                            class="cargo-sell-btn" 
                            style="width: 100%; padding: 1rem; background: #00ff88; color: #000; border: none; border-radius: 6px; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin-top: 1rem;">
                        💰 Sell Cargo
                    </button>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error rendering cargo selling interface:', error);
        return '<div class="mission-cargo-selling"><p style="color: #ff4444;">Error loading cargo sale information</p></div>';
    }
}

function calculateMissionProgress(mission) {
    if (mission.status === 'completed') return 100;
    const phase = mission.current_phase || mission.status;
    if (phase === 'planning') return 10;
    if (phase === 'launched' || phase === 'traveling') return 30;
    if (phase === 'mining') return 60;
    if (phase === 'returning') return 90;
    return 0;
}

function calculateCargoWeight(cargo) {
    return Object.values(cargo).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
}

// Mission Planning Wizard
let missionWizardState = {
    currentStep: 1,
    totalSteps: 6,
    data: { 
        name: '', 
        ship_id: '', 
        ship_option: 'reuse', // 'reuse' or 'purchase'
        ship_to_purchase: null,
        asteroid_id: '', 
        loan: {
            principal: null,
            apr: 8.0,
            term_days: null,
            loan_id: null
        },
        budget: null, 
        estimated_costs: null, 
        estimated_roi: null 
    }
};

function showCreateMissionForm() {
    initMissionWizard();
    document.getElementById('missionWizardModal').classList.add('active');
}

function hideMissionWizard() {
    document.getElementById('missionWizardModal').classList.remove('active');
    missionWizardState = { 
        currentStep: 1, 
        totalSteps: 6, 
        data: { 
            name: '', 
            ship_id: '', 
            ship_option: 'reuse',
            ship_to_purchase: null,
            asteroid_id: '', 
            loan: { principal: null, apr: 8.0, term_days: null, loan_id: null },
            budget: null, 
            estimated_costs: null, 
            estimated_roi: null 
        } 
    };
}

function initMissionWizard() {
    missionWizardState.currentStep = 1;
    updateWizardUI();
    // Load initial data - asteroids will be loaded when step 1 is shown
    loadShipCatalog();
    loadFinancingOptions();
}

function updateWizardUI() {
    const step = missionWizardState.currentStep;
    const progress = (step / missionWizardState.totalSteps) * 100;
    const fill = document.getElementById('wizardProgressFill');
    if (fill) fill.style.width = progress + '%';
    document.querySelectorAll('.wizard-step').forEach((el, idx) => {
        const stepNum = idx + 1;
        el.classList.remove('active', 'completed');
        if (stepNum < step) el.classList.add('completed'); else if (stepNum === step) el.classList.add('active');
    });
    document.querySelectorAll('.wizard-step-content').forEach((content, idx) => {
        content.style.display = (idx + 1 === step) ? 'block' : 'none';
    });
    const backBtn = document.getElementById('wizardBtnBack');
    const nextBtn = document.getElementById('wizardBtnNext');
    const submitBtn = document.getElementById('wizardBtnSubmit');
    if (backBtn) backBtn.style.display = step > 1 ? 'block' : 'none';
    if (nextBtn) nextBtn.style.display = step < missionWizardState.totalSteps ? 'block' : 'none';
    if (submitBtn) submitBtn.style.display = step === missionWizardState.totalSteps ? 'block' : 'none';
    // Load data when entering steps
    if (step === 1) loadAsteroidsForSelection();
    if (step === 3) loadAvailableShips();
    if (step === 4) calculateFinancingNeeds();
    if (step === 5 && missionWizardState.data.ship_id && missionWizardState.data.asteroid_id) calculateMissionBudget();
    if (step === 6 && missionWizardState.data.ship_id && missionWizardState.data.asteroid_id) checkLaunchReadiness();
}

function wizardNextStep() {
    if (validateWizardStep(missionWizardState.currentStep)) {
        if (missionWizardState.currentStep < missionWizardState.totalSteps) {
            missionWizardState.currentStep++;
            updateWizardUI();
        }
    }
}

function wizardPreviousStep() {
    if (missionWizardState.currentStep > 1) {
        missionWizardState.currentStep--;
        updateWizardUI();
    }
}

function validateWizardStep(step) {
    const errorEl = document.getElementById(`errorStep${step}`);
    if (errorEl) { errorEl.classList.remove('show'); errorEl.textContent = ''; }
    switch(step) {
        case 1:
            // Step 1: Asteroid Selection (now first)
            if (!missionWizardState.data.asteroid_id) { showWizardError(1, 'Please select an asteroid'); return false; }
            return true;
        case 2: {
            // Step 2: Mission Info (moved to second)
            const name = (document.getElementById('missionName') || {}).value?.trim() || '';
            if (!name) { showWizardError(2, 'Mission name is required'); return false; }
            missionWizardState.data.name = name;
            missionWizardState.data.description = (document.getElementById('missionDescription') || {}).value?.trim() || '';
            return true;
        }
        case 3:
            // Step 3: Ship Selection (moved to third)
            if (missionWizardState.data.ship_option === 'reuse' && !missionWizardState.data.ship_id) {
                showWizardError(3, 'Please select a ship');
                return false;
            }
            if (missionWizardState.data.ship_option === 'purchase' && !missionWizardState.data.ship_to_purchase) {
                showWizardError(3, 'Please select a ship to purchase');
                return false;
            }
            return true;
        case 4: {
            // Financing is auto-calculated, just validate APR if financing is needed
            if (missionWizardState.data.financing && missionWizardState.data.financing.needs_financing) {
                const apr = parseFloat((document.getElementById('loanAPR') || {}).value || 8.0);
                if (apr < 0 || apr > 100) { showWizardError(4, 'APR must be between 0 and 100%'); return false; }
                missionWizardState.data.loan.principal = missionWizardState.data.financing.loan_principal || 0;
                missionWizardState.data.loan.apr = apr;
                missionWizardState.data.loan.term_days = missionWizardState.data.financing.loan_term_days || 0;
            } else {
                // No financing needed
                missionWizardState.data.loan.principal = 0;
                missionWizardState.data.loan.apr = 8.0;
                missionWizardState.data.loan.term_days = 0;
            }
            return true;
        }
        case 5:
        case 6:
        default:
            return true;
    }
}

function showWizardError(step, message) {
    const errorEl = document.getElementById(`errorStep${step}`);
    if (errorEl) { errorEl.textContent = message; errorEl.classList.add('show'); }
}

async function loadAvailableShips() {
    try {
        const response = await fetch('/api/ships');
        const ships = await response.json();
        const shipsList = document.getElementById('wizardShipsList');
        if (!shipsList) return;
        if (!ships || ships.length === 0) { shipsList.innerHTML = '<div class="wizard-loading">No available ships. Please create a ship first.</div>'; return; }
        shipsList.innerHTML = ships
            .filter(ship => ship.status === 'available')
            .map(ship => `
                <div class="wizard-select-item" onclick="selectShip('${ship._id}', '${ship.name}', ${ship.capacity_kg})">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold; color: #00d4ff;">${ship.name || 'Unnamed Ship'}</div>
                            <div style="font-size: 0.85rem; color: #888; margin-top: 0.25rem;">
                                Capacity: ${ship.capacity_kg?.toLocaleString() || 50000} kg
                            </div>
                        </div>
                        ${ship.veteran ? '<span style="color: #00ff88; font-size: 0.8rem;">✓ Veteran</span>' : ''}
                    </div>
                </div>`).join('');
    } catch (e) {
        console.error('Error loading ships:', e);
        const shipsList = document.getElementById('wizardShipsList');
        if (shipsList) shipsList.innerHTML = '<div class="wizard-loading" style="color: #ff4444;">Error loading ships</div>';
    }
}

function toggleShipOption() {
    const option = document.querySelector('input[name="shipOption"]:checked')?.value || 'reuse';
    missionWizardState.data.ship_option = option;
    const reuseDiv = document.getElementById('wizardShipReuse');
    const purchaseDiv = document.getElementById('wizardShipPurchase');
    if (option === 'reuse') {
        if (reuseDiv) reuseDiv.style.display = 'block';
        if (purchaseDiv) purchaseDiv.style.display = 'none';
        missionWizardState.data.ship_to_purchase = null;
    } else {
        if (reuseDiv) reuseDiv.style.display = 'none';
        if (purchaseDiv) purchaseDiv.style.display = 'block';
        missionWizardState.data.ship_id = '';
        if (!missionWizardState.data.ship_to_purchase) loadShipCatalog();
    }
    const err = document.getElementById('errorStep2'); if (err) err.classList.remove('show');
}

function selectShip(shipId, shipName, capacity) {
    missionWizardState.data.ship_id = shipId;
    missionWizardState.data.ship_name = shipName;
    missionWizardState.data.ship_capacity = capacity;
    missionWizardState.data.ship_to_purchase = null;
    document.querySelectorAll('#wizardShipsList .wizard-select-item').forEach(item => item.classList.remove('selected'));
    if (window.event && window.event.currentTarget) window.event.currentTarget.classList.add('selected');
    const err = document.getElementById('errorStep2'); if (err) err.classList.remove('show');
}

async function loadShipCatalog() {
    try {
        const response = await fetch('/api/ships/catalog');
        const catalog = await response.json();
        const catalogList = document.getElementById('wizardShipCatalog');
        if (!catalogList) return;
        if (!catalog || catalog.length === 0) {
            catalogList.innerHTML = '<div class="wizard-loading">No ships available in catalog</div>';
            return;
        }
        catalogList.innerHTML = catalog.map(ship => `
            <div class="wizard-select-item" onclick="selectShipToPurchase(${JSON.stringify(ship).replace(/"/g, '&quot;')})">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; color: #00d4ff;">${ship.name || 'Unnamed Ship'}</div>
                        <div style="font-size: 0.85rem; color: #888; margin-top: 0.25rem;">
                            Capacity: ${ship.capacity?.toLocaleString() || 50000} kg | Mining: ${ship.mining_power || 50}/100
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #00ff88; font-weight: bold;">${formatCurrency(ship.base_cost || 0)}</div>
                    </div>
                </div>
            </div>`).join('');
    } catch (e) {
        console.error('Error loading ship catalog:', e);
        const catalogList = document.getElementById('wizardShipCatalog');
        if (catalogList) catalogList.innerHTML = '<div class="wizard-loading" style="color: #ff4444;">Error loading ship catalog</div>';
    }
}

function selectShipToPurchase(ship) {
    missionWizardState.data.ship_to_purchase = ship;
    missionWizardState.data.ship_id = '';
    document.querySelectorAll('#wizardShipCatalog .wizard-select-item').forEach(item => item.classList.remove('selected'));
    if (window.event && window.event.currentTarget) window.event.currentTarget.classList.add('selected');
    const infoDiv = document.getElementById('selectedShipInfo');
    const detailsDiv = document.getElementById('selectedShipDetails');
    if (infoDiv && detailsDiv) {
        infoDiv.style.display = 'block';
        detailsDiv.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                <div><span style="color: #888;">Name:</span> <span style="color: #fff;">${ship.name}</span></div>
                <div><span style="color: #888;">Capacity:</span> <span style="color: #fff;">${ship.capacity?.toLocaleString() || 0} kg</span></div>
                <div><span style="color: #888;">Mining Power:</span> <span style="color: #fff;">${ship.mining_power || 0}/100</span></div>
                <div><span style="color: #888;">Cost:</span> <span style="color: #00ff88; font-weight: bold;">${formatCurrency(ship.base_cost || 0)}</span></div>
            </div>`;
    }
    const err = document.getElementById('errorStep2'); if (err) err.classList.remove('show');
}

async function loadFinancingOptions() {
    try {
        const response = await fetch('/api/financing/options');
        const options = await response.json();
        if (options.default_apr) {
            const aprInput = document.getElementById('loanAPR');
            if (aprInput && !aprInput.value) aprInput.value = options.default_apr;
        }
    } catch (e) {
        console.error('Error loading financing options:', e);
    }
}

async function calculateFinancingNeeds() {
    const calcDiv = document.getElementById('financingCalculation');
    const resultsDiv = document.getElementById('financingResults');
    const neededDiv = document.getElementById('financingNeeded');
    const notNeededDiv = document.getElementById('financingNotNeeded');
    
    if (!calcDiv || !resultsDiv) return;
    
    try {
        calcDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        calcDiv.innerHTML = 'Calculating financing needs...';
        
        // Build query parameters
        const params = new URLSearchParams();
        if (missionWizardState.data.asteroid_id) {
            params.append('asteroid_id', missionWizardState.data.asteroid_id);
        }
        if (missionWizardState.data.ship_option === 'purchase' && missionWizardState.data.ship_to_purchase) {
            params.append('ship_to_purchase', JSON.stringify(missionWizardState.data.ship_to_purchase));
        } else if (missionWizardState.data.ship_id) {
            params.append('ship_id', missionWizardState.data.ship_id);
        }
        
        const response = await fetch(`/api/financing/calculate?${params.toString()}`);
        if (!response.ok) {
            throw new Error(`Failed to calculate financing: ${response.status}`);
        }
        
        const financing = await response.json();
        missionWizardState.data.financing = financing;
        
        // Display results
        calcDiv.style.display = 'none';
        resultsDiv.style.display = 'block';
        
        // Update cost breakdown
        document.getElementById('financingShipCost').textContent = formatCurrency(financing.ship_cost || 0);
        document.getElementById('financingMissionCost').textContent = formatCurrency(financing.mission_operational_costs || 0);
        document.getElementById('financingRepairCost').textContent = formatCurrency(financing.estimated_repair_cost || 0);
        document.getElementById('financingRevenue').textContent = formatCurrency(financing.estimated_revenue || 0);
        document.getElementById('financingTotalCosts').textContent = formatCurrency(financing.total_costs || 0);
        
        const profit = financing.estimated_profit || 0;
        const profitEl = document.getElementById('financingProfit');
        profitEl.textContent = formatCurrency(profit);
        profitEl.style.color = profit >= 0 ? '#00ff88' : '#ff4444';
        
        // Show financing needed or not needed
        if (financing.needs_financing && financing.loan_principal > 0) {
            neededDiv.style.display = 'block';
            notNeededDiv.style.display = 'none';
            
            // Update loan details
            document.getElementById('autoLoanPrincipal').textContent = formatCurrency(financing.loan_principal);
            document.getElementById('autoLoanTerm').textContent = `${financing.loan_term_days || financing.mission_duration_days || 0} days`;
            
            // Set default APR
            const aprInput = document.getElementById('loanAPR');
            if (aprInput && !aprInput.value) {
                aprInput.value = financing.loan_apr || 8.0;
            }
            
            // Calculate and update interest/payoff when APR changes
            const updateLoanCalc = () => {
                const apr = parseFloat(aprInput?.value || 8.0);
                const principal = financing.loan_principal;
                const termDays = financing.loan_term_days || financing.mission_duration_days || 0;
                const interest = principal * (apr / 100) * (termDays / 365);
                const payoff = principal + interest;
                
                document.getElementById('autoLoanInterest').textContent = formatCurrency(interest);
                document.getElementById('autoLoanPayoff').textContent = formatCurrency(payoff);
            };
            
            updateLoanCalc();
            if (aprInput) {
                aprInput.addEventListener('input', updateLoanCalc);
            }
        } else {
            neededDiv.style.display = 'none';
            notNeededDiv.style.display = 'block';
        }
        
    } catch (e) {
        console.error('Error calculating financing:', e);
        calcDiv.innerHTML = '<div style="color: #ff4444;">Error calculating financing needs. Please try again.</div>';
    }
}

// Add event listener for APR input updates
document.addEventListener('DOMContentLoaded', () => {
    const loanAPR = document.getElementById('loanAPR');
    if (loanAPR) {
        loanAPR.addEventListener('input', () => {
            if (missionWizardState.data.financing && missionWizardState.data.financing.needs_financing) {
                const apr = parseFloat(loanAPR.value || 8.0);
                const principal = missionWizardState.data.financing.loan_principal;
                const termDays = missionWizardState.data.financing.loan_term_days || missionWizardState.data.financing.mission_duration_days || 0;
                const interest = principal * (apr / 100) * (termDays / 365);
                const payoff = principal + interest;
                
                const interestEl = document.getElementById('autoLoanInterest');
                const payoffEl = document.getElementById('autoLoanPayoff');
                if (interestEl) interestEl.textContent = formatCurrency(interest);
                if (payoffEl) payoffEl.textContent = formatCurrency(payoff);
            }
        });
    }
});

async function loadAsteroidsForSelection() {
    try {
        const response = await fetch('/api/asteroids?limit=50');
        const data = await response.json();
        // Handle both array and object response formats
        const asteroids = Array.isArray(data) ? data : (data.asteroids || []);
        const asteroidsList = document.getElementById('wizardAsteroidsList');
        if (!asteroidsList) return;
        if (!asteroids || asteroids.length === 0) { 
            asteroidsList.innerHTML = '<div class="wizard-loading">No asteroids available</div>'; 
            return; 
        }
        asteroidsList.innerHTML = asteroids.map(asteroid => {
            const asteroidId = asteroid._id || asteroid.id;
            const asteroidName = asteroid.name || asteroid.full_name || 'Unknown Asteroid';
            const moid = asteroid.moid || asteroid.moid_au || 0.1;
            const asteroidClass = asteroid.class || 'C';
            return `
                <div class="wizard-select-item" data-asteroid-id="${asteroidId}" onclick="selectAsteroid('${asteroidId}', '${asteroidName}', ${moid})">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold; color: #00d4ff;">${asteroidName}</div>
                            <div style="font-size: 0.85rem; color: #888; margin-top: 0.25rem;">
                                MOID: ${moid.toFixed(3)} AU | Class: ${asteroidClass}
                            </div>
                        </div>
                        ${getAsteroidClassBadge(asteroidClass)}
                    </div>
                </div>`;
        }).join('');
    } catch (e) {
        console.error('Error loading asteroids:', e);
        const asteroidsList = document.getElementById('wizardAsteroidsList');
        if (asteroidsList) asteroidsList.innerHTML = '<div class="wizard-loading" style="color: #ff4444;">Error loading asteroids</div>';
    }
}

function filterAsteroids() {
    const searchTerm = (document.getElementById('asteroidSearch') || {}).value?.toLowerCase() || '';
    document.querySelectorAll('#wizardAsteroidsList .wizard-select-item').forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
}

async function selectAsteroid(asteroidId, asteroidName, moid) {
    missionWizardState.data.asteroid_id = asteroidId;
    missionWizardState.data.asteroid_name = asteroidName;
    missionWizardState.data.asteroid_moid = moid;
    document.querySelectorAll('#wizardAsteroidsList .wizard-select-item').forEach(item => item.classList.remove('selected'));
    if (window.event && window.event.currentTarget) window.event.currentTarget.classList.add('selected');
    const err = document.getElementById('errorStep1'); if (err) err.classList.remove('show');
    
    const analysisDiv = document.getElementById('asteroidAnalysis');
    if (analysisDiv) {
        analysisDiv.style.display = 'block';
        analysisDiv.innerHTML = '<div class="wizard-loading">Loading asteroid details...</div>';
    }
    
    try {
        const response = await fetch(`/api/asteroids/${asteroidId}/details`);
        if (!response.ok) throw new Error(`Failed to load details: ${response.status}`);
        const details = await response.json();
        
        if (analysisDiv) {
            const asteroid = details.asteroid || {};
            const travel = details.travel || {};
            const mining = details.mining || {};
            const value = details.value || {};
            const composition = details.composition || {};
            
            analysisDiv.innerHTML = `
                <div style="margin-top: 1.5rem; padding: 1.5rem; background: rgba(0,212,255,0.1); border-radius: 8px; border: 1px solid rgba(0,212,255,0.3);">
                    <h4 style="color: #00d4ff; margin-bottom: 1rem; font-size: 1.2rem;">${asteroid.name || asteroidName}</h4>
                    
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1rem;">
                        <div style="padding: 0.75rem; background: rgba(0,0,0,0.3); border-radius: 6px;">
                            <div style="color: #888; font-size: 0.85rem; margin-bottom: 0.25rem;">Asteroid Class</div>
                            <div style="color: #fff; font-weight: bold; font-size: 1.1rem;">${getAsteroidClassBadge(asteroid.class || 'C')}</div>
                        </div>
                        <div style="padding: 0.75rem; background: rgba(0,0,0,0.3); border-radius: 6px;">
                            <div style="color: #888; font-size: 0.85rem; margin-bottom: 0.25rem;">Diameter</div>
                            <div style="color: #fff; font-weight: bold; font-size: 1.1rem;">${(asteroid.diameter || 0).toLocaleString()} km</div>
                        </div>
                        <div style="padding: 0.75rem; background: rgba(0,0,0,0.3); border-radius: 6px;">
                            <div style="color: #888; font-size: 0.85rem; margin-bottom: 0.25rem;">Travel Time (Round Trip)</div>
                            <div style="color: #00ff88; font-weight: bold; font-size: 1.1rem;">${Math.ceil(travel.total_days || 0)} days</div>
                        </div>
                        <div style="padding: 0.75rem; background: rgba(0,0,0,0.3); border-radius: 6px;">
                            <div style="color: #888; font-size: 0.85rem; margin-bottom: 0.25rem;">Mining Difficulty</div>
                            <div style="color: #fff; font-weight: bold; font-size: 1.1rem; text-transform: capitalize;">${asteroid.mining_difficulty || 'medium'}</div>
                        </div>
                    </div>
                    
                    <div style="padding: 1rem; background: rgba(0,255,136,0.1); border-radius: 6px; margin-bottom: 1rem; border: 1px solid rgba(0,255,136,0.3);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <span style="color: #888; font-size: 1.1rem;">Total Estimated Value</span>
                            <span style="color: #00ff88; font-weight: bold; font-size: 1.5rem;">${formatCurrency(value.total_estimated_value || 0)}</span>
                        </div>
                        <div style="color: #888; font-size: 0.85rem;">Based on ${value.total_elements || 0} elements • ${(composition.total_mass_kg || 0).toLocaleString()} kg total mass</div>
                    </div>
                    
                    ${(value.element_breakdown || []).length > 0 ? `
                    <div style="margin-bottom: 1rem;">
                        <h5 style="color: #00d4ff; margin-bottom: 0.75rem; font-size: 0.95rem;">Top Valuable Elements</h5>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; font-size: 0.85rem;">
                            ${value.element_breakdown.slice(0, 6).map(el => `
                                <div style="padding: 0.5rem; background: rgba(0,0,0,0.2); border-radius: 4px;">
                                    <div style="color: #fff; font-weight: bold;">${el.name}</div>
                                    <div style="color: #888; font-size: 0.75rem;">${(el.mass_kg || 0).toLocaleString()} kg × ${formatCurrency(el.price_per_kg || 0)}/kg</div>
                                    <div style="color: #00ff88; font-weight: bold;">${formatCurrency(el.value || 0)}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${mining.estimated_yield ? `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.9rem;">
                        <div style="padding: 0.75rem; background: rgba(0,0,0,0.3); border-radius: 6px;">
                            <div style="color: #888;">Estimated Mining Yield</div>
                            <div style="color: #00ff88; font-weight: bold;">${(mining.estimated_yield || 0).toLocaleString()} kg</div>
                        </div>
                        <div style="padding: 0.75rem; background: rgba(0,0,0,0.3); border-radius: 6px;">
                            <div style="color: #888;">Ore Grade</div>
                            <div style="color: #00ff88; font-weight: bold;">${((mining.ore_grade || 0) * 100).toFixed(1)}%</div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
        }
    } catch (e) { 
        console.error('Error loading asteroid details:', e);
        if (analysisDiv) {
            analysisDiv.innerHTML = '<div style="color: #ff4444; padding: 1rem;">Error loading asteroid details. Please try again.</div>';
        }
    }
}

async function calculateMissionBudget() {
    const budgetDiv = document.getElementById('wizardBudgetDetails');
    if (budgetDiv) budgetDiv.innerHTML = '<div class="wizard-loading">Calculating budget...</div>';
    try {
        const response = await fetch(`/api/missions/budget-estimate?ship_id=${missionWizardState.data.ship_id}&asteroid_id=${missionWizardState.data.asteroid_id}`);
        const budget = await response.json();
        missionWizardState.data.budget = budget;
        missionWizardState.data.estimated_costs = budget.estimated_costs || {};
        missionWizardState.data.estimated_roi = budget.estimated_roi || 0;
        if (budgetDiv) budgetDiv.innerHTML = `
            <div class="wizard-budget-item"><span>Ship Capacity</span><span>${(budget.ship_capacity || 50000).toLocaleString()} kg</span></div>
            <div class="wizard-budget-item"><span>Estimated Travel Time</span><span>${Math.max(1, budget.travel_time_days || 1)} days</span></div>
            <div class="wizard-budget-item"><span>Mining Site Setup</span><span>${budget.mining_setup_days || 3} days</span></div>
            <div class="wizard-budget-item"><span>Estimated Mining Time</span><span>${budget.mining_time_days || 34} days</span></div>
            <div class="wizard-budget-item"><span>Total Mission Duration</span><span>${budget.total_days || 0} days</span></div>
            <div class="wizard-budget-item"><span>Ground Control Costs</span><span>${formatCurrency(budget.estimated_costs?.ground_control || 0)}</span></div>
            <div class="wizard-budget-item"><span>Operation Costs</span><span>${formatCurrency(budget.estimated_costs?.operations || 0)}</span></div>
            <div class="wizard-budget-item"><span>Total Estimated Costs</span><span>${formatCurrency(budget.estimated_costs?.total || 0)}</span></div>
            <div class="wizard-budget-item"><span>Estimated Cargo Value</span><span>${formatCurrency(budget.estimated_revenue || 0)}</span></div>
            <div class="wizard-budget-item"><span>Estimated Net Profit</span><span>${formatCurrency(budget.estimated_profit || 0)}</span></div>
            <div class="wizard-budget-item"><span>Estimated ROI</span><span>${(budget.estimated_roi || 0).toFixed(1)}%</span></div>`;
    } catch (e) {
        console.error('Error calculating budget:', e);
        if (budgetDiv) budgetDiv.innerHTML = '<div class="wizard-loading" style="color: #ff4444;">Error calculating budget</div>';
    }
}

async function checkLaunchReadiness() {
    const readinessDiv = document.getElementById('wizardReadinessCheck');
    if (readinessDiv) readinessDiv.innerHTML = '<div class="wizard-loading">Checking readiness...</div>';
    try {
        const response = await fetch(`/api/missions/readiness?ship_id=${missionWizardState.data.ship_id}&asteroid_id=${missionWizardState.data.asteroid_id}`);
        const readiness = await response.json();
        const checks = [
            { label: 'Mission name provided', pass: !!missionWizardState.data.name },
            { label: 'Ship selected', pass: !!missionWizardState.data.ship_id },
            { label: 'Asteroid selected', pass: !!missionWizardState.data.asteroid_id },
            { label: 'Ship available', pass: readiness.ship_available || false },
            { label: 'Asteroid accessible', pass: readiness.asteroid_accessible || false },
            { label: 'Budget sufficient', pass: readiness.budget_sufficient || false }
        ];
        const allPass = checks.every(c => c.pass);
        if (readinessDiv) readinessDiv.innerHTML = checks.map(c => `
            <div class="wizard-readiness-item ${c.pass ? 'pass' : 'fail'}"><span class="wizard-readiness-icon">${c.pass ? '✓' : '✗'}</span><span>${c.label}</span></div>`).join('') + `
            <div style="margin-top: 1rem; padding: 1rem; background: ${allPass ? 'rgba(0, 255, 136, 0.1)' : 'rgba(255, 68, 68, 0.1)'}; border-radius: 6px; text-align: center;">
                <strong style="color: ${allPass ? '#00ff88' : '#ff4444'}">${allPass ? '✓ Ready to Launch' : '✗ Not Ready - Please review issues above'}</strong>
            </div>`;
    } catch (e) {
        console.error('Error checking readiness:', e);
        if (readinessDiv) readinessDiv.innerHTML = '<div class="wizard-loading" style="color: #ff4444;">Error checking readiness</div>';
    }
}

async function submitMissionPlan() {
    if (!validateWizardStep(6)) return;
    const submitBtn = document.getElementById('wizardBtnSubmit');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Creating Mission...'; }
    try {
        let shipId = missionWizardState.data.ship_id;
        
        // Purchase ship if needed
        if (missionWizardState.data.ship_option === 'purchase' && missionWizardState.data.ship_to_purchase) {
            const purchaseResponse = await fetch('/api/ships/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: missionWizardState.data.ship_to_purchase.name,
                    user_id: 'current_user',
                    capacity: missionWizardState.data.ship_to_purchase.capacity,
                    mining_power: missionWizardState.data.ship_to_purchase.mining_power,
                    shield: missionWizardState.data.ship_to_purchase.shield || 100,
                    hull: missionWizardState.data.ship_to_purchase.hull || 100,
                    power_systems: missionWizardState.data.ship_to_purchase.power_systems || 100
                })
            });
            if (!purchaseResponse.ok) {
                const error = await purchaseResponse.json();
                showWizardError(6, error.detail || 'Failed to purchase ship');
                if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Create Mission'; }
                return;
            }
            const purchasedShip = await purchaseResponse.json();
            shipId = purchasedShip._id || purchasedShip.id;
        }
        
        // Create loan
        let loanId = null;
        if (missionWizardState.data.loan.principal > 0) {
            const loanResponse = await fetch('/api/financing/loans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    principal: missionWizardState.data.loan.principal,
                    apr: missionWizardState.data.loan.apr,
                    term_days: missionWizardState.data.loan.term_days,
                    user_id: 'current_user'
                })
            });
            if (!loanResponse.ok) {
                const error = await loanResponse.json();
                showWizardError(6, error.detail || 'Failed to create loan');
                if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Create Mission'; }
                return;
            }
            const loan = await loanResponse.json();
            loanId = loan._id || loan.id;
        }
        
        // Create mission
        const response = await fetch('/api/missions', {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: missionWizardState.data.name,
                description: missionWizardState.data.description,
                user_id: 'current_user',
                ship_id: shipId,
                asteroid_id: missionWizardState.data.asteroid_id,
                loan_id: loanId
            })
        });
        
        if (response.ok) {
            const mission = await response.json();
            
            // Loan is already linked via loan_id in mission creation, no need to link separately
            
            hideMissionWizard();
            loadAllMissions();
            showToastNotification({ type: 'success', title: 'Mission Created', message: `Mission "${mission.name}" has been created and is ready for planning phase.` });
        } else {
            const error = await response.json();
            showWizardError(6, error.detail || 'Failed to create mission');
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Create Mission'; }
        }
    } catch (e) {
        console.error('Error creating mission:', e);
        showWizardError(6, 'Failed to create mission. Please try again.');
        if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Create Mission'; }
    }
}


