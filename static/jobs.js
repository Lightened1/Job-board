// Add smooth scrolling effect to internal links
const scroll = new SmoothScroll('a[href*="#"]', {
  speed: 800,
  speedAsDuration: true
});

// Toggle mobile navigation
const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');

navToggle.addEventListener('click', () => {
  navMenu.classList.toggle('show');
});