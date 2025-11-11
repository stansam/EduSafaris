(function() {
    'use strict';
    
    let currentStep = 1;
    let emailCheckTimeout = null;
    
    const form = document.getElementById('venVendorRegistrationForm');
    const alertContainer = document.getElementById('venAlertContainer');
    
    document.addEventListener('DOMContentLoaded', init);
    
    function init() {
        setupFormHandlers();
        setupPasswordStrength();
        setupPasswordToggle();
        setupEmailValidation();
        setupPhoneFormatting();
        setupBusinessTypeValidation();
        setupPricingValidation();
    }
    
    /**
     * Setup form event handlers
     */
    function setupFormHandlers() {
        if (!form) return;
        
        form.addEventListener('submit', handleSubmit);
        
        // Add validation on blur and input for error fields
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('ven-error')) {
                    validateField(input);
                }
            });
        });
    }
    
    /**
     * Validate individual form field
     */
    function validateField(field) {
        const value = field.value.trim();
        const name = field.name;
        let isValid = true;
        let errorMessage = '';
        
        // Check required fields
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }
        
        // Specific field validations
        if (value) {
            switch(name) {
                case 'email':
                case 'contact_email':
                    if (!isValidEmail(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid email address';
                    }
                    break;
                    
                case 'phone':
                case 'contact_phone':
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
                    const password = document.getElementById('venPassword').value;
                    if (value !== password) {
                        isValid = false;
                        errorMessage = 'Passwords do not match';
                    }
                    break;
                    
                case 'first_name':
                case 'last_name':
                case 'business_name':
                    if (value.length < 2) {
                        isValid = false;
                        errorMessage = 'Must be at least 2 characters';
                    }
                    break;
                    
                case 'description':
                    if (value.length < 20) {
                        isValid = false;
                        errorMessage = 'Description must be at least 20 characters';
                    }
                    break;
                    
                case 'website':
                    if (!isValidURL(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid URL (e.g., https://example.com)';
                    }
                    break;
                    
                case 'capacity':
                    const capacity = parseInt(value);
                    if (isNaN(capacity) || capacity < 1 || capacity > 10000) {
                        isValid = false;
                        errorMessage = 'Capacity must be between 1 and 10,000';
                    }
                    break;
                    
                case 'base_price':
                case 'price_per_person':
                    const price = parseFloat(value);
                    if (isNaN(price) || price < 0) {
                        isValid = false;
                        errorMessage = 'Price must be a positive number';
                    }
                    break;
            }
        }
        
        updateFieldStatus(field, isValid, errorMessage);
        return isValid;
    }
    
    /**
     * Update field visual status
     */
    function updateFieldStatus(field, isValid, errorMessage) {
        const errorElement = field.closest('.ven-form-group')?.querySelector('.ven-error-message');
        
        if (isValid) {
            field.classList.remove('ven-error');
            field.classList.add('ven-success');
            if (errorElement) {
                errorElement.classList.remove('ven-active');
            }
        } else {
            field.classList.remove('ven-success');
            field.classList.add('ven-error');
            if (errorElement) {
                errorElement.textContent = errorMessage;
                errorElement.classList.add('ven-active');
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
     * URL validation
     */
    function isValidURL(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
        } catch {
            return false;
        }
    }
    
    /**
     * Setup email availability checking
     */
    function setupEmailValidation() {
        const emailInput = document.getElementById('venEmail');
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
     * Check if email is already registered
     */
    async function checkEmailAvailability(email) {
        try {
            const response = await fetch('/api/auth/checks-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            const emailInput = document.getElementById('venEmail');
            
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
        const passwordInput = document.getElementById('venPassword');
        if (!passwordInput) return;
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const result = validatePassword(password);
            updatePasswordStrength(result);
            updatePasswordRequirements(result);
        });
    }
    
    /**
     * Validate password against requirements
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
     * Update password strength visual indicator
     */
    function updatePasswordStrength(result) {
        const strengthFill = document.querySelector('.ven-strength-fill');
        const strengthText = document.querySelector('.ven-strength-text');
        
        if (!strengthFill || !strengthText) return;
        
        strengthFill.className = 'ven-strength-fill ven-' + result.strength;
        strengthText.className = 'ven-strength-text ven-' + result.strength;
        
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
            const requirement = document.querySelector(`.ven-requirement[data-requirement="${key}"]`);
            if (requirement) {
                if (met) {
                    requirement.classList.add('ven-met');
                } else {
                    requirement.classList.remove('ven-met');
                }
            }
        });
    }
    
    /**
     * Setup password visibility toggle
     */
    function setupPasswordToggle() {
        const toggleButtons = document.querySelectorAll('.ven-toggle-password');
        
        toggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const input = document.getElementById(targetId);
                const icon = this.querySelector('i');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
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
                if (value.length > 0 && !e.target.value.startsWith('+')) {
                    value = '+' + value;
                }
                e.target.value = value;
            });
        });
    }
    
    /**
     * Setup business type validation
     */
    function setupBusinessTypeValidation() {
        const businessTypeSelect = document.getElementById('venBusinessType');
        if (!businessTypeSelect) return;
        
        businessTypeSelect.addEventListener('change', function() {
            validateField(this);
        });
    }
    
    /**
     * Setup pricing field validation
     */
    function setupPricingValidation() {
        const priceFields = ['venBasePrice', 'venPricePerson'];
        
        priceFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (!field) return;
            
            field.addEventListener('input', function() {
                // Allow only numbers and decimal point
                this.value = this.value.replace(/[^0-9.]/g, '');
                
                // Prevent multiple decimal points
                const parts = this.value.split('.');
                if (parts.length > 2) {
                    this.value = parts[0] + '.' + parts.slice(1).join('');
                }
                
                // Limit to 2 decimal places
                if (parts.length === 2 && parts[1].length > 2) {
                    this.value = parts[0] + '.' + parts[1].substring(0, 2);
                }
            });
        });
    }
    
    /**
     * Navigate to next step
     */
    window.venNextStep = function(stepNumber) {
        if (!validateStep(currentStep)) {
            showAlert('error', 'Please fill in all required fields correctly');
            return;
        }
        
        updateStepProgress(currentStep, 'completed');
        currentStep = stepNumber;
        updateStepProgress(currentStep, 'active');
        showStep(stepNumber);
        scrollToTop();
    };
    
    /**
     * Navigate to previous step
     */
    window.venPreviousStep = function(stepNumber) {
        updateStepProgress(currentStep, '');
        currentStep = stepNumber;
        updateStepProgress(currentStep, 'active');
        showStep(stepNumber);
        scrollToTop();
    };
    
    /**
     * Validate all fields in current step
     */
    function validateStep(stepNumber) {
        const stepElement = document.querySelector(`.ven-form-step[data-step="${stepNumber}"]`);
        const inputs = stepElement.querySelectorAll('input[required], textarea[required], select[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    /**
     * Show specific form step
     */
    function showStep(stepNumber) {
        document.querySelectorAll('.ven-form-step').forEach(step => {
            step.classList.remove('active');
        });
        
        const targetStep = document.querySelector(`.ven-form-step[data-step="${stepNumber}"]`);
        if (targetStep) {
            targetStep.classList.add('active');
        }
    }
    
    /**
     * Update progress indicator
     */
    function updateStepProgress(stepNumber, status) {
        const stepElement = document.querySelector(`.ven-progress-step[data-step="${stepNumber}"]`);
        if (!stepElement) return;
        
        stepElement.classList.remove('active', 'completed');
        if (status) {
            stepElement.classList.add(status);
        }
    }
    
    /**
     * Scroll to top of form panel
     */
    function scrollToTop() {
        const formPanel = document.querySelector('.ven-form-panel');
        if (formPanel) {
            formPanel.scrollTop = 0;
        }
    }
    
    /**
     * Handle form submission
     */
    async function handleSubmit(e) {
        e.preventDefault();
        
        // Validate all steps
        if (!validateStep(1) || !validateStep(2) || !validateStep(3) || !validateStep(4)) {
            showAlert('error', 'Please complete all required fields correctly');
            return;
        }
        
        // Check terms agreement
        const termsCheckbox = document.getElementById('venTerms');
        if (!termsCheckbox.checked) {
            showAlert('error', 'Please agree to the Terms of Service and Privacy Policy');
            return;
        }
        
        // Collect form data
        const formData = new FormData(form);
        const data = {};
        
        // Convert FormData to JSON object
        for (let [key, value] of formData.entries()) {
            if (key === 'terms') continue; // Don't send terms checkbox
            
            // Handle specializations as array
            if (key === 'specializations' && value) {
                data[key] = value.split(',').map(s => s.trim()).filter(s => s);
            }
            // Handle numeric fields
            else if (['capacity', 'base_price', 'price_per_person'].includes(key)) {
                if (value) {
                    data[key] = key === 'capacity' ? parseInt(value) : parseFloat(value);
                }
            }
            // Handle empty optional fields
            else if (value.trim()) {
                data[key] = value.trim();
            }
        }
        
        const submitButton = form.querySelector('.ven-btn-submit');
        submitButton.classList.add('ven-loading');
        submitButton.disabled = true;
        
        try {
            const response = await fetch('/api/auth/register/vendor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                showAlert('success', result.message || 'Vendor account created successfully!');
                
                // Redirect after brief delay
                setTimeout(() => {
                    window.location.href = result.redirect_url || '/vendor/dashboard';
                }, 1500);
            } else {
                showAlert('error', result.message || 'Registration failed. Please try again.');
                submitButton.classList.remove('ven-loading');
                submitButton.disabled = false;
            }
        } catch (error) {
            console.error('Registration error:', error);
            showAlert('error', 'An error occurred. Please check your connection and try again.');
            submitButton.classList.remove('ven-loading');
            submitButton.disabled = false;
        }
    }
    
    /**
     * Display alert message
     */
    function showAlert(type, message) {
        const alert = document.createElement('div');
        alert.className = `ven-alert ven-alert-${type}`;
        
        const icon = type === 'success' 
            ? '<i class="fas fa-check-circle"></i>' 
            : '<i class="fas fa-exclamation-circle"></i>';
        
        alert.innerHTML = `
            <span class="ven-alert-icon">${icon}</span>
            <div class="ven-alert-content">
                <div class="ven-alert-title">${type === 'success' ? 'Success' : 'Error'}</div>
                <div>${message}</div>
            </div>
            <button class="ven-alert-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
        
        // Scroll alert into view
        alertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
})();