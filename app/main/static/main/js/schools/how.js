document.addEventListener('DOMContentLoaded', function() {
  const steps = document.querySelectorAll('.edu-how-step');
  
  // Add interactive hover effects
  steps.forEach((step, index) => {
    step.addEventListener('mouseenter', function() {
      this.style.zIndex = '10';
    });
    
    step.addEventListener('mouseleave', function() {
      this.style.zIndex = '1';
    });
    
    // Add click handler for mobile
    step.addEventListener('click', function() {
      steps.forEach(s => s.classList.remove('edu-how-active'));
      this.classList.add('edu-how-active');
    });
  });
  
  // Intersection Observer for scroll animations
  const observerOptions = {
    threshold: 0.2,
    rootMargin: '0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
      }
    });
  }, observerOptions);
  
  steps.forEach(step => observer.observe(step));
});