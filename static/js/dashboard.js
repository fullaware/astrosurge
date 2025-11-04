// Dashboard has been modularized. All functionality is now in static/js/modules/*.js
// This file is a minimal compatibility stub that initializes the app.

document.addEventListener('DOMContentLoaded', () => {
    try {
        if (typeof initDashboard === 'function') initDashboard();
        if (typeof initNavigation === 'function') initNavigation();
    } catch (e) { 
        console.error('Error initializing dashboard:', e); 
    }
});
