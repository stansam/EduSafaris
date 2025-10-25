document.addEventListener('DOMContentLoaded', function() {
  const primaryBtn = document.querySelector('.providers-btn-primary');
  const secondaryBtn = document.querySelector('.providers-btn-secondary');
  
  if (primaryBtn) {
    primaryBtn.addEventListener('click', function() {
      // Add your "Become a Provider" action here
      console.log('Become a Provider clicked');
    });
  }
  
  if (secondaryBtn) {
    secondaryBtn.addEventListener('click', function() {
      // Add your "Learn More" action here
      console.log('Learn More clicked');
    });
  }
  
  // Counter animation for stats
  const animateCounter = (element, target) => {
    const duration = 2000;
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        element.textContent = element.textContent.includes('+') ? target + '+' : target + '%';
        clearInterval(timer);
      } else {
        const suffix = element.textContent.includes('+') ? '+' : element.textContent.includes('%') ? '%' : '';
        element.textContent = Math.floor(current) + suffix;
      }
    }, 16);
  };
  
  // Trigger counter animation when stats come into view
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const number = entry.target.querySelector('.providers-stat-number');
        const text = number.textContent;
        const value = parseInt(text.replace(/\D/g, ''));
        
        if (text.includes('K')) {
          animateCounter(number, value);
        } else {
          animateCounter(number, value);
        }
        
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  
  document.querySelectorAll('.providers-stat-card').forEach(card => {
    observer.observe(card);
  });
});