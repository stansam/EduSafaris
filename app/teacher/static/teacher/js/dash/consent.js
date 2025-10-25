// Sample data for testing
const sampleConsents = [
    {
        id: 1,
        participant_name: "Emma Chen",
        parent_name: "Michael Chen",
        parent_email: "michael.chen@email.com",
        parent_phone: "+1 (555) 123-4567",
        is_signed: true,
        trip_title: "Science Museum Trip",
        trip_date: "2025-11-15",
        signed_at: "2025-10-18 14:30:00",
        created_at: "2025-10-15 09:00:00",
        emergency_contact: "Sarah Chen",
        emergency_phone: "+1 (555) 987-6543",
        medical_conditions: "None",
        allergies: "Peanuts",
        special_instructions: "Please ensure no peanut products during lunch"
    },
    {
        id: 2,
        participant_name: "Lucas Martinez",
        parent_name: "Maria Martinez",
        parent_email: "maria.martinez@email.com",
        parent_phone: "+1 (555) 234-5678",
        is_signed: false,
        trip_title: "Zoo Field Trip",
        trip_date: "2025-11-20",
        signed_at: null,
        created_at: "2025-10-20 10:15:00",
        emergency_contact: "Carlos Martinez",
        emergency_phone: "+1 (555) 876-5432",
        medical_conditions: "Asthma - carries inhaler",
        allergies: "None",
        special_instructions: "Needs inhaler access at all times"
    }
];

// Format date function
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format date only
function formatDateOnly(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric'
    });
}

// Show modal with consent details
function showConsentModal(consent) {
    const overlay = document.getElementById('consentModalOverlay');
    const modalBody = document.getElementById('consentModalBody');
    const modalTitle = document.getElementById('modalConsentTitle');
    const modalSubtitle = document.getElementById('modalConsentSubtitle');
    const mainWrapper = document.getElementById('mainContentWrapper');

    // Update title
    modalTitle.innerHTML = `
        <i class="fas fa-file-contract"></i>
        <span>${consent.participant_name}'s Consent</span>
    `;
    modalSubtitle.textContent = `${consent.trip_title}`;

    // Build modal content
    const statusClass = consent.is_signed ? 'signed' : 'pending';
    const statusIcon = consent.is_signed ? 'fa-check-circle' : 'fa-clock';
    const statusText = consent.is_signed ? 'Signed' : 'Pending Signature';

    modalBody.innerHTML = `
        <!-- Status Section -->
        <div class="consent-detail-section">
            <div class="consent-section-title">
                <i class="fas fa-info-circle"></i>
                Status
            </div>
            <div class="consent-status-display ${statusClass}">
                <i class="fas ${statusIcon}"></i>
                ${statusText}
            </div>
        </div>

        <!-- Participant Information -->
        <div class="consent-detail-section">
            <div class="consent-section-title">
                <i class="fas fa-user"></i>
                Participant Information
            </div>
            <div class="consent-info-grid">
                <div class="consent-info-item">
                    <div class="consent-info-label">Participant Name</div>
                    <div class="consent-info-value">${consent.participant_name}</div>
                </div>
                <div class="consent-info-item">
                    <div class="consent-info-label">Trip</div>
                    <div class="consent-info-value">${consent.trip_title}</div>
                </div>
                <div class="consent-info-item">
                    <div class="consent-info-label">Trip Date</div>
                    <div class="consent-info-value">${formatDateOnly(consent.trip_date)}</div>
                </div>
            </div>
        </div>

        <!-- Parent/Guardian Information -->
        <div class="consent-detail-section">
            <div class="consent-section-title">
                <i class="fas fa-user-tie"></i>
                Parent/Guardian Information
            </div>
            <div class="consent-info-grid">
                <div class="consent-info-item">
                    <div class="consent-info-label">Parent Name</div>
                    <div class="consent-info-value">${consent.parent_name}</div>
                </div>
                <div class="consent-info-item">
                    <div class="consent-info-label">Email</div>
                    <div class="consent-info-value">${consent.parent_email || 'Not provided'}</div>
                </div>
                <div class="consent-info-item">
                    <div class="consent-info-label">Phone</div>
                    <div class="consent-info-value">${consent.parent_phone || 'Not provided'}</div>
                </div>
            </div>
        </div>

        <!-- Emergency Contact -->
        <div class="consent-detail-section">
            <div class="consent-section-title">
                <i class="fas fa-phone-alt"></i>
                Emergency Contact
            </div>
            <div class="consent-info-grid">
                <div class="consent-info-item">
                    <div class="consent-info-label">Emergency Contact Name</div>
                    <div class="consent-info-value">${consent.emergency_contact || 'Not provided'}</div>
                </div>
                <div class="consent-info-item">
                    <div class="consent-info-label">Emergency Phone</div>
                    <div class="consent-info-value">${consent.emergency_phone || 'Not provided'}</div>
                </div>
            </div>
        </div>

        <!-- Medical Information -->
        <div class="consent-detail-section">
            <div class="consent-section-title">
                <i class="fas fa-heartbeat"></i>
                Medical Information
            </div>
            <div class="consent-info-grid">
                <div class="consent-info-item">
                    <div class="consent-info-label">Medical Conditions</div>
                    <div class="consent-info-value">${consent.medical_conditions || 'None reported'}</div>
                </div>
                <div class="consent-info-item">
                    <div class="consent-info-label">Allergies</div>
                    <div class="consent-info-value">${consent.allergies || 'None reported'}</div>
                </div>
            </div>
            ${consent.special_instructions ? `
                <div style="margin-top: 16px;">
                    <div class="consent-info-label" style="margin-bottom: 8px;">Special Instructions</div>
                    <div class="consent-description-box">${consent.special_instructions}</div>
                </div>
            ` : ''}
        </div>

        <!-- Timeline -->
        <div class="consent-detail-section">
            <div class="consent-section-title">
                <i class="fas fa-history"></i>
                Timeline
            </div>
            <div class="consent-timeline">
                <div class="consent-timeline-item">
                    <div class="consent-timeline-label">Created</div>
                    <div class="consent-timeline-value">${formatDate(consent.created_at)}</div>
                </div>
                ${consent.signed_at ? `
                    <div class="consent-timeline-item">
                        <div class="consent-timeline-label">Signed</div>
                        <div class="consent-timeline-value">${formatDate(consent.signed_at)}</div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    // Show modal with animation
    mainWrapper.classList.add('blurred');
    document.body.classList.add('consent-modal-open');
    overlay.classList.add('active');
}

// Close modal function
function closeConsentModal() {
    const overlay = document.getElementById('consentModalOverlay');
    const mainWrapper = document.getElementById('mainContentWrapper');
    
    overlay.classList.remove('active');
    mainWrapper.classList.remove('blurred');
    document.body.classList.remove('consent-modal-open');
}

// Print consent function
function printConsent() {
    window.print();
}

// Render consent items
function renderConsents(consents) {
    const container = document.getElementById('consentListContainer');
    
    if (consents.length === 0) {
        container.innerHTML = `
            <div class="consent-empty-state">
                <i class="fas fa-file-contract"></i>
                <h3>No Consent Forms</h3>
                <p>There are no consent forms to display at this time.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = consents.map((consent, index) => {
        const isSigned = consent.is_signed;
        const iconClass = isSigned ? 'signed-icon' : 'pending-icon';
        const badgeClass = isSigned ? 'signed-badge' : 'pending-badge';
        const statusText = isSigned ? 'Signed' : 'Pending';
        
        return `
            <div class="consent-item-card" data-consent-id="${consent.id}" data-consent-index="${index}">
                <div class="consent-left-section">
                    <div class="consent-icon-wrapper ${iconClass}">
                        <i class="fas fa-file-alt"></i>
                    </div>
                    <div class="consent-info-section">
                        <div class="consent-title-text">${consent.participant_name}'s Consent</div>
                        <div class="consent-parent-text">Parent: ${consent.parent_name}</div>
                    </div>
                </div>
                <div class="consent-status-badge ${badgeClass}">
                    ${statusText}
                </div>
            </div>
        `;
    }).join('');

    // Add click event listeners to consent cards
    document.querySelectorAll('.consent-item-card').forEach((card, index) => {
        card.addEventListener('click', () => {
            showConsentModal(consents[index]);
        });
    });
}

// Show loading state
function showLoading() {
    const container = document.getElementById('consentListContainer');
    container.innerHTML = `
        <div class="consent-loading-state">
            <i class="fas fa-spinner"></i>
            <p>Loading consent forms...</p>
        </div>
    `;
}

// Show error state
function showError(message) {
    const container = document.getElementById('consentListContainer');
    container.innerHTML = `
        <div class="consent-error-state">
            <i class="fas fa-exclamation-circle"></i>
            <div>
                <strong>Error:</strong> ${message}
            </div>
        </div>
    `;
}

// Fetch consents from API
async function fetchConsents() {
    showLoading();
    
    try {
        // Attempt to fetch from API
        const response = await fetch('api/consents');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.consents) {
            renderConsents(data.consents);
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.log('API fetch failed, using sample data:', error.message);
        // Fallback to sample data for testing
        setTimeout(() => {
            renderConsents(sampleConsents);
        }, 500);
    }
}

// Modal event listeners
document.getElementById('closeModalBtn').addEventListener('click', closeConsentModal);
document.getElementById('closeModalFooterBtn').addEventListener('click', closeConsentModal);
document.getElementById('printConsentBtn').addEventListener('click', printConsent);

// Close modal when clicking overlay (but not modal content)
document.getElementById('consentModalOverlay').addEventListener('click', (e) => {
    if (e.target.id === 'consentModalOverlay') {
        closeConsentModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('consentModalOverlay').classList.contains('active')) {
        closeConsentModal();
    }
});

// Prevent modal content click from closing modal
document.getElementById('consentModalContent').addEventListener('click', (e) => {
    e.stopPropagation();
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', fetchConsents);