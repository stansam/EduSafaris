const tabBtns = document.querySelectorAll('.teach-trips-tab-btn');
const tabContents = document.querySelectorAll('.teach-trips-tab-content');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        
        // Remove active class from all tabs and contents
        tabBtns.forEach(b => b.classList.remove('active-trip-tab'));
        tabContents.forEach(content => {
            content.style.display = 'none';
        });
        
        // Add active class to clicked tab
        btn.classList.add('active-trip-tab');
        
        // Show corresponding content
        const contentId = targetTab + '-content';
        const activeContent = document.getElementById(contentId);
        if (activeContent) {
            activeContent.style.display = 'block';
        }
    });
});

// Add click animations to buttons
const allBtns = document.querySelectorAll('.teach-trip-btn');
allBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.background = 'rgba(255, 255, 255, 0.5)';
        ripple.style.transform = 'scale(0)';
        ripple.style.animation = 'ripple 0.6s ease-out';
        ripple.style.pointerEvents = 'none';
        
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
});

// Simulate real-time updates for statistics
function updateStats() {
    const statValues = document.querySelectorAll('.teach-trips-stat-value');
    statValues.forEach(stat => {
        stat.style.transition = 'transform 0.3s';
        stat.style.transform = 'scale(1.05)';
        setTimeout(() => {
            stat.style.transform = 'scale(1)';
        }, 300);
    });
}

// Update stats every 30 seconds (simulated)
setInterval(updateStats, 30000);

// Add CSS animation for ripple effect
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Add keyboard navigation support
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        const activeTab = document.querySelector('.teach-trips-tab-btn.active-trip-tab');
        const tabs = Array.from(tabBtns);
        const currentIndex = tabs.indexOf(activeTab);
        let newIndex;
        
        if (e.key === 'ArrowRight') {
            newIndex = (currentIndex + 1) % tabs.length;
        } else {
            newIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        }
        
        tabs[newIndex].click();
        tabs[newIndex].focus();
    }
});