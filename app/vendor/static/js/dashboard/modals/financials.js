/**
 * Vendor Financials Modal Functions
 * Handles all modal dialogs for financials
 */

/**
 * Show payment details modal
 */
function vpFinancialsShowPaymentDetailsModal(invoice) {
    const modal = vpFinancialsCreateModal('payment-details', 'Payment Details');
    
    const content = `
        <div class="vp-modal-invoice">
            <!-- Invoice Header -->
            <div class="vp-invoice-header">
                <div class="vp-invoice-logo">
                    <i class="fas fa-file-invoice"></i>
                    <h2>INVOICE</h2>
                </div>
                <div class="vp-invoice-number">
                    <strong>Invoice #:</strong> ${vpFinancialsEscapeHtml(invoice.invoice_number)}
                    <br>
                    <strong>Date:</strong> ${vpFinancialsFormatDate(invoice.invoice_date)}
                    <br>
                    <span class="vp-status-badge vp-status-${invoice.status}">
                        <i class="fas fa-circle"></i>
                        ${invoice.status}
                    </span>
                </div>
            </div>

            <!-- Vendor & Client Info -->
            <div class="vp-invoice-parties">
                <div class="vp-invoice-party">
                    <h4><i class="fas fa-building"></i> From</h4>
                    <p><strong>${vpFinancialsEscapeHtml(invoice.vendor.business_name)}</strong></p>
                    <p>${vpFinancialsEscapeHtml(invoice.vendor.contact_email)}</p>
                    <p>${vpFinancialsEscapeHtml(invoice.vendor.contact_phone)}</p>
                    ${invoice.vendor.address ? `<p>${vpFinancialsEscapeHtml(invoice.vendor.address)}</p>` : ''}
                </div>
                <div class="vp-invoice-party">
                    <h4><i class="fas fa-user"></i> Bill To</h4>
                    <p><strong>${vpFinancialsEscapeHtml(invoice.client.name || 'N/A')}</strong></p>
                    <p>${vpFinancialsEscapeHtml(invoice.client.email || 'N/A')}</p>
                    <p>${vpFinancialsEscapeHtml(invoice.client.phone || 'N/A')}</p>
                </div>
            </div>

            <!-- Booking Details -->
            ${invoice.booking_details && invoice.booking_details.trip_title ? `
                <div class="vp-invoice-section">
                    <h4><i class="fas fa-map-marked-alt"></i> Service Details</h4>
                    <div class="vp-invoice-detail-grid">
                        <div class="vp-invoice-detail">
                            <span class="vp-detail-label">Trip:</span>
                            <span class="vp-detail-value">${vpFinancialsEscapeHtml(invoice.booking_details.trip_title)}</span>
                        </div>
                        <div class="vp-invoice-detail">
                            <span class="vp-detail-label">Service Type:</span>
                            <span class="vp-detail-value" style="text-transform: capitalize;">${vpFinancialsEscapeHtml(invoice.booking_details.booking_type || 'N/A')}</span>
                        </div>
                        ${invoice.booking_details.service_dates?.start ? `
                            <div class="vp-invoice-detail">
                                <span class="vp-detail-label">Service Period:</span>
                                <span class="vp-detail-value">${vpFinancialsFormatDate(invoice.booking_details.service_dates.start)} - ${vpFinancialsFormatDate(invoice.booking_details.service_dates.end)}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}

            <!-- Line Items -->
            <div class="vp-invoice-section">
                <table class="vp-invoice-table">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th style="text-align: center;">Qty</th>
                            <th style="text-align: right;">Unit Price</th>
                            <th style="text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${invoice.line_items.map(item => `
                            <tr>
                                <td>${vpFinancialsEscapeHtml(item.description)}</td>
                                <td style="text-align: center;">${item.quantity}</td>
                                <td style="text-align: right;">${vpFinancialsFormatCurrency(item.unit_price)}</td>
                                <td style="text-align: right;"><strong>${vpFinancialsFormatCurrency(item.total)}</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>

            <!-- Totals -->
            <div class="vp-invoice-totals">
                <div class="vp-invoice-total-row">
                    <span>Subtotal:</span>
                    <span>${vpFinancialsFormatCurrency(invoice.totals.subtotal)}</span>
                </div>
                ${invoice.totals.tax > 0 ? `
                    <div class="vp-invoice-total-row">
                        <span>Tax:</span>
                        <span>${vpFinancialsFormatCurrency(invoice.totals.tax)}</span>
                    </div>
                ` : ''}
                <div class="vp-invoice-total-row vp-invoice-grand-total">
                    <span>Total:</span>
                    <span>${vpFinancialsFormatCurrency(invoice.totals.total)}</span>
                </div>
                <div class="vp-invoice-total-row" style="color: #28a745;">
                    <span>Amount Paid:</span>
                    <span>${vpFinancialsFormatCurrency(invoice.totals.amount_paid)}</span>
                </div>
                ${invoice.totals.balance_due > 0 ? `
                    <div class="vp-invoice-total-row" style="color: #dc3545;">
                        <span>Balance Due:</span>
                        <span>${vpFinancialsFormatCurrency(invoice.totals.balance_due)}</span>
                    </div>
                ` : ''}
            </div>

            <!-- Payment Details -->
            ${invoice.payment_details ? `
                <div class="vp-invoice-section">
                    <h4><i class="fas fa-credit-card"></i> Payment Information</h4>
                    <div class="vp-invoice-detail-grid">
                        <div class="vp-invoice-detail">
                            <span class="vp-detail-label">Reference Number:</span>
                            <span class="vp-detail-value">${vpFinancialsEscapeHtml(invoice.payment_details.reference_number || 'N/A')}</span>
                        </div>
                        <div class="vp-invoice-detail">
                            <span class="vp-detail-label">Transaction ID:</span>
                            <span class="vp-detail-value">${vpFinancialsEscapeHtml(invoice.payment_details.transaction_id || 'N/A')}</span>
                        </div>
                        <div class="vp-invoice-detail">
                            <span class="vp-detail-label">Payment Method:</span>
                            <span class="vp-detail-value" style="text-transform: capitalize;">${vpFinancialsEscapeHtml(invoice.payment_details.payment_method || 'N/A')}</span>
                        </div>
                        <div class="vp-invoice-detail">
                            <span class="vp-detail-label">Payment Date:</span>
                            <span class="vp-detail-value">${vpFinancialsFormatDate(invoice.payment_details.payment_date)}</span>
                        </div>
                    </div>
                </div>
            ` : ''}

            <!-- Notes -->
            ${invoice.notes ? `
                <div class="vp-invoice-section">
                    <h4><i class="fas fa-sticky-note"></i> Notes</h4>
                    <p class="vp-invoice-notes">${vpFinancialsEscapeHtml(invoice.notes)}</p>
                </div>
            ` : ''}

            <!-- Actions -->
            <div class="vp-invoice-actions">
                <button class="vp-btn vp-btn-secondary" onclick="vpFinancialsPrintInvoice()">
                    <i class="fas fa-print"></i> Print
                </button>
                <button class="vp-btn vp-btn-primary" onclick="vpFinancialsDownloadInvoice('${invoice.invoice_number}')">
                    <i class="fas fa-download"></i> Download PDF
                </button>
            </div>
        </div>
    `;
    
    modal.setContent(content);
    modal.show();
}

/**
 * Show download history modal
 */
function vpFinancialsShowDownloadModal() {
    const modal = vpFinancialsCreateModal('download-history', 'Download Payment History');
    
    const content = `
        <form id="vpDownloadForm" class="vp-modal-form">
            <div class="vp-form-group">
                <label class="vp-form-label">
                    <i class="fas fa-file-alt"></i> File Format
                </label>
                <select id="vpDownloadFormat" class="vp-form-control" required>
                    <option value="csv">CSV (Excel Compatible)</option>
                    <option value="json">JSON</option>
                </select>
                <small class="vp-form-help">Choose the format for your download</small>
            </div>

            <div class="vp-form-group">
                <label class="vp-form-label">
                    <i class="fas fa-calendar-alt"></i> Date Range
                </label>
                <div class="vp-form-row">
                    <input type="date" id="vpDownloadStartDate" class="vp-form-control" placeholder="Start Date">
                    <input type="date" id="vpDownloadEndDate" class="vp-form-control" placeholder="End Date">
                </div>
                <small class="vp-form-help">Leave empty to download all history</small>
            </div>

            <div class="vp-form-group">
                <label class="vp-form-label">
                    <i class="fas fa-filter"></i> Payment Status
                </label>
                <select id="vpDownloadStatus" class="vp-form-control">
                    <option value="">All Statuses</option>
                    <option value="completed">Completed</option>
                    <option value="pending">Pending</option>
                    <option value="processing">Processing</option>
                    <option value="failed">Failed</option>
                    <option value="refunded">Refunded</option>
                </select>
            </div>

            <div class="vp-modal-actions">
                <button type="button" class="vp-btn vp-btn-secondary" onclick="vpFinancialsCloseModal()">
                    Cancel
                </button>
                <button type="submit" class="vp-btn vp-btn-primary">
                    <i class="fas fa-download"></i> Download
                </button>
            </div>
        </form>
    `;
    
    modal.setContent(content);
    modal.show();
    
    // Handle form submission
    document.getElementById('vpDownloadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        vpFinancialsExecuteDownload();
    });
}

/**
 * Execute download
 */
async function vpFinancialsExecuteDownload() {
    const format = document.getElementById('vpDownloadFormat').value;
    const startDate = document.getElementById('vpDownloadStartDate').value;
    const endDate = document.getElementById('vpDownloadEndDate').value;
    const status = document.getElementById('vpDownloadStatus').value;
    
    const params = new URLSearchParams({ format });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (status) params.append('status', status);
    
    try {
        vpFinancialsShowToast('info', 'Downloading', 'Preparing your file...');
        
        const response = await fetch(`/api/vendor/financials/payment-history/download?${params}`, {
            method: 'GET',
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Download failed');
        }
        
        // Get filename from headers or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `payment_history_${new Date().toISOString().split('T')[0]}.${format}`;
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) filename = filenameMatch[1];
        }
        
        // Download file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        vpFinancialsShowToast('success', 'Success', 'Payment history downloaded successfully');
        vpFinancialsCloseModal();
        
    } catch (error) {
        console.error('Download error:', error);
        vpFinancialsShowToast('error', 'Error', error.message || 'Failed to download payment history');
    }
}

/**
 * Show generate report modal
 */
function vpFinancialsShowReportModal() {
    const modal = vpFinancialsCreateModal('generate-report', 'Generate Financial Report');
    
    const content = `
        <form id="vpReportForm" class="vp-modal-form">
            <div class="vp-form-group">
                <label class="vp-form-label">
                    <i class="fas fa-calendar"></i> Report Period
                </label>
                <select id="vpReportPeriod" class="vp-form-control" required onchange="vpFinancialsToggleCustomDates(this.value)">
                    <option value="weekly">Last 7 Days</option>
                    <option value="monthly" selected>Last 30 Days</option>
                    <option value="quarterly">Last 3 Months</option>
                    <option value="yearly">Last Year</option>
                    <option value="custom">Custom Range</option>
                </select>
            </div>

            <div id="vpReportCustomDates" class="vp-form-group" style="display: none;">
                <label class="vp-form-label">
                    <i class="fas fa-calendar-alt"></i> Custom Date Range
                </label>
                <div class="vp-form-row">
                    <input type="date" id="vpReportStartDate" class="vp-form-control" placeholder="Start Date">
                    <input type="date" id="vpReportEndDate" class="vp-form-control" placeholder="End Date">
                </div>
            </div>

            <div class="vp-form-group">
                <label class="vp-form-label">
                    <i class="fas fa-chart-line"></i> Group By
                </label>
                <select id="vpReportGroupBy" class="vp-form-control" required>
                    <option value="day">Daily</option>
                    <option value="month" selected>Monthly</option>
                </select>
                <small class="vp-form-help">How to group revenue data in the report</small>
            </div>

            <div class="vp-form-group">
                <label class="vp-form-label">
                    <i class="fas fa-list-check"></i> Include Sections
                </label>
                <div class="vp-checkbox-group">
                    <label class="vp-checkbox-label">
                        <input type="checkbox" checked> Overall Statistics
                    </label>
                    <label class="vp-checkbox-label">
                        <input type="checkbox" checked> Revenue by Service Type
                    </label>
                    <label class="vp-checkbox-label">
                        <input type="checkbox" checked> Time Series Data
                    </label>
                    <label class="vp-checkbox-label">
                        <input type="checkbox" checked> Top Bookings
                    </label>
                    <label class="vp-checkbox-label">
                        <input type="checkbox" checked> Payment Statistics
                    </label>
                </div>
            </div>

            <div class="vp-modal-actions">
                <button type="button" class="vp-btn vp-btn-secondary" onclick="vpFinancialsCloseModal()">
                    Cancel
                </button>
                <button type="submit" class="vp-btn vp-btn-primary">
                    <i class="fas fa-file-pdf"></i> Generate Report
                </button>
            </div>
        </form>
    `;
    
    modal.setContent(content);
    modal.show();
    
    // Handle form submission
    document.getElementById('vpReportForm').addEventListener('submit', function(e) {
        e.preventDefault();
        vpFinancialsExecuteGenerateReport();
    });
}

/**
 * Toggle custom date fields
 */
function vpFinancialsToggleCustomDates(period) {
    const customDates = document.getElementById('vpReportCustomDates');
    if (customDates) {
        customDates.style.display = period === 'custom' ? 'block' : 'none';
        
        if (period === 'custom') {
            document.getElementById('vpReportStartDate').required = true;
            document.getElementById('vpReportEndDate').required = true;
        } else {
            document.getElementById('vpReportStartDate').required = false;
            document.getElementById('vpReportEndDate').required = false;
        }
    }
}

/**
 * Execute generate report
 */
async function vpFinancialsExecuteGenerateReport() {
    const period = document.getElementById('vpReportPeriod').value;
    const groupBy = document.getElementById('vpReportGroupBy').value;
    
    const params = new URLSearchParams({ period, group_by: groupBy });
    
    if (period === 'custom') {
        const startDate = document.getElementById('vpReportStartDate').value;
        const endDate = document.getElementById('vpReportEndDate').value;
        
        if (!startDate || !endDate) {
            vpFinancialsShowToast('warning', 'Missing Dates', 'Please select start and end dates');
            return;
        }
        
        params.append('start_date', startDate);
        params.append('end_date', endDate);
    }
    
    try {
        vpFinancialsShowToast('info', 'Generating', 'Creating your report...');
        
        const response = await fetch(`/api/vendor/financials/revenue-report?${params}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });
        
        const data = await vpFinancialsHandleResponse(response);
        
        if (data.success) {
            vpFinancialsShowToast('success', 'Success', 'Report generated successfully');
            vpFinancialsCloseModal();
            
            // You could show the report in a new modal or download it
            vpFinancialsShowReportPreview(data.data);
        } else {
            throw new Error(data.message || 'Failed to generate report');
        }
        
    } catch (error) {
        console.error('Report generation error:', error);
        vpFinancialsShowToast('error', 'Error', error.message || 'Failed to generate report');
    }
}

/**
 * Show report preview modal
 */
function vpFinancialsShowReportPreview(reportData) {
    const modal = vpFinancialsCreateModal('report-preview', 'Financial Report Preview', 'large');
    
    const period = reportData.period || {};
    const stats = reportData.overall_statistics || {};
    
    const content = `
        <div class="vp-report-preview">
            <div class="vp-report-header">
                <h3>Financial Report</h3>
                <p>Period: ${vpFinancialsFormatDate(period.start_date)} - ${vpFinancialsFormatDate(period.end_date)}</p>
            </div>

            <div class="vp-report-stats">
                <div class="vp-report-stat">
                    <div class="vp-report-stat-label">Total Revenue</div>
                    <div class="vp-report-stat-value">${vpFinancialsFormatCurrency(stats.total_revenue)}</div>
                </div>
                <div class="vp-report-stat">
                    <div class="vp-report-stat-label">Transactions</div>
                    <div class="vp-report-stat-value">${stats.total_transactions || 0}</div>
                </div>
                <div class="vp-report-stat">
                    <div class="vp-report-stat-label">Average Transaction</div>
                    <div class="vp-report-stat-value">${vpFinancialsFormatCurrency(stats.average_transaction)}</div>
                </div>
                <div class="vp-report-stat">
                    <div class="vp-report-stat-label">Pending Revenue</div>
                    <div class="vp-report-stat-value">${vpFinancialsFormatCurrency(stats.pending_revenue)}</div>
                </div>
            </div>

            <div class="vp-report-actions">
                <button class="vp-btn vp-btn-secondary" onclick="vpFinancialsPrintReport()">
                    <i class="fas fa-print"></i> Print
                </button>
                <button class="vp-btn vp-btn-primary" onclick="vpFinancialsDownloadReport()">
                    <i class="fas fa-download"></i> Download PDF
                </button>
            </div>
        </div>
    `;
    
    modal.setContent(content);
    modal.show();
}

/**
 * Show custom date modal for revenue chart
 */
async function vpFinancialsShowCustomDateModal() {
    const modal = vpFinancialsCreateModal('custom-dates', 'Select Date Range');
    
    const content = `
        <form id="vpCustomDateForm" class="vp-modal-form">
            <div class="vp-form-group">
                <label class="vp-form-label">
                    <i class="fas fa-calendar-alt"></i> Date Range
                </label>
                <div class="vp-form-row">
                    <input type="date" id="vpRevenueStartDate" class="vp-form-control" required>
                    <input type="date" id="vpRevenueEndDate" class="vp-form-control" required>
                </div>
                <small class="vp-form-help">Select start and end dates for the report</small>
            </div>

            <div class="vp-modal-actions">
                <button type="button" class="vp-btn vp-btn-secondary" onclick="vpFinancialsCloseModal(); document.getElementById('vpRevenuePeriod').value='monthly'; vpFinancialsLoadRevenueReport();">
                    Cancel
                </button>
                <button type="submit" class="vp-btn vp-btn-primary">
                    <i class="fas fa-check"></i> Apply
                </button>
            </div>
        </form>
    `;
    
    modal.setContent(content);
    modal.show();
    
    document.getElementById('vpCustomDateForm').addEventListener('submit', function(e) {
        e.preventDefault();
        vpFinancialsCloseModal();
        vpFinancialsLoadRevenueReport();
    });
}

/**
 * Print invoice
 */
function vpFinancialsPrintInvoice() {
    window.print();
}

/**
 * Download invoice as PDF
 */
function vpFinancialsDownloadInvoice(invoiceNumber) {
    vpFinancialsShowToast('info', 'Coming Soon', 'PDF download feature will be available soon');
}

/**
 * Print report
 */
function vpFinancialsPrintReport() {
    window.print();
}

/**
 * Download report
 */
function vpFinancialsDownloadReport() {
    vpFinancialsShowToast('info', 'Coming Soon', 'PDF download feature will be available soon');
}

/**
 * Create modal
 */
function vpFinancialsCreateModal(id, title, size = 'medium') {
    const existingModal = document.getElementById(`vpModal-${id}`);
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = `vpModal-${id}`;
    modal.className = `vp-modal-overlay`;
    modal.innerHTML = `
        <div class="vp-modal vp-modal-${size}">
            <div class="vp-modal-header">
                <h3 class="vp-modal-title">${title}</h3>
                <button class="vp-modal-close" onclick="vpFinancialsCloseModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="vp-modal-body" id="vpModalBody-${id}">
                <!-- Content will be inserted here -->
            </div>
        </div>
    `;
    
    const container = document.getElementById('vpFinancialsModalsContainer');
    if (container) {
        container.appendChild(modal);
    } else {
        document.body.appendChild(modal);
    }
    
    // Close on overlay click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            vpFinancialsCloseModal();
        }
    });
    
    return {
        element: modal,
        show: function() {
            setTimeout(() => modal.classList.add('vp-modal-show'), 10);
        },
        hide: function() {
            modal.classList.remove('vp-modal-show');
            setTimeout(() => modal.remove(), 300);
        },
        setContent: function(content) {
            const body = document.getElementById(`vpModalBody-${id}`);
            if (body) body.innerHTML = content;
        }
    };
}

/**
 * Close modal
 */
function vpFinancialsCloseModal() {
    const modals = document.querySelectorAll('.vp-modal-overlay');
    modals.forEach(modal => {
        modal.classList.remove('vp-modal-show');
        setTimeout(() => modal.remove(), 300);
    });
}