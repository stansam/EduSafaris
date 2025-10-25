// const observerOptions = {
//     threshold: 0.15,
//     rootMargin: '0px 0px -50px 0px'
// };

// const observer = new IntersectionObserver((entries) => {
//     entries.forEach(entry => {
//         if (entry.isIntersecting) {
//             entry.target.classList.add('edusafaris-visible');
//             observer.unobserve(entry.target);
//         }
//     });
// }, observerOptions);

// Observe all feature cards
document.querySelectorAll('.edusafaris-feature-card').forEach(card => {
    observer.observe(card);
});

// Add click tracking for analytics
document.querySelectorAll('.edusafaris-feature-card').forEach(card => {
    card.addEventListener('click', function() {
        const featureName = this.getAttribute('data-feature');
        console.log(`Feature clicked: ${featureName}`);
        
        // For Flask integration with analytics:
        // fetch('/api/track-feature-click', {
        //     method: 'POST',
        //     headers: {'Content-Type': 'application/json'},
        //     body: JSON.stringify({feature: featureName})
        // });
        
        // Add pulse animation on click
        const icon = this.querySelector('.edusafaris-feature-icon-container');
        icon.style.animation = 'edusafaris-why-pulse 0.5s ease';
        setTimeout(() => {
            icon.style.animation = '';
        }, 500);
    });
});

// Add hover sound effect (optional - uncomment if desired)
// document.querySelectorAll('.edusafaris-feature-card').forEach(card => {
//     card.addEventListener('mouseenter', function() {
//         // Play subtle hover sound
//         // const audio = new Audio('/static/sounds/hover.mp3');
//         // audio.volume = 0.2;
//         // audio.play();
//     });
// });

// Parallax effect for feature cards on scroll
let ticking = false;

window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(() => {
            const scrolled = window.pageYOffset;
            const cards = document.querySelectorAll('.edusafaris-feature-card');
            
            cards.forEach((card, index) => {
                const cardTop = card.getBoundingClientRect().top;
                const cardCenter = cardTop + (card.offsetHeight / 2);
                const windowCenter = window.innerHeight / 2;
                const distance = cardCenter - windowCenter;
                
                // Apply subtle parallax effect
                if (Math.abs(distance) < window.innerHeight) {
                    const offset = distance * 0.05;
                    card.style.transform = `translateY(${offset}px)`;
                }
            });
            
            ticking = false;
        });
        
        ticking = true;
    }
});

// Add sequential hover effect
let hoverTimeout;
document.querySelectorAll('.edusafaris-feature-card').forEach((card, index) => {
    card.addEventListener('mouseenter', function() {
        clearTimeout(hoverTimeout);
        
        // Highlight adjacent cards subtly
        const allCards = document.querySelectorAll('.edusafaris-feature-card');
        allCards.forEach((otherCard, otherIndex) => {
            if (Math.abs(index - otherIndex) === 1) {
                otherCard.style.opacity = '0.7';
                otherCard.style.transition = 'opacity 0.3s ease';
            }
        });
    });
    
    card.addEventListener('mouseleave', function() {
        hoverTimeout = setTimeout(() => {
            document.querySelectorAll('.edusafaris-feature-card').forEach(c => {
                c.style.opacity = '1';
            });
        }, 100);
    });
});

// Counter animation for when section comes into view
let countersAnimated = false;

const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !countersAnimated) {
            countersAnimated = true;
            
            // Add staggered entrance animations
            const cards = document.querySelectorAll('.edusafaris-feature-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
    });
}, { threshold: 0.2 });

const section = document.querySelector('.edusafaris-why-section');
if (section) {
    sectionObserver.observe(section);
}