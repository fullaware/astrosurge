// Minimal app bootstrap for walkthrough + feedback

function initWalkthroughApp() {
    bindNavigation();
    loadDashboardPayload();
    loadCivilizationData();
    loadSimulationMetrics();
}

function bindNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');
    navItems.forEach(item => {
        item.addEventListener('click', (event) => {
            event.preventDefault();
            const target = item.getAttribute('href').substring(1);
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            sections.forEach(section => section.classList.remove('active'));
            const section = document.getElementById(`${target}-section`);
            if (section) {
                section.classList.add('active');
            }
            if (target === 'feedback') {
                loadCivilizationData();
            }
            if (target === 'metrics') {
                loadSimulationMetrics();
            }
        });
    });
}

async function loadDashboardPayload() {
    try {
        const response = await apiFetch('/dashboard');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        window.dashboardData = await response.json();
        if (typeof renderWalkthrough === 'function') {
            renderWalkthrough();
        }
    } catch (error) {
        console.error('Error loading dashboard payload:', error);
    }
}

async function loadSimulationMetrics() {
    try {
        const response = await apiFetch('/simulation/metrics');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        renderSimulationMetrics(data);
    } catch (error) {
        console.error('Error loading simulation metrics:', error);
    }
}

function renderSimulationMetrics(metrics) {
    // Update metric cards
    document.getElementById('metric-tech-index').textContent = metrics.tech_index.toFixed(4);
    document.getElementById('metric-energy-per-capita').textContent = metrics.energy_per_capita.toLocaleString();
    document.getElementById('metric-space-population').textContent = metrics.space_population.toLocaleString();
    document.getElementById('metric-resource-independence').textContent = (metrics.resource_independence * 100).toFixed(2) + '%';
    document.getElementById('metric-cultural-influence').textContent = (metrics.cultural_influence * 100).toFixed(2) + '%';
    document.getElementById('metric-ai-sentience').textContent = metrics.ai_sentience.toFixed(4);
    
    // Update detail values
    document.getElementById('metric-earth-population').textContent = metrics.earth_population.toLocaleString();
    document.getElementById('metric-earth-condition').textContent = metrics.earth_condition;
    document.getElementById('metric-ai-directive').textContent = metrics.ai_directive;
    document.getElementById('metric-total-revenue').textContent = '$' + metrics.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    document.getElementById('metric-success-rate').textContent = metrics.success_rate + '%';
}

document.addEventListener('DOMContentLoaded', initWalkthroughApp);
