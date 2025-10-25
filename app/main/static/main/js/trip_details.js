// Smooth scroll animations
const tripObserverOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const tripObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.trip-info-card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    tripObserver.observe(card);
});

// Interactive itinerary days
document.querySelectorAll('.trip-itinerary-day').forEach(day => {
    day.addEventListener('click', function() {
        this.style.background = '#e0f2fe';
        setTimeout(() => {
            this.style.background = '#f9fafb';
        }, 300);
    });
});

// Button handlers
function handleRequestQuote() {
    alert('Request Quote functionality - This would open a quote request form');
    // In a real implementation, this would open a modal or navigate to a form
}

function handleDownloadBrochure() {
    alert('Download Brochure functionality - This would download a PDF brochure');
    // In a real implementation, this would trigger a file download
}

function handleContactUs() {
    alert('Contact Us functionality - This would open a contact form or chat');
    // In a real implementation, this would open a contact modal or chat widget
}

// Animate elements on scroll
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.trip-hero-section');
    if (hero) {
        hero.style.backgroundPositionY = scrolled * 0.5 + 'px';
    }
});

// Add hover effects to curriculum tags
document.querySelectorAll('.trip-curriculum-tag').forEach(tag => {
    tag.addEventListener('mouseenter', function() {
        this.style.background = '#f47621';
        this.style.color = 'white';
        this.style.transform = 'scale(1.05)';
        this.style.transition = 'all 0.3s ease';
    });
    
    tag.addEventListener('mouseleave', function() {
        this.style.background = '#f3f4f6';
        this.style.color = '#374151';
        this.style.transform = 'scale(1)';
    });
});

// Responsive sidebar behavior
function handleSidebarPosition() {
    const sidebar = document.querySelector('.trip-sidebar');
    const mainContainer = document.querySelector('.trip-main-container');
    
    if (window.innerWidth <= 1024) {
        sidebar.style.position = 'static';
    } else {
        sidebar.style.position = 'sticky';
    }
}

window.addEventListener('resize', handleSidebarPosition);
handleSidebarPosition();