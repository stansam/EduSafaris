let epsInitiatePaymentData = {
  registrations: [],
  selectedRegistration: null
};

function openEpsInitiatePaymentModal() {
  const modal = document.getElementById('epsInitiatePaymentModal');
  if (modal) {
    modal.classList.add('eps-modal-active');
    document.body.style.overflow = 'hidden';
    loadEpsRegistrationsForPayment();
  }
}

function closeEpsInitiatePaymentModal() {
  const modal = document.getElementById('epsInitiatePaymentModal');
  if (modal) {
    modal.classList.remove('eps-modal-active');
    document.body.style.overflow = '';
    resetEpsInitiatePaymentForm();
  }
}

async function loadEpsRegistrationsForPayment() {
  const select = document.getElementById('epsPaymentRegistration');
  if (!select) return;

  try {
    const response = await fetch('/api/parent/payments/summary', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const result = await response.json();

    if (result.success && result.data.active_registrations) {
      epsInitiatePaymentData.registrations = result.data.active_registrations
        .filter(reg => reg.outstanding_balance > 0);

      if (epsInitiatePaymentData.registrations.length === 0) {
        select.innerHTML = '<option value="">No registrations with outstanding balance</option>';
        return;
      }

      select.innerHTML = '<option value="">Select a registration</option>' +
        epsInitiatePaymentData.registrations.map(reg => 
          `<option value="${reg.id}">${reg.trip_title} - ${reg.participant_name} (${reg.registration_number})</option>`
        ).join('');

      // Setup event listeners
      select.addEventListener('change', handleEpsRegistrationSelection);
      
      // Setup quick amount buttons
      document.querySelectorAll('.eps-quick-amount-btn').forEach(btn => {
        btn.addEventListener('click', (e) => handleEpsQuickAmount(e.target.dataset.amount));
      });
    }
  } catch (error) {
    console.error('Error loading registrations:', error);
    select.innerHTML = '<option value="">Error loading registrations</option>';
  }
}

function handleEpsRegistrationSelection(e) {
  const regId = parseInt(e.target.value);
  if (!regId) {
    document.getElementById('epsRegistrationDetails').style.display = 'none';
    document.getElementById('epsQuickAmounts').style.display = 'none';
    return;
  }

  epsInitiatePaymentData.selectedRegistration = epsInitiatePaymentData.registrations.find(r => r.id === regId);
  
  if (epsInitiatePaymentData.selectedRegistration) {
    const reg = epsInitiatePaymentData.selectedRegistration;
    
    document.getElementById('epsRegTripTitle').textContent = reg.trip_title;
    document.getElementById('epsRegParticipant').textContent = reg.participant_name;
    document.getElementById('epsRegTotalAmount').textContent = formatEpsCurrency(reg.total_amount);
    document.getElementById('epsRegAmountPaid').textContent = formatEpsCurrency(reg.amount_paid);
    document.getElementById('epsRegOutstanding').textContent = formatEpsCurrency(reg.outstanding_balance);
    
    document.getElementById('epsRegistrationDetails').style.display = 'block';
    document.getElementById('epsQuickAmounts').style.display = 'block';
    
    // Set max amount
    document.getElementById('epsPaymentAmount').max = reg.outstanding_balance;
  }
}

function handleEpsQuickAmount(percentage) {
  if (!epsInitiatePaymentData.selectedRegistration) return;
  
  const outstanding = epsInitiatePaymentData.selectedRegistration.outstanding_balance;
  const amount = (outstanding * (parseInt(percentage) / 100)).toFixed(2);
  
  document.getElementById('epsPaymentAmount').value = amount;
  
  // Update button states
  document.querySelectorAll('.eps-quick-amount-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.amount === percentage) {
      btn.classList.add('active');
    }
  });
}

document.getElementById('epsInitiatePaymentForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  clearEpsErrors();
  
  const registrationId = document.getElementById('epsPaymentRegistration').value;
  const amount = document.getElementById('epsPaymentAmount').value;
  let phoneNumber = document.getElementById('epsPaymentPhone').value;
  const paymentMethod = document.getElementById('epsPaymentMethod').value;
  
  // Validation
  if (!registrationId) {
    showEpsError('epsPaymentRegistration', 'Please select a registration');
    return;
  }
  
  if (!amount || parseFloat(amount) < 100) {
    showEpsError('epsPaymentAmount', 'Minimum amount is KES 100');
    return;
  }
  
  if (!phoneNumber || phoneNumber.length !== 9) {
    showEpsError('epsPaymentPhone', 'Please enter a valid 9-digit phone number');
    return;
  }
  
  // Format phone number
  phoneNumber = '254' + phoneNumber;
  
  const submitBtn = document.getElementById('epsSubmitPaymentBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
  
  try {
    const response = await fetch('/api/parent/payments/initiate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        registration_id: parseInt(registrationId),
        amount: parseFloat(amount),
        phone_number: phoneNumber,
        payment_method: paymentMethod
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      epsPaymentManager.showToast('Success', result.message || 'Payment initiated successfully!', 'success');
      closeEpsInitiatePaymentModal();
      
      // Start polling for payment status
      if (result.data && result.data.payment_id) {
        pollEpsPaymentStatus(result.data.payment_id);
      }
      
      // Refresh data
      setTimeout(() => epsPaymentManager.refresh(), 2000);
    } else {
      throw new Error(result.message || 'Payment initiation failed');
    }
  } catch (error) {
    console.error('Error initiating payment:', error);
    epsPaymentManager.showToast('Error', error.message || 'Failed to initiate payment', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-credit-card"></i> Initiate Payment';
  }
});

function pollEpsPaymentStatus(paymentId, attempts = 0) {
  if (attempts >= 20) return; // Stop after 20 attempts (100 seconds)
  
  setTimeout(async () => {
    try {
      const response = await fetch(`/api/parent/payments/status/${paymentId}`);
      const result = await response.json();
      
      if (result.success) {
        const payment = result.data;
        
        if (payment.status === 'completed') {
          epsPaymentManager.showToast('Success', 'Payment completed successfully!', 'success');
          epsPaymentManager.refresh();
        } else if (payment.status === 'failed' || payment.status === 'cancelled') {
          epsPaymentManager.showToast('Error', payment.failure_reason || 'Payment failed', 'error');
          epsPaymentManager.refresh();
        } else if (payment.status === 'pending') {
          // Continue polling
          pollEpsPaymentStatus(paymentId, attempts + 1);
        }
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
    }
  }, 5000); // Poll every 5 seconds
}

function showEpsError(fieldId, message) {
  const field = document.getElementById(fieldId);
  const errorEl = document.getElementById(fieldId + 'Error');
  
  if (field) field.classList.add('eps-form-error');
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.add('eps-error-visible');
  }
}

function clearEpsErrors() {
  document.querySelectorAll('.eps-form-control').forEach(control => {
    control.classList.remove('eps-form-error');
  });
  document.querySelectorAll('.eps-error-message').forEach(err => {
    err.classList.remove('eps-error-visible');
  });
}

function resetEpsInitiatePaymentForm() {
  document.getElementById('epsInitiatePaymentForm')?.reset();
  document.getElementById('epsRegistrationDetails').style.display = 'none';
  document.getElementById('epsQuickAmounts').style.display = 'none';
  clearEpsErrors();
  
  document.querySelectorAll('.eps-quick-amount-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  epsInitiatePaymentData.selectedRegistration = null;
}

function formatEpsCurrency(amount, currency = 'KES') {
  if (amount === null || amount === undefined) return `${currency} 0.00`;
  const formatted = parseFloat(amount).toFixed(2);
  return `${currency} ${formatted.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
}

// Close modal when clicking outside
document.getElementById('epsInitiatePaymentModal')?.addEventListener('click', function(e) {
  if (e.target === this) {
    closeEpsInitiatePaymentModal();
  }
});