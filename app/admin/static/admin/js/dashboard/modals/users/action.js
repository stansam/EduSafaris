// Toggle Status Modal
const toggleStatusModal = {
    currentUserId: null,
    currentUser: null,

    async open(userId) {
        this.currentUserId = userId;
        document.getElementById('toggleStatusModalOverlay').classList.add('active');
        document.getElementById('toggleStatusLoading').classList.add('active');
        document.getElementById('toggleStatusContent').style.display = 'none';

        try {
            const response = await fetch(`/api/admin/user/${userId}`);
            const data = await response.json();

            if (data.success) {
                this.currentUser = data.data;
                this.render(data.data);
            } else {
                throw new Error(data.error || 'Failed to load user');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load user details');
            this.close();
        }
    },

    render(user) {
        const initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
        
        document.getElementById('toggleStatusUserInfo').innerHTML = `
            <div class="action-modal-avatar">${initials}</div>
            <div class="action-modal-user-details">
                <h4>${user.full_name}</h4>
                <p>${user.email}</p>
            </div>
        `;

        const action = user.is_active ? 'deactivate' : 'activate';
        const actionText = user.is_active ? 'Deactivate' : 'Activate';
        
        document.getElementById('toggleStatusTitle').textContent = `${actionText} User`;
        document.getElementById('toggleStatusWarning').textContent = 
            user.is_active 
                ? 'Deactivating this user will prevent them from logging in and accessing their account.'
                : 'Activating this user will allow them to log in and access their account.';
        document.getElementById('toggleStatusBtnText').textContent = actionText;

        document.getElementById('toggleStatusLoading').classList.remove('active');
        document.getElementById('toggleStatusContent').style.display = 'block';
    },

    async submit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const reason = formData.get('reason') || 'No reason provided';
        const action = this.currentUser.is_active ? 'deactivate' : 'activate';

        const submitBtn = document.getElementById('toggleStatusSubmitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        try {
            const response = await fetch(`/api/admin/user/${this.currentUserId}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ reason })
            });

            const data = await response.json();

            if (data.success) {
                if (typeof userManagement !== 'undefined') {
                    userManagement.showAlert(`User ${action}d successfully`, 'success');
                    userManagement.loadUsers();
                    userManagement.loadStatistics();
                }
                this.close();
            } else {
                throw new Error(data.error || `Failed to ${action} user`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fas fa-toggle-on"></i> ${this.currentUser.is_active ? 'Deactivate' : 'Activate'}`;
        }
    },

    close() {
        document.getElementById('toggleStatusModalOverlay').classList.remove('active');
        document.getElementById('toggleStatusForm').reset();
        this.currentUserId = null;
        this.currentUser = null;
    }
};

// Change Role Modal
const changeRoleModal = {
    currentUserId: null,
    currentUser: null,

    async open(userId) {
        this.currentUserId = userId;
        document.getElementById('changeRoleModalOverlay').classList.add('active');
        document.getElementById('changeRoleLoading').classList.add('active');
        document.getElementById('changeRoleContent').style.display = 'none';

        try {
            const response = await fetch(`/api/admin/user/${userId}`);
            const data = await response.json();

            if (data.success) {
                this.currentUser = data.data;
                this.render(data.data);
            } else {
                throw new Error(data.error || 'Failed to load user');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load user details');
            this.close();
        }
    },

    render(user) {
        const initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
        
        document.getElementById('changeRoleUserInfo').innerHTML = `
            <div class="action-modal-avatar">${initials}</div>
            <div class="action-modal-user-details">
                <h4>${user.full_name}</h4>
                <p>${user.email}</p>
            </div>
        `;

        document.getElementById('currentRoleDisplay').innerHTML = `
            <span style="display: inline-block; padding: 4px 12px; background: #e8f4fd; color: var(--primary-color); border-radius: 12px; font-size: 0.9rem; font-weight: 600;">
                ${user.role.toUpperCase()}
            </span>
        `;

        // Populate role select and exclude current role
        const roleSelect = document.querySelector('#changeRoleForm select[name="role"]');
        Array.from(roleSelect.options).forEach(option => {
            if (option.value === user.role) {
                option.disabled = true;
                option.text += ' (Current)';
            }
        });

        document.getElementById('changeRoleLoading').classList.remove('active');
        document.getElementById('changeRoleContent').style.display = 'block';
    },

    async submit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = {
            role: formData.get('role'),
            reason: formData.get('reason')
        };

        const submitBtn = event.submitter;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Changing...';

        try {
            const response = await fetch(`/api/admin/user/${this.currentUserId}/role`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                if (typeof userManagement !== 'undefined') {
                    userManagement.showAlert('User role changed successfully', 'success');
                    userManagement.loadUsers();
                    userManagement.loadStatistics();
                }
                this.close();
            } else {
                throw new Error(result.error || 'Failed to change role');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Change Role';
        }
    },

    close() {
        document.getElementById('changeRoleModalOverlay').classList.remove('active');
        document.getElementById('changeRoleForm').reset();
        this.currentUserId = null;
        this.currentUser = null;
    }
};

// Reset Password Modal
const resetPasswordModal = {
    currentUserId: null,
    currentUser: null,

    async open(userId) {
        this.currentUserId = userId;
        document.getElementById('resetPasswordModalOverlay').classList.add('active');
        document.getElementById('resetPasswordLoading').classList.add('active');
        document.getElementById('resetPasswordContent').style.display = 'none';

        try {
            const response = await fetch(`/api/admin/user/${userId}`);
            const data = await response.json();

            if (data.success) {
                this.currentUser = data.data;
                this.render(data.data);
            } else {
                throw new Error(data.error || 'Failed to load user');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load user details');
            this.close();
        }
    },

    render(user) {
        const initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
        
        document.getElementById('resetPasswordUserInfo').innerHTML = `
            <div class="action-modal-avatar">${initials}</div>
            <div class="action-modal-user-details">
                <h4>${user.full_name}</h4>
                <p>${user.email}</p>
            </div>
        `;

        document.getElementById('resetPasswordLoading').classList.remove('active');
        document.getElementById('resetPasswordContent').style.display = 'block';
    },

    async submit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const send_email = document.getElementById('sendResetEmail').checked;

        const submitBtn = event.submitter;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        try {
            const response = await fetch(`/api/admin/user/${this.currentUserId}/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ send_email })
            });

            const data = await response.json();

            if (data.success) {
                if (data.data.email_sent) {
                    alert('Password reset email sent successfully!');
                } else {
                    alert(`Password reset token generated:\n\n${data.data.reset_token}\n\nExpires: ${new Date(data.data.expires_at).toLocaleString()}`);
                }
                
                if (typeof userManagement !== 'undefined') {
                    userManagement.showAlert(`User ${action}d successfully`, 'success');
                    userManagement.loadUsers();
                    userManagement.loadStatistics();
                }
                this.close();
            } else {
                throw new Error(data.error || `Failed to ${action} user`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fas fa-toggle-on"></i> ${this.currentUser.is_active ? 'Deactivate' : 'Activate'}`;
        }
    },

    close() {
        document.getElementById('toggleStatusModalOverlay').classList.remove('active');
        document.getElementById('toggleStatusForm').reset();
        this.currentUserId = null;
        this.currentUser = null;
    }
};

// Verify Email Modal
const verifyEmailModal = {
    currentUserId: null,
    currentUser: null,

    async open(userId) {
        this.currentUserId = userId;
        document.getElementById('verifyEmailModalOverlay').classList.add('active');
        document.getElementById('verifyEmailLoading').classList.add('active');
        document.getElementById('verifyEmailContent').style.display = 'none';

        try {
            const response = await fetch(`/api/admin/user/${userId}`);
            const data = await response.json();

            if (data.success) {
                this.currentUser = data.data;
                this.render(data.data);
            } else {
                throw new Error(data.error || 'Failed to load user');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load user details');
            this.close();
        }
    },

    render(user) {
        const initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`;
        
        document.getElementById('verifyEmailUserInfo').innerHTML = `
            <div class="action-modal-avatar">${initials}</div>
            <div class="action-modal-user-details">
                <h4>${user.full_name}</h4>
                <p>${user.email} ${user.is_verified ? '<span style="color: var(--success-color);">✓ Verified</span>' : '<span style="color: var(--warning-color);">⚠ Unverified</span>'}</p>
            </div>
        `;

        if (user.is_verified) {
            document.getElementById('verifyEmailContent').innerHTML = `
                <div class="action-alert action-alert-info">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        <strong>Already Verified:</strong>
                        <p style="margin: 5px 0 0 0;">This user's email is already verified.</p>
                    </div>
                </div>
            `;
            document.querySelector('#verifyEmailModalOverlay .action-modal-footer').innerHTML = `
                <button type="button" class="action-btn action-btn-secondary" onclick="verifyEmailModal.close()">
                    <i class="fas fa-times"></i>
                    Close
                </button>
            `;
        }

        document.getElementById('verifyEmailLoading').classList.remove('active');
        document.getElementById('verifyEmailContent').style.display = 'block';
    },

    toggleMethod() {
        const method = document.getElementById('verifyMethod').value;
        const warning = document.getElementById('manualVerifyWarning');
        const btnText = document.getElementById('verifyEmailBtnText');

        if (method === 'manual') {
            warning.style.display = 'block';
            btnText.textContent = 'Verify Now';
        } else {
            warning.style.display = 'none';
            btnText.textContent = 'Send Verification';
        }
    },

    async submit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const method = formData.get('method');
        const force_verify = method === 'manual';

        const submitBtn = event.submitter;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        try {
            const response = await fetch(`/api/admin/user/${this.currentUserId}/verify-email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ force_verify })
            });

            const data = await response.json();

            if (data.success) {
                if (force_verify) {
                    alert('Email verified successfully!');
                } else {
                    if (data.data.email_sent) {
                        alert('Verification email sent successfully!');
                    } else {
                        alert(`Verification token generated:\n\n${data.data.verification_token}`);
                    }
                }
                
                if (typeof userManagement !== 'undefined') {
                    userManagement.showAlert('Email verification processed successfully', 'success');
                    userManagement.loadUsers();
                    userManagement.loadStatistics();
                }
                this.close();
            } else {
                throw new Error(data.error || 'Failed to verify email');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check"></i> ' + (method === 'manual' ? 'Verify Now' : 'Send Verification');
        }
    },

    close() {
        document.getElementById('verifyEmailModalOverlay').classList.remove('active');
        document.getElementById('verifyEmailForm').reset();
        document.getElementById('manualVerifyWarning').style.display = 'none';
        this.currentUserId = null;
        this.currentUser = null;
    }
};

// Close modals when clicking outside
document.getElementById('toggleStatusModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) toggleStatusModal.close();
});

document.getElementById('changeRoleModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) changeRoleModal.close();
});

document.getElementById('resetPasswordModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) resetPasswordModal.close();
});

document.getElementById('verifyEmailModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) verifyEmailModal.close();
});

// Expose to global scope
window.toggleStatusModal = toggleStatusModal;
window.changeRoleModal = changeRoleModal;
window.resetPasswordModal = resetPasswordModal;
window.verifyEmailModal = verifyEmailModal;

