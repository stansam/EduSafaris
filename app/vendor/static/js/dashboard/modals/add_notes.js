// Add Note Modal JavaScript
window.VBModalAddNote = (function() {
    let currentBookingId = null;

    function open(bookingId) {
        currentBookingId = bookingId;
        const modal = document.getElementById('vbmAddNoteModal');
        const form = document.getElementById('vbmAddNoteForm');
        
        if (modal && form) {
            form.reset();
            const booking = window.VendorBookingsManager.getBooking(bookingId);
            if (booking) {
                document.getElementById('vbmAddNoteBookingId').value = `#${booking.id}`;
            }
            hideError();
            modal.style.display = 'flex';
        }
    }

    function close() {
        const modal = document.getElementById('vbmAddNoteModal');
        if (modal) {
            modal.style.display = 'none';
        }
        currentBookingId = null;
    }

    function validateNote() {
        const note = document.getElementById('vbmAddNoteText').value.trim();

        if (note.length === 0) {
            showError('Note text is required.');
            return false;
        }

        hideError();
        return true;
    }

    function showError(message) {
        const errorDiv = document.getElementById('vbmAddNoteError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    function hideError() {
        const errorDiv = document.getElementById('vbmAddNoteError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateNote()) {
            return;
        }
        
        const submitBtn = document.getElementById('vbmAddNoteSubmitBtn');
        const originalText = submitBtn.innerHTML;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

            const note = document.getElementById('vbmAddNoteText').value.trim();

            const response = await fetch(window.VendorBookingsManager.apiEndpoints.addNote(currentBookingId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ note })
            });

            const result = await response.json();

            if (result.success) {
                showSuccessMessage('Note added successfully!');
                close();
                // If booking details modal is open, refresh it
                if (window.VBModalBookingDetails && window.VBModalBookingDetails.currentBookingId === currentBookingId) {
                    window.VBModalBookingDetails.open(currentBookingId);
                }
            } else {
                throw new Error(result.error || 'Failed to add note');
            }
        } catch (error) {
            console.error('Error adding note:', error);
            showErrorMessage(error.message || 'Failed to add note. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    function showSuccessMessage(message) {
        alert(message);
    }

    function showErrorMessage(message) {
        alert(message);
    }

    // Attach event listeners
    document.getElementById('vbmAddNoteForm')?.addEventListener('submit', handleSubmit);

    return {
        open,
        close
    };
})();

// Close modal on overlay click
document.getElementById('vbmAddNoteModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        VBModalAddNote.close();
    }
});