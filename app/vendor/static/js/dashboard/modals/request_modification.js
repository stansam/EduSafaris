window.VBModalRequestModification = (function() {
    let currentBookingId = null;
    let currentBooking = null;

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmRequestModificationModal');
        const form = document.getElementById('vbmRequestModificationForm');
        
        if (modal && form) {
            form.reset();
            currentBooking = window.VendorBookingsManager.getBooking(bookingId);
            if (currentBooking) {
                document.getElementById('vbmModifyBookingId').value = `#${currentBooking.id}`;
                
                // Set current dates and amount for reference
                const startDate = currentBooking.service_start_date ? formatDate(currentBooking.service_start_date) : 'N/A';
                const endDate = currentBooking.service_end_date ? formatDate(currentBooking.service_end_date) : 'N/A';
                document.getElementById('vbmModifyCurrentDates').textContent = `${startDate} - ${endDate}`;
                document.getElementById('vbmModifyCurrentAmount').textContent = formatCurrency(currentBooking.total_amount, currentBooking.currency);
            }
            document.getElementById('vbmModifyCharCount').textContent = '0';
            hideAllSections();
            hideError();
            modal.style.display = 'flex';
        }
    }

    function close() {
        const modal = document.getElementById('vbmRequestModificationModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
        currentBooking = null;
    }

    function hideAllSections() {
        document.getElementById('vbmModifyDatesSection').style.display = 'none';
        document.getElementById('vbmModifyPricingSection').style.display = 'none';
    }

    function handleTypeChange() {
        const type = document.getElementById('vbmModifyType').value;
        hideAllSections();

        if (type === 'dates') {
            document.getElementById('vbmModifyDatesSection').style.display = 'block';
        } else if (type === 'pricing') {
            document.getElementById('vbmModifyPricingSection').style.display = 'block';
        }
    }

    function validateDetails() {
        const details = document.getElementById('vbmModifyDetails').value.trim();
        const charCount = document.getElementById('vbmModifyCharCount');
        
        charCount.textContent = details.length;

        if (details.length < 20) {
            showError('Modification details must be at least 20 characters long.');
            return false;
        }

        hideError();
        return true;
    }

    function showError(message) {
        const errorDiv = document.getElementById('vbmModifyDetailsError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    function hideError() {
        const errorDiv = document.getElementById('vbmModifyDetailsError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateDetails()) {
            return;
        }
        
        const submitBtn = document.getElementById('vbmModifySubmitBtn');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

            const modificationType = document.getElementById('vbmModifyType').value;
            const details = document.getElementById('vbmModifyDetails').value.trim();

            const requestData = {
                modification_type: modificationType,
                details: details
            };

            // Add type-specific data
            if (modificationType === 'dates') {
                const startDate = document.getElementById('vbmModifySuggestedStartDate').value;
                const endDate = document.getElementById('vbmModifySuggestedEndDate').value;
                
                if (startDate || endDate) {
                    requestData.suggested_dates = {};
                    if (startDate) requestData.suggested_dates.start_date = startDate;
                    if (endDate) requestData.suggested_dates.end_date = endDate;
                }
            } else if (modificationType === 'pricing') {
                const suggestedAmount = document.getElementById('vbmModifySuggestedAmount').value;
                if (suggestedAmount) {
                    requestData.suggested_amount = parseFloat(suggestedAmount);
                }
            }

            const response = await fetch(window.VendorBookingsManager.apiEndpoints.requestModification(currentBookingId), {
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
                showSuccessMessage('Modification request sent successfully! The trip organizer will review your request.');
                close();
                window.VendorBookingsManager.reload();
            } else {
                throw new Error(result.error || 'Failed to send modification request');
            }
        } catch (error) {
            console.error('Error sending modification request:', error);
            showErrorMessage(error.message || 'Failed to send modification request. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function formatCurrency(amount, currency = 'USD') {
        if (!amount) return 'N/A';
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency }).format(amount);
    }

    function showSuccessMessage(message) {
        alert(message);
    }

    function showErrorMessage(message) {
        alert(message);
    }

    // Attach event listeners
    document.getElementById('vbmModifyType')?.addEventListener('change', handleTypeChange);
    document.getElementById('vbmModifyDetails')?.addEventListener('input', validateDetails);
    document.getElementById('vbmRequestModificationForm')?.addEventListener('submit', handleSubmit);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmRequestModificationModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalRequestModification.close();
    }
});