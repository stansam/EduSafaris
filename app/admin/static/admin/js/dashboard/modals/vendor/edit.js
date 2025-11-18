let currentEditVendorId = null;
let originalVendorData = null;

// Open Modal
async function openVendorEditModal(vendorId) {
    currentEditVendorId = vendorId;
    const overlay = document.getElementById('vendorEditModalOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    await loadVendorDataForEdit(vendorId);
}

// Close Modal
function closeVendorEditModal(event) {
    if (event && event.target !== event.currentTarget) return;
    
    // Check for unsaved changes
    if (hasUnsavedChanges()) {
        if (!confirm('You have unsaved changes. Are you sure you want to close?')) {
            return;
        }
    }
    
    const overlay = document.getElementById('vendorEditModalOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    currentEditVendorId = null;
    originalVendorData = null;
}

// Load Vendor Data
async function loadVendorDataForEdit(vendorId) {
    const content = document.getElementById('vendorEditModalContent');
    
    try {
        const response = await fetch(`/api/admin/vendor/${vendorId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to load vendor data');

        const result = await response.json();
        
        if (result.success) {
            originalVendorData = result.data;
            renderEditForm(result.data);
            document.getElementById('vendorEditSaveBtn').disabled = false;
        } else {
            throw new Error(result.error || 'Failed to load vendor');
        }
    } catch (error) {
        console.error('Error loading vendor:', error);
        content.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 15px;"></i>
                <p>${error.message}</p>
                <button class="vendor-edit-btn vendor-edit-btn-primary" onclick="loadVendorDataForEdit(${vendorId})">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render Edit Form
function renderEditForm(vendor) {
    const content = document.getElementById('vendorEditModalContent');
    
    content.innerHTML = `
        <form id="vendorEditForm" onsubmit="event.preventDefault();">
            <!-- Basic Information -->
            <div class="vendor-edit-form-section">
                <h3 class="vendor-edit-section-title">
                    <i class="fas fa-info-circle"></i>
                    Basic Information
                </h3>
                <div class="vendor-edit-form-grid">
                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">
                            Business Name <span class="required">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editBusinessName"
                            value="${escapeHtml(vendor.business_name)}"
                            required
                        >
                        <span class="vendor-edit-form-error">Business name is required</span>
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">
                            Business Type <span class="required">*</span>
                        </label>
                        <select class="vendor-edit-form-select" id="editBusinessType" required>
                            <option value="">Select Type</option>
                            <option value="transportation" ${vendor.business_type === 'transportation' ? 'selected' : ''}>Transportation</option>
                            <option value="accommodation" ${vendor.business_type === 'accommodation' ? 'selected' : ''}>Accommodation</option>
                            <option value="activities" ${vendor.business_type === 'activities' ? 'selected' : ''}>Activities</option>
                            <option value="catering" ${vendor.business_type === 'catering' ? 'selected' : ''}>Catering</option>
                            <option value="tour_guide" ${vendor.business_type === 'tour_guide' ? 'selected' : ''}>Tour Guide</option>
                            <option value="equipment_rental" ${vendor.business_type === 'equipment_rental' ? 'selected' : ''}>Equipment Rental</option>
                            <option value="insurance" ${vendor.business_type === 'insurance' ? 'selected' : ''}>Insurance</option>
                            <option value="other" ${vendor.business_type === 'other' ? 'selected' : ''}>Other</option>
                        </select>
                        <span class="vendor-edit-form-error">Business type is required</span>
                    </div>

                    <div class="vendor-edit-form-group full-width">
                        <label class="vendor-edit-form-label">Description</label>
                        <textarea 
                            class="vendor-edit-form-textarea" 
                            id="editDescription"
                        >${escapeHtml(vendor.description || '')}</textarea>
                    </div>
                </div>
            </div>

            <!-- Contact Information -->
            <div class="vendor-edit-form-section">
                <h3 class="vendor-edit-section-title">
                    <i class="fas fa-address-book"></i>
                    Contact Information
                </h3>
                <div class="vendor-edit-form-grid">
                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">
                            Contact Email <span class="required">*</span>
                        </label>
                        <input 
                            type="email" 
                            class="vendor-edit-form-input" 
                            id="editContactEmail"
                            value="${escapeHtml(vendor.contact_email)}"
                            required
                        >
                        <span class="vendor-edit-form-error">Valid email is required</span>
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">
                            Contact Phone <span class="required">*</span>
                        </label>
                        <input 
                            type="tel" 
                            class="vendor-edit-form-input" 
                            id="editContactPhone"
                            value="${escapeHtml(vendor.contact_phone || '')}"
                            required
                        >
                        <span class="vendor-edit-form-error">Phone number is required</span>
                    </div>

                    <div class="vendor-edit-form-group full-width">
                        <label class="vendor-edit-form-label">Website</label>
                        <input 
                            type="url" 
                            class="vendor-edit-form-input" 
                            id="editWebsite"
                            value="${escapeHtml(vendor.website || '')}"
                            placeholder="https://example.com"
                        >
                    </div>
                </div>
            </div>

            <!-- Address -->
            <div class="vendor-edit-form-section">
                <h3 class="vendor-edit-section-title">
                    <i class="fas fa-map-marker-alt"></i>
                    Address
                </h3>
                <div class="vendor-edit-form-grid">
                    <div class="vendor-edit-form-group full-width">
                        <label class="vendor-edit-form-label">Address Line 1</label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editAddressLine1"
                            value="${escapeHtml(vendor.address_line1 || '')}"
                        >
                    </div>

                    <div class="vendor-edit-form-group full-width">
                        <label class="vendor-edit-form-label">Address Line 2</label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editAddressLine2"
                            value="${escapeHtml(vendor.address_line2 || '')}"
                        >
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">City</label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editCity"
                            value="${escapeHtml(vendor.city || '')}"
                        >
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">State</label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editState"
                            value="${escapeHtml(vendor.state || '')}"
                        >
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">Postal Code</label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editPostalCode"
                            value="${escapeHtml(vendor.postal_code || '')}"
                        >
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">Country</label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editCountry"
                            value="${escapeHtml(vendor.country || '')}"
                        >
                    </div>
                </div>
            </div>

            <!-- Business Details -->
            <div class="vendor-edit-form-section">
                <h3 class="vendor-edit-section-title">
                    <i class="fas fa-briefcase"></i>
                    Business Details
                </h3>
                <div class="vendor-edit-form-grid">
                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">License Number</label>
                        <input 
                            type="text" 
                            class="vendor-edit-form-input" 
                            id="editLicenseNumber"
                            value="${escapeHtml(vendor.license_number || '')}"
                        >
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">Capacity</label>
                        <input 
                            type="number" 
                            class="vendor-edit-form-input" 
                            id="editCapacity"
                            value="${vendor.capacity || ''}"
                            min="1"
                        >
                    </div>

                    <div class="vendor-edit-form-group full-width">
                        <label class="vendor-edit-form-label">Insurance Details</label>
                        <textarea 
                            class="vendor-edit-form-textarea" 
                            id="editInsuranceDetails"
                        >${escapeHtml(vendor.insurance_details || '')}</textarea>
                    </div>
                </div>
            </div>

            <!-- Pricing -->
            <div class="vendor-edit-form-section">
                <h3 class="vendor-edit-section-title">
                    <i class="fas fa-dollar-sign"></i>
                    Pricing
                </h3>
                <div class="vendor-edit-form-grid">
                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">Base Price</label>
                        <input 
                            type="number" 
                            class="vendor-edit-form-input" 
                            id="editBasePrice"
                            value="${vendor.base_price || ''}"
                            min="0"
                            step="0.01"
                        >
                    </div>

                    <div class="vendor-edit-form-group">
                        <label class="vendor-edit-form-label">Price Per Person</label>
                        <input 
                            type="number" 
                            class="vendor-edit-form-input" 
                            id="editPricePerPerson"
                            value="${vendor.price_per_person || ''}"
                            min="0"
                            step="0.01"
                        >
                    </div>

                    <div class="vendor-edit-form-group full-width">
                        <label class="vendor-edit-form-label">Pricing Notes</label>
                        <textarea 
                            class="vendor-edit-form-textarea" 
                            id="editPricingNotes"
                        >${escapeHtml(vendor.pricing_notes || '')}</textarea>
                    </div>
                </div>
            </div>
        </form>
    `;

    // Add change listeners
    const form = document.getElementById('vendorEditForm');
    if (form) {
        form.addEventListener('input', validateForm);
    }
}

// Validate Form
function validateForm() {
    let isValid = true;

    // Validate required fields
    const requiredFields = [
        { id: 'editBusinessName', name: 'Business name' },
        { id: 'editBusinessType', name: 'Business type' },
        { id: 'editContactEmail', name: 'Contact email' },
        { id: 'editContactPhone', name: 'Contact phone' }
    ];

    requiredFields.forEach(field => {
        const input = document.getElementById(field.id);
        const group = input.closest('.vendor-edit-form-group');
        
        if (!input.value.trim()) {
            group.classList.add('error');
            isValid = false;
        } else {
            group.classList.remove('error');
        }
    });

    return isValid;
}

// Check for Unsaved Changes
function hasUnsavedChanges() {
    if (!originalVendorData) return false;

    const currentData = getFormData();
    return JSON.stringify(currentData) !== JSON.stringify(getOriginalFormData());
}

function getFormData() {
    return {
        business_name: document.getElementById('editBusinessName')?.value.trim(),
        business_type: document.getElementById('editBusinessType')?.value,
        description: document.getElementById('editDescription')?.value.trim(),
        contact_email: document.getElementById('editContactEmail')?.value.trim(),
        contact_phone: document.getElementById('editContactPhone')?.value.trim(),
        website: document.getElementById('editWebsite')?.value.trim(),
        address_line1: document.getElementById('editAddressLine1')?.value.trim(),
        address_line2: document.getElementById('editAddressLine2')?.value.trim(),
        city: document.getElementById('editCity')?.value.trim(),
        state: document.getElementById('editState')?.value.trim(),
        postal_code: document.getElementById('editPostalCode')?.value.trim(),
        country: document.getElementById('editCountry')?.value.trim(),
        license_number: document.getElementById('editLicenseNumber')?.value.trim(),
        capacity: document.getElementById('editCapacity')?.value ? parseInt(document.getElementById('editCapacity').value) : null,
        insurance_details: document.getElementById('editInsuranceDetails')?.value.trim(),
        base_price: document.getElementById('editBasePrice')?.value ? parseFloat(document.getElementById('editBasePrice').value) : null,
        price_per_person: document.getElementById('editPricePerPerson')?.value ? parseFloat(document.getElementById('editPricePerPerson').value) : null,
        pricing_notes: document.getElementById('editPricingNotes')?.value.trim()
    };
}

function getOriginalFormData() {
    if (!originalVendorData) return {};

    return {
        business_name: originalVendorData.business_name || '',
        business_type: originalVendorData.business_type || '',
        description: originalVendorData.description || '',
        contact_email: originalVendorData.contact_email || '',
        contact_phone: originalVendorData.contact_phone || '',
        website: originalVendorData.website || '',
        address_line1: originalVendorData.address_line1 || '',
        address_line2: originalVendorData.address_line2 || '',
        city: originalVendorData.city || '',
        state: originalVendorData.state || '',
        postal_code: originalVendorData.postal_code || '',
        country: originalVendorData.country || '',
        license_number: originalVendorData.license_number || '',
        capacity: originalVendorData.capacity || null,
        insurance_details: originalVendorData.insurance_details || '',
        base_price: originalVendorData.base_price || null,
        price_per_person: originalVendorData.price_per_person || null,
        pricing_notes: originalVendorData.pricing_notes || ''
    };
}

// Save Changes
async function saveVendorChanges() {
    if (!validateForm()) {
        alert('Please fill in all required fields correctly.');
        return;
    }

    const saveBtn = document.getElementById('vendorEditSaveBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const data = getFormData();
        
        const response = await fetch(`/api/admin/vendor/${currentEditVendorId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('Vendor updated successfully!');
            closeVendorEditModal();
            // Reload vendors table
            if (typeof loadVendorsData === 'function') {
                loadVendorsData(currentVendorPage);
            }
        } else {
            alert(result.error || 'Failed to update vendor');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
        }
    } catch (error) {
        console.error('Error saving vendor:', error);
        alert('An error occurred while saving changes');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
    }
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}