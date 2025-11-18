let currentActionVendorId = null;
let currentActionVendorData = null;

// Open Modal
function openVendorActionsModal(vendorId, vendorData) {
    currentActionVendorId = vendorId;
    currentActionVendorData = vendorData;
    
    const overlay = document.getElementById('vendorActionsModalOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    renderVendorActions(vendorData);
}

// Close Modal
function closeVendorActionsModal(event) {
    if (event && event.target !== event.currentTarget) return;
    
    const overlay = document.getElementById('vendorActionsModalOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    // currentActionVendorId = null;
    // currentActionVendorData = null;
}

// Render Actions
function renderVendorActions(vendor) {
    // Update info card
    document.getElementById('vendorActionsName').textContent = vendor.business_name;
    document.getElementById('vendorActionsMeta').textContent = `${vendor.business_type || 'N/A'} • ${vendor.city || 'N/A'}`;

    const actionsGrid = document.getElementById('vendorActionsGrid');
    actionsGrid.innerHTML = '';

    // Verification Actions
    if (!vendor.is_verified) {
        actionsGrid.innerHTML += `
            <button class="vendor-action-btn action-verify" onclick="handleVendorVerify()">
                <div class="vendor-action-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="vendor-action-content">
                    <div class="vendor-action-title">Verify Vendor</div>
                    <p class="vendor-action-desc">Mark this vendor as verified and activate</p>
                </div>
            </button>
        `;

        actionsGrid.innerHTML += `
            <button class="vendor-action-btn action-reject" onclick="handleVendorReject()">
                <div class="vendor-action-icon">
                    <i class="fas fa-times-circle"></i>
                </div>
                <div class="vendor-action-content">
                    <div class="vendor-action-title">Reject Vendor</div>
                    <p class="vendor-action-desc">Reject verification and deactivate</p>
                </div>
            </button>
        `;
    }

    // Activation Actions
    if (vendor.is_verified) {
        if (vendor.is_active) {
            actionsGrid.innerHTML += `
                <button class="vendor-action-btn action-deactivate" onclick="handleVendorDeactivate()">
                    <div class="vendor-action-icon">
                        <i class="fas fa-ban"></i>
                    </div>
                    <div class="vendor-action-content">
                        <div class="vendor-action-title">Deactivate Vendor</div>
                        <p class="vendor-action-desc">Temporarily disable this vendor</p>
                    </div>
                </button>
            `;
        } else {
            actionsGrid.innerHTML += `
                <button class="vendor-action-btn action-activate" onclick="handleVendorActivate()">
                    <div class="vendor-action-icon">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="vendor-action-content">
                        <div class="vendor-action-title">Activate Vendor</div>
                        <p class="vendor-action-desc">Re-activate this vendor</p>
                    </div>
                </button>
            `;
        }
    }

    // Document Management
    actionsGrid.innerHTML += `
        <button class="vendor-action-btn action-documents" onclick="handleVendorDocuments()">
            <div class="vendor-action-icon">
                <i class="fas fa-file-alt"></i>
            </div>
            <div class="vendor-action-content">
                <div class="vendor-action-title">Review Documents</div>
                <p class="vendor-action-desc">View and verify vendor documents</p>
            </div>
        </button>
    `;

    // Activity Log
    actionsGrid.innerHTML += `
        <button class="vendor-action-btn action-activity" onclick="handleVendorActivityLog()">
            <div class="vendor-action-icon">
                <i class="fas fa-history"></i>
            </div>
            <div class="vendor-action-content">
                <div class="vendor-action-title">Activity Log</div>
                <p class="vendor-action-desc">View vendor activity history</p>
            </div>
        </button>
    `;

    // Delete Action
    actionsGrid.innerHTML += `
        <button class="vendor-action-btn action-delete" onclick="handleVendorDelete()">
            <div class="vendor-action-icon">
                <i class="fas fa-trash-alt"></i>
            </div>
            <div class="vendor-action-content">
                <div class="vendor-action-title">Delete Vendor</div>
                <p class="vendor-action-desc">Permanently remove this vendor</p>
            </div>
        </button>
    `;
}

// Action Handlers
async function handleVendorVerify() {
    const notes = prompt('Enter verification notes (optional):');
    if (notes === null) return; // User cancelled

    try {
        const response = await fetch(`/api/admin/vendor/${currentActionVendorId}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ notes: notes || 'Verified by admin' })
        });

        const result = await response.json();

        if (result.success) {
            alert('Vendor verified successfully!');
            closeVendorActionsModal();
            if (typeof loadVendorsData === 'function') {
                loadVendorsData(currentVendorPage);
            }
        } else {
            alert(result.error || 'Failed to verify vendor');
        }
    } catch (error) {
        console.error('Error verifying vendor:', error);
        alert('An error occurred while verifying the vendor');
    }
}

async function handleVendorReject() {
    const reason = prompt('Enter rejection reason:');
    if (!reason || !reason.trim()) {
        alert('Rejection reason is required');
        return;
    }

    try {
        const response = await fetch(`/api/admin/vendor/${currentActionVendorId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ reason: reason.trim() })
        });

        const result = await response.json();

        if (result.success) {
            alert('Vendor rejected successfully');
            closeVendorActionsModal();
            if (typeof loadVendorsData === 'function') {
                loadVendorsData(currentVendorPage);
            }
        } else {
            alert(result.error || 'Failed to reject vendor');
        }
    } catch (error) {
        console.error('Error rejecting vendor:', error);
        alert('An error occurred while rejecting the vendor');
    }
}

async function handleVendorActivate() {
    if (!confirm('Are you sure you want to activate this vendor?')) return;

    try {
        const response = await fetch(`/api/admin/vendor/${currentActionVendorId}/activate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ notes: 'Activated by admin' })
        });

        const result = await response.json();

        if (result.success) {
            alert('Vendor activated successfully!');
            closeVendorActionsModal();
            if (typeof loadVendorsData === 'function') {
                loadVendorsData(currentVendorPage);
            }
        } else {
            alert(result.error || 'Failed to activate vendor');
        }
    } catch (error) {
        console.error('Error activating vendor:', error);
        alert('An error occurred while activating the vendor');
    }
}

async function handleVendorDeactivate() {
    const reason = prompt('Enter deactivation reason:');
    if (!reason || !reason.trim()) {
        alert('Deactivation reason is required');
        return;
    }

    try {
        const response = await fetch(`/api/admin/vendor/${currentActionVendorId}/deactivate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ reason: reason.trim() })
        });

        const result = await response.json();

        if (result.success) {
            alert('Vendor deactivated successfully');
            closeVendorActionsModal();
            if (typeof loadVendorsData === 'function') {
                loadVendorsData(currentVendorPage);
            }
        } else if (result.error === 'Vendor has active bookings') {
            if (confirm(`${result.details.message}. Force deactivation?`)) {
                // Retry with force flag
                await forceDeactivateVendor(reason);
            }
        } else {
            alert(result.error || 'Failed to deactivate vendor');
        }
    } catch (error) {
        console.error('Error deactivating vendor:', error);
        alert('An error occurred while deactivating the vendor');
    }
}

async function forceDeactivateVendor(reason) {
    try {
        const response = await fetch(`/api/admin/vendor/${currentActionVendorId}/deactivate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ reason: reason, force: true })
        });

        const result = await response.json();

        if (result.success) {
            alert('Vendor deactivated successfully (forced)');
            closeVendorActionsModal();
            if (typeof loadVendorsData === 'function') {
                loadVendorsData(currentVendorPage);
            }
        } else {
            alert(result.error || 'Failed to deactivate vendor');
        }
    } catch (error) {
        console.error('Error force deactivating vendor:', error);
        alert('An error occurred while deactivating the vendor');
    }
}

async function handleVendorDelete() {
    const confirmDelete = confirm('Are you sure you want to delete this vendor?\n\nNote: This will be a soft delete (deactivation). The vendor can be reactivated later.');
    if (!confirmDelete) return;

    try {
        const response = await fetch(`/api/admin/vendor/${currentActionVendorId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ permanent: false })
        });

        const result = await response.json();

        if (result.success) {
            alert('Vendor deleted successfully');
            closeVendorActionsModal();
            if (typeof loadVendorsData === 'function') {
                loadVendorsData(currentVendorPage);
            }
        } else {
            alert(result.error || 'Failed to delete vendor');
        }
    } catch (error) {
        console.error('Error deleting vendor:', error);
        alert('An error occurred while deleting the vendor');
    }
}

function handleVendorDocuments() {
    closeVendorActionsModal();
    // Open documents modal (to be implemented)
    openVendorDocumentsModal(currentActionVendorId);
}

function handleVendorActivityLog() {
    closeVendorActionsModal();
    // Open activity log modal (to be implemented)
    openVendorActivityLogModal(currentActionVendorId);
}