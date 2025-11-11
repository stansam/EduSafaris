let epsCurrentRegistrationId = null;
let epsCurrentPlanData = null;

async function openEpsPaymentPlanModal(registrationId) {
  epsCurrentRegistrationId = registrationId;
  
  const modal = document.getElementById('epsPaymentPlanModal');
  if (modal) {
    modal.classList.add('eps-modal-active');
    document.body.style.overflow = 'hidden';
    
    // Show loading
    document.getElementById('epsPaymentPlanLoading').style.display = 'block';
    document.getElementById('epsPaymentPlanContent').style.display = 'none';
    
    // Load payment plan
    await loadEpsPaymentPlan(registrationId);
  }
}

function closeEpsPaymentPlanModal() {
  const modal = document.getElementById('epsPaymentPlanModal');
  if (modal) {
    modal.classList.remove('eps-modal-active');
    document.body.style.overflow = '';
    epsCurrentRegistrationId = null;
    epsCurrentPlanData = null;
    hideEpsChangePlanSection();
  }
}

async function loadEpsPaymentPlan(registrationId) {
  try {
    const response = await fetch(`/api/parent/payments/payment-plan/${registrationId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.success) {
      epsCurrentPlanData = result.data;
      renderEpsPaymentPlan(result.data);
    } else {
      throw new Error(result.message || 'Failed to load payment plan');
    }
  } catch (error) {
    console.error('Error loading payment plan:', error);
    epsPaymentManager.showToast('Error', 'Failed to load payment plan', 'error');
    closeEpsPaymentPlanModal();
  }
}

function renderEpsPaymentPlan(data) {
  // Hide loading
  document.getElementById('epsPaymentPlanLoading').style.display = 'none';
  document.getElementById('epsPaymentPlanContent').style.display = 'block';

  const { registration, payment_summary, payment_history, available_plans, allows_installments } = data;

  // Registration details
  document.getElementById('epsPlanTripTitle').textContent = registration.trip_title || 'N/A';
  document.getElementById('epsPlanParticipant').textContent = registration.participant_name || 'N/A';
  document.getElementById('epsPlanRegNumber').textContent = registration.registration_number || 'N/A';
  document.getElementById('epsPlanCurrentPlan').textContent = data.current_plan || 'None';

  // Payment summary
  document.getElementById('epsPlanTotalAmount').textContent = formatEpsCurrency(payment_summary.total_amount, payment_summary.currency);
  document.getElementById('epsPlanAmountPaid').textContent = formatEpsCurrency(payment_summary.amount_paid, payment_summary.currency);
  document.getElementById('epsPlanOutstanding').textContent = formatEpsCurrency(payment_summary.outstanding_balance, payment_summary.currency);

  // Payment history
  const historyContainer = document.getElementById('epsPlanPaymentHistory');
  if (payment_history && payment_history.length > 0) {
    historyContainer.innerHTML = payment_history.map(payment => `
      <div class="eps-plan-payment-item">
        <div class="eps-plan-payment-info">
          <div class="eps-plan-payment-date">${new Date(payment.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</div>
          <div class="eps-plan-payment-amount">${formatEpsCurrency(payment.amount)}</div>
        </div>
        <span class="eps-status-badge eps-status-${payment.status}">
          <i class="fas fa-${payment.status === 'completed' ? 'check-circle' : 'clock'}"></i>
          ${payment.status}
        </span>
      </div>
    `).join('');
  } else {
    historyContainer.innerHTML = `
      <div class="eps-empty-state" style="padding: 40px 20px;">
        <i class="fas fa-receipt"></i>
        <p>No payment history available</p>
      </div>
    `;
  }

  // Available plans
  const plansContainer = document.getElementById('epsAvailablePlans');
  if (available_plans && available_plans.length > 0) {
    plansContainer.innerHTML = available_plans.map(plan => `
      <div class="eps-plan-option-card ${plan.plan_type === data.current_plan ? 'active' : ''}" 
           onclick="selectEpsPlanOption('${plan.plan_type}')">
        <div class="eps-plan-option-name">${plan.name}</div>
        <div class="eps-plan-option-details">
          <div><strong>Installments:</strong> ${plan.installment_count}</div>
          <div><strong>Amount per installment:</strong> ${formatEpsCurrency(plan.installment_amount)}</div>
          <div><strong>Frequency:</strong> ${plan.frequency}</div>
        </div>
      </div>
    `).join('');

    // Populate select dropdown
    const select = document.getElementById('epsNewPlanType');
    if (select) {
      select.innerHTML = '<option value="">Choose a payment plan</option>' +
        available_plans.map(plan => 
          `<option value="${plan.plan_type}">${plan.name} - ${formatEpsCurrency(plan.installment_amount)} per ${plan.frequency}</option>`
        ).join('');
    }
  } else {
    plansContainer.innerHTML = `
      <div class="eps-empty-state" style="padding: 40px 20px;">
        <i class="fas fa-calendar-times"></i>
        <p>${allows_installments ? 'No payment plans available' : 'This trip does not allow installment payments'}</p>
      </div>
    `;
    
    // Hide change plan button if no plans available
    document.getElementById('epsShowChangePlanBtn').style.display = 'none';
  }
}

function selectEpsPlanOption(planType) {
  document.querySelectorAll('.eps-plan-option-card').forEach(card => {
    card.classList.remove('active');
  });
  event.currentTarget.classList.add('active');
  document.getElementById('epsNewPlanType').value = planType;
}

function showEpsChangePlanSection() {
  document.getElementById('epsChangePlanSection').style.display = 'block';
  document.getElementById('epsShowChangePlanBtn').style.display = 'none';
}

function hideEpsChangePlanSection() {
  document.getElementById('epsChangePlanSection').style.display = 'none';
  document.getElementById('epsShowChangePlanBtn').style.display = 'inline-flex';
  document.getElementById('epsChangePlanForm').reset();
}

document.getElementById('epsChangePlanForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const planType = document.getElementById('epsNewPlanType').value;
  
  if (!planType) {
    epsPaymentManager.showToast('Error', 'Please select a payment plan', 'error');
    return;
  }
  
  const submitBtn = document.getElementById('epsSubmitPlanChangeBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
  
  try {
    const response = await fetch(`/api/parent/payments/payment-plan/${epsCurrentRegistrationId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan_type: planType
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      epsPaymentManager.showToast('Success', result.message || 'Payment plan updated successfully', 'success');
      
      // Reload payment plan
      await loadEpsPaymentPlan(epsCurrentRegistrationId);
      hideEpsChangePlanSection();
      
      // Refresh main view
      epsPaymentManager.refresh();
    } else {
      throw new Error(result.message || 'Failed to update payment plan');
    }
  } catch (error) {
    console.error('Error updating payment plan:', error);
    epsPaymentManager.showToast('Error', error.message || 'Failed to update payment plan', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-check"></i> Update Plan';
  }
});

// Close modal when clicking outside
document.getElementById('epsPaymentPlanModal')?.addEventListener('click', function(e) {
  if (e.target === this) {
    closeEpsPaymentPlanModal();
  }
});