// Civilization dashboard module

async function loadCivilizationData() {
    try {
        const response = await apiFetch('/civilization/summary');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        renderCivilizationMetrics(data.metrics || {});
        renderCivilizationEvents(data.events || []);
        renderCivilizationLogs(data.logs || []);
        renderCivilizationTrade(data.trade_routes || []);
        renderCivilizationChart(data.metrics_history || []);
    } catch (error) {
        console.error('Error loading civilization data:', error);
    }
}

function renderCivilizationMetrics(metrics) {
    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };
    setText('civ-tech-index', (metrics.tech_index || 0).toFixed(1));
    setText('civ-epc', Math.round(metrics.energy_per_capita || 0).toLocaleString());
    setText('civ-population', (metrics.population_in_space || 0).toLocaleString());
    setText('civ-independence', `${(metrics.resource_independence || 0).toFixed(1)}%`);
    setText('civ-culture', `${(metrics.cultural_influence || 0).toFixed(1)}%`);
    setText('civ-ai', `${(metrics.ai_sentience || 0).toFixed(1)}%`);
}

function renderCivilizationEvents(events) {
    const container = document.getElementById('civilization-events');
    if (!container) return;
    if (!events.length) {
        container.innerHTML = '<p style="color: #888;">No protocol events logged yet.</p>';
        return;
    }
    container.innerHTML = events.map(event => `
        <div class="civilization-item">
            <div class="civilization-item-title">${event.event_type || 'protocol_event'}</div>
            <div class="civilization-item-text">${event.description || ''}</div>
            <div class="civilization-item-meta">${event.created_at || event.timestamp || ''}</div>
        </div>
    `).join('');
}

function renderCivilizationLogs(logs) {
    const container = document.getElementById('civilization-logs');
    if (!container) return;
    if (!logs.length) {
        container.innerHTML = '<p style="color: #888;">No humanity logs yet.</p>';
        return;
    }
    container.innerHTML = logs.map(log => `
        <div class="civilization-item">
            <div class="civilization-item-title">${log.trigger || 'log'}</div>
            <div class="civilization-item-text">${log.text || ''}</div>
            <div class="civilization-item-meta">${log.created_at || log.timestamp || ''}</div>
        </div>
    `).join('');
}

function renderCivilizationTrade(routes) {
    const container = document.getElementById('civilization-trade');
    if (!container) return;
    if (!routes.length) {
        container.innerHTML = '<p style="color: #888;">No trade routes available.</p>';
        return;
    }
    const rows = routes.map(route => `
        <tr>
            <td>${route.from}</td>
            <td>${route.to}</td>
            <td>${(route.demand_index || 0).toFixed(2)}</td>
            <td>${route.updated_at || ''}</td>
        </tr>
    `).join('');
    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>From</th>
                    <th>To</th>
                    <th>Demand Index</th>
                    <th>Updated</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function renderCivilizationChart(history) {
    const ctx = document.getElementById('civilizationChart');
    if (!ctx || !history.length || typeof Chart !== 'function') {
        return;
    }
    if (!window.charts) {
        window.charts = {};
    }
    if (window.charts.civilization) {
        window.charts.civilization.destroy();
    }
    const labels = history.map(item => new Date(item.created_at || item.timestamp || Date.now()).toLocaleDateString());
    const tech = history.map(item => item.tech_index || 0);
    const ai = history.map(item => item.ai_sentience || 0);
    const independence = history.map(item => item.resource_independence || 0);
    const culture = history.map(item => item.cultural_influence || 0);

    window.charts.civilization = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                { label: 'Tech Index', data: tech, borderColor: '#00d4ff', backgroundColor: 'transparent' },
                { label: 'AI Sentience', data: ai, borderColor: '#b37bff', backgroundColor: 'transparent' },
                { label: 'Resource Independence', data: independence, borderColor: '#00ff88', backgroundColor: 'transparent' },
                { label: 'Cultural Influence', data: culture, borderColor: '#ffaa00', backgroundColor: 'transparent' }
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

async function downloadLegacyExport() {
    try {
        const response = await apiFetch('/civilization/legacy-export');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `civilization_legacy_${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(link.href);
    } catch (error) {
        console.error('Error downloading legacy export:', error);
    }
}
