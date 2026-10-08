/* AgroConnect – product cards, shop filtering/search/sort/pagination, quick view, product detail page */
const Catalog = {
  _promise: null,
  load() { return Catalog._promise || (Catalog._promise = fetch('/api/products').then(r => r.json())); }
};

function productCard(p) {
  const out = p.stock <= 0, low = p.stock > 0 && p.stock <= 10;
  return `<article class="product-card" data-id="${p.id}">
    <div class="pc-media">
      <a href="/product/${p.id}" aria-label="${escapeHTML(p.name)}"><img class="product-image" src="${p.image}" alt="${escapeHTML(p.name)}" loading="lazy" onerror="this.onerror=null;this.src='/static/images/logo/placeholder.svg'"></a>
      ${p.discount ? `<span class="badge-discount">${p.discount}% OFF</span>` : ''}
      <button class="wish-btn" data-wish="${p.id}" data-name="${escapeHTML(p.name)}" aria-label="Add ${escapeHTML(p.name)} to wishlist" aria-pressed="false"><i class="fa-regular fa-heart"></i></button>
      <button class="quick-btn" data-quick="${p.id}" type="button">Quick View</button>
    </div>
    <div class="pc-body">
      <span class="pc-cat">${escapeHTML(p.category)}</span>
      <h3 class="pc-name"><a href="/product/${p.id}">${escapeHTML(p.name)}</a></h3>
      <div class="rating-row"><span class="stars">${starsHTML(p.rating)}</span><span>${p.rating.toFixed(1)} <small>(${p.reviews})</small></span></div>
      <p class="pc-seller">Seller: ${escapeHTML(p.seller)}</p>
      <div class="pc-price"><strong>${formatINR(p.sale_price)}</strong>${p.discount ? `<s>${formatINR(p.price)}</s>` : ''}</div>
      <p class="stock-line ${out ? 'out' : low ? 'low' : 'in'}">${out ? 'Out of stock' : low ? `Only ${p.stock} left` : 'In stock'}</p>
      <button class="btn btn-primary btn-block" data-add="${p.id}" ${out ? 'disabled' : ''}><i class="fa-solid fa-cart-plus"></i> ${out ? 'Out of Stock' : 'Add to Cart'}</button>
    </div></article>`;
}

/* ---------- Shop page ---------- */
const Shop = {
  PER_PAGE: 12, page: 1, all: [], filtered: [],
  state() {
    const $ = id => document.getElementById(id);
    return {
      q: $('shopSearch').value.trim().toLowerCase(), category: document.querySelector('[name=category]:checked').value,
      min: parseFloat($('minPrice').value) || 0, max: parseFloat($('maxPrice').value) || Infinity,
      brand: $('brandFilter').value, seller: $('sellerFilter').value, rating: +document.querySelector('[name=rating]:checked').value,
      inStock: $('inStock').checked, organic: $('organicOnly').checked, discount: $('discountOnly').checked, sort: $('sortBy').value
    };
  },
  apply(resetPage = true) {
    const s = Shop.state(); if (resetPage) Shop.page = 1;
    let list = Shop.all.filter(p =>
      (!s.q || [p.name, p.category, p.seller, p.tags, p.brand].join(' ').toLowerCase().includes(s.q)) &&
      (!s.category || p.category_slug === s.category) && p.sale_price >= s.min && p.sale_price <= s.max &&
      (!s.brand || p.brand === s.brand) && (!s.seller || p.seller === s.seller) && p.rating >= s.rating &&
      (!s.inStock || p.stock > 0) && (!s.organic || p.organic) && (!s.discount || p.discount >= 15));
    const sorters = { 'price-asc': (a, b) => a.sale_price - b.sale_price, 'price-desc': (a, b) => b.sale_price - a.sale_price,
      rating: (a, b) => b.rating - a.rating, discount: (a, b) => b.discount - a.discount, newest: (a, b) => b.created.localeCompare(a.created), featured: (a, b) => (b.rating * Math.log(b.reviews + 2)) - (a.rating * Math.log(a.reviews + 2)) };
    Shop.filtered = list.sort(sorters[s.sort]); Shop.render();
    const url = new URL(location); s.q ? url.searchParams.set('q', document.getElementById('shopSearch').value.trim()) : url.searchParams.delete('q');
    s.category ? url.searchParams.set('category', s.category) : url.searchParams.delete('category'); history.replaceState(null, '', url);
  },
  render() {
    const grid = document.querySelector('[data-shop]'), total = Shop.filtered.length, pages = Math.max(1, Math.ceil(total / Shop.PER_PAGE));
    Shop.page = Math.min(Shop.page, pages);
    const slice = Shop.filtered.slice((Shop.page - 1) * Shop.PER_PAGE, Shop.page * Shop.PER_PAGE);
    document.getElementById('resultCount').textContent = `${total} product${total === 1 ? '' : 's'} found`;
    document.getElementById('noResults').hidden = total > 0; grid.hidden = total === 0;
    grid.innerHTML = slice.map(productCard).join(''); Wishlist.paint();
    const pag = document.getElementById('pagination');
    pag.innerHTML = pages <= 1 ? '' : `<button ${Shop.page === 1 ? 'disabled' : ''} data-p="${Shop.page - 1}" aria-label="Previous page"><i class="fa-solid fa-chevron-left"></i></button>` +
      Array.from({ length: pages }, (_, i) => `<button class="${i + 1 === Shop.page ? 'active' : ''}" data-p="${i + 1}" aria-label="Page ${i + 1}" ${i + 1 === Shop.page ? 'aria-current="page"' : ''}>${i + 1}</button>`).join('') +
      `<button ${Shop.page === pages ? 'disabled' : ''} data-p="${Shop.page + 1}" aria-label="Next page"><i class="fa-solid fa-chevron-right"></i></button>`;
  },
  async init() {
    const params = new URLSearchParams(location.search);
    if (params.get('q')) document.getElementById('shopSearch').value = params.get('q');
    const cat = params.get('category'); if (cat) { const r = document.querySelector(`[name=category][value="${CSS.escape(cat)}"]`); if (r) r.checked = true; }
    Shop.all = await Catalog.load(); Shop.apply();
    const f = document.getElementById('filters');
    f.addEventListener('change', () => Shop.apply());
    f.addEventListener('input', e => { if (e.target.type === 'number') Shop.apply(); });
    document.getElementById('shopSearch').addEventListener('input', () => Shop.apply());
    document.getElementById('sortBy').addEventListener('change', () => Shop.apply());
    document.getElementById('pagination').addEventListener('click', e => { const b = e.target.closest('[data-p]'); if (b && !b.disabled) { Shop.page = +b.dataset.p; Shop.render(); window.scrollTo({ top: 120, behavior: 'smooth' }); } });
    const reset = () => { document.getElementById('shopSearch').value = ''; f.querySelectorAll('input[type=number]').forEach(i => i.value = ''); f.querySelectorAll('select').forEach(s => s.selectedIndex = 0);
      f.querySelectorAll('input[type=checkbox]').forEach(c => c.checked = false); f.querySelector('[name=category][value=""]').checked = true; f.querySelector('[name=rating][value="0"]').checked = true; Shop.apply(); };
    document.getElementById('resetFilters').onclick = reset; document.getElementById('clearSearch').onclick = reset;
    const toggle = open => { f.classList.toggle('open', open); document.getElementById('filterBackdrop').classList.toggle('show', open); };
    document.getElementById('openFilters').onclick = () => toggle(true); document.getElementById('closeFilters').onclick = () => toggle(false);
    document.getElementById('applyFilters').onclick = () => toggle(false); document.getElementById('filterBackdrop').onclick = () => toggle(false);
  }
};

/* ---------- Quick view ---------- */
const QuickView = {
  async open(id) {
    const p = (await Catalog.load()).find(x => x.id === id); if (!p) return;
    const m = document.getElementById('quickView'), out = p.stock <= 0;
    m.innerHTML = `<div class="modal-box qv"><button class="modal-close" data-close aria-label="Close">×</button>
      <img src="${p.image}" alt="${escapeHTML(p.name)}"><div><span class="pc-cat">${escapeHTML(p.category)}</span><h2>${escapeHTML(p.name)}</h2>
      <div class="rating-row"><span class="stars">${starsHTML(p.rating)}</span> ${p.rating.toFixed(1)} (${p.reviews})</div>
      <p class="muted">Seller: ${escapeHTML(p.seller)}</p><p>${escapeHTML(p.description)}…</p>
      <div class="pc-price lg"><strong>${formatINR(p.sale_price)}</strong>${p.discount ? `<s>${formatINR(p.price)}</s><span class="save">${p.discount}% off</span>` : ''}</div>
      <div class="qv-actions"><button class="btn btn-primary" data-add="${p.id}" ${out ? 'disabled' : ''}>${out ? 'Out of Stock' : 'Add to Cart'}</button><a class="btn btn-outline" href="/product/${p.id}">View Details</a></div></div></div>`;
    m.hidden = false; document.body.classList.add('no-scroll'); m.querySelector('[data-close]').focus();
  },
  close() { const m = document.getElementById('quickView'); m.hidden = true; m.innerHTML = ''; document.body.classList.remove('no-scroll'); }
};
document.addEventListener('click', e => {
  const q = e.target.closest('[data-quick]'); if (q) QuickView.open(+q.dataset.quick);
  if (e.target.closest('#quickView [data-close]') || e.target.id === 'quickView') QuickView.close();
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') QuickView.close(); });

/* ---------- Product detail page ---------- */
function initProductPage() {
  const root = document.querySelector('.pd'); if (!root) return;
  const pid = +root.dataset.pid, stock = +root.dataset.stock, qty = document.getElementById('qtyInput');
  const clamp = () => { qty.value = Math.max(1, Math.min(stock || 1, parseInt(qty.value) || 1)); };
  document.getElementById('qtyMinus').onclick = () => { qty.value = (parseInt(qty.value) || 1) - 1; clamp(); };
  document.getElementById('qtyPlus').onclick = () => { qty.value = (parseInt(qty.value) || 1) + 1; clamp(); };
  qty.addEventListener('change', clamp);
  document.getElementById('addToCartBtn').onclick = () => Cart.add(pid, +qty.value);
  document.getElementById('buyNowBtn').onclick = async () => { if (await Cart.add(pid, +qty.value)) location.href = '/checkout'; };

  document.querySelectorAll('.thumb').forEach(t => t.onclick = () => {
    document.getElementById('mainImage').src = t.dataset.src;
    document.querySelectorAll('.thumb').forEach(x => x.classList.toggle('active', x === t));
  });

  // Tabs
  const showTab = key => {
    document.querySelectorAll('.tab').forEach(t => { const on = t.dataset.tab === key; t.classList.toggle('active', on); t.setAttribute('aria-selected', on); });
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'tab-' + key));
  };
  document.querySelectorAll('.tab').forEach(t => t.onclick = () => showTab(t.dataset.tab));
  document.querySelectorAll('[data-tab-link]').forEach(a => a.onclick = () => showTab(a.dataset.tabLink));

  // Delivery estimator
  document.getElementById('pinForm').onsubmit = async e => {
    e.preventDefault(); const out = document.getElementById('pinResult'), pin = document.getElementById('pin').value.trim();
    const res = await api('/api/check-delivery?pincode=' + encodeURIComponent(pin));
    out.className = res.ok ? 'ok' : 'bad';
    out.innerHTML = res.ok ? `<i class="fa-solid fa-check"></i> Delivery available<br><small>Estimated delivery: ${res.days} days</small>` : escapeHTML(res.error || 'Delivery not available.');
  };

  // Reviews
  const form = document.getElementById('reviewForm');
  if (form) form.onsubmit = async e => {
    e.preventDefault();
    const rating = form.querySelector('[name=rating]:checked'), title = form.elements.title.value.trim(), body = form.elements.body.value.trim();
    if (!rating || !title || !body) { toast('Please fill all required fields.', 'error'); return; }
    const res = await api(`/product/${pid}/review`, { method: 'POST', body: { rating: +rating.value, title, body } });
    if (!res.ok) { toast(res.error, 'error'); return; }
    document.getElementById('noReviews')?.remove();
    document.getElementById('reviewList').insertAdjacentHTML('afterbegin', `<article class="review"><div class="review-top"><strong>${escapeHTML(res.name)}</strong><span class="stars">${starsHTML(res.rating)}</span><time>Just now</time></div><h4>${escapeHTML(res.title)}</h4><p>${escapeHTML(res.body)}</p></article>`);
    document.getElementById('avgRating').textContent = res.avg; document.getElementById('reviewCount').textContent = res.count; form.reset(); toast('Thanks! Your review has been posted.');
  };
}

/* ---------- Generic product grids (home, related, deals) ---------- */
async function initGrids() {
  for (const grid of document.querySelectorAll('[data-product-grid]:not([data-shop])')) {
    let list = await Catalog.load();
    if (grid.dataset.category) list = list.filter(p => p.category_slug === grid.dataset.category && p.id !== +grid.dataset.exclude);
    if (grid.dataset.deals) list = list.filter(p => p.discount > 0).sort((a, b) => b.discount - a.discount);
    if (grid.dataset.featured) {
      const wanted = ['Hybrid Maize Seeds', 'Organic Vermicompost', 'NPK 19:19:19 Water Soluble Fertilizer', 'Drip Irrigation Kit (1 Acre)', 'Pressure Hand Sprayer 5 L', 'Paddy Seeds (Rice) - BPT 5204', 'Organic Pesticide - Panchagavya Spray', 'Mini Garden Tool Kit (5 pcs)'];
      const picked = wanted.map(n => list.find(p => p.name === n)).filter(Boolean);
      list = picked.length >= 4 ? picked : list;
    }
    grid.innerHTML = list.slice(0, +grid.dataset.limit || 8).map(productCard).join('') || '<p class="muted">No products found.</p>';
    Wishlist.paint();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('[data-shop]')) Shop.init();
  initGrids(); initProductPage();
});
