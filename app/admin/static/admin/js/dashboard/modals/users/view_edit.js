// View User Modal
const viewUserModal = {
    currentUserId: null,
    currentUserData: null,

    async open(userId) {
        this.currentUserId = userId;
        document.getElementById('viewUserModalOverlay').classList.add('active');
        document.getElementById('viewUserModalBody').innerHTML = `
            <div class="view-user-loading">
                <i class="fas fa-spinner"></i>
                <p>Loading user details...</p>
            </div>
        `;
        document.getElementById('viewUserModalFooter').style.display = 'none';

        try {
            const response = await fetch(`/api/admin/user/${userId}`);
            const data = await response.json();

            if (data.success) {
                this.currentUserData = data.data;
                this.render(data.data);
                document.getElementById('viewUserModalFooter').style.display = 'flex';
            } else {
                throw new Error(data.error || 'Failed to load user details');
            }
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('viewUserModalBody').innerHTML = `
                <div class="view-user-loading">
                    <i class="fas fa-exclamation-circle" style="color: var(--danger-color);"></i>
                    <p>${error.message}</p>
                </div>
            `;
        }
    },

    render(user) {
        const initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
        
        let content = `
            <div class="view-user-profile-header">
                ${user.profile_picture ? 
                    `<img src="${user.profile_picture}" alt="${user.full_name}" class="view-user-avatar-large">` :
                    `<div class="view-user-avatar-placeholder-large">${initials}</div>`
                }
                <div class="view-user-profile-info">
                    <h2>${user.full_name}</h2>
                    <div class="view-user-profile-meta">
                        <span class="view-user-badge ${user.role}">
                            <i class="fas ${this.getRoleIcon(user.role)}"></i>
                            ${user.role}
                        </span>
                        <span class="view-user-badge" style="background: ${user.is_active ? '#d5f4e6' : '#f8d7da'}; color: ${user.is_active ? 'var(--success-color)' : 'var(--danger-color)'};">
                            <i class="fas fa-circle" style="font-size: 8px;"></i>
                            ${user.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <span class="view-user-badge" style="background: ${user.is_verified ? '#d5f4e6' : '#fff3cd'}; color: ${user.is_verified ? 'var(--success-color)' : 'var(--warning-color)'};">
                            <i class="fas ${user.is_verified ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                            ${user.is_verified ? 'Verified' : 'Unverified'}
                        </span>
                    </div>
                </div>
            </div>

            <div class="view-user-tabs">
                <button class="view-user-tab active" onclick="viewUserModal.switchTab('details')">
                    <i class="fas fa-info-circle"></i> Details
                </button>
                <button class="view-user-tab" onclick="viewUserModal.switchTab('statistics')">
                    <i class="fas fa-chart-bar"></i> Statistics
                </button>
                ${user.role === 'parent' ? `
                <button class="view-user-tab" onclick="viewUserModal.switchTab('children')">
                    <i class="fas fa-child"></i> Children
                </button>
                ` : ''}
                ${user.role === 'teacher' ? `
                <button class="view-user-tab" onclick="viewUserModal.switchTab('trips')">
                    <i class="fas fa-bus"></i> Trips
                </button>
                ` : ''}
                ${user.role === 'vendor' ? `
                <button class="view-user-tab" onclick="viewUserModal.switchTab('vendor')">
                    <i class="fas fa-store"></i> Vendor Profile
                </button>
                ` : ''}
            </div>

            <!-- Details Tab -->
            <div class="view-user-tab-content active" data-tab="details">
                <h3 class="view-user-section-title">
                    <i class="fas fa-id-card"></i>
                    Personal Information
                </h3>
                <div class="view-user-info-grid">
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Email</div>
                        <div class="view-user-info-value">${user.email}</div>
                    </div>
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Phone</div>
                        <div class="view-user-info-value ${!user.phone ? 'empty' : ''}">${user.phone || 'Not provided'}</div>
                    </div>
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">City</div>
                        <div class="view-user-info-value ${!user.city ? 'empty' : ''}">${user.city || 'Not provided'}</div>
                    </div>
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Country</div>
                        <div class="view-user-info-value ${!user.country ? 'empty' : ''}">${user.country || 'Not provided'}</div>
                    </div>
                </div>

                ${user.address ? `
                <h3 class="view-user-section-title">
                    <i class="fas fa-map-marker-alt"></i>
                    Address
                </h3>
                <div class="view-user-info-item">
                    <div class="view-user-info-value">${user.address}</div>
                </div>
                ` : ''}

                ${user.bio ? `
                <h3 class="view-user-section-title">
                    <i class="fas fa-quote-left"></i>
                    Bio
                </h3>
                <div class="view-user-info-item">
                    <div class="view-user-info-value">${user.bio}</div>
                </div>
                ` : ''}

                ${user.role === 'teacher' && user.school ? `
                <h3 class="view-user-section-title">
                    <i class="fas fa-school"></i>
                    School Information
                </h3>
                <div class="view-user-info-grid">
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">School Name</div>
                        <div class="view-user-info-value">${user.school.name}</div>
                    </div>
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Teacher ID</div>
                        <div class="view-user-info-value">${user.teacher_id || 'Not provided'}</div>
                    </div>
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Department</div>
                        <div class="view-user-info-value">${user.department || 'Not provided'}</div>
                    </div>
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Specialization</div>
                        <div class="view-user-info-value">${user.specialization || 'Not provided'}</div>
                    </div>
                </div>
                ` : ''}

                <h3 class="view-user-section-title">
                    <i class="fas fa-clock"></i>
                    Account Information
                </h3>
                <div class="view-user-info-grid">
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Created At</div>
                        <div class="view-user-info-value">${this.formatDate(user.created_at)}</div>
                    </div>
                    <div class="view-user-info-item">
                        <div class="view-user-info-label">Last Login</div>
                        <div class="view-user-info-value ${!user.last_login ? 'empty' : ''}">${user.last_login ? this.formatDate(user.last_login) : 'Never'}</div>
                    </div>
                </div>
            </div>

            <!-- Statistics Tab -->
            <div class="view-user-tab-content" data-tab="statistics">
                ${this.renderStatistics(user)}
            </div>

            <!-- Children Tab (Parent) -->
            ${user.role === 'parent' ? `
            <div class="view-user-tab-content" data-tab="children">
                ${this.renderChildren(user)}
            </div>
            ` : ''}

            <!-- Trips Tab (Teacher) -->
            ${user.role === 'teacher' ? `
            <div class="view-user-tab-content" data-tab="trips">
                ${this.renderTrips(user)}
            </div>
            ` : ''}

            <!-- Vendor Tab -->
            ${user.role === 'vendor' && user.vendor_profile ? `
            <div class="view-user-tab-content" data-tab="vendor">
                ${this.renderVendorProfile(user.vendor_profile)}
            </div>
            ` : ''}
        `;

        document.getElementById('viewUserModalBody').innerHTML = content;
    },

    renderStatistics(user) {
        if (!user.statistics) return '<p>No statistics available</p>';

        const stats = user.statistics;
        let html = '<div class="view-user-stats-grid">';

        // Common stats
        if (stats.total_logins !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.total_logins}</div>
                    <div class="view-user-stat-label">Total Logins</div>
                </div>
            `;
        }

        if (stats.account_age_days !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.account_age_days}</div>
                    <div class="view-user-stat-label">Account Age (Days)</div>
                </div>
            `;
        }

        // Teacher stats
        if (stats.total_trips !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.total_trips}</div>
                    <div class="view-user-stat-label">Total Trips</div>
                </div>
            `;
        }

        if (stats.active_trips !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.active_trips}</div>
                    <div class="view-user-stat-label">Active Trips</div>
                </div>
            `;
        }

        if (stats.total_students !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.total_students}</div>
                    <div class="view-user-stat-label">Total Students</div>
                </div>
            `;
        }

        // Parent stats
        if (stats.total_children !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.total_children}</div>
                    <div class="view-user-stat-label">Total Children</div>
                </div>
            `;
        }

        if (stats.active_registrations !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.active_registrations}</div>
                    <div class="view-user-stat-label">Active Registrations</div>
                </div>
            `;
        }

        if (stats.total_spent !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">$${stats.total_spent.toFixed(2)}</div>
                    <div class="view-user-stat-label">Total Spent</div>
                </div>
            `;
        }

        if (stats.outstanding_balance !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">$${stats.outstanding_balance.toFixed(2)}</div>
                    <div class="view-user-stat-label">Outstanding Balance</div>
                </div>
            `;
        }

        // Vendor stats
        if (stats.total_bookings !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.total_bookings}</div>
                    <div class="view-user-stat-label">Total Bookings</div>
                </div>
            `;
        }

        if (stats.average_rating !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.average_rating.toFixed(1)}</div>
                    <div class="view-user-stat-label">Average Rating</div>
                </div>
            `;
        }

        if (stats.total_reviews !== undefined) {
            html += `
                <div class="view-user-stat-card">
                    <div class="view-user-stat-value">${stats.total_reviews}</div>
                    <div class="view-user-stat-label">Total Reviews</div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    },

    renderChildren(user) {
        if (!user.children || user.children.length === 0) {
            return '<p style="text-align: center; color: #7f8c8d; padding: 40px;">No children registered</p>';
        }

        let html = '<div class="view-user-children-list">';
        user.children.forEach(child => {
            html += `
                <div class="view-user-child-card">
                    <div class="view-user-child-info">
                        <h4>${child.full_name}</h4>
                        <p>Age: ${child.age || 'N/A'} | Grade: ${child.grade || 'N/A'}</p>
                    </div>
                    <span class="view-user-badge" style="background: ${child.status === 'active' ? '#d5f4e6' : '#f8d7da'}; color: ${child.status === 'active' ? 'var(--success-color)' : 'var(--danger-color)'};">
                        ${child.status}
                    </span>
                </div>
            `;
        });
        html += '</div>';
        return html;
    },

    renderTrips(user) {
        if (!user.upcoming_trips || user.upcoming_trips.length === 0) {
            return '<p style="text-align: center; color: #7f8c8d; padding: 40px;">No upcoming trips</p>';
        }

        let html = '<div class="view-user-children-list">';
        user.upcoming_trips.forEach(trip => {
            html += `
                <div class="view-user-child-card">
                    <div class="view-user-child-info">
                        <h4>${trip.title}</h4>
                        <p>${this.formatDate(trip.start_date)} - ${this.formatDate(trip.end_date)}</p>
                    </div>
                    <span class="view-user-badge ${trip.status === 'published' ? 'teacher' : 'parent'}">
                        ${trip.status}
                    </span>
                </div>
            `;
        });
        html += '</div>';
        return html;
    },

    renderVendorProfile(vendor) {
        return `
            <h3 class="view-user-section-title">
                <i class="fas fa-store"></i>
                Business Information
            </h3>
            <div class="view-user-info-grid">
                <div class="view-user-info-item">
                    <div class="view-user-info-label">Business Name</div>
                    <div class="view-user-info-value">${vendor.business_name}</div>
                </div>
                <div class="view-user-info-item">
                    <div class="view-user-info-label">Business Type</div>
                    <div class="view-user-info-value">${vendor.business_type || 'Not specified'}</div>
                </div>
                <div class="view-user-info-item">
                    <div class="view-user-info-label">Contact Email</div>
                    <div class="view-user-info-value">${vendor.contact_email}</div>
                </div>
                <div class="view-user-info-item">
                    <div class="view-user-info-label">Contact Phone</div>
                    <div class="view-user-info-value">${vendor.contact_phone}</div>
                </div>
                ${vendor.website ? `
                <div class="view-user-info-item">
                    <div class="view-user-info-label">Website</div>
                    <div class="view-user-info-value"><a href="${vendor.website}" target="_blank">${vendor.website}</a></div>
                </div>
                ` : ''}
                <div class="view-user-info-item">
                    <div class="view-user-info-label">Average Rating</div>
                    <div class="view-user-info-value">${vendor.average_rating ? vendor.average_rating.toFixed(1) + ' ⭐' : 'No ratings yet'}</div>
                </div>
            </div>
            ${vendor.description ? `
            <h3 class="view-user-section-title">
                <i class="fas fa-info-circle"></i>
                Description
            </h3>
            <div class="view-user-info-item">
                <div class="view-user-info-value">${vendor.description}</div>
            </div>
            ` : ''}
        `;
    },

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.view-user-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        event.target.closest('.view-user-tab').classList.add('active');

        // Update tab content
        document.querySelectorAll('.view-user-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.querySelector(`.view-user-tab-content[data-tab="${tabName}"]`).classList.add('active');
    },

    switchToEdit() {
        this.close();
        editUserModal.open(this.currentUserId, this.currentUserData);
    },

    getRoleIcon(role) {
        const icons = {
            parent: 'fa-user',
            teacher: 'fa-chalkboard-teacher',
            vendor: 'fa-store',
            admin: 'fa-user-shield'
        };
        return icons[role] || 'fa-user';
    },

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    close() {
        document.getElementById('viewUserModalOverlay').classList.remove('active');
        this.currentUserId = null;
        this.currentUserData = null;
    }
};

// Edit User Modal
const editUserModal = {
    currentUserId: null,

    async open(userId, userData = null) {
        this.currentUserId = userId;
        document.getElementById('editUserModalOverlay').classList.add('active');

        if (userData) {
            this.renderForm(userData);
        } else {
            try {
                const response = await fetch(`/api/admin/user/${userId}`);
                const data = await response.json();

                if (data.success) {
                    this.renderForm(data.data);
                } else {
                    throw new Error(data.error || 'Failed to load user details');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to load user details');
                this.close();
            }
        }
    },

    renderForm(user) {
        const form = document.getElementById('editUserForm');
        
        let formHTML = `
            <div class="view-user-form-group">
                <label class="view-user-form-label">First Name *</label>
                <input type="text" class="view-user-form-input" name="first_name" value="${user.first_name}" required>
            </div>

            <div class="view-user-form-group">
                <label class="view-user-form-label">Last Name *</label>
                <input type="text" class="view-user-form-input" name="last_name" value="${user.last_name}" required>
            </div>

            <div class="view-user-form-group">
                <label class="view-user-form-label">Email *</label>
                <input type="email" class="view-user-form-input" name="email" value="${user.email}" required>
                <small style="color: #7f8c8d; font-size: 0.85rem;">Changing email will unverify the account</small>
            </div>

            <div class="view-user-form-group">
                <label class="view-user-form-label">Phone</label>
                <input type="tel" class="view-user-form-input" name="phone" value="${user.phone || ''}">
            </div>

            <div class="view-user-form-group">
                <label class="view-user-form-label">Bio</label>
                <textarea class="view-user-form-textarea" name="bio">${user.bio || ''}</textarea>
            </div>

            <h3 class="view-user-section-title">
                <i class="fas fa-map-marker-alt"></i>
                Address Information
            </h3>

            <div class="view-user-form-group">
                <label class="view-user-form-label">Address Line 1</label>
                <input type="text" class="view-user-form-input" name="address_line1" value="${user.address_line1 || ''}">
            </div>

            <div class="view-user-form-group">
                <label class="view-user-form-label">Address Line 2</label>
                <input type="text" class="view-user-form-input" name="address_line2" value="${user.address_line2 || ''}">
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                <div class="view-user-form-group">
                    <label class="view-user-form-label">City</label>
                    <input type="text" class="view-user-form-input" name="city" value="${user.city || ''}">
                </div>

                <div class="view-user-form-group">
                    <label class="view-user-form-label">State</label>
                    <input type="text" class="view-user-form-input" name="state" value="${user.state || ''}">
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                <div class="view-user-form-group">
                    <label class="view-user-form-label">Postal Code</label>
                    <input type="text" class="view-user-form-input" name="postal_code" value="${user.postal_code || ''}">
                </div>

                <div class="view-user-form-group">
                    <label class="view-user-form-label">Country</label>
                    <input type="text" class="view-user-form-input" name="country" value="${user.country || ''}">
                </div>
            </div>
        `;

        // Role-specific fields
        if (user.role === 'teacher') {
            formHTML += `
                <h3 class="view-user-section-title">
                    <i class="fas fa-chalkboard-teacher"></i>
                    Teacher Information
                </h3>

                <div class="view-user-form-group">
                    <label class="view-user-form-label">Teacher ID</label>
                    <input type="text" class="view-user-form-input" name="teacher_id" value="${user.teacher_id || ''}">
                </div>

                <div class="view-user-form-group">
                    <label class="view-user-form-label">Department</label>
                    <input type="text" class="view-user-form-input" name="department" value="${user.department || ''}">
                </div>

                <div class="view-user-form-group">
                    <label class="view-user-form-label">Specialization</label>
                    <input type="text" class="view-user-form-input" name="specialization" value="${user.specialization || ''}">
                </div>

                <div class="view-user-form-group">
                    <label class="view-user-form-label">Years of Experience</label>
                    <input type="number" class="view-user-form-input" name="years_of_experience" value="${user.years_of_experience || ''}">
                </div>
            `;
        }

        form.innerHTML = formHTML;
    },

    async submit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());

        // Remove empty strings
        Object.keys(data).forEach(key => {
            if (data[key] === '') {
                data[key] = null;
            }
        });

        try {
            const response = await fetch(`/api/admin/user/${this.currentUserId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                if (typeof userManagement !== 'undefined') {
                    userManagement.showAlert('User updated successfully', 'success');
                    userManagement.loadUsers();
                }
                this.close();
            } else {
                if (result.validation_errors) {
                    let errorMsg = 'Validation errors:\n';
                    Object.entries(result.validation_errors).forEach(([field, error]) => {
                        errorMsg += `${field}: ${error}\n`;
                    });
                    alert(errorMsg);
                } else {
                    throw new Error(result.error || 'Failed to update user');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to update user: ' + error.message);
        }
    },

    close() {
        document.getElementById('editUserModalOverlay').classList.remove('active');
        this.currentUserId = null;
    }
};

// Close modals when clicking outside
document.getElementById('viewUserModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) {
        viewUserModal.close();
    }
});

document.getElementById('editUserModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) {
        editUserModal.close();
    }
});

// Expose to global scope
window.viewUserModal = viewUserModal;
window.editUserModal = editUserModal;