document.querySelector('.edusafaris-footer-logo')?.addEventListener('click', function() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// Track footer link clicks
document.querySelectorAll('.edusafaris-footer-links a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const linkText = this.textContent;
        console.log(`Footer link clicked: ${linkText}`);
        
        // For Flask integration with analytics:
        // fetch('/api/track-footer-click', {
        //     method: 'POST',
        //     headers: {'Content-Type': 'application/json'},
        //     body: JSON.stringify({link: linkText})
        // });
        
        // Navigate to the href
        // window.location.href = this.getAttribute('href');
    });
});

// Add ripple effect to CTA buttons
document.querySelectorAll('.edusafaris-cta-primary-btn, .edusafaris-cta-secondary-btn').forEach(button => {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
            animation: ripple-effect 0.6s ease-out;
        `;

        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    });
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple-effect {
        from {
            transform: scale(0);
            opacity: 1;
        }
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Parallax effect for CTA section
window.addEventListener('scroll', () => {
    const ctaSection = document.querySelector('.edusafaris-cta-section');
    if (ctaSection) {
        const scrolled = window.pageYOffset;
        const ctaTop = ctaSection.offsetTop;
        const ctaHeight = ctaSection.offsetHeight;
        const windowHeight = window.innerHeight;

        if (scrolled + windowHeight > ctaTop && scrolled < ctaTop + ctaHeight) {
            const offset = ((scrolled + windowHeight - ctaTop) / (ctaHeight + windowHeight)) * 50;
            ctaSection.style.backgroundPosition = `center ${offset}%`;
        }
    }
});

// Animate elements when they come into view
// const observerOptions = {
//     threshold: 0.2,
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

// Observe footer columns
document.querySelectorAll('.edusafaris-footer-column, .edusafaris-footer-brand').forEach(el => {
    observer.observe(el);
});

// Track contact item clicks
document.querySelectorAll('.edusafaris-cta-contact-item a').forEach(link => {
    link.addEventListener('click', function() {
        const type = this.href.startsWith('tel:') ? 'phone' : 'email';
        console.log(`Contact ${type} clicked: ${this.textContent}`);
    });
});

// Social media tracking
document.querySelectorAll('.edusafaris-footer-social-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const platform = this.getAttribute('aria-label');
        console.log(`Social link clicked: ${platform}`);
        
        // For Flask integration:
        // fetch('/api/track-social-click', {
        //     method: 'POST',
        //     headers: {'Content-Type': 'application/json'},
        //     body: JSON.stringify({platform: platform})
        // });
    });
});