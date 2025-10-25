document.addEventListener('DOMContentLoaded', function() {
  const stars = document.querySelectorAll('.edu-remark-star');
  
  // Add interactive star animations
  stars.forEach((star, index) => {
    star.addEventListener('mouseenter', function() {
      // Create sparkle effect
      const sparkle = document.createElement('div');
      sparkle.className = 'edu-remark-sparkle';
      sparkle.style.cssText = `
        position: absolute;
        width: 4px;
        height: 4px;
        background: #f39c12;
        border-radius: 50%;
        pointer-events: none;
        animation: eduRemarkSparkle 0.6s ease-out forwards;
      `;
      
      const rect = this.getBoundingClientRect();
      sparkle.style.left = rect.left + rect.width / 2 + 'px';
      sparkle.style.top = rect.top + rect.height / 2 + 'px';
      
      document.body.appendChild(sparkle);
      
      setTimeout(() => sparkle.remove(), 600);
    });
  });
  
  // Intersection Observer for scroll animation
  const section = document.querySelector('.edu-remark-section');
  const observerOptions = {
    threshold: 0.3,
    rootMargin: '0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('edu-remark-visible');
      }
    });
  }, observerOptions);
  
  observer.observe(section);
});

// Add sparkle animation style dynamically
(() => {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes eduRemarkSparkle {
      0% {
        transform: scale(0) translate(0, 0);
        opacity: 1;
      }
      100% {
        transform: scale(1) translate(${Math.random() * 40 - 20}px, ${Math.random() * 40 - 20}px);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);
})();