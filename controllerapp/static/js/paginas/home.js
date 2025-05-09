// Script para a página inicial

document.addEventListener('DOMContentLoaded', function() {
  // Inicialização do carrossel
  var mainCarousel = new bootstrap.Carousel(document.getElementById('mainCarousel'), {
    interval: 6000,
    wrap: true
  });
  
  // Animação para contador de estatísticas
  function animateCounters() {
    const counters = document.querySelectorAll('.count-up');
    const speed = 200; // Quanto menor, mais rápido
    
    counters.forEach(counter => {
      const target = +counter.getAttribute('data-count');
      let count = 0;
      
      const updateCount = () => {
        const increment = target / speed;
        
        if (count < target) {
          count += increment;
          counter.innerText = Math.ceil(count);
          setTimeout(updateCount, 1);
        } else {
          counter.innerText = target;
        }
      };
      
      updateCount();
    });
  }
  
  // Observador de interseção para iniciar a animação quando os contadores estiverem visíveis
  const statsSection = document.querySelector('.stats-card');
  
  if (statsSection) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounters();
          observer.unobserve(entry.target);
        }
      });
    }, {threshold: 0.5});
    
    observer.observe(statsSection);
  }
});