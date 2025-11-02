// Teacher Profile JavaScript
(function() {
    'use strict';

    // State management
    let teacherProfileData = null;
    let teacherProfileEditMode = false;
    let teacherProfileOriginalData = null;

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Check if we're on the profile tab
        const profileContent = document.getElementById('profile-content');
        if (profileContent && profileContent.style.display !== 'none') {
            teacherProfileLoadProfile();
        }
    });

    // Load profile data
    window.teacherProfileLoadProfile = async function() {
        const loading = document.getElementById('teacherProfileLoading');
        const error = document.getElementById('teacherProfileError');
        const content = document.getElementById('teacherProfileContent');

        // Show loading state
        loading.style.display = 'flex';
        error.style.display = 'none';
        content.style.display = 'none';

        try {
            const response = await fetch('/api/profile', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to load profile');
            }

            if (!data.success) {
                throw new Error(data.error || 'Failed to load profile');
            }

            // Store profile data
            teacherProfileData = data.data;
            
            // Populate the form
            teacherProfilePopulateForm(teacherProfileData);

            // Show content
            loading.style.display = 'none';
            content.style.display = 'block';

        } catch (err) {
            console.error('Error loading profile:', err);
            loading.style.display = 'none';
            error.style.display = 'block';
            document.getElementById('teacherProfileErrorMessage').textContent = 
                err.message || 'Failed to load profile. Please try again.';
        }
    };

    // Populate form with profile data
    function teacherProfilePopulateForm(data) {
        // Header information
        const initials = (data.first_name?.charAt(0) || '') + (data.last_name?.charAt(0) || '');
        document.getElementById('teacherProfileInitials').textContent = initials || 'T';
        document.getElementById('teacherProfileName').textContent = data.full_name || 'Teacher Name';
        document.getElementById('teacherProfileEmail').textContent = data.email || '';

        // Status badges
        const statusBadge = document.getElementById('teacherProfileStatusBadge');
        statusBadge.textContent = data.is_active ? 'Active' : 'Inactive';
        statusBadge.style.background = data.is_active ? '#4caf50' : '#f44336';

        const verifiedBadge = document.getElementById('teacherProfileVerifiedBadge');
        verifiedBadge.style.display = data.is_verified ? 'inline-flex' : 'none';

        // Statistics
        if (data.statistics) {
            document.getElementById('teacherProfileTotalTrips').textContent = 
                data.statistics.total_trips || 0;
            document.getElementById('teacherProfileTotalStudents').textContent = 
                data.statistics.total_students || 0;
        }

        // Form fields
        document.getElementById('teacherProfileFirstName').value = data.first_name || '';
        document.getElementById('teacherProfileLastName').value = data.last_name || '';
        document.getElementById('teacherProfileEmailInput').value = data.email || '';
        document.getElementById('teacherProfilePhone').value = data.phone || '';
        document.getElementById('teacherProfileDOB').value = data.date_of_birth ? 
            data.date_of_birth.split('T')[0] : '';
        document.getElementById('teacherProfileSchool').value = data.school || '';
        document.getElementById('teacherProfileEmergencyContact').value = data.emergency_contact || '';
        document.getElementById('teacherProfileEmergencyPhone').value = data.emergency_phone || '';
        document.getElementById('teacherProfileBio').value = data.bio || '';

        // Update character count
        teacherProfileUpdateCharCount();

        // Account information
        document.getElementById('teacherProfileLastLogin').textContent = 
            teacherProfileFormatDate(data.last_login);
        document.getElementById('teacherProfileCreatedAt').textContent = 
            teacherProfileFormatDate(data.created_at);
        document.getElementById('teacherProfileUpdatedAt').textContent = 
            teacherProfileFormatDate(data.updated_at);
    }

    // Format date for display
    function teacherProfileFormatDate(dateString) {
        if (!dateString) return 'Never';
        
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now - date);
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays === 0) {
                return 'Today at ' + date.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            } else if (diffDays === 1) {
                return 'Yesterday at ' + date.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            } else if (diffDays < 7) {
                return diffDays + ' days ago';
            } else {
                return date.toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric' 
                });
            }
        } catch (e) {
            return 'Invalid date';
        }
    }

    // Toggle edit mode
    window.teacherProfileToggleEditMode = function() {
        teacherProfileEditMode = !teacherProfileEditMode;
        
        // Store original data for cancel functionality
        if (teacherProfileEditMode) {
            teacherProfileOriginalData = { ...teacherProfileData };
        }

        // Toggle input states
        const inputs = [
            'teacherProfileFirstName',
            'teacherProfileLastName',
            'teacherProfileEmailInput',
            'teacherProfilePhone',
            'teacherProfileDOB',
            'teacherProfileSchool',
            'teacherProfileEmergencyContact',
            'teacherProfileEmergencyPhone',
            'teacherProfileBio'
        ];

        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.disabled = !teacherProfileEditMode;
                if (teacherProfileEditMode) {
                    input.style.background = 'white';
                } else {
                    input.style.background = '#f9f9f9';
                }
            }
        });

        // Toggle action buttons
        document.getElementById('teacherProfileActions').style.display = 
            teacherProfileEditMode ? 'flex' : 'none';

        // Update edit button
        const editBtn = document.getElementById('teacherProfileEditBtn');
        if (teacherProfileEditMode) {
            editBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                    <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
                </svg>
                Editing...
            `;
            editBtn.style.background = 'rgba(76, 175, 80, 0.2)';
            editBtn.style.borderColor = 'rgba(76, 175, 80, 0.3)';
        } else {
            editBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5L13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175l-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                </svg>
                Edit Profile
            `;
            editBtn.style.background = 'rgba(255,255,255,0.2)';
            editBtn.style.borderColor = 'rgba(255,255,255,0.3)';
        }

        // Clear any validation errors
        teacherProfileClearErrors();
    };

    // Cancel edit mode
    window.teacherProfileCancelEdit = function() {
        if (teacherProfileOriginalData) {
            teacherProfileData = { ...teacherProfileOriginalData };
            teacherProfilePopulateForm(teacherProfileData);
        }
        teacherProfileToggleEditMode();
    };

    // Update character count for bio
    function teacherProfileUpdateCharCount() {
        const bio = document.getElementById('teacherProfileBio');
        const count = document.getElementById('teacherProfileBioCharCount');
        if (bio && count) {
            count.textContent = bio.value.length;
            if (bio.value.length > 900) {
                count.style.color = '#ff9800';
            } else if (bio.value.length >= 1000) {
                count.style.color = '#f44336';
            } else {
                count.style.color = '#999';
            }
        }
    }

    // Add event listener for bio character count
    document.addEventListener('DOMContentLoaded', function() {
        const bio = document.getElementById('teacherProfileBio');
        if (bio) {
            bio.addEventListener('input', teacherProfileUpdateCharCount);
        }
    });

    // Clear validation errors
    function teacherProfileClearErrors() {
        const errorFields = [
            'teacherProfileFirstNameError',
            'teacherProfileLastNameError',
            'teacherProfileEmailInputError',
            'teacherProfilePhoneError',
            'teacherProfileDOBError',
            'teacherProfileSchoolError',
            'teacherProfileEmergencyContactError',
            'teacherProfileEmergencyPhoneError',
            'teacherProfileBioError'
        ];

        errorFields.forEach(id => {
            const errorElement = document.getElementById(id);
            if (errorElement) {
                errorElement.style.display = 'none';
                errorElement.textContent = '';
            }
        });

        // Remove error class from inputs
        const inputs = document.querySelectorAll('.teacher-profile-input, .teacher-profile-textarea');
        inputs.forEach(input => {
            input.classList.remove('teacher-profile-input-error');
        });
    }

    // Display validation errors
    function teacherProfileDisplayErrors(errors) {
        teacherProfileClearErrors();

        const errorMap = {
            'email': 'teacherProfileEmailInputError',
            'first_name': 'teacherProfileFirstNameError',
            'last_name': 'teacherProfileLastNameError',
            'phone': 'teacherProfilePhoneError',
            'date_of_birth': 'teacherProfileDOBError',
            'school': 'teacherProfileSchoolError',
            'emergency_contact': 'teacherProfileEmergencyContactError',
            'emergency_phone': 'teacherProfileEmergencyPhoneError',
            'bio': 'teacherProfileBioError'
        };

        errors.forEach(error => {
            // Try to find which field this error belongs to
            for (const [field, errorId] of Object.entries(errorMap)) {
                if (error.toLowerCase().includes(field.replace('_', ' '))) {
                    const errorElement = document.getElementById(errorId);
                    const inputId = errorId.replace('Error', '');
                    const inputElement = document.getElementById(inputId);
                    
                    if (errorElement) {
                        errorElement.textContent = error;
                        errorElement.style.display = 'block';
                    }
                    if (inputElement) {
                        inputElement.classList.add('teacher-profile-input-error');
                    }
                    return;
                }
            }
        });
    }

    // Validate form client-side
    function teacherProfileValidateForm() {
        teacherProfileClearErrors();
        const errors = [];

        // First name validation
        const firstName = document.getElementById('teacherProfileFirstName').value.trim();
        if (!firstName) {
            errors.push({ field: 'first_name', message: 'First name is required' });
        } else if (firstName.length < 2) {
            errors.push({ field: 'first_name', message: 'First name must be at least 2 characters' });
        } else if (firstName.length > 50) {
            errors.push({ field: 'first_name', message: 'First name must not exceed 50 characters' });
        }

        // Last name validation
        const lastName = document.getElementById('teacherProfileLastName').value.trim();
        if (!lastName) {
            errors.push({ field: 'last_name', message: 'Last name is required' });
        } else if (lastName.length < 2) {
            errors.push({ field: 'last_name', message: 'Last name must be at least 2 characters' });
        } else if (lastName.length > 50) {
            errors.push({ field: 'last_name', message: 'Last name must not exceed 50 characters' });
        }

        // Email validation
        const email = document.getElementById('teacherProfileEmailInput').value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) {
            errors.push({ field: 'email', message: 'Email is required' });
        } else if (!emailRegex.test(email)) {
            errors.push({ field: 'email', message: 'Invalid email format' });
        }

        // Phone validation (optional but must be valid if provided)
        const phone = document.getElementById('teacherProfilePhone').value.trim();
        if (phone) {
            const phoneRegex = /^[\d\s\+\-\(\)]+$/;
            if (!phoneRegex.test(phone) || phone.length > 20) {
                errors.push({ field: 'phone', message: 'Invalid phone number format' });
            }
        }

        // Emergency phone validation (optional but must be valid if provided)
        const emergencyPhone = document.getElementById('teacherProfileEmergencyPhone').value.trim();
        if (emergencyPhone) {
            const phoneRegex = /^[\d\s\+\-\(\)]+$/;
            if (!phoneRegex.test(emergencyPhone) || emergencyPhone.length > 20) {
                errors.push({ field: 'emergency_phone', message: 'Invalid emergency phone format' });
            }
        }

        // Display errors
        errors.forEach(error => {
            const errorId = 'teacherProfile' + error.field.split('_').map((word, index) => 
                index === 0 ? word.charAt(0).toUpperCase() + word.slice(1) : 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join('') + 'Error';
            
            const inputId = errorId.replace('Error', '');
            const errorElement = document.getElementById(errorId);
            const inputElement = document.getElementById(inputId);
            
            if (errorElement) {
                errorElement.textContent = error.message;
                errorElement.style.display = 'block';
            }
            if (inputElement) {
                inputElement.classList.add('teacher-profile-input-error');
            }
        });

        return errors.length === 0;
    }

    // Show toast notification
    function teacherProfileShowToast(message, type = 'success') {
        const toast = document.getElementById('teacherProfileToast');
        const toastMessage = document.getElementById('teacherProfileToastMessage');
        
        toastMessage.textContent = message;
        
        if (type === 'error') {
            toast.style.background = '#f44336';
        } else {
            toast.style.background = '#4caf50';
        }
        
        toast.style.display = 'flex';
        
        setTimeout(() => {
            toast.style.display = 'none';
        }, 4000);
    }

    // Handle form submission
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('teacherProfileForm');
        if (form) {
            form.addEventListener('submit', async function(e) {
                e.preventDefault();

                // Validate form
                if (!teacherProfileValidateForm()) {
                    teacherProfileShowToast('Please fix the errors in the form', 'error');
                    return;
                }

                // Prepare data
                const formData = {
                    first_name: document.getElementById('teacherProfileFirstName').value.trim(),
                    last_name: document.getElementById('teacherProfileLastName').value.trim(),
                    email: document.getElementById('teacherProfileEmailInput').value.trim(),
                    phone: document.getElementById('teacherProfilePhone').value.trim() || null,
                    date_of_birth: document.getElementById('teacherProfileDOB').value || null,
                    school: document.getElementById('teacherProfileSchool').value.trim() || null,
                    emergency_contact: document.getElementById('teacherProfileEmergencyContact').value.trim() || null,
                    emergency_phone: document.getElementById('teacherProfileEmergencyPhone').value.trim() || null,
                    bio: document.getElementById('teacherProfileBio').value.trim() || null
                };

                // Show loading state
                const saveBtn = document.getElementById('teacherProfileSaveBtn');
                const btnText = saveBtn.querySelector('.teacher-profile-btn-text');
                const btnSpinner = saveBtn.querySelector('.teacher-profile-btn-spinner');
                
                saveBtn.disabled = true;
                btnText.style.display = 'none';
                btnSpinner.style.display = 'block';

                try {
                    const response = await fetch('/api/profile/update', {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        credentials: 'same-origin',
                        body: JSON.stringify(formData)
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        if (data.validation_errors) {
                            teacherProfileDisplayErrors(data.validation_errors);
                            throw new Error('Please fix the validation errors');
                        }
                        throw new Error(data.error || 'Failed to update profile');
                    }

                    if (!data.success) {
                        if (data.validation_errors) {
                            teacherProfileDisplayErrors(data.validation_errors);
                            throw new Error('Please fix the validation errors');
                        }
                        throw new Error(data.error || 'Failed to update profile');
                    }

                    // Update stored data
                    teacherProfileData = data.data;
                    teacherProfilePopulateForm(teacherProfileData);

                    // Exit edit mode
                    teacherProfileToggleEditMode();

                    // Show success message
                    teacherProfileShowToast('Profile updated successfully!');

                } catch (err) {
                    console.error('Error updating profile:', err);
                    teacherProfileShowToast(err.message || 'Failed to update profile', 'error');
                } finally {
                    // Reset button state
                    saveBtn.disabled = false;
                    btnText.style.display = 'inline';
                    btnSpinner.style.display = 'none';
                }
            });
        }
    });

    // Load profile when tab becomes visible
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                const profileContent = document.getElementById('profile-content');
                if (profileContent && profileContent.style.display !== 'none' && !teacherProfileData) {
                    teacherProfileLoadProfile();
                }
            }
        });
    });

    document.addEventListener('DOMContentLoaded', function() {
        const profileContent = document.getElementById('profile-content');
        if (profileContent) {
            observer.observe(profileContent, { attributes: true });
        }
    });
})();