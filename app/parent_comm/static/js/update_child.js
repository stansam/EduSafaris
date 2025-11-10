// Update Child Profile Modal Script
let currentUpdateChildId = null;

// Open modal
function openUpdateChildModal(childId) {
    currentUpdateChildId = childId;
    const modal = document.getElementById('updateChildModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    loadChildForUpdate(childId);
}

// Close modal
function closeUpdateChildModal() {
    const modal = document.getElementById('updateChildModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    currentUpdateChildId = null;
    resetUpdateChildForm();
}

// Load child data for update
async function loadChildForUpdate(childId) {
    const loadingState = document.getElementById('updateChildLoading');
    const content = document.getElementById('updateChildContent');
    
    loadingState.style.display = 'block';
    content.style.display = 'none';
    
    try {
        const response = await fetch(`/api/parent/children/${childId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.child) {
            populateUpdateForm(data.child);
            loadingState.style.display = 'none';
            content.style.display = 'block';
        } else {
            throw new Error(data.error || 'Failed to load child data');
        }
        
    } catch (error) {
        console.error('Error loading child data:', error);
        showNotification('Failed to load child data', 'error');
        closeUpdateChildModal();
    }
}

// Populate form with child data
function populateUpdateForm(child) {
    document.getElementById('updateChildId').value = child.id;
    document.getElementById('updateFirstName').value = child.first_name || '';
    document.getElementById('updateLastName').value = child.last_name || '';
    document.getElementById('updateDateOfBirth').value = child.date_of_birth || '';
    document.getElementById('updateGradeLevel').value = child.grade_level || '';
    document.getElementById('updateStudentId').value = child.student_id || '';
    document.getElementById('updateEmail').value = child.email || '';
    document.getElementById('updatePhone').value = child.phone || '';
    
    // Emergency contacts
    document.getElementById('updateEmergencyContact1Name').value = child.emergency_contact_1_name || '';
    document.getElementById('updateEmergencyContact1Phone').value = child.emergency_contact_1_phone || '';
    document.getElementById('updateEmergencyContact1Relationship').value = child.emergency_contact_1_relationship || '';
    document.getElementById('updateEmergencyContact2Name').value = child.emergency_contact_2_name || '';
    document.getElementById('updateEmergencyContact2Phone').value = child.emergency_contact_2_phone || '';
    document.getElementById('updateEmergencyContact2Relationship').value = child.emergency_contact_2_relationship || '';
    
    // Medical information
    document.getElementById('updateMedicalConditions').value = child.medical_conditions || '';
    document.getElementById('updateMedications').value = child.medications || '';
    document.getElementById('updateAllergies').value = child.allergies || '';
    document.getElementById('updateDietaryRestrictions').value = child.dietary_restrictions || '';
    document.getElementById('updateEmergencyMedicalInfo').value = child.emergency_medical_info || '';
    
    // Special requirements
    document.getElementById('updateSpecialRequirements').value = child.special_requirements || '';
}

// Reset form
function resetUpdateChildForm() {
    const form = document.getElementById('updateChildForm');
    form.reset();
    clearAllErrors('update');
}

// Validate update form
function validateUpdateChildForm(formData) {
    const errors = [];
    
    // Name validation
    if (!formData.first_name || formData.first_name.trim().length < 2) {
        showValidationError('updateFirstName', 'First name must be at least 2 characters');
        errors.push('Invalid first name');
    }
    
    if (!formData.last_name || formData.last_name.trim().length < 2) {
        showValidationError('updateLastName', 'Last name must be at least 2 characters');
        errors.push('Invalid last name');
    }
    
    // Email validation
    if (formData.email && formData.email.trim()) {
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(formData.email)) {
            showValidationError('updateEmail', 'Please enter a valid email address');
            errors.push('Invalid email');
        }
    }
    
    // Phone validation
    if (formData.phone && formData.phone.trim()) {
        const phonePattern = /^[\d\s\-\+\(\)]{10,}$/;
        if (!phonePattern.test(formData.phone)) {
            showValidationError('updatePhone', 'Please enter a valid phone number');
            errors.push('Invalid phone');
        }
    }
    
    // Date of birth validation
    if (formData.date_of_birth) {
        const dob = new Date(formData.date_of_birth);
        const today = new Date();
        if (dob > today) {
            showValidationError('updateDateOfBirth', 'Date of birth cannot be in the future');
            errors.push('Invalid date of birth');
        }
    }
    
    return errors;
}

// Handle form submission
document.getElementById('updateChildForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Clear previous errors
    clearAllErrors('update');
    
    const childId = document.getElementById('updateChildId').value;
    
    // Get form data
    const formData = {
        first_name: document.getElementById('updateFirstName').value.trim(),
        last_name: document.getElementById('updateLastName').value.trim(),
        date_of_birth: document.getElementById('updateDateOfBirth').value,
        grade_level: document.getElementById('updateGradeLevel').value.trim(),
        student_id: document.getElementById('updateStudentId').value.trim(),
        email: document.getElementById('updateEmail').value.trim(),
        phone: document.getElementById('updatePhone').value.trim(),
        emergency_contact_1_name: document.getElementById('updateEmergencyContact1Name').value.trim(),
        emergency_contact_1_phone: document.getElementById('updateEmergencyContact1Phone').value.trim(),
        emergency_contact_1_relationship: document.getElementById('updateEmergencyContact1Relationship').value.trim(),
        emergency_contact_2_name: document.getElementById('updateEmergencyContact2Name').value.trim(),
        emergency_contact_2_phone: document.getElementById('updateEmergencyContact2Phone').value.trim(),
        emergency_contact_2_relationship: document.getElementById('updateEmergencyContact2Relationship').value.trim(),
        medical_conditions: document.getElementById('updateMedicalConditions').value.trim(),
        medications: document.getElementById('updateMedications').value.trim(),
        allergies: document.getElementById('updateAllergies').value.trim(),
        dietary_restrictions: document.getElementById('updateDietaryRestrictions').value.trim(),
        emergency_medical_info: document.getElementById('updateEmergencyMedicalInfo').value.trim(),
        special_requirements: document.getElementById('updateSpecialRequirements').value.trim()
    };
    
    // Validate form
    const validationErrors = validateUpdateChildForm(formData);
    if (validationErrors.length > 0) {
        showNotification('Please correct the errors in the form', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('updateChildSubmitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/parent/children/${childId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                // 'Authorization': `Bearer ${getAuthToken()}`
            },
            credentials: 'include',
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showNotification('Profile updated successfully!', 'success');
            closeUpdateChildModal();
            refreshChildren();
        } else {
            if (data.validation_errors && Array.isArray(data.validation_errors)) {
                data.validation_errors.forEach(error => {
                    showNotification(error, 'error');
                });
            } else {
                showNotification(data.error || 'Failed to update profile', 'error');
            }
        }
        
    } catch (error) {
        console.error('Error updating child profile:', error);
        showNotification('Network error. Please check your connection and try again.', 'error');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

// Close modal when clicking outside
document.getElementById('updateChildModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeUpdateChildModal();
    }
});