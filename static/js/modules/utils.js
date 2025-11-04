// Utility functions

// Format currency
function formatCurrency(amount) {
    if (amount >= 1000000000) {
        return '$' + (amount / 1000000000).toFixed(1) + 'B';
    } else if (amount >= 1000000) {
        return '$' + (amount / 1000000).toFixed(1) + 'M';
    } else if (amount >= 1000) {
        return '$' + (amount / 1000).toFixed(1) + 'K';
    } else {
        return '$' + amount.toFixed(0);
    }
}

// Calculate mission progress
function calculateMissionProgress(mission) {
    if (mission.status === 'completed') return 100;
    const phase = mission.current_phase || mission.status;
    if (phase === 'planning') return 10;
    if (phase === 'launched' || phase === 'traveling') return 30;
    if (phase === 'mining') return 60;
    if (phase === 'returning') return 90;
    return 0;
}

// Calculate cargo weight
function calculateCargoWeight(cargo) {
    return Object.values(cargo).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
}

// Get asteroid class badge HTML
function getAsteroidClassBadge(asteroidClass) {
    const classColors = {
        'C': { bg: 'rgba(0, 212, 255, 0.2)', border: '#00d4ff', label: 'C-Type' },
        'S': { bg: 'rgba(0, 255, 136, 0.2)', border: '#00ff88', label: 'S-Type' },
        'M': { bg: 'rgba(255, 170, 0, 0.2)', border: '#ffaa00', label: 'M-Type' }
    };
    const style = classColors[asteroidClass] || classColors['C'];
    return `<span style="padding: 0.2rem 0.5rem; background: ${style.bg}; border: 1px solid ${style.border}; border-radius: 4px; font-size: 0.7rem; color: ${style.border}; font-weight: bold;">${style.label}</span>`;
}

// Get progress color based on percentage
function getProgressColor(percentage) {
    const pct = parseFloat(percentage);
    if (pct < 50) return '#00ff88'; // Green
    if (pct < 80) return '#ffaa00'; // Yellow
    return '#ff4444'; // Red
}

// Format notification time
function formatNotificationTime(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return time.toLocaleDateString();
}

