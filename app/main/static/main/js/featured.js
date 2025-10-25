function viewTripDetails(tripId) {
    console.log(`Viewing details for trip ${tripId}`);
    window.location.href = `/trip/${tripId}`;
    // alert(`Viewing details for trip ${tripId}`);
}

// Function to view all trips
function viewAllTrips() {
    console.log('Viewing all trips');
    window.location.href = '/explore-trips';
    // alert('Redirecting to all trips...');
}

// Add click handler to entire card
document.querySelectorAll('.edusafaris-trip-card').forEach(card => {
    card.addEventListener('click', function(e) {
        // Don't trigger if clicking the button
        if (!e.target.closest('.edusafaris-view-details-btn')) {
            const tripId = this.getAttribute('data-trip-id');
            viewTripDetails(tripId);
        }
    });
});

// Intersection Observer for scroll animations
// const observerOptions = {
//     threshold: 0.1,
//     rootMargin: '0px 0px -50px 0px'
// };

// const observer = new IntersectionObserver((entries) => {
//     entries.forEach(entry => {
//         if (entry.isIntersecting) {
//             entry.target.style.opacity = '1';
//             entry.target.style.transform = 'translateY(0)';
//         }
//     });
// }, observerOptions);

// Observe all trip cards
document.querySelectorAll('.edusafaris-trip-card').forEach(card => {
    observer.observe(card);
});

// Add ripple effect on button click
document.querySelectorAll('.edusafaris-view-details-btn, .edusafaris-view-all-btn').forEach(button => {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');

        this.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    });
});