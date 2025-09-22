// Profile management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // Image preview functionality
    const profilePicture = document.getElementById('profilePicture');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    
    if (profilePicture) {
        profilePicture.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Please select a valid image file (JPG, JPEG, PNG, or GIF)');
                    this.value = '';
                    imagePreview.style.display = 'none';
                    return;
                }
                
                // Validate file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert('File size must be less than 5MB');
                    this.value = '';
                    imagePreview.style.display = 'none';
                    return;
                }
                
                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.style.display = 'none';
            }
        });
    }
    
    // Password visibility toggles
    const toggleButtons = [
        { button: 'toggleCurrentPassword', field: 'currentPassword' },
        { button: 'toggleNewPassword', field: 'newPassword' },
        { button: 'toggleConfirmPassword', field: 'confirmPassword' }
    ];
    
    toggleButtons.forEach(item => {
        const button = document.getElementById(item.button);
        const field = document.getElementById(item.field);
        
        if (button && field) {
            button.addEventListener('click', function() {
                const type = field.getAttribute('type') === 'password' ? 'text' : 'password';
                field.setAttribute('type', type);
                
                const icon = this.querySelector('i');
                if (type === 'text') {
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
        }
    });
    
    // Password strength checker
    const newPasswordField = document.getElementById('newPassword');
    const strengthIndicator = document.getElementById('passwordStrength');
    const strengthText = document.getElementById('strengthText');
    const strengthBar = document.getElementById('strengthBar');
    
    if (newPasswordField && strengthIndicator) {
        newPasswordField.addEventListener('input', function() {
            const password = this.value;
            
            if (password.length === 0) {
                strengthIndicator.style.display = 'none';
                return;
            }
            
            strengthIndicator.style.display = 'block';
            const strength = calculatePasswordStrength(password);
            
            // Remove existing classes
            strengthBar.classList.remove('strength-weak', 'strength-medium', 'strength-strong');
            
            if (strength.score <= 2) {
                strengthText.textContent = 'Weak';
                strengthText.style.color = '#dc3545';
                strengthBar.classList.add('strength-weak');
                strengthBar.style.width = '25%';
            } else if (strength.score <= 3) {
                strengthText.textContent = 'Medium';
                strengthText.style.color = '#ffc107';
                strengthBar.classList.add('strength-medium');
                strengthBar.style.width = '50%';
            } else {
                strengthText.textContent = 'Strong';
                strengthText.style.color = '#28a745';
                strengthBar.classList.add('strength-strong');
                strengthBar.style.width = '100%';
            }
        });
    }
    
    // Form validation
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            if (!validateProfileForm()) {
                e.preventDefault();
                return false;
            }
            
            // Add loading state
            this.classList.add('form-submitting');
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            submitButton.disabled = true;
            
            // Reset on error (this would be called by server-side validation errors)
            setTimeout(() => {
                this.classList.remove('form-submitting');
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }, 10000); // Fallback timeout
        });
    }
    
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            if (!validatePasswordForm()) {
                e.preventDefault();
                return false;
            }
            
            // Add loading state
            this.classList.add('form-submitting');
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Changing...';
            submitButton.disabled = true;
        });
    }
    
    // Phone number formatting
    const phoneFields = document.querySelectorAll('input[name="phone"], input[name="emergency_phone"]');
    phoneFields.forEach(field => {
        field.addEventListener('input', function() {
            // Remove non-numeric characters except +, -, (, ), and spaces
            this.value = this.value.replace(/[^\d\+\-\(\)\s]/g, '');
        });
    });
});

function calculatePasswordStrength(password) {
    let score = 0;
    const checks = {
        length: password.length >= 8,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        number: /\d/.test(password),
        special: /[^A-Za-z0-9]/.test(password)
    };
    
    // Add points for each criteria met
    Object.values(checks).forEach(check => {
        if (check) score++;
    });
    
    // Bonus points for longer passwords
    if (password.length >= 12) score++;
    if (password.length >= 16) score++;
    
    return { score, checks };
}

function validateProfileForm() {
    let isValid = true;
    const errors = [];
    
    // First name validation
    const firstName = document.querySelector('input[name="first_name"]');
    if (firstName && firstName.value.trim().length < 2) {
        errors.push('First name must be at least 2 characters long');
        firstName.classList.add('is-invalid');
        isValid = false;
    } else if (firstName) {
        firstName.classList.remove('is-invalid');
    }
    
    // Last name validation
    const lastName = document.querySelector('input[name="last_name"]');
    if (lastName && lastName.value.trim().length < 2) {
        errors.push('Last name must be at least 2 characters long');
        lastName.classList.add('is-invalid');
        isValid = false;
    } else if (lastName) {
        lastName.classList.remove('is-invalid');
    }
    
    // Phone validation (if provided)
    const phone = document.querySelector('input[name="phone"]');
    if (phone && phone.value.trim() && !/^[\+]?[\d\s\-\(\)]+$/.test(phone.value)) {
        errors.push('Please enter a valid phone number');
        phone.classList.add('is-invalid');
        isValid = false;
    } else if (phone) {
        phone.classList.remove('is-invalid');
    }
    
    // Show errors if any
    if (errors.length > 0) {
        alert('Please fix the following errors:\n' + errors.join('\n'));
    }
    
    return isValid;
}

function validatePasswordForm() {
    let isValid = true;
    const errors = [];
    
    const currentPassword = document.getElementById('currentPassword');
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    
    // Current password validation
    if (!currentPassword.value.trim()) {
        errors.push('Current password is required');
        currentPassword.classList.add('is-invalid');
        isValid = false;
    } else {
        currentPassword.classList.remove('is-invalid');
    }
    
    // New password validation
    const strength = calculatePasswordStrength(newPassword.value);
    if (!newPassword.value.trim()) {
        errors.push('New password is required');
        newPassword.classList.add('is-invalid');
        isValid = false;
    } else if (!strength.checks.length || !strength.checks.lowercase || !strength.checks.uppercase || !strength.checks.number) {
        errors.push('Password must contain at least one lowercase letter, one uppercase letter, and one digit');
        newPassword.classList.add('is-invalid');
        isValid = false;
    } else {
        newPassword.classList.remove('is-invalid');
    }
    
    // Confirm password validation
    if (newPassword.value !== confirmPassword.value) {
        errors.push('Passwords do not match');
        confirmPassword.classList.add('is-invalid');
        isValid = false;
    } else {
        confirmPassword.classList.remove('is-invalid');
    }
    
    // Show errors if any
    if (errors.length > 0) {
        alert('Please fix the following errors:\n' + errors.join('\n'));
    }
    
    return isValid;
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
});