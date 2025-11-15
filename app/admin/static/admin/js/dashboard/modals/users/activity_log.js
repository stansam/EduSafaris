const activityLogModal = {
    currentUserId: null,
    currentPage: 1,
    perPage: 50,
    totalPages: 0,
    currentFilters: {
        action: '',
        category: '',
        status: ''
    },

    async open(userId) {
        this.currentUserId = userId;
        this.currentPage = 1;
        document.getElementById('activityLogModalOverlay').classList.add('active');
        
        // Reset UI
        document.getElementById('activityUserBar').innerHTML = `
            <div class="activity-loading">
                <i class="fas fa-spinner"></i>
            </div>
        `;
        document.getElementById('activityFilters').style.display = 'none';
        document.getElementById('activityPagination').style.display = 'none';

        await this.loadUserInfo();
        await this.loadActivities();
    },

    async loadUserInfo() {
        try {
            const response = await fetch(`/api/admin/user/${this.currentUserId}`);
            const data = await response.json();

            if (data.success) {
                this.renderUserBar(data.data);
            }
        } catch (error) {
            console.error('Error loading user info:', error);
        }
    },

    renderUserBar(user) {
        const initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
        const stats = user.statistics || {};

        document.getElementById('activityUserBar').innerHTML = `
            <div class="activity-user-info">
                <div class="activity-user-avatar">${initials}</div>
                <div class="activity-user-details">
                    <h4>${user.full_name}</h4>
                    <p>${user.email}</p>
                </div>
            </div>
            <div class="activity-stats">
                <div class="activity-stat-item">
                    <div class="activity-stat-value">${stats.total_logins || 0}</div>
                    <div class="activity-stat-label">Total Logins</div>
                </div>
                <div class="activity-stat-item">
                    <div class="activity-stat-value">${stats.account_age_days || 0}</div>
                    <div class="activity-stat-label">Days Active</div>
                </div>
            </div>
        `;
    },

    async loadActivities() {
        const body = document.getElementById('activityModalBody');
        body.innerHTML = `
            <div class="activity-loading">
                <i class="fas fa-spinner"></i>
                <p>Loading activities...</p>
            </div>
        `;

        document.getElementById('activityFilters').style.display = 'none';
        document.getElementById('activityPagination').style.display = 'none';

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.currentFilters
            });

            const response = await fetch(`/api/admin/user/${this.currentUserId}/activity?${params}`);
            const data = await response.json();

            if (data.success) {
                this.totalPages = data.data.pagination.total_pages;
                this.renderActivities(data.data.activities);
                this.renderPagination(data.data.pagination);
                document.getElementById('activityFilters').style.display = 'flex';
                document.getElementById('activityPagination').style.display = 'flex';
                this.attachFilterListeners();
            } else {
                throw new Error(data.error || 'Failed to load activities');
            }
        } catch (error) {
            console.error('Error loading activities:', error);
            body.innerHTML = `
                <div class="activity-empty">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error Loading Activities</h3>
                    <p>${error.message}</p>
                </div>
            `;
        }
    },

    renderActivities(activities) {
        const body = document.getElementById('activityModalBody');

        if (!activities || activities.length === 0) {
            body.innerHTML = `
                <div class="activity-empty">
                    <i class="fas fa-history"></i>
                    <h3>No Activities Found</h3>
                    <p>No activity records match your current filters.</p>
                </div>
            `;
            return;
        }

        let html = '<div class="activity-timeline">';

        activities.forEach(activity => {
            const category = activity.action_category || 'user';
            const status = activity.status || 'success';
            const iconClass = this.getActivityIcon(activity.action, category);

            html += `
                <div class="activity-item">
                    <div class="activity-icon ${category} ${status}">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="activity-content ${status}">
                        <div class="activity-header">
                            <div class="activity-action">${this.formatAction(activity.action)}</div>
                            <div class="activity-time">
                                <i class="far fa-clock"></i>
                                ${this.formatDate(activity.created_at)}
                            </div>
                        </div>
                        <div class="activity-description">
                            ${activity.description || 'No description available'}
                        </div>
                        ${activity.action_category ? `
                            <span class="activity-category-badge ${activity.action_category}">
                                ${activity.action_category}
                            </span>
                        ` : ''}
                        ${this.renderActivityDetails(activity)}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        body.innerHTML = html;
    },

    renderActivityDetails(activity) {
        if (!activity.new_values && !activity.old_values && !activity.metadata) {
            return '';
        }

        let html = '<div class="activity-details">';

        if (activity.old_values || activity.new_values) {
            html += '<div class="activity-detail-row">';
            html += '<div class="activity-detail-label">Changes:</div>';
            html += '<div class="activity-detail-value">';
            
            if (activity.old_values) {
                html += `<strong>From:</strong> ${JSON.stringify(activity.old_values)}<br>`;
            }
            if (activity.new_values) {
                html += `<strong>To:</strong> ${JSON.stringify(activity.new_values)}`;
            }
            
            html += '</div></div>';
        }

        if (activity.metadata) {
            html += '<div class="activity-detail-row">';
            html += '<div class="activity-detail-label">Metadata:</div>';
            html += `<div class="activity-detail-value">${JSON.stringify(activity.metadata)}</div>`;
            html += '</div>';
        }

        if (activity.ip_address) {
            html += '<div class="activity-detail-row">';
            html += '<div class="activity-detail-label">IP Address:</div>';
            html += `<div class="activity-detail-value">${activity.ip_address}</div>`;
            html += '</div>';
        }

        if (activity.error_message) {
            html += '<div class="activity-detail-row">';
            html += '<div class="activity-detail-label">Error:</div>';
            html += `<div class="activity-detail-value" style="color: var(--danger-color);">${activity.error_message}</div>`;
            html += '</div>';
        }

        html += '</div>';
        return html;
    },

    renderPagination(pagination) {
        const info = document.getElementById('activityPaginationInfo');
        const controls = document.getElementById('activityPaginationControls');

        const start = (pagination.page - 1) * pagination.per_page + 1;
        const end = Math.min(pagination.page * pagination.per_page, pagination.total_items);

        info.textContent = `Showing ${start}-${end} of ${pagination.total_items} activities`;

        let buttons = '';

        // Previous button
        buttons += `
            <button class="activity-page-btn" 
                    onclick="activityLogModal.goToPage(${pagination.page - 1})"
                    ${!pagination.has_prev ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, pagination.page - Math.floor(maxVisible / 2));
        let endPage = Math.min(pagination.total_pages, startPage + maxVisible - 1);

        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            buttons += `
                <button class="activity-page-btn ${i === pagination.page ? 'active' : ''}"
                        onclick="activityLogModal.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        // Next button
        buttons += `
            <button class="activity-page-btn"
                    onclick="activityLogModal.goToPage(${pagination.page + 1})"
                    ${!pagination.has_next ? 'disabled' : ''}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        controls.innerHTML = buttons;
    },

    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.loadActivities();
    },

    attachFilterListeners() {
        document.getElementById('activityActionFilter').addEventListener('change', (e) => {
            this.currentFilters.action = e.target.value;
            this.currentPage = 1;
            this.loadActivities();
        });

        document.getElementById('activityCategoryFilter').addEventListener('change', (e) => {
            this.currentFilters.category = e.target.value;
            this.currentPage = 1;
            this.loadActivities();
        });

        document.getElementById('activityStatusFilter').addEventListener('change', (e) => {
            this.currentFilters.status = e.target.value;
            this.currentPage = 1;
            this.loadActivities();
        });
    },

    getActivityIcon(action, category) {
        const iconMap = {
            'login': 'fas fa-sign-in-alt',
            'logout': 'fas fa-sign-out-alt',
            'payment_processed': 'fas fa-credit-card',
            'trip_registration_created': 'fas fa-bus',
            'service_booking_created': 'fas fa-calendar-check',
            'user_updated': 'fas fa-user-edit',
            'user_activated': 'fas fa-user-check',
            'user_deactivated': 'fas fa-user-times',
            'password_reset_initiated': 'fas fa-key',
            'email_verified': 'fas fa-envelope-circle-check',
            'consent_signed': 'fas fa-file-signature',
            'emergency_reported': 'fas fa-exclamation-triangle'
        };

        return iconMap[action] || 'fas fa-circle';
    },

    formatAction(action) {
        return action
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    },

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    close() {
        document.getElementById('activityLogModalOverlay').classList.remove('active');
        this.currentUserId = null;
        this.currentPage = 1;
        this.currentFilters = {
            action: '',
            category: '',
            status: ''
        };
    }
};

// Close modal when clicking outside
document.getElementById('activityLogModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) {
        activityLogModal.close();
    }
});

// Expose to global scope
window.activityLogModal = activityLogModal;