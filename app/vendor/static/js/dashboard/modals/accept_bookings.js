// Accept Booking Modal JavaScript
window.VBModalAcceptBooking = (function() {
    let currentBookingId = null;

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmAcceptBookingModal');
        const form = document.getElementById('vbmAcceptBookingForm');
        
        if (modal && form) {
            form.reset();
            const booking = window.VendorBookingsManager.getBooking(bookingId);
            if (booking) {
                document.getElementById('vbmAcceptBookingId').value = `#${booking.id}`;
                document.getElementById('vbmAcceptQuotedAmount').textContent = formatCurrency(booking.quoted_amount, booking.currency);
            }
            modal.style.display = 'flex';
        }
    }

    function close() {
        const modal = document.getElementById('vbmAcceptBookingModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
    }

    async function handleSubmit(e) {
        e.preventDefault();
        
        const submitBtn = document.getElementById('vbmAcceptSubmitBtn');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            const finalAmount = document.getElementById('vbmAcceptFinalAmount').value;
            const notes = document.getElementById('vbmAcceptNotes').value.trim();

            const requestData = {};
            if (finalAmount) requestData.final_amount = parseFloat(finalAmount);
            if (notes) requestData.notes = notes;

            const response = await fetch(window.VendorBookingsManager.apiEndpoints.acceptBooking(currentBookingId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.success) {
                showSuccessMessage('Booking accepted successfully!');
                close();
                window.VendorBookingsManager.reload();
            } else {
                throw new Error(result.error || 'Failed to accept booking');
            }
        } catch (error) {
            console.error('Error accepting booking:', error);
            showErrorMessage(error.message || 'Failed to accept booking. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    function formatCurrency(amount, currency = 'USD') {
        if (!amount) return 'N/A';
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency }).format(amount);
    }

    function showSuccessMessage(message) {
        // Simple alert for now, can be replaced with better notification system
        alert(message);
    }

    function showErrorMessage(message) {
        alert(message);
    }

    // Attach form submit handler
    document.getElementById('vbmAcceptBookingForm')?.addEventListener('submit', handleSubmit);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmAcceptBookingModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalAcceptBooking.close();
    }
});