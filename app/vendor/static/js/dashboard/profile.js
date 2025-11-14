// Vendor Profile Management JavaScript
(function() {
    'use strict';

    // State management
    let vpProfileData = null;
    let vpSpecializations = [];

    // Initialize on DOM load
    document.addEventListener('DOMContentLoaded', function() {
        vpInitialize();
    });

    /**
     * Initialize the profile management system
     */
    function vpInitialize() {
        vpBindEvents();
        vpLoadProfile();
    }

    /**
     * Bind event listeners
     */
    function vpBindEvents() {
        // Edit button
        const editBtn = document.getElementById('vpEditProfileBtn');
        if (editBtn) {
            editBtn.addEventListener('click', vpEnterEditMode);
        }

        // Cancel button
        const cancelBtn = document.getElementById('vpCancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', vpCancelEdit);
        }

        // Form submission
        const profileForm = document.getElementById('vpProfileForm');
        if (profileForm) {
            profileForm.addEventListener('submit', vpHandleSubmit);
        }

        // Specializations input
        const specializationsInput = document.getElementById('vpSpecializationsInput');
        if (specializationsInput) {
            specializationsInput.addEventListener('keydown', vpHandleSpecializationInput);
        }
    }

    /**
     * Load vendor profile data
     */
    async function vpLoadProfile() {
        try {
            vpShowLoading(true);
            
            const response = await fetch('/api/vendor/profile', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                vpProfileData = result.data;
                vpPopulateViewMode(result.data);
            } else {
                vpShowAlert('error', result.message || 'Failed to load profile data');
            }
        } catch (error) {
            console.error('Error loading profile:', error);
            vpShowAlert('error', 'Network error. Please check your connection and try again.');
        } finally {
            vpShowLoading(false);
        }
    }

    /**
     * Populate view mode with data
     */
    function vpPopulateViewMode(data) {
        // Business Information
        vpSetText('vpViewBusinessName', data.business_name);
        vpSetText('vpViewBusinessType', vpFormatBusinessType(data.business_type));
        vpSetText('vpViewDescription', data.description);
        vpSetText('vpViewLicenseNumber', data.license_number);
        vpSetText('vpViewCapacity', data.capacity);
        
        // Specializations
        const specializationsContainer = document.getElementById('vpViewSpecializations');
        if (specializationsContainer) {
            specializationsContainer.innerHTML = '';
            if (data.specializations && data.specializations.length > 0) {
                data.specializations.forEach(spec => {
                    const tag = document.createElement('span');
                    tag.className = 'vp-tag';
                    tag.textContent = spec;
                    specializationsContainer.appendChild(tag);
                });
            } else {
                specializationsContainer.innerHTML = '<span class="vp-info-value">-</span>';
            }
        }

        // Contact Information
        vpSetText('vpViewContactEmail', data.contact_email);
        vpSetText('vpViewContactPhone', data.contact_phone);
        vpSetText('vpViewWebsite', data.website);

        // Address
        vpSetText('vpViewAddressLine1', data.address_line1);
        vpSetText('vpViewAddressLine2', data.address_line2);
        vpSetText('vpViewCity', data.city);
        vpSetText('vpViewState', data.state);
        vpSetText('vpViewPostalCode', data.postal_code);
        vpSetText('vpViewCountry', data.country);

        // Pricing
        vpSetText('vpViewBasePrice', vpFormatPrice(data.base_price));
        vpSetText('vpViewPricePerPerson', vpFormatPrice(data.price_per_person));
        vpSetText('vpViewPricingNotes', data.pricing_notes);

        // Insurance
        vpSetText('vpViewInsuranceDetails', data.insurance_details);

        // User Information
        if (data.user_info) {
            vpSetText('vpViewFirstName', data.user_info.first_name);
            vpSetText('vpViewLastName', data.user_info.last_name);
            vpSetText('vpViewEmail', data.user_info.email);
            vpSetText('vpViewPhone', data.user_info.phone);
        }

        // Statistics
        if (data.statistics) {
            vpSetText('vpStatTotalBookings', data.statistics.total_bookings || 0);
            vpSetText('vpStatActiveBookings', data.statistics.active_bookings || 0);
            vpSetText('vpStatAverageRating', 
                (data.statistics.average_rating || 0).toFixed(1));
            vpSetText('vpStatTotalReviews', data.statistics.total_reviews || 0);
        }
    }

    /**
     * Enter edit mode
     */
    function vpEnterEditMode() {
        if (!vpProfileData) {
            vpShowAlert('error', 'Profile data not loaded');
            return;
        }

        // Hide view mode, show edit mode
        document.getElementById('vpViewMode').style.display = 'none';
        document.getElementById('vpEditMode').style.display = 'block';

        // Populate form with current data
        vpPopulateEditForm(vpProfileData);

        // Update header button
        const editBtn = document.getElementById('vpEditProfileBtn');
        if (editBtn) {
            editBtn.style.display = 'none';
        }

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * Populate edit form with data
     */
    function vpPopulateEditForm(data) {
        // Business Information
        vpSetValue('vpBusinessName', data.business_name);
        vpSetValue('vpBusinessType', data.business_type);
        vpSetValue('vpDescription', data.description);
        vpSetValue('vpLicenseNumber', data.license_number);
        vpSetValue('vpCapacity', data.capacity);

        // Specializations
        vpSpecializations = data.specializations || [];
        vpRenderSpecializations();

        // Contact Information
        vpSetValue('vpContactEmail', data.contact_email);
        vpSetValue('vpContactPhone', data.contact_phone);
        vpSetValue('vpWebsite', data.website);

        // Address
        vpSetValue('vpAddressLine1', data.address_line1);
        vpSetValue('vpAddressLine2', data.address_line2);
        vpSetValue('vpCity', data.city);
        vpSetValue('vpState', data.state);
        vpSetValue('vpPostalCode', data.postal_code);
        vpSetValue('vpCountry', data.country);

        // Pricing
        vpSetValue('vpBasePrice', data.base_price);
        vpSetValue('vpPricePerPerson', data.price_per_person);
        vpSetValue('vpPricingNotes', data.pricing_notes);

        // Insurance
        vpSetValue('vpInsuranceDetails', data.insurance_details);
    }

    /**
     * Cancel edit mode
     */
    function vpCancelEdit() {
        // Clear form errors
        vpClearAllErrors();

        // Show view mode, hide edit mode
        document.getElementById('vpViewMode').style.display = 'block';
        document.getElementById('vpEditMode').style.display = 'none';

        // Show edit button
        const editBtn = document.getElementById('vpEditProfileBtn');
        if (editBtn) {
            editBtn.style.display = 'inline-flex';
        }

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * Handle form submission
     */
    async function vpHandleSubmit(e) {
        e.preventDefault();

        // Clear previous errors
        vpClearAllErrors();

        // Get form data
        const formData = vpGetFormData();

        // Client-side validation
        const validationErrors = vpValidateFormData(formData);
        if (Object.keys(validationErrors).length > 0) {
            vpDisplayErrors(validationErrors);
            vpShowAlert('error', 'Please correct the errors in the form');
            return;
        }

        try {
            vpShowLoading(true);
            
            const response = await fetch('/api/vendor/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                vpProfileData = result.data;
                vpPopulateViewMode(result.data);
                vpCancelEdit();
                vpShowAlert('success', result.message || 'Profile updated successfully');
            } else {
                if (result.errors) {
                    vpDisplayErrors(result.errors);
                }
                vpShowAlert('error', result.message || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            vpShowAlert('error', 'Network error. Please check your connection and try again.');
        } finally {
            vpShowLoading(false);
        }
    }

    /**
     * Get form data
     */
    function vpGetFormData() {
        const data = {
            business_name: vpGetValue('vpBusinessName'),
            business_type: vpGetValue('vpBusinessType'),
            description: vpGetValue('vpDescription'),
            license_number: vpGetValue('vpLicenseNumber'),
            capacity: vpGetValue('vpCapacity') ? parseInt(vpGetValue('vpCapacity')) : null,
            specializations: vpSpecializations,
            contact_email: vpGetValue('vpContactEmail'),
            contact_phone: vpGetValue('vpContactPhone'),
            website: vpGetValue('vpWebsite'),
            address_line1: vpGetValue('vpAddressLine1'),
            address_line2: vpGetValue('vpAddressLine2'),
            city: vpGetValue('vpCity'),
            state: vpGetValue('vpState'),
            postal_code: vpGetValue('vpPostalCode'),
            country: vpGetValue('vpCountry'),
            base_price: vpGetValue('vpBasePrice') ? parseFloat(vpGetValue('vpBasePrice')) : null,
            price_per_person: vpGetValue('vpPricePerPerson') ? 
                parseFloat(vpGetValue('vpPricePerPerson')) : null,
            pricing_notes: vpGetValue('vpPricingNotes'),
            insurance_details: vpGetValue('vpInsuranceDetails')
        };

        // Remove empty strings
        Object.keys(data).forEach(key => {
            if (data[key] === '') {
                data[key] = null;
            }
        });

        return data;
    }

    /**
     * Client-side validation
     */
    function vpValidateFormData(data) {
        const errors = {};

        // Business name
        if (!data.business_name || data.business_name.trim().length < 3) {
            errors.business_name = 'Business name must be at least 3 characters';
        }

        // Contact email
        if (!data.contact_email) {
            errors.contact_email = 'Contact email is required';
        } else if (!vpIsValidEmail(data.contact_email)) {
            errors.contact_email = 'Invalid email format';
        }

        // Contact phone
        if (!data.contact_phone) {
            errors.contact_phone = 'Contact phone is required';
        }

        // Capacity
        if (data.capacity !== null && data.capacity < 1) {
            errors.capacity = 'Capacity must be at least 1';
        }

        // Prices
        if (data.base_price !== null && data.base_price < 0) {
            errors.base_price = 'Base price cannot be negative';
        }

        if (data.price_per_person !== null && data.price_per_person < 0) {
            errors.price_per_person = 'Price per person cannot be negative';
        }

        // Website
        if (data.website && !vpIsValidUrl(data.website)) {
            errors.website = 'Invalid URL format. Must start with http:// or https://';
        }

        return errors;
    }

    /**
     * Handle specialization input
     */
    function vpHandleSpecializationInput(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = e.target;
            const value = input.value.trim();

            if (value && !vpSpecializations.includes(value)) {
                vpSpecializations.push(value);
                vpRenderSpecializations();
                input.value = '';
            } else if (vpSpecializations.includes(value)) {
                vpShowAlert('warning', 'Specialization already added');
            }
        }
    }

    /**
     * Render specializations tags
     */
    function vpRenderSpecializations() {
        const container = document.getElementById('vpSpecializationsTags');
        if (!container) return;

        container.innerHTML = '';

        vpSpecializations.forEach((spec, index) => {
            const tag = document.createElement('div');
            tag.className = 'vp-tag-item';
            tag.innerHTML = `
                <span>${vpEscapeHtml(spec)}</span>
                <button type="button" class="vp-tag-remove" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            `;

            const removeBtn = tag.querySelector('.vp-tag-remove');
            removeBtn.addEventListener('click', function() {
                vpRemoveSpecialization(index);
            });

            container.appendChild(tag);
        });
    }

    /**
     * Remove specialization
     */
    function vpRemoveSpecialization(index) {
        vpSpecializations.splice(index, 1);
        vpRenderSpecializations();
    }

    /**
     * Display validation errors
     */
    function vpDisplayErrors(errors) {
        Object.keys(errors).forEach(field => {
            const errorElement = document.getElementById(`vpError${vpCapitalize(field)}`);
            const inputElement = document.getElementById(`vp${vpCapitalize(field)}`);

            if (errorElement) {
                errorElement.textContent = errors[field];
            }

            if (inputElement) {
                inputElement.classList.add('vp-error');
            }
        });
    }

    /**
     * Clear all errors
     */
    function vpClearAllErrors() {
        document.querySelectorAll('.vp-error-message').forEach(el => {
            el.textContent = '';
        });

        document.querySelectorAll('.vp-error').forEach(el => {
            el.classList.remove('vp-error');
        });
    }

    /**
     * Show alert message
     */
    function vpShowAlert(type, message) {
        const container = document.getElementById('vpAlertContainer');
        if (!container) return;

        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle'
        };

        const alert = document.createElement('div');
        alert.className = `vp-alert vp-alert-${type}`;
        alert.innerHTML = `
            <i class="fas ${iconMap[type]}"></i>
            <span>${vpEscapeHtml(message)}</span>
        `;

        container.appendChild(alert);

        // Auto remove after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);

        // Scroll to alert
        alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Show/hide loading overlay
     */
    function vpShowLoading(show) {
        const overlay = document.getElementById('vpLoadingOverlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }

        // Disable/enable buttons
        const buttons = document.querySelectorAll('.vp-btn');
        buttons.forEach(btn => {
            btn.disabled = show;
        });
    }

    // Utility functions
    function vpSetText(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value || '-';
        }
    }

    function vpSetValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value || '';
        }
    }

    function vpGetValue(id) {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    }

    function vpFormatBusinessType(type) {
        if (!type) return '-';
        return type.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    function vpFormatPrice(price) {
        if (price === null || price === undefined) return '-';
        return `${parseFloat(price).toFixed(2)}`;
    }

    function vpCapitalize(str) {
        return str.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join('');
    }

    function vpIsValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function vpIsValidUrl(url) {
        const re = /^https?:\/\/.+/;
        return re.test(url);
    }

    function vpEscapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

})();
