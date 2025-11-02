/**
 * Vendor Action Modals JavaScript
 * Handles all vendor-related modal interactions
 */

// Global state for modals
const VendorModalsState = {
    currentVendorId: null,
    currentBookingId: null,
    userTrips: [],
    selectedRating: 0
};

/* ============================================
   REQUEST QUOTE MODAL
   ============================================ */

async function openRequestQuoteModal(vendorId) {
    VendorModalsState.currentVendorId = vendorId;
    const modal = document.getElementById('requestQuoteModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadUserTrips('rqTripSelect');
    setupRequestQuoteForm();
}

function closeRequestQuoteModal() {
    const modal = document.getElementById('requestQuoteModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        document.getElementById('requestQuoteForm').reset();
    }
}

function setupRequestQuoteForm() {
    const form = document.getElementById('requestQuoteForm');
    if (!form) return;

    form.onsubmit = async (e) => {
        e.preventDefault();
        await handleRequestQuote();
    };
}

async function handleRequestQuote() {
    const btn = document.querySelector('#requestQuoteForm button[type="submit"]');
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    btn.disabled = true;

    try {
        const data = {
            vendor_id: VendorModalsState.currentVendorId,
            trip_id: document.getElementById('rqTripSelect').value,
            booking_type: document.getElementById('rqServiceType').value,
            service_description: document.getElementById('rqServiceDescription').value,
            special_requirements: document.getElementById('rqSpecialRequirements').value,
            notes: document.getElementById('rqNotes').value
        };

        const response = await fetch(`/api/teacher/vendors/${data.vendor_id}/quote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await handleModalApiResponse(response);

        if (result.success) {
            showModalNotification('Quote request sent successfully!', 'success');
            closeRequestQuoteModal();
            if (typeof refreshVendorsData === 'function') {
                refreshVendorsData();
            }
        } else {
            showModalNotification(result.error || 'Failed to send quote request', 'error');
        }
    } catch (error) {
        console.error('Error requesting quote:', error);
        showModalNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/* ============================================
   CREATE BOOKING MODAL
   ============================================ */

async function openCreateBookingModal(vendorId) {
    VendorModalsState.currentVendorId = vendorId;
    const modal = document.getElementById('createBookingModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadUserTrips('cbTripSelect');
    await loadVendorInfoForBooking(vendorId);
    setupCreateBookingForm();
}

function closeCreateBookingModal() {
    const modal = document.getElementById('createBookingModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        document.getElementById('createBookingForm').reset();
    }
}

async function loadVendorInfoForBooking(vendorId) {
    try {
        const response = await fetch(`/api/teacher/vendors/${vendorId}`);
        const data = await handleModalApiResponse(response);

        if (data.success) {
            document.getElementById('cbVendorName').textContent = data.data.business_name;
            document.getElementById('cbVendorType').textContent = data.data.business_type;
        }
    } catch (error) {
        console.error('Error loading vendor info:', error);
    }
}

function setupCreateBookingForm() {
    const form = document.getElementById('createBookingForm');
    if (!form) return;

    form.onsubmit = async (e) => {
        e.preventDefault();
        await handleCreateBooking();
    };
}

async function handleCreateBooking() {
    const btn = document.querySelector('#createBookingForm button[type="submit"]');
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
    btn.disabled = true;

    try {
        const data = {
            vendor_id: VendorModalsState.currentVendorId,
            trip_id: document.getElementById('cbTripSelect').value,
            booking_type: document.getElementById('cbServiceType').value,
            service_description: document.getElementById('cbServiceDescription').value,
            quoted_amount: parseFloat(document.getElementById('cbQuotedAmount').value),
            special_requirements: document.getElementById('cbSpecialRequirements').value,
            notes: document.getElementById('cbNotes').value
        };

        const response = await fetch('/api/teacher/vendors/bookings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await handleModalApiResponse(response);

        if (result.success) {
            showModalNotification('Booking created successfully!', 'success');
            closeCreateBookingModal();
            if (typeof refreshVendorsData === 'function') {
                refreshVendorsData();
            }
        } else {
            showModalNotification(result.error || 'Failed to create booking', 'error');
        }
    } catch (error) {
        console.error('Error creating booking:', error);
        showModalNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/* ============================================
   CONFIRM BOOKING MODAL
   ============================================ */

async function openConfirmBookingModal(bookingId) {
    VendorModalsState.currentBookingId = bookingId;
    const modal = document.getElementById('confirmBookingModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadBookingSummary(bookingId, 'cfmBookingSummary');
    setupConfirmBookingForm();
}

function closeConfirmBookingModal() {
    const modal = document.getElementById('confirmBookingModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        document.getElementById('confirmBookingForm').reset();
    }
}

function setupConfirmBookingForm() {
    const form = document.getElementById('confirmBookingForm');
    if (!form) return;

    form.onsubmit = async (e) => {
        e.preventDefault();
        await handleConfirmBooking();
    };
}

async function handleConfirmBooking() {
    const btn = document.querySelector('#confirmBookingForm button[type="submit"]');
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Confirming...';
    btn.disabled = true;

    try {
        const finalAmount = document.getElementById('cfmFinalAmount').value;
        const data = finalAmount ? { final_amount: parseFloat(finalAmount) } : {};

        const response = await fetch(
            `/api/teacher/vendors/bookings/${VendorModalsState.currentBookingId}/confirm`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }
        );

        const result = await handleModalApiResponse(response);

        if (result.success) {
            showModalNotification('Booking confirmed successfully!', 'success');
            closeConfirmBookingModal();
            if (typeof refreshVendorsData === 'function') {
                refreshVendorsData();
            }
        } else {
            showModalNotification(result.error || 'Failed to confirm booking', 'error');
        }
    } catch (error) {
        console.error('Error confirming booking:', error);
        showModalNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/* ============================================
   CANCEL BOOKING MODAL
   ============================================ */

async function openCancelBookingModal(bookingId) {
    VendorModalsState.currentBookingId = bookingId;
    const modal = document.getElementById('cancelBookingModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadBookingSummary(bookingId, 'cnlBookingSummary');
    setupCancelBookingForm();
}

function closeCancelBookingModal() {
    const modal = document.getElementById('cancelBookingModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        document.getElementById('cancelBookingForm').reset();
    }
}

function setupCancelBookingForm() {
    const form = document.getElementById('cancelBookingForm');
    if (!form) return;

    form.onsubmit = async (e) => {
        e.preventDefault();
        await handleCancelBooking();
    };
}

async function handleCancelBooking() {
    const btn = document.querySelector('#cancelBookingForm button[type="submit"]');
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cancelling...';
    btn.disabled = true;

    try {
        const data = {
            reason: document.getElementById('cnlReason').value
        };

        const response = await fetch(
            `/api/teacher/vendors/bookings/${VendorModalsState.currentBookingId}/cancel`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }
        );

        const result = await handleModalApiResponse(response);

        if (result.success) {
            showModalNotification('Booking cancelled successfully', 'success');
            closeCancelBookingModal();
            if (typeof refreshVendorsData === 'function') {
                refreshVendorsData();
            }
        } else {
            showModalNotification(result.error || 'Failed to cancel booking', 'error');
        }
    } catch (error) {
        console.error('Error cancelling booking:', error);
        showModalNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/* ============================================
   RATE VENDOR MODAL
   ============================================ */

async function openRateVendorModal(bookingId) {
    VendorModalsState.currentBookingId = bookingId;
    VendorModalsState.selectedRating = 0;
    const modal = document.getElementById('rateVendorModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadBookingForRating(bookingId);
    setupRateVendorForm();
    setupStarRating();
}

function closeRateVendorModal() {
    const modal = document.getElementById('rateVendorModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        document.getElementById('rateVendorForm').reset();
        VendorModalsState.selectedRating = 0;
        resetStarRating();
    }
}

async function loadBookingForRating(bookingId) {
    try {
        const response = await fetch(`/api/teacher/vendors/bookings/${bookingId}`);
        const data = await handleModalApiResponse(response);

        if (data.success) {
            const booking = data.data;
            const vendorInfo = document.getElementById('rvVendorInfo');
            
            vendorInfo.innerHTML = `
                <div class="vam-vendor-avatar">
                    <i class="fas fa-store"></i>
                </div>
                <div>
                    <h4>${booking.vendor?.business_name || 'Unknown Vendor'}</h4>
                    <span>${booking.booking_type}</span>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading booking:', error);
    }
}

function setupStarRating() {
    const stars = document.querySelectorAll('#rvStarRating i');
    
    stars.forEach(star => {
        star.addEventListener('click', () => {
            const rating = parseInt(star.dataset.rating);
            VendorModalsState.selectedRating = rating;
            document.getElementById('rvRating').value = rating;
            updateStarDisplay(rating);
        });

        star.addEventListener('mouseenter', () => {
            const rating = parseInt(star.dataset.rating);
            updateStarDisplay(rating);
        });
    });

    const container = document.getElementById('rvStarRating');
    container.addEventListener('mouseleave', () => {
        updateStarDisplay(VendorModalsState.selectedRating);
    });
}

function updateStarDisplay(rating) {
    const stars = document.querySelectorAll('#rvStarRating i');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.className = 'fas fa-star active';
        } else {
            star.className = 'far fa-star';
        }
    });
}

function resetStarRating() {
    const stars = document.querySelectorAll('#rvStarRating i');
    stars.forEach(star => {
        star.className = 'far fa-star';
    });
}

function setupRateVendorForm() {
    const form = document.getElementById('rateVendorForm');
    if (!form) return;

    form.onsubmit = async (e) => {
        e.preventDefault();
        await handleRateVendor();
    };
}

async function handleRateVendor() {
    if (VendorModalsState.selectedRating === 0) {
        showModalNotification('Please select a rating', 'error');
        return;
    }

    const btn = document.querySelector('#rateVendorForm button[type="submit"]');
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    btn.disabled = true;

    try {
        const data = {
            rating: VendorModalsState.selectedRating,
            title: document.getElementById('rvTitle').value,
            review: document.getElementById('rvReview').value,
            value_rating: document.getElementById('rvValueRating').value || null,
            safety_rating: document.getElementById('rvSafetyRating').value || null,
            organization_rating: document.getElementById('rvOrganizationRating').value || null,
            communication_rating: document.getElementById('rvCommunicationRating').value || null
        };

        // Convert empty strings to null
        Object.keys(data).forEach(key => {
            if (data[key] === '') data[key] = null;
            if (typeof data[key] === 'string' && !isNaN(data[key])) {
                data[key] = parseInt(data[key]);
            }
        });

        const response = await fetch(
            `/api/teacher/vendors/bookings/${VendorModalsState.currentBookingId}/rate`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }
        );

        const result = await handleModalApiResponse(response);

        if (result.success) {
            showModalNotification('Rating submitted successfully!', 'success');
            closeRateVendorModal();
            if (typeof refreshVendorsData === 'function') {
                refreshVendorsData();
            }
        } else {
            showModalNotification(result.error || 'Failed to submit rating', 'error');
        }
    } catch (error) {
        console.error('Error rating vendor:', error);
        showModalNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/* ============================================
   PAYMENT MODAL (M-PESA)
   ============================================ */

async function openPaymentModal(bookingId) {
    VendorModalsState.currentBookingId = bookingId;
    const modal = document.getElementById('paymentModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadPaymentSummary(bookingId);
    setupPaymentForm();
}

function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        document.getElementById('mpesaPaymentForm').reset();
        document.getElementById('pmtProcessingState').style.display = 'none';
    }
}

async function loadPaymentSummary(bookingId) {
    try {
        const response = await fetch(`/api/teacher/vendors/bookings/${bookingId}`);
        const data = await handleModalApiResponse(response);

        if (data.success) {
            const booking = data.data;
            const amount = booking.total_amount || booking.quoted_amount || 0;
            
            const summaryDiv = document.getElementById('pmtBookingSummary');
            summaryDiv.innerHTML = `
                <h3>${booking.vendor?.business_name || 'Vendor'}</h3>
                <p style="margin: 5px 0 15px; opacity: 0.9;">${booking.booking_type} - ${booking.trip?.title || 'Trip'}</p>
                <div class="vam-payment-amount">KES ${parseFloat(amount).toLocaleString()}</div>
            `;

            document.getElementById('pmtAmount').value = amount;
        }
    } catch (error) {
        console.error('Error loading payment summary:', error);
    }
}

function setupPaymentForm() {
    const form = document.getElementById('mpesaPaymentForm');
    if (!form) return;

    // Phone number formatting
    const phoneInput = document.getElementById('pmtPhoneNumber');
    phoneInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 12) value = value.slice(0, 12);
        e.target.value = value;
    });

    form.onsubmit = async (e) => {
        e.preventDefault();
        await handleInitiatePayment();
    };
}

async function handleInitiatePayment() {
    const phoneInput = document.getElementById('pmtPhoneNumber');
    const phoneNumber = phoneInput.value.trim();

    // Validate phone number format
    if (!/^254[0-9]{9}$/.test(phoneNumber)) {
        showModalNotification('Invalid phone number. Use format: 254XXXXXXXXX', 'error');
        phoneInput.focus();
        return;
    }

    const btn = document.getElementById('btnInitiatePayment');
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initiating...';
    btn.disabled = true;

    try {
        const data = {
            phone_number: phoneNumber,
            amount: parseFloat(document.getElementById('pmtAmount').value)
        };

        const response = await fetch(
            `/api/teacher/vendors/bookings/${VendorModalsState.currentBookingId}/payment/mpesa`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }
        );

        const result = await handleModalApiResponse(response);

        if (result.success) {
            document.getElementById('mpesaPaymentForm').style.display = 'none';
            document.getElementById('pmtProcessingState').style.display = 'block';
            btn.style.display = 'none';
            
            showModalNotification('Payment initiated! Please check your phone.', 'success');
            
            // Start checking payment status
            setTimeout(() => checkPaymentStatus(), 5000);
        } else {
            showModalNotification(result.error || 'Failed to initiate payment', 'error');
        }
    } catch (error) {
        console.error('Error initiating payment:', error);
        showModalNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function checkPaymentStatus() {
    try {
        const response = await fetch(
            `/api/teacher/vendors/bookings/${VendorModalsState.currentBookingId}/payment/status`
        );
        const data = await handleModalApiResponse(response);

        if (data.success) {
            const payments = data.data.payments || [];
            const latestPayment = payments[0];

            if (latestPayment) {
                if (latestPayment.status === 'completed') {
                    showModalNotification('Payment completed successfully!', 'success');
                    setTimeout(() => {
                        closePaymentModal();
                        if (typeof refreshVendorsData === 'function') {
                            refreshVendorsData();
                        }
                    }, 2000);
                } else if (latestPayment.status === 'failed') {
                    showModalNotification('Payment failed. Please try again.', 'error');
                    resetPaymentForm();
                } else {
                    // Still processing, check again
                    setTimeout(() => checkPaymentStatus(), 3000);
                }
            }
        }
    } catch (error) {
        console.error('Error checking payment status:', error);
    }
}

function resetPaymentForm() {
    document.getElementById('mpesaPaymentForm').style.display = 'block';
    document.getElementById('pmtProcessingState').style.display = 'none';
    document.getElementById('btnInitiatePayment').style.display = 'flex';
}

/* ============================================
   HELPER FUNCTIONS
   ============================================ */

async function loadUserTrips(selectId) {
    try {
        const response = await fetch('/api/participants/teacher/trips?status=active');
        const data = await handleModalApiResponse(response);

        if (data.success) {
            VendorModalsState.userTrips = data.data.trips || [];
            const select = document.getElementById(selectId);
            
            if (select) {
                select.innerHTML = '<option value="">Select a trip...</option>';
                
                VendorModalsState.userTrips.forEach(trip => {
                    const option = document.createElement('option');
                    option.value = trip.id;
                    option.textContent = `${trip.title} - ${formatModalDate(trip.start_date)}`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading trips:', error);
    }
}

async function loadBookingSummary(bookingId, containerId) {
    try {
        const response = await fetch(`/api/teacher/vendors/bookings/${bookingId}`);
        const data = await handleModalApiResponse(response);

        if (data.success) {
            const booking = data.data;
            const container = document.getElementById(containerId);
            
            container.innerHTML = `
                <h4><i class="fas fa-file-invoice"></i> Booking Details</h4>
                <div class="vam-summary-row">
                    <span class="vam-summary-label">Vendor:</span>
                    <span class="vam-summary-value">${booking.vendor?.business_name || 'N/A'}</span>
                </div>
                <div class="vam-summary-row">
                    <span class="vam-summary-label">Trip:</span>
                    <span class="vam-summary-value">${booking.trip?.title || 'N/A'}</span>
                </div>
                <div class="vam-summary-row">
                    <span class="vam-summary-label">Service Type:</span>
                    <span class="vam-summary-value" style="text-transform: capitalize;">${booking.booking_type}</span>
                </div>
                <div class="vam-summary-row">
                    <span class="vam-summary-label">Amount:</span>
                    <span class="vam-summary-value">KES ${parseFloat(booking.total_amount || booking.quoted_amount || 0).toLocaleString()}</span>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading booking summary:', error);
    }
}

async function handleModalApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'An error occurred');
    }
    return await response.json();
}

function formatModalDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function showModalNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `vam-notification vam-notification-${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 
                 'info-circle';
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    // Add styles if not already present
    if (!document.getElementById('vam-notification-styles')) {
        const style = document.createElement('style');
        style.id = 'vam-notification-styles';
        style.textContent = `
            .vam-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                background: #fff;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                display: flex;
                align-items: center;
                gap: 12px;
                z-index: 99999;
                animation: vamSlideIn 0.3s ease;
                max-width: 400px;
            }
            .vam-notification-success {
                border-left: 4px solid #27ae60;
                color: #27ae60;
            }
            .vam-notification-error {
                border-left: 4px solid #e74c3c;
                color: #e74c3c;
            }
            .vam-notification-info {
                border-left: 4px solid #3498db;
                color: #3498db;
            }
            .vam-notification i {
                font-size: 20px;
            }
            .vam-notification span {
                color: #2c3e50;
                font-weight: 600;
            }
            @keyframes vamSlideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'vamSlideIn 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Close modals on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('vam-modal-overlay')) {
        if (e.target.id === 'requestQuoteModal') closeRequestQuoteModal();
        else if (e.target.id === 'createBookingModal') closeCreateBookingModal();
        else if (e.target.id === 'confirmBookingModal') closeConfirmBookingModal();
        else if (e.target.id === 'cancelBookingModal') closeCancelBookingModal();
        else if (e.target.id === 'rateVendorModal') closeRateVendorModal();
        else if (e.target.id === 'paymentModal') closePaymentModal();
    }
});

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeRequestQuoteModal();
        closeCreateBookingModal();
        closeConfirmBookingModal();
        closeCancelBookingModal();
        closeRateVendorModal();
        closePaymentModal();
    }
});