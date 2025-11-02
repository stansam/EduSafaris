/**
 * Teacher Registration Form Handler
 * Handles multi-step form, validation, and API communication
 */

(function() {
    'use strict';
    
    // State
    let currentStep = 1;
    let formData = {};
    let emailCheckTimeout = null;
    
    // DOM Elements
    const form = document.getElementById('teacherRegistrationForm');
    const alertContainer = document.getElementById('alert-container');
    
    // Initialize
    document.addEventListener('DOMContentLoaded', init);
    
    function init() {
        setupFormHandlers();
        setupPasswordStrength();
        setupPasswordToggle();
        setupEmailValidation();
        setupPhoneFormatting();
    }
    
    /**
     * Setup form submission and validation
     */
    function setupFormHandlers() {
        if (!form) return;
        
        form.addEventListener('submit', handleSubmit);
        
        // Real-time validation for all inputs
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('error')) {
                    validateField(input);
                }
            });
        });
    }
    
    /**
     * Validate individual field
     */
    function validateField(field) {
        const value = field.value.trim();
        const name = field.name;
        let isValid = true;
        let errorMessage = '';
        
        // Required field check
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }
        
        // Specific validations
        if (value) {
            switch(name) {
                case 'email':
                    if (!isValidEmail(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid email address';
                    }
                    break;
                    
                case 'phone':
                case 'emergency_phone':
                    if (!isValidPhone(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid phone number';
                    }
                    break;
                    
                case 'password':
                    const passwordValidation = validatePassword(value);
                    if (!passwordValidation.isValid) {
                        isValid = false;
                        errorMessage = 'Password does not meet requirements';
                    }
                    break;
                    
                case 'confirm_password':
                    const password = document.getElementById('password').value;
                    if (value !== password) {
                        isValid = false;
                        errorMessage = 'Passwords do not match';
                    }
                    break;
                    
                case 'first_name':
                case 'last_name':
                    if (value.length < 2) {
                        isValid = false;
                        errorMessage = 'Name must be at least 2 characters';
                    }
                    break;
            }
        }
        
        // Update UI
        updateFieldStatus(field, isValid, errorMessage);
        return isValid;
    }
    
    /**
     * Update field status visually
     */
    function updateFieldStatus(field, isValid, errorMessage) {
        const errorElement = field.parentElement.querySelector('.error-message');
        
        if (isValid) {
            field.classList.remove('error');
            field.classList.add('success');
            if (errorElement) {
                errorElement.classList.remove('active');
            }
        } else {
            field.classList.remove('success');
            field.classList.add('error');
            if (errorElement) {
                errorElement.textContent = errorMessage;
                errorElement.classList.add('active');
            }
        }
    }
    
    /**
     * Email validation
     */
    function isValidEmail(email) {
        const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return re.test(email);
    }
    
    /**
     * Phone validation
     */
    function isValidPhone(phone) {
        const cleaned = phone.replace(/[\s\-\(\)]/g, '');
        return /^\+?\d{10,15}$/.test(cleaned);
    }
    
    /**
     * Setup email availability check
     */
    function setupEmailValidation() {
        const emailInput = document.getElementById('email');
        if (!emailInput) return;
        
        emailInput.addEventListener('input', function() {
            clearTimeout(emailCheckTimeout);
            const email = this.value.trim();
            
            if (isValidEmail(email)) {
                emailCheckTimeout = setTimeout(() => {
                    checkEmailAvailability(email);
                }, 500);
            }
        });
    }
    
    /**
     * Check email availability via API
     */
    async function checkEmailAvailability(email) {
        try {
            // const token = document.querySelector('meta[name="csrf-token"]').content;
            const response = await fetch('/api/auth/check-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // 'X-CSRFToken': token
                },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            const emailInput = document.getElementById('email');
            
            if (!data.available) {
                updateFieldStatus(emailInput, false, 'This email is already registered');
            }
        } catch (error) {
            console.error('Email check failed:', error);
        }
    }
    
    /**
     * Setup password strength indicator
     */
    function setupPasswordStrength() {
        const passwordInput = document.getElementById('password');
        if (!passwordInput) return;
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const result = validatePassword(password);
            updatePasswordStrength(result);
            updatePasswordRequirements(result);
        });
    }
    
    /**
     * Validate password and return strength
     */
    function validatePassword(password) {
        const requirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password)
        };
        
        const metCount = Object.values(requirements).filter(Boolean).length;
        let strength = 'weak';
        
        if (metCount === 4) strength = 'strong';
        else if (metCount >= 3) strength = 'medium';
        
        return {
            isValid: metCount === 4,
            strength,
            requirements
        };
    }
    
    /**
     * Update password strength bar
     */
    function updatePasswordStrength(result) {
        const strengthFill = document.querySelector('.strength-fill');
        const strengthText = document.querySelector('.strength-text');
        
        if (!strengthFill || !strengthText) return;
        
        strengthFill.className = 'strength-fill ' + result.strength;
        strengthText.className = 'strength-text ' + result.strength;
        
        const strengthLabels = {
            weak: 'Weak',
            medium: 'Medium',
            strong: 'Strong'
        };
        
        strengthText.textContent = strengthLabels[result.strength];
    }
    
    /**
     * Update password requirements checklist
     */
    function updatePasswordRequirements(result) {
        Object.entries(result.requirements).forEach(([key, met]) => {
            const requirement = document.querySelector(`[data-requirement="${key}"]`);
            if (requirement) {
                if (met) {
                    requirement.classList.add('met');
                } else {
                    requirement.classList.remove('met');
                }
            }
        });
    }
    
    /**
     * Setup password visibility toggle
     */
    function setupPasswordToggle() {
        const toggleButtons = document.querySelectorAll('.toggle-password');
        
        toggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const input = document.getElementById(targetId);
                
                if (input.type === 'password') {
                    input.type = 'text';
                    this.querySelector('.eye-icon').textContent = '👁️‍🗨️';
                } else {
                    input.type = 'password';
                    this.querySelector('.eye-icon').textContent = '👁️';
                }
            });
        });
    }
    
    /**
     * Setup phone number formatting
     */
    function setupPhoneFormatting() {
        const phoneInputs = document.querySelectorAll('input[type="tel"]');
        
        phoneInputs.forEach(input => {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 0 && !value.startsWith('+')) {
                    value = '+' + value;
                }
                e.target.value = value;
            });
        });
    }
    
    /**
     * Navigate to next step
     */
    window.nextStep = function(stepNumber) {
        // Validate current step
        if (!validateStep(currentStep)) {
            showAlert('error', 'Please fill in all required fields correctly');
            return;
        }
        
        // Update progress
        updateStepProgress(currentStep, 'completed');
        currentStep = stepNumber;
        updateStepProgress(currentStep, 'active');
        
        // Show new step
        showStep(stepNumber);
        
        // Scroll to top
        document.querySelector('.form-panel').scrollTop = 0;
    };
    
    /**
     * Navigate to previous step
     */
    window.previousStep = function(stepNumber) {
        currentStep = stepNumber;
        updateStepProgress(currentStep, 'active');
        showStep(stepNumber);
        document.querySelector('.form-panel').scrollTop = 0;
    };
    
    /**
     * Validate all fields in a step
     */
    function validateStep(stepNumber) {
        const stepElement = document.querySelector(`.form-step[data-step="${stepNumber}"]`);
        const inputs = stepElement.querySelectorAll('input[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    /**
     * Show specific step
     */
    function showStep(stepNumber) {
        document.querySelectorAll('.form-step').forEach(step => {
            step.classList.remove('active');
        });
        
        const targetStep = document.querySelector(`.form-step[data-step="${stepNumber}"]`);
        if (targetStep) {
            targetStep.classList.add('active');
        }
    }
    
    /**
     * Update step progress indicator
     */
    function updateStepProgress(stepNumber, status) {
        const stepElement = document.querySelector(`.progress-step[data-step="${stepNumber}"]`);
        if (!stepElement) return;
        
        stepElement.classList.remove('active', 'completed');
        if (status) {
            stepElement.classList.add(status);
        }
    }
    
    /**
     * Handle form submission
     */
    async function handleSubmit(e) {
        e.preventDefault();
        
        // Validate all steps
        if (!validateStep(1) || !validateStep(2) || !validateStep(3)) {
            showAlert('error', 'Please complete all required fields');
            return;
        }
        
        // Check terms agreement
        const termsCheckbox = document.getElementById('terms');
        if (!termsCheckbox.checked) {
            showAlert('error', 'Please agree to the Terms of Service and Privacy Policy');
            return;
        }
        
        // Collect form data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Show loading state
        const submitButton = form.querySelector('.btn-submit');
        submitButton.classList.add('loading');
        submitButton.disabled = true;
        
        try {
            // const token = document.querySelector('meta[name="csrf-token"]').content;
            const response = await fetch('/api/auth/register/teacher', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // 'X-CSRFToken': token
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                showAlert('success', result.message);
                
                // Redirect after delay
                setTimeout(() => {
                    window.location.href = result.redirect_url;
                }, 1500);
            } else {
                showAlert('error', result.message || 'Registration failed. Please try again.');
                submitButton.classList.remove('loading');
                submitButton.disabled = false;
            }
        } catch (error) {
            console.error('Registration error:', error);
            showAlert('error', 'An error occurred. Please try again.');
            submitButton.classList.remove('loading');
            submitButton.disabled = false;
        }
    }
    
    /**
     * Show alert message
     */
    function showAlert(type, message) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        
        const icon = type === 'success' ? '✓' : '⚠';
        
        alert.innerHTML = `
            <span class="alert-icon">${icon}</span>
            <div class="alert-content">
                <div class="alert-title">${type === 'success' ? 'Success' : 'Error'}</div>
                <div>${message}</div>
            </div>
        `;
        
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }
    
})();