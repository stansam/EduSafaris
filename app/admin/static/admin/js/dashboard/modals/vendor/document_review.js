let currentDocsVendorId = null;
let vendorDocumentsData = [];
let filteredDocumentsData = [];

// Open Modal
async function openVendorDocumentsModal(vendorId) {
    currentDocsVendorId = vendorId;
    const overlay = document.getElementById('vendorDocsModalOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    await loadVendorDocuments(vendorId);
}

// Close Modal
function closeVendorDocumentsModal(event) {
    if (event && event.target !== event.currentTarget) return;
    
    const overlay = document.getElementById('vendorDocsModalOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    currentDocsVendorId = null;
    vendorDocumentsData = [];
    filteredDocumentsData = [];
}

// Load Documents
async function loadVendorDocuments(vendorId) {
    const content = document.getElementById('vendorDocsContent');
    
    try {
        const response = await fetch(`/api/admin/vendor/${vendorId}/documents`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to load documents');

        const result = await response.json();
        
        if (result.success) {
            vendorDocumentsData = result.data.documents;
            filteredDocumentsData = [...vendorDocumentsData];
            renderVendorDocuments();
            updateDocumentStats();
        } else {
            throw new Error(result.error || 'Failed to load documents');
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        content.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 15px;"></i>
                <p>${error.message}</p>
                <button class="vendor-doc-btn vendor-doc-btn-view" onclick="loadVendorDocuments(${vendorId})">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render Documents
function renderVendorDocuments() {
    const content = document.getElementById('vendorDocsContent');
    
    if (filteredDocumentsData.length === 0) {
        content.innerHTML = `
            <div class="vendor-docs-empty">
                <i class="fas fa-folder-open"></i>
                <p>No documents found</p>
            </div>
        `;
        return;
    }

    const listHtml = filteredDocumentsData.map(doc => `
        <div class="vendor-doc-item ${doc.is_verified ? 'verified' : ''}">
            <div class="vendor-doc-icon ${doc.is_verified ? 'verified' : ''}">
                <i class="fas ${getDocumentIcon(doc.document_type)}"></i>
            </div>
            <div class="vendor-doc-content">
                <div class="vendor-doc-header">
                    <h4 class="vendor-doc-title">${escapeHtml(doc.title)}</h4>
                    <span class="vendor-doc-badge ${doc.is_verified ? 'badge-verified' : 'badge-pending'}">
                        <i class="fas ${doc.is_verified ? 'fa-check-circle' : 'fa-clock'}"></i>
                        ${doc.is_verified ? 'Verified' : 'Pending'}
                    </span>
                </div>
                <div class="vendor-doc-meta">
                    <i class="fas fa-tag"></i>${formatDocType(doc.document_type)}
                    <i class="fas fa-file" style="margin-left: 15px;"></i>${doc.file_size_mb} MB
                    <i class="fas fa-calendar" style="margin-left: 15px;"></i>${formatDate(doc.created_at)}
                </div>
                ${doc.notes ? `<div class="vendor-doc-meta" style="color: #e74c3c;"><i class="fas fa-info-circle"></i>${escapeHtml(doc.notes)}</div>` : ''}
                <div class="vendor-doc-actions">
                    ${!doc.is_verified ? `
                        <button class="vendor-doc-btn vendor-doc-btn-verify" onclick="verifyDocument(${doc.id})">
                            <i class="fas fa-check"></i> Verify
                        </button>
                        <button class="vendor-doc-btn vendor-doc-btn-reject" onclick="rejectDocument(${doc.id})">
                            <i class="fas fa-times"></i> Reject
                        </button>
                    ` : ''}
                    <button class="vendor-doc-btn vendor-doc-btn-view" onclick="viewDocument('${escapeHtml(doc.file_path)}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="vendor-doc-btn vendor-doc-btn-delete" onclick="deleteDocument(${doc.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');

    content.innerHTML = `<div class="vendor-docs-list">${listHtml}</div>`;
}

// Filter Documents
function filterVendorDocuments() {
    const typeFilter = document.getElementById('vendorDocsTypeFilter').value;
    const statusFilter = document.getElementById('vendorDocsStatusFilter').value;

    filteredDocumentsData = vendorDocumentsData.filter(doc => {
        if (typeFilter && doc.document_type !== typeFilter) return false;
        if (statusFilter === 'verified' && !doc.is_verified) return false;
        if (statusFilter === 'pending' && doc.is_verified) return false;
        return true;
    });

    renderVendorDocuments();
    updateDocumentStats();
}

// Update Stats
function updateDocumentStats() {
    const total = filteredDocumentsData.length;
    const verified = filteredDocumentsData.filter(d => d.is_verified).length;
    const pending = total - verified;

    document.getElementById('vendorDocsStats').innerHTML = `
        <strong>${total}</strong> documents • 
        <span style="color: #27ae60;">${verified} verified</span> • 
        <span style="color: #f39c12;">${pending} pending</span>
    `;
}

// Document Actions
async function verifyDocument(documentId) {
    if (!confirm('Are you sure you want to verify this document?')) return;

    try {
        const response = await fetch(`/api/admin/vendor/${currentDocsVendorId}/documents/${documentId}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ notes: 'Document verified by admin' })
        });

        const result = await response.json();

        if (result.success) {
            alert('Document verified successfully!');
            await loadVendorDocuments(currentDocsVendorId);
        } else {
            alert(result.error || 'Failed to verify document');
        }
    } catch (error) {
        console.error('Error verifying document:', error);
        alert('An error occurred while verifying the document');
    }
}

async function rejectDocument(documentId) {
    const reason = prompt('Enter rejection reason:');
    if (!reason || !reason.trim()) {
        alert('Rejection reason is required');
        return;
    }

    try {
        const response = await fetch(`/api/admin/vendor/${currentDocsVendorId}/documents/${documentId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ reason: reason.trim() })
        });

        const result = await response.json();

        if (result.success) {
            alert('Document rejected successfully');
            await loadVendorDocuments(currentDocsVendorId);
        } else {
            alert(result.error || 'Failed to reject document');
        }
    } catch (error) {
        console.error('Error rejecting document:', error);
        alert('An error occurred while rejecting the document');
    }
}

async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
        const response = await fetch(`/api/admin/vendor/${currentDocsVendorId}/documents/${documentId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success) {
            alert('Document deleted successfully');
            await loadVendorDocuments(currentDocsVendorId);
        } else {
            alert(result.error || 'Failed to delete document');
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        alert('An error occurred while deleting the document');
    }
}

function viewDocument(filePath) {
    // Open document in new window
    window.open(filePath, '_blank');
}

// Utility Functions
function getDocumentIcon(docType) {
    const icons = {
        'vendor_license': 'fa-file-certificate',
        'insurance': 'fa-file-shield',
        'verification': 'fa-file-check',
        'other': 'fa-file'
    };
    return icons[docType] || 'fa-file';
}

function formatDocType(type) {
    if (!type) return 'N/A';
    return type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}