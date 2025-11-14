// Cancel Booking Modal JavaScript
window.VBModalCancelBooking = (function() {
    let currentBookingId = null;

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmCancelBookingModal');
        const form = document.getElementById('vbmCancelBookingForm');
        
        if (modal && form) {
            form.reset();
            const booking = window.VendorBookingsManager.getBooking(bookingId);
            if (booking) {
                document.getElementById('vbmCancelBookingId').value = `#${booking.id}`;
                document.getElementById('vbmCancelCurrentStatus').innerHTML = `<span class="vb-status-badge vb-status-${booking.status}">${booking.status.replace('_', ' ')}</span>`;
            }
            document.getElementById('vbmCancelCharCount').textContent = '0';
            hideError();
            modal.style.display = 'flex';
        }
    }

    function close() {
        const modal = document.getElementById('vbmCancelBookingModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
    }

    function validateReason() {
        const reason = document.getElementById('vbmCancelReason').value.trim();
        const charCount = document.getElementById('vbmCancelCharCount');
        
        charCount.textContent = reason.length;

        if (reason.length < 10) {
            showError('Cancellation reason must be at least 10 characters long.');
            return false;
        }

        hideError();
        return true;
    }

    function showError(message) {
        const errorDiv = document.getElementById('vbmCancelReasonError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    function hideError() {
        const errorDiv = document.getElementById('vbmCancelReasonError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateReason()) {
            return;
        }
        
        // Double confirm action
        if (!confirm('Are you absolutely sure you want to cancel this booking? This action cannot be undone and will notify the trip organizer immediately.')) {
            return;
        }
        
        const submitBtn = document.getElementById('vbmCancelSubmitBtn');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cancelling...';

            const reason = document.getElementById('vbmCancelReason').value.trim();

            const response = await fetch(window.VendorBookingsManager.apiEndpoints.cancelBooking(currentBookingId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ reason })
            });

            const result = await response.json();

            if (result.success) {
                showSuccessMessage('Booking cancelled successfully. The trip organizer has been notified.');
                close();
                window.VendorBookingsManager.reload();
            } else {
                throw new Error(result.error || 'Failed to cancel booking');
            }
        } catch (error) {
            console.error('Error cancelling booking:', error);
            showErrorMessage(error.message || 'Failed to cancel booking. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    function showSuccessMessage(message) {
        alert(message);
    }

    function showErrorMessage(message) {
        alert(message);
    }

    // Attach event listeners
    document.getElementById('vbmCancelReason')?.addEventListener('input', validateReason);
    document.getElementById('vbmCancelBookingForm')?.addEventListener('submit', handleSubmit);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmCancelBookingModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalCancelBooking.close();
    }
});// Cancel Booking Modal JavaScript
window.VBModalCancelBooking = (function() {
    let currentBookingId = null;

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmCancelBookingModal');
        const form = document.getElementById('vbmCancelBookingForm');
        
        if (modal && form) {
            form.reset();
            const booking = window.VendorBookingsManager.getBooking(bookingId);
            if (booking) {
                document.getElementById('vbmCancelBookingId').value = `#${booking.id}`;
                document.getElementById('vbmCancelCurrentStatus').innerHTML = `<span class="vb-status-badge vb-status-${booking.status}">${booking.status.replace('_', ' ')}</span>`;
            }
            document.getElementById('vbmCancelCharCount').textContent = '0';
            hideError();
            modal.style.display = 'flex';
        }
    }

    function close() {
        const modal = document.getElementById('vbmCancelBookingModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
    }

    function validateReason() {
        const reason = document.getElementById('vbmCancelReason').value.trim();
        const charCount = document.getElementById('vbmCancelCharCount');
        
        charCount.textContent = reason.length;

        if (reason.length < 10) {
            showError('Cancellation reason must be at least 10 characters long.');
            return false;
        }

        hideError();
        return true;
    }

    function showError(message) {
        const errorDiv = document.getElementById('vbmCancelReasonError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    function hideError() {
        const errorDiv = document.getElementById('vbmCancelReasonError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateReason()) {
            return;
        }
        
        // Double confirm action
        if (!confirm('Are you absolutely sure you want to cancel this booking? This action cannot be undone and will notify the trip organizer immediately.')) {
            return;
        }
        
        const submitBtn = document.getElementById('vbmCancelSubmitBtn');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cancelling...';

            const reason = document.getElementById('vbmCancelReason').value.trim();

            const response = await fetch(window.VendorBookingsManager.apiEndpoints.cancelBooking(currentBookingId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ reason })
            });

            const result = await response.json();

            if (result.success) {
                showSuccessMessage('Booking cancelled successfully. The trip organizer has been notified.');
                close();
                window.VendorBookingsManager.reload();
            } else {
                throw new Error(result.error || 'Failed to cancel booking');
            }
        } catch (error) {
            console.error('Error cancelling booking:', error);
            showErrorMessage(error.message || 'Failed to cancel booking. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    function showSuccessMessage(message) {
        alert(message);
    }

    function showErrorMessage(message) {
        alert(message);
    }

    // Attach event listeners
    document.getElementById('vbmCancelReason')?.addEventListener('input', validateReason);
    document.getElementById('vbmCancelBookingForm')?.addEventListener('submit', handleSubmit);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmCancelBookingModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalCancelBooking.close();
    }
});