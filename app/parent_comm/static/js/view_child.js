// View Child Profile Modal Script
let currentViewChildId = null;
let currentViewChildData = null;

// Open modal
function openViewChildModal(childId) {
    currentViewChildId = childId;
    const modal = document.getElementById('viewChildModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    loadChildProfile(childId);
}

// Close modal
function closeViewChildModal() {
    const modal = document.getElementById('viewChildModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    currentViewChildId = null;
    currentViewChildData = null;
}

// Load child profile
async function loadChildProfile(childId) {
    const loadingState = document.getElementById('viewChildLoading');
    const errorState = document.getElementById('viewChildError');
    const content = document.getElementById('viewChildContent');
    
    loadingState.style.display = 'block';
    errorState.style.display = 'none';
    content.style.display = 'none';
    
    try {
        const response = await fetch(`/api/parent/children/${childId}`, {
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
        
        if (data.success && data.child) {
            currentViewChildData = data.child;
            renderChildProfile(data.child);
            loadingState.style.display = 'none';
            content.style.display = 'block';
        } else {
            throw new Error(data.error || 'Failed to load profile');
        }
        
    } catch (error) {
        console.error('Error loading child profile:', error);
        loadingState.style.display = 'none';
        errorState.style.display = 'block';
        document.getElementById('viewChildErrorMessage').textContent = 
            'Failed to load child profile. Please try again.';
    }
}

// Render child profile
function renderChildProfile(child) {
    // Update modal title
    document.getElementById('viewChildName').textContent = 
        `${child.first_name} ${child.last_name}'s Profile`;
    
    // Show medical alert if needed
    const medicalAlert = document.getElementById('viewChildMedicalAlert');
    const medicalContent = document.getElementById('viewChildMedicalContent');
    
    if (child.allergies || child.medical_conditions) {
        let alertText = [];
        if (child.allergies) alertText.push(`<strong>Allergies:</strong> ${escapeHtml(child.allergies)}`);
        if (child.medical_conditions) alertText.push(`<strong>Conditions:</strong> ${escapeHtml(child.medical_conditions)}`);
        medicalContent.innerHTML = alertText.join('<br>');
        medicalAlert.style.display = 'block';
    } else {
        medicalAlert.style.display = 'none';
    }
    
    // Render current trip
    renderCurrentTrip(child);
    
    // Render personal information
    renderPersonalInfo(child);
    
    // Render contact information
    renderContactInfo(child);
    
    // Render emergency contacts
    renderEmergencyContacts(child);
    
    // Render medical information
    renderMedicalInfo(child);
    
    // Render documents
    renderDocuments(child.documents || []);
    
    // Render consents
    renderConsents(child.consents || []);
    
    // Render trip history
    renderTripHistory(child.trip_history || []);
}

// Render current trip
function renderCurrentTrip(child) {
    const container = document.getElementById('viewChildTripInfo');
    const registration = child.current_registration;  // Changed from current_trip
    
    if (registration && registration.trip) {
        const trip = registration.trip;
        container.innerHTML = `
            <div class="profile-child-info-grid">
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Trip Name</span>
                    <span class="profile-child-info-value">${escapeHtml(trip.title)}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Destination</span>
                    <span class="profile-child-info-value">${escapeHtml(trip.destination || 'N/A')}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Start Date</span>
                    <span class="profile-child-info-value">${formatDate(trip.start_date)}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">End Date</span>
                    <span class="profile-child-info-value">${formatDate(trip.end_date)}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Registration Status</span>
                    <span class="profile-child-badge ${registration.status}">${registration.status || 'Registered'}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Payment Status</span>
                    <span class="profile-child-badge ${registration.payment_status}">${formatPaymentStatus(registration.payment_status)}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Registration Number</span>
                    <span class="profile-child-info-value">${escapeHtml(registration.registration_number || 'N/A')}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Total Amount</span>
                    <span class="profile-child-info-value">KES ${formatCurrency(registration.total_amount)}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Amount Paid</span>
                    <span class="profile-child-info-value">KES ${formatCurrency(registration.amount_paid || 0)}</span>
                </div>
                <div class="profile-child-info-item">
                    <span class="profile-child-info-label">Outstanding Balance</span>
                    <span class="profile-child-info-value">KES ${formatCurrency(registration.outstanding_balance || 0)}</span>
                </div>
            </div>
        `;
    } else {
        container.innerHTML = '<p style="color: #7f8c8d;">No active trip registration</p>';
    }
}

// Render personal information
function renderPersonalInfo(child) {
    const container = document.getElementById('viewChildPersonalInfo');
    container.innerHTML = `
        <div class="profile-child-info-item">
            <span class="profile-child-info-label">Full Name</span>
            <span class="profile-child-info-value">${escapeHtml(child.first_name)} ${escapeHtml(child.last_name)}</span>
        </div>
        <div class="profile-child-info-item">
            <span class="profile-child-info-label">Date of Birth</span>
            <span class="profile-child-info-value">${child.date_of_birth ? formatDate(child.date_of_birth) : 'Not provided'}</span>
        </div>
        <div class="profile-child-info-item">
            <span class="profile-child-info-label">Grade/Class</span>
            <span class="profile-child-info-value">${escapeHtml(child.grade_level || 'Not provided')}</span>
        </div>
        <div class="profile-child-info-item">
            <span class="profile-child-info-label">Student ID</span>
            <span class="profile-child-info-value">${escapeHtml(child.student_id || 'Not provided')}</span>
        </div>
    `;
}

// Render contact information
function renderContactInfo(child) {
    const container = document.getElementById('viewChildContactInfo');
    container.innerHTML = `
        <div class="profile-child-info-item">
            <span class="profile-child-info-label">Email</span>
            <span class="profile-child-info-value">${escapeHtml(child.email || 'Not provided')}</span>
        </div>
        <div class="profile-child-info-item">
            <span class="profile-child-info-label">Phone</span>
            <span class="profile-child-info-value">${escapeHtml(child.phone || 'Not provided')}</span>
        </div>
    `;
}

// Render emergency contacts
function renderEmergencyContacts(child) {
    const container = document.getElementById('viewChildEmergencyContacts');
    
    let html = '';
    
    if (child.emergency_contact_1_name) {
        html += `
            <div style="margin-bottom: 20px;">
                <h4 style="color: #2c3e50; margin-bottom: 12px;">Primary Contact</h4>
                <div class="profile-child-info-grid">
                    <div class="profile-child-info-item">
                        <span class="profile-child-info-label">Name</span>
                        <span class="profile-child-info-value">${escapeHtml(child.emergency_contact_1_name)}</span>
                    </div>
                    <div class="profile-child-info-item">
                        <span class="profile-child-info-label">Phone</span>
                        <span class="profile-child-info-value">${escapeHtml(child.emergency_contact_1_phone || 'N/A')}</span>
                    </div>
                    <div class="profile-child-info-item">
                        <span class="profile-child-info-label">Relationship</span>
                        <span class="profile-child-info-value">${escapeHtml(child.emergency_contact_1_relationship || 'N/A')}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (child.emergency_contact_2_name) {
        html += `
            <div>
                <h4 style="color: #2c3e50; margin-bottom: 12px;">Secondary Contact</h4>
                <div class="profile-child-info-grid">
                    <div class="profile-child-info-item">
                        <span class="profile-child-info-label">Name</span>
                        <span class="profile-child-info-value">${escapeHtml(child.emergency_contact_2_name)}</span>
                    </div>
                    <div class="profile-child-info-item">
                        <span class="profile-child-info-label">Phone</span>
                        <span class="profile-child-info-value">${escapeHtml(child.emergency_contact_2_phone || 'N/A')}</span>
                    </div>
                    <div class="profile-child-info-item">
                        <span class="profile-child-info-label">Relationship</span>
                        <span class="profile-child-info-value">${escapeHtml(child.emergency_contact_2_relationship || 'N/A')}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html || '<p style="color: #7f8c8d;">No emergency contacts provided</p>';
}

// Render medical information
function renderMedicalInfo(child) {
    const container = document.getElementById('viewChildMedicalInfo');
    container.innerHTML = `
        <div class="profile-child-info-grid">
            <div class="profile-child-info-item" style="grid-column: 1 / -1;">
                <span class="profile-child-info-label">Medical Conditions</span>
                <span class="profile-child-info-value">${escapeHtml(child.medical_conditions || 'None reported')}</span>
            </div>
            <div class="profile-child-info-item" style="grid-column: 1 / -1;">
                <span class="profile-child-info-label">Medications</span>
                <span class="profile-child-info-value">${escapeHtml(child.medications || 'None reported')}</span>
            </div>
            <div class="profile-child-info-item" style="grid-column: 1 / -1;">
                <span class="profile-child-info-label">Allergies</span>
                <span class="profile-child-info-value">${escapeHtml(child.allergies || 'None reported')}</span>
            </div>
            <div class="profile-child-info-item" style="grid-column: 1 / -1;">
                <span class="profile-child-info-label">Dietary Restrictions</span>
                <span class="profile-child-info-value">${escapeHtml(child.dietary_restrictions || 'None reported')}</span>
            </div>
            <div class="profile-child-info-item" style="grid-column: 1 / -1;">
                <span class="profile-child-info-label">Emergency Medical Info</span>
                <span class="profile-child-info-value">${escapeHtml(child.emergency_medical_info || 'None provided')}</span>
            </div>
        </div>
    `;
}

// Render documents
function renderDocuments(documents) {
    const container = document.getElementById('viewChildDocuments');
    
    if (documents.length === 0) {
        container.innerHTML = '<p style="color: #7f8c8d;">No documents uploaded</p>';
        return;
    }
    
    container.innerHTML = documents.map(doc => `
        <div class="document-child-item">
            <div class="document-child-info">
                <div class="document-child-icon">
                    <i class="fas fa-file-${getFileIcon(doc.file_type)}"></i>
                </div>
                <div class="document-child-details">
                    <div class="document-child-name">${escapeHtml(doc.title)}</div>
                    <div class="document-child-meta">
                        ${doc.document_type} • ${formatFileSize(doc.file_size)} • ${formatDate(doc.created_at)}
                    </div>
                </div>
            </div>
            <div class="document-child-actions">
                <button class="document-child-btn" style="background: #3498db; color: white;" onclick="downloadDocument(${doc.id})">
                    <i class="fas fa-download"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Render consents
function renderConsents(consents) {
    const container = document.getElementById('viewChildConsents');
    
    if (consents.length === 0) {
        container.innerHTML = '<p style="color: #7f8c8d;">No consent forms</p>';
        return;
    }
    
    container.innerHTML = consents.map(consent => `
        <div class="consent-child-item ${consent.is_signed ? 'signed' : 'unsigned'}">
            <div class="consent-child-header">
                <span class="consent-child-title">${escapeHtml(consent.consent_type)}</span>
                <span class="profile-child-badge ${consent.is_signed ? 'signed' : 'unsigned'}">
                    <i class="fas fa-${consent.is_signed ? 'check-circle' : 'clock'}"></i>
                    ${consent.is_signed ? 'Signed' : 'Pending'}
                </span>
            </div>
            ${consent.consent_text ? `
                <div class="consent-child-content">${escapeHtml(consent.consent_text).substring(0, 150)}...</div>
            ` : ''}
            <div class="consent-child-footer">
                <span style="font-size: 13px; color: #7f8c8d;">
                    ${consent.is_signed ? `Signed on ${formatDate(consent.signed_date)}` : 'Not yet signed'}
                </span>
                ${!consent.is_signed ? `
                    <button class="action-btn primary" style="padding: 6px 12px; font-size: 13px;" onclick="openSignConsentModal(${consent.id})">
                        <i class="fas fa-signature"></i> Sign Now
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Render trip history
function renderTripHistory(child) {
    const container = document.getElementById('viewChildTripHistory');
    const history = child.registrations_history || [];  // Changed from trip_history
    
    if (history.length === 0) {
        container.innerHTML = '<p style="color: #7f8c8d;">No previous registrations</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="profile-child-section">
            ${history.map(registration => {
                const trip = registration.trip;
                return trip ? `
                    <div style="padding: 12px; border-bottom: 1px solid #ecf0f1;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px;">
                                    ${escapeHtml(trip.title)}
                                </div>
                                <div style="font-size: 13px; color: #7f8c8d;">
                                    ${formatDate(trip.start_date)} to ${formatDate(trip.end_date)}
                                </div>
                                <div style="font-size: 13px; color: #95a5a6; margin-top: 4px;">
                                    Registration: ${escapeHtml(registration.registration_number || 'N/A')}
                                </div>
                            </div>
                            <div>
                                <span class="status-badge ${registration.status}">${registration.status}</span>
                                <div style="font-size: 12px; color: #7f8c8d; margin-top: 4px; text-align: right;">
                                    Payment: ${formatPaymentStatus(registration.payment_status)}
                                </div>
                            </div>
                        </div>
                    </div>
                ` : '';
            }).join('')}
        </div>
    `;
}
// Helper functions
function getFileIcon(fileType) {
    if (fileType.includes('pdf')) return 'pdf';
    if (fileType.includes('image')) return 'image';
    if (fileType.includes('word')) return 'word';
    return 'alt';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function downloadDocument(docId) {
    showNotification('Document download started', 'success');
    // Implement download logic
}

function openUpdateChildModalFromView() {
    closeViewChildModal();
    openUpdateChildModal(currentViewChildId);
}

// Close modal when clicking outside
document.getElementById('viewChildModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeViewChildModal();
    }
});