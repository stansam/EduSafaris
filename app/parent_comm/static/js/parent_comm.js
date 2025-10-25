// Parent Communication JavaScript

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize signature canvas if present
    initializeSignatureCanvas();
    
    // Initialize SocketIO for real-time notifications
    initializeSocketIO();
    
    // Initialize notification handlers
    initializeNotifications();
    
    // Initialize form validations
    initializeFormValidations();
});

// Signature Canvas Implementation
function initializeSignatureCanvas() {
    const canvas = document.getElementById('signature-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let hasSignature = false;
    
    // Set canvas styles
    canvas.style.border = '2px solid #ddd';
    canvas.style.borderRadius = '5px';
    canvas.style.backgroundColor = '#fff';
    canvas.style.cursor = 'crosshair';
    
    // Drawing functions
    function startDrawing(e) {
        isDrawing = true;
        hasSignature = true;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        ctx.beginPath();
        ctx.moveTo(x, y);
    }
    
    function draw(e) {
        if (!isDrawing) return;
        
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#000';
        ctx.lineTo(x, y);
        ctx.stroke();
    }
    
    function stopDrawing() {
        if (!isDrawing) return;
        isDrawing = false;
        ctx.beginPath();
    }
    
    // Touch support for mobile devices
    function getTouchPos(e) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: e.touches[0].clientX - rect.left,
            y: e.touches[0].clientY - rect.top
        };
    }
    
    // Mouse events
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
    
    // Touch events
    canvas.addEventListener('touchstart', function(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    });
    
    canvas.addEventListener('touchmove', function(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    });
    
    canvas.addEventListener('touchend', function(e) {
        e.preventDefault();
        const mouseEvent = new MouseEvent('mouseup', {});
        canvas.dispatchEvent(mouseEvent);
    });
    
    // Clear button
    const clearBtn = document.getElementById('clear-canvas');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            hasSignature = false;
            document.getElementById('signature_image').value = '';
            
            // Show feedback
            showTemporaryMessage('Signature cleared', 'info');
        });
    }
    
    // Save signature button
    const saveBtn = document.getElementById('save-signature');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            if (!hasSignature) {
                showTemporaryMessage('Please draw your signature first', 'warning');
                return;
            }
            
            // Convert canvas to base64
            const dataURL = canvas.toDataURL('image/png');
            document.getElementById('signature_image').value = dataURL;
            
            // Clear typed signature if digital signature is used
            const typedSignature = document.getElementById('signature_text');
            if (typedSignature) {
                typedSignature.value = '';
            }
            
            showTemporaryMessage('Signature saved successfully', 'success');
        });
    }
}

// SocketIO Implementation
function initializeSocketIO() {
    if (typeof io === 'undefined') return;
    
    const socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        // Join parent-specific room
        socket.emit('join_parent_room');
    });
    
    socket.on('room_joined', function(data) {
        console.log('Joined room:', data.room);
    });
    
    socket.on('new_notification', function(notification) {
        console.log('New notification received:', notification);
        
        // Update notification badge
        updateNotificationBadge();
        
        // Show toast notification
        showNotificationToast(notification);
        
        // If we're on the notifications page, refresh it
        if (window.location.pathname.includes('/notifications')) {
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
}

// Notification handlers
function initializeNotifications() {
    // Mark as read buttons
    const markReadButtons = document.querySelectorAll('.mark-read-btn');
    markReadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const notificationId = this.dataset.id;
            markNotificationAsRead(notificationId, this);
        });
    });
    
    // Update notification badge on page load
    updateNotificationBadge();
}

function markNotificationAsRead(notificationId, buttonElement) {
    fetch(`/parents/notifications/mark-read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            const notificationCard = buttonElement.closest('.notification-card');
            notificationCard.classList.remove('unread');
            buttonElement.remove();
            
            // Update badge
            updateNotificationBadge();
            
            showTemporaryMessage('Notification marked as read', 'success');
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
        showTemporaryMessage('Error updating notification', 'error');
    });
}

function updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;
    
    // Count unread notifications on current page
    const unreadCount = document.querySelectorAll('.notification-card.unread').length;
    
    if (unreadCount > 0) {
        badge.textContent = unreadCount;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }
}

function showNotificationToast(notification) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'notification-toast';
    toast.innerHTML = `
        <div class="toast-header">
            <strong>${notification.title}</strong>
            <button type="button" class="close-toast">&times;</button>
        </div>
        <div class="toast-body">
            ${notification.message.length > 100 ? notification.message.substring(0, 100) + '...' : notification.message}
        </div>
    `;
    
    // Add to page
    document.body.appendChild(toast);
    
    // Show with animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        removeToast(toast);
    }, 5000);
    
    // Close button
    toast.querySelector('.close-toast').addEventListener('click', () => {
        removeToast(toast);
    });
}

function removeToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// Form validations
function initializeFormValidations() {
    const consentForm = document.getElementById('consent-form');
    if (consentForm) {
        consentForm.addEventListener('submit', function(e) {
            if (!validateConsentForm()) {
                e.preventDefault();
                return false;
            }
        });
    }
}

function validateConsentForm() {
    const agreement = document.getElementById('consent-agreement');
    if (agreement && !agreement.checked) {
        showTemporaryMessage('Please check the consent agreement box', 'warning');
        agreement.focus();
        return false;
    }
    
    const signatureImage = document.getElementById('signature_image').value;
    const signatureText = document.getElementById('signature_text').value.trim();
    
    if (!signatureImage && !signatureText) {
        showTemporaryMessage('Please provide either a digital signature or type your name', 'warning');
        return false;
    }
    
    return true;
}

// Utility functions
function getCSRFToken() {
    const token = document.querySelector('meta[name=csrf-token]');
    return token ? token.getAttribute('content') : '';
}

function showTemporaryMessage(message, type = 'info') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.temp-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type} temp-message`;
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '9999';
    messageDiv.style.minWidth = '300px';
    messageDiv.innerHTML = message;
    
    document.body.appendChild(messageDiv);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 3000);
}

momentDiv = document.getElementById("generated_time")
if(momentDiv){
    momentDiv.textContent = moment().format("MMMM Do, YYYY [at] h:mm A");
}

// Export functions for external use
window.ParentComm = {
    markNotificationAsRead,
    showNotificationToast,
    updateNotificationBadge
};