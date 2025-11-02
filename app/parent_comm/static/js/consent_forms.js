// Consent Forms Modal Script
let currentConsentChildId = null;
let currentConsents = [];

// Open consent modal
function openConsentModal(childId) {
    currentConsentChildId = childId;
    const modal = document.getElementById('consentModal');
    const child = getChildById(childId);
    
    if (child) {
        document.getElementById('consentChildName').textContent = `${child.first_name} ${child.last_name}`;
    }
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    loadConsentForms(childId);
}

// Close consent modal
function closeConsentModal() {
    const modal = document.getElementById('consentModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    currentConsentChildId = null;
    currentConsents = [];
}

// Load consent forms
async function loadConsentForms(childId) {
    const loadingState = document.getElementById('consentLoading');
    const errorState = document.getElementById('consentError');
    const emptyState = document.getElementById('consentEmpty');
    const listContainer = document.getElementById('consentList');
    
    loadingState.style.display = 'block';
    errorState.style.display = 'none';
    emptyState.style.display = 'none';
    listContainer.style.display = 'none';
    
    try {
        const response = await fetch(`/api/parent/children/${childId}/consents`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        loadingState.style.display = 'none';
        
        if (data.success && data.consents && data.consents.length > 0) {
            currentConsents = data.consents;
            renderConsentForms(data.consents);
            listContainer.style.display = 'flex';
        } else {
            emptyState.style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error loading consent forms:', error);
        loadingState.style.display = 'none';
        errorState.style.display = 'block';
        document.getElementById('consentErrorMessage').textContent = 
            'Failed to load consent forms. Please try again.';
    }
}

// Render consent forms
function renderConsentForms(consents) {
    const container = document.getElementById('consentList');
    
    container.innerHTML = consents.map(consent => `
        <div class="consent-child-item ${consent.is_signed ? 'signed' : 'unsigned'}">
            <div class="consent-child-header">
                <span class="consent-child-title">${escapeHtml(consent.consent_type || 'Consent Form')}</span>
                <span class="profile-child-badge ${consent.is_signed ? 'signed' : 'unsigned'}">
                    <i class="fas fa-${consent.is_signed ? 'check-circle' : 'clock'}"></i>
                    ${consent.is_signed ? 'Signed' : 'Pending Signature'}
                </span>
            </div>
            
            ${consent.consent_text ? `
                <div class="consent-child-content">
                    ${escapeHtml(consent.consent_text).substring(0, 200)}${consent.consent_text.length > 200 ? '...' : ''}
                </div>
            ` : ''}
            
            <div class="consent-child-footer">
                <div style="font-size: 13px; color: ${consent.is_signed ? '#155724' : '#856404'};">
                    ${consent.is_signed 
                        ? `<i class="fas fa-check"></i> Signed by ${escapeHtml(consent.signer_name || 'Unknown')} on ${formatDate(consent.signed_date)}` 
                        : '<i class="fas fa-exclamation-circle"></i> Signature required'}
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="action-btn secondary" style="padding: 8px 16px; font-size: 13px;" onclick="viewConsentDetails(${consent.id})">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                    ${!consent.is_signed ? `
                        <button class="action-btn success" style="padding: 8px 16px; font-size: 13px;" onclick="openSignConsentModal(${consent.id})">
                            <i class="fas fa-signature"></i> Sign Now
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

// View consent details
function viewConsentDetails(consentId) {
    const consent = currentConsents.find(c => c.id === consentId);
    if (consent) {
        // If already signed, just show details in alert
        if (consent.is_signed) {
            alert(`Consent Type: ${consent.consent_type}\n\nSigned by: ${consent.signer_name}\nDate: ${formatDate(consent.signed_date)}\n\n${consent.consent_text}`);
        } else {
            // If not signed, open sign modal
            openSignConsentModal(consentId);
        }
    }
}

// Open sign consent modal
function openSignConsentModal(consentId) {
    const consent = currentConsents.find(c => c.id === consentId);
    if (!consent) {
        showNotification('Consent form not found', 'error');
        return;
    }
    
    // Populate consent details
    document.getElementById('signConsentId').value = consent.id;
    document.getElementById('signConsentChildId').value = currentConsentChildId;
    
    document.getElementById('signConsentDetails').innerHTML = `
        <div class="profile-child-info-grid">
            <div class="profile-child-info-item">
                <span class="profile-child-info-label">Consent Type</span>
                <span class="profile-child-info-value">${escapeHtml(consent.consent_type || 'General Consent')}</span>
            </div>
            <div class="profile-child-info-item">
                <span class="profile-child-info-label">Created Date</span>
                <span class="profile-child-info-value">${formatDate(consent.created_at)}</span>
            </div>
        </div>
    `;
    
    document.getElementById('signConsentText').textContent = consent.consent_text || 'No consent text available.';
    
    // Show modal
    const modal = document.getElementById('signConsentModal');
    modal.style.display = 'flex';
    resetSignConsentForm();
}

// Close sign consent modal
function closeSignConsentModal() {
    const modal = document.getElementById('signConsentModal');
    modal.style.display = 'none';
    resetSignConsentForm();
}

// Reset sign consent form
function resetSignConsentForm() {
    const form = document.getElementById('signConsentForm');
    const inputs = form.querySelectorAll('input[type="text"], textarea, select, input[type="checkbox"]');
    inputs.forEach(input => {
        if (input.type === 'checkbox') {
            input.checked = false;
        } else if (input.id !== 'signConsentId' && input.id !== 'signConsentChildId') {
            input.value = '';
        }
    });
    clearAllErrors('signConsent');
}

// Validate sign consent form
function validateSignConsentForm() {
    const errors = [];
    
    const signerName = document.getElementById('signConsentSignerName').value.trim();
    const relationship = document.getElementById('signConsentRelationship').value;
    const agree = document.getElementById('signConsentAgree').checked;
    
    if (!signerName || signerName.length < 3) {
        showValidationError('signConsentSignerName', 'Please enter your full legal name');
        errors.push('Invalid signer name');
    }
    
    if (!relationship) {
        showValidationError('signConsentRelationship', 'Please select your relationship to the child');
        errors.push('Missing relationship');
    }
    
    if (!agree) {
        showValidationError('signConsentAgree', 'You must agree to the terms to sign this consent form');
        errors.push('Agreement required');
    }
    
    return errors;
}

// Handle sign consent form submission
document.getElementById('signConsentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Clear previous errors
    clearAllErrors('signConsent');
    
    // Validate form
    const validationErrors = validateSignConsentForm();
    if (validationErrors.length > 0) {
        showNotification('Please correct the errors in the form', 'error');
        return;
    }
    
    const consentId = document.getElementById('signConsentId').value;
    const childId = document.getElementById('signConsentChildId').value;
    
    const formData = {
        signer_name: document.getElementById('signConsentSignerName').value.trim(),
        signer_relationship: document.getElementById('signConsentRelationship').value,
        notes: document.getElementById('signConsentNotes').value.trim()
    };
    
    // Show loading state
    const submitBtn = document.getElementById('signConsentSubmitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/parent/children/${childId}/consents/${consentId}/sign`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showNotification('Consent form signed successfully!', 'success');
            closeSignConsentModal();
            loadConsentForms(childId); // Reload consent list
            refreshChildren(); // Refresh main children list
        } else {
            showNotification(data.error || 'Failed to sign consent form', 'error');
        }
        
    } catch (error) {
        console.error('Error signing consent form:', error);
        showNotification('Network error. Please check your connection and try again.', 'error');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

// Close modals when clicking outside
document.getElementById('consentModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeConsentModal();
    }
});

document.getElementById('signConsentModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeSignConsentModal();
    }
});