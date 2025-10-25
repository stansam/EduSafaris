document.addEventListener('DOMContentLoaded', function() {
  // Intersection Observer for scroll-triggered animations
  const observerOptions = {
    threshold: 0.2,
    rootMargin: '0px 0px -100px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const steps = entry.target.querySelectorAll('.providers-started-step');
        steps.forEach((step, index) => {
          setTimeout(() => {
            step.style.animationPlayState = 'running';
          }, index * 200);
        });
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);
  
  const timeline = document.querySelector('.providers-started-timeline');
  if (timeline) {
    observer.observe(timeline);
  }
  
  // Add hover effect for step numbers
  const stepNumbers = document.querySelectorAll('.providers-started-step-number');
  stepNumbers.forEach(number => {
    number.addEventListener('mouseenter', function() {
      this.style.transform = 'scale(1.15) rotate(5deg)';
    });
    
    number.addEventListener('mouseleave', function() {
      this.style.transform = 'scale(1) rotate(0deg)';
    });
  });
});