const tabButtons = document.querySelectorAll('.vp-tab');
const tabContents = document.querySelectorAll('.vp-tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');

        // Remove active class from all tabs and contents
        tabButtons.forEach(btn => btn.classList.remove('vp-active'));
        tabContents.forEach(content => content.classList.remove('vp-active'));

        // Add active class to clicked tab and corresponding content
        button.classList.add('vp-active');
        document.getElementById(tabName).classList.add('vp-active');
    });
});

// Search functionality for bookings
const bookingSearch = document.getElementById('bookingSearch');
const bookingsTableBody = document.getElementById('bookingsTableBody');

bookingSearch.addEventListener('keyup', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const rows = bookingsTableBody.querySelectorAll('tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});

// Initialize date inputs with date picker functionality
const startDateInput = document.getElementById('startDate');
const endDateInput = document.getElementById('endDate');

startDateInput.addEventListener('click', function() {
    this.type = 'date';
});

endDateInput.addEventListener('click', function() {
    this.type = 'date';
});

startDateInput.addEventListener('change', function() {
    this.type = 'text';
    if(this.value) {
        const date = new Date(this.value);
        this.value = (date.getMonth() + 1).toString().padStart(2, '0') + '/' + 
                    date.getDate().toString().padStart(2, '0') + '/' + 
                    date.getFullYear();
    }
});

endDateInput.addEventListener('change', function() {
    this.type = 'text';
    if(this.value) {
        const date = new Date(this.value);
        this.value = (date.getMonth() + 1).toString().padStart(2, '0') + '/' + 
                    date.getDate().toString().padStart(2, '0') + '/' + 
                    date.getFullYear();
    }
});

// Check Availability button
document.querySelector('.vp-check-btn').addEventListener('click', () => {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    if(startDate && endDate) {
        alert(`Checking availability from ${startDate} to ${endDate}`);
    } else {
        alert('Please select both start and end dates');
    }
});

// Save Changes button
document.querySelector('.vp-save-btn').addEventListener('click', () => {
    alert('Profile changes saved successfully!');
});