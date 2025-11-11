// Update Child Modal JavaScript

(function() {
    'use strict';

    // State management
    const updateChildModalState = {
        currentStep: 1,
        totalSteps: 3,
        childId: null,
        originalData: {},
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
        triggerButtons: []
    };

    // Initialize modal
    function initUpdateChildModal() {
        cacheElements();
        attachEventListeners();
        setDateConstraints();
    }

    // Cache DOM elements
    function cacheElements() {
        elements.overlay = document.getElementById('updateChildModalOverlay');
        elements.modal = elements.overlay?.querySelector('.ucm-modal-container');
        elements.form = document.getElementById('updateChildForm');
        elements.steps = Array.from(document.querySelectorAll('.ucm-form-step'));
        elements.stepIndicators = Array.from(document.querySelectorAll('.ucm-step'));
        elements.prevBtn = document.getElementById('updateChildPrevBtn');
        elements.nextBtn = document.getElementById('updateChildNextBtn');
        elements.submitBtn = document.getElementById('updateChildSubmitBtn');
        elements.cancelBtn = document.getElementById('updateChildCancelBtn');
        elements.closeBtn = document.getElementById('updateChildModalClose');
        elements.alertContainer = document.getElementById('updateChildAlertContainer');
        elements.loadingOverlay = document.getElementById('updateChildLoadingOverlay');
        elements.triggerButtons = Array.from(document.querySelectorAll('[data-update-child-id]'));
    }

    // Attach event listeners
    function attachEventListeners() {
        if (!elements.form) return;

        // Open modal from trigger buttons
        elements.triggerButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const childId = this.getAttribute('data-update-child-id');
                if (childId) {
                    openUpdateChildModal(childId);
                }
            });
        });

        // Close modal
        elements.closeBtn?.addEventListener('click', closeUpdateChildModal);
        elements.cancelBtn?.addEventListener('click', closeUpdateChildModal);
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
        const dobInput = document.getElementById('ucmDateOfBirth');
        if (!dobInput) return;

        const today = new Date();
        const maxDate = new Date(today.getFullYear() - 3, today.getMonth(), today.getDate());
        const minDate = new Date(today.getFullYear() - 25, today.getMonth(), today.getDate());

        dobInput.max = maxDate.toISOString().split('T')[0];
        dobInput.min = minDate.toISOString().split('T')[0];
    }

    // Open modal
    async function openUpdateChildModal(childId) {
        if (!elements.overlay || !childId) return;
        
        updateChildModalState.childId = childId;
        elements.overlay.classList.add('ucm-show');
        document.body.style.overflow = 'hidden';
        resetModal();
        showStep(1);
        
        // Load child data
        await loadChildData(childId);
    }

    // Load child data from API
    async function loadChildData(childId) {
        showLoading(true);
        clearAlerts();

        try {
            const response = await fetch(`/api/parent/children/${childId}`);
            const data = await response.json();

            if (response.ok && data.success) {
                updateChildModalState.originalData = data.data;
                populateForm(data.child);
            } else {
                showAlert('error', 'Failed to load child data. Please try again.');
                setTimeout(closeUpdateChildModal, 2000);
            }
        } catch (error) {
            console.error('Load error:', error);
            showAlert('error', 'Network error. Please check your connection.');
            setTimeout(closeUpdateChildModal, 2000);
        } finally {
            showLoading(false);
        }
    }

    // Populate form with child data
    function populateForm(childData) {
        // Set child ID
        const childIdInput = document.getElementById('ucmChildId');
        if (childIdInput) {
            childIdInput.value = childData.id || '';
        }

        // Field mapping
        const fieldMapping = {
            first_name: 'ucmFirstName',
            last_name: 'ucmLastName',
            date_of_birth: 'ucmDateOfBirth',
            gender: 'ucmGender',
            grade_level: 'ucmGradeLevel',
            school_name: 'ucmSchoolName',
            email: 'ucmEmail',
            phone: 'ucmPhone',
            blood_type: 'ucmBloodType',
            allergies: 'ucmAllergies',
            medical_conditions: 'ucmMedicalConditions',
            medications: 'ucmMedications',
            dietary_restrictions: 'ucmDietaryRestrictions',
            doctor_name: 'ucmDoctorName',
            doctor_phone: 'ucmDoctorPhone',
            special_requirements: 'ucmSpecialRequirements',
            emergency_contact_1_name: 'ucmEmergencyContact1Name',
            emergency_contact_1_phone: 'ucmEmergencyContact1Phone',
            emergency_contact_1_relationship: 'ucmEmergencyContact1Relationship',
            emergency_contact_1_email: 'ucmEmergencyContact1Email',
            emergency_contact_2_name: 'ucmEmergencyContact2Name',
            emergency_contact_2_phone: 'ucmEmergencyContact2Phone',
            emergency_contact_2_relationship: 'ucmEmergencyContact2Relationship',
            emergency_contact_2_email: 'ucmEmergencyContact2Email'
        };

        // Populate fields
        Object.keys(fieldMapping).forEach(dataKey => {
            const elementId = fieldMapping[dataKey];
            const element = document.getElementById(elementId);
            
            if (element && childData[dataKey] !== undefined && childData[dataKey] !== null) {
                element.value = childData[dataKey];
            }
        });
    }

    // Close modal
    function closeUpdateChildModal() {
        if (!elements.overlay) return;
        
        if (updateChildModalState.isSubmitting) {
            return; // Prevent closing during submission
        }

        elements.overlay.classList.remove('ucm-show');
        document.body.style.overflow = '';
        setTimeout(resetModal, 300);
    }

    // Handle overlay click (close on outside click)
    function handleOverlayClick(e) {
        if (e.target === elements.overlay) {
            closeUpdateChildModal();
        }
    }

    // Handle escape key
    function handleEscapeKey(e) {
        if (e.key === 'Escape' && elements.overlay?.classList.contains('ucm-show')) {
            closeUpdateChildModal();
        }
    }

    // Reset modal to initial state
    function resetModal() {
        updateChildModalState.currentStep = 1;
        updateChildModalState.childId = null;
        updateChildModalState.originalData = {};
        updateChildModalState.isSubmitting = false;
        
        elements.form?.reset();
        clearAllErrors();
        clearAlerts();
        updateNavigationButtons();
    }

    // Navigate to specific step
    function showStep(stepNumber) {
        if (stepNumber < 1 || stepNumber > updateChildModalState.totalSteps) return;

        updateChildModalState.currentStep = stepNumber;

        // Update step content
        elements.steps.forEach((step, index) => {
            if (index + 1 === stepNumber) {
                step.classList.add('ucm-form-step-active');
            } else {
                step.classList.remove('ucm-form-step-active');
            }
        });

        // Update step indicators
        elements.stepIndicators.forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.remove('ucm-step-active', 'ucm-step-completed');
            
            if (stepNum === stepNumber) {
                indicator.classList.add('ucm-step-active');
            } else if (stepNum < stepNumber) {
                indicator.classList.add('ucm-step-completed');
            }
        });

        updateNavigationButtons();
        
        // Scroll to top of modal body
        const modalBody = elements.modal?.querySelector('.ucm-modal-body');
        if (modalBody) {
            modalBody.scrollTop = 0;
        }
    }

    // Update navigation buttons visibility
    function updateNavigationButtons() {
        const isFirstStep = updateChildModalState.currentStep === 1;
        const isLastStep = updateChildModalState.currentStep === updateChildModalState.totalSteps;

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
        if (updateChildModalState.currentStep > 1) {
            showStep(updateChildModalState.currentStep - 1);
        }
    }

    // Go to next step
    function goToNextStep() {
        if (validateCurrentStep()) {
            if (updateChildModalState.currentStep < updateChildModalState.totalSteps) {
                showStep(updateChildModalState.currentStep + 1);
            }
        }
    }

    // Validate current step
    function validateCurrentStep() {
        const currentStepElement = elements.steps[updateChildModalState.currentStep - 1];
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
        field.classList.add('ucm-input-error');
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    // Clear field error
    function clearFieldError(field) {
        field.classList.remove('ucm-input-error');
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

        if (updateChildModalState.isSubmitting) return;

        // Final validation
        if (!validateAllFields()) {
            showAlert('error', 'Please correct the errors in the form.');
            return;
        }

        // Collect form data
        const formData = collectFormData();

        // Check if any changes were made
        if (!hasChanges(formData)) {
            showAlert('warning', 'No changes were made to the profile.');
            return;
        }

        // Submit data
        await submitChildData(formData);
    }

    // Validate all fields
    function validateAllFields() {
        const inputs = elements.form.querySelectorAll('input, select, textarea');
        let isValid = true;

        inputs.forEach(input => {
            if (input.name === 'child_id') return; // Skip hidden field
            
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
            if (input.name === 'child_id') return; // Skip hidden field
            
            const value = input.value.trim();
            if (value || input.hasAttribute('required')) {
                formData[input.name] = value || null;
            }
        });

        return formData;
    }

    // Check if form has changes
    function hasChanges(newData) {
        const originalData = updateChildModalState.originalData;
        
        for (let key in newData) {
            const newValue = newData[key];
            const originalValue = originalData[key];
            
            // Convert both to strings for comparison (handles null/undefined)
            const newStr = newValue === null ? '' : String(newValue);
            const origStr = originalValue === null || originalValue === undefined ? '' : String(originalValue);
            
            if (newStr !== origStr) {
                return true;
            }
        }
        
        return false;
    }

    // Submit child data to API
    async function submitChildData(formData) {
        updateChildModalState.isSubmitting = true;
        showLoading(true);
        clearAlerts();

        const childId = updateChildModalState.childId;

        try {
            const response = await fetch(`/api/parent/children/${childId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert('success', 'Child profile updated successfully!');
                
                // Wait 1.5 seconds then close modal
                setTimeout(() => {
                    closeUpdateChildModal();
                    // Trigger custom event for parent page to refresh data
                    window.dispatchEvent(new CustomEvent('childUpdated', { detail: data.data }));
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
            updateChildModalState.isSubmitting = false;
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
        } else if (data.code === 'NOT_FOUND') {
            showAlert('error', 'Child profile not found or access denied.');
        } else {
            showAlert('error', data.error || 'Failed to update child profile. Please try again.');
        }
    }

    // Show/hide loading overlay
    function showLoading(show) {
        if (elements.loadingOverlay) {
            if (show) {
                elements.loadingOverlay.classList.add('ucm-show');
            } else {
                elements.loadingOverlay.classList.remove('ucm-show');
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
            <div class="ucm-alert ucm-alert-${type}">
                <i class="fas ${icons[type]}"></i>
                <div class="ucm-alert-content">
                    <div class="ucm-alert-title">${titles[type]}</div>
                    <div class="ucm-alert-message">${message}</div>
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

    // Public method to refresh trigger buttons (call after dynamic content loads)
    window.refreshUpdateChildTriggers = function() {
        elements.triggerButtons = Array.from(document.querySelectorAll('[data-update-child-id]'));
        elements.triggerButtons.forEach(btn => {
            // Remove old listener if any
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            // Add new listener
            newBtn.addEventListener('click', function() {
                const childId = this.getAttribute('data-update-child-id');
                if (childId) {
                    openUpdateChildModal(childId);
                }
            });
        });
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initUpdateChildModal);
    } else {
        initUpdateChildModal();
    }

})();