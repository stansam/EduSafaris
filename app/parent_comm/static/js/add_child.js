// Add Child Modal JavaScript

(function() {
    'use strict';

    // State management
    const addChildModalState = {
        currentStep: 1,
        totalSteps: 3,
        formData: {},
        isSubmitting: false
    };

    // DOM elements
    const elements = {
        modal: null,
        overlay: null,
        form: null,
        steps: [],
        stepIndicators: [],
        prevBtn: null,
        nextBtn: null,
        submitBtn: null,
        cancelBtn: null,
        closeBtn: null,
        alertContainer: null,
        loadingOverlay: null,
        triggerBtn: null
    };

    // Initialize modal
    function initAddChildModal() {
        cacheElements();
        attachEventListeners();
        setDateConstraints();
    }

    // Cache DOM elements
    function cacheElements() {
        elements.overlay = document.getElementById('addChildModalOverlay');
        elements.modal = elements.overlay?.querySelector('.acm-modal-container');
        elements.form = document.getElementById('addChildForm');
        elements.steps = Array.from(document.querySelectorAll('.acm-form-step'));
        elements.stepIndicators = Array.from(document.querySelectorAll('.acm-step'));
        elements.prevBtn = document.getElementById('addChildPrevBtn');
        elements.nextBtn = document.getElementById('addChildNextBtn');
        elements.submitBtn = document.getElementById('addChildSubmitBtn');
        elements.cancelBtn = document.getElementById('addChildCancelBtn');
        elements.closeBtn = document.getElementById('addChildModalClose');
        elements.alertContainer = document.getElementById('addChildAlertContainer');
        elements.loadingOverlay = document.getElementById('addChildLoadingOverlay');
        elements.triggerBtn = document.getElementById('openAddChildModal');
    }

    // Attach event listeners
    function attachEventListeners() {
        if (!elements.form) return;

        // Open modal
        elements.triggerBtn?.addEventListener('click', openAddChildModal);

        // Close modal
        elements.closeBtn?.addEventListener('click', closeAddChildModal);
        elements.cancelBtn?.addEventListener('click', closeAddChildModal);
        elements.overlay?.addEventListener('click', handleOverlayClick);

        // Navigation
        elements.prevBtn?.addEventListener('click', goToPreviousStep);
        elements.nextBtn?.addEventListener('click', goToNextStep);

        // Form submission
        elements.form.addEventListener('submit', handleFormSubmit);

        // Real-time validation
        const inputs = elements.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => clearFieldError(input));
        });

        // Escape key to close
        document.addEventListener('keydown', handleEscapeKey);
    }

    // Set date constraints for date of birth
    function setDateConstraints() {
        const dobInput = document.getElementById('acmDateOfBirth');
        if (!dobInput) return;

        const today = new Date();
        const maxDate = new Date(today.getFullYear() - 3, today.getMonth(), today.getDate());
        const minDate = new Date(today.getFullYear() - 25, today.getMonth(), today.getDate());

        dobInput.max = maxDate.toISOString().split('T')[0];
        dobInput.min = minDate.toISOString().split('T')[0];
    }

    // Open modal
    function openAddChildModal() {
        if (!elements.overlay) return;
        
        elements.overlay.classList.add('acm-show');
        document.body.style.overflow = 'hidden';
        resetModal();
        showStep(1);
    }

    // Close modal
    function closeAddChildModal() {
        if (!elements.overlay) return;
        
        if (addChildModalState.isSubmitting) {
            return; // Prevent closing during submission
        }

        elements.overlay.classList.remove('acm-show');
        document.body.style.overflow = '';
        setTimeout(resetModal, 300);
    }

    // Handle overlay click (close on outside click)
    function handleOverlayClick(e) {
        if (e.target === elements.overlay) {
            closeAddChildModal();
        }
    }

    // Handle escape key
    function handleEscapeKey(e) {
        if (e.key === 'Escape' && elements.overlay?.classList.contains('acm-show')) {
            closeAddChildModal();
        }
    }

    // Reset modal to initial state
    function resetModal() {
        addChildModalState.currentStep = 1;
        addChildModalState.formData = {};
        addChildModalState.isSubmitting = false;
        
        elements.form?.reset();
        clearAllErrors();
        clearAlerts();
        updateNavigationButtons();
    }

    // Navigate to specific step
    function showStep(stepNumber) {
        if (stepNumber < 1 || stepNumber > addChildModalState.totalSteps) return;

        addChildModalState.currentStep = stepNumber;

        // Update step content
        elements.steps.forEach((step, index) => {
            if (index + 1 === stepNumber) {
                step.classList.add('acm-form-step-active');
            } else {
                step.classList.remove('acm-form-step-active');
            }
        });

        // Update step indicators
        elements.stepIndicators.forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.remove('acm-step-active', 'acm-step-completed');
            
            if (stepNum === stepNumber) {
                indicator.classList.add('acm-step-active');
            } else if (stepNum < stepNumber) {
                indicator.classList.add('acm-step-completed');
            }
        });

        updateNavigationButtons();
        
        // Scroll to top of modal body
        const modalBody = elements.modal?.querySelector('.acm-modal-body');
        if (modalBody) {
            modalBody.scrollTop = 0;
        }
    }

    // Update navigation buttons visibility
    function updateNavigationButtons() {
        const isFirstStep = addChildModalState.currentStep === 1;
        const isLastStep = addChildModalState.currentStep === addChildModalState.totalSteps;

        if (elements.prevBtn) {
            elements.prevBtn.style.display = isFirstStep ? 'none' : 'inline-flex';
        }

        if (elements.nextBtn) {
            elements.nextBtn.style.display = isLastStep ? 'none' : 'inline-flex';
        }

        if (elements.submitBtn) {
            elements.submitBtn.style.display = isLastStep ? 'inline-flex' : 'none';
        }
    }

    // Go to previous step
    function goToPreviousStep() {
        if (addChildModalState.currentStep > 1) {
            showStep(addChildModalState.currentStep - 1);
        }
    }

    // Go to next step
    function goToNextStep() {
        if (validateCurrentStep()) {
            if (addChildModalState.currentStep < addChildModalState.totalSteps) {
                showStep(addChildModalState.currentStep + 1);
            }
        }
    }

    // Validate current step
    function validateCurrentStep() {
        const currentStepElement = elements.steps[addChildModalState.currentStep - 1];
        const inputs = currentStepElement.querySelectorAll('input[required], select[required], textarea[required]');
        
        let isValid = true;
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });

        if (!isValid) {
            showAlert('error', 'Please fill in all required fields correctly.');
        }

        return isValid;
    }

    // Validate individual field
    function validateField(field) {
        const fieldName = field.name;
        const fieldValue = field.value.trim();
        const errorElement = document.getElementById(`${field.id}Error`);

        // Clear previous error
        clearFieldError(field);

        // Required field validation
        if (field.hasAttribute('required') && !fieldValue) {
            setFieldError(field, errorElement, 'This field is required');
            return false;
        }

        // Skip further validation if field is empty and not required
        if (!fieldValue && !field.hasAttribute('required')) {
            return true;
        }

        // Field-specific validation
        switch (fieldName) {
            case 'first_name':
            case 'last_name':
                if (fieldValue.length < 2) {
                    setFieldError(field, errorElement, 'Must be at least 2 characters');
                    return false;
                }
                if (fieldValue.length > 50) {
                    setFieldError(field, errorElement, 'Must not exceed 50 characters');
                    return false;
                }
                break;

            case 'date_of_birth':
                if (!isValidDateOfBirth(fieldValue)) {
                    setFieldError(field, errorElement, 'Participant must be 3-25 years old');
                    return false;
                }
                break;

            case 'email':
            case 'emergency_contact_1_email':
            case 'emergency_contact_2_email':
                if (fieldValue && !isValidEmail(fieldValue)) {
                    setFieldError(field, errorElement, 'Invalid email format');
                    return false;
                }
                break;

            case 'phone':
            case 'emergency_contact_1_phone':
            case 'emergency_contact_2_phone':
            case 'doctor_phone':
                if (fieldValue && !isValidPhone(fieldValue)) {
                    setFieldError(field, errorElement, 'Invalid phone number format');
                    return false;
                }
                break;

            case 'gender':
                const validGenders = ['male', 'female', 'other', 'prefer_not_to_say'];
                if (!validGenders.includes(fieldValue)) {
                    setFieldError(field, errorElement, 'Please select a valid gender');
                    return false;
                }
                break;

            case 'blood_type':
                if (fieldValue) {
                    const validBloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
                    if (!validBloodTypes.includes(fieldValue)) {
                        setFieldError(field, errorElement, 'Please select a valid blood type');
                        return false;
                    }
                }
                break;
        }

        return true;
    }

    // Validation helper functions
    function isValidEmail(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return pattern.test(email);
    }

    function isValidPhone(phone) {
        const cleaned = phone.replace(/[\s\-\(\)]/g, '');
        const pattern = /^(\+?\d{1,4})?[\d]{9,15}$/;
        return pattern.test(cleaned);
    }

    function isValidDateOfBirth(dateString) {
        try {
            const dob = new Date(dateString);
            const today = new Date();
            const age = today.getFullYear() - dob.getFullYear() - 
                       ((today.getMonth() < dob.getMonth() || 
                        (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate())) ? 1 : 0);
            
            return age >= 3 && age <= 25 && dob < today;
        } catch {
            return false;
        }
    }

    // Set field error
    function setFieldError(field, errorElement, message) {
        field.classList.add('acm-input-error');
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    // Clear field error
    function clearFieldError(field) {
        field.classList.remove('acm-input-error');
        const errorElement = document.getElementById(`${field.id}Error`);
        if (errorElement) {
            errorElement.textContent = '';
        }
    }

    // Clear all errors
    function clearAllErrors() {
        const inputs = elements.form?.querySelectorAll('input, select, textarea');
        inputs?.forEach(clearFieldError);
    }

    // Handle form submission
    async function handleFormSubmit(e) {
        e.preventDefault();

        if (addChildModalState.isSubmitting) return;

        // Final validation
        if (!validateAllFields()) {
            showAlert('error', 'Please correct the errors in the form.');
            return;
        }

        // Collect form data
        const formData = collectFormData();

        // Submit data
        await submitChildData(formData);
    }

    // Validate all fields
    function validateAllFields() {
        const inputs = elements.form.querySelectorAll('input, select, textarea');
        let isValid = true;

        inputs.forEach(input => {
            if (input.hasAttribute('required') || input.value.trim()) {
                if (!validateField(input)) {
                    isValid = false;
                }
            }
        });

        return isValid;
    }

    // Collect form data
    function collectFormData() {
        const formData = {};
        const inputs = elements.form.querySelectorAll('input, select, textarea');

        inputs.forEach(input => {
            const value = input.value.trim();
            if (value || input.hasAttribute('required')) {
                formData[input.name] = value || null;
            }
        });

        return formData;
    }

    // Submit child data to API
    async function submitChildData(formData) {
        addChildModalState.isSubmitting = true;
        showLoading(true);
        clearAlerts();

        try {
            const response = await fetch('/api/parent/children', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert('success', 'Child profile created successfully!');
                
                // Wait 1.5 seconds then close modal and reload
                setTimeout(() => {
                    closeAddChildModal();
                    // Trigger custom event for parent page to refresh data
                    window.dispatchEvent(new CustomEvent('childAdded', { detail: data.data }));
                    // Or reload the page
                    // window.location.reload();
                }, 1500);
            } else {
                handleSubmissionError(data);
            }
        } catch (error) {
            console.error('Submission error:', error);
            showAlert('error', 'Network error. Please check your connection and try again.');
        } finally {
            addChildModalState.isSubmitting = false;
            showLoading(false);
        }
    }

    // Handle submission errors
    function handleSubmissionError(data) {
        if (data.code === 'VALIDATION_ERROR' && data.details) {
            // Show field-specific errors
            Object.keys(data.details).forEach(fieldName => {
                const input = elements.form.querySelector(`[name="${fieldName}"]`);
                if (input) {
                    const errorElement = document.getElementById(`${input.id}Error`);
                    setFieldError(input, errorElement, data.details[fieldName]);
                }
            });
            showAlert('error', 'Please correct the validation errors.');
        } else if (data.code === 'DUPLICATE_CHILD') {
            showAlert('error', 'A child with the same name and date of birth already exists.');
        } else {
            showAlert('error', data.error || 'Failed to create child profile. Please try again.');
        }
    }

    // Show/hide loading overlay
    function showLoading(show) {
        if (elements.loadingOverlay) {
            if (show) {
                elements.loadingOverlay.classList.add('acm-show');
            } else {
                elements.loadingOverlay.classList.remove('acm-show');
            }
        }
    }

    // Show alert message
    function showAlert(type, message, title = null) {
        if (!elements.alertContainer) return;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle'
        };

        const titles = {
            success: title || 'Success',
            error: title || 'Error',
            warning: title || 'Warning'
        };

        const alertHTML = `
            <div class="acm-alert acm-alert-${type}">
                <i class="fas ${icons[type]}"></i>
                <div class="acm-alert-content">
                    <div class="acm-alert-title">${titles[type]}</div>
                    <div class="acm-alert-message">${message}</div>
                </div>
            </div>
        `;

        elements.alertContainer.innerHTML = alertHTML;

        // Scroll to alert
        elements.alertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                clearAlerts();
            }, 5000);
        }
    }

    // Clear alerts
    function clearAlerts() {
        if (elements.alertContainer) {
            elements.alertContainer.innerHTML = '';
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAddChildModal);
    } else {
        initAddChildModal();
    }

})();