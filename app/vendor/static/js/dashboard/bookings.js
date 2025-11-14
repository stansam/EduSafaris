// Vendor Bookings Management JavaScript
(function() {
    'use strict';

    // State management
    const VendorBookingsState = {
        currentPage: 1,
        perPage: 20,
        totalPages: 0,
        totalBookings: 0,
        bookings: [],
        filters: {
            status: '',
            booking_type: '',
            start_date: '',
            end_date: '',
            search: ''
        },
        statistics: {
            pending: 0,
            confirmed: 0,
            in_progress: 0,
            completed: 0,
            total: 0
        }
    };

    // API Endpoints
    const API_ENDPOINTS = {
        getBookings: '/api/vendor/bookings',
        getBookingDetails: (id) => `/api/vendor/bookings/${id}`,
        acceptBooking: (id) => `/api/vendor/bookings/${id}/accept`,
        rejectBooking: (id) => `/api/vendor/bookings/${id}/reject`,
        updateStatus: (id) => `/api/vendor/bookings/${id}/status`,
        cancelBooking: (id) => `/api/vendor/bookings/${id}/cancel`,
        requestModification: (id) => `/api/vendor/bookings/${id}/modification-request`,
        getCalendar: '/api/vendor/bookings/calendar',
        addNote: (id) => `/api/vendor/bookings/${id}/notes`
    };

    // Initialize on DOM load
    document.addEventListener('DOMContentLoaded', function() {
        initializeBookingsManagement();
    });

    function initializeBookingsManagement() {
        attachEventListeners();
        loadBookings();
    }

    // Attach Event Listeners
    function attachEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('vbRefreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => loadBookings());
        }

        // Calendar view button
        const calendarBtn = document.getElementById('vbCalendarViewBtn');
        if (calendarBtn) {
            calendarBtn.addEventListener('click', openCalendarModal);
        }

        // Search input
        const searchInput = document.getElementById('vbSearchInput');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function(e) {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    VendorBookingsState.filters.search = e.target.value;
                    VendorBookingsState.currentPage = 1;
                    loadBookings();
                }, 500);
            });
        }

        // Filter buttons
        const applyFiltersBtn = document.getElementById('vbApplyFiltersBtn');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', applyFilters);
        }

        const clearFiltersBtn = document.getElementById('vbClearFiltersBtn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', clearFilters);
        }

        // Pagination buttons
        const prevPageBtn = document.getElementById('vbPrevPageBtn');
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => changePage(VendorBookingsState.currentPage - 1));
        }

        const nextPageBtn = document.getElementById('vbNextPageBtn');
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => changePage(VendorBookingsState.currentPage + 1));
        }
    }

    // Load Bookings
    async function loadBookings() {
        showLoading();
        hideError();

        try {
            const params = new URLSearchParams({
                page: VendorBookingsState.currentPage,
                per_page: VendorBookingsState.perPage,
                ...VendorBookingsState.filters
            });

            // Remove empty filters
            for (const [key, value] of [...params]) {
                if (!value) params.delete(key);
            }

            const response = await fetch(`${API_ENDPOINTS.getBookings}?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                VendorBookingsState.bookings = result.data.bookings;
                VendorBookingsState.currentPage = result.data.pagination.page;
                VendorBookingsState.totalPages = result.data.pagination.pages;
                VendorBookingsState.totalBookings = result.data.pagination.total;
                VendorBookingsState.statistics = result.data.statistics;

                updateStatistics();
                renderBookingsTable();
                updatePagination();
            } else {
                throw new Error(result.error || 'Failed to load bookings');
            }
        } catch (error) {
            console.error('Error loading bookings:', error);
            showError(error.message || 'Failed to load bookings. Please try again.');
        } finally {
            hideLoading();
        }
    }

    // Update Statistics
    function updateStatistics() {
        const stats = VendorBookingsState.statistics;
        
        const statElements = {
            vbStatPending: stats.pending || 0,
            vbStatConfirmed: stats.confirmed || 0,
            vbStatProgress: stats.in_progress || 0,
            vbStatCompleted: stats.completed || 0,
            vbStatTotal: stats.total || 0
        };

        for (const [id, value] of Object.entries(statElements)) {
            const element = document.getElementById(id);
            if (element) {
                animateValue(element, parseInt(element.textContent) || 0, value, 500);
            }
        }
    }

    // Animate number value
    function animateValue(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 16);
    }

    // Render Bookings Table
    function renderBookingsTable() {
        const tableBody = document.getElementById('vbTableBody');
        const tableWrapper = document.getElementById('vbTableWrapper');
        const emptyState = document.getElementById('vbEmptyState');

        if (!tableBody) return;

        if (VendorBookingsState.bookings.length === 0) {
            tableWrapper.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        tableWrapper.style.display = 'block';
        emptyState.style.display = 'none';

        tableBody.innerHTML = VendorBookingsState.bookings.map(booking => `
            <tr>
                <td><strong>#${booking.id}</strong></td>
                <td>
                    <div class="vb-trip-info">
                        <span class="vb-trip-title">${escapeHtml(booking.trip?.title || 'N/A')}</span>
                        <span class="vb-trip-organizer">
                            <i class="fas fa-user"></i> ${escapeHtml(booking.trip?.organizer?.full_name || 'Unknown')}
                        </span>
                    </div>
                </td>
                <td>
                    <span style="text-transform: capitalize;">
                        <i class="fas fa-${getBookingTypeIcon(booking.booking_type)}"></i> 
                        ${escapeHtml(booking.booking_type?.replace('_', ' ') || 'N/A')}
                    </span>
                </td>
                <td>
                    ${booking.service_start_date ? formatDate(booking.service_start_date) : 'N/A'}<br>
                    <small style="color: #7f8c8d;">to ${booking.service_end_date ? formatDate(booking.service_end_date) : 'N/A'}</small>
                </td>
                <td>
                    <strong>${formatBookingCurrency(booking.total_amount, booking.currency)}</strong>
                </td>
                <td>
                    <span class="vb-status-badge vb-status-${booking.status}">
                        ${escapeHtml(booking.status?.replace('_', ' ') || 'Unknown')}
                    </span>
                </td>
                <td>
                    <span class="vb-payment-badge vb-payment-${booking.payment_status}">
                        ${escapeHtml(booking.payment_status?.replace('_', ' ') || 'Unknown')}
                    </span>
                </td>
                <td>${booking.booking_date ? formatDate(booking.booking_date) : 'N/A'}</td>
                <td>
                    <div class="vb-action-buttons">
                        ${renderActionButtons(booking)}
                    </div>
                </td>
            </tr>
        `).join('');

        // Attach action button listeners
        attachActionButtonListeners();
    }

    // Render Action Buttons based on booking status
    function renderActionButtons(booking) {
        let buttons = `
            <button class="vb-action-btn vb-action-view" data-action="view" data-booking-id="${booking.id}">
                <i class="fas fa-eye"></i> View
            </button>
        `;

        if (booking.status === 'pending') {
            buttons += `
                <button class="vb-action-btn vb-action-accept" data-action="accept" data-booking-id="${booking.id}">
                    <i class="fas fa-check"></i> Accept
                </button>
                <button class="vb-action-btn vb-action-reject" data-action="reject" data-booking-id="${booking.id}">
                    <i class="fas fa-times"></i> Reject
                </button>
            `;
        }

        if (booking.status === 'confirmed' || booking.status === 'in_progress') {
            buttons += `
                <button class="vb-action-btn vb-action-modify" data-action="update-status" data-booking-id="${booking.id}">
                    <i class="fas fa-edit"></i> Update
                </button>
            `;
        }

        if (booking.status === 'pending' || booking.status === 'confirmed') {
            buttons += `
                <button class="vb-action-btn vb-action-modify" data-action="request-modification" data-booking-id="${booking.id}">
                    <i class="fas fa-pen"></i> Modify
                </button>
            `;
        }

        if (booking.status === 'pending' || booking.status === 'confirmed') {
            buttons += `
                <button class="vb-action-btn vb-action-reject" data-action="cancel" data-booking-id="${booking.id}">
                    <i class="fas fa-ban"></i> Cancel
                </button>
            `;
        }

        return buttons;
    }

    // Attach Action Button Listeners
    function attachActionButtonListeners() {
        const actionButtons = document.querySelectorAll('[data-action]');
        actionButtons.forEach(button => {
            button.addEventListener('click', handleActionClick);
        });
    }

    // Handle Action Button Click
    async function handleActionClick(e) {
        const action = e.currentTarget.dataset.action;
        const bookingId = parseInt(e.currentTarget.dataset.bookingId);

        switch (action) {
            case 'view':
                await openBookingDetailsModal(bookingId);
                break;
            case 'accept':
                openAcceptBookingModal(bookingId);
                break;
            case 'reject':
                openRejectBookingModal(bookingId);
                break;
            case 'update-status':
                openUpdateStatusModal(bookingId);
                break;
            case 'request-modification':
                openRequestModificationModal(bookingId);
                break;
            case 'cancel':
                openCancelBookingModal(bookingId);
                break;
        }
    }

    // Get Booking Type Icon
    function getBookingTypeIcon(type) {
        const icons = {
            'transportation': 'bus',
            'accommodation': 'hotel',
            'activity': 'hiking'
        };
        return icons[type] || 'tag';
    }

    // Apply Filters
    function applyFilters() {
        VendorBookingsState.filters.status = document.getElementById('vbFilterStatus')?.value || '';
        VendorBookingsState.filters.booking_type = document.getElementById('vbFilterType')?.value || '';
        VendorBookingsState.filters.start_date = document.getElementById('vbFilterStartDate')?.value || '';
        VendorBookingsState.filters.end_date = document.getElementById('vbFilterEndDate')?.value || '';
        VendorBookingsState.currentPage = 1;
        loadBookings();
    }

    // Clear Filters
    function clearFilters() {
        VendorBookingsState.filters = {
            status: '',
            booking_type: '',
            start_date: '',
            end_date: '',
            search: ''
        };

        document.getElementById('vbFilterStatus').value = '';
        document.getElementById('vbFilterType').value = '';
        document.getElementById('vbFilterStartDate').value = '';
        document.getElementById('vbFilterEndDate').value = '';
        document.getElementById('vbSearchInput').value = '';

        VendorBookingsState.currentPage = 1;
        loadBookings();
    }

    // Pagination
    function updatePagination() {
        const pagination = document.getElementById('vbPagination');
        const paginationInfo = document.getElementById('vbPaginationInfo');
        const prevBtn = document.getElementById('vbPrevPageBtn');
        const nextBtn = document.getElementById('vbNextPageBtn');
        const pageNumbers = document.getElementById('vbPageNumbers');

        if (!pagination) return;

        if (VendorBookingsState.totalBookings === 0) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';

        // Update info
        const start = (VendorBookingsState.currentPage - 1) * VendorBookingsState.perPage + 1;
        const end = Math.min(start + VendorBookingsState.perPage - 1, VendorBookingsState.totalBookings);
        paginationInfo.textContent = `Showing ${start}-${end} of ${VendorBookingsState.totalBookings} bookings`;

        // Update buttons
        prevBtn.disabled = VendorBookingsState.currentPage === 1;
        nextBtn.disabled = VendorBookingsState.currentPage === VendorBookingsState.totalPages;

        // Render page numbers
        pageNumbers.innerHTML = renderPageNumbers();
        attachPageNumberListeners();
    }

    function renderPageNumbers() {
        const current = VendorBookingsState.currentPage;
        const total = VendorBookingsState.totalPages;
        const pages = [];

        if (total <= 7) {
            for (let i = 1; i <= total; i++) {
                pages.push(i);
            }
        } else {
            if (current <= 4) {
                pages.push(1, 2, 3, 4, 5, '...', total);
            } else if (current >= total - 3) {
                pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total);
            } else {
                pages.push(1, '...', current - 1, current, current + 1, '...', total);
            }
        }

        return pages.map(page => {
            if (page === '...') {
                return '<span style="padding: 8px;">...</span>';
            }
            return `<button class="vb-page-btn ${page === current ? 'active' : ''}" data-page="${page}">${page}</button>`;
        }).join('');
    }

    function attachPageNumberListeners() {
        const pageButtons = document.querySelectorAll('.vb-page-btn');
        pageButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(e.target.dataset.page);
                changePage(page);
            });
        });
    }

    function changePage(page) {
        if (page < 1 || page > VendorBookingsState.totalPages) return;
        VendorBookingsState.currentPage = page;
        loadBookings();
    }

    // UI Helper Functions
    function showLoading() {
        const loading = document.getElementById('vbLoadingIndicator');
        const table = document.getElementById('vbTableWrapper');
        const empty = document.getElementById('vbEmptyState');
        
        if (loading) loading.style.display = 'block';
        if (table) table.style.display = 'none';
        if (empty) empty.style.display = 'none';
    }

    function hideLoading() {
        const loading = document.getElementById('vbLoadingIndicator');
        if (loading) loading.style.display = 'none';
    }

    function showError(message) {
        const errorDiv = document.getElementById('vbErrorMessage');
        const errorText = document.getElementById('vbErrorText');
        if (errorDiv && errorText) {
            errorText.textContent = message;
            errorDiv.style.display = 'flex';
        }
    }

    function hideError() {
        const errorDiv = document.getElementById('vbErrorMessage');
        if (errorDiv) errorDiv.style.display = 'none';
    }

    // Utility Functions
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    function formatBookingCurrency(amount, currency = 'KES') {
        // if (!amount) return 'N/A';
        const kenCurr = 'KES'
        if (amount === null || amount === undefined) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: kenCurr
        }).format(amount);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Modal Functions (to be implemented in modal files)
    function openBookingDetailsModal(bookingId) {
        if (window.VBModalBookingDetails) {
            window.VBModalBookingDetails.open(bookingId);
        }
    }

    function openAcceptBookingModal(bookingId) {
        if (window.VBModalAcceptBooking) {
            window.VBModalAcceptBooking.open(bookingId);
        }
    }

    function openRejectBookingModal(bookingId) {
        if (window.VBModalRejectBooking) {
            window.VBModalRejectBooking.open(bookingId);
        }
    }

    function openUpdateStatusModal(bookingId) {
        if (window.VBModalUpdateStatus) {
            window.VBModalUpdateStatus.open(bookingId);
        }
    }

    function openRequestModificationModal(bookingId) {
        if (window.VBModalRequestModification) {
            window.VBModalRequestModification.open(bookingId);
        }
    }

    function openCancelBookingModal(bookingId) {
        if (window.VBModalCancelBooking) {
            window.VBModalCancelBooking.open(bookingId);
        }
    }

    function openCalendarModal() {
        if (window.VBModalCalendar) {
            window.VBModalCalendar.open();
        }
    }

    // Export functions for modal callbacks
    window.VendorBookingsManager = {
        reload: loadBookings,
        getBooking: (id) => VendorBookingsState.bookings.find(b => b.id === id),
        apiEndpoints: API_ENDPOINTS
    };
})();