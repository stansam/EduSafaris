// Children Tab Management Script
let childrenData = [];
let filteredChildren = [];

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    loadChildren();
    loadTripsForFilter();
});

// Load all children
async function loadChildren() {
    const loadingState = document.getElementById('childrenLoadingState');
    const errorState = document.getElementById('childrenErrorState');
    const emptyState = document.getElementById('childrenEmptyState');
    const childrenGrid = document.getElementById('childrenGrid');
    
    // Show loading
    loadingState.style.display = 'block';
    errorState.style.display = 'none';
    emptyState.style.display = 'none';
    childrenGrid.style.display = 'none';
    
    try {
        const response = await fetch('/api/parent/children', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        loadingState.style.display = 'none';
        
        if (data.success && data.children && data.children.length > 0) {
            childrenData = data.children;
            filteredChildren = [...childrenData];
            renderChildren(filteredChildren);
            childrenGrid.style.display = 'grid';
        } else {
            emptyState.style.display = 'flex';
        }
        
    } catch (error) {
        console.error('Error loading children:', error);
        loadingState.style.display = 'none';
        errorState.style.display = 'block';
        document.getElementById('childrenErrorMessage').textContent = 
            'Failed to load children. Please check your connection and try again.';
    }
}

// Render children cards
function renderChildren(children) {
    const childrenGrid = document.getElementById('childrenGrid');
    
    if (!children || children.length === 0) {
        document.getElementById('childrenEmptyState').style.display = 'block';
        childrenGrid.style.display = 'none';
        return;
    }
    
    childrenGrid.innerHTML = children.map(child => createChildCard(child)).join('');
    childrenGrid.style.display = 'grid';
    document.getElementById('childrenEmptyState').style.display = 'none';
}

// Create individual child card HTML
function createChildCard(child) {
    const statusClass = child.status ? child.status.toLowerCase() : 'registered';
    const paymentStatus = child.payment_status || 'pending';
    const trip = child.trip || {};
    
    return `
        <div class="child-card" data-child-id="${child.id}">
            <div class="child-header">
                <div class="child-name-section">
                    <div class="child-name">${escapeHtml(child.first_name)} ${escapeHtml(child.last_name)}</div>
                    <span class="status-badge ${statusClass}">${child.status || 'Registered'}</span>
                </div>
                <i class="fas fa-child child-icon"></i>
            </div>
            
            ${trip.title ? `
                <div class="trip-info-section">
                    <div class="trip-label">Current Trip</div>
                    <div class="trip-name">${escapeHtml(trip.title)}</div>
                    ${trip.start_date ? `
                        <div class="trip-dates">${formatDate(trip.start_date)} to ${formatDate(trip.end_date)}</div>
                    ` : ''}
                </div>
            ` : '<div class="trip-info-section"><div class="trip-label">No active trip</div></div>'}
            
            ${child.medical_conditions || child.allergies ? `
                <div class="medical-info">
                    <div class="medical-label"><i class="fas fa-heartbeat"></i> Medical Info:</div>
                    <div class="medical-detail">
                        ${child.allergies ? escapeHtml(child.allergies) : ''}
                        ${child.medical_conditions ? (child.allergies ? ', ' : '') + escapeHtml(child.medical_conditions) : ''}
                    </div>
                </div>
            ` : ''}
            
            <div class="action-buttons">
                <button class="action-btn primary" onclick="openViewChildModal(${child.id})">
                    <i class="fas fa-eye"></i> View Profile
                </button>
                <button class="action-btn secondary" onclick="openUpdateChildModal(${child.id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="action-btn warning" onclick="openUploadDocumentModal(${child.id})">
                    <i class="fas fa-upload"></i> Upload Doc
                </button>
                <button class="action-btn success" onclick="openConsentModal(${child.id})">
                    <i class="fas fa-file-signature"></i> Consent
                </button>
            </div>
            
            <div class="info-row">
                <span class="info-label"><i class="fas fa-money-bill-wave"></i> Payment</span>
                <span class="payment-badge ${paymentStatus}">${formatPaymentStatus(paymentStatus)}</span>
            </div>
            
            ${child.amount_paid ? `
                <div class="info-row">
                    <span class="info-label">Amount Paid</span>
                    <span class="info-value">KES ${formatCurrency(child.amount_paid)}</span>
                </div>
            ` : ''}
        </div>
    `;
}

// Load trips for filter dropdown
async function loadTripsForFilter() {
    try {
        const response = await fetch('/api/parent/trips', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.trips) {
                const tripFilter = document.getElementById('tripFilter');
                data.trips.forEach(trip => {
                    const option = document.createElement('option');
                    option.value = trip.id;
                    option.textContent = trip.title;
                    tripFilter.appendChild(option); 
                });
            }
        }
    } catch (error) {
        console.error('Error loading trips for filter:', error);
    }
}

// Filter children based on selected criteria
function filterChildren() {
    const statusFilter = document.getElementById('statusFilter').value.toLowerCase();
    const tripFilter = document.getElementById('tripFilter').value;
    const paymentFilter = document.getElementById('paymentFilter').value.toLowerCase();
    
    filteredChildren = childrenData.filter(child => {
        const matchesStatus = !statusFilter || 
            (child.status && child.status.toLowerCase() === statusFilter);
        
        const matchesTrip = !tripFilter || 
            (child.trip_id && child.trip_id.toString() === tripFilter);
        
        const matchesPayment = !paymentFilter || 
            (child.payment_status && child.payment_status.toLowerCase() === paymentFilter);
        
        return matchesStatus && matchesTrip && matchesPayment;
    });
    
    renderChildren(filteredChildren);
}

// Clear all filters
function clearFilters() {
    document.getElementById('statusFilter').value = '';
    document.getElementById('tripFilter').value = '';
    document.getElementById('paymentFilter').value = '';
    filteredChildren = [...childrenData];
    renderChildren(filteredChildren);
}

// Get child data by ID
function getChildById(childId) {
    return childrenData.find(child => child.id === childId);
}

// Utility Functions
function getAuthToken() {
    return localStorage.getItem('authToken') || '';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatCurrency(amount) {
    if (!amount) return '0.00';
    return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatPaymentStatus(status) {
    const statusMap = {
        'paid': 'Paid',
        'pending': 'Pending',
        'partial': 'Partial Payment'
    };
    return statusMap[status] || status;
}

// Show notification
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Refresh children data after updates
function refreshChildren() {
    loadChildren();
}