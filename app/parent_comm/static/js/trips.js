// Trips Management Module
const TripsManager = (function() {
    'use strict';

    // State
    const state = {
        currentPage: 1,
        perPage: 9,
        totalPages: 1,
        currentView: 'grid',
        trips: [],
        registrations: [],
        categories: [],
        gradeLevels: [],
        filters: {
            search: '',
            destination: '',
            category: '',
            gradeLevel: '',
            minPrice: null,
            maxPrice: null,
            startDateFrom: '',
            startDateTo: '',
            sortBy: 'start_date',
            sortOrder: 'asc'
        },
        loading: false
    };

    // DOM Elements
    const elements = {
        // Search and Filters
        searchInput: null,
        clearSearchBtn: null,
        toggleFiltersBtn: null,
        filtersPanel: null,
        destinationFilter: null,
        categoryFilter: null,
        gradeLevelFilter: null,
        minPriceFilter: null,
        maxPriceFilter: null,
        startDateFromFilter: null,
        startDateToFilter: null,
        sortByFilter: null,
        applyFiltersBtn: null,
        resetFiltersBtn: null,
        
        // View Toggle
        gridViewBtn: null,
        listViewBtn: null,
        resultsInfo: null,
        
        // Content
        gridView: null,
        listView: null,
        loadingState: null,
        emptyState: null,
        errorState: null,
        errorMessage: null,
        retryBtn: null,
        
        // Pagination
        paginationContainer: null,
        prevPageBtn: null,
        nextPageBtn: null,
        paginationInfo: null,
        
        // Registrations
        registrationsContainer: null,
        registrationsEmpty: null,
        refreshRegistrationsBtn: null,
        
        // Toast
        toast: null,
        toastMessage: null
    };

    // Initialize
    function init() {
        try {
            cacheDOM();
            bindEvents();
            loadCategories();
            loadTrips();
            loadRegistrations();
        } catch (error) {
            console.error('Failed to initialize TripsManager:', error);
            showToast('Failed to initialize trips manager', 'error');
        }
    }

    // Cache DOM Elements
    function cacheDOM() {
        elements.searchInput = document.getElementById('tripsSearchInput');
        elements.clearSearchBtn = document.getElementById('tripsClearSearchBtn');
        elements.toggleFiltersBtn = document.getElementById('tripsToggleFiltersBtn');
        elements.filtersPanel = document.getElementById('tripsFiltersPanel');
        elements.destinationFilter = document.getElementById('tripsDestinationFilter');
        elements.categoryFilter = document.getElementById('tripsCategoryFilter');
        elements.gradeLevelFilter = document.getElementById('tripsGradeLevelFilter');
        elements.minPriceFilter = document.getElementById('tripsMinPriceFilter');
        elements.maxPriceFilter = document.getElementById('tripsMaxPriceFilter');
        elements.startDateFromFilter = document.getElementById('tripsStartDateFromFilter');
        elements.startDateToFilter = document.getElementById('tripsStartDateToFilter');
        elements.sortByFilter = document.getElementById('tripsSortByFilter');
        elements.applyFiltersBtn = document.getElementById('tripsApplyFiltersBtn');
        elements.resetFiltersBtn = document.getElementById('tripsResetFiltersBtn');
        
        elements.gridViewBtn = document.getElementById('tripsGridViewBtn');
        elements.listViewBtn = document.getElementById('tripsListViewBtn');
        elements.resultsInfo = document.getElementById('tripsResultsInfo');
        
        elements.gridView = document.getElementById('tripsGridView');
        elements.listView = document.getElementById('tripsListView');
        elements.loadingState = document.getElementById('tripsLoadingState');
        elements.emptyState = document.getElementById('tripsEmptyState');
        elements.errorState = document.getElementById('tripsErrorState');
        elements.errorMessage = document.getElementById('tripsErrorMessage');
        elements.retryBtn = document.getElementById('tripsRetryBtn');
        
        elements.paginationContainer = document.getElementById('tripsPaginationContainer');
        elements.prevPageBtn = document.getElementById('tripsPrevPageBtn');
        elements.nextPageBtn = document.getElementById('tripsNextPageBtn');
        elements.paginationInfo = document.getElementById('tripsPaginationInfo');
        
        elements.registrationsContainer = document.getElementById('tripsRegistrationsContainer');
        elements.registrationsEmpty = document.getElementById('tripsRegistrationsEmpty');
        elements.refreshRegistrationsBtn = document.getElementById('tripsRefreshRegistrationsBtn');
        
        elements.toast = document.getElementById('tripsToast');
        elements.toastMessage = document.getElementById('tripsToastMessage');
    }

    // Bind Events
    function bindEvents() {
        // Search
        if (elements.searchInput) {
            elements.searchInput.addEventListener('input', debounce(handleSearchInput, 500));
        }
        
        if (elements.clearSearchBtn) {
            elements.clearSearchBtn.addEventListener('click', clearSearch);
        }
        
        // Filters
        if (elements.toggleFiltersBtn) {
            elements.toggleFiltersBtn.addEventListener('click', toggleFilters);
        }
        
        if (elements.applyFiltersBtn) {
            elements.applyFiltersBtn.addEventListener('click', applyFilters);
        }
        
        if (elements.resetFiltersBtn) {
            elements.resetFiltersBtn.addEventListener('click', resetFilters);
        }
        
        // View Toggle
        if (elements.gridViewBtn) {
            elements.gridViewBtn.addEventListener('click', () => switchView('grid'));
        }
        
        if (elements.listViewBtn) {
            elements.listViewBtn.addEventListener('click', () => switchView('list'));
        }
        
        // Pagination
        if (elements.prevPageBtn) {
            elements.prevPageBtn.addEventListener('click', () => changePage(state.currentPage - 1));
        }
        
        if (elements.nextPageBtn) {
            elements.nextPageBtn.addEventListener('click', () => changePage(state.currentPage + 1));
        }
        
        // Retry
        if (elements.retryBtn) {
            elements.retryBtn.addEventListener('click', loadTrips);
        }
        
        // Registrations
        if (elements.refreshRegistrationsBtn) {
            elements.refreshRegistrationsBtn.addEventListener('click', loadRegistrations);
        }
    }

    // Debounce Helper
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Load Categories
    async function loadCategories() {
        try {
            const response = await fetch('/api/parent/trips/categories', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to load categories');
            }

            const result = await response.json();
            
            if (result.success && result.data) {
                state.categories = result.data.categories || [];
                state.gradeLevels = result.data.grade_levels || [];
                populateFilterDropdowns();
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    // Populate Filter Dropdowns
    function populateFilterDropdowns() {
        // Categories
        if (elements.categoryFilter && state.categories.length > 0) {
            state.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                elements.categoryFilter.appendChild(option);
            });
        }
        
        // Grade Levels
        if (elements.gradeLevelFilter && state.gradeLevels.length > 0) {
            state.gradeLevels.forEach(level => {
                const option = document.createElement('option');
                option.value = level;
                option.textContent = level;
                elements.gradeLevelFilter.appendChild(option);
            });
        }
    }

    // Load Trips
    async function loadTrips() {
        if (state.loading) return;
        
        state.loading = true;
        showLoadingState();

        try {
            const queryParams = new URLSearchParams({
                page: state.currentPage,
                per_page: state.perPage,
                ...(state.filters.search && { q: state.filters.search }),
                ...(state.filters.destination && { destination: state.filters.destination }),
                ...(state.filters.category && { category: state.filters.category }),
                ...(state.filters.gradeLevel && { grade_level: state.filters.gradeLevel }),
                ...(state.filters.minPrice !== null && { min_price: state.filters.minPrice }),
                ...(state.filters.maxPrice !== null && { max_price: state.filters.maxPrice }),
                ...(state.filters.startDateFrom && { start_date_from: state.filters.startDateFrom }),
                ...(state.filters.startDateTo && { start_date_to: state.filters.startDateTo }),
                sort_by: state.filters.sortBy,
                sort_order: state.filters.sortOrder
            });

            const endpoint = state.filters.search || 
                            state.filters.destination || 
                            state.filters.category || 
                            state.filters.gradeLevel ||
                            state.filters.minPrice !== null ||
                            state.filters.maxPrice !== null ||
                            state.filters.startDateFrom ||
                            state.filters.startDateTo
                ? '/api/parent/trips/search'
                : '/api/parents/trips';

            const response = await fetch(`${endpoint}?${queryParams}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Failed to load trips: ${response.status}`);
            }

            const result = await response.json();

            if (result.success && result.data) {
                state.trips = result.data.trips || [];
                
                if (result.data.pagination) {
                    state.currentPage = result.data.pagination.page;
                    state.totalPages = result.data.pagination.total_pages;
                    updatePagination(result.data.pagination);
                }
                
                renderTrips();
                updateResultsInfo();
            } else {
                throw new Error(result.message || 'Failed to load trips');
            }
        } catch (error) {
            console.error('Error loading trips:', error);
            showErrorState(error.message);
        } finally {
            state.loading = false;
        }
    }

    // Render Trips
    function renderTrips() {
        hideAllStates();
        
        if (state.trips.length === 0) {
            showEmptyState();
            return;
        }

        if (state.currentView === 'grid') {
            renderGridView();
        } else {
            renderListView();
        }
    }

    // Render Grid View
    function renderGridView() {
        if (!elements.gridView) return;
        
        elements.gridView.innerHTML = '';
        
        state.trips.forEach(trip => {
            const card = createTripCard(trip);
            elements.gridView.appendChild(card);
        });
        
        elements.gridView.style.display = 'grid';
        if (elements.listView) {
            elements.listView.style.display = 'none';
        }
    }

    // Create Trip Card
    function createTripCard(trip) {
        const card = document.createElement('div');
        card.className = 'trips-card';
        card.setAttribute('data-trip-id', trip.id);
        
        const isFull = trip.is_full || false;
        const canRegister = trip.can_register || false;
        const spotsRemaining = trip.spots_remaining || 0;
        
        let badgeHTML = '';
        if (trip.featured) {
            badgeHTML = '<span class="trips-card-badge trips-badge-featured">Featured</span>';
        } else if (isFull) {
            badgeHTML = '<span class="trips-card-badge trips-badge-full">Full</span>';
        } else if (canRegister) {
            badgeHTML = '<span class="trips-card-badge trips-badge-available">Available</span>';
        }
        
        card.innerHTML = `
            <div class="trips-card-image"></div>
            <div class="trips-card-body">
                <div class="trips-card-header">
                    <div>
                        <h3 class="trips-card-title">${escapeHtml(trip.title)}</h3>
                    </div>
                    ${badgeHTML}
                </div>
                
                <div class="trips-card-destination">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${escapeHtml(trip.destination)}</span>
                </div>
                
                <div class="trips-card-info">
                    <div class="trips-info-item">
                        <span class="trips-info-label">Start Date</span>
                        <span class="trips-info-value">${formatDate(trip.start_date)}</span>
                    </div>
                    <div class="trips-info-item">
                        <span class="trips-info-label">Duration</span>
                        <span class="trips-info-value">${trip.duration_days} days</span>
                    </div>
                    <div class="trips-info-item">
                        <span class="trips-info-label">Spots Left</span>
                        <span class="trips-info-value">${spotsRemaining}</span>
                    </div>
                    <div class="trips-info-item">
                        <span class="trips-info-label">Grade Level</span>
                        <span class="trips-info-value">${escapeHtml(trip.grade_level || 'All')}</span>
                    </div>
                </div>
                
                <div class="trips-card-price">
                    <span class="trips-price-label">Price per student</span>
                    <span class="trips-price-value">Kshs. ${formatNumber(trip.price_per_student)}</span>
                </div>
                
                <div class="trips-card-footer">
                    <button class="trips-card-btn trips-view-details-btn" onclick="TripsManager.viewTripDetails(${trip.id})">
                        <i class="fas fa-info-circle"></i>
                        Details
                    </button>
                    <button class="trips-card-btn trips-register-btn" 
                            onclick="TripsManager.openRegisterModal(${trip.id})"
                            ${!canRegister ? 'disabled' : ''}>
                        <i class="fas fa-user-plus"></i>
                        Register
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }

    // Render List View
    function renderListView() {
        if (!elements.listView) return;
        
        elements.listView.innerHTML = '';
        
        state.trips.forEach(trip => {
            const item = createTripListItem(trip);
            elements.listView.appendChild(item);
        });
        
        elements.listView.style.display = 'flex';
        if (elements.gridView) {
            elements.gridView.style.display = 'none';
        }
    }

    // Create Trip List Item
    function createTripListItem(trip) {
        const item = document.createElement('div');
        item.className = 'trips-list-item';
        item.setAttribute('data-trip-id', trip.id);
        
        const isFull = trip.is_full || false;
        const canRegister = trip.can_register || false;
        
        let badgeHTML = '';
        if (trip.featured) {
            badgeHTML = '<span class="trips-card-badge trips-badge-featured">Featured</span>';
        } else if (isFull) {
            badgeHTML = '<span class="trips-card-badge trips-badge-full">Full</span>';
        } else if (canRegister) {
            badgeHTML = '<span class="trips-card-badge trips-badge-available">Available</span>';
        }
        
        item.innerHTML = `
            <div class="trips-list-image"></div>
            <div class="trips-list-content">
                <div class="trips-list-header">
                    <h3 class="trips-list-title">${escapeHtml(trip.title)}</h3>
                    ${badgeHTML}
                </div>
                <div class="trips-list-details">
                    <div class="trips-list-detail">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${escapeHtml(trip.destination)}</span>
                    </div>
                    <div class="trips-list-detail">
                        <i class="fas fa-calendar"></i>
                        <span>${formatDate(trip.start_date)}</span>
                    </div>
                    <div class="trips-list-detail">
                        <i class="fas fa-clock"></i>
                        <span>${trip.duration_days} days</span>
                    </div>
                    <div class="trips-list-detail">
                        <i class="fas fa-users"></i>
                        <span>${trip.spots_remaining} spots left</span>
                    </div>
                    <div class="trips-list-detail">
                        <i class="fas fa-dollar-sign"></i>
                        <span>$${formatNumber(trip.price_per_student)}</span>
                    </div>
                </div>
            </div>
            <div class="trips-list-actions">
                <button class="trips-card-btn trips-view-details-btn" onclick="TripsManager.viewTripDetails(${trip.id})">
                    <i class="fas fa-info-circle"></i>
                    Details
                </button>
                <button class="trips-card-btn trips-register-btn" 
                        onclick="TripsManager.openRegisterModal(${trip.id})"
                        ${!canRegister ? 'disabled' : ''}>
                    <i class="fas fa-user-plus"></i>
                    Register
                </button>
            </div>
        `;
        
        return item;
    }

    // Load Registrations
    async function loadRegistrations() {
        try {
            if (elements.registrationsContainer) {
                elements.registrationsContainer.innerHTML = '<div class="trips-spinner"></div>';
            }

            const response = await fetch('/api/parent/registrations', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to load registrations');
            }

            const result = await response.json();

            if (result.success && result.data) {
                state.registrations = result.data.registrations || [];
                renderRegistrations();
            } else {
                throw new Error(result.message || 'Failed to load registrations');
            }
        } catch (error) {
            console.error('Error loading registrations:', error);
            if (elements.registrationsContainer) {
                elements.registrationsContainer.innerHTML = `
                    <div class="trips-error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load registrations</p>
                    </div>
                `;
            }
        }
    }

    // Render Registrations
    function renderRegistrations() {
        if (!elements.registrationsContainer) return;
        
        elements.registrationsContainer.innerHTML = '';
        
        if (state.registrations.length === 0) {
            if (elements.registrationsEmpty) {
                elements.registrationsEmpty.style.display = 'block';
            }
            return;
        }
        
        if (elements.registrationsEmpty) {
            elements.registrationsEmpty.style.display = 'none';
        }
        
        state.registrations.forEach(registration => {
            const card = createRegistrationCard(registration);
            elements.registrationsContainer.appendChild(card);
        });
    }

    // Create Registration Card
    function createRegistrationCard(registration) {
        const card = document.createElement('div');
        card.className = 'trips-registration-card';
        
        let statusClass = 'trips-status-registered';
        if (registration.participant_status === 'confirmed') {
            statusClass = 'trips-status-confirmed';
        } else if (registration.participant_status === 'cancelled') {
            statusClass = 'trips-status-cancelled';
        }
        
        card.innerHTML = `
            <div class="trips-registration-header">
                <div>
                    <h4 class="trips-registration-trip-title">${escapeHtml(registration.trip_title)}</h4>
                    <div class="trips-registration-child-name">
                        <i class="fas fa-user"></i>
                        <span>${escapeHtml(registration.participant_name)}</span>
                    </div>
                </div>
                <span class="trips-registration-status ${statusClass}">${registration.participant_status}</span>
            </div>
            
            <div class="trips-registration-details">
                <div class="trips-registration-detail">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${escapeHtml(registration.destination)}</span>
                </div>
                <div class="trips-registration-detail">
                    <i class="fas fa-calendar"></i>
                    <span>${formatDate(registration.start_date)}</span>
                </div>
                <div class="trips-registration-detail">
                    <i class="fas fa-clock"></i>
                    <span>${registration.duration_days} days</span>
                </div>
                <div class="trips-registration-detail">
                    <i class="fas fa-dollar-sign"></i>
                    <span>$${formatNumber(registration.price_per_student)}</span>
                </div>
            </div>
            
            ${registration.participant_status !== 'cancelled' ? `
                <div class="trips-registration-actions">
                    <button class="trips-registration-btn trips-update-requirements-btn" 
                            onclick="TripsManager.openUpdateRequirementsModal(${registration.trip_id}, ${registration.participant_id})">
                        <i class="fas fa-edit"></i>
                        Update Requirements
                    </button>
                    <button class="trips-registration-btn trips-cancel-registration-btn" 
                            onclick="TripsManager.openCancelModal(${registration.trip_id}, ${registration.participant_id})">
                        <i class="fas fa-times-circle"></i>
                        Cancel
                    </button>
                </div>
            ` : ''}
        `;
        
        return card;
    }

    // Handle Search Input
    function handleSearchInput(event) {
        state.filters.search = event.target.value.trim();
        state.currentPage = 1;
        
        if (state.filters.search) {
            if (elements.clearSearchBtn) {
                elements.clearSearchBtn.style.display = 'flex';
            }
        } else {
            if (elements.clearSearchBtn) {
                elements.clearSearchBtn.style.display = 'none';
            }
        }
        
        loadTrips();
    }

    // Clear Search
    function clearSearch() {
        if (elements.searchInput) {
            elements.searchInput.value = '';
        }
        state.filters.search = '';
        state.currentPage = 1;
        
        if (elements.clearSearchBtn) {
            elements.clearSearchBtn.style.display = 'none';
        }
        
        loadTrips();
    }

    // Toggle Filters
    function toggleFilters() {
        if (!elements.filtersPanel) return;
        
        const isVisible = elements.filtersPanel.style.display !== 'none';
        elements.filtersPanel.style.display = isVisible ? 'none' : 'block';
        
        if (elements.toggleFiltersBtn) {
            elements.toggleFiltersBtn.classList.toggle('active', !isVisible);
        }
    }

    // Apply Filters
    function applyFilters() {
        if (elements.destinationFilter) {
            state.filters.destination = elements.destinationFilter.value.trim();
        }
        
        if (elements.categoryFilter) {
            state.filters.category = elements.categoryFilter.value;
        }
        
        if (elements.gradeLevelFilter) {
            state.filters.gradeLevel = elements.gradeLevelFilter.value;
        }
        
        if (elements.minPriceFilter) {
            const minPrice = parseFloat(elements.minPriceFilter.value);
            state.filters.minPrice = isNaN(minPrice) ? null : minPrice;
        }
        
        if (elements.maxPriceFilter) {
            const maxPrice = parseFloat(elements.maxPriceFilter.value);
            state.filters.maxPrice = isNaN(maxPrice) ? null : maxPrice;
        }
        
        if (elements.startDateFromFilter) {
            state.filters.startDateFrom = elements.startDateFromFilter.value;
        }
        
        if (elements.startDateToFilter) {
            state.filters.startDateTo = elements.startDateToFilter.value;
        }
        
        if (elements.sortByFilter) {
            state.filters.sortBy = elements.sortByFilter.value;
        }
        
        state.currentPage = 1;
        loadTrips();
        
        showToast('Filters applied successfully', 'success');
    }

    // Reset Filters
    function resetFilters() {
        state.filters = {
            search: state.filters.search,
            destination: '',
            category: '',
            gradeLevel: '',
            minPrice: null,
            maxPrice: null,
            startDateFrom: '',
            startDateTo: '',
            sortBy: 'start_date',
            sortOrder: 'asc'
        };
        
        if (elements.destinationFilter) elements.destinationFilter.value = '';
        if (elements.categoryFilter) elements.categoryFilter.value = '';
        if (elements.gradeLevelFilter) elements.gradeLevelFilter.value = '';
        if (elements.minPriceFilter) elements.minPriceFilter.value = '';
        if (elements.maxPriceFilter) elements.maxPriceFilter.value = '';
        if (elements.startDateFromFilter) elements.startDateFromFilter.value = '';
        if (elements.startDateToFilter) elements.startDateToFilter.value = '';
        if (elements.sortByFilter) elements.sortByFilter.value = 'start_date';
        
        state.currentPage = 1;
        loadTrips();
        
        showToast('Filters reset', 'success');
    }

    // Switch View
    function switchView(view) {
        state.currentView = view;
        
        if (elements.gridViewBtn && elements.listViewBtn) {
            elements.gridViewBtn.classList.toggle('active', view === 'grid');
            elements.listViewBtn.classList.toggle('active', view === 'list');
        }
        
        renderTrips();
    }

    // Change Page
    function changePage(page) {
        if (page < 1 || page > state.totalPages) return;
        
        state.currentPage = page;
        loadTrips();
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update Pagination
    function updatePagination(pagination) {
        if (!elements.paginationContainer) return;
        
        elements.paginationContainer.style.display = pagination.total_pages > 1 ? 'flex' : 'none';
        
        if (elements.prevPageBtn) {
            elements.prevPageBtn.disabled = !pagination.has_prev;
        }
        
        if (elements.nextPageBtn) {
            elements.nextPageBtn.disabled = !pagination.has_next;
        }
        
        if (elements.paginationInfo) {
            elements.paginationInfo.textContent = `Page ${pagination.page} of ${pagination.total_pages}`;
        }
    }

    // Update Results Info
    function updateResultsInfo() {
        if (!elements.resultsInfo) return;
        
        const totalTrips = state.trips.length;
        elements.resultsInfo.textContent = `Showing ${totalTrips} trip${totalTrips !== 1 ? 's' : ''}`;
    }

    // Show Loading State
    function showLoadingState() {
        hideAllStates();
        if (elements.loadingState) {
            elements.loadingState.style.display = 'flex';
        }
    }

    // Show Empty State
    function showEmptyState() {
        hideAllStates();
        if (elements.emptyState) {
            elements.emptyState.style.display = 'flex';
        }
    }

    // Show Error State
    function showErrorState(message) {
        hideAllStates();
        if (elements.errorState) {
            elements.errorState.style.display = 'flex';
        }
        if (elements.errorMessage) {
            elements.errorMessage.textContent = message;
        }
    }

    // Hide All States
    function hideAllStates() {
        if (elements.loadingState) elements.loadingState.style.display = 'none';
        if (elements.emptyState) elements.emptyState.style.display = 'none';
        if (elements.errorState) elements.errorState.style.display = 'none';
    }

    // Show Toast
    function showToast(message, type = 'success') {
        if (!elements.toast || !elements.toastMessage) return;
        
        elements.toastMessage.textContent = message;
        elements.toast.className = `trips-toast ${type}`;
        
        const icon = elements.toast.querySelector('.trips-toast-icon');
        if (icon) {
            if (type === 'success') {
                icon.className = 'fas fa-check-circle trips-toast-icon';
            } else if (type === 'error') {
                icon.className = 'fas fa-exclamation-circle trips-toast-icon';
            } else if (type === 'warning') {
                icon.className = 'fas fa-exclamation-triangle trips-toast-icon';
            }
        }
        
        elements.toast.classList.add('show');
        
        setTimeout(() => {
            elements.toast.classList.remove('show');
        }, 3000);
    }

    // Public Methods
    function viewTripDetails(tripId) {
        if (typeof TripDetailsModal !== 'undefined' && TripDetailsModal.open) {
            TripDetailsModal.open(tripId);
        } else {
            console.error('TripDetailsModal not found');
            showToast('Failed to open trip details', 'error');
        }
    }

    function openRegisterModal(tripId) {
        if (typeof RegisterChildModal !== 'undefined' && RegisterChildModal.open) {
            RegisterChildModal.open(tripId);
        } else {
            console.error('RegisterChildModal not found');
            showToast('Failed to open registration form', 'error');
        }
    }

    function openUpdateRequirementsModal(tripId, participantId) {
        if (typeof UpdateRequirementsModal !== 'undefined' && UpdateRequirementsModal.open) {
            UpdateRequirementsModal.open(tripId, participantId);
        } else {
            console.error('UpdateRequirementsModal not found');
            showToast('Failed to open update form', 'error');
        }
    }

    function openCancelModal(tripId, participantId) {
        if (typeof CancelRegistrationModal !== 'undefined' && CancelRegistrationModal.open) {
            CancelRegistrationModal.open(tripId, participantId);
        } else {
            console.error('CancelRegistrationModal not found');
            showToast('Failed to open cancel form', 'error');
        }
    }

    function refreshTrips() {
        loadTrips();
    }

    function refreshRegistrations() {
        loadRegistrations();
    }

    // Utility Functions
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        } catch (error) {
            return dateString;
        }
    }

    function formatNumber(number) {
        if (number === null || number === undefined) return '0';
        return parseFloat(number).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    // Return Public API
    return {
        init,
        viewTripDetails,
        openRegisterModal,
        openUpdateRequirementsModal,
        openCancelModal,
        refreshTrips,
        refreshRegistrations,
        showToast
    };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        TripsManager.init();
    });
} else {
    TripsManager.init();
}