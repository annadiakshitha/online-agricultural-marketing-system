/* AgroConnect – wishlist (localStorage, mirrored to the server for logged-in users) */
const Wishlist = {
  ids() { return Store.get('agro_wish'); },
  has(id) { return Wishlist.ids().includes(id); },

  toggle(id, name) {
    name = name || (document.querySelector(`[data-wish="${id}"]`) || {dataset: {}}).dataset.name || 'Product';
    let ids = Wishlist.ids();
    if (ids.includes(id)) {
      ids = ids.filter(i => i !== id); Store.set('agro_wish', ids);
      api('/remove-wishlist', { method: 'POST', body: { product_id: id } }); toast(tr('removed_wish', name));
    } else {
      ids.push(id); Store.set('agro_wish', ids);
      api('/add-wishlist', { method: 'POST', body: { product_id: id } }); toast('♡ ' + tr('added_wish', name));
    }
    Wishlist.paint();
  },

  paint() {
    document.querySelectorAll('[data-wish]').forEach(btn => {
      const on = Wishlist.has(+btn.dataset.wish);
      btn.classList.toggle('active', on); btn.setAttribute('aria-pressed', on);
      const icon = btn.querySelector('i'); if (icon) icon.className = (on ? 'fa-solid' : 'fa-regular') + ' fa-heart';
    });
  },

  async renderPage() {
    const grid = document.getElementById('wishlistGrid'), empty = document.getElementById('wishEmpty');
    const ids = Wishlist.ids();
    if (!ids.length) { grid.innerHTML = ''; empty.hidden = false; return; }
    empty.hidden = true;
    const products = await (await fetch('/api/cart-items?ids=' + ids.join(','))).json();
    grid.innerHTML = products.map(p => `
      <article class="wish-card" data-id="${p.id}">
        <a href="/product/${p.id}"><img src="${p.image}" alt="${escapeHTML(p.name)}"></a>
        <div><a href="/product/${p.id}"><h3>${escapeHTML(p.name)}</h3></a><span class="muted">${escapeHTML(p.seller)}</span>
        <div class="price-sm">${formatINR(p.sale_price)} ${p.discount ? `<s>${formatINR(p.price)}</s>` : ''}</div>
        <div class="wish-actions"><button class="btn btn-primary btn-sm" data-move="${p.id}" ${p.stock <= 0 ? 'disabled' : ''}>${p.stock <= 0 ? 'Out of stock' : 'Move to Cart'}</button>
        <button class="btn btn-outline btn-sm" data-remove="${p.id}">Remove</button></div></div>
      </article>`).join('');
    grid.onclick = async e => {
      const mv = e.target.closest('[data-move]'), rm = e.target.closest('[data-remove]');
      if (mv) { const id = +mv.dataset.move; if (await Cart.add(id, 1)) { Store.set('agro_wish', Wishlist.ids().filter(i => i !== id)); api('/remove-wishlist', { method: 'POST', body: { product_id: id } }); Wishlist.renderPage(); } }
      if (rm) { Wishlist.toggle(+rm.dataset.remove, rm.closest('.wish-card').querySelector('h3').textContent); Wishlist.renderPage(); }
    };
  }
};

document.addEventListener('click', e => {
  const btn = e.target.closest('[data-wish]');
  if (btn) { e.preventDefault(); e.stopPropagation(); Wishlist.toggle(+btn.dataset.wish); }
});
document.addEventListener('DOMContentLoaded', async () => {
  // Merge server-side wishlist into the local one when logged in
  if (window.AGRO.loggedIn) {
    try { const server = await (await fetch('/api/wishlist')).json(); const merged = [...new Set([...Wishlist.ids(), ...server])]; if (merged.length !== Wishlist.ids().length) Store.set('agro_wish', merged); } catch (e) { /* offline */ }
  }
  Wishlist.paint();
});
