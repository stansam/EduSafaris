let epsCancelPaymentData = null;

async function openEpsCancelPaymentModal(paymentId) {
  try {
    // Fetch payment details
    const response = await fetch(`/api/parent/payments/status/${paymentId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const result = await response.json();

    if (result.success) {
      epsCancelPaymentData = result.data;
      
      // Populate modal
      document.getElementById('epsCancelPaymentRef').textContent = epsCancelPaymentData.reference_number || 'N/A';
      document.getElementById('epsCancelPaymentAmount').textContent = formatEpsCurrency(epsCancelPaymentData.amount, epsCancelPaymentData.currency);
      document.getElementById('epsCancelPaymentId').value = paymentId;
      
      // Open modal
      const modal = document.getElementById('epsCancelPaymentModal');
      if (modal) {
        modal.classList.add('eps-modal-active');
        document.body.style.overflow = 'hidden';
      }
    } else {
      throw new Error(result.message || 'Failed to load payment details');
    }
  } catch (error) {
    console.error('Error loading payment for cancellation:', error);
    epsPaymentManager.showToast('Error', 'Failed to load payment details', 'error');
  }
}

function closeEpsCancelPaymentModal() {
  const modal = document.getElementById('epsCancelPaymentModal');
  if (modal) {
    modal.classList.remove('eps-modal-active');
    document.body.style.overflow = '';
    epsCancelPaymentData = null;
  }
}

document.getElementById('epsCancelPaymentForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const paymentId = document.getElementById('epsCancelPaymentId').value;
  
  if (!paymentId) {
    epsPaymentManager.showToast('Error', 'Invalid payment ID', 'error');
    return;
  }
  
  const submitBtn = document.getElementById('epsConfirmCancelBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cancelling...';
  
  try {
    const response = await fetch(`/api/parent/payments/cancel/${paymentId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const result = await response.json();
    
    if (result.success) {
      epsPaymentManager.showToast('Success', result.message || 'Payment cancelled successfully', 'success');
      closeEpsCancelPaymentModal();
      
      // Refresh data
      setTimeout(() => epsPaymentManager.refresh(), 1000);
    } else {
      throw new Error(result.message || 'Failed to cancel payment');
    }
  } catch (error) {
    console.error('Error cancelling payment:', error);
    epsPaymentManager.showToast('Error', error.message || 'Failed to cancel payment', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-times-circle"></i> Cancel Payment';
  }
});

// Close modal when clicking outside
document.getElementById('epsCancelPaymentModal')?.addEventListener('click', function(e) {
  if (e.target === this) {
    closeEpsCancelPaymentModal();
  }
});