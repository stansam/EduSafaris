document.addEventListener('DOMContentLoaded', function() {
  const heroButtons = document.querySelectorAll('.edu-hero-btn');
  
  heroButtons.forEach(button => {
    button.addEventListener('click', function() {
      const btnText = this.textContent;
      console.log(`${btnText} clicked`);
      
      // Add ripple effect
      const ripple = document.createElement('span');
      ripple.classList.add('edu-hero-ripple');
      this.appendChild(ripple);
      
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + 'px';
      
      setTimeout(() => ripple.remove(), 600);
    });
  });
});