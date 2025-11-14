// ==================== MODAL MANAGEMENT ====================

// Global modal state
const ModalState = {
    currentPayment: null,
    completedPayments: [],
    generatedInvoice: null
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeModals();
    setupModalEventListeners();
});

function initializeModals() {
    console.log('Initializing modals...');
    
    // Set max date for report download
    const today = new Date().toISOString().split('T')[0];
    const reportStartDate = document.getElementById('report-start-date');
    const reportEndDate = document.getElementById('report-end-date');
    
    if (reportStartDate) reportStartDate.max = today;
    if (reportEndDate) reportEndDate.max = today;
}

function setupModalEventListeners() {
    // Invoice form submission
    const invoiceForm = document.getElementById('invoiceForm');
    if (invoiceForm) {
        invoiceForm.addEventListener('submit', handleInvoiceGeneration);
    }
    
    // Download report form submission
    const downloadForm = document.getElementById('downloadReportForm');
    if (downloadForm) {
        downloadForm.addEventListener('submit', handleReportDownload);
    }
    
    // Generate invoice from details modal
    const generateFromDetails = document.getElementById('generateInvoiceFromDetails');
    if (generateFromDetails) {
        generateFromDetails.addEventListener('click', function() {
            if (ModalState.currentPayment) {
                closeModal('paymentDetailsModal');
                window.selectedPaymentId = ModalState.currentPayment.id;
                openGenerateInvoiceModal();
            }
        });
    }
}

// ==================== MODAL CONTROL FUNCTIONS ====================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        
        // Reset forms
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

// ==================== PAYMENT DETAILS MODAL ====================
function openPaymentDetailsModal(payment) {
    ModalState.currentPayment = payment;
    
    // Populate payment information
    document.getElementById('detail-reference').textContent = payment.reference_number || 'N/A';
    document.getElementById('detail-transaction').textContent = payment.transaction_id || 'N/A';
    document.getElementById('detail-amount').textContent = formatCurrency(payment.amount);
    
    // Status badge
    const statusElement = document.getElementById('detail-status');
    statusElement.innerHTML = `<span class="status-badge status-${payment.status}">${payment.status}</span>`;
    
    document.getElementById('detail-method').textContent = capitalizeFirst(payment.payment_method || 'N/A');
    document.getElementById('detail-date').textContent = formatDate(payment.payment_date);
    document.getElementById('detail-processed').textContent = payment.processed_date ? 
        formatDate(payment.processed_date) : 'Not processed';
    
    // Payer information
    document.getElementById('detail-payer-name').textContent = payment.payer_name || 'N/A';
    document.getElementById('detail-payer-email').textContent = payment.payer_email || 'N/A';
    document.getElementById('detail-payer-phone').textContent = payment.payer_phone || 'N/A';
    
    // Booking information
    const booking = payment.service_booking || {};
    const trip = booking.trip || {};
    
    document.getElementById('detail-trip').textContent = trip.title || 'N/A';
    document.getElementById('detail-booking-type').textContent = 
        capitalizeFirst(booking.booking_type || 'N/A');
    document.getElementById('detail-booking-id').textContent = booking.id || 'N/A';
    document.getElementById('detail-description').textContent = 
        payment.description || booking.service_description || 'No description';
    
    // Show/hide generate invoice button based on status
    const generateBtn = document.getElementById('generateInvoiceFromDetails');
    if (payment.status === 'completed') {
        generateBtn.style.display = 'inline-flex';
    } else {
        generateBtn.style.display = 'none';
    }
    
    openModal('paymentDetailsModal');
}

// ==================== GENERATE INVOICE MODAL ====================
async function openGenerateInvoiceModal() {
    try {
        // Load completed payments for dropdown
        await loadCompletedPayments();
        
        // Pre-select payment if one was selected
        if (window.selectedPaymentId) {
            document.getElementById('invoice-payment-id').value = window.selectedPaymentId;
            window.selectedPaymentId = null;
        }
        
        openModal('generateInvoiceModal');
    } catch (error) {
        console.error('Error opening invoice modal:', error);
        showToast('Failed to load payment options', 'error');
    }
}

async function loadCompletedPayments() {
    try {
        const response = await fetch('/api/vendor/financials/booking-payments?status=completed&per_page=100', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load completed payments');
        }
        
        const data = await response.json();
        
        if (data.success) {
            ModalState.completedPayments = data.data.payments;
            populatePaymentDropdown(data.data.payments);
        }
    } catch (error) {
        console.error('Error loading completed payments:', error);
        throw error;
    }
}

function populatePaymentDropdown(payments) {
    const select = document.getElementById('invoice-payment-id');
    select.innerHTML = '<option value="">Select a completed payment...</option>';
    
    payments.forEach(payment => {
        const booking = payment.service_booking || {};
        const trip = booking.trip || {};
        const option = document.createElement('option');
        option.value = payment.id;
        option.textContent = `${payment.reference_number} - ${trip.title || 'N/A'} - ${formatCurrency(payment.amount)}`;
        select.appendChild(option);
    });
}

async function handleInvoiceGeneration(e) {
    e.preventDefault();
    
    const paymentId = document.getElementById('invoice-payment-id').value;
    const invoiceNumber = document.getElementById('invoice-number').value;
    const notes = document.getElementById('invoice-notes').value;
    
    if (!paymentId) {
        showToast('Please select a payment', 'warning');
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    try {
        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        
        const response = await fetch('/api/vendor/financials/invoices/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                payment_id: parseInt(paymentId),
                invoice_number: invoiceNumber || undefined,
                notes: notes || undefined
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to generate invoice');
        }
        
        if (data.success) {
            ModalState.generatedInvoice = data.data.invoice;
            
            showToast('Invoice generated successfully!', 'success');
            closeModal('generateInvoiceModal');
            
            // Show invoice preview
            setTimeout(() => {
                showInvoicePreview(data.data.invoice);
            }, 300);
        } else {
            throw new Error(data.message || 'Failed to generate invoice');
        }
    } catch (error) {
        console.error('Error generating invoice:', error);
        showToast(error.message || 'Failed to generate invoice', 'error');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// ==================== INVOICE PREVIEW MODAL ====================
function showInvoicePreview(invoiceData) {
    const content = document.getElementById('invoicePreviewContent');
    
    // Build invoice HTML
    const booking = invoiceData.booking_details || {};
    const vendor = invoiceData.vendor || {};
    const client = invoiceData.client || {};
    const totals = invoiceData.totals || {};
    
    content.innerHTML = `
        <div class="invoice-header">
            <div>
                <div class="invoice-logo">${vendor.business_name || 'Vendor'}</div>
                <p style="margin: 8px 0; color: var(--text-secondary);">
                    ${vendor.address || ''}<br>
                    ${vendor.contact_email || ''}<br>
                    ${vendor.contact_phone || ''}
                </p>
            </div>
            <div class="invoice-number">
                <h2>INVOICE</h2>
                <p><strong>Invoice #:</strong> ${invoiceData.invoice_number}</p>
                <p><strong>Date:</strong> ${formatDate(invoiceData.invoice_date)}</p>
                <p><strong>Status:</strong> <span class="status-badge status-${invoiceData.status}">${invoiceData.status}</span></p>
            </div>
        </div>
        
        <div class="invoice-parties">
            <div class="invoice-party">
                <h3>Bill To</h3>
                <p><strong>${client.name || 'N/A'}</strong></p>
                <p>${client.email || ''}</p>
                <p>${client.phone || ''}</p>
            </div>
            <div class="invoice-party">
                <h3>Service Details</h3>
                <p><strong>Trip:</strong> ${booking.trip_title || 'N/A'}</p>
                <p><strong>Type:</strong> ${capitalizeFirst(booking.booking_type || 'N/A')}</p>
                <p><strong>Booking ID:</strong> #${booking.booking_id || 'N/A'}</p>
            </div>
        </div>
        
        <table class="invoice-table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align: center;">Quantity</th>
                    <th style="text-align: right;">Unit Price</th>
                    <th style="text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                ${invoiceData.line_items.map(item => `
                    <tr>
                        <td>${item.description}</td>
                        <td style="text-align: center;">${item.quantity}</td>
                        <td style="text-align: right;">${formatCurrency(item.unit_price)}</td>
                        <td style="text-align: right;">${formatCurrency(item.total)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        
        <div class="invoice-total">
            <div class="invoice-total-row">
                <span>Subtotal:</span>
                <span>${formatCurrency(totals.subtotal)}</span>
            </div>
            ${totals.tax > 0 ? `
                <div class="invoice-total-row">
                    <span>Tax:</span>
                    <span>${formatCurrency(totals.tax)}</span>
                </div>
            ` : ''}
            <div class="invoice-total-row grand-total">
                <span>Total:</span>
                <span>${formatCurrency(totals.total)}</span>
            </div>
            <div class="invoice-total-row" style="color: var(--success-color);">
                <span>Amount Paid:</span>
                <span>${formatCurrency(totals.amount_paid)}</span>
            </div>
            ${totals.balance_due > 0 ? `
                <div class="invoice-total-row" style="color: var(--danger-color);">
                    <span>Balance Due:</span>
                    <span>${formatCurrency(totals.balance_due)}</span>
                </div>
            ` : ''}
        </div>
        
        ${invoiceData.notes ? `
            <div class="invoice-notes">
                <h4>Notes</h4>
                <p>${invoiceData.notes}</p>
            </div>
        ` : ''}
        
        ${invoiceData.payment_details ? `
            <div class="invoice-notes">
                <h4>Payment Information</h4>
                <p>
                    <strong>Payment Method:</strong> ${capitalizeFirst(invoiceData.payment_details.payment_method)}<br>
                    <strong>Transaction ID:</strong> ${invoiceData.payment_details.transaction_id || 'N/A'}<br>
                    <strong>Payment Date:</strong> ${formatDate(invoiceData.payment_details.payment_date)}
                </p>
            </div>
        ` : ''}
    `;
    
    openModal('invoicePreviewModal');
}

function printInvoice() {
    window.print();
}

function downloadInvoice() {
    // In a real implementation, this would generate a PDF
    showToast('PDF generation feature coming soon!', 'info');
    
    // For now, we can trigger the browser's print dialog with save as PDF option
    setTimeout(() => {
        window.print();
    }, 500);
}

// ==================== DOWNLOAD REPORT MODAL ====================
function openDownloadReportModal() {
    // Pre-fill with current filter values if applicable
    const currentStatus = FinancialsState.currentStatus;
    if (currentStatus) {
        document.getElementById('report-status').value = currentStatus;
    }
    
    if (FinancialsState.currentPeriod === 'custom') {
        document.getElementById('report-start-date').value = FinancialsState.startDate || '';
        document.getElementById('report-end-date').value = FinancialsState.endDate || '';
    }
    
    openModal('downloadReportModal');
}

async function handleReportDownload(e) {
    e.preventDefault();
    
    const format = document.getElementById('report-format').value;
    const status = document.getElementById('report-status').value;
    const startDate = document.getElementById('report-start-date').value;
    const endDate = document.getElementById('report-end-date').value;
    
    // Validate date range if provided
    if (startDate && endDate) {
        if (new Date(startDate) > new Date(endDate)) {
            showToast('Start date cannot be after end date', 'error');
            return;
        }
        
        // Check if range exceeds 2 years
        const daysDiff = (new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24);
        if (daysDiff > 730) {
            showToast('Date range cannot exceed 2 years', 'error');
            return;
        }
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    try {
        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        
        // Build URL
        let url = `/api/vendor/financials/payment-history/download?format=${format}`;
        
        if (status) {
            url += `&status=${status}`;
        }
        
        if (startDate) {
            url += `&start_date=${startDate}`;
        }
        
        if (endDate) {
            url += `&end_date=${endDate}`;
        }
        
        // Trigger download
        window.location.href = url;
        
        showToast('Download started successfully!', 'success');
        
        setTimeout(() => {
            closeModal('downloadReportModal');
        }, 1000);
        
    } catch (error) {
        console.error('Error downloading report:', error);
        showToast(error.message || 'Failed to download report', 'error');
    } finally {
        setTimeout(() => {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }, 1000);
    }
}

// ==================== UTILITY FUNCTIONS ====================
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount || 0);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const id = 'toast-' + Date.now();
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const titles = {
        success: 'Success',
        error: 'Error',
        warning: 'Warning',
        info: 'Information'
    };
    
    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${icons[type]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${titles[type]}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast('${id}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        closeToast(id);
    }, 5000);
}

function closeToast(id) {
    const toast = document.getElementById(id);
    if (toast) {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// Make functions globally accessible
window.openModal = openModal;
window.closeModal = closeModal;
window.openPaymentDetailsModal = openPaymentDetailsModal;
window.openGenerateInvoiceModal = openGenerateInvoiceModal;
window.openDownloadReportModal = openDownloadReportModal;
window.printInvoice = printInvoice;
window.downloadInvoice = downloadInvoice;
window.closeToast = closeToast;

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        const modal = e.target.closest('.modal');
        if (modal) {
            closeModal(modal.id);
        }
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.active');
        if (activeModal) {
            closeModal(activeModal.id);
        }
    }
});