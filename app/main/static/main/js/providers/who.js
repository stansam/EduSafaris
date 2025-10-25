document.addEventListener('DOMContentLoaded', function() {
  // Intersection Observer for scroll animations
  const observerOptions = {
    threshold: 0.2,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
      }
    });
  }, observerOptions);
  
  // Observe all cards
  document.querySelectorAll('.providers-join-card').forEach(card => {
    observer.observe(card);
  });
  
  // Touch device card flip functionality
  const cards = document.querySelectorAll('.providers-join-card');
  
  cards.forEach(card => {
    // Check if device supports touch
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (isTouchDevice) {
      card.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Remove flipped class from all other cards
        cards.forEach(otherCard => {
          if (otherCard !== card) {
            otherCard.classList.remove('flipped');
          }
        });
        
        // Toggle flipped class on clicked card
        this.classList.toggle('flipped');
      });
    }
  });
  
  // Close flipped cards when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.providers-join-card')) {
      cards.forEach(card => {
        card.classList.remove('flipped');
      });
    }
  });
  
  // Add subtle parallax effect on scroll
  let ticking = false;
  
  window.addEventListener('scroll', function() {
    if (!ticking) {
      window.requestAnimationFrame(function() {
        const scrolled = window.pageYOffset;
        const joinSection = document.querySelector('.providers-join-wrapper');
        
        if (joinSection) {
          const rect = joinSection.getBoundingClientRect();
          if (rect.top < window.innerHeight && rect.bottom > 0) {
            const cards = joinSection.querySelectorAll('.providers-join-card');
            cards.forEach((card, index) => {
              const speed = 0.5 + (index * 0.1);
              const yPos = -(scrolled * speed * 0.05);
              card.style.transform = `translateY(${yPos}px)`;
            });
          }
        }
        
        ticking = false;
      });
      
      ticking = true;
    }
  });
});