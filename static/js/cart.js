/* AgroConnect – cart logic (localStorage) + cart page rendering */
const Cart = {
  items() { return Store.get('agro_cart'); },

  async add(id, qty = 1) {
    const res = await api('/add-to-cart', { method: 'POST', body: { product_id: id, quantity: qty } });
    if (!res.ok) { toast(res.error || 'Could not add to cart.', 'error'); return false; }
    const cart = Cart.items(), line = cart.find(i => i.id === id), max = res.max;
    if (line) line.qty = Math.min(line.qty + qty, max); else cart.push({ id, qty: Math.min(qty, max) });
    Store.set('agro_cart', cart);
    toast('✓ ' + tr('added_cart', res.product.name));
    return true;
  },

  setQty(id, qty, max) {
    const cart = Cart.items(), line = cart.find(i => i.id === id); if (!line) return;
    line.qty = Math.max(1, Math.min(qty, max || 99)); Store.set('agro_cart', cart);
  },

  async remove(id, name = 'Product') {
    Store.set('agro_cart', Cart.items().filter(i => i.id !== id));
    api('/remove-from-cart', { method: 'POST', body: { product_id: id } });
    toast(tr('removed_cart', name));
  },

  clear() { Store.set('agro_cart', []); },

  /* Mirrors backend.calc_totals */
  totals(lines) {
    const A = window.AGRO;
    const subtotal = lines.reduce((n, l) => n + l.p.price * l.qty, 0);
    const net = lines.reduce((n, l) => n + l.p.sale_price * l.qty, 0);
    const delivery = net === 0 || net >= A.freeAbove ? 0 : A.deliveryFee;
    const tax = Math.round(net * A.taxPercent / 100);
    return { subtotal, discount: subtotal - net, delivery, tax, total: net + delivery + tax };
  },

  async lines() {
    const cart = Cart.items(); if (!cart.length) return [];
    const products = await (await fetch('/api/cart-items?ids=' + cart.map(i => i.id).join(','))).json();
    const valid = cart.map(i => ({ ...i, p: products.find(p => p.id === i.id) })).filter(l => l.p);
    if (valid.length !== cart.length) Store.set('agro_cart', valid.map(({ id, qty }) => ({ id, qty })));
    valid.forEach(l => { if (l.qty > l.p.stock) l.qty = Math.max(1, l.p.stock); });
    return valid;
  },

  summaryHTML(t, checkout = false) {
    const row = (label, val, cls = '') => `<div class="sum-row ${cls}"><span>${label}</span><span>${val}</span></div>`;
    return `<h2>Order Summary</h2>
      ${row('Subtotal', formatINR(t.subtotal))}
      ${row('Discount', '−' + formatINR(t.discount), 'green')}
      ${row('Delivery', t.delivery ? formatINR(t.delivery) : 'Free')}
      ${row(`Tax (GST ${window.AGRO.taxPercent}%)`, formatINR(t.tax))}
      ${row('Total', formatINR(t.total), 'total')}
      ${checkout ? '' : `<a class="btn btn-primary btn-block btn-lg" href="/checkout">Proceed to Checkout</a>
      <a class="btn btn-outline btn-block" href="${window.AGRO.urls.shop}">Continue Shopping</a>`}
      <p class="hint"><i class="fa-solid fa-lock"></i> Secure checkout · Free delivery above ${formatINR(window.AGRO.freeAbove)}</p>`;
  },

  async renderPage() {
    const itemsEl = document.getElementById('cartItems'), sumEl = document.getElementById('cartSummary');
    const layout = document.getElementById('cartLayout'), empty = document.getElementById('cartEmpty');
    const lines = await Cart.lines();
    if (!lines.length) { layout.hidden = true; empty.hidden = false; return; }
    layout.hidden = false; empty.hidden = true;
    itemsEl.innerHTML = lines.map(l => `
      <article class="cart-row" data-id="${l.p.id}">
        <a href="/product/${l.p.id}"><img src="${l.p.image}" alt="${escapeHTML(l.p.name)}"></a>
        <div class="cart-info"><a href="/product/${l.p.id}"><h3>${escapeHTML(l.p.name)}</h3></a><span class="muted">Seller: ${escapeHTML(l.p.seller)}</span>
          <span class="price-sm">${formatINR(l.p.sale_price)} ${l.p.discount ? `<s>${formatINR(l.p.price)}</s>` : ''}</span></div>
        <div class="qty" role="group" aria-label="Quantity"><button data-act="dec" aria-label="Decrease quantity">−</button><span aria-live="polite">${l.qty}</span><button data-act="inc" aria-label="Increase quantity">+</button></div>
        <strong class="line-total">${formatINR(l.p.sale_price * l.qty)}</strong>
        <button class="icon-btn danger" data-act="rm" aria-label="Remove ${escapeHTML(l.p.name)}"><i class="fa-regular fa-trash-can"></i></button>
      </article>`).join('');
    sumEl.innerHTML = Cart.summaryHTML(Cart.totals(lines));
    itemsEl.onclick = async e => {
      const btn = e.target.closest('[data-act]'); if (!btn) return;
      const id = +btn.closest('.cart-row').dataset.id, line = lines.find(l => l.p.id === id);
      if (btn.dataset.act === 'rm') await Cart.remove(id, line.p.name);
      else {
        const next = line.qty + (btn.dataset.act === 'inc' ? 1 : -1);
        if (next > line.p.stock) { toast('Product is out of stock beyond this quantity.', 'error'); return; }
        Cart.setQty(id, next, line.p.stock);
      }
      Cart.renderPage();
    };
  }
};

document.addEventListener('click', e => {
  const btn = e.target.closest('[data-add]');
  if (btn) { e.preventDefault(); Cart.add(+btn.dataset.add, 1); }
});
