const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        switchTab(targetTab);
    });
});

function switchTab(tabName) {
    // Remove active class from all tabs and panes
    tabBtns.forEach(btn => btn.classList.remove('active'));
    tabPanes.forEach(pane => pane.classList.remove('active'));

    // Add active class to selected tab and pane
    const selectedBtn = document.querySelector(`[data-tab="${tabName}"]`);
    const selectedPane = document.getElementById(tabName);

    if (selectedBtn && selectedPane) {
        selectedBtn.classList.add('active');
        selectedPane.classList.add('active');
    }

    if (tabName === 'payments' && typeof epsPaymentManager !== 'undefined') {
            epsPaymentManager.refresh();
        }
}

// Interactive button actions
function viewConsent(childName, tripName) {
    alert(`Viewing consent form for ${childName} - ${tripName}`);
    // In a real application, this would open a modal or navigate to consent details
}

function signConsent(childName, tripName) {
    const confirmed = confirm(`Sign consent form for ${childName} - ${tripName}?`);
    if (confirmed) {
        alert('Consent form signed successfully!');
        // In a real application, this would open a consent signing interface
    }
}

// Add smooth scrolling to stat cards
document.querySelectorAll('.stat-card').forEach(card => {
    card.addEventListener('click', function() {
        const tabsContainer = document.querySelector('.tabs-container');
        tabsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
});