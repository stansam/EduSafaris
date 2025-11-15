// ============================================================================
// EDUSAFARI VIEW TRIP MODAL - JAVASCRIPT
// ============================================================================

(function() {
    'use strict';

    const ViewTripModal = {
        currentTripId: null,
        currentTrip: null,

        init() {
            this.attachEventListeners();
        },

        attachEventListeners() {
            // Close buttons
            document.getElementById('edusafariViewTripCloseBtn')?.addEventListener('click', () => this.close());
            document.getElementById('edusafariViewTripCloseFooterBtn')?.addEventListener('click', () => this.close());
            
            // Overlay click to close
            document.querySelector('#edusafariViewTripModal .edusafari-modal-overlay')?.addEventListener('click', () => this.close());

            // Tab buttons
            document.querySelectorAll('#edusafariViewTripModal .edusafari-tab-btn').forEach(btn => {
                btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
            });

            // Action buttons
            document.getElementById('edusafariViewTripEditBtn')?.addEventListener('click', () => {
                this.close();
                if (typeof window.EdusafariEditTripModal !== 'undefined') {
                    window.EdusafariEditTripModal.open(this.currentTripId);
                }
            });

            document.getElementById('edusafariViewTripReportBtn')?.addEventListener('click', () => {
                if (typeof window.EdusafariReportModal !== 'undefined') {
                    window.EdusafariReportModal.open(this.currentTripId);
                }
            });

            // ESC key to close
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen()) {
                    this.close();
                }
            });
        },

        async open(tripId) {
            this.currentTripId = tripId;
            const modal = document.getElementById('edusafariViewTripModal');
            if (!modal) return;

            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';

            // Show loading state
            document.getElementById('edusafariViewTripLoading').style.display = 'block';
            document.getElementById('edusafariViewTripContent').style.display = 'none';

            // Reset to first tab
            this.switchTab('overview');

            // Load trip data
            await this.loadTripData(tripId);
        },

        close() {
            const modal = document.getElementById('edusafariViewTripModal');
            if (!modal) return;

            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            this.currentTripId = null;
            this.currentTrip = null;
        },

        isOpen() {
            const modal = document.getElementById('edusafariViewTripModal');
            return modal && modal.style.display === 'block';
        },

        switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('#edusafariViewTripModal .edusafari-tab-btn').forEach(btn => {
                if (btn.dataset.tab === tabName) {
                    btn.classList.add('edusafari-tab-active');
                } else {
                    btn.classList.remove('edusafari-tab-active');
                }
            });

            // Update tab panes
            document.querySelectorAll('#edusafariViewTripModal .edusafari-tab-pane').forEach(pane => {
                if (pane.dataset.pane === tabName) {
                    pane.classList.add('edusafari-tab-active');
                } else {
                    pane.classList.remove('edusafari-tab-active');
                }
            });
        },

        async loadTripData(tripId) {
            try {
                const response = await fetch(`/api/admin/trips/${tripId}`, {
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
                    this.currentTrip = data.data;
                    this.renderTripData(data.data);
                    
                    // Show content
                    document.getElementById('edusafariViewTripLoading').style.display = 'none';
                    document.getElementById('edusafariViewTripContent').style.display = 'block';
                } else {
                    throw new Error(data.error || 'Failed to load trip details');
                }
            } catch (error) {
                console.error('Error loading trip details:', error);
                if (window.EdusafariTrips) {
                    window.EdusafariTrips.showToast('error', 'Error', 'Failed to load trip details');
                }
                this.close();
            }
        },

        renderTripData(data) {
            const trip = data.trip;

            // Header section
            const coverImg = document.getElementById('edusafariViewTripCover');
            if (coverImg) {
                coverImg.src = trip.cover_image_url || 'https://placehold.co/800x400?text=No+Image&font=roboto';
            }

            document.getElementById('edusafariViewTripTitle').textContent = trip.title || 'N/A';

            // Badges
            const badgesContainer = document.getElementById('edusafariViewTripBadges');
            badgesContainer.innerHTML = '';
            
            const statusBadge = document.createElement('span');
            statusBadge.className = `edusafari-status-badge edusafari-status-${trip.status}`;
            statusBadge.textContent = this.formatStatus(trip.status);
            badgesContainer.appendChild(statusBadge);

            if (trip.featured) {
                const featuredBadge = document.createElement('span');
                featuredBadge.className = 'edusafari-featured-badge';
                featuredBadge.innerHTML = '<i class="fas fa-star"></i> Featured';
                badgesContainer.appendChild(featuredBadge);
            }

            // Quick info cards
            document.getElementById('edusafariViewTripDestination').textContent = 
                `${trip.destination}${trip.destination_country ? ', ' + trip.destination_country : ''}`;
            
            const startDate = trip.start_date ? new Date(trip.start_date).toLocaleDateString() : 'N/A';
            const endDate = trip.end_date ? new Date(trip.end_date).toLocaleDateString() : 'N/A';
            document.getElementById('edusafariViewTripDuration').textContent = 
                `${startDate} - ${endDate} (${trip.duration_days} days)`;
            
            document.getElementById('edusafariViewTripParticipants').textContent = 
                `${trip.current_participants} / ${trip.max_participants}`;
            
            document.getElementById('edusafariViewTripPrice').textContent = 
                `KES ${parseFloat(trip.price_per_student).toLocaleString()}`;

            // Overview tab
            this.renderOverview(trip);

            // Registrations tab
            this.renderRegistrations(data);

            // Financials tab
            this.renderFinancials(data);

            // Services tab
            this.renderServices(data);

            // Activity tab
            this.renderActivity(data);
        },

        renderOverview(trip) {
            // Description
            document.getElementById('edusafariViewTripDescription').textContent = 
                trip.description || 'No description available.';

            // Itinerary
            const itineraryContainer = document.getElementById('edusafariViewTripItinerary');
            if (trip.itinerary && Array.isArray(trip.itinerary) && trip.itinerary.length > 0) {
                itineraryContainer.innerHTML = trip.itinerary.map((item, index) => `
                    <div class="edusafari-itinerary-item" style="margin-bottom: 15px; padding-left: 25px; position: relative;">
                        <strong style="position: absolute; left: 0;">Day ${index + 1}:</strong>
                        <span>${this.escapeHtml(item.title || item)}</span>
                        ${item.description ? `<p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 14px;">${this.escapeHtml(item.description)}</p>` : ''}
                    </div>
                `).join('');
            } else {
                itineraryContainer.innerHTML = '<p style="color: #7f8c8d;">No itinerary available.</p>';
            }

            // Educational info
            const educationalContainer = document.getElementById('edusafariViewTripEducational');
            educationalContainer.innerHTML = `
                <ul class="edusafari-detail-list">
                    <li><strong>Grade Level:</strong> <span>${trip.grade_level || 'Not specified'}</span></li>
                    <li><strong>Age Range:</strong> <span>${trip.min_age || 'N/A'} - ${trip.max_age || 'N/A'} years</span></li>
                    <li><strong>Category:</strong> <span>${trip.category || 'Not specified'}</span></li>
                    ${trip.learning_objectives && trip.learning_objectives.length > 0 ? 
                        `<li><strong>Learning Objectives:</strong> <span>${trip.learning_objectives.join(', ')}</span></li>` : ''}
                    ${trip.subjects_covered && trip.subjects_covered.length > 0 ? 
                        `<li><strong>Subjects:</strong> <span>${trip.subjects_covered.join(', ')}</span></li>` : ''}
                </ul>
            `;

            // Logistics
            const logisticsContainer = document.getElementById('edusafariViewTripLogistics');
            logisticsContainer.innerHTML = `
                <ul class="edusafari-detail-list">
                    <li><strong>Transportation:</strong> <span>${trip.transportation_included ? 'Included' : 'Not included'}</span></li>
                    <li><strong>Meals:</strong> <span>${trip.meals_included ? 'Included' : 'Not included'}</span></li>
                    <li><strong>Accommodation:</strong> <span>${trip.accommodation_included ? 'Included' : 'Not included'}</span></li>
                    <li><strong>Meeting Point:</strong> <span>${trip.meeting_point || 'TBD'}</span></li>
                    ${trip.meals_provided && trip.meals_provided.length > 0 ? 
                        `<li><strong>Meals Provided:</strong> <span>${trip.meals_provided.join(', ')}</span></li>` : ''}
                </ul>
            `;

            // Safety & Requirements
            const safetyContainer = document.getElementById('edusafariViewTripSafety');
            safetyContainer.innerHTML = `
                <ul class="edusafari-detail-list">
                    <li><strong>Medical Info Required:</strong> <span>${trip.medical_info_required ? 'Yes' : 'No'}</span></li>
                    <li><strong>Consent Required:</strong> <span>${trip.consent_required ? 'Yes' : 'No'}</span></li>
                    <li><strong>Insurance:</strong> <span>${trip.insurance_required ? 'Required' : 'Not required'}</span></li>
                    ${trip.vaccination_requirements ? 
                        `<li><strong>Vaccinations:</strong> <span>${this.escapeHtml(trip.vaccination_requirements)}</span></li>` : ''}
                    ${trip.special_equipment_needed ? 
                        `<li><strong>Equipment Needed:</strong> <span>${this.escapeHtml(trip.special_equipment_needed)}</span></li>` : ''}
                    ${trip.physical_requirements ? 
                        `<li><strong>Physical Requirements:</strong> <span>${this.escapeHtml(trip.physical_requirements)}</span></li>` : ''}
                </ul>
            `;
        },

        renderRegistrations(data) {
            const stats = data.registration_stats || {};
            
            document.getElementById('edusafariViewRegConfirmed').textContent = stats.confirmed || 0;
            document.getElementById('edusafariViewRegPending').textContent = stats.pending || 0;
            document.getElementById('edusafariViewRegWaitlisted').textContent = stats.waitlisted || 0;
            document.getElementById('edusafariViewRegCancelled').textContent = stats.cancelled || 0;

            // Registrations table
            const tbody = document.getElementById('edusafariViewRegTableBody');
            const registrations = data.registrations || [];

            if (registrations.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: #7f8c8d;">No registrations yet</td></tr>';
                return;
            }

            tbody.innerHTML = registrations.map(reg => `
                <tr>
                    <td>${this.escapeHtml(reg.registration_number || 'N/A')}</td>
                    <td>${this.escapeHtml(reg.participant?.full_name || 'N/A')}</td>
                    <td>
                        ${this.escapeHtml(reg.parent?.full_name || 'N/A')}<br>
                        <small style="color: #7f8c8d;">${this.escapeHtml(reg.parent?.email || '')}</small>
                    </td>
                    <td><span class="edusafari-status-badge edusafari-status-${reg.status}">${this.formatStatus(reg.status)}</span></td>
                    <td><span class="edusafari-status-badge edusafari-status-${reg.payment_status}">${this.formatStatus(reg.payment_status)}</span></td>
                    <td>KES ${parseFloat(reg.amount_paid || 0).toLocaleString()}</td>
                </tr>
            `).join('');
        },

        renderFinancials(data) {
            const financial = data.financial_summary || {};
            const paymentStats = data.payment_stats || {};

            document.getElementById('edusafariViewFinRevenue').textContent = 
                `KES ${parseFloat(financial.total_revenue || 0).toLocaleString()}`;
            
            document.getElementById('edusafariViewFinExpenses').textContent = 
                `KES ${parseFloat(financial.total_expenses || 0).toLocaleString()}`;
            
            const profit = (financial.total_revenue || 0) - (financial.total_expenses || 0);
            const profitEl = document.getElementById('edusafariViewFinProfit');
            profitEl.textContent = `KES ${parseFloat(profit).toLocaleString()}`;
            profitEl.style.color = profit >= 0 ? 'var(--edusafari-success)' : 'var(--edusafari-danger)';

            // Payment breakdown
            document.getElementById('edusafariViewPayFullyPaid').textContent = paymentStats.fully_paid || 0;
            document.getElementById('edusafariViewPayPartial').textContent = paymentStats.partial || 0;
            document.getElementById('edusafariViewPayUnpaid').textContent = paymentStats.unpaid || 0;
        },

        renderServices(data) {
            const tbody = document.getElementById('edusafariViewServicesTableBody');
            const emptyMsg = document.getElementById('edusafariViewServicesEmpty');
            const bookings = data.service_bookings || [];

            if (bookings.length === 0) {
                tbody.innerHTML = '';
                emptyMsg.style.display = 'block';
                return;
            }

            emptyMsg.style.display = 'none';
            tbody.innerHTML = bookings.map(booking => {
                const date = booking.booking_date ? new Date(booking.booking_date).toLocaleDateString() : 'N/A';
                return `
                    <tr>
                        <td>${this.escapeHtml(booking.service_type || 'N/A')}</td>
                        <td>${this.escapeHtml(booking.vendor_name || 'N/A')}</td>
                        <td><span class="edusafari-status-badge edusafari-status-${booking.status}">${this.formatStatus(booking.status)}</span></td>
                        <td>KES ${parseFloat(booking.total_amount || 0).toLocaleString()}</td>
                        <td>${date}</td>
                    </tr>
                `;
            }).join('');
        },

        renderActivity(data) {
            const timeline = document.getElementById('edusafariViewActivityTimeline');
            const emptyMsg = document.getElementById('edusafariViewActivityEmpty');
            const activities = data.recent_activity || [];

            if (activities.length === 0) {
                timeline.innerHTML = '';
                emptyMsg.style.display = 'block';
                return;
            }

            emptyMsg.style.display = 'none';
            timeline.innerHTML = activities.map(activity => {
                const time = activity.created_at ? this.formatRelativeTime(activity.created_at) : 'Unknown';
                return `
                    <div class="edusafari-activity-item">
                        <div class="edusafari-activity-header">
                            <span class="edusafari-activity-action">${this.escapeHtml(activity.action || 'Action')}</span>
                            <span class="edusafari-activity-time">${time}</span>
                        </div>
                        <p class="edusafari-activity-description">${this.escapeHtml(activity.description || '')}</p>
                    </div>
                `;
            }).join('');
        },

        formatStatus(status) {
            const statusMap = {
                'draft': 'Draft',
                'published': 'Published',
                'registration_open': 'Registration Open',
                'registration_closed': 'Registration Closed',
                'full': 'Full',
                'in_progress': 'In Progress',
                'completed': 'Completed',
                'cancelled': 'Cancelled',
                'confirmed': 'Confirmed',
                'pending': 'Pending',
                'waitlisted': 'Waitlisted',
                'paid': 'Paid',
                'partial': 'Partial',
                'unpaid': 'Unpaid',
                'refunded': 'Refunded'
            };
            return statusMap[status] || status;
        },

        formatRelativeTime(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);

            if (diffInSeconds < 60) return 'Just now';
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
            if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
            
            return date.toLocaleDateString();
        },

        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ViewTripModal.init());
    } else {
        ViewTripModal.init();
    }

    // Export to global scope
    window.EdusafariViewTripModal = ViewTripModal;

})();