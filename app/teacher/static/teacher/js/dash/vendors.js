/**
 * Vendors Management - Main JavaScript
 * Handles vendor search, filtering, and booking management
 */

// Global state management
const VendorsState = {
    vendors: [],
    bookings: [],
    currentPage: 1,
    totalPages: 1,
    filters: {
        searchTerm: '',
        businessType: '',
        city: '',
        verified: false,
        minRating: null
    },
    bookingFilter: 'all',
    isLoading: false
};

// API endpoints
const API_ENDPOINTS = {
    searchVendors: '/api/teacher/vendors/search',
    vendorProfile: '/api/teacher/vendors/',
    bookings: '/api/teacher/vendors/bookings',
    stats: '/api/teacher/vendors/stats',
    availability: '/api/teacher/vendors/availability'
};

/**
 * Initialize the vendors management module
 */
function initVendorsManagement() {
    setupVendorEventListeners();
    loadVendors();
    loadTeacherBookings();
    loadVendorStats();
}

/**
 * Setup all event listeners
 */
function setupVendorEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('vendorSearchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const clearBtn = document.getElementById('btnClearVendorSearch');
            if (clearBtn) {
                clearBtn.style.display = e.target.value ? 'block' : 'none';
            }
            searchTimeout = setTimeout(() => {
                VendorsState.filters.searchTerm = e.target.value.trim();
                VendorsState.currentPage = 1;
                loadVendors();
            }, 500);
        });
    }

    // Clear search button
    const clearSearchBtn = document.getElementById('btnClearVendorSearch');
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            VendorsState.filters.searchTerm = '';
            VendorsState.currentPage = 1;
            loadVendors();
        });
    }

    // Filter toggle
    const filterToggleBtn = document.getElementById('btnToggleVendorFilters');
    const filtersPanel = document.getElementById('vendorFiltersPanel');
    if (filterToggleBtn && filtersPanel) {
        filterToggleBtn.addEventListener('click', () => {
            const isVisible = filtersPanel.style.display !== 'none';
            filtersPanel.style.display = isVisible ? 'none' : 'block';
        });
    }

    // Apply filters button
    const applyFiltersBtn = document.getElementById('btnApplyVendorFilters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyVendorFilters);
    }

    // Reset filters button
    const resetFiltersBtn = document.getElementById('btnResetVendorFilters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', resetVendorFilters);
    }

    // Pagination
    const prevBtn = document.getElementById('btnVendorsPrevPage');
    const nextBtn = document.getElementById('btnVendorsNextPage');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (VendorsState.currentPage > 1) {
                VendorsState.currentPage--;
                loadVendors();
            }
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (VendorsState.currentPage < VendorsState.totalPages) {
                VendorsState.currentPage++;
                loadVendors();
            }
        });
    }

    // Quick links
    const viewBookingsBtn = document.getElementById('btnViewMyBookings');
    if (viewBookingsBtn) {
        viewBookingsBtn.addEventListener('click', () => {
            toggleBookingsSection(true);
        });
    }

    const pendingPaymentsBtn = document.getElementById('btnViewPendingPayments');
    if (pendingPaymentsBtn) {
        pendingPaymentsBtn.addEventListener('click', () => {
            VendorsState.bookingFilter = 'confirmed';
            toggleBookingsSection(true);
            filterBookingsByStatus('confirmed');
        });
    }

    const checkAvailabilityBtn = document.getElementById('btnCheckAvailability');
    if (checkAvailabilityBtn) {
        checkAvailabilityBtn.addEventListener('click', () => {
            if (typeof openAvailabilityModal === 'function') {
                openAvailabilityModal();
            }
        });
    }

    // Statistics button
    const statsBtn = document.getElementById('btnShowVendorStats');
    if (statsBtn) {
        statsBtn.addEventListener('click', () => {
            if (typeof showVendorStatsModal === 'function') {
                showVendorStatsModal();
            }
        });
    }

    // Close bookings section
    const closeBookingsBtn = document.getElementById('btnCloseBookingsSection');
    if (closeBookingsBtn) {
        closeBookingsBtn.addEventListener('click', () => {
            toggleBookingsSection(false);
        });
    }

    // Booking status tabs
    const tabButtons = document.querySelectorAll('.vendors-tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const status = btn.dataset.status;
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterBookingsByStatus(status);
        });
    });
}

/**
 * Load vendors from API
 */
async function loadVendors() {
    if (VendorsState.isLoading) return;

    VendorsState.isLoading = true;
    showVendorsLoading(true);

    try {
        const queryParams = new URLSearchParams({
            page: VendorsState.currentPage,
            per_page: 12,
            q: VendorsState.filters.searchTerm,
            type: VendorsState.filters.businessType,
            city: VendorsState.filters.city,
            verified: VendorsState.filters.verified,
            ...(VendorsState.filters.minRating && { min_rating: VendorsState.filters.minRating })
        });

        const response = await fetch(`${API_ENDPOINTS.searchVendors}?${queryParams}`);
        const data = await handleApiResponse(response);

        if (data.success) {
            VendorsState.vendors = data.data.vendors;
            VendorsState.totalPages = data.data.pagination.pages;
            displayVendors(data.data.vendors);
            updatePagination(data.data.pagination);
        } else {
            showVendorsError('Failed to load vendors');
        }
    } catch (error) {
        console.error('Error loading vendors:', error);
        showVendorsError('An error occurred while loading vendors');
    } finally {
        VendorsState.isLoading = false;
        showVendorsLoading(false);
    }
}

/**
 * Display vendors in grid
 */
function displayVendors(vendors) {
    const vendorsGrid = document.getElementById('vendorsGrid');
    const emptyState = document.getElementById('vendorsEmptyState');

    if (!vendorsGrid) return;

    if (!vendors || vendors.length === 0) {
        vendorsGrid.innerHTML = '';
        if (emptyState) emptyState.style.display = 'block';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    const template = document.getElementById('vendorCardTemplate');
    if (!template) {
        console.error('Vendor card template not found');
        return;
    }

    vendorsGrid.innerHTML = '';

    vendors.forEach(vendor => {
        const card = createVendorCard(vendor, template);
        vendorsGrid.appendChild(card);
    });
}

/**
 * Create vendor card from template
 */
function createVendorCard(vendor, template) {
    const card = template.content.cloneNode(true);
    const cardElement = card.querySelector('.vendor-card');

    // Set vendor ID
    cardElement.dataset.vendorId = vendor.id;

    // Set badges
    const verifiedBadge = card.querySelector('.vendor-badge-verified');
    if (verifiedBadge && vendor.is_verified) {
        verifiedBadge.style.display = 'inline-flex';
    }

    const typeBadge = card.querySelector('.vendor-badge-type');
    if (typeBadge) {
        typeBadge.textContent = vendor.business_type || 'General';
    }

    // Set name
    const nameElement = card.querySelector('.vendor-card-name');
    if (nameElement) {
        nameElement.textContent = vendor.business_name || 'Unknown Vendor';
    }

    // Set rating
    const ratingStars = card.querySelector('.vendor-stars');
    const ratingText = card.querySelector('.vendor-rating-text');
    if (ratingStars && ratingText) {
        updateStarRating(ratingStars, vendor.average_rating || 0);
        const reviewCount = vendor.total_reviews || 0;
        ratingText.textContent = `${(vendor.average_rating || 0).toFixed(1)} (${reviewCount} ${reviewCount === 1 ? 'review' : 'reviews'})`;
    }

    // Set location
    const locationText = card.querySelector('.vendor-location-text');
    if (locationText) {
        const location = [vendor.city, vendor.state].filter(Boolean).join(', ') || 'Location not specified';
        locationText.textContent = location;
    }

    // Set description
    const descriptionElement = card.querySelector('.vendor-card-description');
    if (descriptionElement) {
        descriptionElement.textContent = vendor.description || 'No description available';
    }

    // Set contact info
    const phoneElement = card.querySelector('.vendor-phone');
    const emailElement = card.querySelector('.vendor-email');
    if (phoneElement) {
        phoneElement.textContent = vendor.phone || 'N/A';
    }
    if (emailElement) {
        emailElement.textContent = vendor.email || 'N/A';
    }

    // Set up action buttons
    const viewBtn = card.querySelector('.btn-vendor-view');
    const quoteBtn = card.querySelector('.btn-vendor-quote');

    if (viewBtn) {
        viewBtn.addEventListener('click', () => {
            if (typeof openVendorProfileModal === 'function') {
                openVendorProfileModal(vendor.id);
            }
        });
    }

    if (quoteBtn) {
        quoteBtn.addEventListener('click', () => {
            if (typeof openRequestQuoteModal === 'function') {
                openRequestQuoteModal(vendor.id);
            }
        });
    }

    return card;
}

/**
 * Update star rating display
 */
function updateStarRating(container, rating) {
    const stars = container.querySelectorAll('i');
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    stars.forEach((star, index) => {
        star.className = 'fas fa-star';
        if (index >= fullStars) {
            star.className = 'far fa-star';
        }
        if (index === fullStars && hasHalfStar) {
            star.className = 'fas fa-star-half-alt';
        }
    });
}

/**
 * Update pagination controls
 */
function updatePagination(pagination) {
    const paginationContainer = document.getElementById('vendorsPagination');
    const prevBtn = document.getElementById('btnVendorsPrevPage');
    const nextBtn = document.getElementById('btnVendorsNextPage');
    const pageInfo = document.getElementById('vendorsPageInfo');

    if (!paginationContainer) return;

    if (pagination.pages <= 1) {
        paginationContainer.style.display = 'none';
        return;
    }

    paginationContainer.style.display = 'flex';

    if (prevBtn) {
        prevBtn.disabled = !pagination.has_prev;
    }

    if (nextBtn) {
        nextBtn.disabled = !pagination.has_next;
    }

    if (pageInfo) {
        pageInfo.textContent = `Page ${pagination.page} of ${pagination.pages}`;
    }
}

/**
 * Apply vendor filters
 */
function applyVendorFilters() {
    VendorsState.filters.businessType = document.getElementById('filterVendorType')?.value || '';
    VendorsState.filters.city = document.getElementById('filterVendorCity')?.value.trim() || '';
    VendorsState.filters.minRating = document.getElementById('filterMinRating')?.value || null;
    VendorsState.filters.verified = document.getElementById('filterVerifiedOnly')?.checked || false;
    VendorsState.currentPage = 1;
    loadVendors();
}

/**
 * Reset vendor filters
 */
function resetVendorFilters() {
    VendorsState.filters = {
        searchTerm: '',
        businessType: '',
        city: '',
        verified: false,
        minRating: null
    };

    document.getElementById('filterVendorType').value = '';
    document.getElementById('filterVendorCity').value = '';
    document.getElementById('filterMinRating').value = '';
    document.getElementById('filterVerifiedOnly').checked = false;

    VendorsState.currentPage = 1;
    loadVendors();
}

/**
 * Load teacher's bookings
 */
async function loadTeacherBookings() {
    try {
        const response = await fetch(API_ENDPOINTS.bookings);
        const data = await handleApiResponse(response);

        if (data.success) {
            VendorsState.bookings = data.data.bookings;
            updateBookingCounts();
            displayBookings(data.data.bookings);
        }
    } catch (error) {
        console.error('Error loading bookings:', error);
    }
}

/**
 * Update booking count badges
 */
function updateBookingCounts() {
    const bookings = VendorsState.bookings;

    const counts = {
        all: bookings.length,
        pending: bookings.filter(b => b.status === 'pending').length,
        confirmed: bookings.filter(b => b.status === 'confirmed').length,
        completed: bookings.filter(b => b.status === 'completed').length,
        cancelled: bookings.filter(b => b.status === 'cancelled').length
    };

    // Update tab counts
    document.getElementById('countAllBookings').textContent = counts.all;
    document.getElementById('countPendingBookings').textContent = counts.pending;
    document.getElementById('countConfirmedBookings').textContent = counts.confirmed;
    document.getElementById('countCompletedBookings').textContent = counts.completed;
    document.getElementById('countCancelledBookings').textContent = counts.cancelled;

    // Update quick link badges
    document.getElementById('badgePendingBookings').textContent = counts.pending;
    document.getElementById('badgePendingPayments').textContent = counts.confirmed;
}

/**
 * Display bookings list
 */
function displayBookings(bookings) {
    const bookingsList = document.getElementById('vendorBookingsList');
    if (!bookingsList) return;

    if (!bookings || bookings.length === 0) {
        bookingsList.innerHTML = '<p style="text-align: center; color: #95a5a6; padding: 40px;">No bookings found</p>';
        return;
    }

    const template = document.getElementById('bookingItemTemplate');
    if (!template) {
        console.error('Booking item template not found');
        return;
    }

    bookingsList.innerHTML = '';

    bookings.forEach(booking => {
        const item = createBookingItem(booking, template);
        bookingsList.appendChild(item);
    });
}

/**
 * Create booking item from template
 */
function createBookingItem(booking, template) {
    const item = template.content.cloneNode(true);
    const itemElement = item.querySelector('.vendor-booking-item');

    itemElement.dataset.bookingId = booking.id;

    // Set vendor name
    const vendorName = item.querySelector('.booking-vendor-name');
    if (vendorName) {
        vendorName.textContent = booking.vendor?.business_name || 'Unknown Vendor';
    }

    // Set status badge
    const statusBadge = item.querySelector('.booking-status-badge');
    if (statusBadge) {
        statusBadge.textContent = booking.status;
        statusBadge.className = `booking-status-badge status-${booking.status}`;
    }

    // Set trip name
    const tripName = item.querySelector('.booking-trip-name');
    if (tripName) {
        tripName.textContent = booking.trip?.title || 'N/A';
    }

    // Set booking type
    const bookingType = item.querySelector('.booking-type');
    if (bookingType) {
        bookingType.textContent = booking.booking_type;
        bookingType.style.textTransform = 'capitalize';
    }

    // Set amount
    const amount = item.querySelector('.booking-amount');
    if (amount) {
        const amountValue = booking.total_amount || booking.quoted_amount || 0;
        amount.textContent = `KES ${parseFloat(amountValue).toLocaleString()}`;
    }

    // Set date
    const dateElement = item.querySelector('.booking-date');
    if (dateElement && booking.created_at) {
        dateElement.textContent = formatDate(booking.created_at);
    }

    // Setup action buttons
    setupBookingActions(item, booking);

    return item;
}

/**
 * Setup booking action buttons
 */
function setupBookingActions(item, booking) {
    const viewBtn = item.querySelector('[data-action="view"]');
    const confirmBtn = item.querySelector('[data-action="confirm"]');
    const payBtn = item.querySelector('[data-action="pay"]');
    const rateBtn = item.querySelector('[data-action="rate"]');
    const cancelBtn = item.querySelector('[data-action="cancel"]');

    // View button
    if (viewBtn) {
        viewBtn.addEventListener('click', () => {
            if (typeof openBookingDetailsModal === 'function') {
                openBookingDetailsModal(booking.id);
            }
        });
    }

    // Show/hide buttons based on status
    if (booking.status === 'pending') {
        if (confirmBtn) {
            confirmBtn.style.display = 'flex';
            confirmBtn.addEventListener('click', () => {
                if (typeof openConfirmBookingModal === 'function') {
                    openConfirmBookingModal(booking.id);
                }
            });
        }
        if (cancelBtn) {
            cancelBtn.style.display = 'flex';
            cancelBtn.addEventListener('click', () => {
                if (typeof openCancelBookingModal === 'function') {
                    openCancelBookingModal(booking.id);
                }
            });
        }
    }

    if (booking.status === 'confirmed') {
        if (payBtn) {
            payBtn.style.display = 'flex';
            payBtn.addEventListener('click', () => {
                if (typeof openPaymentModal === 'function') {
                    openPaymentModal(booking.id);
                }
            });
        }
        if (cancelBtn) {
            cancelBtn.style.display = 'flex';
            cancelBtn.addEventListener('click', () => {
                if (typeof openCancelBookingModal === 'function') {
                    openCancelBookingModal(booking.id);
                }
            });
        }
    }

    if (booking.status === 'completed' && !booking.rating) {
        if (rateBtn) {
            rateBtn.style.display = 'flex';
            rateBtn.addEventListener('click', () => {
                if (typeof openRateVendorModal === 'function') {
                    openRateVendorModal(booking.id);
                }
            });
        }
    }
}

/**
 * Filter bookings by status
 */
function filterBookingsByStatus(status) {
    VendorsState.bookingFilter = status;
    let filteredBookings = VendorsState.bookings;

    if (status !== 'all') {
        filteredBookings = filteredBookings.filter(b => b.status === status);
    }

    displayBookings(filteredBookings);
}

/**
 * Toggle bookings section visibility
 */
function toggleBookingsSection(show) {
    const bookingsSection = document.getElementById('myBookingsSection');
    if (bookingsSection) {
        bookingsSection.style.display = show ? 'block' : 'none';
        if (show) {
            bookingsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

/**
 * Load vendor statistics
 */
async function loadVendorStats() {
    try {
        const response = await fetch(API_ENDPOINTS.stats);
        const data = await handleApiResponse(response);

        if (data.success) {
            // Store stats for modal display
            window.vendorStatsData = data.data;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Show/hide loading state
 */
function showVendorsLoading(show) {
    const loadingState = document.getElementById('vendorsLoadingState');
    const vendorsGrid = document.getElementById('vendorsGrid');

    if (loadingState) {
        loadingState.style.display = show ? 'block' : 'none';
    }

    if (vendorsGrid && show) {
        vendorsGrid.innerHTML = '';
    }
}

/**
 * Show error message
 */
function showVendorsError(message) {
    const emptyState = document.getElementById('vendorsEmptyState');
    if (emptyState) {
        emptyState.style.display = 'block';
        emptyState.querySelector('h3').textContent = 'Error';
        emptyState.querySelector('p').textContent = message;
    }
}

/**
 * Handle API response
 */
async function handleApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'An error occurred');
    }
    return await response.json();
}

/**
 * Format date string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Refresh vendors and bookings data
 */
function refreshVendorsData() {
    loadVendors();
    loadTeacherBookings();
    loadVendorStats();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVendorsManagement);
} else {
    initVendorsManagement();
}