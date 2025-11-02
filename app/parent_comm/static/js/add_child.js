// Add Child Modal Script

// Open modal
function openAddChildModal() {
    const modal = document.getElementById('addChildModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    loadAvailableTrips();
    resetAddChildForm();
}

// Close modal
function closeAddChildModal() {
    const modal = document.getElementById('addChildModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    resetAddChildForm();
}

// Load available trips
async function loadAvailableTrips() {
    const tripSelect = document.getElementById('addTripSelect');
    tripSelect.innerHTML = '<option value="">Loading trips...</option>';
    
    try {
        const response = await fetch('/api/parent/trips?status=active', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load trips');
        }
        
        const data = await response.json();
        
        tripSelect.innerHTML = '<option value="">Choose a trip...</option>';
        
        if (data.success && data.trips && data.trips.length > 0) {
            data.trips.forEach(trip => {
                const option = document.createElement('option');
                option.value = trip.id;
                option.textContent = `${trip.title} - ${formatDate(trip.start_date)} to ${formatDate(trip.end_date)}`;
                option.dataset.price = trip.price_per_student || 0;
                tripSelect.appendChild(option);
            });
        } else {
            tripSelect.innerHTML = '<option value="">No active trips available</option>';
        }
        
    } catch (error) {
        console.error('Error loading trips:', error);
        tripSelect.innerHTML = '<option value="">Error loading trips</option>';
        showNotification('Failed to load available trips', 'error');
    }
}

// Reset form
function resetAddChildForm() {
    const form = document.getElementById('addChildForm');
    form.reset();
    clearAllErrors('add');
}

// Clear all validation errors
function clearAllErrors(prefix) {
    const errorElements = document.querySelectorAll(`[id^="${prefix}"][id$="Error"]`);
    errorElements.forEach(element => {
        element.textContent = '';
    });
    
    const inputElements = document.querySelectorAll('.form-child-input, .form-child-textarea, .form-child-select');
    inputElements.forEach(element => {
        element.classList.remove('error');
    });
}

// Show validation error
function showValidationError(fieldId, message) {
    const errorElement = document.getElementById(`${fieldId}Error`);
    const inputElement = document.getElementById(fieldId);
    
    if (errorElement) {
        errorElement.textContent = message;
    }
    if (inputElement) {
        inputElement.classList.add('error');
    }
}

// Validate form
function validateAddChildForm(formData) {
    const errors = [];
    
    // Trip validation
    if (!formData.trip_id) {
        showValidationError('addTripSelect', 'Please select a trip');
        errors.push('Trip is required');
    }
    
    // Name validation
    if (!formData.first_name || formData.first_name.trim().length < 2) {
        showValidationError('addFirstName', 'First name must be at least 2 characters');
        errors.push('Invalid first name');
    }
    
    if (!formData.last_name || formData.last_name.trim().length < 2) {
        showValidationError('addLastName', 'Last name must be at least 2 characters');
        errors.push('Invalid last name');
    }
    
    // Email validation
    if (formData.email && formData.email.trim()) {
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(formData.email)) {
            showValidationError('addEmail', 'Please enter a valid email address');
            errors.push('Invalid email');
        }
    }
    
    // Phone validation
    if (formData.phone && formData.phone.trim()) {
        const phonePattern = /^[\d\s\-\+\(\)]{10,}$/;
        if (!phonePattern.test(formData.phone)) {
            showValidationError('addPhone', 'Please enter a valid phone number');
            errors.push('Invalid phone');
        }
    }
    
    // Date of birth validation
    if (formData.date_of_birth) {
        const dob = new Date(formData.date_of_birth);
        const today = new Date();
        if (dob > today) {
            showValidationError('addDateOfBirth', 'Date of birth cannot be in the future');
            errors.push('Invalid date of birth');
        }
    }
    
    return errors;
}

// Handle form submission
document.getElementById('addChildForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Clear previous errors
    clearAllErrors('add');
    
    // Get form data
    const formData = {
        trip_id: document.getElementById('addTripSelect').value,
        first_name: document.getElementById('addFirstName').value.trim(),
        last_name: document.getElementById('addLastName').value.trim(),
        date_of_birth: document.getElementById('addDateOfBirth').value,
        grade_level: document.getElementById('addGradeLevel').value.trim(),
        student_id: document.getElementById('addStudentId').value.trim(),
        email: document.getElementById('addEmail').value.trim(),
        phone: document.getElementById('addPhone').value.trim(),
        special_requirements: document.getElementById('addSpecialRequirements').value.trim()
    };
    
    // Validate form
    const validationErrors = validateAddChildForm(formData);
    if (validationErrors.length > 0) {
        showNotification('Please correct the errors in the form', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('addChildSubmitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/parent/children', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showNotification(`${formData.first_name} ${formData.last_name} registered successfully!`, 'success');
            closeAddChildModal();
            refreshChildren();
        } else {
            // Handle validation errors from server
            if (data.validation_errors && Array.isArray(data.validation_errors)) {
                data.validation_errors.forEach(error => {
                    showNotification(error, 'error');
                });
            } else {
                showNotification(data.error || 'Failed to register child', 'error');
            }
        }
        
    } catch (error) {
        console.error('Error registering child:', error);
        showNotification('Network error. Please check your connection and try again.', 'error');
    } finally {
        // Reset button state
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

// Close modal when clicking outside
document.getElementById('addChildModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeAddChildModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('addChildModal');
        if (modal.style.display === 'flex') {
            closeAddChildModal();
        }
    }
});