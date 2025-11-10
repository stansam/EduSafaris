// Cancel Registration Modal Module
const CancelRegistrationModal = (function() {
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
        confirmCheckbox: null,
        reasonTextarea: null,
        alert: null,
        alertMessage: null,
        
        // Content sections
        loading: null,
        content: null,
        error: null,
        errorMessage: null,
        retryBtn: null,
        footer: null,
        
        // Registration info
        tripTitle: null,
        childName: null,
        destination: null,
        startDate: null,
        price: null,
        status: null
    };

    // Initialize
    function init() {
        try {
            cacheDOM();
            bindEvents();
        } catch (error) {
            console.error('Failed to initialize CancelRegistrationModal:', error);
        }
    }

    // Cache DOM Elements
    function cacheDOM() {
        elements.overlay = document.getElementById('cancelRegistrationModalOverlay');
        elements.close = document.getElementById('cancelRegistrationModalClose');
        elements.cancelBtn = document.getElementById('cancelRegistrationCancelBtn');
        elements.form = document.getElementById('cancelRegistrationForm');
        elements.submitBtn = document.getElementById('cancelRegistrationSubmitBtn');
        elements.confirmCheckbox = document.getElementById('cancelRegistrationConfirm');
        elements.reasonTextarea = document.getElementById('cancelRegistrationReason');
        elements.alert = document.getElementById('cancelRegistrationAlert');
        elements.alertMessage = document.getElementById('cancelRegistrationAlertMessage');
        
        elements.loading = document.getElementById('cancelRegistrationLoading');
        elements.content = document.getElementById('cancelRegistrationContent');
        elements.error = document.getElementById('cancelRegistrationError');
        elements.errorMessage = document.getElementById('cancelRegistrationErrorMessage');
        elements.retryBtn = document.getElementById('cancelRegistrationRetryBtn');
        elements.footer = document.getElementById('cancelRegistrationModalFooter');
        
        elements.tripTitle = document.getElementById('cancelRegistrationTripTitle');
        elements.childName = document.getElementById('cancelRegistrationChildName');
        elements.destination = document.getElementById('cancelRegistrationDestination');
        elements.startDate = document.getElementById('cancelRegistrationStartDate');
        elements.price = document.getElementById('cancelRegistrationPrice');
        elements.status = document.getElementById('cancelRegistrationStatus');
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
        
        // Checkbox validation
        if (elements.confirmCheckbox) {
            elements.confirmCheckbox.addEventListener('change', updateSubmitButton);
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
    async function loadParticipantData(tripId, participantId) {
        showLoading();
        
        try {
            // First, get trip details
            const tripResponse = await fetch(`/api/parent/trips/${tripId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!tripResponse.ok) {
                throw new Error('Failed to load trip details');
            }

            const tripResult = await tripResponse.json();
            
            if (!tripResult.success || !tripResult.data) {
                throw new Error('Invalid trip data');
            }

            // Find participant in trip data
            const participant = tripResult.data.user_participants?.find(
                p => p.id === participantId
            );

            if (!participant) {
                throw new Error('Participant not found');
            }

            state.participantData = {
                trip: tripResult.data,
                participant: participant
            };

            displayParticipantData();
        } catch (error) {
            console.error('Error loading participant data:', error);
            showError(error.message);
        }
    }

    // Display Participant Data
    function displayParticipantData() {
        const { trip, participant } = state.participantData;
        
        if (elements.tripTitle) {
            elements.tripTitle.textContent = trip.title || 'N/A';
        }
        
        if (elements.childName) {
            const fullName = `${participant.first_name || ''} ${participant.last_name || ''}`.trim();
            elements.childName.textContent = fullName || 'N/A';
        }
        
        if (elements.destination) {
            elements.destination.textContent = trip.destination || 'N/A';
        }
        
        if (elements.startDate) {
            elements.startDate.textContent = formatDate(trip.start_date);
        }
        
        if (elements.price) {
            elements.price.textContent = `$${formatNumber(trip.price_per_student)}`;
        }
        
        if (elements.status) {
            const status = participant.status || 'Unknown';
            elements.status.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
        
        showContent();
    }

    // Handle Submit
    async function handleSubmit(e) {
        e.preventDefault();
        
        if (state.submitting) return;
        
        // Validate checkbox
        if (!elements.confirmCheckbox || !elements.confirmCheckbox.checked) {
            showAlert('Please confirm that you want to cancel this registration', 'error');
            return;
        }
        
        state.submitting = true;
        setSubmitButtonLoading(true);
        hideAlert();
        
        try {
            const reason = elements.reasonTextarea?.value.trim() || '';
            
            const response = await fetch(
                `/api/parent/trips/${state.currentTripId}/registrations/${state.currentParticipantId}/cancel`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        cancellation_reason: reason
                    })
                }
            );

            const result = await response.json();

            if (response.ok && result.success) {
                // Success
                if (typeof TripsManager !== 'undefined' && TripsManager.showToast) {
                    TripsManager.showToast('Registration cancelled successfully', 'success');
                }
                
                if (typeof TripsManager !== 'undefined' && TripsManager.refreshTrips) {
                    TripsManager.refreshTrips();
                }
                
                if (typeof TripsManager !== 'undefined' && TripsManager.refreshRegistrations) {
                    TripsManager.refreshRegistrations();
                }
                
                close();
            } else {
                // Error from server
                const errorMessage = result.message || 'Failed to cancel registration';
                showAlert(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error cancelling registration:', error);
            showAlert('An error occurred while cancelling. Please try again.', 'error');
        } finally {
            state.submitting = false;
            setSubmitButtonLoading(false);
        }
    }

    // Update Submit Button
    function updateSubmitButton() {
        if (!elements.submitBtn || !elements.confirmCheckbox) return;
        
        elements.submitBtn.disabled = !elements.confirmCheckbox.checked;
    }

    // Reset Form
    function resetForm() {
        if (elements.form) {
            elements.form.reset();
        }
        
        if (elements.confirmCheckbox) {
            elements.confirmCheckbox.checked = false;
        }
        
        updateSubmitButton();
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
        elements.alert.className = `cancel-registration-alert-message ${type}`;
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
            updateSubmitButton();
        }
    }

    // Utility Functions
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } catch (error) {
            return dateString;
        }
    }

    function formatNumber(number) {
        if (number === null || number === undefined) return '0.00';
        return parseFloat(number).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
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
        CancelRegistrationModal.init();
    });
} else {
    CancelRegistrationModal.init();
}