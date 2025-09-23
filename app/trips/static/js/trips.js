// Client-side JavaScript for trips functionality

class TripManager {
    constructor() {
        this.init();
    }

    init() {
        // Initialize event listeners and components
        this.setupEventListeners();
        this.setupFormValidation();
    }

    setupEventListeners() {
        // CSV Upload handling
        const csvUploadForms = document.querySelectorAll('form[data-csv-upload]');
        csvUploadForms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleCsvUpload(e));
        });

        // Participant management
        const participantForms = document.querySelectorAll('.participant-form');
        participantForms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleParticipantSubmit(e));
        });

        // Trip status management
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="start-trip"]')) {
                this.handleTripStart(e);
            } else if (e.target.matches('[data-action="end-trip"]')) {
                this.handleTripEnd(e);
            }
        });
    }

    setupFormValidation() {
        // Real-time form validation
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', () => this.validateField(input));
                input.addEventListener('input', () => this.clearFieldError(input));
            });
        });
    }

    async handleCsvUpload(event) {
        event.preventDefault();
        
        const form = event.target;
        const fileInput = form.querySelector('input[type="file"]');
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (!fileInput.files.length) {
            this.showAlert('Please select a CSV file', 'warning');
            return;
        }

        const formData = new FormData(form);
        
        // Update button state
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>Uploading...';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert(result.message, 'success');
                
                // Display any errors if present
                if (result.errors && result.errors.length > 0) {
                    const errorList = result.errors.map(error => `<li>${error}</li>`).join('');
                    this.showAlert(
                        `<strong>Upload completed with warnings:</strong><ul class="mb-0 mt-2">${errorList}</ul>`,
                        'warning'
                    );
                }

                // Refresh participant list
                await this.refreshParticipantList();
                
                // Close modal if exists
                const modal = form.closest('.modal');
                if (modal) {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                }
            } else {
                this.showAlert(result.error || 'Upload failed', 'danger');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showAlert('Network error during upload', 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    async handleParticipantSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Validate required fields
        const requiredFields = form.querySelectorAll('input[required], select[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.setFieldError(field, 'This field is required');
                isValid = false;
            }
        });

        if (!isValid) {
            this.showAlert('Please fill in all required fields', 'warning');
            return;
        }

        // Update button state
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>Adding...';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert(result.message, 'success');
                
                // Add participant to list
                this.addParticipantToList(result.participant);
                
                // Reset form
                form.reset();
                
                // Close modal if exists
                const modal = form.closest('.modal');
                if (modal) {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                }
            } else {
                this.showAlert(result.error || 'Failed to add participant', 'danger');
                
                // Show field-specific errors
                if (result.errors) {
                    Object.keys(result.errors).forEach(field => {
                        const fieldElement = form.querySelector(`[name="${field}"]`);
                        if (fieldElement) {
                            this.setFieldError(fieldElement, result.errors[field][0]);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Participant add error:', error);
            this.showAlert('Network error adding participant', 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    async handleTripStart(event) {
        event.preventDefault();
        
        if (!confirm('Are you sure you want to start this trip? This will enable location tracking.')) {
            return;
        }

        const button = event.target;
        const tripId = button.dataset.tripId;

        try {
            const response = await fetch(`/trips/${tripId}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert(result.message, 'success');
                
                // Update UI to reflect trip started
                this.updateTripStatus(tripId, 'in_progress');
                
                // Refresh page after short delay
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.showAlert(result.error || 'Failed to start trip', 'danger');
            }
        } catch (error) {
            console.error('Trip start error:', error);
            this.showAlert('Network error starting trip', 'danger');
        }
    }

    async handleTripEnd(event) {
        event.preventDefault();
        
        if (!confirm('Are you sure you want to end this trip? This action cannot be undone.')) {
            return;
        }

        const button = event.target;
        const tripId = button.dataset.tripId;

        try {
            const response = await fetch(`/trips/${tripId}/end`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert(result.message, 'success');
                
                // Update UI to reflect trip ended
                this.updateTripStatus(tripId, 'completed');
                
                // Refresh page after short delay
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.showAlert(result.error || 'Failed to end trip', 'danger');
            }
        } catch (error) {
            console.error('Trip end error:', error);
            this.showAlert('Network error ending trip', 'danger');
        }
    }

    async refreshParticipantList() {
        const participantsList = document.getElementById('participants-list');
        if (!participantsList) return;

        const tripId = this.getCurrentTripId();
        if (!tripId) return;

        try {
            const response = await fetch(`/trips/${tripId}/participants`);
            const participants = await response.json();
            
            this.renderParticipantList(participants);
        } catch (error) {
            console.error('Error refreshing participants:', error);
        }
    }

    addParticipantToList(participant) {
        const participantsList = document.getElementById('participants-list');
        if (!participantsList) return;

        // Remove "no participants" message if it exists
        const noParticipantsMsg = participantsList.querySelector('.text-center');
        if (noParticipantsMsg) {
            noParticipantsMsg.remove();
        }

        // Create participant HTML
        const participantHTML = `
            <div class="participant-item fade-in" data-participant-id="${participant.id}">
                <div class="row align-items-center">
                    <div class="col-md-4">
                        <strong>${participant.full_name}</strong>
                        ${participant.grade_level ? `<br><small class="text-muted">Grade ${participant.grade_level}</small>` : ''}
                    </div>
                    <div class="col-md-3">
                        <span class="badge bg-${this.getPaymentStatusClass(participant.payment_status)}">
                            ${participant.payment_status.charAt(0).toUpperCase() + participant.payment_status.slice(1)}
                        </span>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">
                            Paid: $${participant.amount_paid.toFixed(2)}
                        </small>
                    </div>
                    <div class="col-md-2 text-end">
                        <a href="/trips/${this.getCurrentTripId()}/participants/${participant.id}/consent" 
                           class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-file-text"></i>
                        </a>
                    </div>
                </div>
            </div>
        `;

        participantsList.insertAdjacentHTML('beforeend', participantHTML);
    }

    getPaymentStatusClass(status) {
        const statusMap = {
            'paid': 'success',
            'partial': 'warning',
            'pending': 'secondary'
        };
        return statusMap[status] || 'secondary';
    }

    updateTripStatus(tripId, status) {
        const statusBadges = document.querySelectorAll('.status-badge');
        statusBadges.forEach(badge => {
            badge.className = `status-badge status-${status}`;
            badge.textContent = status.replace('_', ' ').toUpperCase();
        });
    }

    validateField(field) {
        const value = field.value.trim();
        
        // Clear previous errors
        this.clearFieldError(field);

        // Required field validation
        if (field.hasAttribute('required') && !value) {
            this.setFieldError(field, 'This field is required');
            return false;
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                this.setFieldError(field, 'Please enter a valid email address');
                return false;
            }
        }

        // Date validation
        if (field.type === 'date' && value) {
            const selectedDate = new Date(value);
            const today = new Date();
            
            if (field.name === 'date_of_birth' && selectedDate > today) {
                this.setFieldError(field, 'Date of birth cannot be in the future');
                return false;
            }
        }

        return true;
    }

    setFieldError(field, message) {
        field.classList.add('is-invalid');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }

        // Add new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorMsg = field.parentNode.querySelector('.invalid-feedback');
        if (errorMsg) {
            errorMsg.remove();
        }
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.querySelector('.alert-container') || document.body;
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
        
        // Auto-dismiss after 5 seconds for success/info alerts
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    getCurrentTripId() {
        // Extract trip ID from URL or data attribute
        const match = window.location.pathname.match(/\/trips\/(\d+)/);
        return match ? match[1] : null;
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new TripManager();
});

// Export for potential external use
window.TripManager = TripManager;