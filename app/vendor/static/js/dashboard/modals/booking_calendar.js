// Booking Calendar Modal JavaScript
window.VBModalCalendar = (function() {
    function open() {
        const modal = document.getElementById('vbmBookingCalendarModal');
        if (modal) {
            setDefaultDates();
            modal.style.display = 'flex';
            loadCalendar();
        }
    }

    function close() {
        const modal = document.getElementById('vbmBookingCalendarModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    function setDefaultDates() {
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

        document.getElementById('vbmCalendarStartDate').value = firstDay.toISOString().split('T')[0];
        document.getElementById('vbmCalendarEndDate').value = lastDay.toISOString().split('T')[0];
    }

    async function loadCalendar() {
        const loading = document.getElementById('vbmCalendarLoading');
        const content = document.getElementById('vbmCalendarContent');
        const empty = document.getElementById('vbmCalendarEmpty');

        loading.style.display = 'block';
        content.style.display = 'none';
        empty.style.display = 'none';

        try {
            const startDate = document.getElementById('vbmCalendarStartDate').value;
            const endDate = document.getElementById('vbmCalendarEndDate').value;

            if (!startDate || !endDate) {
                throw new Error('Please select both start and end dates');
            }

            const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
            const response = await fetch(`${window.VendorBookingsManager.apiEndpoints.getCalendar}?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error('Failed to load calendar');
            }

            const result = await response.json();

            if (result.success) {
                if (result.data.events.length === 0) {
                    empty.style.display = 'block';
                } else {
                    renderCalendar(result.data);
                    content.style.display = 'block';
                }
            } else {
                throw new Error(result.error || 'Failed to load calendar');
            }
        } catch (error) {
            console.error('Error loading calendar:', error);
            alert(error.message || 'Failed to load calendar. Please try again.');
        } finally {
            loading.style.display = 'none';
        }
    }

    function renderCalendar(data) {
        // Render availability summary
        document.getElementById('vbmTotalDays').textContent = data.availability.total_days;
        document.getElementById('vbmBookedDays').textContent = data.availability.booked_days;
        document.getElementById('vbmAvailableDays').textContent = data.availability.available_days;
        document.getElementById('vbmAvailabilityPercent').textContent = `${data.availability.availability_percentage}%`;

        // Render events
        const eventsList = document.getElementById('vbmEventsList');
        document.getElementById('vbmEventCount').textContent = `(${data.events.length})`;

        eventsList.innerHTML = data.events.map(event => `
            <div class="vbm-event-item ${event.status}">
                <div class="vbm-event-header">
                    <div class="vbm-event-title">
                        <i class="fas fa-${getBookingTypeIcon(event.booking_type)}"></i> ${escapeHtml(event.title)}
                    </div>
                    <span class="vb-status-badge vb-status-${event.status}">${event.status.replace('_', ' ')}</span>
                </div>
                <div class="vbm-event-details">
                    <div class="vbm-event-detail">
                        <i class="fas fa-calendar"></i>
                        <span>${formatDate(event.start)} - ${formatDate(event.end)}</span>
                    </div>
                    <div class="vbm-event-detail">
                        <i class="fas fa-dollar-sign"></i>
                        <span>${formatCurrency(event.amount, 'USD')}</span>
                    </div>
                    <div class="vbm-event-detail">
                        <i class="fas fa-credit-card"></i>
                        <span style="text-transform: capitalize;">${event.payment_status.replace('_', ' ')}</span>
                    </div>
                </div>
                <div class="vbm-event-actions">
                    <button class="vb-action-btn vb-action-view" onclick="VBModalBookingDetails.open(${event.id})">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                </div>
            </div>
        `).join('');
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    function formatCurrency(amount, currency = 'USD') {
        if (!amount) return 'N/A';
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency }).format(amount);
    }

    function getBookingTypeIcon(type) {
        const icons = { 'transportation': 'bus', 'accommodation': 'hotel', 'activity': 'hiking' };
        return icons[type] || 'tag';
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Attach event listener to load button
    document.getElementById('vbmCalendarLoadBtn')?.addEventListener('click', loadCalendar);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmBookingCalendarModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalCalendar.close();
    }
});