// ── Mobile Menu ──────────────────────────
function toggleMenu() {
  const nav = document.getElementById('navLinks');
  if (nav) nav.classList.toggle('open');
}

// ── Auto-dismiss flash messages ──────────
setTimeout(() => {
  const fc = document.getElementById('flashContainer');
  if (fc) {
    try {
      fc.animate([{opacity:1},{opacity:0}],{duration:500}).onfinish = () => fc.remove();
    } catch(e) { fc.remove(); }
  }
}, 4000);

// ── Navbar scroll shadow ─────────────────
window.addEventListener('scroll', () => {
  const nb = document.querySelector('.navbar');
  if (nb) nb.style.boxShadow = window.scrollY > 10
    ? '0 4px 24px rgba(0,0,0,0.35)'
    : '0 4px 20px rgba(0,0,0,0.25)';
});