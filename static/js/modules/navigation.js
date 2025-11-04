// Navigation handling module

// Navigation handling
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const target = item.getAttribute('href').substring(1);
            
            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Show target section
            sections.forEach(section => section.classList.remove('active'));
            const targetSection = document.getElementById(target + '-section');
            if (targetSection) {
                targetSection.classList.add('active');
                
                // Load section-specific data
                if (typeof loadSectionData === 'function') {
                    loadSectionData(target);
                }
            }
        });
    });
}

// Load section-specific data
async function loadSectionData(section) {
    switch(section) {
        case 'missions':
            if (typeof loadAllMissions === 'function') {
                await loadAllMissions();
            }
            break;
        case 'mining':
            if (typeof loadMiningOperationsData === 'function') {
                await loadMiningOperationsData();
            }
            break;
        case 'fleet':
            if (typeof loadFleetData === 'function') {
                await loadFleetData();
            }
            break;
        case 'asteroids':
            if (typeof loadAsteroidBrowser === 'function') {
                await loadAsteroidBrowser();
            }
            break;
        case 'economics':
            if (typeof loadEconomicsData === 'function') {
                await loadEconomicsData();
            }
            break;
        case 'orbital':
            if (typeof loadOrbitalData === 'function') {
                await loadOrbitalData();
            }
            break;
        case 'risk':
            if (typeof loadRiskData === 'function') {
                await loadRiskData();
            }
            break;
        case 'market':
            if (typeof loadMarketData === 'function') {
                await loadMarketData();
            }
            break;
    }
}

