// Register Child Modal Module
const RegisterChildModal = (function() {
    'use strict';

    // State
    const state = {
        currentTripId: null,
        tripData: null,
        submitting: false
    };

    // DOM Elements
    const elements = {
        overlay: null,
        close: null,
        cancelBtn: null,
        form: null,
        submitBtn: null,
        alert: null,
        alertMessage: null,
        
        // Trip Info
        tripTitle: null,
        tripDestination: null,
        tripDate: null,
        tripPrice: null,
        
        // Form Fields
        firstName: null,
        lastName: null,
        dob: null,
        gradeLevel: null,
        studentId: null,
        email: null,
        phone: null,
        medicalConditions: null,
        medications: null,
        allergies: null,
        dietaryRestrictions: null,
        emergencyMedical: null,
        emergency1Name: null,
        emergency1Phone: null,
        emergency1Relationship: null,
        emergency2Name: null,
        emergency2Phone: null,
        emergency2Relationship: null,
        specialRequirements: null,
        
        // Error spans
        firstNameError: null,
        lastNameError: null,
        dobError: null
    };

    // Initialize
    function init() {
        try {
            cacheDOM();
            bindEvents();
        } catch (error) {
            console.error('Failed to initialize RegisterChildModal:', error);
        }
    }

    // Cache DOM Elements
    function cacheDOM() {
        elements.overlay = document.getElementById('registerChildModalOverlay');
        elements.close = document.getElementById('registerChildModalClose');
        elements.cancelBtn = document.getElementById('registerChildCancelBtn');
        elements.form = document.getElementById('registerChildForm');
        elements.submitBtn = document.getElementById('registerChildSubmitBtn');
        elements.alert = document.getElementById('registerChildAlert');
        elements.alertMessage = document.getElementById('registerChildAlertMessage');
        
        // Trip Info
        elements.tripTitle = document.getElementById('registerChildTripTitle');
        elements.tripDestination = document.getElementById('registerChildTripDestination');
        elements.tripDate = document.getElementById('registerChildTripDate');
        elements.tripPrice = document.getElementById('registerChildTripPrice');
        
        // Form Fields
        elements.firstName = document.getElementById('registerChildFirstName');
        elements.lastName = document.getElementById('registerChildLastName');
        elements.dob = document.getElementById('registerChildDOB');
        elements.gradeLevel = document.getElementById('registerChildGradeLevel');
        elements.studentId = document.getElementById('registerChildStudentId');
        elements.email = document.getElementById('registerChildEmail');
        elements.phone = document.getElementById('registerChildPhone');
        elements.medicalConditions = document.getElementById('registerChildMedicalConditions');
        elements.medications = document.getElementById('registerChildMedications');
        elements.allergies = document.getElementById('registerChildAllergies');
        elements.dietaryRestrictions = document.getElementById('registerChildDietaryRestrictions');
        elements.emergencyMedical = document.getElementById('registerChildEmergencyMedical');
        elements.emergency1Name = document.getElementById('registerChildEmergency1Name');
        elements.emergency1Phone = document.getElementById('registerChildEmergency1Phone');
        elements.emergency1Relationship = document.getElementById('registerChildEmergency1Relationship');
        elements.emergency2Name = document.getElementById('registerChildEmergency2Name');
        elements.emergency2Phone = document.getElementById('registerChildEmergency2Phone');
        elements.emergency2Relationship = document.getElementById('registerChildEmergency2Relationship');
        elements.specialRequirements = document.getElementById('registerChildSpecialRequirements');
        
        // Error spans
        elements.firstNameError = document.getElementById('registerChildFirstNameError');
        elements.lastNameError = document.getElementById('registerChildLastNameError');
        elements.dobError = document.getElementById('registerChildDOBError');
    }

    // Bind Events
    function bindEvents() {
        // Close modal
        if (elements.close) {
            elements.close.addEventListener('click', close);
        }
        
        if (elements.cancelBtn) {
            elements.cancelBtn.addEventListener('click', close);
        }
        
        if (elements.overlay) {
            elements.overlay.addEventListener('click', (e) => {
                if (e.target === elements.overlay) {
                    close();
                }
            });
        }
        
        // Form submission
        if (elements.form) {
            elements.form.addEventListener('submit', handleSubmit);
        }
        
        // Real-time validation
        if (elements.firstName) {
            elements.firstName.addEventListener('blur', () => validateField('firstName'));
            elements.firstName.addEventListener('input', () => clearFieldError('firstName'));
        }
        
        if (elements.lastName) {
            elements.lastName.addEventListener('blur', () => validateField('lastName'));
            elements.lastName.addEventListener('input', () => clearFieldError('lastName'));
        }
        
        if (elements.dob) {
            elements.dob.addEventListener('blur', () => validateField('dob'));
            elements.dob.addEventListener('input', () => clearFieldError('dob'));
        }
        
        if (elements.email) {
            elements.email.addEventListener('blur', () => validateEmail());
        }
        
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && elements.overlay && elements.overlay.classList.contains('active')) {
                close();
            }
        });
    }

    // Open Modal
    function open(tripId) {
        if (!tripId) {
            console.error('Trip ID is required');
            return;
        }
        
        state.currentTripId = tripId;
        
        if (elements.overlay) {
            elements.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
        
        resetForm();
        loadTripInfo(tripId);
    }

    // Close Modal
    function close() {
        if (elements.overlay) {
            elements.overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        state.currentTripId = null;
        state.tripData = null;
        resetForm();
    }

    // Load Trip Info
    async function loadTripInfo(tripId) {
        try {
            const response = await fetch(`/api/parent/trips/${tripId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to load trip information');
            }

            const result = await response.json();

            if (result.success && result.data) {
                state.tripData = result.data;
                displayTripInfo(result.data);
            }
        } catch (error) {
            console.error('Error loading trip info:', error);
            showAlert('Failed to load trip information', 'error');
        }
    }

    // Display Trip Info
    function displayTripInfo(trip) {
        if (elements.tripTitle) {
            elements.tripTitle.textContent = trip.title || 'Trip';
        }
        
        if (elements.tripDestination) {
            elements.tripDestination.textContent = trip.destination || 'N/A';
        }
        
        if (elements.tripDate) {
            elements.tripDate.textContent = formatDate(trip.start_date);
        }
        
        if (elements.tripPrice) {
            elements.tripPrice.textContent = `$${formatNumber(trip.price_per_student)}`;
        }
    }

    // Handle Form Submit
    async function handleSubmit(e) {
        e.preventDefault();
        
        if (state.submitting) return;
        
        // Validate form
        if (!validateForm()) {
            showAlert('Please fix the errors in the form', 'error');
            return;
        }
        
        state.submitting = true;
        setSubmitButtonLoading(true);
        hideAlert();
        
        try {
            const formData = collectFormData();
            
            const response = await fetch(`/api/parent/trips/${state.currentTripId}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Success
                if (typeof TripsManager !== 'undefined' && TripsManager.showToast) {
                    TripsManager.showToast('Child registered successfully!', 'success');
                }
                
                if (typeof TripsManager !== 'undefined' && TripsManager.refreshTrips) {
                    TripsManager.refreshTrips();
                }
                
                if (typeof TripsManager !== 'undefined' && TripsManager.refreshRegistrations) {
                    TripsManager.refreshRegistrations();
                }
                
                close();
            } else {
                // Error from server
                let errorMessage = result.message || 'Failed to register child';
                
                if (result.errors) {
                    const errors = Object.values(result.errors);
                    if (errors.length > 0) {
                        errorMessage = errors.join(', ');
                    }
                }
                
                showAlert(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error registering child:', error);
            showAlert('An error occurred while registering. Please try again.', 'error');
        } finally {
            state.submitting = false;
            setSubmitButtonLoading(false);
        }
    }

    // Validate Form
    function validateForm() {
        let isValid = true;
        
        // Required fields
        if (!validateField('firstName')) isValid = false;
        if (!validateField('lastName')) isValid = false;
        if (!validateField('dob')) isValid = false;
        
        // Email validation if provided
        if (elements.email && elements.email.value.trim()) {
            if (!validateEmail()) isValid = false;
        }
        
        return isValid;
    }

    // Validate Field
    function validateField(fieldName) {
        let element, errorElement, errorMessage;
        
        switch (fieldName) {
            case 'firstName':
                element = elements.firstName;
                errorElement = elements.firstNameError;
                errorMessage = 'First name is required';
                break;
            case 'lastName':
                element = elements.lastName;
                errorElement = elements.lastNameError;
                errorMessage = 'Last name is required';
                break;
            case 'dob':
                element = elements.dob;
                errorElement = elements.dobError;
                errorMessage = 'Date of birth is required';
                
                // Additional validation for DOB
                if (element && element.value) {
                    const dob = new Date(element.value);
                    const today = new Date();
                    
                    if (dob > today) {
                        errorMessage = 'Date of birth cannot be in the future';
                    } else {
                        // Check if child is at least 5 years old and not more than 25
                        const age = today.getFullYear() - dob.getFullYear();
                        if (age < 5) {
                            errorMessage = 'Child must be at least 5 years old';
                        } else if (age > 25) {
                            errorMessage = 'Please enter a valid date of birth';
                        } else {
                            // Valid
                            if (errorElement) {
                                errorElement.classList.remove('show');
                            }
                            if (element) {
                                element.classList.remove('error');
                            }
                            return true;
                        }
                    }
                }
                break;
            default:
                return true;
        }
        
        if (!element) return true;
        
        const value = element.value.trim();
        
        if (!value) {
            if (errorElement) {
                errorElement.textContent = errorMessage;
                errorElement.classList.add('show');
            }
            element.classList.add('error');
            return false;
        }
        
        if (errorElement) {
            errorElement.classList.remove('show');
        }
        element.classList.remove('error');
        return true;
    }

    // Validate Email
    function validateEmail() {
        if (!elements.email) return true;
        
        const value = elements.email.value.trim();
        if (!value) return true; // Email is optional
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!emailRegex.test(value)) {
            elements.email.classList.add('error');
            return false;
        }
        
        elements.email.classList.remove('error');
        return true;
    }

    // Clear Field Error
    function clearFieldError(fieldName) {
        let element, errorElement;
        
        switch (fieldName) {
            case 'firstName':
                element = elements.firstName;
                errorElement = elements.firstNameError;
                break;
            case 'lastName':
                element = elements.lastName;
                errorElement = elements.lastNameError;
                break;
            case 'dob':
                element = elements.dob;
                errorElement = elements.dobError;
                break;
            default:
                return;
        }
        
        if (element) {
            element.classList.remove('error');
        }
        
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    // Collect Form Data
    function collectFormData() {
        return {
            first_name: elements.firstName?.value.trim() || '',
            last_name: elements.lastName?.value.trim() || '',
            date_of_birth: elements.dob?.value || '',
            grade_level: elements.gradeLevel?.value.trim() || '',
            student_id: elements.studentId?.value.trim() || '',
            email: elements.email?.value.trim() || '',
            phone: elements.phone?.value.trim() || '',
            medical_conditions: elements.medicalConditions?.value.trim() || '',
            medications: elements.medications?.value.trim() || '',
            allergies: elements.allergies?.value.trim() || '',
            dietary_restrictions: elements.dietaryRestrictions?.value.trim() || '',
            emergency_medical_info: elements.emergencyMedical?.value.trim() || '',
            emergency_contact_1_name: elements.emergency1Name?.value.trim() || '',
            emergency_contact_1_phone: elements.emergency1Phone?.value.trim() || '',
            emergency_contact_1_relationship: elements.emergency1Relationship?.value.trim() || '',
            emergency_contact_2_name: elements.emergency2Name?.value.trim() || '',
            emergency_contact_2_phone: elements.emergency2Phone?.value.trim() || '',
            emergency_contact_2_relationship: elements.emergency2Relationship?.value.trim() || '',
            special_requirements: elements.specialRequirements?.value.trim() || ''
        };
    }

    // Reset Form
    function resetForm() {
        if (elements.form) {
            elements.form.reset();
        }
        
        // Clear all error states
        document.querySelectorAll('.register-child-input, .register-child-textarea').forEach(input => {
            input.classList.remove('error');
        });
        
        document.querySelectorAll('.register-child-error').forEach(error => {
            error.classList.remove('show');
        });
        
        hideAlert();
    }

    // Show Alert
    function showAlert(message, type = 'error') {
        if (!elements.alert || !elements.alertMessage) return;
        
        elements.alertMessage.textContent = message;
        elements.alert.className = `register-child-alert ${type}`;
        elements.alert.style.display = 'flex';
        
        // Scroll to alert
        elements.alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Hide Alert
    function hideAlert() {
        if (elements.alert) {
            elements.alert.style.display = 'none';
        }
    }

    // Set Submit Button Loading
    function setSubmitButtonLoading(loading) {
        if (!elements.submitBtn) return;
        
        if (loading) {
            elements.submitBtn.classList.add('loading');
            elements.submitBtn.disabled = true;
        } else {
            elements.submitBtn.classList.remove('loading');
            elements.submitBtn.disabled = false;
        }
    }

    // Utility Functions
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } catch (error) {
            return dateString;
        }
    }

    function formatNumber(number) {
        if (number === null || number === undefined) return '0.00';
        return parseFloat(number).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    // Return Public API
    return {
        init,
        open,
        close
    };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        RegisterChildModal.init();
    });
} else {
    RegisterChildModal.init();
}