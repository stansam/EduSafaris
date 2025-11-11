/**
 * Teacher Registration Form Handler - Updated for EduSafaris
 */

(function() {
    'use strict';
    
    let currentStep = 1;
    let emailCheckTimeout = null;
    let schoolSearchTimeout = null;
    
    const form = document.getElementById('eduTeacherRegistrationForm');
    const alertContainer = document.getElementById('eduAlertContainer');
    
    document.addEventListener('DOMContentLoaded', init);
    
    function init() {
        setupFormHandlers();
        setupPasswordStrength();
        setupPasswordToggle();
        setupEmailValidation();
        setupPhoneFormatting();
        setupSchoolSearch();
    }
    
    function setupFormHandlers() {
        if (!form) return;
        
        form.addEventListener('submit', handleSubmit);
        
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('edu-error')) {
                    validateField(input);
                }
            });
        });
    }
    
    function validateField(field) {
        const value = field.value.trim();
        const name = field.name;
        let isValid = true;
        let errorMessage = '';
        
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }
        
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
                    const password = document.getElementById('eduPassword').value;
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
                    
                case 'years_of_experience':
                    const exp = parseInt(value);
                    if (isNaN(exp) || exp < 0 || exp > 60) {
                        isValid = false;
                        errorMessage = 'Years of experience must be between 0 and 60';
                    }
                    break;
            }
        }
        
        updateFieldStatus(field, isValid, errorMessage);
        return isValid;
    }
    
    function updateFieldStatus(field, isValid, errorMessage) {
        const errorElement = field.closest('.edu-form-group')?.querySelector('.edu-error-message');
        
        if (isValid) {
            field.classList.remove('edu-error');
            field.classList.add('edu-success');
            if (errorElement) {
                errorElement.classList.remove('edu-active');
            }
        } else {
            field.classList.remove('edu-success');
            field.classList.add('edu-error');
            if (errorElement) {
                errorElement.textContent = errorMessage;
                errorElement.classList.add('edu-active');
            }
        }
    }
    
    function isValidEmail(email) {
        const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return re.test(email);
    }
    
    function isValidPhone(phone) {
        const cleaned = phone.replace(/[\s\-\(\)]/g, '');
        return /^\+?\d{10,15}$/.test(cleaned);
    }
    
    function setupEmailValidation() {
        const emailInput = document.getElementById('eduEmail');
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
            const emailInput = document.getElementById('eduEmail');
            
            if (!data.available) {
                updateFieldStatus(emailInput, false, 'This email is already registered');
            }
        } catch (error) {
            console.error('Email check failed:', error);
        }
    }
    
    function setupSchoolSearch() {
        const searchInput = document.getElementById('eduSchoolSearch');
        const resultsDiv = document.getElementById('eduSchoolResults');
        const hiddenInput = document.getElementById('eduSchoolId');
        
        if (!searchInput || !resultsDiv) return;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(schoolSearchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                resultsDiv.style.display = 'none';
                resultsDiv.innerHTML = '';
                hiddenInput.value = '';
                return;
            }
            
            schoolSearchTimeout = setTimeout(() => {
                searchSchools(query);
            }, 300);
        });
        
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.edu-school-search-wrapper')) {
                resultsDiv.style.display = 'none';
            }
        });
    }
    
    async function searchSchools(query) {
        const resultsDiv = document.getElementById('eduSchoolResults');
        
        try {
            const response = await fetch(`/api/auth/schools/search?q=${encodeURIComponent(query)}&limit=10`);
            const data = await response.json();
            
            if (data.success && data.schools.length > 0) {
                resultsDiv.innerHTML = data.schools.map(school => `
                    <div class="edu-school-result-item" data-school-id="${school.id}">
                        <div class="edu-school-name">
                            ${school.name}
                            ${school.is_verified ? '<i class="fas fa-check-circle edu-verified-icon"></i>' : ''}
                        </div>
                        <div class="edu-school-location">${school.city || ''}, ${school.country || ''}</div>
                    </div>
                `).join('');
                
                resultsDiv.style.display = 'block';
                
                resultsDiv.querySelectorAll('.edu-school-result-item').forEach(item => {
                    item.addEventListener('click', function() {
                        const schoolId = this.getAttribute('data-school-id');
                        const schoolName = this.querySelector('.edu-school-name').textContent.trim();
                        
                        document.getElementById('eduSchoolId').value = schoolId;
                        document.getElementById('eduSchoolSearch').value = schoolName;
                        resultsDiv.style.display = 'none';
                    });
                });
            } else {
                resultsDiv.innerHTML = '<div class="edu-no-results">No schools found</div>';
                resultsDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('School search failed:', error);
            resultsDiv.style.display = 'none';
        }
    }
    
    function setupPasswordStrength() {
        const passwordInput = document.getElementById('eduPassword');
        if (!passwordInput) return;
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const result = validatePassword(password);
            updatePasswordStrength(result);
            updatePasswordRequirements(result);
        });
    }
    
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
    
    function updatePasswordStrength(result) {
        const strengthFill = document.querySelector('.edu-strength-fill');
        const strengthText = document.querySelector('.edu-strength-text');
        
        if (!strengthFill || !strengthText) return;
        
        strengthFill.className = 'edu-strength-fill edu-' + result.strength;
        strengthText.className = 'edu-strength-text edu-' + result.strength;
        
        const strengthLabels = {
            weak: 'Weak',
            medium: 'Medium',
            strong: 'Strong'
        };
        
        strengthText.textContent = strengthLabels[result.strength];
    }
    
    function updatePasswordRequirements(result) {
        Object.entries(result.requirements).forEach(([key, met]) => {
            const requirement = document.querySelector(`.edu-requirement[data-requirement="${key}"]`);
            if (requirement) {
                if (met) {
                    requirement.classList.add('edu-met');
                } else {
                    requirement.classList.remove('edu-met');
                }
            }
        });
    }
    
    function setupPasswordToggle() {
        const toggleButtons = document.querySelectorAll('.edu-toggle-password');
        
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
    
    window.eduNextStep = function(stepNumber) {
        if (!validateStep(currentStep)) {
            showAlert('error', 'Please fill in all required fields correctly');
            return;
        }
        
        updateStepProgress(currentStep, 'completed');
        currentStep = stepNumber;
        updateStepProgress(currentStep, 'active');
        showStep(stepNumber);
        document.querySelector('.edu-form-panel').scrollTop = 0;
    };
    
    window.eduPreviousStep = function(stepNumber) {
        updateStepProgress(currentStep, '');
        currentStep = stepNumber;
        updateStepProgress(currentStep, 'active');
        showStep(stepNumber);
        document.querySelector('.edu-form-panel').scrollTop = 0;
    };
    
    function validateStep(stepNumber) {
        const stepElement = document.querySelector(`.edu-form-step[data-step="${stepNumber}"]`);
        const inputs = stepElement.querySelectorAll('input[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    function showStep(stepNumber) {
        document.querySelectorAll('.edu-form-step').forEach(step => {
            step.classList.remove('active');
        });
        
        const targetStep = document.querySelector(`.edu-form-step[data-step="${stepNumber}"]`);
        if (targetStep) {
            targetStep.classList.add('active');
        }
    }
    
    function updateStepProgress(stepNumber, status) {
        const stepElement = document.querySelector(`.edu-progress-step[data-step="${stepNumber}"]`);
        if (!stepElement) return;
        
        stepElement.classList.remove('active', 'completed');
        if (status) {
            stepElement.classList.add(status);
        }
    }
    
    async function handleSubmit(e) {
        e.preventDefault();
        
        if (!validateStep(1) || !validateStep(2) || !validateStep(3)) {
            showAlert('error', 'Please complete all required fields');
            return;
        }
        
        const termsCheckbox = document.getElementById('eduTerms');
        if (!termsCheckbox.checked) {
            showAlert('error', 'Please agree to the Terms of Service and Privacy Policy');
            return;
        }
        
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        const submitButton = form.querySelector('.edu-btn-submit');
        submitButton.classList.add('edu-loading');
        submitButton.disabled = true;
        
        try {
            const response = await fetch('/api/auth/register/teacher', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                showAlert('success', result.message);
                
                setTimeout(() => {
                    window.location.href = result.redirect_url;
                }, 1500);
            } else {
                showAlert('error', result.message || 'Registration failed. Please try again.');
                submitButton.classList.remove('edu-loading');
                submitButton.disabled = false;
            }
        } catch (error) {
            console.error('Registration error:', error);
            showAlert('error', 'An error occurred. Please try again.');
            submitButton.classList.remove('edu-loading');
            submitButton.disabled = false;
        }
    }
    
    function showAlert(type, message) {
        const alert = document.createElement('div');
        alert.className = `edu-alert edu-alert-${type}`;
        
        const icon = type === 'success' ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-circle"></i>';
        
        alert.innerHTML = `
            <span class="edu-alert-icon">${icon}</span>
            <div class="edu-alert-content">
                <div class="edu-alert-title">${type === 'success' ? 'Success' : 'Error'}</div>
                <div>${message}</div>
            </div>
            <button class="edu-alert-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }
})();