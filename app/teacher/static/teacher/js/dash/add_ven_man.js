/**
 * Additional Modals JavaScript
 * Handles booking details, statistics, and availability checking
 */

/* ============================================
   BOOKING DETAILS MODAL
   ============================================ */

async function openBookingDetailsModal(bookingId) {
    const modal = document.getElementById('bookingDetailsModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadBookingDetails(bookingId);
}

function closeBookingDetailsModal() {
    const modal = document.getElementById('bookingDetailsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

async function loadBookingDetails(bookingId) {
    const loadingState = document.getElementById('bdmLoadingState');
    const content = document.getElementById('bdmContent');

    if (loadingState) loadingState.style.display = 'block';
    if (content) content.style.display = 'none';

    try {
        const response = await fetch(`/api/teacher/vendors/bookings/${bookingId}`);
        const data = await handleBdmApiResponse(response);

        if (data.success) {
            displayBookingDetails(data.data);
            if (loadingState) loadingState.style.display = 'none';
            if (content) content.style.display = 'block';
        } else {
            showBdmError('Failed to load booking details');
        }
    } catch (error) {
        console.error('Error loading booking details:', error);
        showBdmError('An error occurred while loading the booking');
    }
}

function displayBookingDetails(booking) {
    // Status badge
    const statusBadge = document.getElementById('bdmStatusBadge');
    if (statusBadge) {
        statusBadge.textContent = booking.status;
        statusBadge.className = `bdm-status-badge status-${booking.status}`;
    }

    // Booking ID
    const bookingId = document.getElementById('bdmBookingId');
    if (bookingId) {
        bookingId.textContent = `Booking #${booking.id}`;
    }

    // Action buttons
    const actionButtons = document.getElementById('bdmActionButtons');
    if (actionButtons) {
        actionButtons.innerHTML = '';

        if (booking.status === 'pending') {
            actionButtons.innerHTML += `
                <button class="bdm-action-btn" onclick="openConfirmBookingModal(${booking.id})">
                    <i class="fas fa-check"></i> Confirm
                </button>
            `;
        }

        if (booking.status === 'confirmed') {
            actionButtons.innerHTML += `
                <button class="bdm-action-btn" onclick="openPaymentModal(${booking.id})">
                    <i class="fas fa-credit-card"></i> Pay
                </button>
            `;
        }

        if (booking.status === 'completed' && !booking.rating) {
            actionButtons.innerHTML += `
                <button class="bdm-action-btn" onclick="openRateVendorModal(${booking.id})">
                    <i class="fas fa-star"></i> Rate
                </button>
            `;
        }

        if (['pending', 'confirmed'].includes(booking.status)) {
            actionButtons.innerHTML += `
                <button class="bdm-action-btn" onclick="openCancelBookingModal(${booking.id})">
                    <i class="fas fa-times"></i> Cancel
                </button>
            `;
        }
    }

    // Vendor info
    document.getElementById('bdmVendorName').textContent = booking.vendor?.business_name || 'N/A';
    document.getElementById('bdmVendorType').textContent = booking.vendor?.business_type || 'N/A';
    document.getElementById('bdmVendorPhone').textContent = booking.vendor?.phone || 'N/A';
    document.getElementById('bdmVendorEmail').textContent = booking.vendor?.email || 'N/A';

    // Trip info
    document.getElementById('bdmTripTitle').textContent = booking.trip?.title || 'N/A';
    
    const tripDates = [booking.trip?.start_date, booking.trip?.end_date]
        .filter(Boolean)
        .map(d => formatBdmDate(d))
        .join(' - ') || 'N/A';
    document.getElementById('bdmTripDates').textContent = tripDates;
    
    document.getElementById('bdmTripDestination').textContent = booking.trip?.destination || 'N/A';

    // Service details
    document.getElementById('bdmServiceType').textContent = booking.booking_type || 'N/A';
    document.getElementById('bdmServiceDescription').textContent = booking.service_description || 'N/A';

    // Special requirements
    if (booking.special_requirements) {
        document.getElementById('bdmSpecialReqRow').style.display = 'flex';
        document.getElementById('bdmSpecialRequirements').textContent = booking.special_requirements;
    }

    // Notes
    if (booking.notes) {
        document.getElementById('bdmNotesRow').style.display = 'flex';
        document.getElementById('bdmNotes').textContent = booking.notes;
    }

    // Financial details
    const quotedAmount = parseFloat(booking.quoted_amount || 0);
    const totalAmount = parseFloat(booking.total_amount || quotedAmount);
    const amountPaid = booking.total_paid || 0;
    const balance = totalAmount - amountPaid;

    document.getElementById('bdmQuotedAmount').textContent = `KES ${quotedAmount.toLocaleString()}`;
    document.getElementById('bdmTotalAmount').textContent = `KES ${totalAmount.toLocaleString()}`;
    document.getElementById('bdmAmountPaid').textContent = `KES ${amountPaid.toLocaleString()}`;
    document.getElementById('bdmBalance').textContent = `KES ${balance.toLocaleString()}`;

    // Payment history
    if (booking.payments && booking.payments.length > 0) {
        const paymentSection = document.getElementById('bdmPaymentSection');
        paymentSection.style.display = 'block';
        
        const paymentList = document.getElementById('bdmPaymentList');
        paymentList.innerHTML = '';

        booking.payments.forEach(payment => {
            const statusClass = payment.status === 'completed' ? 'success' : 
                              payment.status === 'failed' ? 'failed' : '';
            
            const item = document.createElement('div');
            item.className = 'bdm-payment-item';
            item.innerHTML = `
                <div class="bdm-payment-info">
                    <div class="bdm-payment-icon ${statusClass}">
                        <i class="fas fa-${payment.status === 'completed' ? 'check' : payment.status === 'failed' ? 'times' : 'clock'}"></i>
                    </div>
                    <div class="bdm-payment-details">
                        <h5>${payment.payment_method.toUpperCase()} Payment</h5>
                        <p>${formatBdmDate(payment.created_at)} - ${payment.status}</p>
                    </div>
                </div>
                <div class="bdm-payment-amount">KES ${parseFloat(payment.amount).toLocaleString()}</div>
            `;
            paymentList.appendChild(item);
        });
    }

    // Activity timeline
    if (booking.activity_logs && booking.activity_logs.length > 0) {
        const timeline = document.getElementById('bdmTimeline');
        timeline.innerHTML = '';

        booking.activity_logs.forEach(log => {
            const item = document.createElement('div');
            item.className = 'bdm-timeline-item';
            item.innerHTML = `
                <div class="bdm-timeline-dot"></div>
                <div class="bdm-timeline-content">
                    <div class="bdm-timeline-header">
                        <span class="bdm-timeline-action">${log.action.replace(/_/g, ' ').toUpperCase()}</span>
                        <span class="bdm-timeline-time">${formatBdmDate(log.created_at)}</span>
                    </div>
                    <p class="bdm-timeline-description">${log.description || ''}</p>
                </div>
            `;
            timeline.appendChild(item);
        });
    } else {
        document.getElementById('bdmTimeline').innerHTML = '<p style="color: #95a5a6; text-align: center;">No activity yet</p>';
    }
}

async function handleBdmApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'An error occurred');
    }
    return await response.json();
}

function formatBdmDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return date.toLocaleDateString('en-US', options);
}

function showBdmError(message) {
    const loadingState = document.getElementById('bdmLoadingState');
    if (loadingState) {
        loadingState.innerHTML = `
            <i class="fas fa-exclamation-circle" style="font-size: 48px; color: #e74c3c; margin-bottom: 20px;"></i>
            <p style="color: #e74c3c; font-weight: 600;">${message}</p>
            <button onclick="closeBookingDetailsModal()" style="margin-top: 20px; padding: 10px 20px; background: #3498db; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Close</button>
        `;
    }
}

/* ============================================
   VENDOR STATISTICS MODAL
   ============================================ */

async function showVendorStatsModal() {
    const modal = document.getElementById('vendorStatsModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadVendorStatistics();
}

function closeVendorStatsModal() {
    const modal = document.getElementById('vendorStatsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

async function loadVendorStatistics() {
    const loadingState = document.getElementById('vsmLoadingState');
    const content = document.getElementById('vsmContent');

    if (loadingState) loadingState.style.display = 'block';
    if (content) content.style.display = 'none';

    try {
        const response = await fetch('/api/teacher/vendors/stats');
        const data = await handleVsmApiResponse(response);

        if (data.success) {
            displayVendorStatistics(data.data);
            if (loadingState) loadingState.style.display = 'none';
            if (content) content.style.display = 'block';
        } else {
            showVsmError('Failed to load statistics');
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
        showVsmError('An error occurred while loading statistics');
    }
}

function displayVendorStatistics(stats) {
    // Overview stats
    document.getElementById('vsmTotalBookings').textContent = stats.total_bookings || 0;
    document.getElementById('vsmCompletedBookings').textContent = stats.by_status?.completed || 0;
    document.getElementById('vsmPendingBookings').textContent = stats.by_status?.pending || 0;
    document.getElementById('vsmUniqueVendors').textContent = stats.unique_vendors || 0;

    // Financial summary
    document.getElementById('vsmTotalSpent').textContent = `KES ${(stats.total_spent || 0).toLocaleString()}`;
    document.getElementById('vsmPendingPayments').textContent = `KES ${(stats.pending_payments || 0).toLocaleString()}`;
    document.getElementById('vsmAverageRating').textContent = (stats.average_rating || 0).toFixed(1);

    // Status chart
    const statusChart = document.getElementById('vsmStatusChart');
    if (statusChart && stats.by_status) {
        statusChart.innerHTML = '';
        const statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled'];
        const maxCount = Math.max(...Object.values(stats.by_status), 1);

        statuses.forEach(status => {
            const count = stats.by_status[status] || 0;
            const percentage = (count / maxCount) * 100;

            const row = document.createElement('div');
            row.className = 'vsm-chart-bar-row';
            row.innerHTML = `
                <span class="vsm-chart-label">${status}</span>
                <div class="vsm-chart-bar-container">
                    <div class="vsm-chart-bar-fill" style="width: ${percentage}%">${count}</div>
                </div>
                <span class="vsm-chart-count">${count}</span>
            `;
            statusChart.appendChild(row);
        });
    }

    // Type list
    const typeList = document.getElementById('vsmTypeList');
    if (typeList && stats.by_type) {
        typeList.innerHTML = '';

        Object.entries(stats.by_type).forEach(([type, count]) => {
            const item = document.createElement('div');
            item.className = 'vsm-type-item';
            item.innerHTML = `
                <span class="vsm-type-name">${type}</span>
                <span class="vsm-type-count">${count}</span>
            `;
            typeList.appendChild(item);
        });

        if (Object.keys(stats.by_type).length === 0) {
            typeList.innerHTML = '<p style="text-align: center; color: #95a5a6; padding: 20px;">No bookings by type yet</p>';
        }
    }
}

async function handleVsmApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'An error occurred');
    }
    return await response.json();
}

function showVsmError(message) {
    const loadingState = document.getElementById('vsmLoadingState');
    if (loadingState) {
        loadingState.innerHTML = `
            <i class="fas fa-exclamation-circle" style="font-size: 48px; color: #e74c3c; margin-bottom: 20px;"></i>
            <p style="color: #e74c3c; font-weight: 600;">${message}</p>
            <button onclick="closeVendorStatsModal()" style="margin-top: 20px; padding: 10px 20px; background: #3498db; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Close</button>
        `;
    }
}

function exportVendorStats() {
    if (typeof window.vendorStatsData === 'undefined') {
        showModalNotification('No statistics data available to export', 'error');
        return;
    }

    const stats = window.vendorStatsData;
    const content = `Vendor Management Statistics Report
Generated: ${new Date().toLocaleString()}

OVERVIEW
--------
Total Bookings: ${stats.total_bookings || 0}
Completed: ${stats.by_status?.completed || 0}
Pending: ${stats.by_status?.pending || 0}
Confirmed: ${stats.by_status?.confirmed || 0}
Cancelled: ${stats.by_status?.cancelled || 0}
Unique Vendors: ${stats.unique_vendors || 0}

FINANCIAL SUMMARY
-----------------
Total Spent: KES ${(stats.total_spent || 0).toLocaleString()}
Pending Payments: KES ${(stats.pending_payments || 0).toLocaleString()}
Average Rating: ${(stats.average_rating || 0).toFixed(1)} stars

BOOKINGS BY TYPE
----------------
${Object.entries(stats.by_type || {}).map(([type, count]) => `${type}: ${count}`).join('\n')}
`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vendor-stats-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showModalNotification('Statistics exported successfully', 'success');
}

function printVendorStats() {
    window.print();
}

/* ============================================
   CHECK AVAILABILITY MODAL
   ============================================ */

async function openAvailabilityModal() {
    const modal = document.getElementById('checkAvailabilityModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    await loadVendorsForAvailability();
    setupAvailabilityForm();
    
    // Set min date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('camStartDate').min = today;
    document.getElementById('camEndDate').min = today;
}

function closeAvailabilityModal() {
    const modal = document.getElementById('checkAvailabilityModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        document.getElementById('checkAvailabilityForm').reset();
        document.getElementById('camResults').style.display = 'none';
    }
}

async function loadVendorsForAvailability() {
    try {
        const response = await fetch('/api/teacher/vendors/search?per_page=100');
        const data = await handleCamApiResponse(response);

        if (data.success) {
            const select = document.getElementById('camVendorSelect');
            select.innerHTML = '<option value="">Choose a vendor...</option>';

            data.data.vendors.forEach(vendor => {
                const option = document.createElement('option');
                option.value = vendor.id;
                option.textContent = `${vendor.business_name} - ${vendor.business_type}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading vendors:', error);
    }
}

function setupAvailabilityForm() {
    const form = document.getElementById('checkAvailabilityForm');
    if (!form) return;

    // Date validation
    const startDate = document.getElementById('camStartDate');
    const endDate = document.getElementById('camEndDate');

    startDate.addEventListener('change', () => {
        endDate.min = startDate.value;
        if (endDate.value && endDate.value < startDate.value) {
            endDate.value = startDate.value;
        }
    });

    form.onsubmit = async (e) => {
        e.preventDefault();
        await handleCheckAvailability();
    };
}

async function handleCheckAvailability() {
    const vendorId = document.getElementById('camVendorSelect').value;
    const startDate = document.getElementById('camStartDate').value;
    const endDate = document.getElementById('camEndDate').value;

    if (!vendorId || !startDate || !endDate) {
        showModalNotification('Please fill in all fields', 'error');
        return;
    }

    const btn = document.querySelector('#checkAvailabilityForm button[type="submit"]');
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/teacher/vendors/availability', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vendor_id: parseInt(vendorId),
                start_date: startDate,
                end_date: endDate
            })
        });

        const data = await handleCamApiResponse(response);

        if (data.success) {
            displayAvailabilityResult(data.data);
        } else {
            showModalNotification(data.error || 'Failed to check availability', 'error');
        }
    } catch (error) {
        console.error('Error checking availability:', error);
        showModalNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function displayAvailabilityResult(result) {
    const resultsDiv = document.getElementById('camResults');
    const resultCard = document.getElementById('camResultCard');

    if (result.is_available) {
        resultCard.className = 'cam-result-card available';
        resultCard.innerHTML = `
            <div class="cam-result-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <h3>Vendor is Available!</h3>
            <p>${result.vendor_name} is available from ${formatCamDate(result.start_date)} to ${formatCamDate(result.end_date)}</p>
        `;
    } else {
        resultCard.className = 'cam-result-card unavailable';
        const conflicts = result.conflicting_bookings || [];
        const conflictInfo = conflicts.length > 0
            ? `<p style="margin-top: 15px; font-size: 13px;">Conflicts with ${conflicts.length} existing ${conflicts.length === 1 ? 'booking' : 'bookings'}</p>`
            : '';
        
        resultCard.innerHTML = `
            <div class="cam-result-icon">
                <i class="fas fa-times-circle"></i>
            </div>
            <h3>Vendor is Not Available</h3>
            <p>${result.vendor_name} is not available for the selected dates</p>
            ${conflictInfo}
        `;
    }

    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function handleCamApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'An error occurred');
    }
    return await response.json();
}

function formatCamDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/* ============================================
   EVENT LISTENERS FOR OVERLAY CLICKS
   ============================================ */

document.addEventListener('click', (e) => {
    if (e.target.id === 'bookingDetailsModal') closeBookingDetailsModal();
    if (e.target.id === 'vendorStatsModal') closeVendorStatsModal();
    if (e.target.id === 'checkAvailabilityModal') closeAvailabilityModal();
});

// Close on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeBookingDetailsModal();
        closeVendorStatsModal();
        closeAvailabilityModal();
    }
});