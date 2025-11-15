// User Management System
const userManagement = {
    currentPage: 1,
    perPage: 20,
    totalPages: 0,
    totalItems: 0,
    selectedUsers: new Set(),
    searchTimeout: null,
    currentFilters: {
        search: '',
        role: '',
        status: '',
        verified: '',
        sort_by: 'created_at',
        sort_order: 'desc'
    },

    init() {
        this.attachEventListeners();
        this.loadStatistics();
        this.loadUsers();
    },

    attachEventListeners() {
        // Search input with debounce
        document.getElementById('userSearchInput').addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.currentFilters.search = e.target.value;
                this.currentPage = 1;
                this.loadUsers();
            }, 500);
        });

        // Filters
        document.getElementById('roleFilter').addEventListener('change', (e) => {
            this.currentFilters.role = e.target.value;
            this.currentPage = 1;
            this.loadUsers();
        });

        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.currentFilters.status = e.target.value;
            this.currentPage = 1;
            this.loadUsers();
        });

        document.getElementById('verifiedFilter').addEventListener('change', (e) => {
            this.currentFilters.verified = e.target.value;
            this.currentPage = 1;
            this.loadUsers();
        });

        document.getElementById('sortByFilter').addEventListener('change', (e) => {
            this.currentFilters.sort_by = e.target.value;
            this.loadUsers();
        });

        document.getElementById('sortOrderFilter').addEventListener('change', (e) => {
            this.currentFilters.sort_order = e.target.value;
            this.loadUsers();
        });
    },

    async loadStatistics() {
        try {
            const response = await fetch('/api/admin/user/statistics');
            const data = await response.json();

            if (data.success) {
                const stats = data.data;
                document.getElementById('totalUsersCount').textContent = stats.overview.total_users;
                document.getElementById('activeUsersCount').textContent = stats.overview.active_users;
                document.getElementById('verifiedUsersCount').textContent = stats.overview.verified_users;
                document.getElementById('newUsersCount').textContent = stats.new_users.last_30_days;
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    },

    async loadUsers() {
        const tbody = document.getElementById('userTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="user-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <h3>Loading users...</h3>
                </td>
            </tr>
        `;

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.currentFilters
            });

            const response = await fetch(`/api/admin/user?${params}`);
            const data = await response.json();

            if (data.success) {
                this.totalPages = data.data.pagination.total_pages;
                this.totalItems = data.data.pagination.total_items;
                this.renderUsers(data.data.users);
                this.renderPagination(data.data.pagination);
            } else {
                throw new Error(data.error || 'Failed to load users');
            }
        } catch (error) {
            console.error('Error loading users:', error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="user-empty">
                        <i class="fas fa-exclamation-circle"></i>
                        <h3>Error Loading Users</h3>
                        <p>${error.message}</p>
                    </td>
                </tr>
            `;
            this.showAlert('Failed to load users. Please try again.', 'error');
        }
    },

    renderUsers(users) {
        const tbody = document.getElementById('userTableBody');

        if (users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="user-empty">
                        <i class="fas fa-users"></i>
                        <h3>No Users Found</h3>
                        <p>Try adjusting your filters or search criteria.</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = users.map(user => {
            const isSelected = this.selectedUsers.has(user.id);
            const initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
            
            return `
                <tr>
                    <td>
                        <input 
                            type="checkbox" 
                            class="user-checkbox user-row-checkbox" 
                            data-user-id="${user.id}"
                            ${isSelected ? 'checked' : ''}
                            onchange="userManagement.toggleUserSelection(${user.id}, this.checked)"
                        >
                    </td>
                    <td>
                        <div class="user-info">
                            ${user.profile_picture ? 
                                `<img src="${user.profile_picture}" alt="${user.full_name}" class="user-avatar">` :
                                `<div class="user-avatar-placeholder">${initials}</div>`
                            }
                            <div class="user-details">
                                <h4>${user.full_name}</h4>
                                <p>${user.email}</p>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="user-badge user-badge-${user.role}">${user.role}</span>
                    </td>
                    <td>
                        <span class="user-status-badge ${user.is_active ? 'user-status-active' : 'user-status-inactive'}">
                            <i class="fas fa-circle" style="font-size: 8px;"></i>
                            ${user.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td>
                        <i class="fas ${user.is_verified ? 'fa-check-circle user-verified' : 'fa-times-circle user-unverified'}" 
                            data-tooltip="${user.is_verified ? 'Verified' : 'Unverified'}"></i>
                    </td>
                    <td>${this.formatDate(user.created_at)}</td>
                    <td>${user.last_login ? this.formatDate(user.last_login) : 'Never'}</td>
                    <td>
                        <div class="user-action-buttons">
                            <button class="user-action-btn view" onclick="userManagement.viewUser(${user.id})" data-tooltip="View Details">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="user-action-btn edit" onclick="userManagement.editUser(${user.id})" data-tooltip="Edit User">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="user-action-btn" onclick="userManagement.showMoreActions(${user.id}, event)" data-tooltip="More Actions">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },

    renderPagination(pagination) {
        const info = document.getElementById('paginationInfo');
        const controls = document.getElementById('paginationControls');

        const start = (pagination.page - 1) * pagination.per_page + 1;
        const end = Math.min(pagination.page * pagination.per_page, pagination.total_items);

        info.textContent = `Showing ${start}-${end} of ${pagination.total_items} users`;

        let buttons = '';

        // Previous button
        buttons += `
            <button class="user-page-btn" 
                    onclick="userManagement.goToPage(${pagination.page - 1})"
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

        if (startPage > 1) {
            buttons += `<button class="user-page-btn" onclick="userManagement.goToPage(1)">1</button>`;
            if (startPage > 2) {
                buttons += `<button class="user-page-btn" disabled>...</button>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            buttons += `
                <button class="user-page-btn ${i === pagination.page ? 'active' : ''}"
                        onclick="userManagement.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        if (endPage < pagination.total_pages) {
            if (endPage < pagination.total_pages - 1) {
                buttons += `<button class="user-page-btn" disabled>...</button>`;
            }
            buttons += `<button class="user-page-btn" onclick="userManagement.goToPage(${pagination.total_pages})">${pagination.total_pages}</button>`;
        }

        // Next button
        buttons += `
            <button class="user-page-btn"
                    onclick="userManagement.goToPage(${pagination.page + 1})"
                    ${!pagination.has_next ? 'disabled' : ''}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        controls.innerHTML = buttons;
    },

    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.loadUsers();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    toggleSelectAll(checkbox) {
        const checkboxes = document.querySelectorAll('.user-row-checkbox');
        checkboxes.forEach(cb => {
            const userId = parseInt(cb.dataset.userId);
            cb.checked = checkbox.checked;
            if (checkbox.checked) {
                this.selectedUsers.add(userId);
            } else {
                this.selectedUsers.delete(userId);
            }
        });
        this.updateBulkActions();
    },

    toggleUserSelection(userId, checked) {
        if (checked) {
            this.selectedUsers.add(userId);
        } else {
            this.selectedUsers.delete(userId);
        }
        this.updateBulkActions();
    },

    updateBulkActions() {
        const bulkActions = document.getElementById('userBulkActions');
        const selectedCount = document.getElementById('selectedCount');
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');

        selectedCount.textContent = `${this.selectedUsers.size} selected`;

        if (this.selectedUsers.size > 0) {
            bulkActions.classList.add('active');
        } else {
            bulkActions.classList.remove('active');
        }

        // Update select all checkbox
        const allCheckboxes = document.querySelectorAll('.user-row-checkbox');
        const allChecked = Array.from(allCheckboxes).every(cb => cb.checked);
        selectAllCheckbox.checked = allChecked && allCheckboxes.length > 0;
    },

    clearSelection() {
        this.selectedUsers.clear();
        document.querySelectorAll('.user-row-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('selectAllCheckbox').checked = false;
        this.updateBulkActions();
    },

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
        
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    },

    showAlert(message, type = 'success') {
        const container = document.getElementById('userAlertContainer');
        const alertId = `alert-${Date.now()}`;
        
        const alertHTML = `
            <div class="user-alert user-alert-${type}" id="${alertId}">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-exclamation-triangle'}"></i>
                <span>${message}</span>
                <i class="fas fa-times user-alert-close" onclick="this.parentElement.remove()"></i>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', alertHTML);
        
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) alert.remove();
        }, 5000);
    },

    async viewUser(userId) {
        // Open view user modal
        window.viewUserModal.open(userId);
    },

    async editUser(userId) {
        // Open edit user modal
        window.editUserModal.open(userId);
    },

    showMoreActions(userId, event) {
        // Create context menu for more actions
        event.stopPropagation();
        
        const existingMenu = document.querySelector('.user-context-menu');
        if (existingMenu) existingMenu.remove();

        const menu = document.createElement('div');
        menu.className = 'user-context-menu';
        menu.style.cssText = `
            position: fixed;
            top: ${event.clientY}px;
            left: ${event.clientX}px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 10000;
            min-width: 200px;
            padding: 8px 0;
        `;

        menu.innerHTML = `
            <div style="padding: 8px 16px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#f5f7fa'" onmouseout="this.style.background='white'" onclick="userManagement.changeRole(${userId})">
                <i class="fas fa-user-tag" style="width: 20px; color: var(--primary-color);"></i> Change Role
            </div>
            <div style="padding: 8px 16px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#f5f7fa'" onmouseout="this.style.background='white'" onclick="userManagement.toggleUserStatus(${userId})">
                <i class="fas fa-toggle-on" style="width: 20px; color: var(--warning-color);"></i> Toggle Status
            </div>
            <div style="padding: 8px 16px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#f5f7fa'" onmouseout="this.style.background='white'" onclick="userManagement.resetPassword(${userId})">
                <i class="fas fa-key" style="width: 20px; color: var(--success-color);"></i> Reset Password
            </div>
            <div style="padding: 8px 16px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#f5f7fa'" onmouseout="this.style.background='white'" onclick="userManagement.verifyEmail(${userId})">
                <i class="fas fa-envelope-circle-check" style="width: 20px; color: var(--primary-color);"></i> Verify Email
            </div>
            <div style="padding: 8px 16px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#f5f7fa'" onmouseout="this.style.background='white'" onclick="userManagement.viewActivity(${userId})">
                <i class="fas fa-history" style="width: 20px; color: var(--dark-color);"></i> View Activity
            </div>
            <hr style="margin: 8px 0; border: none; border-top: 1px solid #ecf0f1;">
            <div style="padding: 8px 16px; cursor: pointer; transition: background 0.2s; color: var(--danger-color);" onmouseover="this.style.background='#fee'" onmouseout="this.style.background='white'" onclick="userManagement.deleteUser(${userId})">
                <i class="fas fa-trash" style="width: 20px;"></i> Delete User
            </div>
        `;

        document.body.appendChild(menu);

        // Close menu when clicking outside
        const closeMenu = (e) => {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        };
        setTimeout(() => document.addEventListener('click', closeMenu), 0);
    },

    async changeRole(userId) {
        window.changeRoleModal.open(userId);
    },

    async toggleUserStatus(userId) {
        window.toggleStatusModal.open(userId);
    },

    async resetPassword(userId) {
        window.resetPasswordModal.open(userId);
    },

    async verifyEmail(userId) {
        window.verifyEmailModal.open(userId);
    },

    async viewActivity(userId) {
        window.activityLogModal.open(userId);
    },

    async deleteUser(userId) {
        // Implement delete confirmation and action
        if (confirm('Are you sure you want to delete this user? This action may be irreversible.')) {
            // Implement delete logic
            console.log('Delete user:', userId);
        }
    },

    async bulkActivate() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`Activate ${this.selectedUsers.size} users?`)) return;

        try {
            const response = await fetch('/api/admin/user/bulk-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_ids: Array.from(this.selectedUsers),
                    action: 'activate',
                    reason: 'Bulk activation by admin'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert(`Successfully activated ${data.data.success.length} users`, 'success');
                this.clearSelection();
                this.loadUsers();
                this.loadStatistics();
            } else {
                throw new Error(data.error || 'Failed to activate users');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert(error.message, 'error');
        }
    },

    async bulkDeactivate() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`Deactivate ${this.selectedUsers.size} users?`)) return;

        try {
            const response = await fetch('/api/admin/user/bulk-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_ids: Array.from(this.selectedUsers),
                    action: 'deactivate',
                    reason: 'Bulk deactivation by admin'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert(`Successfully deactivated ${data.data.success.length} users`, 'success');
                this.clearSelection();
                this.loadUsers();
                this.loadStatistics();
            } else {
                throw new Error(data.error || 'Failed to deactivate users');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert(error.message, 'error');
        }
    },

    async bulkVerify() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`Verify email for ${this.selectedUsers.size} users?`)) return;

        try {
            const response = await fetch('/api/admin/user/bulk-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_ids: Array.from(this.selectedUsers),
                    action: 'verify_email',
                    reason: 'Bulk verification by admin'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert(`Successfully verified ${data.data.success.length} users`, 'success');
                this.clearSelection();
                this.loadUsers();
                this.loadStatistics();
            } else {
                throw new Error(data.error || 'Failed to verify users');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert(error.message, 'error');
        }
    },

    async exportUsers() {
        try {
            const params = new URLSearchParams(this.currentFilters);
            const response = await fetch(`/api/admin/user/export?${params}`);
            const data = await response.json();

            if (data.success) {
                // Create and download CSV
                const blob = new Blob([data.data.csv_content], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.data.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                this.showAlert('Users exported successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to export users');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Failed to export users', 'error');
        }
    },

    refreshData() {
        this.loadStatistics();
        this.loadUsers();
        this.showAlert('Data refreshed successfully', 'success');
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => userManagement.init());
} else {
    userManagement.init();
}