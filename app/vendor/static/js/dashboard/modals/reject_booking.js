// Reject Booking Modal JavaScript
window.VBModalRejectBooking = (function() {
    let currentBookingId = null;

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmRejectBookingModal');
        const form = document.getElementById('vbmRejectBookingForm');
        
        if (modal && form) {
            form.reset();
            const booking = window.VendorBookingsManager.getBooking(bookingId);
            if (booking) {
                document.getElementById('vbmRejectBookingId').value = `#${booking.id}`;
            }
            document.getElementById('vbmRejectCharCount').textContent = '0';
            hideError();
            modal.style.display = 'flex';
        }
    }

    function close() {
        const modal = document.getElementById('vbmRejectBookingModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
    }

    function validateReason() {
        const reason = document.getElementById('vbmRejectReason').value.trim();
        const charCount = document.getElementById('vbmRejectCharCount');
        const errorDiv = document.getElementById('vbmRejectReasonError');
        
        charCount.textContent = reason.length;

        if (reason.length < 10) {
            showError('Rejection reason must be at least 10 characters long.');
            return false;
        }

        hideError();
        return true;
    }

    function showError(message) {
        const errorDiv = document.getElementById('vbmRejectReasonError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    function hideError() {
        const errorDiv = document.getElementById('vbmRejectReasonError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateReason()) {
            return;
        }
        
        const submitBtn = document.getElementById('vbmRejectSubmitBtn');
        const originalText = submitBtn.innerHTML;
        
        // Confirm action
        if (!confirm('Are you sure you want to reject this booking request? This action cannot be undone.')) {
            return;
        }
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            const reason = document.getElementById('vbmRejectReason').value.trim();

            const response = await fetch(window.VendorBookingsManager.apiEndpoints.rejectBooking(currentBookingId), {
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
                showSuccessMessage('Booking rejected successfully.');
                close();
                window.VendorBookingsManager.reload();
            } else {
                throw new Error(result.error || 'Failed to reject booking');
            }
        } catch (error) {
            console.error('Error rejecting booking:', error);
            showErrorMessage(error.message || 'Failed to reject booking. Please try again.');
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
    document.getElementById('vbmRejectReason')?.addEventListener('input', validateReason);
    document.getElementById('vbmRejectBookingForm')?.addEventListener('submit', handleSubmit);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmRejectBookingModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalRejectBooking.close();
    }
});