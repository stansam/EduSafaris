async function loadDashboardStats() {
    const statsContainer = document.querySelector('.teach-trips-stats-container');
    
    // Show loading state
    showStatsLoading(statsContainer);
    
    try {
        const response = await fetch('api/dashboard/stats', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin' // Include cookies for authentication
        });
        
        if (!response.ok) {
            if (response.status === 403) {
                throw new Error('Unauthorized access. Please ensure you have teacher permissions.');
            } else if (response.status === 401) {
                throw new Error('Session expired. Please log in again.');
            }
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load statistics');
        }
        
        // Populate the stats
        populateStats(data.stats);
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showStatsError(statsContainer, error.message);
    }
}

/**
 * Populate stats cards with data
 */
function populateStats(stats) {
    // Update Upcoming Trips
    const upcomingTripsValue = document.querySelector('.teach-trips-stat-card:nth-child(1) .teach-trips-stat-value');
    if (upcomingTripsValue) {
        upcomingTripsValue.textContent = stats.upcoming_trips || 0;
        animateValue(upcomingTripsValue, 0, stats.upcoming_trips || 0, 500);
    }
    
    // Update Confirmed Students
    const confirmedStudentsValue = document.querySelector('.teach-trips-stat-card:nth-child(2) .teach-trips-stat-value');
    if (confirmedStudentsValue) {
        confirmedStudentsValue.textContent = stats.confirmed_students || 0;
        animateValue(confirmedStudentsValue, 0, stats.confirmed_students || 0, 500);
    }
    
    // Update Consent Completion
    const consentCompletionValue = document.querySelector('.teach-trips-stat-card:nth-child(3) .teach-trips-stat-value');
    if (consentCompletionValue) {
        consentCompletionValue.textContent = `${stats.consent_completion || 0}%`;
        animateValue(consentCompletionValue, 0, stats.consent_completion || 0, 500, '%');
    }
    
    // Remove any existing error/loading states
    const statsContainer = document.querySelector('.teach-trips-stats-container');
    if (statsContainer) {
        statsContainer.classList.remove('stats-loading', 'stats-error');
        hideStatsLoading(statsContainer);
    }
}

/**
 * Show loading state for stats
 */
function showStatsLoading(container) {
    if (!container) return;
    
    container.classList.add('stats-loading');
    
    // Add loading spinner or placeholder
    const statValues = container.querySelectorAll('.teach-trips-stat-value');
    statValues.forEach(value => {
        value.style.opacity = '0.5';
        value.textContent = '...';
    });
}

function hideStatsLoading(container) {
    if (!container) return;

    container.classList.remove('stats-loading');

    const statValues = container.querySelectorAll('.teach-trips-stat-value');
    statValues.forEach(value => {
        value.style.opacity = '1';
    });
}

/**
 * Show error state for stats
 */
function showStatsError(container, errorMessage) {
    if (!container) return;
    
    container.classList.add('stats-error');
    
    // Display error message
    const statValues = container.querySelectorAll('.teach-trips-stat-value');
    statValues.forEach(value => {
        value.style.opacity = '1';
        value.textContent = '--';
    });
    
    // Show error notification (optional - customize based on your notification system)
    showNotification('error', `Failed to load statistics: ${errorMessage}`);
}

/**
 * Animate number changes for better UX
 */
function animateValue(element, start, end, duration, suffix = '') {
    if (!element) return;
    
    const startTime = performance.now();
    const isDecimal = end % 1 !== 0;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutQuad = progress * (2 - progress);
        const current = start + (end - start) * easeOutQuad;
        
        if (isDecimal) {
            element.textContent = current.toFixed(1) + suffix;
        } else {
            element.textContent = Math.floor(current) + suffix;
        }
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            // Ensure final value is exact
            element.textContent = (isDecimal ? end.toFixed(1) : end) + suffix;
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Simple notification function (customize based on your notification system)
 */
function showNotification(type, message) {
    // Replace this with your existing notification system
    console[type === 'error' ? 'error' : 'log'](message);
    
    // Example: Create a simple toast notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#f44336' : '#4caf50'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 10000;
        max-width: 400px;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

/**
 * Initialize dashboard stats on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
    
    // Optional: Refresh stats periodically (every 5 minutes)
    setInterval(loadDashboardStats, 5 * 60 * 1000);
});

/**
 * Optional: Expose refresh function for manual refresh
 */
window.refreshDashboardStats = loadDashboardStats;