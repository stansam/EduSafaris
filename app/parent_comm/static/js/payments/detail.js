let epsCurrentPaymentId = null;

async function openEpsPaymentDetailsModal(paymentId) {
  epsCurrentPaymentId = paymentId;
  
  const modal = document.getElementById('epsPaymentDetailsModal');
  if (modal) {
    modal.classList.add('eps-modal-active');
    document.body.style.overflow = 'hidden';
    
    // Show loading
    document.getElementById('epsPaymentDetailsLoading').style.display = 'block';
    document.getElementById('epsPaymentDetailsContent').style.display = 'none';
    
    // Load payment details
    await loadEpsPaymentDetails(paymentId);
  }
}

function closeEpsPaymentDetailsModal() {
  const modal = document.getElementById('epsPaymentDetailsModal');
  if (modal) {
    modal.classList.remove('eps-modal-active');
    document.body.style.overflow = '';
    epsCurrentPaymentId = null;
  }
}

async function loadEpsPaymentDetails(paymentId) {
  try {
    const response = await fetch(`/api/parent/payments/status/${paymentId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.success) {
      renderEpsPaymentDetails(result.data);
    } else {
      throw new Error(result.message || 'Failed to load payment details');
    }
  } catch (error) {
    console.error('Error loading payment details:', error);
    epsPaymentManager.showToast('Error', 'Failed to load payment details', 'error');
    closeEpsPaymentDetailsModal();
  }
}

function renderEpsPaymentDetails(payment) {
  // Hide loading
  document.getElementById('epsPaymentDetailsLoading').style.display = 'none';
  document.getElementById('epsPaymentDetailsContent').style.display = 'block';

  // Status section
  const statusIcon = document.getElementById('epsDetailStatusIcon');
  const statusTitle = document.getElementById('epsDetailStatusTitle');
  const statusMessage = document.getElementById('epsDetailStatusMessage');

  statusIcon.className = 'eps-status-icon';
  
  if (payment.status === 'completed') {
    statusIcon.classList.add('eps-status-success');
    statusIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
    statusTitle.textContent = 'Payment Completed';
    statusMessage.textContent = 'Your payment has been processed successfully';
    document.getElementById('epsDownloadReceiptBtn').style.display = 'inline-flex';
    document.getElementById('epsCheckStatusBtn').style.display = 'none';
  } else if (payment.status === 'pending') {
    statusIcon.classList.add('eps-status-pending');
    statusIcon.innerHTML = '<i class="fas fa-clock"></i>';
    statusTitle.textContent = 'Payment Pending';
    statusMessage.textContent = 'Your payment is being processed';
    document.getElementById('epsDownloadReceiptBtn').style.display = 'none';
    document.getElementById('epsCheckStatusBtn').style.display = 'inline-flex';
  } else if (payment.status === 'failed' || payment.status === 'cancelled') {
    statusIcon.classList.add('eps-status-failed');
    statusIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
    statusTitle.textContent = payment.status === 'failed' ? 'Payment Failed' : 'Payment Cancelled';
    statusMessage.textContent = payment.failure_reason || 'The payment was not completed';
    document.getElementById('epsDownloadReceiptBtn').style.display = 'none';
    document.getElementById('epsCheckStatusBtn').style.display = 'none';
    
    // Show failure reason
    if (payment.failure_reason) {
      document.getElementById('epsDetailFailureReason').textContent = payment.failure_reason;
      document.getElementById('epsDetailFailureSection').style.display = 'flex';
    }
  }

  // Payment information
  document.getElementById('epsDetailRefNumber').textContent = payment.reference_number || 'N/A';
  document.getElementById('epsDetailTxnId').textContent = payment.transaction_id || 'N/A';
  document.getElementById('epsDetailAmount').textContent = formatEpsCurrency(payment.amount, payment.currency);
  document.getElementById('epsDetailMethod').textContent = payment.payment_method || 'N/A';
  document.getElementById('epsDetailMpesaReceipt').textContent = payment.mpesa_receipt_number || 'N/A';
  document.getElementById('epsDetailPaymentDate').textContent = payment.transaction_date 
    ? new Date(payment.transaction_date).toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    : 'N/A';

  // Registration information
  if (payment.registration) {
    document.getElementById('epsDetailRegNumber').textContent = payment.registration.registration_number || 'N/A';
    document.getElementById('epsDetailTrip').textContent = payment.registration.trip_title || 'N/A';
    document.getElementById('epsDetailParticipant').textContent = payment.registration.participant_name || 'N/A';
    document.getElementById('epsDetailOutstanding').textContent = formatEpsCurrency(payment.registration.outstanding_balance);
  }
}

async function downloadEpsPaymentReceipt() {
  if (!epsCurrentPaymentId) return;

  const btn = document.getElementById('epsDownloadReceiptBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';

  try {
    const response = await fetch(`/api/parent/payments/receipt/${epsCurrentPaymentId}`, {
      method: 'GET'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `receipt_${epsCurrentPaymentId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    epsPaymentManager.showToast('Success', 'Receipt downloaded successfully', 'success');
  } catch (error) {
    console.error('Error downloading receipt:', error);
    epsPaymentManager.showToast('Error', 'Failed to download receipt', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-download"></i> Download Receipt';
  }
}

async function checkEpsPaymentStatusFromModal() {
  if (!epsCurrentPaymentId) return;

  const btn = document.getElementById('epsCheckStatusBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';

  try {
    await loadEpsPaymentDetails(epsCurrentPaymentId);
    epsPaymentManager.showToast('Info', 'Payment status updated', 'info');
    
    // If status changed, refresh the main view
    epsPaymentManager.refresh();
  } catch (error) {
    console.error('Error checking payment status:', error);
    epsPaymentManager.showToast('Error', 'Failed to check payment status', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-sync"></i> Check Status';
  }
}

// Close modal when clicking outside
document.getElementById('epsPaymentDetailsModal')?.addEventListener('click', function(e) {
  if (e.target === this) {
    closeEpsPaymentDetailsModal();
  }
});