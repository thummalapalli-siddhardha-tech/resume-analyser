document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.btn, .link-btn');
  buttons.forEach((btn) => {
    btn.addEventListener('mouseenter', () => btn.style.opacity = '0.96');
    btn.addEventListener('mouseleave', () => btn.style.opacity = '1');
  });
});
