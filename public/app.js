const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add("is-visible");
  });
}, { threshold: 0.15 });

document.querySelectorAll(".project-card").forEach((card, index) => {
  card.style.animationDelay = `${index * 110}ms`;
  observer.observe(card);
});
