window.VBModalBookingDetails = (function() {
    let currentBookingId = null;

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmBookingDetailsModal');
        if (modal) {
            modal.style.display = 'flex';
            loadBookingDetails(bookingId);
        }
    }

    function close() {
        const modal = document.getElementById('vbmBookingDetailsModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
    }

    async function loadBookingDetails(bookingId) {
        const loading = document.getElementById('vbmDetailsLoading');
        const content = document.getElementById('vbmDetailsContent');
        
        if (loading) loading.style.display = 'block';
        if (content) content.style.display = 'none';

        try {
            const response = await fetch(window.VendorBookingsManager.apiEndpoints.getBookingDetails(bookingId), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error('Failed to load booking details');
            }

            const result = await response.json();
            if (result.success) {
                populateBookingDetails(result.data);
                if (loading) loading.style.display = 'none';
                if (content) content.style.display = 'block';
            } else {
                throw new Error(result.error || 'Failed to load booking details');
            }
        } catch (error) {
            console.error('Error loading booking details:', error);
            alert('Failed to load booking details. Please try again.');
            close();
        }
    }

    function populateBookingDetails(booking) {
        // Header info
        document.getElementById('vbmDetailBookingId').textContent = `#${booking.id}`;
        document.getElementById('vbmDetailStatus').innerHTML = `<span class="vb-status-badge vb-status-${booking.status}">${booking.status?.replace('_', ' ')}</span>`;
        document.getElementById('vbmDetailPaymentStatus').innerHTML = `<span class="vb-payment-badge vb-payment-${booking.payment_status}">${booking.payment_status?.replace('_', ' ')}</span>`;

        // Trip information
        document.getElementById('vbmDetailTripTitle').textContent = booking.trip?.title || 'N/A';
        document.getElementById('vbmDetailTripDates').textContent = booking.trip?.start_date && booking.trip?.end_date 
            ? `${formatDate(booking.trip.start_date)} - ${formatDate(booking.trip.end_date)}` 
            : 'N/A';
        document.getElementById('vbmDetailOrganizer').textContent = booking.trip?.organizer?.full_name || 'N/A';
        document.getElementById('vbmDetailOrganizerContact').innerHTML = booking.trip?.organizer 
            ? `<i class="fas fa-envelope"></i> ${booking.trip.organizer.email}<br><i class="fas fa-phone"></i> ${booking.trip.organizer.phone || 'N/A'}`
            : 'N/A';

        // Service details
        document.getElementById('vbmDetailBookingType').innerHTML = `<i class="fas fa-${getBookingTypeIcon(booking.booking_type)}"></i> ${booking.booking_type?.replace('_', ' ').toUpperCase()}`;
        document.getElementById('vbmDetailServiceDates').textContent = booking.service_start_date && booking.service_end_date
            ? `${formatDate(booking.service_start_date)} - ${formatDate(booking.service_end_date)}`
            : 'N/A';
        document.getElementById('vbmDetailBookingDate').textContent = formatDate(booking.booking_date) || 'N/A';
        document.getElementById('vbmDetailConfirmedDate').textContent = formatDate(booking.confirmed_date) || 'Not confirmed';
        document.getElementById('vbmDetailServiceDesc').textContent = booking.service_description || 'No description provided';

        // Special requirements
        if (booking.special_requirements) {
            document.getElementById('vbmDetailSpecialReqSection').style.display = 'block';
            document.getElementById('vbmDetailSpecialReq').textContent = booking.special_requirements;
        } else {
            document.getElementById('vbmDetailSpecialReqSection').style.display = 'none';
        }

        // Pricing
        document.getElementById('vbmDetailQuotedAmount').textContent = formatCurrency(booking.quoted_amount, booking.currency);
        document.getElementById('vbmDetailFinalAmount').textContent = formatCurrency(booking.final_amount, booking.currency);
        document.getElementById('vbmDetailTotalAmount').textContent = formatCurrency(booking.total_amount, booking.currency);

        // Payments
        if (booking.payments && booking.payments.length > 0) {
            document.getElementById('vbmDetailPaymentsSection').style.display = 'block';
            const paymentsList = document.getElementById('vbmDetailPaymentsList');
            paymentsList.innerHTML = booking.payments.map(payment => `
                <div class="vbm-payment-item">
                    <div class="vbm-payment-info">
                        <span class="vbm-payment-amount">${formatCurrency(payment.amount, booking.currency)}</span>
                        <span class="vbm-payment-method">${payment.payment_method?.toUpperCase()}</span>
                        <span class="vb-payment-badge vb-payment-${payment.status}">${payment.status}</span>
                    </div>
                    <div class="vbm-payment-details">
                        <small>Date: ${formatDate(payment.payment_date) || 'N/A'}</small>
                        <small>Ref: ${payment.reference_number || 'N/A'}</small>
                    </div>
                </div>
            `).join('');
        }

        // Notes
        if (booking.notes) {
            document.getElementById('vbmDetailNotesSection').style.display = 'block';
            document.getElementById('vbmDetailNotes').innerHTML = booking.notes.replace(/\n/g, '<br>');
        } else {
            document.getElementById('vbmDetailNotesSection').style.display = 'none';
        }

        // Rating & Review
        if (booking.rating && booking.review) {
            document.getElementById('vbmDetailReviewSection').style.display = 'block';
            document.getElementById('vbmDetailRating').innerHTML = '★'.repeat(booking.rating) + '☆'.repeat(5 - booking.rating);
            document.getElementById('vbmDetailReview').textContent = booking.review;
        }
    }

    function formatDate(dateString) {
        if (!dateString) return null;
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function formatCurrency(amount, currency = 'USD') {
        if (!amount) return 'N/A';
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency }).format(amount);
    }

    function getBookingTypeIcon(type) {
        const icons = { 'transportation': 'bus', 'accommodation': 'hotel', 'activity': 'hiking' };
        return icons[type] || 'tag';
    }

    // Print functionality
    document.getElementById('vbmDetailsPrintBtn')?.addEventListener('click', () => {
        window.print();
    });

    return {
        open,
        close,
        currentBookingId
    };
})();

// Close modal on overlay click
document.getElementById('vbmBookingDetailsModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalBookingDetails.close();
    }
});