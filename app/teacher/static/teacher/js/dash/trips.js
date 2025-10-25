// State management
let currentPage = 1;
let currentFilters = {
    status: 'all',
    search: ''
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadTrips();
    setupFilters();
});

// Setup filter event listeners
function setupFilters() {
    const statusFilter = document.getElementById('statusFilter');
    const searchFilter = document.getElementById('searchFilter');

    statusFilter.addEventListener('change', function() {
        currentFilters.status = this.value;
        currentPage = 1;
        loadTrips();
    });

    let searchTimeout;
    searchFilter.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.search = this.value;
            currentPage = 1;
            loadTrips();
        }, 500);
    });
}

// Load trips from API
async function loadTrips() {
    const container = document.getElementById('tripsContainer');
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

    try {
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 9,
            ...(currentFilters.status !== 'all' && { status: currentFilters.status }),
            ...(currentFilters.search && { search: currentFilters.search })
        });

        const response = await fetch(`api/trips?${params}`);
        const data = await response.json();

        if (data.success) {
            renderTrips(data.trips);
            renderPagination(data.pagination);
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Error loading trips:', error);
        showError('Failed to load trips. Please try again.');
    }
}

// Render trips
function renderTrips(trips) {
    const container = document.getElementById('tripsContainer');

    if (trips.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <div class="empty-state-title">No trips found</div>
                <div class="empty-state-text">Try adjusting your filters or create a new trip</div>
            </div>
        `;
        return;
    }

    container.innerHTML = trips.map(trip => `
        <div class="teach-trip-card">
            <div class="teach-trip-header">
                <div>
                    <h3 class="teach-trip-title-text">${escapeHtml(trip.title)}</h3>
                    <p class="teach-trip-location">${escapeHtml(trip.destination)}</p>
                </div>
                <span class="teach-trip-status-badge status-${trip.status}">${trip.status.replace('_', ' ')}</span>
            </div>
            <div class="teach-trip-details">
                <div class="teach-trip-detail-row">
                    <svg class="teach-trip-detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    <span>${formatDate(trip.start_date)} to ${formatDate(trip.end_date)}</span>
                </div>
                <div class="teach-trip-detail-row">
                    <svg class="teach-trip-detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                    <span>${trip.current_participants_count || 0}/${trip.max_participants} spots filled</span>
                </div>
                ${trip.pending_consents > 0 ? `
                <div class="teach-trip-detail-row" style="color: #ed8936;">
                    <svg class="teach-trip-detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <span>${trip.pending_consents} pending consent${trip.pending_consents !== 1 ? 's' : ''}</span>
                </div>
                ` : ''}
            </div>
            <div class="teach-trip-actions">
                <button class="teach-trip-btn teach-trip-btn-secondary" onclick="viewTripDetails(${trip.id})">View Details</button>
                <button class="teach-trip-btn teach-trip-btn-primary" onclick="viewParticipants(${trip.id}, '${escapeHtml(trip.title)}')">Participants</button>
            </div>
        </div>
    `).join('');
}

// Render pagination
function renderPagination(pagination) {
    const container = document.getElementById('paginationContainer');
    
    if (pagination.pages <= 1) {
        container.innerHTML = '';
        return;
    }

    const buttons = [];
    
    // Previous button
    buttons.push(`
        <button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} 
            onclick="changePage(${currentPage - 1})">Previous</button>
    `);

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(pagination.pages, currentPage + 2);

    if (startPage > 1) {
        buttons.push(`<button class="pagination-btn" onclick="changePage(1)">1</button>`);
        if (startPage > 2) buttons.push(`<span class="pagination-info">...</span>`);
    }

    for (let i = startPage; i <= endPage; i++) {
        buttons.push(`
            <button class="pagination-btn ${i === currentPage ? 'active' : ''}" 
                onclick="changePage(${i})">${i}</button>
        `);
    }

    if (endPage < pagination.pages) {
        if (endPage < pagination.pages - 1) buttons.push(`<span class="pagination-info">...</span>`);
        buttons.push(`<button class="pagination-btn" onclick="changePage(${pagination.pages})">${pagination.pages}</button>`);
    }

    // Next button
    buttons.push(`
        <button class="pagination-btn" ${currentPage === pagination.pages ? 'disabled' : ''} 
            onclick="changePage(${currentPage + 1})">Next</button>
    `);

    container.innerHTML = buttons.join('');
}

// Change page
function changePage(page) {
    currentPage = page;
    loadTrips();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// View trip details
async function viewTripDetails(tripId) {
    const modal = document.getElementById('tripDetailsModal');
    const content = document.getElementById('tripDetailsContent');
    
    modal.classList.add('active');
    content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

    try {
        const response = await fetch(`api/trips/${tripId}`);
        const data = await response.json();

        if (data.success) {
            const trip = data.trip;
            document.getElementById('tripModalTitle').textContent = trip.title;
            
            content.innerHTML = `
                <div class="modal-section">
                    <h3 class="modal-section-title">Trip Information</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label">Destination</span>
                            <span class="info-value">${escapeHtml(trip.destination)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Status</span>
                            <span class="info-value">${trip.status.replace('_', ' ')}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Start Date</span>
                            <span class="info-value">${formatDate(trip.start_date)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">End Date</span>
                            <span class="info-value">${formatDate(trip.end_date)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Price per Student</span>
                            <span class="info-value">$${parseFloat(trip.price_per_student || 0).toFixed(2)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Participants</span>
                            <span class="info-value">${trip.participants.length}/${trip.max_participants}</span>
                        </div>
                    </div>
                </div>

                ${trip.description ? `
                <div class="modal-section">
                    <h3 class="modal-section-title">Description</h3>
                    <p style="color: #4a5568; line-height: 1.6;">${escapeHtml(trip.description)}</p>
                </div>
                ` : ''}

                <div class="modal-section">
                    <h3 class="modal-section-title">Financial Summary</h3>
                    <div class="financial-card">
                        <div class="financial-item">
                            <span class="financial-label">Total Revenue</span>
                            <span class="financial-value">$${parseFloat(trip.financial.total_revenue).toFixed(2)}</span>
                        </div>
                        <div class="financial-item">
                            <span class="financial-label">Total Paid</span>
                            <span class="financial-value" style="color: #48bb78;">$${parseFloat(trip.financial.total_paid).toFixed(2)}</span>
                        </div>
                        <div class="financial-item">
                            <span class="financial-label">Outstanding</span>
                            <span class="financial-value" style="color: #ed8936;">$${parseFloat(trip.financial.outstanding).toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                ${trip.bookings && trip.bookings.length > 0 ? `
                <div class="modal-section">
                    <h3 class="modal-section-title">Bookings</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Provider</th>
                                <th>Status</th>
                                <th>Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${trip.bookings.map(booking => `
                                <tr>
                                    <td>${escapeHtml(booking.service_type || 'N/A')}</td>
                                    <td>${escapeHtml(booking.provider_name || 'N/A')}</td>
                                    <td>${escapeHtml(booking.status || 'N/A')}</td>
                                    <td>$${parseFloat(booking.cost || 0).toFixed(2)}</td>
                                </tr>
                                `).join('')}
                        </tbody>
                    </table>
                </div>
                ` : ''}
            `;
        } else {
            showError(data.error);
            closeModal('tripDetailsModal');
        }
    } catch (error) {
        console.error('Error loading trip details:', error);
        showError('Failed to load trip details.');
        closeModal('tripDetailsModal');
    }
}

// View participants
async function viewParticipants(tripId, tripTitle) {
    const modal = document.getElementById('participantsModal');
    const content = document.getElementById('participantsContent');
    
    modal.classList.add('active');
    document.getElementById('participantsModalTitle').textContent = `Participants - ${tripTitle}`;
    content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

    try {
        const response = await fetch(`api/participants?trip_id=${tripId|| ''}`);
        const data = await response.json();

        if (data.success) {
            const participants = data.participants;
            
            if (participants.length === 0) {
                content.innerHTML = `
                    <div class="empty-state">
                        <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="9" cy="7" r="4"></circle>
                            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                        </svg>
                        <div class="empty-state-title">No participants yet</div>
                        <div class="empty-state-text">Students will appear here once they register for this trip</div>
                    </div>
                `;
                return;
            }

            content.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Student Name</th>
                            <th>Email</th>
                            <th>Consent Status</th>
                            <th>Payment Status</th>
                            <th>Amount Paid</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${participants.map(p => `
                            <tr>
                                <td>${escapeHtml(p.student_name)}</td>
                                <td>${escapeHtml(p.student_email)}</td>
                                <td>
                                    <span class="status-indicator ${p.consent_signed ? 'signed' : 'pending'}"></span>
                                    ${p.consent_signed ? 'Signed' : 'Pending'}
                                </td>
                                <td>
                                    <span class="status-indicator ${p.payment_status === 'paid' ? 'signed' : 'pending'}"></span>
                                    ${p.payment_status}
                                </td>
                                <td>$${parseFloat(p.amount_paid || 0).toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            showError(data.error);
            closeModal('participantsModal');
        }
    } catch (error) {
        console.error('Error loading participants:', error);
        showError('Failed to load participants.');
        closeModal('participantsModal');
    }
}

// Close modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.remove('active');
        }
    });
});

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    alert(message);
}