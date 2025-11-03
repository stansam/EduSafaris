function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-target'));
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;

    const updateCounter = () => {
        current += increment;
        if (current < target) {
            element.textContent = Math.floor(current);
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target;
        }
    };

    updateCounter();
}

// Intersection Observer for stat counters
const observerOptions = {
    threshold: 0.5
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const counters = entry.target.querySelectorAll('.edusafaris-stat-number');
            counters.forEach(counter => {
                animateCounter(counter);
            });
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

const statsSection = document.querySelector('.edusafaris-stats');
if (statsSection) {
    observer.observe(statsSection);
}

function signIn() {
    window.location.href = '/auth/login';
}

function signUp() {
    window.location.href = '/auth/register';
}

// Button click handlers
function exploreTrips() {
    window.location.href = '/explore-trips';
}

function forSchools() {
    window.location.href = '/for-schools';
}

// Add smooth hover effect to floating cards
const floatingCards = document.querySelectorAll('.edusafaris-floating-card');
floatingCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.05)';
        this.style.transition = 'transform 0.3s ease';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
});

// Add parallax effect to hero image on scroll
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const heroImage = document.querySelector('.edusafaris-main-image');
    if (heroImage) {
        heroImage.style.transform = `translateY(${scrolled * 0.1}px)`;
    }
});

function toggleUserDropdown() {
  const dropdown = document.getElementById('userDropdown');
  const userInfo = document.querySelector('.edusafaris-user-info');
  dropdown.classList.toggle('show');
  userInfo.classList.toggle('active');
}

// Hide dropdown when clicking outside
document.addEventListener('click', (e) => {
  const menu = document.querySelector('.edusafaris-user-menu');
    if (menu && !menu.contains(e.target)) {
        document.getElementById('userDropdown').classList.remove('show');
        document.querySelector('.edusafaris-user-info').classList.remove('active');
    }
});

document.addEventListener("DOMContentLoaded", () => {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll(".edusafaris-nav-links a");

  navLinks.forEach(link => {
    // Match exact path or allow partial matches (optional)
    if (link.getAttribute("href") === currentPath || 
        (currentPath.startsWith(link.getAttribute("href")) && link.getAttribute("href") !== "/")) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });
});
