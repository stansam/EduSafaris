/* ===================================
   ADMIN VENDORS MANAGEMENT JAVASCRIPT
   =================================== */

// Global Variables
let vendorsData = [];
let filteredVendors = [];
let selectedVendorIds = new Set();
let currentVendorPage = 1;
let vendorPageSize = 20;
let totalVendorPages = 1;
let currentSortField = 'created_at';
let currentSortOrder = 'desc';
let searchTimeout = null;

// API Base URL (adjust as needed)
const VENDOR_API_BASE = '/api/admin/vendor';

/* ===================================
   Initialization
   =================================== */
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the vendors tab
    if (document.querySelector('.admin-vendors-container')) {
        initializeVendorsManagement();
    }
});

function initializeVendorsManagement() {
    console.log('Initializing vendors management...');
    loadVendorsData();
    
    // Set up event listeners
    setupVendorEventListeners();
}

function setupVendorEventListeners() {
    // Page size change
    const pageSizeSelect = document.getElementById('vendorPageSize');
    if (pageSizeSelect) {
        vendorPageSize = parseInt(pageSizeSelect.value);
    }
}

/* ===================================
   Data Loading
   =================================== */
async function loadVendorsData(page = 1) {
    try {
        showVendorLoading(true);
        hideVendorError();
        
        // Build query parameters
        const params = new URLSearchParams({
            page: page,
            per_page: vendorPageSize,
            sort_by: currentSortField,
            sort_order: currentSortOrder
        });
        
        // Add filters
        const searchTerm = document.getElementById('vendorSearchInput')?.value.trim();
        if (searchTerm) params.append('search', searchTerm);
        
        const typeFilter = document.getElementById('vendorTypeFilter')?.value;
        if (typeFilter) params.append('business_type', typeFilter);
        
        const statusFilter = document.getElementById('vendorStatusFilter')?.value;
        if (statusFilter) params.append('is_verified', statusFilter);
        
        const activeFilter = document.getElementById('vendorActiveFilter')?.value;
        if (activeFilter) params.append('is_active', activeFilter);
        
        const cityFilter = document.getElementById('vendorCityFilter')?.value.trim();
        if (cityFilter) params.append('city', cityFilter);
        
        const ratingFilter = document.getElementById('vendorRatingFilter')?.value;
        if (ratingFilter) params.append('min_rating', ratingFilter);
        
        const response = await fetch(`${VENDOR_API_BASE}?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            vendorsData = result.data.vendors;
            filteredVendors = [...vendorsData];
            currentVendorPage = result.data.pagination.page;
            totalVendorPages = result.data.pagination.total_pages;
            
            // Update statistics
            updateVendorStatistics(result.data.statistics);
            
            // Render table
            renderVendorsTable();
            renderVendorPagination(result.data.pagination);
            
            showVendorLoading(false);
        } else {
            throw new Error(result.error || 'Failed to load vendors');
        }
        
    } catch (error) {
        console.error('Error loading vendors:', error);
        showVendorError(error.message);
        showVendorLoading(false);
    }
}

/* ===================================
   UI Rendering
   =================================== */
function updateVendorStatistics(stats) {
    document.getElementById('vendorStatTotal').textContent = stats.total_vendors || 0;
    document.getElementById('vendorStatVerified').textContent = stats.verified_vendors || 0;
    document.getElementById('vendorStatActive').textContent = stats.active_vendors || 0;
    document.getElementById('vendorStatPending').textContent = stats.unverified_vendors || 0;
}

function renderVendorsTable() {
    const tbody = document.getElementById('vendorsTableBody');
    const emptyState = document.getElementById('vendorsTableEmpty');
    const tableWrapper = document.getElementById('vendorsTableWrapper');
    
    if (!tbody) return;
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Update results count
    document.getElementById('vendorResultsCount').textContent = filteredVendors.length;
    
    if (filteredVendors.length === 0) {
        emptyState.style.display = 'block';
        tableWrapper.style.display = 'none';
        return;
    }
    
    emptyState.style.display = 'none';
    tableWrapper.style.display = 'block';
    
    // Render each vendor row
    filteredVendors.forEach(vendor => {
        const row = createVendorRow(vendor);
        tbody.appendChild(row);
    });
}

function createVendorRow(vendor) {
    const tr = document.createElement('tr');
    tr.className = selectedVendorIds.has(vendor.id) ? 'vendor-row-selected' : '';
    tr.setAttribute('data-vendor-id', vendor.id);
    
    tr.innerHTML = `
        <td class="col-checkbox">
            <input 
                type="checkbox" 
                class="vendor-checkbox" 
                value="${vendor.id}"
                ${selectedVendorIds.has(vendor.id) ? 'checked' : ''}
                onchange="handleVendorSelection(${vendor.id})"
            >
        </td>
        <td class="vendor-name-cell">
            <div class="vendor-name-primary">${escapeHtml(vendor.business_name)}</div>
            <div class="vendor-name-secondary">${escapeHtml(vendor.user?.full_name || 'N/A')}</div>
        </td>
        <td>
            <span class="vendor-type-badge">${formatBusinessType(vendor.business_type)}</span>
        </td>
        <td class="vendor-contact-cell">
            <div class="contact-item">
                <i class="fas fa-envelope"></i>
                <span>${escapeHtml(vendor.contact_email)}</span>
            </div>
            <div class="contact-item">
                <i class="fas fa-phone"></i>
                <span>${escapeHtml(vendor.contact_phone || 'N/A')}</span>
            </div>
        </td>
        <td class="vendor-location-cell">
            <span class="location-city">${escapeHtml(vendor.city || 'N/A')}</span>
            <span class="location-country">${escapeHtml(vendor.country || '')}</span>
        </td>
        <td>
            <div class="vendor-rating-cell">
                <div class="rating-stars">
                    <span class="rating-value">${vendor.average_rating?.toFixed(1) || '0.0'}</span>
                    <i class="fas fa-star"></i>
                </div>
                <span class="rating-count">(${vendor.total_reviews || 0} reviews)</span>
            </div>
        </td>
        <td>
            <span class="vendor-status-badge ${vendor.is_active ? 'status-active' : 'status-inactive'}">
                <i class="fas ${vendor.is_active ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                ${vendor.is_active ? 'Active' : 'Inactive'}
            </span>
        </td>
        <td>
            <span class="vendor-verification-badge ${vendor.is_verified ? 'verification-verified' : 'verification-pending'}">
                <i class="fas ${vendor.is_verified ? 'fa-check-circle' : 'fa-clock'}"></i>
                ${vendor.is_verified ? 'Verified' : 'Pending'}
            </span>
        </td>
        <td class="vendor-date-cell">
            ${formatDate(vendor.created_at)}
        </td>
        <td class="vendor-actions-cell">
            <button class="btn-vendor-action btn-vendor-view" onclick="viewVendorDetails(${vendor.id})" title="View Details">
                <i class="fas fa-eye"></i>
            </button>
            <button class="btn-vendor-action btn-vendor-edit" onclick="editVendor(${vendor.id})" title="Edit">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn-vendor-action btn-vendor-more" onclick="showVendorActions(${vendor.id})" title="More Actions">
                <i class="fas fa-ellipsis-v"></i>
            </button>
        </td>
    `;
    
    return tr;
}

function renderVendorPagination(pagination) {
    const paginationInfo = document.getElementById('vendorPaginationInfo');
    const pageNumbers = document.getElementById('vendorPageNumbers');
    const btnFirst = document.getElementById('vendorBtnFirst');
    const btnPrev = document.getElementById('vendorBtnPrev');
    const btnNext = document.getElementById('vendorBtnNext');
    const btnLast = document.getElementById('vendorBtnLast');
    
    if (!pagination) return;
    
    // Update info
    const start = ((pagination.page - 1) * pagination.per_page) + 1;
    const end = Math.min(pagination.page * pagination.per_page, pagination.total_items);
    paginationInfo.textContent = `Showing ${start}-${end} of ${pagination.total_items} vendors`;
    
    // Update buttons
    btnFirst.disabled = !pagination.has_prev;
    btnPrev.disabled = !pagination.has_prev;
    btnNext.disabled = !pagination.has_next;
    btnLast.disabled = !pagination.has_next;
    
    // Render page numbers
    pageNumbers.innerHTML = '';
    const maxPages = 5;
    let startPage = Math.max(1, pagination.page - Math.floor(maxPages / 2));
    let endPage = Math.min(pagination.total_pages, startPage + maxPages - 1);
    
    if (endPage - startPage < maxPages - 1) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.className = `btn-page ${i === pagination.page ? 'active' : ''}`;
        btn.textContent = i;
        btn.onclick = () => goToVendorPage(i);
        pageNumbers.appendChild(btn);
    }
}

/* ===================================
   Filter and Search
   =================================== */
function handleVendorSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        applyVendorFilters();
    }, 500);
}

function applyVendorFilters() {
    currentVendorPage = 1;
    loadVendorsData(currentVendorPage);
}

function clearVendorFilters() {
    document.getElementById('vendorSearchInput').value = '';
    document.getElementById('vendorTypeFilter').value = '';
    document.getElementById('vendorStatusFilter').value = '';
    document.getElementById('vendorActiveFilter').value = '';
    document.getElementById('vendorCityFilter').value = '';
    document.getElementById('vendorRatingFilter').value = '';
    applyVendorFilters();
}

/* ===================================
   Sorting
   =================================== */
function sortVendorsBy(field) {
    if (currentSortField === field) {
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortField = field;
        currentSortOrder = 'desc';
    }
    
    // Update sort icons
    document.querySelectorAll('.vendors-table .sort-icon').forEach(icon => {
        icon.className = 'fas fa-sort sort-icon';
    });
    
    const sortedHeader = event.target.closest('th');
    if (sortedHeader) {
        const icon = sortedHeader.querySelector('.sort-icon');
        if (icon) {
            icon.className = currentSortOrder === 'asc' ? 
                'fas fa-sort-up sort-icon' : 
                'fas fa-sort-down sort-icon';
        }
    }
    
    loadVendorsData(currentVendorPage);
}

/* ===================================
   Selection Management
   =================================== */
function handleVendorSelection(vendorId) {
    if (selectedVendorIds.has(vendorId)) {
        selectedVendorIds.delete(vendorId);
    } else {
        selectedVendorIds.add(vendorId);
    }
    
    updateVendorSelectionUI();
}

function toggleAllVendorSelection() {
    const selectAllCheckbox = document.getElementById('vendorSelectAll');
    
    if (selectAllCheckbox.checked) {
        filteredVendors.forEach(vendor => selectedVendorIds.add(vendor.id));
    } else {
        selectedVendorIds.clear();
    }
    
    updateVendorSelectionUI();
    renderVendorsTable();
}

function clearVendorSelection() {
    selectedVendorIds.clear();
    document.getElementById('vendorSelectAll').checked = false;
    updateVendorSelectionUI();
    renderVendorsTable();
}

function updateVendorSelectionUI() {
    const bulkActionsBar = document.getElementById('vendorBulkActionsBar');
    const selectedCount = document.getElementById('vendorBulkSelectedCount');
    
    if (selectedVendorIds.size > 0) {
        bulkActionsBar.style.display = 'flex';
        selectedCount.textContent = selectedVendorIds.size;
    } else {
        bulkActionsBar.style.display = 'none';
    }
    
    // Update select all checkbox
    const selectAllCheckbox = document.getElementById('vendorSelectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = selectedVendorIds.size === filteredVendors.length && filteredVendors.length > 0;
    }
}

/* ===================================
   Pagination
   =================================== */
function goToVendorPage(page) {
    if (page === 'last') {
        page = totalVendorPages;
    }
    
    if (page >= 1 && page <= totalVendorPages) {
        currentVendorPage = page;
        loadVendorsData(page);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function previousVendorPage() {
    if (currentVendorPage > 1) {
        goToVendorPage(currentVendorPage - 1);
    }
}

function nextVendorPage() {
    if (currentVendorPage < totalVendorPages) {
        goToVendorPage(currentVendorPage + 1);
    }
}

function changeVendorPageSize() {
    const pageSizeSelect = document.getElementById('vendorPageSize');
    vendorPageSize = parseInt(pageSizeSelect.value);
    currentVendorPage = 1;
    loadVendorsData(1);
}

/* ===================================
   Vendor Actions
   =================================== */
function viewVendorDetails(vendorId) {
    // Open view modal (to be implemented)
    openVendorViewModal(vendorId);
}

function editVendor(vendorId) {
    // Open edit modal (to be implemented)
    openVendorEditModal(vendorId);
}

function showVendorActions(vendorId) {
    const vendor = vendorsData.find(v => v.id === vendorId);
    if (!vendor) return;
    
    // Show context menu or dropdown with more actions
    openVendorActionsModal(vendorId, vendor);
}

/* ===================================
   Bulk Actions
   =================================== */
async function bulkVerifyVendors() {
    if (selectedVendorIds.size === 0) {
        showNotification('Please select vendors to verify', 'warning');
        return;
    }
    
    if (!confirm(`Are you sure you want to verify ${selectedVendorIds.size} vendor(s)?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${VENDOR_API_BASE}/bulk/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                vendor_ids: Array.from(selectedVendorIds),
                notes: 'Bulk verification'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            clearVendorSelection();
            loadVendorsData(currentVendorPage);
        } else {
            showNotification(result.error || 'Failed to verify vendors', 'error');
        }
    } catch (error) {
        console.error('Error in bulk verify:', error);
        showNotification('An error occurred while verifying vendors', 'error');
    }
}

async function bulkDeactivateVendors() {
    if (selectedVendorIds.size === 0) {
        showNotification('Please select vendors to deactivate', 'warning');
        return;
    }
    
    const reason = prompt(`Reason for deactivating ${selectedVendorIds.size} vendor(s):`);
    if (!reason) return;
    
    try {
        const response = await fetch(`${VENDOR_API_BASE}/bulk/deactivate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                vendor_ids: Array.from(selectedVendorIds),
                reason: reason
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            clearVendorSelection();
            loadVendorsData(currentVendorPage);
        } else {
            showNotification(result.error || 'Failed to deactivate vendors', 'error');
        }
    } catch (error) {
        console.error('Error in bulk deactivate:', error);
        showNotification('An error occurred while deactivating vendors', 'error');
    }
}

/* ===================================
   Export
   =================================== */
function exportVendorsData() {
    // Build query parameters for export
    const params = new URLSearchParams();
    
    const searchTerm = document.getElementById('vendorSearchInput')?.value.trim();
    if (searchTerm) params.append('search', searchTerm);
    
    const typeFilter = document.getElementById('vendorTypeFilter')?.value;
    if (typeFilter) params.append('business_type', typeFilter);
    
    const statusFilter = document.getElementById('vendorStatusFilter')?.value;
    if (statusFilter) params.append('is_verified', statusFilter);
    
    const activeFilter = document.getElementById('vendorActiveFilter')?.value;
    if (activeFilter) params.append('is_active', activeFilter);
    
    // Open export URL
    window.open(`${VENDOR_API_BASE}/export?${params.toString()}`, '_blank');
    showNotification('Export started. Download will begin shortly.', 'success');
}

/* ===================================
   UI Helper Functions
   =================================== */
function showVendorLoading(show) {
    const loading = document.getElementById('vendorsTableLoading');
    const tableWrapper = document.getElementById('vendorsTableWrapper');
    
    if (loading) loading.style.display = show ? 'flex' : 'none';
    if (tableWrapper) tableWrapper.style.display = show ? 'none' : 'block';
}

function showVendorError(message) {
    const errorDiv = document.getElementById('vendorsTableError');
    const errorMessage = document.getElementById('vendorsErrorMessage');
    const tableWrapper = document.getElementById('vendorsTableWrapper');
    
    if (errorDiv) errorDiv.style.display = 'flex';
    if (errorMessage) errorMessage.textContent = message;
    if (tableWrapper) tableWrapper.style.display = 'none';
}

function hideVendorError() {
    const errorDiv = document.getElementById('vendorsTableError');
    if (errorDiv) errorDiv.style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Implementation depends on your notification system
    // This is a simple alert fallback
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    
    alert(`${icons[type] || ''} ${message}`);
}

/* ===================================
   Utility Functions
   =================================== */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatBusinessType(type) {
    if (!type) return 'N/A';
    return type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}