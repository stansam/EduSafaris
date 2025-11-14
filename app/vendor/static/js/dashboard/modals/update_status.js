// Update Status Modal JavaScript
window.VBModalUpdateStatus = (function() {
    let currentBookingId = null;
    let currentStatus = null;

    // Valid status transitions
    const STATUS_TRANSITIONS = {
        'confirmed': ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'cancelled']
    };

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmUpdateStatusModal');
        const form = document.getElementById('vbmUpdateStatusForm');
        
        if (modal && form) {
            form.reset();
            const booking = window.VendorBookingsManager.getBooking(bookingId);
            if (booking) {
                currentStatus = booking.status;
                document.getElementById('vbmUpdateStatusBookingId').value = `#${booking.id}`;
                document.getElementById('vbmUpdateCurrentStatus').innerHTML = `<span class="vb-status-badge vb-status-${booking.status}">${booking.status.replace('_', ' ')}</span>`;
                populateStatusOptions(booking.status);
            }
            modal.style.display = 'flex';
        }
    }

    function close() {
        const modal = document.getElementById('vbmUpdateStatusModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
        currentStatus = null;
    }

    function populateStatusOptions(currentStatus) {
        const select = document.getElementById('vbmUpdateNewStatus');
        const validTransitions = STATUS_TRANSITIONS[currentStatus] || [];
        
        select.innerHTML = '<option value="">Select new status...</option>';
        
        const statusLabels = {
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled'
        };

        validTransitions.forEach(status => {
            const option = document.createElement('option');
            option.value = status;
            option.textContent = statusLabels[status] || status;
            select.appendChild(option);
        });
    }

    function handleStatusChange() {
        const newStatus = document.getElementById('vbmUpdateNewStatus').value;
        const cancellationGroup = document.getElementById('vbmUpdateCancellationReasonGroup');
        
        if (newStatus === 'cancelled') {
            cancellationGroup.style.display = 'block';
            document.getElementById('vbmUpdateCancellationReason').required = true;
        } else {
            cancellationGroup.style.display = 'none';
            document.getElementById('vbmUpdateCancellationReason').required = false;
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();
        
        const submitBtn = document.getElementById('vbmUpdateStatusSubmitBtn');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';

            const newStatus = document.getElementById('vbmUpdateNewStatus').value;
            const notes = document.getElementById('vbmUpdateNotes').value.trim();
            const cancellationReason = document.getElementById('vbmUpdateCancellationReason').value.trim();

            const requestData = { status: newStatus };
            if (notes) requestData.notes = notes;
            if (newStatus === 'cancelled' && cancellationReason) {
                requestData.cancellation_reason = cancellationReason;
            }

            const response = await fetch(window.VendorBookingsManager.apiEndpoints.updateStatus(currentBookingId), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.success) {
                showSuccessMessage('Booking status updated successfully!');
                close();
                window.VendorBookingsManager.reload();
            } else {
                throw new Error(result.error || 'Failed to update status');
            }
        } catch (error) {
            console.error('Error updating status:', error);
            showErrorMessage(error.message || 'Failed to update status. Please try again.');
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
    document.getElementById('vbmUpdateNewStatus')?.addEventListener('change', handleStatusChange);
    document.getElementById('vbmUpdateStatusForm')?.addEventListener('submit', handleSubmit);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmUpdateStatusModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalUpdateStatus.close();
    }
});