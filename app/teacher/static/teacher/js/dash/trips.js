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
                <button class="teach-trip-btn teach-trip-btn-primary" onclick="viewRegistrations(${trip.id}, '${escapeHtml(trip.title)}')">Registrations</button>
                <button class="trip-demo-btn" onclick="tripOpenEditModal(${trip.id})">Edit Trip</button>
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

            const spotsTaken = trip.max_participants - trip.available_spots; 
            
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
                            <span class="info-value">Kshs. ${parseFloat(trip.price_per_student || 0).toFixed(2)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Registrations</span>
                            <span class="info-value">${trip.registrations.length || 0}/${trip.max_participants}</span>
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
                            <span class="financial-value">Kshs. ${parseFloat(trip.financial.total_revenue).toFixed(2)}</span>
                        </div>
                        <div class="financial-item">
                            <span class="financial-label">Total Paid</span>
                            <span class="financial-value" style="color: #48bb78;">Kshs. ${parseFloat(trip.financial.total_paid).toFixed(2)}</span>
                        </div>
                        <div class="financial-item">
                            <span class="financial-label">Outstanding</span>
                            <span class="financial-value" style="color: #ed8936;">Kshs. ${parseFloat(trip.financial.outstanding).toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                ${trip.registrations && trip.registrations.length > 0 ? `
                <div class="modal-section">
                    <h3 class="modal-section-title">Recent Registrations (${trip.registrations.length})</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Registration #</th>
                                <th>Student</th>
                                <th>Status</th>
                                <th>Payment</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${trip.registrations.slice(0, 5).map(reg => `
                                <tr>
                                    <td>${escapeHtml(reg.registration_number || 'N/A')}</td>
                                    <td>${escapeHtml(reg.participant?.full_name || 'N/A')}</td>
                                    <td>
                                        <span class="status-badge status-${reg.status}">${reg.status}</span>
                                    </td>
                                    <td>
                                        <span class="status-badge status-${reg.payment_status}">${reg.payment_status}</span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    ${trip.registrations.length > 5 ? `
                        <div style="text-align: center; margin-top: 1rem;">
                            <button class="teach-trip-btn teach-trip-btn-secondary" 
                                onclick="closeModal('tripDetailsModal'); viewRegistrations(${trip.id}, '${escapeHtml(trip.title)}')">
                                View All Registrations
                            </button>
                        </div>
                    ` : ''}
                </div>
                ` : ''}

                ${trip.bookings && trip.bookings.length > 0 ? `
                <div class="modal-section">
                    <h3 class="modal-section-title">Service Bookings</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Service Type</th>
                                <th>Vendor</th>
                                <th>Status</th>
                                <th>Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${trip.bookings.map(booking => `
                                <tr>
                                    <td>${escapeHtml(booking.booking_type || 'N/A')}</td>
                                    <td>${escapeHtml(booking.vendor?.business_name || 'N/A')}</td>
                                    <td>
                                        <span class="status-badge status-${booking.status}">${booking.status}</span>
                                    </td>
                                    <td>Kshs. ${parseFloat(booking.total_amount || 0).toFixed(2)}</td>
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

// View registrations (renamed from viewParticipants)
async function viewRegistrations(tripId, tripTitle) {
    const modal = document.getElementById('participantsModal');
    const content = document.getElementById('participantsContent');
    
    modal.classList.add('active');
    document.getElementById('participantsModalTitle').textContent = `Registrations - ${tripTitle}`;
    content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

    try {
        const response = await fetch(`api/registrations?trip_id=${tripId || ''}`);
        const data = await response.json();

        if (data.success) {
            const registrations = data.registrations;
            
            if (registrations.length === 0) {
                content.innerHTML = `
                    <div class="empty-state">
                        <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="9" cy="7" r="4"></circle>
                            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                        </svg>
                        <div class="empty-state-title">No registrations yet</div>
                        <div class="empty-state-text">Students will appear here once they register for this trip</div>
                    </div>
                `;
                return;
            }

            content.innerHTML = `
                <div style="margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <div style="color: #4a5568;">
                        <strong>${registrations.length}</strong> total registration${registrations.length !== 1 ? 's' : ''}
                    </div>
                    <button class="teach-trip-btn teach-trip-btn-secondary" onclick="exportRegistrations(${tripId})">
                        <svg style="width: 16px; height: 16px; margin-right: 4px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        Export CSV
                    </button>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Registration #</th>
                            <th>Student Name</th>
                            <th>Parent Email</th>
                            <th>Status</th>
                            <th>Consent</th>
                            <th>Medical Form</th>
                            <th>Payment</th>
                            <th>Amount Paid</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${registrations.map(reg => `
                            <tr>
                                <td>${escapeHtml(reg.registration_number || 'N/A')}</td>
                                <td>${escapeHtml(reg.participant?.full_name || 'N/A')}</td>
                                <td>${escapeHtml(reg.parent?.email || 'N/A')}</td>
                                <td>
                                    <span class="status-badge status-${reg.status}">${reg.status}</span>
                                </td>
                                <td>
                                    <span class="status-indicator ${reg.consent_signed ? 'signed' : 'pending'}"></span>
                                    ${reg.consent_signed ? 'Signed' : 'Pending'}
                                </td>
                                <td>
                                    <span class="status-indicator ${reg.medical_form_submitted ? 'signed' : 'pending'}"></span>
                                    ${reg.medical_form_submitted ? 'Submitted' : 'Pending'}
                                </td>
                                <td>
                                    <span class="status-badge status-${reg.payment_status}">${reg.payment_status}</span>
                                </td>
                                <td>Kshs. ${parseFloat(reg.amount_paid || 0).toFixed(2)}</td>
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
        console.error('Error loading registrations:', error);
        showError('Failed to load registrations.');
        closeModal('participantsModal');
    }
}

// Export registrations to CSV
async function exportRegistrations(tripId) {
    try {
        const response = await fetch(`api/participants/trip/${tripId}/export?format=csv`);
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `registrations_trip_${tripId}.csv`;
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showSuccess('Registrations exported successfully!');
    } catch (error) {
        console.error('Error exporting registrations:', error);
        showError('Failed to export registrations.');
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
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    // You can replace this with a better notification system
    alert(message);
}

function showSuccess(message) {
    // You can replace this with a better notification system
    alert(message);
}