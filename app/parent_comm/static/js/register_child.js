// Global state
let currentTripData = null;
let registerChildrenData = [];
let selectedChildId = null;
let registrationResult = null;

/**
 * Open trip registration modal
 * @param {number} tripId - The trip ID
 * @param {object} tripData - Optional trip data object
 */
async function openTripRegistrationModal(tripId, tripData = null) {
    try {
        const modal = document.getElementById('tripRegistrationModal');
        
        // Reset form
        resetRegistrationForm();
        
        // Show modal with loading state
        modal.style.display = 'flex';
        showAlert('info', 'Loading trip details...');
        
        // Load trip data if not provided
        if (!tripData) {
            tripData = await fetchTripDetails(tripId);
        }
        
        currentTripData = tripData;
        
        // Populate trip information
        populateTripInfo(tripData);
        
        // Load children
        await loadRegisterChildren(tripId);
        
        // Hide loading alert
        hideAlert();
        
    } catch (error) {
        console.error('Error opening registration modal:', error);
        showAlert('error', error.message || 'Failed to load trip details. Please try again.');
    }
}

/**
 * Fetch trip details from API
 */
async function fetchTripDetails(tripId) {
    try {
        const response = await fetch(`/api/parent/trips/${tripId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to fetch trip details');
        }
        
        return result.data || result;
    } catch (error) {
        console.error('Error fetching trip details:', error);
        throw new Error('Unable to load trip details. Please check your connection.');
    }
}

/**
 * Populate trip information in the modal
 */
function populateTripInfo(trip) {
    // Title
    document.getElementById('tripTitle').textContent = trip.title || trip.name;
    
    // Price
    const price = parseFloat(trip.price_per_student || trip.price || 0);
    document.getElementById('tripPrice').textContent = formatCurrency(price);
    
    // Dates
    const startDate = formatDate(trip.start_date);
    const endDate = formatDate(trip.end_date);
    document.getElementById('tripDates').textContent = `${startDate} - ${endDate}`;
    
    // Location
    document.getElementById('tripLocation').textContent = trip.location || trip.destination || 'Not specified';
    
    // Capacity
    const availableSpots = trip.available_spots || 0;
    const totalCapacity = trip.capacity || 0;
    const registered = totalCapacity - availableSpots;
    document.getElementById('tripCapacity').textContent = 
        `${registered}/${totalCapacity} registered (${availableSpots} spots left)`;
    
    // Age restrictions
    const ageRestrictionDiv = document.getElementById('tripAgeRestriction');
    const ageTextSpan = document.getElementById('tripAgeText');
    
    if (trip.min_age || trip.max_age) {
        let ageText = 'Age requirement: ';
        if (trip.min_age && trip.max_age) {
            ageText += `${trip.min_age}-${trip.max_age} years`;
        } else if (trip.min_age) {
            ageText += `${trip.min_age}+ years`;
        } else {
            ageText += `Up to ${trip.max_age} years`;
        }
        ageTextSpan.textContent = ageText;
        ageRestrictionDiv.style.display = 'flex';
    } else {
        ageRestrictionDiv.style.display = 'none';
    }
}

/**
 * Load children and check eligibility
 */
async function loadRegisterChildren(tripId) {
    try {
        // Fetch children
        const response = await fetch('/api/parent/children', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to fetch children');
        }
        
        registerChildrenData = result.data || result.children || [];
        
        // Render children list
        renderChildrenList(tripId);
        
    } catch (error) {
        console.error('Error loading children:', error);
        showAlert('error', 'Failed to load children. Please refresh the page.');
    }
}

/**
 * Render children list with eligibility checks
 */
function renderChildrenList(tripId) {
    const childrenList = document.getElementById('childrenList');
    const noChildrenMsg = document.getElementById('noChildrenMessage');
    
    if (!registerChildrenData || registerChildrenData.length === 0) {
        childrenList.style.display = 'none';
        noChildrenMsg.style.display = 'block';
        return;
    }
    
    childrenList.style.display = 'grid';
    noChildrenMsg.style.display = 'none';
    childrenList.innerHTML = '';
    
    registerChildrenData.forEach(child => {
        const eligibility = checkChildEligibility(child, currentTripData);
        const childCard = createChildCardRegister(child, eligibility);
        childrenList.appendChild(childCard);
    });
}

/**
 * Check if child is eligible for trip
 */
function checkChildEligibility(child, trip) {
    const issues = [];
    
    // Check age restrictions
    const age = child.age || calculateAge(child.date_of_birth);
    if (trip.min_age && age < trip.min_age) {
        issues.push(`Must be at least ${trip.min_age} years old`);
    }
    if (trip.max_age && age > trip.max_age) {
        issues.push(`Must be at most ${trip.max_age} years old`);
    }
    
    // Check medical information
    if (trip.medical_info_required && !child.has_complete_medical_info) {
        issues.push('Complete medical information required');
    }
    
    // Check if already registered
    if (child.is_registered_for_trip) {
        issues.push('Already registered for this trip');
    }
    
    return {
        eligible: issues.length === 0,
        issues: issues,
        age: age
    };
}

/**
 * Create child card element
 */
function createChildCardRegister(child, eligibility) {
    const card = document.createElement('label');
    card.className = `child-card ${!eligibility.eligible ? 'disabled' : ''}`;
    
    const initials = getInitials(child.first_name, child.last_name);
    const fullName = `${child.first_name} ${child.last_name}`;
    
    let statusBadge = '';
    if (child.is_registered_for_trip) {
        statusBadge = '<span class="child-status-badge registered">Registered</span>';
    } else if (!eligibility.eligible && !child.is_registered_for_trip) {
        statusBadge = '<span class="child-status-badge incomplete">Ineligible</span>';
    }
    
    let warningHtml = '';
    if (!eligibility.eligible && eligibility.issues.length > 0) {
        warningHtml = `
            <div class="child-warning">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                ${eligibility.issues.join(', ')}
            </div>
        `;
    }
    
    card.innerHTML = `
        <input type="radio" name="child_selection" value="${child.id}" class="child-card-input" 
               ${!eligibility.eligible ? 'disabled' : ''}>
        ${statusBadge}
        <div class="child-card-content">
            <div class="child-avatar">${initials}</div>
            <div class="child-info">
                <h3 class="child-name">${fullName}</h3>
                <div class="child-details">
                    <span class="child-detail-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        ${eligibility.age} years old
                    </span>
                    ${child.grade_level ? `
                        <span class="child-detail-item">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                            </svg>
                            ${child.grade_level}
                        </span>
                    ` : ''}
                </div>
                ${warningHtml}
            </div>
        </div>
    `;
    
    if (eligibility.eligible) {
        card.addEventListener('click', () => selectChild(child.id));
    }
    
    return card;
}

/**
 * Select a child for registration
 */
function selectChild(childId) {
    selectedChildId = childId;
    
    // Update UI
    document.querySelectorAll('.child-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    const selectedCard = document.querySelector(`input[value="${childId}"]`).closest('.child-card');
    selectedCard.classList.add('selected');
    
    // Check medical info requirement
    const child = registerChildrenData.find(c => c.id === childId);
    const medicalWarning = document.getElementById('medicalWarning');
    
    if (currentTripData.medical_info_required && !child.has_complete_medical_info) {
        medicalWarning.style.display = 'flex';
    } else {
        medicalWarning.style.display = 'none';
    }
}

/**
 * Handle form submission
 */
document.getElementById('tripRegistrationForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!validateForm()) {
        return;
    }
    
    await submitRegistration();
});

/**
 * Validate registration form
 */
function validateForm() {
    // Check if child is selected
    if (!selectedChildId) {
        showAlert('error', 'Please select a child to register');
        return false;
    }
    
    // Check terms acceptance
    const termsAccepted = document.getElementById('termsAccepted').checked;
    if (!termsAccepted) {
        showAlert('error', 'Please accept the terms and conditions');
        return false;
    }
    
    return true;
}

/**
 * Submit registration to API
 */
async function submitRegistration() {
    const submitBtn = document.getElementById('submitRegistrationBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    try {
        // Show loading state
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'block';
        hideAlert();
        
        // Prepare form data
        const formData = {
            participant_id: selectedChildId,
            payment_plan: document.querySelector('input[name="payment_plan"]:checked').value,
            parent_notes: document.getElementById('parentNotes').value.trim()
        };
        
        // Submit to API
        const response = await fetch(`/api/parent/children/trips/${currentTripData.id}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            // Handle specific error codes
            if (result.code === 'ALREADY_REGISTERED') {
                throw new Error('This child is already registered for this trip');
            } else if (result.code === 'REGISTRATION_CLOSED') {
                throw new Error('Registration is no longer open for this trip');
            } else if (result.code === 'AGE_RESTRICTION') {
                throw new Error(result.error || 'This child does not meet the age requirements');
            } else if (result.code === 'INCOMPLETE_MEDICAL_INFO') {
                throw new Error('Please update the child\'s medical information before registering');
            } else {
                throw new Error(result.error || 'Registration failed. Please try again.');
            }
        }
        
        // Store result for success modal
        registrationResult = result;
        
        // Close registration modal and show success modal
        closeTripRegistrationModal();
        showSuccessModal(result);
        
    } catch (error) {
        console.error('Registration error:', error);
        showAlert('error', error.message || 'An unexpected error occurred. Please try again.');
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
    }
}

/**
 * Show success modal
 */
function showSuccessModal(result) {
    const modal = document.getElementById('registrationSuccessModal');
    const successMessage = document.getElementById('successMessage');
    const nextStepsList = document.getElementById('nextStepsList');
    
    // Get child name
    const child = registerChildrenData.find(c => c.id === selectedChildId);
    const childName = child ? `${child.first_name} ${child.last_name}` : 'your child';
    
    // Set message
    const status = result.data?.status || 'pending';
    if (status === 'waitlisted') {
        successMessage.textContent = `${childName} has been added to the waitlist for ${currentTripData.title}. You'll be notified if a spot becomes available.`;
    } else {
        successMessage.textContent = `${childName} has been successfully registered for ${currentTripData.title}!`;
    }
    
    // Build next steps
    const nextSteps = result.next_steps || {};
    nextStepsList.innerHTML = '';
    
    if (nextSteps.payment_required) {
        const li = document.createElement('li');
        li.textContent = `Complete payment of ${formatCurrency(nextSteps.amount_due)} ${nextSteps.payment_deadline ? 'by ' + formatDate(nextSteps.payment_deadline) : ''}`;
        nextStepsList.appendChild(li);
    }
    
    if (nextSteps.consent_required) {
        const li = document.createElement('li');
        li.textContent = 'Sign the consent form';
        nextStepsList.appendChild(li);
    }
    
    if (nextSteps.documents_required) {
        const li = document.createElement('li');
        li.textContent = 'Submit required documents';
        nextStepsList.appendChild(li);
    }
    
    if (nextStepsList.children.length === 0) {
        document.getElementById('nextStepsSection').style.display = 'none';
    } else {
        document.getElementById('nextStepsSection').style.display = 'block';
    }
    
    modal.style.display = 'flex';
}

/**
 * Close registration modal
 */
function closeTripRegistrationModal() {
    const modal = document.getElementById('tripRegistrationModal');
    modal.style.display = 'none';
    resetRegistrationForm();
}

/**
 * Close success modal
 */
function closeSuccessModal() {
    const modal = document.getElementById('registrationSuccessModal');
    modal.style.display = 'none';
    
    // Refresh trips list or registration list
    if (typeof refreshTripsDisplay === 'function') {
        refreshTripsDisplay();
    }
    if (typeof refreshRegistrations === 'function') {
        refreshRegistrations();
    }
}

/**
 * View registration details
 */
function viewRegistrationDetails() {
    if (registrationResult && registrationResult.data) {
        closeSuccessModal();
        // Navigate to registration details page
        window.location.href = `/parent/registrations/${registrationResult.data.id}`;
    }
}

/**
 * Reset registration form
 */
function resetRegistrationForm() {
    document.getElementById('tripRegistrationForm').reset();
    selectedChildId = null;
    currentTripData = null;
    
    // Reset child selection
    document.querySelectorAll('.child-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Reset payment plan to full
    document.querySelector('input[name="payment_plan"][value="full"]').checked = true;
    
    // Clear notes
    document.getElementById('parentNotes').value = '';
    updateCharacterCount();
    
    // Hide warnings and alerts
    document.getElementById('medicalWarning').style.display = 'none';
    hideAlert();
}

/**
 * Show alert message
 */
function showAlert(type, message) {
    const alert = document.getElementById('registrationAlert');
    const alertMessage = document.getElementById('registrationAlertMessage');
    
    alert.className = `alert ${type}`;
    alertMessage.textContent = message;
    alert.style.display = 'block';
    
    // Scroll to alert
    alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Hide alert message
 */
function hideAlert() {
    const alert = document.getElementById('registrationAlert');
    alert.style.display = 'none';
}

/**
 * Update character count for notes
 */
document.getElementById('parentNotes').addEventListener('input', updateCharacterCount);

function updateCharacterCount() {
    const textarea = document.getElementById('parentNotes');
    const counter = document.getElementById('notesCharCount');
    counter.textContent = textarea.value.length;
}

/**
 * Navigate to add child page
 */
function navigateToAddChild() {
    window.location.href = '/parent/children/add';
}

/**
 * Show terms modal (placeholder)
 */
function showTermsModal() {
    alert('Terms and conditions modal would open here');
}

/**
 * Show policies modal (placeholder)
 */
function showPoliciesModal() {
    alert('Cancellation policy modal would open here');
}

/**
 * Utility: Calculate age from date of birth
 */
function calculateAge(dateOfBirth) {
    if (!dateOfBirth) return 0;
    
    const dob = new Date(dateOfBirth);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
        age--;
    }
    
    return age;
}

/**
 * Utility: Get initials from names
 */
function getInitials(firstName, lastName) {
    const first = firstName ? firstName.charAt(0).toUpperCase() : '';
    const last = lastName ? lastName.charAt(0).toUpperCase() : '';
    return first + last;
}

/**
 * Utility: Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES'
    }).format(amount);
}

/**
 * Utility: Format date
 */
function formatDate(dateString) {
    if (!dateString) return 'Not specified';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    }).format(date);
}

/**
 * Close modal when clicking outside
 */
document.addEventListener('click', function(e) {
    const registrationModal = document.getElementById('tripRegistrationModal');
    const successModal = document.getElementById('registrationSuccessModal');
    
    if (e.target === registrationModal) {
        closeTripRegistrationModal();
    }
    
    if (e.target === successModal) {
        closeSuccessModal();
    }
});

/**
 * Close modal on escape key
 */
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const registrationModal = document.getElementById('tripRegistrationModal');
        const successModal = document.getElementById('registrationSuccessModal');
        
        if (registrationModal.style.display === 'flex') {
            closeTripRegistrationModal();
        }
        
        if (successModal.style.display === 'flex') {
            closeSuccessModal();
        }
    }
});