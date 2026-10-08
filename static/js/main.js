/* AgroConnect – core utilities: storage, toast, API helper, navbar, counters, reveal animations */
const Store = {
  get(key) { try { return JSON.parse(localStorage.getItem(key)) || []; } catch (e) { return []; } },
  set(key, value) { localStorage.setItem(key, JSON.stringify(value)); Store.updateBadges(); },
  updateBadges() {
    const cartQty = Store.get('agro_cart').reduce((n, i) => n + i.qty, 0);
    document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = cartQty; el.hidden = cartQty === 0; });
    const wish = Store.get('agro_wish').length;
    document.querySelectorAll('[data-wish-count]').forEach(el => { el.textContent = wish; el.hidden = wish === 0; });
  }
};

const formatINR = n => '₹' + Math.round(n).toLocaleString('en-IN');
const escapeHTML = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

async function api(url, { method = 'GET', body, form } = {}) {
  const headers = { 'X-CSRF-Token': window.AGRO.csrf, 'X-Requested-With': 'fetch' };
  const opts = { method, headers };
  if (form) opts.body = form;
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  try {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({ ok: false, error: 'Unexpected server response.' }));
    if (res.status === 401 && data.error) { toast(data.error, 'error'); }
    return { status: res.status, ...data };
  } catch (e) { return { ok: false, error: 'Network error. Please check your connection.' }; }
}

const tr = (k, name) => (window.I18N ? I18N.t(k, { name }) : k);
function toast(message, type = 'success') {
  const wrap = document.getElementById('toastWrap');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`; el.setAttribute('role', 'status'); el.textContent = message;
  wrap.appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, 2800);
}

document.addEventListener('DOMContentLoaded', () => {
  Store.updateBadges();
  try { if (sessionStorage.getItem('agro_order_ok')) { sessionStorage.removeItem('agro_order_ok'); setTimeout(() => toast('✓ ' + tr('order_ok')), 400); } } catch (e) {}

  // Sticky navbar appearance
  const nav = document.getElementById('navbar');
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 10);
  onScroll(); window.addEventListener('scroll', onScroll, { passive: true });

  // Mobile menu, search bar, account dropdown
  const menuBtn = document.getElementById('menuToggle'), links = document.getElementById('navLinks');
  menuBtn.addEventListener('click', () => { const open = links.classList.toggle('open'); menuBtn.setAttribute('aria-expanded', open); });
  const searchBar = document.getElementById('searchBar');
  document.getElementById('searchToggle').addEventListener('click', () => {
    searchBar.classList.toggle('open'); if (searchBar.classList.contains('open')) document.getElementById('navSearch').focus();
  });
  const accBtn = document.getElementById('accountBtn'), dd = document.getElementById('accountDropdown');
  accBtn.addEventListener('click', e => { e.stopPropagation(); const o = dd.classList.toggle('open'); accBtn.setAttribute('aria-expanded', o); });
  document.addEventListener('click', () => { dd.classList.remove('open'); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { dd.classList.remove('open'); searchBar.classList.remove('open'); links.classList.remove('open'); } });

  // Scroll reveal
  const io = new IntersectionObserver(entries => entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('visible'); io.unobserve(en.target); } }), { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));

  // Animated counters
  const counterIO = new IntersectionObserver(entries => entries.forEach(en => {
    if (!en.isIntersecting) return;
    const el = en.target, target = +el.dataset.counter, suffix = el.dataset.suffix || '', start = performance.now(), dur = 1400;
    const tick = now => { const p = Math.min((now - start) / dur, 1); el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + (p === 1 ? suffix : ''); if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick); counterIO.unobserve(el);
  }), { threshold: 0.4 });
  document.querySelectorAll('[data-counter]').forEach(el => counterIO.observe(el));

  // Newsletter
  const nl = document.getElementById('newsletterForm');
  if (nl) nl.addEventListener('submit', e => {
    e.preventDefault(); const input = document.getElementById('nlEmail');
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(input.value)) { toast('Please enter a valid email address.', 'error'); return; }
    toast('Thanks for subscribing to AgroConnect insights!'); nl.reset();
  });

  // Flash messages auto-dismiss
  document.querySelectorAll('.flash').forEach(f => setTimeout(() => f.remove(), 6000));

  // Render star ratings
  renderStars(document);
});

function starsHTML(rating) {
  let html = '';
  for (let i = 1; i <= 5; i++) html += `<i class="fa-${rating >= i - 0.25 ? 'solid fa-star' : rating >= i - 0.75 ? 'solid fa-star-half-stroke' : 'regular fa-star'}"></i>`;
  return html;
}
function renderStars(root) {
  root.querySelectorAll('[data-stars]').forEach(el => { el.innerHTML = starsHTML(+el.dataset.stars); el.setAttribute('aria-label', `${el.dataset.stars} out of 5 stars`); });
}
