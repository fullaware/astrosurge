// Auto-refresh and state management module

// Auto-refresh system state
let refreshInterval = null;
let isRefreshing = false;
let lastRefreshTime = null;
let refreshRetryCount = 0;
const REFRESH_INTERVAL = 30000; // 30 seconds
const MAX_RETRY_COUNT = 3;
const RETRY_DELAY = 5000; // 5 seconds

// User input preservation
let preservedState = {
    scrollPosition: 0,
    activeSection: 'overview',
    searchInputs: {},
    formInputs: {}
};

// Mission polling for active missions
let missionPollInterval = null;
let activeMissionIds = new Set();
let lastMissionStates = new Map();

// Auto refresh
function startAutoRefresh() {
    // Clear any existing interval
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Set up periodic refresh
    refreshInterval = setInterval(() => {
        if (!isRefreshing) {
            refreshDashboard(true); // Auto-refresh (not manual)
        }
    }, REFRESH_INTERVAL);
    
    // Update last refresh time display
    updateRefreshIndicator();
}

// Stop auto refresh
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    if (missionPollInterval) {
        clearInterval(missionPollInterval);
        missionPollInterval = null;
    }
}

// Mission polling for active missions
function startMissionPolling() {
    // Poll every 8 seconds for active missions
    missionPollInterval = setInterval(() => {
        pollActiveMissions();
    }, 8000);
    
    // Initial poll
    pollActiveMissions();
}

function stopMissionPolling() {
    if (missionPollInterval) {
        clearInterval(missionPollInterval);
        missionPollInterval = null;
    }
}

async function pollActiveMissions() {
    try {
        const response = await fetch('/api/missions');
        const missions = await response.json();
        
        // Filter active missions
        const activeMissions = missions.filter(m => {
            const phase = m.current_phase || m.status || '';
            return ['launched', 'traveling', 'mining_setup', 'mining', 'cargo_loading', 'returning'].includes(phase);
        });
        
        // Update active mission IDs
        const currentActiveIds = new Set(activeMissions.map(m => m._id || m.id));
        activeMissionIds = currentActiveIds;
        
        // Check for changes and highlight them
        activeMissions.forEach(mission => {
            const missionId = mission._id || mission.id;
            const previousState = lastMissionStates.get(missionId);
            
            if (previousState) {
                // Check for phase transitions
                if (previousState.current_phase !== mission.current_phase) {
                    highlightPhaseTransition(missionId, previousState.current_phase, mission.current_phase);
                    if (typeof showToastNotification === 'function') {
                        showToastNotification({
                            type: 'info',
                            title: 'Phase Transition',
                            message: `Mission "${mission.name}" moved from ${previousState.current_phase} to ${mission.current_phase}`
                        });
                    }
                }
                
                // Check for new events
                const currentEventCount = (mission.events || []).length;
                const previousEventCount = (previousState.events || []).length;
                if (currentEventCount > previousEventCount) {
                    highlightNewEvents(missionId);
                }
                
                // Check for cargo changes
                const currentCargo = sumCargo(mission.cargo || {});
                const previousCargo = sumCargo(previousState.cargo || {});
                if (Math.abs(currentCargo - previousCargo) > 0.1) {
                    highlightCargoUpdate(missionId);
                }
            }
            
            // Store current state
            lastMissionStates.set(missionId, {
                current_phase: mission.current_phase || mission.status,
                events: mission.events || [],
                cargo: mission.cargo || {}
            });
        });
        
        // Update mission cards if on missions section
        const missionsSection = document.getElementById('missions-section');
        if (missionsSection && missionsSection.classList.contains('active')) {
            if (typeof loadAllMissions === 'function') {
                loadAllMissions();
            }
        }
        
    } catch (error) {
        console.error('Error polling active missions:', error);
    }
}

function sumCargo(cargo) {
    return Object.values(cargo).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
}

function highlightPhaseTransition(missionId, oldPhase, newPhase) {
    const missionCard = document.querySelector(`[data-mission-id="${missionId}"]`);
    if (missionCard) {
        missionCard.classList.add('phase-transition');
        setTimeout(() => {
            missionCard.classList.remove('phase-transition');
        }, 2000);
    }
}

function highlightNewEvents(missionId) {
    const missionCard = document.querySelector(`[data-mission-id="${missionId}"]`);
    if (missionCard) {
        const badge = missionCard.querySelector('.new-events-badge');
        if (badge) {
            badge.style.display = 'block';
            badge.classList.add('pulse');
        } else {
            const newBadge = document.createElement('div');
            newBadge.className = 'new-events-badge pulse';
            newBadge.textContent = '!';
            newBadge.style.cssText = 'position: absolute; top: 10px; right: 10px; background: #ff4444; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem;';
            missionCard.style.position = 'relative';
            missionCard.appendChild(newBadge);
        }
    }
}

function highlightCargoUpdate(missionId) {
    const missionCard = document.querySelector(`[data-mission-id="${missionId}"]`);
    if (missionCard) {
        const cargoIndicator = missionCard.querySelector('.cargo-update-indicator');
        if (cargoIndicator) {
            cargoIndicator.classList.add('active');
            setTimeout(() => {
                cargoIndicator.classList.remove('active');
            }, 2000);
        }
    }
}

// Refresh dashboard with enhanced features
async function refreshDashboard(isAutoRefresh = false) {
    // Manual refresh (clicking button) - reset retry count
    if (!isAutoRefresh) {
        refreshRetryCount = 0;
    }
    // Prevent multiple simultaneous refreshes
    if (isRefreshing) {
        console.log('Refresh already in progress, skipping...');
        return;
    }
    
    isRefreshing = true;
    
    // Save current state before refresh
    preserveUserState();
    
    // Show refreshing indicator
    showRefreshIndicator('refreshing');
    
    try {
        // Attempt to load new data
        const success = await loadDashboardData();
        
        if (success) {
            // Restore user state before rendering
            restoreUserState();
            
            // Render updated data
            if (typeof renderDashboard === 'function') {
                renderDashboard();
            }
            if (typeof updateCharts === 'function') {
                updateCharts();
            }
            
            // Show success indicator
            showRefreshIndicator('updated');
            showRefreshStatus('Data updated successfully', 'success');
            
            // Reset retry count on success
            refreshRetryCount = 0;
            lastRefreshTime = new Date();
            
            // Highlight updated elements
            highlightDataUpdates();
            
        } else {
            // Handle failure
            handleRefreshFailure(isAutoRefresh);
        }
        
    } catch (error) {
        console.error('Error during refresh:', error);
        handleRefreshFailure(isAutoRefresh, error);
    } finally {
        isRefreshing = false;
        
        // Reset refresh indicator after delay
        setTimeout(() => {
            updateRefreshIndicator();
        }, 2000);
    }
}

// Preserve user state before refresh
function preserveUserState() {
    // Save scroll position
    preservedState.scrollPosition = window.scrollY || document.documentElement.scrollTop;
    
    // Save active section
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection) {
        preservedState.activeSection = activeSection.id.replace('-section', '');
    }
    
    // Save search inputs
    const searchInputs = document.querySelectorAll('input[type="text"][id*="search"], input[type="text"][id*="Search"]');
    searchInputs.forEach(input => {
        if (input.value) {
            preservedState.searchInputs[input.id] = input.value;
        }
    });
    
    // Save form inputs
    const formInputs = document.querySelectorAll('input[type="number"], input[type="text"], select');
    formInputs.forEach(input => {
        if (input.value && input.id) {
            preservedState.formInputs[input.id] = input.value;
        }
    });
    
    // Save notifications panel state
    const notificationsPanel = document.getElementById('notifications-panel');
    if (notificationsPanel) {
        preservedState.notificationsPanelOpen = notificationsPanel.classList.contains('active');
    }
}

// Restore user state after refresh
function restoreUserState() {
    // Restore scroll position
    setTimeout(() => {
        window.scrollTo(0, preservedState.scrollPosition);
    }, 100);
    
    // Restore active section
    if (preservedState.activeSection) {
        const targetSection = document.getElementById(preservedState.activeSection + '-section');
        if (targetSection) {
            // Update navigation
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
                if (item.getAttribute('href') === '#' + preservedState.activeSection) {
                    item.classList.add('active');
                }
            });
            
            // Show target section
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            targetSection.classList.add('active');
            
            // Load section data if needed
            if (typeof loadSectionData === 'function') {
                loadSectionData(preservedState.activeSection);
            }
        }
    }
    
    // Restore search inputs
    Object.keys(preservedState.searchInputs).forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = preservedState.searchInputs[inputId];
            // Trigger search if applicable
            if (input.oninput || input.addEventListener) {
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
    
    // Restore form inputs
    Object.keys(preservedState.formInputs).forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = preservedState.formInputs[inputId];
        }
    });
    
    // Restore notifications panel state
    if (preservedState.notificationsPanelOpen) {
        const notificationsPanel = document.getElementById('notifications-panel');
        if (notificationsPanel && !notificationsPanel.classList.contains('active')) {
            notificationsPanel.classList.add('active');
            if (typeof renderNotificationsPanel === 'function') {
                renderNotificationsPanel();
            }
        }
    }
}

// Show refresh indicator with state
function showRefreshIndicator(state) {
    const indicator = document.getElementById('refresh-indicator');
    const icon = document.getElementById('refresh-icon');
    if (!indicator || !icon) return;
    
    // Remove all state classes
    indicator.classList.remove('refreshing', 'updated', 'error');
    
    if (state === 'refreshing') {
        indicator.classList.add('refreshing');
        icon.textContent = '🔄';
        indicator.title = 'Refreshing...';
    } else if (state === 'updated') {
        indicator.classList.add('updated');
        icon.textContent = '✓';
        indicator.title = 'Data updated';
    } else if (state === 'error') {
        indicator.classList.add('error');
        icon.textContent = '⚠';
        indicator.title = 'Refresh failed - Click to retry';
    }
}

// Update refresh indicator with time
function updateRefreshIndicator() {
    const indicator = document.getElementById('refresh-indicator');
    const icon = document.getElementById('refresh-icon');
    if (!indicator || !icon) return;
    
    indicator.classList.remove('refreshing', 'updated', 'error');
    icon.textContent = '🔄';
    
    if (lastRefreshTime) {
        const secondsSinceRefresh = Math.floor((new Date() - lastRefreshTime) / 1000);
        const minutes = Math.floor(secondsSinceRefresh / 60);
        const seconds = secondsSinceRefresh % 60;
        
        if (minutes > 0) {
            indicator.title = `Last updated: ${minutes}m ${seconds}s ago - Click to refresh`;
        } else {
            indicator.title = `Last updated: ${seconds}s ago - Click to refresh`;
        }
    } else {
        indicator.title = 'Click to refresh';
    }
}

// Show refresh status message
function showRefreshStatus(message, type = 'info') {
    const statusEl = document.getElementById('refresh-status');
    if (!statusEl) return;
    
    statusEl.textContent = message;
    statusEl.className = `refresh-status show ${type}`;
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        statusEl.classList.remove('show');
    }, 3000);
}

// Handle refresh failure
function handleRefreshFailure(isAutoRefresh, error = null) {
    refreshRetryCount++;
    
    showRefreshIndicator('error');
    showRefreshStatus(
        error ? `Refresh failed: ${error.message}` : 'Failed to refresh data',
        'error'
    );
    
    // Auto-retry for auto-refreshes (up to max retries)
    if (isAutoRefresh && refreshRetryCount < MAX_RETRY_COUNT) {
        console.log(`Auto-retry in ${RETRY_DELAY / 1000} seconds... (${refreshRetryCount}/${MAX_RETRY_COUNT})`);
        setTimeout(() => {
            refreshDashboard(true);
        }, RETRY_DELAY);
    } else if (refreshRetryCount >= MAX_RETRY_COUNT) {
        console.error('Max retry count reached, stopping auto-refresh');
        stopAutoRefresh();
        showRefreshStatus('Auto-refresh stopped due to repeated failures', 'error');
    }
}

// Highlight data updates
function highlightDataUpdates() {
    // Add update indicator to metric cards
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach(card => {
        const indicator = document.createElement('div');
        indicator.className = 'data-update-indicator active';
        card.style.position = 'relative';
        
        // Remove existing indicator
        const existing = card.querySelector('.data-update-indicator');
        if (existing) {
            existing.remove();
        }
        
        card.appendChild(indicator);
        
        // Fade out indicator after 2 seconds
        setTimeout(() => {
            indicator.classList.remove('active');
            setTimeout(() => indicator.remove(), 300);
        }, 2000);
    });
}

// Enhanced load dashboard data with error handling
async function loadDashboardData() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch('/api/dashboard', {
            signal: controller.signal,
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        window.dashboardData = await response.json();
        return true;
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        
        if (error.name === 'AbortError') {
            console.error('Request timeout');
            return false;
        }
        
        // Use cached data if available
        if (window.dashboardData) {
            console.warn('Using cached data due to fetch failure');
            return true;
        }
        
        // Fallback to mock data
        if (typeof getMockData === 'function') {
            window.dashboardData = getMockData();
        }
        return false; // Indicate we're using fallback data
    }
}

