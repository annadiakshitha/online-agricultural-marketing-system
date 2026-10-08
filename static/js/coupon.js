/* Checkout coupon box. Works alongside checkout.js (which reads window.AGRO_COUPON when placing the order). */
(() => {
  const input = document.getElementById('couponCode'); if (!input) return;
  const btn = document.getElementById('couponApply'), msg = document.getElementById('couponMsg'), offers = document.getElementById('couponOffers');
  const items = () => Cart.items().map(i => ({ id: i.id, qty: i.qty }));
  let baseTotal = null;
  function paint(total, discount, code) {
    const sum = document.getElementById('cartSummary'); if (!sum) return;
    const totalRow = sum.querySelector('.sum-row.total'); if (!totalRow) return;
    if (baseTotal === null) baseTotal = totalRow.lastElementChild.textContent;
    let row = sum.querySelector('.sum-row.coupon');
    if (!discount) { if (row) row.remove(); totalRow.lastElementChild.textContent = baseTotal; return; }
    if (!row) { row = document.createElement('div'); row.className = 'sum-row coupon'; totalRow.before(row); }
    row.innerHTML = `<span>Coupon (${escapeHTML(code)})</span><span>−${formatINR(discount)}</span>`;
    totalRow.lastElementChild.textContent = formatINR(total);
  }
  async function apply(code) {
    code = (code || '').trim().toUpperCase(); if (!code) { msg.className = 'coupon-msg err'; msg.textContent = 'Enter a coupon code.'; return; }
    btn.disabled = true; const r = await api('/api/coupon/validate', { method: 'POST', body: { code, items: items() } }); btn.disabled = false;
    if (r.ok) { window.AGRO_COUPON = { code: r.code }; msg.className = 'coupon-msg ok'; msg.textContent = `✓ ${r.code} applied: you save ${formatINR(r.discount)}`; paint(r.total, r.discount, r.code); toast('✓ Coupon ' + r.code + ' applied'); }
    else { window.AGRO_COUPON = null; paint(0, 0); msg.className = 'coupon-msg err'; msg.textContent = r.error || 'Could not apply the coupon.'; }
  }
  btn.addEventListener('click', () => apply(input.value));
  input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); apply(input.value); } });
  input.addEventListener('input', () => { if (window.AGRO_COUPON) { window.AGRO_COUPON = null; paint(0, 0); msg.textContent = ''; } });
  fetch('/api/coupons/available').then(r => r.json()).then(list => {
    offers.innerHTML = list.map(c => `<button type="button" data-code="${escapeHTML(c.code)}" title="${escapeHTML(c.description || '')}">${escapeHTML(c.code)}</button>`).join('');
  }).catch(() => {});
  offers.addEventListener('click', e => { const b = e.target.closest('button'); if (b) { input.value = b.dataset.code; apply(b.dataset.code); } });
})();
