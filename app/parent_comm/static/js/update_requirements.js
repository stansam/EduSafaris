// Update Requirements Modal Module
const UpdateRequirementsModal = (function() {
    'use strict';

    // State
    const state = {
        currentTripId: null,
        currentParticipantId: null,
        participantData: null,
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
        
        // Content sections
        loading: null,
        content: null,
        error: null,
        errorMessage: null,
        retryBtn: null,
        footer: null,
        
        // Participant info
        childName: null,
        tripTitle: null,
        
        // Form fields
        medicalConditions: null,
        medications: null,
        allergies: null,
        emergencyMedical: null,
        dietaryRestrictions: null,
        specialRequirements: null
    };

    // Initialize
    function init() {
        try {
            cacheDOM();
            bindEvents();
        } catch (error) {
            console.error('Failed to initialize UpdateRequirementsModal:', error);
        }
    }

    // Cache DOM Elements
    function cacheDOM() {
        elements.overlay = document.getElementById('updateRequirementsModalOverlay');
        elements.close = document.getElementById('updateRequirementsModalClose');
        elements.cancelBtn = document.getElementById('updateRequirementsCancelBtn');
        elements.form = document.getElementById('updateRequirementsForm');
        elements.submitBtn = document.getElementById('updateRequirementsSubmitBtn');
        elements.alert = document.getElementById('updateRequirementsAlert');
        elements.alertMessage = document.getElementById('updateRequirementsAlertMessage');
        
        elements.loading = document.getElementById('updateRequirementsLoading');
        elements.content = document.getElementById('updateRequirementsContent');
        elements.error = document.getElementById('updateRequirementsError');
        elements.errorMessage = document.getElementById('updateRequirementsErrorMessage');
        elements.retryBtn = document.getElementById('updateRequirementsRetryBtn');
        elements.footer = document.getElementById('updateRequirementsModalFooter');
        
        elements.childName = document.getElementById('updateRequirementsChildName');
        elements.tripTitle = document.getElementById('updateRequirementsTripTitle');
        
        elements.medicalConditions = document.getElementById('updateRequirementsMedicalConditions');
        elements.medications = document.getElementById('updateRequirementsMedications');
        elements.allergies = document.getElementById('updateRequirementsAllergies');
        elements.emergencyMedical = document.getElementById('updateRequirementsEmergencyMedical');
        elements.dietaryRestrictions = document.getElementById('updateRequirementsDietaryRestrictions');
        elements.specialRequirements = document.getElementById('updateRequirementsSpecialRequirements');
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
        
        // Retry button
        if (elements.retryBtn) {
            elements.retryBtn.addEventListener('click', () => {
                if (state.currentTripId && state.currentParticipantId) {
                    loadParticipantData(state.currentTripId, state.currentParticipantId);
                }
            });
        }
        
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && elements.overlay && elements.overlay.classList.contains('active')) {
                close();
            }
        });
    }

    // Open Modal
    function open(tripId, registrationId) {
        if (!tripId || !registrationId) {
            console.error('Trip ID and Registration ID are required');
            return;
        }
        
        state.currentTripId = tripId;
        state.currentParticipantId = registrationId;
        
        if (elements.overlay) {
            elements.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
        
        resetForm();
        loadParticipantData(tripId, registrationId);
    }

    // Close Modal
    function close() {
        if (elements.overlay) {
            elements.overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        state.currentTripId = null;
        state.currentParticipantId = null;
        state.participantData = null;
        resetForm();
    }

    // Load Participant Data
    async function loadParticipantData(tripId, upRegistrationId) {
        showLoading();
        
        try {
            // Get trip details which includes participant info
            const tripResponse = await fetch(`/api/parent/trips/${tripId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!tripResponse.ok) {
                throw new Error('Failed to load participant details');
            }
            console.log('Trip response status:', upRegistrationId);
            const tripResult = await tripResponse.json();
            
            if (!tripResult.success || !tripResult.data) {
                throw new Error('Invalid participant data');
            }

            // Find participant in trip data
            // const participant = tripResult.data.user_participants?.find(
            //     p => p.id === participantId
            // );
            console.log(tripResult.data.user_registrations.map(r => r.participant.id));

            const registration = tripResult.data.user_registrations?.find(
                r => r.participant && r.participant.id === Number(upRegistrationId)
            );

            if (!registration) {
                throw new Error('Participant not found');
            }

            // Re-map data to match expected structure downstream
            const participant = registration.participant;
            state.participantData = {
                trip: tripResult.data,
                participant,
                registration
            };

            // if (!participant) {
            //     throw new Error('Participant not found');
            // }

            // state.participantData = {
            //     trip: tripResult.data,
            //     participant: participant
            // };

            displayParticipantData();
            populateForm();
        } catch (error) {
            console.error('Error loading participant data:', error);
            showError(error.message);
        }
    }

    // Display Participant Data
    function displayParticipantData() {
        // const { trip, participant } = state.participantData;
        const { trip, participant, registration } = state.participantData;
        
        if (elements.childName) {
            const fullName = `${participant.first_name || ''} ${participant.last_name || ''}`.trim();
            elements.childName.textContent = fullName || 'Child';
        }
        
        if (elements.tripTitle) {
            elements.tripTitle.textContent = trip.title || 'Trip';
        }

        if (registration && elements.registrationNumber) {
            elements.registrationNumber.textContent = registration.registration_number || '';
        }
        
        showContent();
    }

    // Populate Form
    function populateForm() {
        const { participant } = state.participantData || {};

        if (!participant) return;
        
        if (elements.medicalConditions) {
            elements.medicalConditions.value = participant.medical_conditions || '';
        }
        
        if (elements.medications) {
            elements.medications.value = participant.medications || '';
        }
        
        if (elements.allergies) {
            elements.allergies.value = participant.allergies || '';
        }
        
        if (elements.emergencyMedical) {
            elements.emergencyMedical.value = participant.emergency_medical_info || '';
        }
        
        if (elements.dietaryRestrictions) {
            elements.dietaryRestrictions.value = participant.dietary_restrictions || '';
        }
        
        if (elements.specialRequirements) {
            elements.specialRequirements.value = participant.special_requirements || '';
        }
    }

    // Handle Submit
    async function handleSubmit(e) {
        e.preventDefault();
        
        if (state.submitting) return;
        
        state.submitting = true;
        setSubmitButtonLoading(true);
        hideAlert();
        
        try {
            const formData = collectFormData();
            
            const response = await fetch(
                `/api/parent/trips/${state.currentTripId}/registrations/${state.currentParticipantId}/requirements`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify(formData)
                }
            );

            const result = await response.json();

            if (response.ok && result.success) {
                // Success
                if (typeof TripsManager !== 'undefined' && TripsManager.showToast) {
                    TripsManager.showToast('Requirements updated successfully!', 'success');
                }
                
                if (typeof TripsManager !== 'undefined' && TripsManager.refreshRegistrations) {
                    TripsManager.refreshRegistrations();
                }
                
                close();
            } else {
                // Error from server
                const errorMessage = result.message || 'Failed to update requirements';
                showAlert(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error updating requirements:', error);
            showAlert('An error occurred while updating. Please try again.', 'error');
        } finally {
            state.submitting = false;
            setSubmitButtonLoading(false);
        }
    }

    // Collect Form Data
    function collectFormData() {
        return {
            medical_conditions: elements.medicalConditions?.value.trim() || '',
            medications: elements.medications?.value.trim() || '',
            allergies: elements.allergies?.value.trim() || '',
            emergency_medical_info: elements.emergencyMedical?.value.trim() || '',
            dietary_restrictions: elements.dietaryRestrictions?.value.trim() || '',
            special_requirements: elements.specialRequirements?.value.trim() || ''
        };
    }

    // Reset Form
    function resetForm() {
        if (elements.form) {
            elements.form.reset();
        }
        hideAlert();
    }

    // Show Loading
    function showLoading() {
        if (elements.loading) elements.loading.style.display = 'flex';
        if (elements.content) elements.content.style.display = 'none';
        if (elements.error) elements.error.style.display = 'none';
        if (elements.footer) elements.footer.style.display = 'none';
    }

    // Show Content
    function showContent() {
        if (elements.loading) elements.loading.style.display = 'none';
        if (elements.content) elements.content.style.display = 'block';
        if (elements.error) elements.error.style.display = 'none';
        if (elements.footer) elements.footer.style.display = 'flex';
    }

    // Show Error
    function showError(message) {
        if (elements.loading) elements.loading.style.display = 'none';
        if (elements.content) elements.content.style.display = 'none';
        if (elements.error) elements.error.style.display = 'flex';
        if (elements.footer) elements.footer.style.display = 'none';
        
        if (elements.errorMessage) {
            elements.errorMessage.textContent = message || 'An error occurred';
        }
    }

    // Show Alert
    function showAlert(message, type = 'error') {
        if (!elements.alert || !elements.alertMessage) return;
        
        elements.alertMessage.textContent = message;
        elements.alert.className = `update-requirements-alert ${type}`;
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
        UpdateRequirementsModal.init();
    });
} else {
    UpdateRequirementsModal.init();
}