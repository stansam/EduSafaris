let currentActivityVendorId = null;
let vendorActivityData = [];
let filteredActivityData = [];

// Open Modal
async function openVendorActivityLogModal(vendorId) {
    currentActivityVendorId = vendorId;
    const overlay = document.getElementById('vendorActivityModalOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    await loadVendorActivityLog(vendorId);
}

// Close Modal
function closeVendorActivityLogModal(event) {
    if (event && event.target !== event.currentTarget) return;
    
    const overlay = document.getElementById('vendorActivityModalOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    currentActivityVendorId = null;
    vendorActivityData = [];
    filteredActivityData = [];
}

// Load Activity Log
async function loadVendorActivityLog(vendorId) {
    const content = document.getElementById('vendorActivityContent');
    
    try {
        const response = await fetch(`/api/admin/vendor/${vendorId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to load activity log');

        const result = await response.json();
        
        if (result.success && result.data.activity_logs) {
            vendorActivityData = result.data.activity_logs;
            filteredActivityData = [...vendorActivityData];
            renderVendorActivityLog();
            updateActivityStats();
        } else {
            throw new Error(result.error || 'Failed to load activity log');
        }
    } catch (error) {
        console.error('Error loading activity log:', error);
        content.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 15px;"></i>
                <p>${error.message}</p>
                <button style="padding: 10px 20px; background: #9b59b6; color: white; border: none; border-radius: 6px; cursor: pointer;" onclick="loadVendorActivityLog(${vendorId})">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render Activity Log
function renderVendorActivityLog() {
    const content = document.getElementById('vendorActivityContent');
    
    if (filteredActivityData.length === 0) {
        content.innerHTML = `
            <div class="vendor-activity-empty">
                <i class="fas fa-history"></i>
                <p>No activity found</p>
            </div>
        `;
        return;
    }

    const timelineHtml = filteredActivityData.map(activity => {
        const activityClass = getActivityClass(activity.action);
        const statusBadge = getStatusBadge(activity.status);
        
        return `
            <div class="vendor-activity-item ${activityClass}">
                <div class="vendor-activity-header">
                    <div class="vendor-activity-action">
                        <i class="${getActivityIcon(activity.action)}"></i>
                        ${formatAction(activity.action)}
                    </div>
                    <div class="vendor-activity-time">
                        ${formatDateTime(activity.created_at)}
                    </div>
                </div>
                
                ${activity.description ? `
                    <div class="vendor-activity-desc">
                        ${escapeHtml(activity.description)}
                    </div>
                ` : ''}
                
                <div class="vendor-activity-meta">
                    ${activity.user ? `
                        <div class="vendor-activity-meta-item">
                            <i class="fas fa-user"></i>
                            ${escapeHtml(activity.user.full_name)}
                        </div>
                    ` : ''}
                    
                    ${activity.action_category ? `
                        <div class="vendor-activity-meta-item">
                            <span class="vendor-activity-badge badge-admin">
                                ${formatCategory(activity.action_category)}
                            </span>
                        </div>
                    ` : ''}
                    
                    ${statusBadge}
                </div>
            </div>
        `;
    }).join('');

    content.innerHTML = `
        <div class="vendor-activity-timeline">
            ${timelineHtml}
        </div>
    `;
}

// Filter Activity
function filterVendorActivity() {
    const categoryFilter = document.getElementById('vendorActivityCategoryFilter').value;
    const statusFilter = document.getElementById('vendorActivityStatusFilter').value;

    filteredActivityData = vendorActivityData.filter(activity => {
        if (categoryFilter && activity.action_category !== categoryFilter) return false;
        if (statusFilter && activity.status !== statusFilter) return false;
        return true;
    });

    renderVendorActivityLog();
    updateActivityStats();
}

// Update Stats
function updateActivityStats() {
    const total = filteredActivityData.length;
    const success = filteredActivityData.filter(a => a.status === 'success').length;
    const failed = filteredActivityData.filter(a => a.status === 'failed').length;

    document.getElementById('vendorActivityStats').innerHTML = `
        <strong>${total}</strong> activities • 
        <span style="color: #27ae60;">${success} successful</span> • 
        <span style="color: #e74c3c;">${failed} failed</span>
    `;
}

// Utility Functions
function getActivityClass(action) {
    if (action.includes('create') || action.includes('added')) return 'activity-create';
    if (action.includes('update') || action.includes('edit')) return 'activity-update';
    if (action.includes('delete') || action.includes('removed')) return 'activity-delete';
    if (action.includes('verify') || action.includes('approved')) return 'activity-verify';
    return '';
}

function getActivityIcon(action) {
    const icons = {
        'vendor_created': 'fa-plus-circle',
        'vendor_updated': 'fa-edit',
        'vendor_verified': 'fa-check-circle',
        'vendor_rejected': 'fa-times-circle',
        'vendor_activated': 'fa-toggle-on',
        'vendor_deactivated': 'fa-ban',
        'vendor_deleted': 'fa-trash',
        'vendor_document_verified': 'fa-file-check',
        'vendor_document_rejected': 'fa-file-times',
        'service_booking_created': 'fa-shopping-cart',
        'payment_processed': 'fa-dollar-sign'
    };
    
    return icons[action] || 'fa-circle';
}

function getStatusBadge(status) {
    if (!status) return '';
    
    const badges = {
        'success': '<span class="vendor-activity-badge badge-success"><i class="fas fa-check"></i> Success</span>',
        'failed': '<span class="vendor-activity-badge badge-danger"><i class="fas fa-times"></i> Failed</span>',
        'warning': '<span class="vendor-activity-badge badge-warning"><i class="fas fa-exclamation-triangle"></i> Warning</span>'
    };
    
    return `<div class="vendor-activity-meta-item">${badges[status] || ''}</div>`;
}

function formatAction(action) {
    if (!action) return 'Unknown Action';
    return action.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function formatCategory(category) {
    if (!category) return 'N/A';
    return category.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) return 'Just now';
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
    
    // Format full date
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}