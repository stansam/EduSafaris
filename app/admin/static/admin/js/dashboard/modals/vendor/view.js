let currentViewVendorId = null;

// Open Modal
async function openVendorViewModal(vendorId) {
    currentViewVendorId = vendorId;
    const overlay = document.getElementById('vendorViewModalOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Load vendor details
    await loadVendorDetailsForView(vendorId);
}

// Close Modal
function closeVendorViewModal(event) {
    if (event && event.target !== event.currentTarget) return;
    
    const overlay = document.getElementById('vendorViewModalOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    currentViewVendorId = null;
}

// Load Vendor Details
async function loadVendorDetailsForView(vendorId) {
    const content = document.getElementById('vendorViewModalContent');
    
    try {
        const response = await fetch(`/api/admin/vendor/${vendorId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to load vendor details');

        const result = await response.json();
        
        if (result.success) {
            renderVendorDetails(result.data);
        } else {
            throw new Error(result.error || 'Failed to load vendor');
        }
    } catch (error) {
        console.error('Error loading vendor:', error);
        content.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 15px;"></i>
                <p>${error.message}</p>
                <button class="vendor-view-btn vendor-view-btn-primary" onclick="loadVendorDetailsForView(${vendorId})">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render Vendor Details
function renderVendorDetails(vendor) {
    const content = document.getElementById('vendorViewModalContent');
    const titleText = document.getElementById('vendorViewModalTitleText');
    
    titleText.textContent = vendor.business_name;
    
    content.innerHTML = `
        <!-- Basic Information -->
        <div class="vendor-view-section">
            <h3 class="vendor-view-section-title">
                <i class="fas fa-info-circle"></i>
                Basic Information
            </h3>
            <div class="vendor-info-grid">
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Business Name</span>
                    <span class="vendor-info-value">${escapeHtml(vendor.business_name)}</span>
                </div>
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Business Type</span>
                    <span class="vendor-info-value">${formatBusinessType(vendor.business_type)}</span>
                </div>
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Status</span>
                    <span class="vendor-info-value">
                        <span class="vendor-view-badge ${vendor.is_active ? 'badge-active' : 'badge-inactive'}">
                            <i class="fas ${vendor.is_active ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                            ${vendor.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </span>
                </div>
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Verification</span>
                    <span class="vendor-info-value">
                        <span class="vendor-view-badge ${vendor.is_verified ? 'badge-verified' : 'badge-pending'}">
                            <i class="fas ${vendor.is_verified ? 'fa-check-circle' : 'fa-clock'}"></i>
                            ${vendor.is_verified ? 'Verified' : 'Pending'}
                        </span>
                    </span>
                </div>
            </div>
            ${vendor.description ? `
                <div class="vendor-info-item" style="margin-top: 15px;">
                    <span class="vendor-info-label">Description</span>
                    <span class="vendor-info-value">${escapeHtml(vendor.description)}</span>
                </div>
            ` : ''}
        </div>

        <!-- Contact Information -->
        <div class="vendor-view-section">
            <h3 class="vendor-view-section-title">
                <i class="fas fa-address-book"></i>
                Contact Information
            </h3>
            <div class="vendor-info-grid">
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Email</span>
                    <span class="vendor-info-value">
                        <i class="fas fa-envelope" style="color: #3498db; margin-right: 5px;"></i>
                        ${escapeHtml(vendor.contact_email)}
                    </span>
                </div>
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Phone</span>
                    <span class="vendor-info-value">
                        <i class="fas fa-phone" style="color: #27ae60; margin-right: 5px;"></i>
                        ${escapeHtml(vendor.contact_phone || 'N/A')}
                    </span>
                </div>
                ${vendor.website ? `
                    <div class="vendor-info-item">
                        <span class="vendor-info-label">Website</span>
                        <span class="vendor-info-value">
                            <i class="fas fa-globe" style="color: #9b59b6; margin-right: 5px;"></i>
                            <a href="${escapeHtml(vendor.website)}" target="_blank" style="color: #3498db;">
                                ${escapeHtml(vendor.website)}
                            </a>
                        </span>
                    </div>
                ` : ''}
            </div>
        </div>

        <!-- Location -->
        <div class="vendor-view-section">
            <h3 class="vendor-view-section-title">
                <i class="fas fa-map-marker-alt"></i>
                Location
            </h3>
            <div class="vendor-info-grid">
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Address</span>
                    <span class="vendor-info-value">${escapeHtml(vendor.address_line1 || 'N/A')}</span>
                </div>
                <div class="vendor-info-item">
                    <span class="vendor-info-label">City</span>
                    <span class="vendor-info-value">${escapeHtml(vendor.city || 'N/A')}</span>
                </div>
                <div class="vendor-info-item">
                    <span class="vendor-info-label">State</span>
                    <span class="vendor-info-value">${escapeHtml(vendor.state || 'N/A')}</span>
                </div>
                <div class="vendor-info-item">
                    <span class="vendor-info-label">Country</span>
                    <span class="vendor-info-value">${escapeHtml(vendor.country || 'N/A')}</span>
                </div>
            </div>
        </div>

        <!-- Statistics -->
        <div class="vendor-view-section">
            <h3 class="vendor-view-section-title">
                <i class="fas fa-chart-line"></i>
                Statistics
            </h3>
            <div class="vendor-stats-grid">
                <div class="vendor-stat-box">
                    <h3 class="vendor-stat-value">${vendor.statistics?.total_bookings || 0}</h3>
                    <p class="vendor-stat-label">Total Bookings</p>
                </div>
                <div class="vendor-stat-box">
                    <h3 class="vendor-stat-value">${vendor.statistics?.completed_bookings || 0}</h3>
                    <p class="vendor-stat-label">Completed</p>
                </div>
                <div class="vendor-stat-box">
                    <h3 class="vendor-stat-value">${vendor.average_rating?.toFixed(1) || '0.0'}</h3>
                    <p class="vendor-stat-label">Avg Rating</p>
                </div>
                <div class="vendor-stat-box">
                    <h3 class="vendor-stat-value">${vendor.total_reviews || 0}</h3>
                    <p class="vendor-stat-label">Reviews</p>
                </div>
            </div>
        </div>

        <!-- Documents -->
        ${vendor.documents && vendor.documents.length > 0 ? `
            <div class="vendor-view-section">
                <h3 class="vendor-view-section-title">
                    <i class="fas fa-file-alt"></i>
                    Documents (${vendor.documents.length})
                </h3>
                <div class="vendor-documents-list">
                    ${vendor.documents.map(doc => `
                        <div class="vendor-document-item">
                            <div class="vendor-document-info">
                                <div class="vendor-document-icon">
                                    <i class="fas fa-file-pdf"></i>
                                </div>
                                <div class="vendor-document-details">
                                    <div class="vendor-document-title">${escapeHtml(doc.title)}</div>
                                    <div class="vendor-document-meta">
                                        ${doc.document_type} • ${doc.file_size_mb} MB
                                        ${doc.is_verified ? '<span style="color: #27ae60;">• Verified</span>' : '<span style="color: #f39c12;">• Pending</span>'}
                                    </div>
                                </div>
                            </div>
                            <div class="vendor-document-actions">
                                ${!doc.is_verified ? `
                                    <button class="vendor-view-btn vendor-view-btn-success" onclick="verifyVendorDocument(${vendor.id}, ${doc.id})">
                                        <i class="fas fa-check"></i> Verify
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}

        <!-- Activity Log -->
        ${vendor.activity_logs && vendor.activity_logs.length > 0 ? `
            <div class="vendor-view-section">
                <h3 class="vendor-view-section-title">
                    <i class="fas fa-history"></i>
                    Recent Activity
                </h3>
                <div class="vendor-activity-list">
                    ${vendor.activity_logs.slice(0, 5).map(log => `
                        <div class="vendor-activity-item">
                            <div class="vendor-activity-icon">
                                <i class="fas fa-circle"></i>
                            </div>
                            <div class="vendor-activity-content">
                                <div class="vendor-activity-desc">${escapeHtml(log.description || log.action)}</div>
                                <div class="vendor-activity-time">${formatDate(log.created_at)}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    `;
}

// Edit from View
function editVendorFromView() {
    if (currentViewVendorId) {
        closeVendorViewModal();
        // Open edit modal
        openVendorEditModal(currentViewVendorId);
    }
}

// Verify Document
async function verifyVendorDocument(vendorId, documentId) {
    if (!confirm('Are you sure you want to verify this document?')) return;

    try {
        const response = await fetch(`/api/admin/vendor/${vendorId}/documents/${documentId}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ notes: 'Document verified' })
        });

        const result = await response.json();
        
        if (result.success) {
            alert('Document verified successfully!');
            loadVendorDetailsForView(vendorId);
        } else {
            alert(result.error || 'Failed to verify document');
        }
    } catch (error) {
        console.error('Error verifying document:', error);
        alert('An error occurred while verifying the document');
    }
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatBusinessType(type) {
    if (!type) return 'N/A';
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}