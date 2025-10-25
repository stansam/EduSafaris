document.addEventListener('DOMContentLoaded', function() {
  const cards = document.querySelectorAll('.edu-why-card[data-aos]');
  
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('aos-animate');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);
  
  cards.forEach((card, index) => {
    // Stagger animation delays
    setTimeout(() => {
      observer.observe(card);
    }, index * 50);
  });
});