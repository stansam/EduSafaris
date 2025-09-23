/**
 * Vendor-related JavaScript functionality
 */

let currentBookingId = null;

/**
 * Accept a booking request
 */
function acceptBooking(bookingId) {
    currentBookingId = bookingId;
    document.getElementById('acceptModal').style.display = 'block';
}

/**
 * Decline a booking request
 */
function declineBooking(bookingId) {
    currentBookingId = bookingId;
    document.getElementById('declineModal').style.display = 'block';
}

/**
 * Close any open modal
 */
function closeModal() {
    document.getElementById('acceptModal').style.display = 'none';
    document.getElementById('declineModal').style.display = 'none';
    currentBookingId = null;
}

/**
 * Handle accept booking form submission
 */
document.getElementById('acceptForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const finalAmount = document.getElementById('finalAmount').value;
    
    try {
        const response = await fetch(`/vendors/bookings/${currentBookingId}/accept`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                final_amount: finalAmount ? parseFloat(finalAmount) : null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Booking accepted successfully!', 'success');
            // Reload page to update the booking lists
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showNotification(data.error || 'Failed to accept booking', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    }
    
    closeModal();
});

/**
 * Handle decline booking form submission
 */
document.getElementById('declineForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const reason = document.getElementById('declineReason').value;
    
    try {
        const response = await fetch(`/vendors/bookings/${currentBookingId}/decline`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Booking declined', 'info');
            // Reload page to update the booking lists
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showNotification(data.error || 'Failed to decline booking', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    }
    
    closeModal();
});

/**
 * Submit vendor rating (AJAX)
 */
async function submitRating(bookingId, rating, review = '') {
    try {
        const response = await fetch(`/vendors/rate/${bookingId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                rating: rating,
                review: review
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Rating submitted successfully!', 'success');
            // Update the vendor rating display
            updateVendorRatingDisplay(data.vendor_rating);
            // Hide or disable the rating form
            hideRatingForm(bookingId);
        } else {
            showNotification(data.error || 'Failed to submit rating', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    }
}

/**
 * Create interactive star rating system
 */
function createStarRating(containerId, bookingId, currentRating = 0) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    for (let i = 1; i <= 5; i++) {
        const star = document.createElement('span');
        star.className = 'rating-star';
        star.innerHTML = i <= currentRating ? '★' : '☆';
        star.style.cursor = 'pointer';
        star.style.fontSize = '24px';
        star.style.color = i <= currentRating ? '#f39c12' : '#ddd';
        star.style.marginRight = '5px';
        
        star.addEventListener('click', () => {
            // Update visual feedback
            const stars = container.querySelectorAll('.rating-star');
            stars.forEach((s, index) => {
                s.innerHTML = index < i ? '★' : '☆';
                s.style.color = index < i ? '#f39c12' : '#ddd';
            });
            
            // Store the rating for submission
            container.dataset.rating = i;
        });
        
        container.appendChild(star);
    }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 4px;
        color: white;
        font-weight: 600;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#27ae60',
        error: '#e74c3c',
        info: '#3498db',
        warning: '#f39c12'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

/**
 * Update vendor rating display
 */
function updateVendorRatingDisplay(newRating) {
    const ratingDisplays = document.querySelectorAll('.vendor-rating');
    ratingDisplays.forEach(display => {
        const stars = display.querySelector('.stars');
        if (stars) {
            let starHTML = '';
            for (let i = 1; i <= 5; i++) {
                starHTML += i <= newRating ? '★' : '☆';
            }
            stars.innerHTML = starHTML;
        }
        
        const ratingText = display.querySelector('.rating-text');
        if (ratingText) {
            ratingText.textContent = `${newRating.toFixed(1)} stars`;
        }
    });
}

/**
 * Hide rating form after submission
 */
function hideRatingForm(bookingId) {
    const form = document.getElementById(`rating-form-${bookingId}`);
    if (form) {
        form.style.display = 'none';
        
        // Show a "Thank you" message
        const thankYou = document.createElement('div');
        thankYou.style.cssText = 'color: #27ae60; font-weight: 600; margin-top: 10px;';
        thankYou.textContent = 'Thank you for your rating!';
        form.parentNode.insertBefore(thankYou, form.nextSibling);
    }
}

/**
 * Filter vendor directory
 */
function filterVendors() {
    const searchTerm = document.getElementById('vendor-search')?.value.toLowerCase() || '';
    const typeFilter = document.getElementById('type-filter')?.value || '';
    const ratingFilter = parseFloat(document.getElementById('rating-filter')?.value || 0);
    
    const vendorCards = document.querySelectorAll('.vendor-card');
    
    vendorCards.forEach(card => {
        const name = card.querySelector('.vendor-name')?.textContent.toLowerCase() || '';
        const description = card.querySelector('.vendor-description')?.textContent.toLowerCase() || '';
        const type = card.dataset.type || '';
        const rating = parseFloat(card.dataset.rating || 0);
        
        const matchesSearch = !searchTerm || name.includes(searchTerm) || description.includes(searchTerm);
        const matchesType = !typeFilter || type === typeFilter;
        const matchesRating = rating >= ratingFilter;
        
        card.style.display = matchesSearch && matchesType && matchesRating ? 'block' : 'none';
    });
}

/**
 * Initialize vendor functionality when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
        }
        @keyframes slideOut {
            from { transform: translateX(0); }
            to { transform: translateX(100%); }
        }
        .rating-star {
            transition: color 0.2s ease;
        }
        .rating-star:hover {
            transform: scale(1.1);
        }
    `;
    document.head.appendChild(style);
    
    // Initialize any existing star ratings
    const ratingContainers = document.querySelectorAll('[data-rating-for]');
    ratingContainers.forEach(container => {
        const bookingId = container.dataset.ratingFor;
        createStarRating(container.id, bookingId);
    });
    
    // Close modals when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    });
});

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        submitRating,
        createStarRating,
        showNotification,
        acceptBooking,
        declineBooking
    };
}