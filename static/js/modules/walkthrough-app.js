// Minimal app bootstrap for walkthrough + feedback

function initWalkthroughApp() {
    bindNavigation();
    loadDashboardPayload();
    loadCivilizationData();
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

document.addEventListener('DOMContentLoaded', initWalkthroughApp);
