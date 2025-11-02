// Participants Management System
class ParticipantsManager {
    constructor() {
        this.currentTripId = null;
        this.currentPage = 1;
        this.perPage = 20;
        this.filters = {
            status: '',
            payment_status: '',
            search: ''
        };
        this.trips = [];
        this.participants = [];
        this.statistics = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTrips();
    }

    bindEvents() {
        // Trip search
        const tripSearch = document.getElementById('ptmTripSearch');
        if (tripSearch) {
            tripSearch.addEventListener('input', (e) => {
                this.filterTrips(e.target.value);
            });
        }

        // Mobile toggle
        const mobileToggle = document.getElementById('ptmMobileToggle');
        const sidebar = document.getElementById('ptmTripSidebar');
        if (mobileToggle && sidebar) {
            mobileToggle.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
            });
        }

        // Modal close
        const modalClose = document.getElementById('ptmModalClose');
        const modal = document.getElementById('ptmDetailModal');
        if (modalClose && modal) {
            modalClose.addEventListener('click', () => {
                modal.classList.remove('active');
            });

            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        }
    }

    async loadTrips() {
        const tripsList = document.getElementById('ptmTripsList');
        
        try {
            // Replace with your actual API endpoint
            const response = await fetch('/api/participants/teacher/trips?include_stats=true');
            
            if (!response.ok) {
                throw new Error('Failed to load trips');
            }

            const data = await response.json();
            
            if (data.success && data.data.trips) {
                this.trips = data.data.trips || [];
                this.renderTrips();
            } else {
                throw new Error(data.message || 'Failed to load trips');
            }
        } catch (error) {
            console.error('Error loading trips:', error);
            tripsList.innerHTML = `
                <div class="ptm-empty-state">
                    <div class="ptm-empty-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <h3 class="ptm-empty-title">Error Loading Trips</h3>
                    <p class="ptm-empty-text">${error.message}</p>
                    <button class="ptm-btn ptm-btn-primary" onclick="participantsManager.loadTrips()" style="margin-top: 16px;">
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    renderTrips() {
        const tripsList = document.getElementById('ptmTripsList');
        
        if (!this.trips || this.trips.length === 0) {
            tripsList.innerHTML = `
                <div class="ptm-empty-state">
                    <div class="ptm-empty-icon">📋</div>
                    <h3 class="ptm-empty-title">No Trips Found</h3>
                    <p class="ptm-empty-text">You haven't created any trips yet</p>
                </div>
            `;
            return;
        }

        const tripsHTML = this.trips.map(trip => {
            const startDate = trip.start_date ? new Date(trip.start_date).toLocaleDateString() : 'TBD';
            const endDate = trip.end_date ? new Date(trip.end_date).toLocaleDateString() : 'TBD';
            const participantCount = trip.participant_count || 0;
            const confirmedCount = trip.confirmed_count || 0;
            const paidCount = trip.paid_count || 0;
            const isActive = this.currentTripId === trip.id;

            return `
                <div class="ptm-trip-card ${isActive ? 'active' : ''}" data-trip-id="${trip.id}">
                    <div class="ptm-trip-title">${this.escapeHtml(trip.title)}</div>
                    <div class="ptm-trip-date">
                        <i class="fa-solid fa-calendar"></i> ${startDate} - ${endDate}
                    </div>
                    <div class="ptm-trip-stats">
                        <span class="ptm-stat-badge"><i class="fa-solid fa-users"></i> ${participantCount}</span>
                        <span class="ptm-stat-badge confirmed">✓ ${confirmedCount}</span>
                        <span class="ptm-stat-badge paid"><i class="fa-solid fa-sack-dollar"></i> ${paidCount}</span>
                    </div>
                </div>
            `;
        }).join('');

        tripsList.innerHTML = tripsHTML;

        // Add click handlers
        document.querySelectorAll('.ptm-trip-card').forEach(card => {
            card.addEventListener('click', () => {
                const tripId = parseInt(card.dataset.tripId);
                this.selectTrip(tripId);
            });
        });
    }

    filterTrips(searchTerm) {
        const cards = document.querySelectorAll('.ptm-trip-card');
        const term = searchTerm.toLowerCase();

        cards.forEach(card => {
            const title = card.querySelector('.ptm-trip-title').textContent.toLowerCase();
            if (title.includes(term)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    async selectTrip(tripId) {
        this.currentTripId = tripId;
        this.currentPage = 1;
        this.filters = { status: '', payment_status: '', search: '' };

        // Update active state
        document.querySelectorAll('.ptm-trip-card').forEach(card => {
            card.classList.toggle('active', parseInt(card.dataset.tripId) === tripId);
        });

        // Close mobile sidebar
        const sidebar = document.getElementById('ptmTripSidebar');
        if (sidebar) {
            sidebar.classList.remove('mobile-open');
        }

        await this.loadParticipants();
    }

    async loadParticipants() {
        const mainContent = document.getElementById('ptmMainContent');
        
        mainContent.innerHTML = `
            <div class="ptm-loading" style="padding: 120px 20px;">
                <div class="ptm-spinner"></div>
                <p style="margin-top: 16px;">Loading participants...</p>
            </div>
        `;

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.filters
            });

            const response = await fetch(`/api/participants/trip/${this.currentTripId}?${params}`);
            
            if (!response.ok) {
                throw new Error('Failed to load participants');
            }

            const data = await response.json();
            
            if (data.success && data.data) {
                this.participants = data.data.participants || [];
                this.statistics = data.data.statistics || {};
                this.pagination = data.data.pagination || {};
                this.tripInfo = data.data.trip || {};
                this.renderParticipantsView();
            } else {
                throw new Error(data.message || 'Failed to load participants');
            }
        } catch (error) {
            console.error('Error loading participants:', error);
            this.showError('Failed to load participants', error.message);
        }
    }

    renderParticipantsView() {
        const mainContent = document.getElementById('ptmMainContent');
        const trip = this.tripInfo;

        mainContent.innerHTML = `
            <!-- Header -->
            <div class="ptm-content-header">
                <div class="ptm-header-top">
                    <div class="ptm-header-title">
                        <h1>${this.escapeHtml(trip.title || 'Trip Participants')}</h1>
                        <div class="ptm-header-subtitle">
                            ${trip.start_date ? new Date(trip.start_date).toLocaleDateString() : ''} - 
                            ${trip.end_date ? new Date(trip.end_date).toLocaleDateString() : ''}
                        </div>
                    </div>
                    <div class="ptm-header-actions">
                        <button class="ptm-btn ptm-btn-secondary" onclick="participantsManager.exportParticipants()">
                            <i class="fa-solid fa-download"></i> Export
                        </button>
                        <button class="ptm-btn ptm-btn-primary" onclick="participantsManager.refreshData()">
                            <i class="fa-solid fa-rotate-right"></i> Refresh
                        </button>
                    </div>
                </div>

                <!-- Filters -->
                <div class="ptm-filters">
                    <div class="ptm-search-box">
                        <input type="text" id="ptmParticipantSearch" placeholder="Search by name or email..." value="${this.filters.search}">
                        <span class="ptm-search-icon"><i class="fa-solid fa-magnifying-glass"></i></span>
                    </div>
                    <select class="ptm-filter-select" id="ptmStatusFilter">
                        <option value="">All Status</option>
                        <option value="registered" ${this.filters.status === 'registered' ? 'selected' : ''}>Registered</option>
                        <option value="confirmed" ${this.filters.status === 'confirmed' ? 'selected' : ''}>Confirmed</option>
                        <option value="cancelled" ${this.filters.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                        <option value="completed" ${this.filters.status === 'completed' ? 'selected' : ''}>Completed</option>
                    </select>
                    <select class="ptm-filter-select" id="ptmPaymentFilter">
                        <option value="">All Payments</option>
                        <option value="pending" ${this.filters.payment_status === 'pending' ? 'selected' : ''}>Pending</option>
                        <option value="partial" ${this.filters.payment_status === 'partial' ? 'selected' : ''}>Partial</option>
                        <option value="paid" ${this.filters.payment_status === 'paid' ? 'selected' : ''}>Paid</option>
                        <option value="refunded" ${this.filters.payment_status === 'refunded' ? 'selected' : ''}>Refunded</option>
                    </select>
                </div>
            </div>

            <!-- Statistics -->
            <div class="ptm-stats-grid">
                <div class="ptm-stat-card">
                    <div class="ptm-stat-icon total"><i class="fa-solid fa-users"></i></div>
                    <div class="ptm-stat-label">Total Participants</div>
                    <div class="ptm-stat-value">${this.statistics.total_participants || 0}</div>
                </div>
                <div class="ptm-stat-card">
                    <div class="ptm-stat-icon confirmed">✓</div>
                    <div class="ptm-stat-label">Confirmed</div>
                    <div class="ptm-stat-value">${this.statistics.confirmed_participants || 0}</div>
                </div>
                <div class="ptm-stat-card">
                    <div class="ptm-stat-icon paid"><i class="fa-solid fa-sack-dollar"></i></div>
                    <div class="ptm-stat-label">Fully Paid</div>
                    <div class="ptm-stat-value">${this.statistics.fully_paid || 0}</div>
                </div>
                <div class="ptm-stat-card">
                    <div class="ptm-stat-icon capacity"><i class="fa-solid fa-chart-simple"></i></div>
                    <div class="ptm-stat-label">Capacity</div>
                    <div class="ptm-stat-value">${this.statistics.trip_capacity || 'N/A'}</div>
                </div>
            </div>

            <!-- Table -->
            <div class="ptm-table-container">
                ${this.renderParticipantsTable()}
            </div>
        `;

        this.bindFilterEvents();
    }

    renderParticipantsTable() {
        if (!this.participants || this.participants.length === 0) {
            return `
                <div class="ptm-empty-state">
                    <div class="ptm-empty-icon"><i class="fa-solid fa-user"></i></div>
                    <h3 class="ptm-empty-title">No Participants Found</h3>
                    <p class="ptm-empty-text">No participants match your current filters</p>
                </div>
            `;
        }

        const tableHTML = `
            <div class="ptm-table-wrapper">
                <table class="ptm-table">
                    <thead>
                        <tr>
                            <th>Participant</th>
                            <th>Age/Grade</th>
                            <th>Status</th>
                            <th>Payment</th>
                            <th>Amount Paid</th>
                            <th>Balance</th>
                            <th>Consents</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.participants.map(p => this.renderParticipantRow(p)).join('')}
                    </tbody>
                </table>
            </div>
            ${this.renderPagination()}
        `;

        return tableHTML;
    }

    renderParticipantRow(participant) {
        const initials = this.getInitials(participant.full_name);
        const age = participant.age || 'N/A';
        const grade = participant.grade_level || 'N/A';
        const amountPaid = parseFloat(participant.amount_paid || 0).toFixed(2);
        const balance = parseFloat(participant.outstanding_balance || 0).toFixed(2);

        return `
            <tr data-participant-id="${participant.id}">
                <td>
                    <div class="ptm-participant-name">
                        <div class="ptm-avatar">${initials}</div>
                        <div class="ptm-name-details">
                            <div class="ptm-name">${this.escapeHtml(participant.full_name)}</div>
                            <div class="ptm-email">${this.escapeHtml(participant.email || 'No email')}</div>
                        </div>
                    </div>
                </td>
                <td>${age} / ${grade}</td>
                <td>
                    <span class="ptm-status-badge ${participant.status}">
                        ${this.capitalizeFirst(participant.status)}
                    </span>
                </td>
                <td>
                    <span class="ptm-payment-badge ${participant.payment_status}">
                        ${this.capitalizeFirst(participant.payment_status)}
                    </span>
                </td>
                <td>${amountPaid}</td>
                <td>${balance}</td>
                <td>
                    <div class="ptm-consent-indicator">
                        <div class="ptm-consent-icon ${participant.has_all_consents ? 'complete' : 'incomplete'}">
                            ${participant.has_all_consents ? '✓' : '✗'}
                        </div>
                        ${participant.has_all_consents ? 'Complete' : 'Incomplete'}
                    </div>
                </td>
                <td>
                    <div class="ptm-action-buttons">
                        <button class="ptm-action-btn view" onclick="participantsManager.viewParticipant(${participant.id})">
                            <i class="fa-solid fa-eye"></i> View
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    renderPagination() {
        if (!this.pagination || this.pagination.pages <= 1) {
            return '';
        }

        const currentPage = this.pagination.page;
        const totalPages = this.pagination.pages;
        let pages = [];

        // Always show first page
        pages.push(1);

        // Show pages around current page
        for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
            pages.push(i);
        }

        // Always show last page
        if (totalPages > 1) {
            pages.push(totalPages);
        }

        // Remove duplicates and sort
        pages = [...new Set(pages)].sort((a, b) => a - b);

        const pagesHTML = pages.map((page, index) => {
            // Add ellipsis if there's a gap
            const prevPage = index > 0 ? pages[index - 1] : 0;
            const gap = page - prevPage > 1 ? '<span style="padding: 8px;">...</span>' : '';

            return `
                ${gap}
                <button class="ptm-page-btn ${page === currentPage ? 'active' : ''}" 
                        onclick="participantsManager.goToPage(${page})">
                    ${page}
                </button>
            `;
        }).join('');

        return `
            <div class="ptm-pagination">
                <button class="ptm-page-btn" 
                        onclick="participantsManager.goToPage(${currentPage - 1})"
                        ${!this.pagination.has_prev ? 'disabled' : ''}>
                    ← Previous
                </button>
                ${pagesHTML}
                <button class="ptm-page-btn" 
                        onclick="participantsManager.goToPage(${currentPage + 1})"
                        ${!this.pagination.has_next ? 'disabled' : ''}>
                    Next →
                </button>
            </div>
        `;
    }

    bindFilterEvents() {
        // Search
        const searchInput = document.getElementById('ptmParticipantSearch');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.filters.search = e.target.value;
                    this.currentPage = 1;
                    this.loadParticipants();
                }, 500);
            });
        }

        // Status filter
        const statusFilter = document.getElementById('ptmStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.currentPage = 1;
                this.loadParticipants();
            });
        }

        // Payment filter
        const paymentFilter = document.getElementById('ptmPaymentFilter');
        if (paymentFilter) {
            paymentFilter.addEventListener('change', (e) => {
                this.filters.payment_status = e.target.value;
                this.currentPage = 1;
                this.loadParticipants();
            });
        }
    }

    async viewParticipant(participantId) {
        const modal = document.getElementById('ptmDetailModal');
        const modalBody = document.getElementById('ptmModalBody');
        const modalTitle = document.getElementById('ptmModalTitle');

        modal.classList.add('active');
        modalTitle.textContent = 'Loading...';
        modalBody.innerHTML = `
            <div class="ptm-loading">
                <div class="ptm-spinner"></div>
                <p style="margin-top: 16px;">Loading participant details...</p>
            </div>
        `;

        try {
            const response = await fetch(`/api/participant/${participantId}`);
            
            if (!response.ok) {
                throw new Error('Failed to load participant details');
            }

            const data = await response.json();
            
            if (data.success && data.data) {
                this.renderParticipantDetails(data.data);
            } else {
                throw new Error(data.message || 'Failed to load participant details');
            }
        } catch (error) {
            console.error('Error loading participant details:', error);
            modalBody.innerHTML = `
                <div class="ptm-empty-state">
                    <div class="ptm-empty-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <h3 class="ptm-empty-title">Error Loading Details</h3>
                    <p class="ptm-empty-text">${error.message}</p>
                </div>
            `;
        }
    }

    renderParticipantDetails(participant) {
        const modalTitle = document.getElementById('ptmModalTitle');
        const modalBody = document.getElementById('ptmModalBody');

        modalTitle.textContent = participant.full_name;

        modalBody.innerHTML = `
            <!-- Basic Information -->
            <div class="ptm-detail-section">
                <h3 class="ptm-section-title">Basic Information</h3>
                <div class="ptm-detail-grid">
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Full Name</div>
                        <div class="ptm-detail-value">${this.escapeHtml(participant.full_name)}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Date of Birth</div>
                        <div class="ptm-detail-value">${participant.date_of_birth || 'Not provided'}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Age</div>
                        <div class="ptm-detail-value">${participant.age || 'N/A'}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Grade Level</div>
                        <div class="ptm-detail-value">${participant.grade_level || 'Not provided'}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Student ID</div>
                        <div class="ptm-detail-value">${participant.student_id || 'Not provided'}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Status</div>
                        <div class="ptm-detail-value">
                            <span class="ptm-status-badge ${participant.status}">
                                ${this.capitalizeFirst(participant.status)}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Contact Information -->
            <div class="ptm-detail-section">
                <h3 class="ptm-section-title">Contact Information</h3>
                <div class="ptm-detail-grid">
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Email</div>
                        <div class="ptm-detail-value">${this.escapeHtml(participant.contact?.email || 'Not provided')}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Phone</div>
                        <div class="ptm-detail-value">${participant.contact?.phone || 'Not provided'}</div>
                    </div>
                </div>
            </div>

            <!-- Emergency Contacts -->
            <div class="ptm-detail-section">
                <h3 class="ptm-section-title">Emergency Contacts</h3>
                ${this.renderEmergencyContacts(participant.emergency_contacts)}
            </div>

            <!-- Medical Information -->
            <div class="ptm-detail-section">
                <h3 class="ptm-section-title">Medical Information</h3>
                <div class="ptm-detail-grid">
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Medical Conditions</div>
                        <div class="ptm-detail-value">${participant.medical?.conditions || 'None reported'}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Medications</div>
                        <div class="ptm-detail-value">${participant.medical?.medications || 'None reported'}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Allergies</div>
                        <div class="ptm-detail-value">${participant.medical?.allergies || 'None reported'}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Dietary Restrictions</div>
                        <div class="ptm-detail-value">${participant.medical?.dietary_restrictions || 'None reported'}</div>
                    </div>
                </div>
            </div>

            <!-- Payment Information -->
            <div class="ptm-detail-section">
                <h3 class="ptm-section-title">Payment Information</h3>
                <div class="ptm-detail-grid">
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Payment Status</div>
                        <div class="ptm-detail-value">
                            <span class="ptm-payment-badge ${participant.payment?.status}">
                                ${this.capitalizeFirst(participant.payment?.status || 'pending')}
                            </span>
                        </div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Amount Paid</div>
                        <div class="ptm-detail-value">${parseFloat(participant.payment?.amount_paid || 0).toFixed(2)}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Outstanding Balance</div>
                        <div class="ptm-detail-value">${parseFloat(participant.payment?.outstanding_balance || 0).toFixed(2)}</div>
                    </div>
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">Total Paid</div>
                        <div class="ptm-detail-value">${parseFloat(participant.payment?.total_paid || 0).toFixed(2)}</div>
                    </div>
                </div>
                ${this.renderPaymentHistory(participant.payment?.payment_history)}
            </div>

            <!-- Consent Forms -->
            <div class="ptm-detail-section">
                <h3 class="ptm-section-title">Consent Forms</h3>
                ${this.renderConsentForms(participant.consents)}
            </div>

            <!-- Special Requirements -->
            ${participant.special_requirements ? `
                <div class="ptm-detail-section">
                    <h3 class="ptm-section-title">Special Requirements</h3>
                    <div class="ptm-detail-value">${this.escapeHtml(participant.special_requirements)}</div>
                </div>
            ` : ''}

            <!-- Actions -->
            <div class="ptm-detail-section">
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button class="ptm-btn ptm-btn-secondary" onclick="participantsManager.closeModal()">
                        Close
                    </button>
                    <button class="ptm-btn ptm-btn-primary" onclick="participantsManager.deleteParticipantConfirm(${participant.id})">
                        <i class="fa-solid fa-trash"></i> Delete Participant
                    </button>
                </div>
            </div>
        `;
    }

    renderEmergencyContacts(contacts) {
        if (!contacts || contacts.length === 0 || !contacts[0]) {
            return '<p style="color: #6b7280;">No emergency contacts provided</p>';
        }

        return `
            <div class="ptm-detail-grid">
                ${contacts.filter(c => c).map((contact, index) => `
                    <div class="ptm-detail-item" style="grid-column: span 2;">
                        <div class="ptm-detail-label">Contact ${index + 1}</div>
                        <div class="ptm-detail-value">
                            <strong>${this.escapeHtml(contact.name)}</strong><br>
                            ${contact.phone}<br>
                            <em>${contact.relationship}</em>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderPaymentHistory(history) {
        if (!history || history.length === 0) {
            return '<p style="color: #6b7280; margin-top: 12px;">No payment history</p>';
        }

        return `
            <div class="ptm-payment-history" style="margin-top: 16px;">
                <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Payment History</h4>
                ${history.map(payment => `
                    <div class="ptm-payment-item">
                        <div>
                            <div style="font-weight: 600;">${parseFloat(payment.amount).toFixed(2)}</div>
                            <div style="font-size: 12px; color: #6b7280;">${new Date(payment.date).toLocaleDateString()}</div>
                        </div>
                        <span class="ptm-payment-badge ${payment.status}">
                            ${this.capitalizeFirst(payment.status)}
                        </span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderConsentForms(consents) {
        if (!consents || !consents.forms || consents.forms.length === 0) {
            return '<p style="color: #6b7280;">No consent forms</p>';
        }

        return `
            <div class="ptm-detail-grid">
                ${consents.forms.map(consent => `
                    <div class="ptm-detail-item">
                        <div class="ptm-detail-label">${this.escapeHtml(consent.title || 'Consent Form')}</div>
                        <div class="ptm-detail-value">
                            <div class="ptm-consent-indicator">
                                <div class="ptm-consent-icon ${consent.is_signed ? 'complete' : 'incomplete'}">
                                    ${consent.is_signed ? '✓' : '✗'}
                                </div>
                                ${consent.is_signed ? 'Signed' : 'Not Signed'}
                            </div>
                            ${consent.is_signed && consent.signed_date ? `
                                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                                    Signed on ${new Date(consent.signed_date).toLocaleDateString()}
                                    ${consent.signer_name ? `by ${this.escapeHtml(consent.signer_name)}` : ''}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async deleteParticipantConfirm(participantId) {
        if (!confirm('Are you sure you want to delete this participant? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/participant/${participantId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Participant deleted successfully', 'success');
                this.closeModal();
                await this.loadParticipants();
            } else {
                // Check if force delete is required
                if (data.data && data.data.requires_force) {
                    if (confirm('This participant is confirmed. Are you sure you want to force delete?')) {
                        await this.forceDeleteParticipant(participantId);
                    }
                } else {
                    throw new Error(data.message || 'Failed to delete participant');
                }
            }
        } catch (error) {
            console.error('Error deleting participant:', error);
            this.showToast('Failed to delete participant', 'error');
        }
    }

    async forceDeleteParticipant(participantId) {
        try {
            const response = await fetch(`/api/participant/${participantId}?force=true`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Participant deleted successfully', 'success');
                this.closeModal();
                await this.loadParticipants();
            } else {
                throw new Error(data.message || 'Failed to delete participant');
            }
        } catch (error) {
            console.error('Error force deleting participant:', error);
            this.showToast('Failed to delete participant', 'error');
        }
    }

    closeModal() {
        const modal = document.getElementById('ptmDetailModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    goToPage(page) {
        if (page < 1 || page > this.pagination.pages) {
            return;
        }
        this.currentPage = page;
        this.loadParticipants();
    }

    async refreshData() {
        this.showToast('Refreshing data...', 'info');
        await this.loadParticipants();
        this.showToast('Data refreshed successfully', 'success');
    }

    async exportParticipants() {
        try {
            this.showToast('Preparing export...', 'info');

            const params = new URLSearchParams({
                ...this.filters,
                export: 'csv'
            });

            // Create download link
            const url = `/api/participants/trip/${this.currentTripId}/export?${params}`;
            const link = document.createElement('a');
            link.href = url;
            link.download = `participants_trip_${this.currentTripId}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.showToast('Export started', 'success');
        } catch (error) {
            console.error('Error exporting participants:', error);
            this.showToast('Failed to export participants', 'error');
        }
    }

    showError(title, message) {
        const mainContent = document.getElementById('ptmMainContent');
        mainContent.innerHTML = `
            <div class="ptm-empty-state" style="padding: 120px 20px;">
                <div class="ptm-empty-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                <h3 class="ptm-empty-title">${this.escapeHtml(title)}</h3>
                <p class="ptm-empty-text">${this.escapeHtml(message)}</p>
                <button class="ptm-btn ptm-btn-primary" onclick="participantsManager.loadParticipants()" style="margin-top: 16px;">
                    Try Again
                </button>
            </div>
        `;
    }

    showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.ptm-toast').forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `ptm-toast ${type}`;
        
        const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
        toast.innerHTML = `
            <span style="font-size: 20px;">${icon}</span>
            <span>${this.escapeHtml(message)}</span>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'ptmSlideIn 0.3s reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Utility functions
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getInitials(name) {
        if (!name) return '?';
        return name
            .split(' ')
            .map(part => part[0])
            .join('')
            .toUpperCase()
            .substring(0, 2);
    }

    capitalizeFirst(text) {
        if (!text) return '';
        return text.charAt(0).toUpperCase() + text.slice(1);
    }
}

// Initialize the manager when DOM is ready
let participantsManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        participantsManager = new ParticipantsManager();
    });
} else {
    participantsManager = new ParticipantsManager();
}