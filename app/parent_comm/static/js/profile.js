(function() {
    'use strict';

    const ProfileManager = {
        config: {
            apiEndpoints: {
                getProfile: '/api/profile',
                updateProfile: '/api/profile/update'
            },
            selectors: {
                loadingOverlay: '#profileLoadingOverlay',
                successAlert: '#profileSuccessAlert',
                errorAlert: '#profileErrorAlert',
                editModal: '#profileEditModal',
                editForm: '#profileEditForm',
                editBtn: '#profileEditBtn',
                modalCloseBtn: '#profileModalCloseBtn',
                cancelBtn: '#profileCancelBtn',
                saveBtn: '#profileSaveBtn'
            },
            timeouts: {
                alertDismiss: 5000,
                requestTimeout: 30000
            }
        },

        state: {
            isLoading: false,
            currentUserData: null,
            isModalOpen: false
        },

        init() {
            this.attachEventListeners();
            this.loadProfileData();
            this.setupFormValidation();
        },

        attachEventListeners() {
            const editBtn = document.getElementById('profileEditBtn');
            const modalCloseBtn = document.getElementById('profileModalCloseBtn');
            const cancelBtn = document.getElementById('profileCancelBtn');
            const editForm = document.getElementById('profileEditForm');
            const bioTextarea = document.getElementById('editBio');

            if (editBtn) {
                editBtn.addEventListener('click', () => this.openEditModal());
            }

            if (modalCloseBtn) {
                modalCloseBtn.addEventListener('click', () => this.closeEditModal());
            }

            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => this.closeEditModal());
            }

            if (editForm) {
                editForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
            }

            if (bioTextarea) {
                bioTextarea.addEventListener('input', (e) => this.updateCharCount(e));
            }

            const modal = document.getElementById('profileEditModal');
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        this.closeEditModal();
                    }
                });
            }

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.state.isModalOpen) {
                    this.closeEditModal();
                }
            });
        },

        async loadProfileData() {
            try {
                this.showLoading(true);

                const response = await this.makeRequest(
                    this.config.apiEndpoints.getProfile,
                    'GET'
                );

                if (response.success && response.data) {
                    this.state.currentUserData = response.data;
                    this.populateProfileView(response.data);
                    this.showLoading(false);
                } else {
                    throw new Error(response.error || 'Failed to load profile data');
                }
            } catch (error) {
                this.showLoading(false);
                this.showError('Failed to load profile: ' + error.message);
                console.error('Profile loading error:', error);
            }
        },

        populateProfileView(data) {
            this.setTextContent('profileUserName', data.full_name || 'N/A');
            this.setTextContent('profileFirstName', data.first_name || '-');
            this.setTextContent('profileLastName', data.last_name || '-');
            this.setTextContent('profileEmail', data.email || '-');
            this.setTextContent('profilePhone', data.phone || '-');
            this.setTextContent('profileDOB', this.formatDate(data.date_of_birth) || '-');
            this.setTextContent('profileSchool', data.school || '-');
            this.setTextContent('profileBio', data.bio || '-');
            this.setTextContent('profileEmergencyContact', data.emergency_contact || '-');
            this.setTextContent('profileEmergencyPhone', data.emergency_phone || '-');

            const statusElement = document.getElementById('profileStatus');
            if (statusElement) {
                statusElement.textContent = data.is_active ? 'Active' : 'Inactive';
                statusElement.style.color = data.is_active ? '#28a745' : '#dc3545';
            }

            this.setTextContent('profileCreatedAt', this.formatDateTime(data.created_at) || '-');
            this.setTextContent('profileLastLogin', this.formatDateTime(data.last_login) || '-');

            const verificationBadge = document.getElementById('profileVerificationBadge');
            if (verificationBadge) {
                if (data.is_verified) {
                    verificationBadge.classList.remove('unverified');
                    verificationBadge.innerHTML = '<i class="fas fa-check-circle"></i><span>Verified</span>';
                } else {
                    verificationBadge.classList.add('unverified');
                    verificationBadge.innerHTML = '<i class="fas fa-exclamation-circle"></i><span>Unverified</span>';
                }
            }

            if (data.statistics) {
                if (data.role === 'parent') {
                    this.setTextContent('profileChildrenCount', data.statistics.children_count || 0);
                    this.setTextContent('profileUpcomingTrips', data.statistics.upcoming_trips || 0);
                } else if (data.role === 'teacher') {
                    this.setTextContent('profileChildrenCount', data.statistics.total_students || 0);
                    this.setTextContent('profileUpcomingTrips', data.statistics.total_trips || 0);
                }
            }
        },

        openEditModal() {
            if (!this.state.currentUserData) {
                this.showError('Profile data not loaded. Please refresh the page.');
                return;
            }

            this.populateEditForm(this.state.currentUserData);

            const modal = document.getElementById('profileEditModal');
            if (modal) {
                modal.classList.add('active');
                this.state.isModalOpen = true;
                document.body.style.overflow = 'hidden';
            }
        },

        closeEditModal() {
            const modal = document.getElementById('profileEditModal');
            if (modal) {
                modal.classList.remove('active');
                this.state.isModalOpen = false;
                document.body.style.overflow = '';
                this.clearFormErrors();
            }
        },

        populateEditForm(data) {
            this.setInputValue('editFirstName', data.first_name);
            this.setInputValue('editLastName', data.last_name);
            this.setInputValue('editEmail', data.email);
            this.setInputValue('editPhone', data.phone);
            this.setInputValue('editDOB', this.formatDateForInput(data.date_of_birth));
            this.setInputValue('editSchool', data.school);
            this.setInputValue('editBio', data.bio);
            this.setInputValue('editEmergencyContact', data.emergency_contact);
            this.setInputValue('editEmergencyPhone', data.emergency_phone);

            const bioTextarea = document.getElementById('editBio');
            if (bioTextarea) {
                this.updateCharCount({ target: bioTextarea });
            }
        },

        async handleFormSubmit(event) {
            event.preventDefault();

            if (this.state.isLoading) {
                return;
            }

            this.clearFormErrors();

            const formData = this.collectFormData();

            const validationErrors = this.validateFormData(formData);
            if (validationErrors.length > 0) {
                this.displayFormErrors(validationErrors);
                return;
            }

            try {
                this.showLoading(true);
                const saveBtn = document.getElementById('profileSaveBtn');
                if (saveBtn) {
                    saveBtn.disabled = true;
                }

                const response = await this.makeRequest(
                    this.config.apiEndpoints.updateProfile,
                    'PUT',
                    formData
                );

                if (response.success) {
                    this.state.currentUserData = response.data;
                    this.populateProfileView(response.data);
                    this.closeEditModal();
                    this.showSuccess(response.message || 'Profile updated successfully');
                } else {
                    if (response.validation_errors && response.validation_errors.length > 0) {
                        this.displayFormErrors(response.validation_errors);
                    } else {
                        throw new Error(response.error || 'Failed to update profile');
                    }
                }
            } catch (error) {
                this.showError('Failed to update profile: ' + error.message);
                console.error('Profile update error:', error);
            } finally {
                this.showLoading(false);
                const saveBtn = document.getElementById('profileSaveBtn');
                if (saveBtn) {
                    saveBtn.disabled = false;
                }
            }
        },

        collectFormData() {
            const formData = {};

            const fields = [
                'first_name', 'last_name', 'email', 'phone',
                'date_of_birth', 'school', 'bio',
                'emergency_contact', 'emergency_phone'
            ];

            fields.forEach(field => {
                const element = document.getElementById('edit' + this.capitalizeFirstLetter(field.replace(/_/g, '')));
                if (element) {
                    const value = element.value.trim();
                    formData[field] = value || null;
                }
            });

            return formData;
        },

        validateFormData(data) {
            const errors = [];

            if (!data.first_name || data.first_name.length < 2) {
                errors.push({ field: 'first_name', message: 'First name must be at least 2 characters' });
            } else if (data.first_name.length > 50) {
                errors.push({ field: 'first_name', message: 'First name must not exceed 50 characters' });
            }

            if (!data.last_name || data.last_name.length < 2) {
                errors.push({ field: 'last_name', message: 'Last name must be at least 2 characters' });
            } else if (data.last_name.length > 50) {
                errors.push({ field: 'last_name', message: 'Last name must not exceed 50 characters' });
            }

            if (!data.email || !this.validateEmail(data.email)) {
                errors.push({ field: 'email', message: 'Invalid email format' });
            }

            if (data.phone && data.phone.length > 20) {
                errors.push({ field: 'phone', message: 'Phone number must not exceed 20 characters' });
            }

            if (data.school && data.school.length > 100) {
                errors.push({ field: 'school', message: 'School name must not exceed 100 characters' });
            }

            if (data.bio && data.bio.length > 1000) {
                errors.push({ field: 'bio', message: 'Bio must not exceed 1000 characters' });
            }

            if (data.emergency_contact && data.emergency_contact.length > 100) {
                errors.push({ field: 'emergency_contact', message: 'Emergency contact name must not exceed 100 characters' });
            }

            if (data.emergency_phone && data.emergency_phone.length > 20) {
                errors.push({ field: 'emergency_phone', message: 'Emergency phone must not exceed 20 characters' });
            }

            return errors;
        },

        displayFormErrors(errors) {
            this.clearFormErrors();

            errors.forEach(error => {
                let fieldName = error.field || this.extractFieldFromMessage(error);
                if (typeof error === 'string') {
                    fieldName = this.extractFieldFromMessage(error);
                }

                const errorMessage = error.message || error;

                const fieldNameCamelCase = this.toCamelCase(fieldName);
                const errorElement = document.getElementById('error' + this.capitalizeFirstLetter(fieldNameCamelCase));
                const inputElement = document.getElementById('edit' + this.capitalizeFirstLetter(fieldNameCamelCase));

                if (errorElement) {
                    errorElement.textContent = errorMessage;
                }

                if (inputElement) {
                    inputElement.classList.add('error');
                }
            });
        },

        extractFieldFromMessage(message) {
            const msgStr = typeof message === 'string' ? message : message.message || '';
            const lowerMsg = msgStr.toLowerCase();

            const fieldMap = {
                'first name': 'firstName',
                'last name': 'lastName',
                'email': 'email',
                'phone': 'phone',
                'date of birth': 'dob',
                'school': 'school',
                'bio': 'bio',
                'emergency contact name': 'emergencyContact',
                'emergency phone': 'emergencyPhone'
            };

            for (const [key, value] of Object.entries(fieldMap)) {
                if (lowerMsg.includes(key)) {
                    return value;
                }
            }

            return '';
        },

        clearFormErrors() {
            const errorElements = document.querySelectorAll('.profile-form-error');
            errorElements.forEach(el => {
                el.textContent = '';
            });

            const inputElements = document.querySelectorAll('.profile-form-input, .profile-form-textarea');
            inputElements.forEach(el => {
                el.classList.remove('error');
            });
        },

        setupFormValidation() {
            const form = document.getElementById('profileEditForm');
            if (!form) return;

            const inputs = form.querySelectorAll('input, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', (e) => {
                    this.validateField(e.target);
                });

                input.addEventListener('input', (e) => {
                    if (e.target.classList.contains('error')) {
                        this.validateField(e.target);
                    }
                });
            });
        },

        validateField(field) {
            const fieldName = field.name;
            const value = field.value.trim();
            const errorElementId = 'error' + this.capitalizeFirstLetter(this.toCamelCase(fieldName));
            const errorElement = document.getElementById(errorElementId);

            if (!errorElement) return;

            let errorMessage = '';

            switch (fieldName) {
                case 'first_name':
                    if (value && value.length < 2) {
                        errorMessage = 'First name must be at least 2 characters';
                    } else if (value.length > 50) {
                        errorMessage = 'First name must not exceed 50 characters';
                    }
                    break;
                case 'last_name':
                    if (value && value.length < 2) {
                        errorMessage = 'Last name must be at least 2 characters';
                    } else if (value.length > 50) {
                        errorMessage = 'Last name must not exceed 50 characters';
                    }
                    break;
                case 'email':
                    if (value && !this.validateEmail(value)) {
                        errorMessage = 'Invalid email format';
                    }
                    break;
                case 'phone':
                    if (value && value.length > 20) {
                        errorMessage = 'Phone number must not exceed 20 characters';
                    }
                    break;
                case 'school':
                    if (value && value.length > 100) {
                        errorMessage = 'School name must not exceed 100 characters';
                    }
                    break;
                case 'bio':
                    if (value && value.length > 1000) {
                        errorMessage = 'Bio must not exceed 1000 characters';
                    }
                    break;
                case 'emergency_contact':
                    if (value && value.length > 100) {
                        errorMessage = 'Emergency contact name must not exceed 100 characters';
                    }
                    break;
                case 'emergency_phone':
                    if (value && value.length > 20) {
                        errorMessage = 'Emergency phone must not exceed 20 characters';
                    }
                    break;
            }

            errorElement.textContent = errorMessage;

            if (errorMessage) {
                field.classList.add('error');
            } else {
                field.classList.remove('error');
            }
        },

        updateCharCount(event) {
            const textarea = event.target;
            const currentLength = textarea.value.length;
            const maxLength = 1000;

            const charCountElement = document.getElementById('bioCharCount');
            if (charCountElement) {
                charCountElement.textContent = currentLength;

                if (currentLength > maxLength) {
                    charCountElement.style.color = '#dc3545';
                } else if (currentLength > maxLength * 0.9) {
                    charCountElement.style.color = '#ffc107';
                } else {
                    charCountElement.style.color = '';
                }
            }
        },

        async makeRequest(url, method = 'GET', data = null) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.timeouts.requestTimeout);

            try {
                const options = {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    signal: controller.signal
                };

                if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
                    options.body = JSON.stringify(data);
                }

                const response = await fetch(url, options);

                clearTimeout(timeoutId);

                if (response.status === 401) {
                    window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
                    throw new Error('Authentication required');
                }

                if (response.status === 403) {
                    throw new Error('You do not have permission to perform this action');
                }

                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned an invalid response');
                }

                const responseData = await response.json();

                if (!response.ok) {
                    throw new Error(responseData.error || `Request failed with status ${response.status}`);
                }

                return responseData;
            } catch (error) {
                clearTimeout(timeoutId);

                if (error.name === 'AbortError') {
                    throw new Error('Request timeout. Please try again.');
                }

                throw error;
            }
        },

        showLoading(show) {
            this.state.isLoading = show;
            const overlay = document.getElementById('profileLoadingOverlay');
            if (overlay) {
                overlay.style.display = show ? 'flex' : 'none';
            }
        },

        showSuccess(message) {
            const alert = document.getElementById('profileSuccessAlert');
            const messageElement = document.getElementById('profileSuccessMessage');

            if (alert && messageElement) {
                messageElement.textContent = message;
                alert.style.display = 'flex';

                setTimeout(() => {
                    this.closeAlert('profileSuccessAlert');
                }, this.config.timeouts.alertDismiss);
            }
        },

        showError(message) {
            const alert = document.getElementById('profileErrorAlert');
            const messageElement = document.getElementById('profileErrorMessage');

            if (alert && messageElement) {
                messageElement.textContent = message;
                alert.style.display = 'flex';

                setTimeout(() => {
                    this.closeAlert('profileErrorAlert');
                }, this.config.timeouts.alertDismiss);
            }
        },

        closeAlert(alertId) {
            const alert = document.getElementById(alertId);
            if (alert) {
                alert.style.display = 'none';
            }
        },

        setTextContent(elementId, value) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = value || '-';
            }
        },

        setInputValue(elementId, value) {
            const element = document.getElementById(elementId);
            if (element) {
                element.value = value || '';
            }
        },

        formatDate(dateString) {
            if (!dateString) return null;

            try {
                const date = new Date(dateString);
                if (isNaN(date.getTime())) return null;

                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            } catch (error) {
                console.error('Date formatting error:', error);
                return null;
            }
        },

        formatDateTime(dateString) {
            if (!dateString) return null;

            try {
                const date = new Date(dateString);
                if (isNaN(date.getTime())) return null;

                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (error) {
                console.error('DateTime formatting error:', error);
                return null;
            }
        },

        formatDateForInput(dateString) {
            if (!dateString) return '';

            try {
                const date = new Date(dateString);
                if (isNaN(date.getTime())) return '';

                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');

                return `${year}-${month}-${day}`;
            } catch (error) {
                console.error('Date input formatting error:', error);
                return '';
            }
        },

        validateEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },

        capitalizeFirstLetter(string) {
            if (!string) return '';
            return string.charAt(0).toUpperCase() + string.slice(1);
        },

        toCamelCase(string) {
            return string.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
        }
    };

    window.closeProfileAlert = function(alertId) {
        ProfileManager.closeAlert(alertId);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            ProfileManager.init();
        });
    } else {
        ProfileManager.init();
    }

})();
