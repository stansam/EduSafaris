// Page Loader Management
window.addEventListener('load', function() {
    const loader = document.getElementById('pageLoader');
    if (loader) {
        setTimeout(() => {
            loader.classList.remove('active');
        }, 300);
    }
});

// Show loader on page navigation
window.addEventListener('beforeunload', function() {
    const loader = document.getElementById('pageLoader');
    if (loader) {
        loader.classList.add('active');
    }
});

// Prevent form double submission
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        let isSubmitting = false;
        form.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            isSubmitting = true;
            
            // Reset after 3 seconds as fallback
            setTimeout(() => {
                isSubmitting = false;
            }, 3000);
        });
    });
});

// Handle network errors globally
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Show user-friendly error message for network issues
    if (event.reason && event.reason.message && 
        (event.reason.message.includes('fetch') || 
            event.reason.message.includes('network'))) {
        showGlobalError('Network error. Please check your connection and try again.');
    }
});

// Global error notification function
function showGlobalError(message) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.innerHTML = `
        <span class="alert-icon">⚠</span>
        <div class="alert-content">
            <div class="alert-title">Error</div>
            <div>${message}</div>
        </div>
    `;
    
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

// Handle browser back button
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        // Page was loaded from cache (back button)
        window.location.reload();
    }
});

// Detect if user is offline
window.addEventListener('offline', function() {
    showGlobalError('You are currently offline. Please check your internet connection.');
});

window.addEventListener('online', function() {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.innerHTML = `
        <span class="alert-icon">✓</span>
        <div class="alert-content">
            <div class="alert-title">Success</div>
            <div>Connection restored!</div>
        </div>
    `;
    
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
});

// Utility: Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility: Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Utility: Format date
function formatDate(date, format = 'YYYY-MM-DD') {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day);
}

// Utility: Validate email format
function isValidEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
}

// Utility: Validate phone format
function isValidPhone(phone) {
    const cleaned = phone.replace(/[\s\-\(\)]/g, '');
    return /^\+?\d{10,15}$/.test(cleaned);
}

// Session timeout warning (optional)
let sessionTimeout;
let sessionWarningTimeout;
const SESSION_DURATION = 3600000; // 1 hour in milliseconds
const WARNING_BEFORE = 300000; // Warn 5 minutes before

function resetSessionTimeout() {
    clearTimeout(sessionTimeout);
    clearTimeout(sessionWarningTimeout);
    
    sessionWarningTimeout = setTimeout(() => {
        console.log('Session will expire soon');
        // Could show a warning modal here
    }, SESSION_DURATION - WARNING_BEFORE);
    
    sessionTimeout = setTimeout(() => {
        console.log('Session expired');
        // Could redirect to login or show session expired message
    }, SESSION_DURATION);
}

// Reset session timeout on user activity
['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
    document.addEventListener(event, throttle(resetSessionTimeout, 60000), true);
});

// Initialize session timeout
resetSessionTimeout();