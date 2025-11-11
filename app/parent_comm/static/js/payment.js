/**
 * EduSafaris Payment Management System
 * Main Controller
 */

class EduSafarisPaymentManager {
  constructor() {
    this.currentTab = 'overview';
    this.currentPage = 1;
    this.perPage = 20;
    this.filters = {
      status: '',
      startDate: '',
      endDate: '',
      search: ''
    };
    this.paymentSummary = null;
    this.paymentHistory = [];
    this.activeRegistrations = [];
    
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.loadPaymentSummary();
  }

  setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.eps-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = e.currentTarget.dataset.epsTab;
        this.switchTab(tab);
      });
    });

    // Initiate payment button
    const initiateBtn = document.getElementById('epsInitiatePaymentBtn');
    if (initiateBtn) {
      initiateBtn.addEventListener('click', () => this.openInitiatePaymentModal());
    }

    // View all payments
    const viewAllBtn = document.getElementById('epsViewAllPayments');
    if (viewAllBtn) {
      viewAllBtn.addEventListener('click', () => this.switchTab('history'));
    }

    // History filters
    const applyFiltersBtn = document.getElementById('epsApplyFilters');
    if (applyFiltersBtn) {
      applyFiltersBtn.addEventListener('click', () => this.applyHistoryFilters());
    }

    const searchInput = document.getElementById('epsHistorySearch');
    if (searchInput) {
      let searchTimeout;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          this.filters.search = e.target.value;
          this.loadPaymentHistory();
        }, 500);
      });
    }

    // Toast close
    const toastClose = document.querySelector('.eps-toast-close');
    if (toastClose) {
      toastClose.addEventListener('click', () => this.hideToast());
    }
  }

  switchTab(tabName) {
    this.currentTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.eps-tab-btn').forEach(btn => {
      btn.classList.remove('eps-tab-active');
    });
    document.querySelectorAll('.eps-tab-pane').forEach(pane => {
      pane.classList.remove('eps-tab-active');
    });

    const activeBtn = document.querySelector(`[data-eps-tab="${tabName}"]`);
    const activePane = document.getElementById(`eps${this.capitalize(tabName)}Tab`);

    if (activeBtn) activeBtn.classList.add('eps-tab-active');
    if (activePane) activePane.classList.add('eps-tab-active');

    // Load tab content
    switch (tabName) {
      case 'overview':
        // Already loaded in summary
        break;
      case 'history':
        this.loadPaymentHistory();
        break;
      case 'plans':
        this.loadPaymentPlans();
        break;
      case 'registrations':
        this.loadActiveRegistrations();
        break;
    }
  }

  async loadPaymentSummary() {
    try {
      const response = await fetch('/api/parent/payments/summary', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.paymentSummary = result.data;
        this.renderStatistics();
        this.renderRecentPayments();
        this.renderUpcomingDeadlines();
        this.renderAlerts();
      } else {
        throw new Error(result.message || 'Failed to load payment summary');
      }
    } catch (error) {
      console.error('Error loading payment summary:', error);
      this.showToast('Error', 'Failed to load payment summary', 'error');
    }
  }

  renderStatistics() {
    if (!this.paymentSummary) return;

    const { overview, overdue_payments } = this.paymentSummary;

    document.getElementById('epsTotalOwed').textContent = 
      this.formatCurrency(overview.total_owed, overview.currency);
    document.getElementById('epsActiveRegs').textContent = 
      `${overview.active_registrations_count} active registrations`;

    document.getElementById('epsTotalPaid').textContent = 
      this.formatCurrency(overview.total_paid, overview.currency);
    document.getElementById('epsTotalTransactions').textContent = 
      `${overview.total_transactions} transactions`;

    document.getElementById('epsOutstanding').textContent = 
      this.formatCurrency(overview.total_outstanding, overview.currency);
    document.getElementById('epsOverdueCount').textContent = 
      `${overdue_payments.length} overdue`;
  }

  renderRecentPayments() {
    const container = document.getElementById('epsRecentPaymentsContainer');
    const loading = document.getElementById('epsRecentPaymentsLoading');

    if (loading) loading.style.display = 'none';
    if (!container) return;

    const { recent_payments } = this.paymentSummary;

    if (!recent_payments || recent_payments.length === 0) {
      container.innerHTML = `
        <div class="eps-empty-state" style="padding: 40px 20px;">
          <i class="fas fa-receipt"></i>
          <h3>No Recent Payments</h3>
          <p>You haven't made any payments yet.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = recent_payments.slice(0, 5).map(payment => `
      <div class="eps-payment-card">
        <div class="eps-card-header">
          <div>
            <h4 class="eps-card-title">${this.escapeHtml(payment.trip_title || 'N/A')}</h4>
            <p class="eps-card-subtitle">${this.escapeHtml(payment.participant_name || 'N/A')}</p>
          </div>
          ${this.getStatusBadge(payment.status)}
        </div>
        <div class="eps-card-body">
          <div class="eps-card-detail">
            <span class="eps-card-detail-label">Amount</span>
            <span class="eps-card-detail-value">${this.formatCurrency(payment.amount, payment.currency)}</span>
          </div>
          <div class="eps-card-detail">
            <span class="eps-card-detail-label">Reference</span>
            <span class="eps-card-detail-value">${this.escapeHtml(payment.reference_number)}</span>
          </div>
          <div class="eps-card-detail">
            <span class="eps-card-detail-label">Date</span>
            <span class="eps-card-detail-value">${this.formatDate(payment.created_at)}</span>
          </div>
          <div class="eps-card-detail">
            <span class="eps-card-detail-label">Method</span>
            <span class="eps-card-detail-value">${this.escapeHtml(payment.payment_method || 'N/A')}</span>
          </div>
        </div>
        <div class="eps-card-footer">
          <div class="eps-action-buttons">
            <button class="eps-action-btn" onclick="epsPaymentManager.viewPaymentDetails(${payment.id})">
              <i class="fas fa-eye"></i> View Details
            </button>
            ${payment.status === 'completed' ? `
              <button class="eps-action-btn" onclick="epsPaymentManager.downloadReceipt(${payment.id})">
                <i class="fas fa-download"></i> Receipt
              </button>
            ` : ''}
            ${payment.status === 'pending' ? `
              <button class="eps-action-btn" onclick="epsPaymentManager.checkPaymentStatus(${payment.id})">
                <i class="fas fa-sync"></i> Check Status
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `).join('');
  }

  renderUpcomingDeadlines() {
    const container = document.getElementById('epsDeadlinesContainer');
    const loading = document.getElementById('epsDeadlinesLoading');

    if (loading) loading.style.display = 'none';
    if (!container) return;

    const { upcoming_deadlines, overdue_payments } = this.paymentSummary;
    const allDeadlines = [...overdue_payments, ...upcoming_deadlines].slice(0, 5);

    if (allDeadlines.length === 0) {
      container.innerHTML = `
        <div class="eps-empty-state" style="padding: 40px 20px;">
          <i class="fas fa-calendar-check"></i>
          <h3>No Upcoming Deadlines</h3>
          <p>All payments are up to date!</p>
        </div>
      `;
      return;
    }

    container.innerHTML = allDeadlines.map(deadline => {
      const isOverdue = deadline.is_overdue || deadline.days_overdue > 0;
      const daysText = isOverdue 
        ? `${deadline.days_overdue} days overdue`
        : `${deadline.days_remaining} days remaining`;
      
      return `
        <div class="eps-deadline-card ${isOverdue ? 'eps-deadline-overdue' : deadline.days_remaining <= 3 ? 'eps-deadline-urgent' : ''}">
          <div class="eps-card-header">
            <div>
              <h4 class="eps-card-title">${this.escapeHtml(deadline.trip_title)}</h4>
              <p class="eps-card-subtitle">${this.escapeHtml(deadline.participant_name)}</p>
            </div>
            <span class="eps-status-badge ${isOverdue ? 'eps-status-failed' : 'eps-status-pending'}">
              <i class="fas fa-clock"></i> ${daysText}
            </span>
          </div>
          <div class="eps-card-body">
            <div class="eps-card-detail">
              <span class="eps-card-detail-label">Amount Due</span>
              <span class="eps-card-detail-value">${this.formatCurrency(deadline.amount_due)}</span>
            </div>
            <div class="eps-card-detail">
              <span class="eps-card-detail-label">Deadline</span>
              <span class="eps-card-detail-value">${this.formatDate(deadline.deadline)}</span>
            </div>
            <div class="eps-card-detail">
              <span class="eps-card-detail-label">Registration</span>
              <span class="eps-card-detail-value">${this.escapeHtml(deadline.registration_number)}</span>
            </div>
          </div>
          <div class="eps-card-footer">
            <button class="eps-btn eps-btn-primary eps-btn-sm" 
                    onclick="epsPaymentManager.openPaymentModal(${deadline.registration_id})">
              <i class="fas fa-credit-card"></i> Make Payment
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  renderAlerts() {
    const container = document.getElementById('epsAlertsContainer');
    if (!container) return;

    const { overdue_payments } = this.paymentSummary;

    if (overdue_payments && overdue_payments.length > 0) {
      container.innerHTML = `
        <div class="eps-alert eps-alert-error">
          <i class="fas fa-exclamation-triangle"></i>
          <div>
            <strong>Payment Overdue!</strong><br>
            You have ${overdue_payments.length} overdue payment${overdue_payments.length > 1 ? 's' : ''}. 
            Please make payment as soon as possible to avoid trip cancellation.
          </div>
        </div>
      `;
    } else {
      container.innerHTML = '';
    }
  }

  async loadPaymentHistory() {
    const loading = document.getElementById('epsHistoryLoading');
    const tableWrapper = document.getElementById('epsHistoryTableWrapper');
    const empty = document.getElementById('epsHistoryEmpty');

    if (loading) loading.style.display = 'block';
    if (tableWrapper) tableWrapper.style.display = 'none';
    if (empty) empty.style.display = 'none';

    try {
      const params = new URLSearchParams({
        page: this.currentPage,
        per_page: this.perPage,
        ...(this.filters.status && { status: this.filters.status }),
        ...(this.filters.startDate && { start_date: this.filters.startDate }),
        ...(this.filters.endDate && { end_date: this.filters.endDate })
      });

      const response = await fetch(`/api/parent/payments/history?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.paymentHistory = result.data.payments;
        this.renderPaymentHistory(result.data);
      } else {
        throw new Error(result.message || 'Failed to load payment history');
      }
    } catch (error) {
      console.error('Error loading payment history:', error);
      this.showToast('Error', 'Failed to load payment history', 'error');
      if (empty) empty.style.display = 'block';
    } finally {
      if (loading) loading.style.display = 'none';
    }
  }

  renderPaymentHistory(data) {
    const tableBody = document.getElementById('epsHistoryTableBody');
    const tableWrapper = document.getElementById('epsHistoryTableWrapper');
    const empty = document.getElementById('epsHistoryEmpty');

    if (!tableBody) return;

    const { payments, pagination } = data;

    if (payments.length === 0) {
      if (tableWrapper) tableWrapper.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }

    if (tableWrapper) tableWrapper.style.display = 'block';
    if (empty) empty.style.display = 'none';

    // Filter by search if needed
    let filteredPayments = payments;
    if (this.filters.search) {
      const searchLower = this.filters.search.toLowerCase();
      filteredPayments = payments.filter(p => 
        (p.reference_number && p.reference_number.toLowerCase().includes(searchLower)) ||
        (p.registration && p.registration.trip_title && p.registration.trip_title.toLowerCase().includes(searchLower)) ||
        (p.registration && p.registration.participant_name && p.registration.participant_name.toLowerCase().includes(searchLower))
      );
    }

    tableBody.innerHTML = filteredPayments.map(payment => `
      <tr>
        <td>${this.formatDate(payment.created_at)}</td>
        <td>
          <strong>${this.escapeHtml(payment.reference_number)}</strong>
          ${payment.transaction_id ? `<br><small style="color: #6b7280;">${this.escapeHtml(payment.transaction_id)}</small>` : ''}
        </td>
        <td>
          ${payment.registration ? `
            <strong>${this.escapeHtml(payment.registration.trip_title)}</strong><br>
            <small style="color: #6b7280;">${this.escapeHtml(payment.registration.participant_name)}</small>
          ` : 'N/A'}
        </td>
        <td><strong>${this.formatCurrency(payment.amount, payment.currency)}</strong></td>
        <td>${this.escapeHtml(payment.payment_method || 'N/A')}</td>
        <td>${this.getStatusBadge(payment.status)}</td>
        <td>
          <div class="eps-action-buttons">
            <button class="eps-action-btn" onclick="epsPaymentManager.viewPaymentDetails(${payment.id})">
              <i class="fas fa-eye"></i> View
            </button>
            ${payment.can_download_receipt ? `
              <button class="eps-action-btn" onclick="epsPaymentManager.downloadReceipt(${payment.id})">
                <i class="fas fa-download"></i> Receipt
              </button>
            ` : ''}
            ${payment.status === 'pending' ? `
              <button class="eps-action-btn eps-action-danger" onclick="epsPaymentManager.openCancelPaymentModal(${payment.id})">
                <i class="fas fa-times"></i> Cancel
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `).join('');

    this.renderPagination(pagination);
  }

  renderPagination(pagination) {
    const container = document.getElementById('epsPaginationContainer');
    if (!container || !pagination) return;

    const { page, total_pages, has_prev, has_next } = pagination;

    if (total_pages <= 1) {
      container.innerHTML = '';
      return;
    }

    let html = `
      <button class="eps-pagination-btn" ${!has_prev ? 'disabled' : ''} 
              onclick="epsPaymentManager.changePage(${page - 1})">
        <i class="fas fa-chevron-left"></i>
      </button>
    `;

    for (let i = 1; i <= total_pages; i++) {
      if (i === 1 || i === total_pages || (i >= page - 2 && i <= page + 2)) {
        html += `
          <button class="eps-pagination-btn ${i === page ? 'eps-pagination-active' : ''}" 
                  onclick="epsPaymentManager.changePage(${i})">
            ${i}
          </button>
        `;
      } else if (i === page - 3 || i === page + 3) {
        html += `<span>...</span>`;
      }
    }

    html += `
      <button class="eps-pagination-btn" ${!has_next ? 'disabled' : ''} 
              onclick="epsPaymentManager.changePage(${page + 1})">
        <i class="fas fa-chevron-right"></i>
      </button>
    `;

    container.innerHTML = html;
  }

  changePage(page) {
    this.currentPage = page;
    this.loadPaymentHistory();
  }

  applyHistoryFilters() {
    this.filters.status = document.getElementById('epsHistoryStatusFilter')?.value || '';
    this.filters.startDate = document.getElementById('epsHistoryStartDate')?.value || '';
    this.filters.endDate = document.getElementById('epsHistoryEndDate')?.value || '';
    this.currentPage = 1;
    this.loadPaymentHistory();
  }

  async loadPaymentPlans() {
    const loading = document.getElementById('epsPlansLoading');
    const container = document.getElementById('epsPlansContainer');
    const empty = document.getElementById('epsPlansEmpty');

    if (loading) loading.style.display = 'block';
    if (container) container.style.display = 'none';
    if (empty) empty.style.display = 'none';

    try {
      // Get all active registrations and render their payment plans
      if (!this.paymentSummary) {
        await this.loadPaymentSummary();
      }

      const { active_registrations } = this.paymentSummary;

      if (loading) loading.style.display = 'none';

      if (!active_registrations || active_registrations.length === 0) {
        if (empty) empty.style.display = 'block';
        return;
      }

      if (container) {
        container.style.display = 'block';
        container.innerHTML = active_registrations.map(reg => {
          const progress = (reg.amount_paid / reg.total_amount) * 100;
          return `
            <div class="eps-payment-card">
              <div class="eps-card-header">
                <div>
                  <h4 class="eps-card-title">${this.escapeHtml(reg.trip_title)}</h4>
                  <p class="eps-card-subtitle">${this.escapeHtml(reg.participant_name)}</p>
                </div>
                <span class="eps-status-badge eps-status-${reg.payment_status}">
                  ${this.escapeHtml(reg.payment_status)}
                </span>
              </div>
              <div class="eps-card-body">
                <div class="eps-card-detail">
                  <span class="eps-card-detail-label">Total Amount</span>
                  <span class="eps-card-detail-value">${this.formatCurrency(reg.total_amount)}</span>
                </div>
                <div class="eps-card-detail">
                  <span class="eps-card-detail-label">Amount Paid</span>
                  <span class="eps-card-detail-value">${this.formatCurrency(reg.amount_paid)}</span>
                </div>
                <div class="eps-card-detail">
                  <span class="eps-card-detail-label">Outstanding</span>
                  <span class="eps-card-detail-value">${this.formatCurrency(reg.outstanding_balance)}</span>
                </div>
                <div class="eps-card-detail">
                  <span class="eps-card-detail-label">Payment Plan</span>
                  <span class="eps-card-detail-value">${this.escapeHtml(reg.payment_plan || 'None')}</span>
                </div>
              </div>
              <div style="margin: 16px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; color: #6b7280;">
                  <span>Payment Progress</span>
                  <span>${progress.toFixed(0)}%</span>
                </div>
                <div style="height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                  <div style="height: 100%; background: linear-gradient(90deg, #10b981 0%, #059669 100%); width: ${progress}%; transition: width 0.5s ease;"></div>
                </div>
              </div>
              <div class="eps-card-footer">
                <div class="eps-action-buttons">
                  <button class="eps-btn eps-btn-primary eps-btn-sm" onclick="epsPaymentManager.openPaymentModal(${reg.id})">
                    <i class="fas fa-credit-card"></i> Make Payment
                  </button>
                  <button class="eps-action-btn" onclick="epsPaymentManager.viewPaymentPlan(${reg.id})">
                    <i class="fas fa-calendar-alt"></i> View Plan
                  </button>
                </div>
              </div>
            </div>
          `;
        }).join('');
      }
    } catch (error) {
      console.error('Error loading payment plans:', error);
      this.showToast('Error', 'Failed to load payment plans', 'error');
      if (empty) empty.style.display = 'block';
    } finally {
      if (loading) loading.style.display = 'none';
    }
  }

  async loadActiveRegistrations() {
    const loading = document.getElementById('epsRegistrationsLoading');
    const container = document.getElementById('epsRegistrationsContainer');
    const empty = document.getElementById('epsRegistrationsEmpty');

    if (loading) loading.style.display = 'block';
    if (container) container.style.display = 'none';
    if (empty) empty.style.display = 'none';

    try {
      if (!this.paymentSummary) {
        await this.loadPaymentSummary();
      }

      const { active_registrations } = this.paymentSummary;

      if (loading) loading.style.display = 'none';

      if (!active_registrations || active_registrations.length === 0) {
        if (empty) empty.style.display = 'block';
        return;
      }

      if (container) {
        container.style.display = 'block';
        container.innerHTML = active_registrations.map(reg => `
          <div class="eps-payment-card">
            <div class="eps-card-header">
              <div>
                <h4 class="eps-card-title">${this.escapeHtml(reg.trip_title)}</h4>
                <p class="eps-card-subtitle">
                  ${this.escapeHtml(reg.participant_name)} • ${this.escapeHtml(reg.registration_number)}
                </p>
              </div>
              <span class="eps-status-badge eps-status-${reg.status}">
                ${this.escapeHtml(reg.status)}
              </span>
            </div>
            <div class="eps-card-body">
              <div class="eps-card-detail">
                <span class="eps-card-detail-label">Total Amount</span>
                <span class="eps-card-detail-value">${this.formatCurrency(reg.total_amount)}</span>
              </div>
              <div class="eps-card-detail">
                <span class="eps-card-detail-label">Amount Paid</span>
                <span class="eps-card-detail-value">${this.formatCurrency(reg.amount_paid)}</span>
              </div>
              <div class="eps-card-detail">
                <span class="eps-card-detail-label">Outstanding</span>
                <span class="eps-card-detail-value">${this.formatCurrency(reg.outstanding_balance)}</span>
              </div>
              <div class="eps-card-detail">
                <span class="eps-card-detail-label">Payment Deadline</span>
                <span class="eps-card-detail-value">${reg.payment_deadline ? this.formatDate(reg.payment_deadline) : 'Not set'}</span>
              </div>
            </div>
            <div class="eps-card-footer">
              <div class="eps-action-buttons">
                ${reg.outstanding_balance > 0 ? `
                  <button class="eps-btn eps-btn-primary eps-btn-sm" onclick="epsPaymentManager.openPaymentModal(${reg.id})">
                    <i class="fas fa-credit-card"></i> Make Payment
                  </button>
                ` : ''}
                <button class="eps-action-btn" onclick="epsPaymentManager.viewRegistrationDetails(${reg.id})">
                  <i class="fas fa-eye"></i> View Details
                </button>
              </div>
            </div>
          </div>
        `).join('');
      }
    } catch (error) {
      console.error('Error loading registrations:', error);
      this.showToast('Error', 'Failed to load registrations', 'error');
      if (empty) empty.style.display = 'block';
    } finally {
      if (loading) loading.style.display = 'none';
    }
  }

  // Modal triggers
  openInitiatePaymentModal() {
    if (typeof openEpsInitiatePaymentModal === 'function') {
      openEpsInitiatePaymentModal();
    }
  }

  openPaymentModal(registrationId) {
    if (typeof openEpsPaymentModal === 'function') {
      openEpsPaymentModal(registrationId);
    }
  }

  openCancelPaymentModal(paymentId) {
    if (typeof openEpsCancelPaymentModal === 'function') {
      openEpsCancelPaymentModal(paymentId);
    }
  }

  viewPaymentDetails(paymentId) {
    if (typeof openEpsPaymentDetailsModal === 'function') {
      openEpsPaymentDetailsModal(paymentId);
    }
  }

  viewPaymentPlan(registrationId) {
    if (typeof openEpsPaymentPlanModal === 'function') {
      openEpsPaymentPlanModal(registrationId);
    }
  }

  viewRegistrationDetails(registrationId) {
    // Navigate to registration details or open modal
    this.showToast('Info', 'Registration details feature coming soon', 'info');
  }

  async checkPaymentStatus(paymentId) {
    try {
      this.showToast('Info', 'Checking payment status...', 'info');

      const response = await fetch(`/api/parent/payments/status/${paymentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        const payment = result.data;
        
        if (payment.status === 'completed') {
          this.showToast('Success', 'Payment completed successfully!', 'success');
          this.loadPaymentSummary();
        } else if (payment.status === 'failed' || payment.status === 'cancelled') {
          this.showToast('Error', payment.failure_reason || 'Payment was not successful', 'error');
          this.loadPaymentSummary();
        } else {
          this.showToast('Info', 'Payment is still being processed', 'info');
        }
      } else {
        throw new Error(result.message || 'Failed to check payment status');
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
      this.showToast('Error', 'Failed to check payment status', 'error');
    }
  }

  async downloadReceipt(paymentId) {
    try {
      this.showToast('Info', 'Downloading receipt...', 'info');

      const response = await fetch(`/api/parent/payments/receipt/${paymentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt_${paymentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      this.showToast('Success', 'Receipt downloaded successfully', 'success');
    } catch (error) {
      console.error('Error downloading receipt:', error);
      this.showToast('Error', 'Failed to download receipt', 'error');
    }
  }

  // Utility methods
  showToast(title, message, type = 'info') {
    const toast = document.getElementById('epsToast');
    if (!toast) return;

    const iconMap = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };

    toast.className = `eps-toast eps-toast-visible eps-toast-${type}`;
    
    const icon = toast.querySelector('.eps-toast-icon');
    const titleEl = toast.querySelector('.eps-toast-title');
    const messageEl = toast.querySelector('.eps-toast-message');

    if (icon) {
      icon.className = `eps-toast-icon fas ${iconMap[type]}`;
    }
    if (titleEl) {
      titleEl.textContent = title;
    }
    if (messageEl) {
      messageEl.textContent = message;
    }

    setTimeout(() => this.hideToast(), 5000);
  }

  hideToast() {
    const toast = document.getElementById('epsToast');
    if (toast) {
      toast.classList.remove('eps-toast-visible');
    }
  }

  getStatusBadge(status) {
    const statusConfig = {
      completed: { label: 'Completed', icon: 'fa-check-circle' },
      pending: { label: 'Pending', icon: 'fa-clock' },
      failed: { label: 'Failed', icon: 'fa-times-circle' },
      cancelled: { label: 'Cancelled', icon: 'fa-ban' },
      confirmed: { label: 'Confirmed', icon: 'fa-check' },
      waitlisted: { label: 'Waitlisted', icon: 'fa-list' },
      paid: { label: 'Paid', icon: 'fa-check-circle' },
      partial: { label: 'Partial', icon: 'fa-clock' },
      unpaid: { label: 'Unpaid', icon: 'fa-exclamation-circle' }
    };

    const config = statusConfig[status] || { label: status, icon: 'fa-circle' };
    return `<span class="eps-status-badge eps-status-${status}">
      <i class="fas ${config.icon}"></i> ${config.label}
    </span>`;
  }

  formatCurrency(amount, currency = 'KES') {
    if (amount === null || amount === undefined) return `${currency} 0.00`;
    const formatted = parseFloat(amount).toFixed(2);
    return `${currency} ${formatted.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
  }

  formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  }

  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Refresh methods
  refresh() {
    this.loadPaymentSummary();
    if (this.currentTab === 'history') {
      this.loadPaymentHistory();
    } else if (this.currentTab === 'plans') {
      this.loadPaymentPlans();
    } else if (this.currentTab === 'registrations') {
      this.loadActiveRegistrations();
    }
  }
}

// Initialize on DOM ready
let epsPaymentManager;
document.addEventListener('DOMContentLoaded', () => {
  epsPaymentManager = new EduSafarisPaymentManager();
});