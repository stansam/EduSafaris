/**
 * Vendor Financials Dashboard JavaScript
 * Handles all financial data fetching, display, and interactions
 */

// Global state
const vpFinancialsState = {
    currentPage: 1,
    perPage: 20,
    totalPages: 0,
    filters: {
        status: '',
        startDate: '',
        endDate: ''
    },
    revenueChart: null,
    isLoading: false
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('vendorFinancials')) {
        vpFinancialsInit();
    }
});

/**
 * Initialize financials dashboard
 */
function vpFinancialsInit() {
    console.log('Initializing vendor financials dashboard...');
    
    // Load all data
    vpFinancialsLoadSummary();
    vpFinancialsLoadRevenueReport();
    vpFinancialsLoadPayments();
    vpFinancialsLoadPaymentStats();
}

/**
 * Load financial summary data
 */
async function vpFinancialsLoadSummary() {
    try {
        const period = document.getElementById('vpRevenuePeriod')?.value || 'monthly';
        const response = await fetch(`/api/vendor/financials/payment-statistics?period=${period}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        const data = await vpFinancialsHandleResponse(response);
        
        if (data.success) {
            vpFinancialsDisplaySummary(data.data);
        } else {
            throw new Error(data.message || 'Failed to load summary');
        }
    } catch (error) {
        console.error('Error loading summary:', error);
        vpFinancialsShowToast('error', 'Error', 'Failed to load financial summary');
        vpFinancialsDisplaySummaryError();
    }
}

/**
 * Display summary data
 */
function vpFinancialsDisplaySummary(data) {
    const metrics = data.metrics || {};
    const statusBreakdown = data.status_breakdown || [];
    
    // Total Revenue
    const completedStatus = statusBreakdown.find(s => s.status === 'completed');
    const totalRevenue = completedStatus ? completedStatus.total_amount : 0;
    document.getElementById('vpTotalRevenue').innerHTML = 
        `${vpFinancialsFormatCurrency(totalRevenue)}`;
    
    // Pending Payments
    const pendingStatus = statusBreakdown.find(s => s.status === 'pending');
    const pendingAmount = pendingStatus ? pendingStatus.total_amount : 0;
    const pendingCount = pendingStatus ? pendingStatus.count : 0;
    document.getElementById('vpPendingAmount').innerHTML = 
        `${vpFinancialsFormatCurrency(pendingAmount)}`;
    document.getElementById('vpPendingCount').textContent = 
        `${pendingCount} pending transaction${pendingCount !== 1 ? 's' : ''}`;
    
    // Total Transactions
    document.getElementById('vpTotalTransactions').innerHTML = 
        `${metrics.total_payments || 0}`;
    document.getElementById('vpTransactionPeriod').textContent = 
        `Last ${vpFinancialsGetPeriodLabel()}`;
    
    // Average Transaction
    document.getElementById('vpAvgTransaction').innerHTML = 
        `${vpFinancialsFormatCurrency(metrics.average_payment_value || 0)}`;
    document.getElementById('vpSuccessRate').textContent = 
        `${metrics.success_rate || 0}% success rate`;
}

/**
 * Display summary error state
 */
function vpFinancialsDisplaySummaryError() {
    const elements = [
        'vpTotalRevenue', 'vpPendingAmount', 
        'vpTotalTransactions', 'vpAvgTransaction'
    ];
    
    elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '<span style="color: #dc3545;">Error</span>';
    });
}

/**
 * Load revenue report and chart
 */
async function vpFinancialsLoadRevenueReport() {
    try {
        const periodSelect = document.getElementById('vpRevenuePeriod');
        const period = periodSelect?.value || 'monthly';
        
        // Show loader
        const chartLoader = document.getElementById('vpChartLoader');
        const chartError = document.getElementById('vpChartError');
        if (chartLoader) chartLoader.style.display = 'flex';
        if (chartError) chartError.style.display = 'none';
        
        let url = `/api/vendor/financials/revenue-report?period=${period}`;
        
        // Add custom date range if selected
        if (period === 'custom') {
            const startDate = document.getElementById('vpRevenueStartDate')?.value;
            const endDate = document.getElementById('vpRevenueEndDate')?.value;
            
            if (!startDate || !endDate) {
                await vpFinancialsShowCustomDateModal();
                return;
            }
            
            url += `&start_date=${startDate}&end_date=${endDate}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        const data = await vpFinancialsHandleResponse(response);
        
        if (data.success) {
            vpFinancialsDisplayRevenueChart(data.data);
            vpFinancialsDisplayRevenueBreakdown(data.data);
            vpFinancialsDisplayTopBookings(data.data);
        } else {
            throw new Error(data.message || 'Failed to load revenue report');
        }
    } catch (error) {
        console.error('Error loading revenue report:', error);
        vpFinancialsShowToast('error', 'Error', 'Failed to load revenue report');
        
        const chartLoader = document.getElementById('vpChartLoader');
        const chartError = document.getElementById('vpChartError');
        if (chartLoader) chartLoader.style.display = 'none';
        if (chartError) chartError.style.display = 'flex';
    }
}

/**
 * Display revenue chart
 */
function vpFinancialsDisplayRevenueChart(data) {
    const chartLoader = document.getElementById('vpChartLoader');
    if (chartLoader) chartLoader.style.display = 'none';
    
    const ctx = document.getElementById('vpRevenueChart');
    if (!ctx) return;
    
    const timeSeries = data.time_series || [];
    const labels = timeSeries.map(item => item.period);
    const revenues = timeSeries.map(item => item.revenue);
    const transactions = timeSeries.map(item => item.transactions);
    
    // Destroy existing chart
    if (vpFinancialsState.revenueChart) {
        vpFinancialsState.revenueChart.destroy();
    }
    
    // Create new chart
    vpFinancialsState.revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue (KES)',
                data: revenues,
                borderColor: '#4a90e2',
                backgroundColor: 'rgba(74, 144, 226, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }, {
                label: 'Transactions',
                data: transactions,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.datasetIndex === 0) {
                                label += vpFinancialsFormatCurrency(context.parsed.y);
                            } else {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        callback: function(value) {
                            return 'KES ' + value.toLocaleString();
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            }
        }
    });
}

/**
 * Display revenue breakdown by service type
 */
function vpFinancialsDisplayRevenueBreakdown(data) {
    const container = document.getElementById('vpServiceTypeBreakdown');
    if (!container) return;
    
    const breakdown = data.revenue_by_service_type || [];
    
    if (breakdown.length === 0) {
        container.innerHTML = `
            <div class="vp-loading-placeholder">
                <i class="fas fa-chart-pie" style="font-size: 48px; color: #dee2e6; margin-bottom: 15px;"></i>
                <p>No revenue data available</p>
            </div>
        `;
        return;
    }
    
    const icons = {
        transportation: 'fa-bus',
        accommodation: 'fa-hotel',
        activity: 'fa-hiking',
        default: 'fa-concierge-bell'
    };
    
    const html = breakdown.map(item => {
        const icon = icons[item.service_type] || icons.default;
        return `
            <div class="vp-breakdown-item">
                <div class="vp-breakdown-icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="vp-breakdown-info">
                    <div class="vp-breakdown-type">${item.service_type}</div>
                    <div class="vp-breakdown-count">${item.transaction_count} transaction${item.transaction_count !== 1 ? 's' : ''}</div>
                </div>
                <div class="vp-breakdown-amount">
                    ${vpFinancialsFormatCurrency(item.revenue)}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

/**
 * Display top bookings
 */
function vpFinancialsDisplayTopBookings(data) {
    const container = document.getElementById('vpTopBookings');
    if (!container) return;
    
    const topBookings = data.top_bookings || [];
    
    if (topBookings.length === 0) {
        container.innerHTML = `
            <div class="vp-loading-placeholder">
                <i class="fas fa-trophy" style="font-size: 48px; color: #dee2e6; margin-bottom: 15px;"></i>
                <p>No booking data available</p>
            </div>
        `;
        return;
    }
    
    const html = topBookings.slice(0, 5).map((booking, index) => {
        const rank = index + 1;
        const rankClass = rank <= 3 ? `vp-rank-${rank}` : '';
        return `
            <div class="vp-top-booking-item">
                <div class="vp-booking-rank ${rankClass}">${rank}</div>
                <div class="vp-booking-info">
                    <div class="vp-booking-title">${vpFinancialsEscapeHtml(booking.trip_title || 'N/A')}</div>
                    <div class="vp-booking-type">${booking.booking_type}</div>
                </div>
                <div class="vp-booking-revenue">
                    ${vpFinancialsFormatCurrency(booking.revenue)}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

/**
 * Load payments list
 */
async function vpFinancialsLoadPayments() {
    if (vpFinancialsState.isLoading) return;
    
    try {
        vpFinancialsState.isLoading = true;
        
        // Build query parameters
        const params = new URLSearchParams({
            page: vpFinancialsState.currentPage,
            per_page: vpFinancialsState.perPage
        });
        
        if (vpFinancialsState.filters.status) {
            params.append('status', vpFinancialsState.filters.status);
        }
        if (vpFinancialsState.filters.startDate) {
            params.append('start_date', vpFinancialsState.filters.startDate);
        }
        if (vpFinancialsState.filters.endDate) {
            params.append('end_date', vpFinancialsState.filters.endDate);
        }
        
        const response = await fetch(`/api/vendor/financials/booking-payments?${params}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        const data = await vpFinancialsHandleResponse(response);
        
        if (data.success) {
            vpFinancialsDisplayPayments(data.data);
        } else {
            throw new Error(data.message || 'Failed to load payments');
        }
    } catch (error) {
        console.error('Error loading payments:', error);
        vpFinancialsShowToast('error', 'Error', 'Failed to load payments');
        vpFinancialsDisplayPaymentsError();
    } finally {
        vpFinancialsState.isLoading = false;
    }
}

/**
 * Display payments in table
 */
function vpFinancialsDisplayPayments(data) {
    const tbody = document.getElementById('vpPaymentsTableBody');
    if (!tbody) return;
    
    const payments = data.payments || [];
    const pagination = data.pagination || {};
    
    if (payments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px 20px;">
                    <i class="fas fa-inbox" style="font-size: 48px; color: #dee2e6; margin-bottom: 15px;"></i>
                    <p style="color: #6c757d; margin: 0;">No payments found</p>
                </td>
            </tr>
        `;
        document.getElementById('vpPaymentsPagination').style.display = 'none';
        return;
    }
    
    const html = payments.map(payment => {
        const statusClass = `vp-status-${payment.status}`;
        const booking = payment.service_booking || {};
        
        return `
            <tr>
                <td>#${payment.id}</td>
                <td>${vpFinancialsEscapeHtml(payment.reference_number || 'N/A')}</td>
                <td style="text-transform: capitalize;">${booking.booking_type || 'N/A'}</td>
                <td><strong>${vpFinancialsFormatCurrency(payment.amount)}</strong></td>
                <td>
                    <span class="vp-status-badge ${statusClass}">
                        <i class="fas fa-circle"></i>
                        ${payment.status}
                    </span>
                </td>
                <td>${vpFinancialsFormatDate(payment.payment_date)}</td>
                <td>
                    <div class="vp-action-buttons">
                        <button class="vp-btn-action" onclick="vpFinancialsViewPaymentDetails(${payment.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${payment.status === 'completed' ? `
                            <button class="vp-btn-action" onclick="vpFinancialsGenerateInvoice(${payment.id})" title="Generate Invoice">
                                <i class="fas fa-file-invoice"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = html;
    
    // Update pagination
    vpFinancialsUpdatePagination(pagination);
}

/**
 * Display payments error state
 */
function vpFinancialsDisplayPaymentsError() {
    const tbody = document.getElementById('vpPaymentsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = `
        <tr>
            <td colspan="7" style="text-align: center; padding: 40px 20px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #dc3545; margin-bottom: 15px;"></i>
                <p style="color: #dc3545; margin: 0 0 15px 0;">Failed to load payments</p>
                <button class="vp-btn vp-btn-secondary vp-btn-sm" onclick="vpFinancialsLoadPayments()">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </td>
        </tr>
    `;
}

/**
 * Update pagination controls
 */
function vpFinancialsUpdatePagination(pagination) {
    const paginationDiv = document.getElementById('vpPaymentsPagination');
    if (!paginationDiv) return;
    
    paginationDiv.style.display = 'flex';
    
    // Update info
    const start = ((pagination.current_page - 1) * pagination.per_page) + 1;
    const end = Math.min(pagination.current_page * pagination.per_page, pagination.total_items);
    document.getElementById('vpPaginationInfo').textContent = 
        `Showing ${start}-${end} of ${pagination.total_items} payments`;
    
    // Update state
    vpFinancialsState.currentPage = pagination.current_page;
    vpFinancialsState.totalPages = pagination.total_pages;
    
    // Update buttons
    document.getElementById('vpPrevPage').disabled = !pagination.has_prev;
    document.getElementById('vpNextPage').disabled = !pagination.has_next;
    
    // Generate page numbers
    const pageNumbers = document.getElementById('vpPageNumbers');
    if (pageNumbers) {
        const pages = vpFinancialsGeneratePageNumbers(pagination.current_page, pagination.total_pages);
        pageNumbers.innerHTML = pages.map(page => {
            if (page === '...') {
                return '<span class="vp-page-number" style="cursor: default; border: none;">...</span>';
            }
            const activeClass = page === pagination.current_page ? 'vp-active' : '';
            return `<span class="vp-page-number ${activeClass}" onclick="vpFinancialsGoToPage(${page})">${page}</span>`;
        }).join('');
    }
}

/**
 * Generate page numbers for pagination
 */
function vpFinancialsGeneratePageNumbers(current, total) {
    const pages = [];
    const delta = 2;
    
    for (let i = 1; i <= total; i++) {
        if (i === 1 || i === total || (i >= current - delta && i <= current + delta)) {
            pages.push(i);
        } else if (pages[pages.length - 1] !== '...') {
            pages.push('...');
        }
    }
    
    return pages;
}

/**
 * Change page
 */
function vpFinancialsChangePage(direction) {
    const newPage = vpFinancialsState.currentPage + direction;
    if (newPage >= 1 && newPage <= vpFinancialsState.totalPages) {
        vpFinancialsState.currentPage = newPage;
        vpFinancialsLoadPayments();
    }
}

/**
 * Go to specific page
 */
function vpFinancialsGoToPage(page) {
    if (page >= 1 && page <= vpFinancialsState.totalPages) {
        vpFinancialsState.currentPage = page;
        vpFinancialsLoadPayments();
    }
}

/**
 * Filter payments
 */
function vpFinancialsFilterPayments() {
    vpFinancialsState.filters.status = document.getElementById('vpPaymentStatusFilter')?.value || '';
    vpFinancialsState.filters.startDate = document.getElementById('vpPaymentStartDate')?.value || '';
    vpFinancialsState.filters.endDate = document.getElementById('vpPaymentEndDate')?.value || '';
    
    vpFinancialsState.currentPage = 1;
    vpFinancialsLoadPayments();
}

/**
 * Clear filters
 */
function vpFinancialsClearFilters() {
    document.getElementById('vpPaymentStatusFilter').value = '';
    document.getElementById('vpPaymentStartDate').value = '';
    document.getElementById('vpPaymentEndDate').value = '';
    
    vpFinancialsState.filters = { status: '', startDate: '', endDate: '' };
    vpFinancialsState.currentPage = 1;
    vpFinancialsLoadPayments();
}

/**
 * Load payment statistics
 */
async function vpFinancialsLoadPaymentStats() {
    try {
        const period = document.getElementById('vpRevenuePeriod')?.value || 'month';
        const response = await fetch(`/api/vendor/financials/payment-statistics?period=${period}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        const data = await vpFinancialsHandleResponse(response);
        
        if (data.success) {
            vpFinancialsDisplayPaymentStats(data.data);
        }
    } catch (error) {
        console.error('Error loading payment stats:', error);
    }
}

/**
 * Display payment statistics
 */
function vpFinancialsDisplayPaymentStats(data) {
    const container = document.getElementById('vpPaymentStats');
    if (!container) return;
    
    const methodBreakdown = data.payment_method_breakdown || [];
    const metrics = data.metrics || {};
    
    if (methodBreakdown.length === 0) {
        container.innerHTML = `
            <div class="vp-loading-placeholder">
                <p>No payment statistics available</p>
            </div>
        `;
        return;
    }
    
    const totalAmount = methodBreakdown.reduce((sum, item) => sum + item.total_amount, 0);
    
    const html = methodBreakdown.map(item => {
        const percentage = totalAmount > 0 ? (item.total_amount / totalAmount * 100).toFixed(1) : 0;
        return `
            <div class="vp-stat-item">
                <div>
                    <div class="vp-stat-label">
                        <i class="fas fa-credit-card"></i>
                        ${item.method ? item.method.replace('_', ' ').toUpperCase() : 'Unknown'}
                    </div>
                    <div class="vp-stat-bar">
                        <div class="vp-stat-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                </div>
                <div class="vp-stat-value">
                    ${vpFinancialsFormatCurrency(item.total_amount)}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html + `
        <div class="vp-stat-item">
            <div class="vp-stat-label">
                <i class="fas fa-percentage"></i>
                Success Rate
            </div>
            <div class="vp-stat-value" style="color: #28a745;">
                ${metrics.success_rate || 0}%
            </div>
        </div>
    `;
}

/**
 * Refresh chart
 */
function vpFinancialsRefreshChart() {
    vpFinancialsLoadRevenueReport();
    vpFinancialsShowToast('info', 'Refreshing', 'Updating revenue data...');
}

/**
 * View payment details
 */
async function vpFinancialsViewPaymentDetails(paymentId) {
    try {
        const response = await fetch(`/api/vendor/financials/invoices/${paymentId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        const data = await vpFinancialsHandleResponse(response);
        
        if (data.success) {
            vpFinancialsShowPaymentDetailsModal(data.data.invoice);
        } else if (response.status === 404) {
            // No invoice yet, show basic payment details
            await vpFinancialsShowBasicPaymentDetails(paymentId);
        } else {
            throw new Error(data.message || 'Failed to load payment details');
        }
    } catch (error) {
        console.error('Error loading payment details:', error);
        vpFinancialsShowToast('error', 'Error', 'Failed to load payment details');
    }
}

/**
 * Show basic payment details when no invoice exists
 */
async function vpFinancialsShowBasicPaymentDetails(paymentId) {
    // This would fetch basic payment info from the payments list
    vpFinancialsShowToast('info', 'No Invoice', 'No invoice has been generated for this payment yet');
}

/**
 * Generate invoice
 */
async function vpFinancialsGenerateInvoice(paymentId) {
    if (!confirm('Generate invoice for this payment?')) return;
    
    try {
        const response = await fetch('/api/vendor/financials/invoices/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify({ payment_id: paymentId })
        });

        const data = await vpFinancialsHandleResponse(response);
        
        if (data.success) {
            vpFinancialsShowToast('success', 'Success', 'Invoice generated successfully');
            vpFinancialsShowPaymentDetailsModal(data.data.invoice);
        } else {
            throw new Error(data.message || 'Failed to generate invoice');
        }
    } catch (error) {
        console.error('Error generating invoice:', error);
        vpFinancialsShowToast('error', 'Error', error.message || 'Failed to generate invoice');
    }
}

/**
 * Download payment history
 */
function vpFinancialsDownloadHistory() {
    vpFinancialsShowDownloadModal();
}

/**
 * Generate report
 */
function vpFinancialsGenerateReport() {
    vpFinancialsShowReportModal();
}

/**
 * Handle API response
 */
async function vpFinancialsHandleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error ${response.status}`);
    }
    return response.json();
}

/**
 * Show toast notification
 */
function vpFinancialsShowToast(type, title, message) {
    const container = document.getElementById('vpFinancialsToastContainer');
    if (!container) return;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const toast = document.createElement('div');
    toast.className = `vp-toast vp-toast-${type}`;
    toast.innerHTML = `
        <div class="vp-toast-icon">
            <i class="fas ${icons[type] || icons.info}"></i>
        </div>
        <div class="vp-toast-content">
            <div class="vp-toast-title">${vpFinancialsEscapeHtml(title)}</div>
            <div class="vp-toast-message">${vpFinancialsEscapeHtml(message)}</div>
        </div>
        <button class="vp-toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'vpSlideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Utility: Format currency
 */
function vpFinancialsFormatCurrency(amount) {
    const num = parseFloat(amount) || 0;
    return 'KES ' + num.toLocaleString('en-KE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Utility: Format date
 */
function vpFinancialsFormatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

/**
 * Utility: Escape HTML
 */
function vpFinancialsEscapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Utility: Get period label
 */
function vpFinancialsGetPeriodLabel() {
    const period = document.getElementById('vpRevenuePeriod')?.value || 'monthly';
    const labels = {
        weekly: '7 days',
        monthly: '30 days',
        quarterly: '3 months',
        yearly: 'year',
        custom: 'period'
    };
    return labels[period] || 'period';
}

// Keyframe for slide
const style = document.createElement('style');
style.textContent = `
    @keyframes vpSlideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);