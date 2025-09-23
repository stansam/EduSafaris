// Auth JavaScript utilities and client-side validation

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all auth functionality
    initPasswordToggle();
    initFormValidation();
    initPasswordStrengthChecker();
});


/**
 * Toggle password visibility
 */
function initPasswordToggle() {
    // Handle main password field
    const togglePassword = document.getElementById('togglePassword');
    const passwordField = document.getElementById('password');
    const eyeIcon = document.getElementById('eyeIcon');
    
    if (togglePassword && passwordField) {
        togglePassword.addEventListener('click', function() {
            const type = passwordField.type === 'password' ? 'text' : 'password';
            passwordField.type = type;
            
            if (eyeIcon) {
                eyeIcon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
            }
        });
    }
    
    // Handle confirm password field
    const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');
    const confirmPasswordField = document.getElementById('confirmPassword');
    const eyeIconConfirm = document.getElementById('eyeIconConfirm');
    
    if (toggleConfirmPassword && confirmPasswordField) {
        toggleConfirmPassword.addEventListener('click', function() {
            const type = confirmPasswordField.type === 'password' ? 'text' : 'password';
            confirmPasswordField.type = type;
            
            if (eyeIconConfirm) {
                eyeIconConfirm.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
            }
        });
    }
}

/**
 * Password strength checker
 */
function initPasswordStrengthChecker() {
    // Check if password strength elements exist
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('strengthBar');
    const strengthLevel = document.getElementById('strengthLevel');
    const strengthText = document.getElementById('strengthText');
    
    if (passwordInput && strengthBar && strengthLevel) {
        // Initialize password strength with custom configuration
        const passwordStrengthAPI = initPasswordStrength('password', {
            minLength: 8,
            showDetails: true,
            customMessages: {
                weak: 'Weak',
                fair: 'Fair', 
                good: 'Good',
                strong: 'Strong',
                veryStrong: 'Very Strong'
            }
        });
        
        // Store the API for later use
        window.passwordStrengthAPI = passwordStrengthAPI;
        
        // Listen for password strength changes to integrate with form validation
        passwordInput.addEventListener('passwordStrengthChanged', function(event) {
            const { score, level, percentage } = event.detail;
            
            // Add visual feedback to the password field based on strength
            if (percentage >= 60) {
                passwordInput.classList.remove('is-invalid');
                passwordInput.classList.add('is-valid');
            } else if (passwordInput.value.length > 0) {
                passwordInput.classList.remove('is-valid');
                // Don't add is-invalid here as it might conflict with other validation
            }
        });
    }
}

function checkPasswordStrength(password) {
    // Use the password strength API if available
    if (window.passwordStrengthAPI) {
        return window.passwordStrengthAPI.checkPassword(password);
    }
    
    // Fallback basic strength check
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[a-z]/.test(password)) strength += 15;
    if (/[A-Z]/.test(password)) strength += 15;
    if (/\d/.test(password)) strength += 15;
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(password)) strength += 30;
    
    let level = 'Weak';
    if (strength >= 80) level = 'Very Strong';
    else if (strength >= 60) level = 'Strong';
    else if (strength >= 40) level = 'Good';
    else if (strength >= 20) level = 'Fair';
    
    return { score: strength, level, percentage: Math.min(strength, 100) };
}


/**
 * Enhanced form validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add validation on submit
        form.addEventListener('submit', function(e) {
            if (!validateFormInputs(form)) {
                e.preventDefault();
                showValidationErrors(form);
            }
        });
        
        // Real-time validation for specific fields
        const emailFields = form.querySelectorAll('input[id="email"]');
        emailFields.forEach(field => {
            field.addEventListener('blur', () => validateEmail(field));
        });
        
        const passwordFields = form.querySelectorAll('input[id="password"]');
        passwordFields.forEach(field => {
            field.addEventListener('input', () => {
                if (field.id === 'password') {
                    checkPasswordStrength(field.value);
                }
                validatePassword(field);
            });
        });
    });
}

/**
 * Validate individual email field
 */
function validateEmail(field) {
    const email = field.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        showFieldError(field, 'Please enter a valid email address');
        return false;
    } else {
        clearFieldError(field);
        return true;
    }
}

/**
 * Validate individual password field
 */
function validatePassword(field) {
    const password = field.value;
    const minLength = 8;
    
    if (password && password.length < minLength) {
        showFieldError(field, `Password must be at least ${minLength} characters long`);
        return false;
    }
    
    // Check password strength if API is available
    if (password && window.passwordStrengthAPI) {
        const strength = window.passwordStrengthAPI.checkPassword(password);
        
        // Require at least "Fair" strength for form submission
        if (strength.percentage < 40) {
            showFieldError(field, 'Password is too weak. Please make it stronger.');
            return false;
        }
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate entire form
 */
function validateFormInputs(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            // Field-specific validation
            if (field.type === 'email' && !validateEmail(field)) {
                isValid = false;
            } else if (field.type === 'password' && !validatePassword(field)) {
                isValid = false;
            } else {
                clearFieldError(field);
            }
        }
    });
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
    // Find or create error message element
    let errorElement = field.parentNode.querySelector('.invalid-feedback');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback';
        
        // Insert after the field or input group
        const inputGroup = field.closest('.input-group');
        if (inputGroup) {
            inputGroup.parentNode.insertBefore(errorElement, inputGroup.nextSibling);
        } else {
            field.parentNode.insertBefore(errorElement, field.nextSibling);
        }
    }
    
    errorElement.textContent = message;
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorElement = field.parentNode.querySelector('.invalid-feedback');
    if (errorElement && !field.classList.contains('is-invalid')) {
        errorElement.textContent = '';
    }
}

/**
 * Show validation errors summary
 */
function showValidationErrors(form) {
    const invalidFields = form.querySelectorAll('.is-invalid');
    if (invalidFields.length > 0) {
        // Focus on first invalid field
        invalidFields[0].focus();
        
        // Optionally show a toast or alert
        console.warn(`Please correct ${invalidFields.length} error(s) in the form`);
    }
}

/**
 * Utility function to show loading state on buttons
 */
function setButtonLoading(button, isLoading = true, loadingText = 'Loading...') {
    if (isLoading) {
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> ${loadingText}`;
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        button.disabled = false;
    }
}

/**
 * Auto-hide alerts after a delay
 */
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000); // Hide after 5 seconds
    });
});

/**
 * AJAX helper for API calls
 */
function makeAPICall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    return fetch(url, options)
        .then(response => response.json())
        .catch(error => {
            console.error('API call failed:', error);
            throw error;
        });
}

// Export functions for use in other scripts
window.AuthUtils = {
    checkPasswordStrength,
    validateEmail,
    validatePassword,
    setButtonLoading,
    makeAPICall
};