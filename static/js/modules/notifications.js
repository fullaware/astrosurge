// Notification system module

// Notification state
let allNotifications = [];
let unreadCount = 0;
const NOTIFICATION_FADE_DELAY = 5000; // 5 seconds before fade
const NOTIFICATIONS_STORAGE_KEY = 'astrosurge_notifications';

// Load notifications from localStorage on page load
function loadNotificationsFromStorage() {
    try {
        const stored = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            allNotifications = parsed.notifications || [];
            // Recalculate unread count
            unreadCount = allNotifications.filter(n => !n.read).length;
            updateNotificationBadge();
        }
    } catch (e) {
        console.error('Error loading notifications from storage:', e);
        allNotifications = [];
        unreadCount = 0;
    }
}

// Save notifications to localStorage
function saveNotificationsToStorage() {
    try {
        localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify({
            notifications: allNotifications,
            lastUpdated: new Date().toISOString()
        }));
    } catch (e) {
        console.error('Error saving notifications to storage:', e);
    }
}

// Render alerts (toast notifications that fade away)
function renderAlerts() {
    if (!window.dashboardData) return;
    
    const toastContainer = document.getElementById('alerts-toast-container');
    const newAlerts = window.dashboardData.alerts || [];
    
    // Add new alerts to all notifications
    newAlerts.forEach(alert => {
        // Create a unique key for this alert (title + message)
        const alertKey = `${alert.title}|${alert.message}`;
        
        // Check if this alert already exists (by title and message)
        const existing = allNotifications.find(n => 
            n.title === alert.title && n.message === alert.message
        );
        
        if (!existing) {
            const notification = {
                ...alert,
                id: Date.now() + Math.random(),
                key: alertKey,
                timestamp: new Date().toISOString(),
                read: false
            };
            allNotifications.unshift(notification); // Add to beginning
            unreadCount++;
            
            // Save to localStorage
            saveNotificationsToStorage();
            
            // Show as toast (auto-fade)
            showToastNotification(notification);
        }
    });
    
    // Update notification badge
    updateNotificationBadge();
    
    // Update notifications panel if open
    const panel = document.getElementById('notifications-panel');
    if (panel && panel.classList.contains('active')) {
        renderNotificationsPanel();
    }
}

// Show toast notification (fades away after delay)
function showToastNotification(notification) {
    const toastContainer = document.getElementById('alerts-toast-container');
    const toastItem = document.createElement('div');
    toastItem.className = 'alert-toast-item';
    toastItem.dataset.notificationId = notification.id;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${notification.type}`;
    alertElement.innerHTML = `
        <div class="alert-title">${notification.title}</div>
        <div class="alert-message">${notification.message}</div>
        <div class="alert-time">${formatNotificationTime(notification.timestamp)}</div>
    `;
    
    toastItem.appendChild(alertElement);
    toastContainer.appendChild(toastItem);
    
    // Auto-fade after delay
    setTimeout(() => {
        alertElement.classList.add('fading');
        setTimeout(() => {
            if (toastItem.parentNode) {
                toastItem.remove();
            }
        }, 500); // Fade animation duration
    }, NOTIFICATION_FADE_DELAY);
}

// Toggle notifications panel
function toggleNotificationsPanel() {
    const panel = document.getElementById('notifications-panel');
    panel.classList.toggle('active');
    
    if (panel.classList.contains('active')) {
        renderNotificationsPanel();
    }
}

// Render notifications panel
function renderNotificationsPanel() {
    const container = document.getElementById('notifications-list');
    container.innerHTML = '';
    
    if (allNotifications.length === 0) {
        container.innerHTML = '<p style="color: #888; text-align: center; padding: 2rem;">No notifications</p>';
        return;
    }
    
    // Sort by timestamp (newest first)
    const sortedNotifications = [...allNotifications].sort((a, b) => 
        new Date(b.timestamp) - new Date(a.timestamp)
    );
    
    sortedNotifications.forEach(notification => {
        const notificationElement = document.createElement('div');
        notificationElement.className = `alert alert-${notification.type} ${notification.read ? 'read' : ''}`;
        notificationElement.dataset.notificationId = notification.id;
        notificationElement.style.cursor = notification.read ? 'default' : 'pointer';
        notificationElement.innerHTML = `
            <div class="alert-title">${notification.title}</div>
            <div class="alert-message">${notification.message}</div>
            <div class="alert-time">${formatNotificationTime(notification.timestamp)}</div>
        `;
        
        // Mark as read on click (only if unread)
        if (!notification.read) {
            notificationElement.addEventListener('click', () => {
                markNotificationAsRead(notification.id);
            });
        }
        
        container.appendChild(notificationElement);
    });
    
    // Add "Mark all as read" button if there are unread notifications
    if (unreadCount > 0) {
        const markAllButton = document.createElement('button');
        markAllButton.textContent = 'Mark all as read';
        markAllButton.style.cssText = 'width: 100%; padding: 0.75rem; margin-top: 1rem; background: #00d4ff; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;';
        markAllButton.addEventListener('click', markAllNotificationsAsRead);
        container.appendChild(markAllButton);
    }
}

// Mark notification as read
function markNotificationAsRead(notificationId) {
    const notification = allNotifications.find(n => n.id === notificationId);
    if (notification && !notification.read) {
        notification.read = true;
        unreadCount = Math.max(0, unreadCount - 1);
        saveNotificationsToStorage(); // Persist the change
        updateNotificationBadge();
        renderNotificationsPanel();
    }
}

// Mark all as read
function markAllNotificationsAsRead() {
    allNotifications.forEach(n => {
        if (!n.read) {
            n.read = true;
        }
    });
    unreadCount = 0;
    saveNotificationsToStorage(); // Persist the change
    updateNotificationBadge();
    renderNotificationsPanel();
}

// Update notification badge
function updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    if (badge) {
        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

// Close notifications panel when clicking outside
document.addEventListener('click', (e) => {
    const panel = document.getElementById('notifications-panel');
    const bell = document.querySelector('.notification-bell');
    if (panel && panel.classList.contains('active') && 
        !panel.contains(e.target) && 
        bell && !bell.contains(e.target)) {
        panel.classList.remove('active');
    }
});

