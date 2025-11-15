(function() {
    'use strict';

    // State Management
    const EdusafariTripsState = {
        currentPage: 1,
        perPage: 20,
        totalPages: 1,
        totalItems: 0,
        filters: {},
        sortBy: 'created_at',
        sortOrder: 'desc',
        selectedTrips: new Set(),
        trips: []
    };

    // ============================================================================
    // INITIALIZATION
    // ============================================================================

    document.addEventListener('DOMContentLoaded', function() {
        initEdusafariTrips();
    });

    function initEdusafariTrips() {
        setupEdusafariEventListeners();
        loadEdusafariTrips();
        loadEdusafariQuickStats();
    }

    // ============================================================================
    // EVENT LISTENERS
    // ============================================================================

    function setupEdusafariEventListeners() {
        // Filter buttons
        document.getElementById('edusafariApplyFiltersBtn')?.addEventListener('click', applyEdusafariFilters);
        document.getElementById('edusafariResetFiltersBtn')?.addEventListener('click', resetEdusafariFilters);

        // Search input - debounced
        const searchInput = document.getElementById('edusafariTripSearchInput');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    applyEdusafariFilters();
                }, 500);
            });
        }

        // Pagination
        document.getElementById('edusafariFirstPageBtn')?.addEventListener('click', () => goToEdusafariPage(1));
        document.getElementById('edusafariPrevPageBtn')?.addEventListener('click', () => goToEdusafariPage(EdusafariTripsState.currentPage - 1));
        document.getElementById('edusafariNextPageBtn')?.addEventListener('click', () => goToEdusafariPage(EdusafariTripsState.currentPage + 1));
        document.getElementById('edusafariLastPageBtn')?.addEventListener('click', () => goToEdusafariPage(EdusafariTripsState.totalPages));
        document.getElementById('edusafariPageSizeSelect')?.addEventListener('change', handleEdusafariPageSizeChange);

        // Select all checkbox
        document.getElementById('edusafariSelectAllTrips')?.addEventListener('change', handleEdusafariSelectAll);

        // Bulk actions
        document.getElementById('edusafariBulkApproveBtn')?.addEventListener('click', handleEdusafariBulkApprove);
        document.getElementById('edusafariBulkFeatureBtn')?.addEventListener('click', handleEdusafariBulkFeature);
        document.getElementById('edusafariBulkCancelBtn')?.addEventListener('click', handleEdusafariBulkCancel);
        document.getElementById('edusafariClearSelectionBtn')?.addEventListener('click', clearEdusafariSelection);

        // Other buttons
        document.getElementById('edusafariTripsStatsBtn')?.addEventListener('click', openEdusafariStatsModal);
        document.getElementById('edusafariCreateTripBtn')?.addEventListener('click', () => {
            showEdusafariToast('info', 'Info', 'Trip creation feature coming soon!');
        });
        document.getElementById('edusafariRetryBtn')?.addEventListener('click', loadEdusafariTrips);

        // Sortable columns
        document.querySelectorAll('.edusafari-sortable').forEach(th => {
            th.addEventListener('click', function() {
                const sortField = this.dataset.sort;
                handleEdusafariSort(sortField);
            });
        });
    }

    // ============================================================================
    // DATA LOADING
    // ============================================================================

    async function loadEdusafariTrips() {
        showEdusafariLoading();
        hideEdusafariError();
        hideEdusafariEmpty();

        try {
            const queryParams = buildEdusafariQueryParams();
            const response = await fetch(`/api/admin/trips?${queryParams}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                EdusafariTripsState.trips = data.data.trips;
                EdusafariTripsState.currentPage = data.data.pagination.page;
                EdusafariTripsState.totalPages = data.data.pagination.total_pages;
                EdusafariTripsState.totalItems = data.data.pagination.total_items;

                renderEdusafariTrips(data.data.trips);
                updateEdusafariPagination(data.data.pagination);
                
                if (data.data.trips.length === 0) {
                    showEdusafariEmpty();
                }
            } else {
                throw new Error(data.error || 'Failed to load trips');
            }
        } catch (error) {
            console.error('Error loading trips:', error);
            showEdusafariError(error.message);
            showEdusafariToast('error', 'Error', 'Failed to load trips. Please try again.');
        } finally {
            hideEdusafariLoading();
        }
    }

    async function loadEdusafariQuickStats() {
        try {
            const response = await fetch('/api/admin/trips/statistics?period=all', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                const stats = data.data.overview;
                document.getElementById('edusafariTotalTripsCount').textContent = stats.total_trips || 0;
                document.getElementById('edusafariActiveTripsCount').textContent = stats.active_trips || 0;
                document.getElementById('edusafariPendingTripsCount').textContent = stats.draft_trips || 0;
                document.getElementById('edusafariTotalParticipantsCount').textContent = stats.total_participants || 0;
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    // ============================================================================
    // RENDERING
    // ============================================================================

    function renderEdusafariTrips(trips) {
        const tbody = document.getElementById('edusafariTripsTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        trips.forEach(trip => {
            const row = createEdusafariTripRow(trip);
            tbody.appendChild(row);
        });

        // Reattach event listeners for dynamic elements
        attachEdusafariRowEventListeners();
    }

    function createEdusafariTripRow(trip) {
        const row = document.createElement('tr');
        row.dataset.tripId = trip.id;

        if (EdusafariTripsState.selectedTrips.has(trip.id)) {
            row.classList.add('edusafari-selected');
        }

        // Calculate capacity percentage
        const capacityPercentage = trip.max_participants > 0 
            ? (trip.current_participants / trip.max_participants) * 100 
            : 0;

        let progressClass = '';
        if (capacityPercentage >= 90) progressClass = 'edusafari-progress-danger';
        else if (capacityPercentage >= 70) progressClass = 'edusafari-progress-warning';

        // Format date
        const startDate = trip.start_date ? new Date(trip.start_date).toLocaleDateString() : 'N/A';

        // Format price
        const price = `KES ${parseFloat(trip.price_per_student).toLocaleString()}`;

        // Days until trip
        const daysUntil = trip.days_until_trip !== null && trip.days_until_trip >= 0
            ? `${trip.days_until_trip} days`
            : 'Past';

        row.innerHTML = `
            <td class="edusafari-checkbox-col">
                <input type="checkbox" class="edusafari-trip-checkbox" data-trip-id="${trip.id}" 
                       ${EdusafariTripsState.selectedTrips.has(trip.id) ? 'checked' : ''}>
            </td>
            <td>
                <strong>${escapeEdusafariHtml(trip.title)}</strong>
                ${trip.featured ? '<span class="edusafari-featured-badge"><i class="fas fa-star"></i> Featured</span>' : ''}
                <div style="font-size: 12px; color: #7f8c8d; margin-top: 3px;">${daysUntil}</div>
            </td>
            <td>
                <div>${escapeEdusafariHtml(trip.destination)}</div>
                ${trip.destination_country ? `<div style="font-size: 12px; color: #7f8c8d;">${escapeEdusafariHtml(trip.destination_country)}</div>` : ''}
            </td>
            <td>${startDate}</td>
            <td>
                <span class="edusafari-status-badge edusafari-status-${trip.status}">
                    ${formatEdusafariStatus(trip.status)}
                </span>
            </td>
            <td>
                <div class="edusafari-participants-info">
                    <span class="edusafari-participants-count">
                        ${trip.current_participants} / ${trip.max_participants}
                    </span>
                    <div class="edusafari-progress-bar">
                        <div class="edusafari-progress-fill ${progressClass}" 
                             style="width: ${capacityPercentage}%"></div>
                    </div>
                </div>
            </td>
            <td>${price}</td>
            <td>
                <div class="edusafari-action-buttons">
                    <button class="edusafari-action-btn edusafari-action-view" 
                            data-action="view" data-trip-id="${trip.id}" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="edusafari-action-btn edusafari-action-edit" 
                            data-action="edit" data-trip-id="${trip.id}" title="Edit Trip">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="edusafari-action-btn edusafari-action-report" 
                            data-action="report" data-trip-id="${trip.id}" title="Generate Report">
                        <i class="fas fa-file-alt"></i>
                    </button>
                    <button class="edusafari-action-btn edusafari-action-delete" 
                            data-action="delete" data-trip-id="${trip.id}" title="Delete Trip">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;

        return row;
    }

    function attachEdusafariRowEventListeners() {
        // Checkbox listeners
        document.querySelectorAll('.edusafari-trip-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', handleEdusafariTripSelection);
        });

        // Action button listeners
        document.querySelectorAll('.edusafari-action-btn').forEach(btn => {
            btn.addEventListener('click', handleEdusafariTripAction);
        });
    }

    // ============================================================================
    // PAGINATION
    // ============================================================================

    function updateEdusafariPagination(pagination) {
        // Update info
        const showingFrom = pagination.total_items === 0 ? 0 : (pagination.page - 1) * pagination.per_page + 1;
        const showingTo = Math.min(pagination.page * pagination.per_page, pagination.total_items);

        document.getElementById('edusafariShowingFrom').textContent = showingFrom;
        document.getElementById('edusafariShowingTo').textContent = showingTo;
        document.getElementById('edusafariTotalItems').textContent = pagination.total_items;

        // Update buttons
        const firstBtn = document.getElementById('edusafariFirstPageBtn');
        const prevBtn = document.getElementById('edusafariPrevPageBtn');
        const nextBtn = document.getElementById('edusafariNextPageBtn');
        const lastBtn = document.getElementById('edusafariLastPageBtn');

        if (firstBtn) firstBtn.disabled = !pagination.has_prev;
        if (prevBtn) prevBtn.disabled = !pagination.has_prev;
        if (nextBtn) nextBtn.disabled = !pagination.has_next;
        if (lastBtn) lastBtn.disabled = !pagination.has_next;

        // Render page numbers
        renderEdusafariPageNumbers(pagination);
    }

    function renderEdusafariPageNumbers(pagination) {
        const container = document.getElementById('edusafariPageNumbers');
        if (!container) return;

        container.innerHTML = '';

        const maxButtons = 5;
        let startPage = Math.max(1, pagination.page - Math.floor(maxButtons / 2));
        let endPage = Math.min(pagination.total_pages, startPage + maxButtons - 1);

        if (endPage - startPage < maxButtons - 1) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.className = 'edusafari-page-btn';
            btn.textContent = i;
            btn.dataset.page = i;

            if (i === pagination.page) {
                btn.classList.add('edusafari-active');
            }

            btn.addEventListener('click', () => goToEdusafariPage(i));
            container.appendChild(btn);
        }
    }

    function goToEdusafariPage(page) {
        if (page < 1 || page > EdusafariTripsState.totalPages) return;
        EdusafariTripsState.currentPage = page;
        loadEdusafariTrips();
    }

    function handleEdusafariPageSizeChange(e) {
        EdusafariTripsState.perPage = parseInt(e.target.value);
        EdusafariTripsState.currentPage = 1;
        loadEdusafariTrips();
    }

    // ============================================================================
    // FILTERS & SORTING
    // ============================================================================

    function buildEdusafariQueryParams() {
        const params = new URLSearchParams();

        params.append('page', EdusafariTripsState.currentPage);
        params.append('per_page', EdusafariTripsState.perPage);
        params.append('sort_by', EdusafariTripsState.sortBy);
        params.append('sort_order', EdusafariTripsState.sortOrder);

        // Apply filters
        Object.entries(EdusafariTripsState.filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        return params.toString();
    }

    function applyEdusafariFilters() {
        const filters = {};

        // Status filter
        const statusSelect = document.getElementById('edusafariTripStatusFilter');
        if (statusSelect) {
            const selectedStatuses = Array.from(statusSelect.selectedOptions).map(opt => opt.value);
            if (selectedStatuses.length > 0) {
                filters.status = selectedStatuses.join(',');
            }
        }

        // Category filter
        const categorySelect = document.getElementById('edusafariTripCategoryFilter');
        if (categorySelect) {
            const selectedCategories = Array.from(categorySelect.selectedOptions).map(opt => opt.value);
            if (selectedCategories.length > 0) {
                filters.category = selectedCategories.join(',');
            }
        }

        // Search filter
        const searchInput = document.getElementById('edusafariTripSearchInput');
        if (searchInput && searchInput.value.trim()) {
            filters.search = searchInput.value.trim();
        }

        // Date filters
        const dateFrom = document.getElementById('edusafariTripDateFromFilter');
        if (dateFrom && dateFrom.value) {
            filters.start_date_from = dateFrom.value;
        }

        const dateTo = document.getElementById('edusafariTripDateToFilter');
        if (dateTo && dateTo.value) {
            filters.start_date_to = dateTo.value;
        }

        // Checkbox filters
        const featuredOnly = document.getElementById('edusafariFeaturedOnlyFilter');
        if (featuredOnly && featuredOnly.checked) {
            filters.featured = 'true';
        }

        const publishedOnly = document.getElementById('edusafariPublishedOnlyFilter');
        if (publishedOnly && publishedOnly.checked) {
            filters.is_published = 'true';
        }

        const availableSpots = document.getElementById('edusafariAvailableSpotsFilter');
        if (availableSpots && availableSpots.checked) {
            filters.has_available_spots = 'true';
        }

        EdusafariTripsState.filters = filters;
        EdusafariTripsState.currentPage = 1;
        loadEdusafariTrips();
    }

    function resetEdusafariFilters() {
        // Clear filter inputs
        document.getElementById('edusafariTripStatusFilter').selectedIndex = -1;
        document.getElementById('edusafariTripCategoryFilter').selectedIndex = -1;
        document.getElementById('edusafariTripSearchInput').value = '';
        document.getElementById('edusafariTripDateFromFilter').value = '';
        document.getElementById('edusafariTripDateToFilter').value = '';
        document.getElementById('edusafariFeaturedOnlyFilter').checked = false;
        document.getElementById('edusafariPublishedOnlyFilter').checked = false;
        document.getElementById('edusafariAvailableSpotsFilter').checked = false;

        EdusafariTripsState.filters = {};
        EdusafariTripsState.currentPage = 1;
        loadEdusafariTrips();
    }

    function handleEdusafariSort(field) {
        if (EdusafariTripsState.sortBy === field) {
            EdusafariTripsState.sortOrder = EdusafariTripsState.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            EdusafariTripsState.sortBy = field;
            EdusafariTripsState.sortOrder = 'asc';
        }

        loadEdusafariTrips();
    }

    // ============================================================================
    // SELECTION HANDLING
    // ============================================================================

    function handleEdusafariSelectAll(e) {
        const isChecked = e.target.checked;
        
        document.querySelectorAll('.edusafari-trip-checkbox').forEach(checkbox => {
            checkbox.checked = isChecked;
            const tripId = parseInt(checkbox.dataset.tripId);
            
            if (isChecked) {
                EdusafariTripsState.selectedTrips.add(tripId);
                checkbox.closest('tr').classList.add('edusafari-selected');
            } else {
                EdusafariTripsState.selectedTrips.delete(tripId);
                checkbox.closest('tr').classList.remove('edusafari-selected');
            }
        });

        updateEdusafariBulkActionsBar();
    }

    function handleEdusafariTripSelection(e) {
        const tripId = parseInt(e.target.dataset.tripId);
        const row = e.target.closest('tr');

        if (e.target.checked) {
            EdusafariTripsState.selectedTrips.add(tripId);
            row.classList.add('edusafari-selected');
        } else {
            EdusafariTripsState.selectedTrips.delete(tripId);
            row.classList.remove('edusafari-selected');
        }

        updateEdusafariBulkActionsBar();
    }

    function clearEdusafariSelection() {
        EdusafariTripsState.selectedTrips.clear();
        document.querySelectorAll('.edusafari-trip-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.querySelectorAll('tr.edusafari-selected').forEach(row => {
            row.classList.remove('edusafari-selected');
        });
        document.getElementById('edusafariSelectAllTrips').checked = false;
        updateEdusafariBulkActionsBar();
    }

    function updateEdusafariBulkActionsBar() {
        const bulkBar = document.getElementById('edusafariBulkActionsBar');
        const selectedCount = document.getElementById('edusafariSelectedCount');

        if (EdusafariTripsState.selectedTrips.size > 0) {
            bulkBar.style.display = 'flex';
            selectedCount.textContent = EdusafariTripsState.selectedTrips.size;
        } else {
            bulkBar.style.display = 'none';
        }
    }

    // ============================================================================
    // TRIP ACTIONS
    // ============================================================================

    function handleEdusafariTripAction(e) {
        const btn = e.currentTarget;
        const action = btn.dataset.action;
        const tripId = parseInt(btn.dataset.tripId);

        switch (action) {
            case 'view':
                openEdusafariViewTripModal(tripId);
                break;
            case 'edit':
                openEdusafariEditTripModal(tripId);
                break;
            case 'report':
                openEdusafariReportModal(tripId);
                break;
            case 'delete':
                handleEdusafariDeleteTrip(tripId);
                break;
        }
    }

    async function handleEdusafariDeleteTrip(tripId) {
        if (!confirm('Are you sure you want to delete this trip? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/trips/${tripId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                showEdusafariToast('success', 'Success', data.message || 'Trip deleted successfully');
                loadEdusafariTrips();
                loadEdusafariQuickStats();
            } else {
                throw new Error(data.error || 'Failed to delete trip');
            }
        } catch (error) {
            console.error('Error deleting trip:', error);
            showEdusafariToast('error', 'Error', error.message);
        }
    }

    // ============================================================================
    // BULK ACTIONS
    // ============================================================================

    async function handleEdusafariBulkApprove() {
        if (EdusafariTripsState.selectedTrips.size === 0) return;

        if (!confirm(`Approve ${EdusafariTripsState.selectedTrips.size} trip(s)?`)) {
            return;
        }

        try {
            const response = await fetch('/api/admin/trips/bulk/status', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    trip_ids: Array.from(EdusafariTripsState.selectedTrips),
                    status: 'published'
                })
            });

            const data = await response.json();

            if (data.success) {
                showEdusafariToast('success', 'Success', `${data.data.updated_count} trip(s) approved`);
                clearEdusafariSelection();
                loadEdusafariTrips();
                loadEdusafariQuickStats();
            } else {
                throw new Error(data.error || 'Bulk update failed');
            }
        } catch (error) {
            console.error('Error in bulk approve:', error);
            showEdusafariToast('error', 'Error', error.message);
        }
    }

    async function handleEdusafariBulkFeature() {
        if (EdusafariTripsState.selectedTrips.size === 0) return;

        if (!confirm(`Feature ${EdusafariTripsState.selectedTrips.size} trip(s)?`)) {
            return;
        }

        let successCount = 0;
        let failCount = 0;

        for (const tripId of EdusafariTripsState.selectedTrips) {
            try {
                const response = await fetch(`/api/admin/trips/${tripId}/feature`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ featured: true })
                });

                const data = await response.json();
                if (data.success) {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (error) {
                failCount++;
            }
        }

        showEdusafariToast('success', 'Success', `${successCount} trip(s) featured${failCount > 0 ? `, ${failCount} failed` : ''}`);
        clearEdusafariSelection();
        loadEdusafariTrips();
    }

    async function handleEdusafariBulkCancel() {
        if (EdusafariTripsState.selectedTrips.size === 0) return;

        if (!confirm(`Cancel ${EdusafariTripsState.selectedTrips.size} trip(s)? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch('/api/admin/trips/bulk/status', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    trip_ids: Array.from(EdusafariTripsState.selectedTrips),
                    status: 'cancelled',
                    reason: 'Bulk cancellation by administrator'
                })
            });

            const data = await response.json();

            if (data.success) {
                showEdusafariToast('success', 'Success', `${data.data.updated_count} trip(s) cancelled`);
                clearEdusafariSelection();
                loadEdusafariTrips();
                loadEdusafariQuickStats();
            } else {
                throw new Error(data.error || 'Bulk cancel failed');
            }
        } catch (error) {
            console.error('Error in bulk cancel:', error);
            showEdusafariToast('error', 'Error', error.message);
        }
    }

    // ============================================================================
    // MODAL FUNCTIONS (Placeholder - will be implemented in separate files)
    // ============================================================================

    function openEdusafariViewTripModal(tripId) {
        if (typeof window.EdusafariViewTripModal !== 'undefined') {
            window.EdusafariViewTripModal.open(tripId);
        } else {
            showEdusafariToast('info', 'Info', 'Loading trip details...');
        }
    }

    function openEdusafariEditTripModal(tripId) {
        if (typeof window.EdusafariEditTripModal !== 'undefined') {
            window.EdusafariEditTripModal.open(tripId);
        } else {
            showEdusafariToast('info', 'Info', 'Loading trip editor...');
        }
    }

    function openEdusafariReportModal(tripId) {
        if (typeof window.EdusafariReportModal !== 'undefined') {
            window.EdusafariReportModal.open(tripId);
        } else {
            showEdusafariToast('info', 'Info', 'Generating report...');
        }
    }

    function openEdusafariStatsModal() {
        if (typeof window.EdusafariStatsModal !== 'undefined') {
            window.EdusafariStatsModal.open();
        } else {
            showEdusafariToast('info', 'Info', 'Loading statistics...');
        }
    }

    // ============================================================================
    // UTILITY FUNCTIONS
    // ============================================================================

    function showEdusafariLoading() {
        document.getElementById('edusafariTripsLoading').style.display = 'block';
        document.getElementById('edusafariTripsTableContainer').style.opacity = '0.5';
    }

    function hideEdusafariLoading() {
        document.getElementById('edusafariTripsLoading').style.display = 'none';
        document.getElementById('edusafariTripsTableContainer').style.opacity = '1';
    }

    function showEdusafariError(message) {
        const errorState = document.getElementById('edusafariErrorState');
        const errorMessage = document.getElementById('edusafariErrorMessage');
        
        if (errorState && errorMessage) {
            errorMessage.textContent = message || 'An error occurred while loading trips.';
            errorState.style.display = 'block';
        }
        
        document.querySelector('.edusafari-trips-table').style.display = 'none';
    }

    function hideEdusafariError() {
        const errorState = document.getElementById('edusafariErrorState');
        if (errorState) {
            errorState.style.display = 'none';
        }
        document.querySelector('.edusafari-trips-table').style.display = 'table';
    }

    function showEdusafariEmpty() {
        document.getElementById('edusafariEmptyState').style.display = 'block';
        document.querySelector('.edusafari-trips-table').style.display = 'none';
    }

    function hideEdusafariEmpty() {
        document.getElementById('edusafariEmptyState').style.display = 'none';
        document.querySelector('.edusafari-trips-table').style.display = 'table';
    }

    function showEdusafariToast(type, title, message) {
        const container = document.getElementById('edusafariToastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `edusafari-toast edusafari-toast-${type}`;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        toast.innerHTML = `
            <div class="edusafari-toast-icon">
                <i class="fas ${icons[type] || icons.info}"></i>
            </div>
            <div class="edusafari-toast-content">
                <div class="edusafari-toast-title">${escapeEdusafariHtml(title)}</div>
                <div class="edusafari-toast-message">${escapeEdusafariHtml(message)}</div>
            </div>
            <button class="edusafari-toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(toast);

        // Close button
        toast.querySelector('.edusafari-toast-close').addEventListener('click', () => {
            toast.remove();
        });

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    function formatEdusafariStatus(status) {
        const statusMap = {
            'draft': 'Draft',
            'published': 'Published',
            'registration_open': 'Registration Open',
            'registration_closed': 'Registration Closed',
            'full': 'Full',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled'
        };
        return statusMap[status] || status;
    }

    function escapeEdusafariHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Export functions for use in modals
    window.EdusafariTrips = {
        reload: loadEdusafariTrips,
        reloadStats: loadEdusafariQuickStats,
        showToast: showEdusafariToast,
        getState: () => EdusafariTripsState
    };

})();