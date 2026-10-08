/* AgroConnect – multi-step checkout */
(async function () {
  const lines = await Cart.lines();
  if (!lines.length) { location.href = window.AGRO.urls.cart; return; }
  document.getElementById('cartSummary').innerHTML = Cart.summaryHTML(Cart.totals(lines), true);

  let step = 1; const total = 4;
  const $ = id => document.getElementById(id), errBox = $('checkoutError');
  const panels = document.querySelectorAll('.step-panel'), steps = document.querySelectorAll('#stepper li');
  const method = () => document.querySelector('[name=pay]:checked').value;
  const showError = msg => { errBox.textContent = msg; errBox.hidden = !msg; };

  function validate(n) {
    if (n === 1) {
      if (!$('c_name').value.trim() || !$('c_phone').value.trim() || !$('c_email').value.trim()) return 'Please fill all required fields.';
      if (!/^(\+91[\s-]?)?[6-9]\d{9}$/.test($('c_phone').value.trim())) return 'Enter a valid 10-digit Indian mobile number.';
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test($('c_email').value.trim())) return 'Enter a valid email address.';
    }
    if (n === 2) {
      if (['a_line1', 'a_village', 'a_district', 'a_state', 'a_pin'].some(id => !$(id).value.trim())) return 'Please fill all required fields.';
      if (!/^[1-9]\d{5}$/.test($('a_pin').value.trim())) return 'Enter a valid 6-digit pincode.';
    }
    if (n === 3) {
      if (method() === 'UPI' && !/^[\w.\-]{2,}@[a-zA-Z]{2,}$/.test($('upi').value.trim())) return 'Enter a valid UPI ID (e.g. name@okbank).';
      if (method() === 'Credit/Debit Card') {
        if (!/^\d{13,19}$/.test($('cardNo').value.replace(/\s/g, ''))) return 'Enter a valid card number.';
        if (!/^(0[1-9]|1[0-2])\s*\/\s*\d{2}$/.test($('cardExp').value.trim())) return 'Enter card expiry as MM/YY.';
        if (!/^\d{3,4}$/.test($('cardCvv').value)) return 'Enter a valid CVV.';
      }
    }
    return '';
  }

  function review() {
    $('reviewBox').innerHTML = `
      <div class="review-block"><h3>Items</h3>${lines.map(l => `<div class="line-item"><img src="${l.p.image}" alt="${escapeHTML(l.p.name)}"><div><strong>${escapeHTML(l.p.name)}</strong><span class="muted">Qty ${l.qty} × ${formatINR(l.p.sale_price)}</span></div><strong>${formatINR(l.p.sale_price * l.qty)}</strong></div>`).join('')}</div>
      <div class="review-block"><h3>Deliver to</h3><p>${escapeHTML($('c_name').value)} · ${escapeHTML($('c_phone').value)}<br>${escapeHTML($('a_line1').value)}, ${escapeHTML($('a_village').value)}, ${escapeHTML($('a_district').value)}, ${escapeHTML($('a_state').value)} - ${escapeHTML($('a_pin').value)}</p></div>
      <div class="review-block"><h3>Payment</h3><p>${escapeHTML(method())}</p></div>`;
  }

  function go(n) {
    step = n; showError('');
    panels.forEach(p => p.classList.toggle('active', +p.dataset.step === n));
    steps.forEach((s, i) => { s.classList.toggle('active', i + 1 === n); s.classList.toggle('done', i + 1 < n); });
    $('prevStep').hidden = n === 1; $('nextStep').hidden = n === total; $('placeOrder').hidden = n !== total;
    if (n === total) review(); window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  $('nextStep').onclick = () => { const e = validate(step); if (e) return showError(e); go(step + 1); };
  $('prevStep').onclick = () => go(step - 1);
  document.querySelectorAll('[name=pay]').forEach(r => r.onchange = () => {
    $('pay-UPI').hidden = method() !== 'UPI'; $('pay-Card').hidden = method() !== 'Credit/Debit Card';
    document.querySelectorAll('.pay-opt').forEach(o => o.classList.toggle('selected', o.querySelector('input').checked));
  });
  document.querySelector('.pay-opt').classList.add('selected');
  $('cardNo').addEventListener('input', e => { e.target.value = e.target.value.replace(/\D/g, '').slice(0, 19).replace(/(.{4})/g, '$1 ').trim(); });

  $('checkoutForm').addEventListener('submit', async e => {
    e.preventDefault(); const btn = $('placeOrder');
    for (let n = 1; n <= 3; n++) { const err = validate(n); if (err) { go(n); return showError(err); } }
    btn.disabled = true; btn.textContent = 'Placing order…';
    const res = await api('/place-order', { method: 'POST', body: {
      customer: { name: $('c_name').value, phone: $('c_phone').value, email: $('c_email').value },
      address: { line1: $('a_line1').value, village: $('a_village').value, district: $('a_district').value, state: $('a_state').value, pincode: $('a_pin').value },
      payment: { method: method(), upi: $('upi').value, card_number: $('cardNo').value, expiry: $('cardExp').value, cvv: $('cardCvv').value },
      coupon: (window.AGRO_COUPON && window.AGRO_COUPON.code) || null,
      items: lines.map(l => ({ id: l.p.id, qty: l.qty })) } });
    if (res.ok) { Cart.clear(); try { sessionStorage.setItem('agro_order_ok', '1'); } catch (e) {} location.href = res.redirect; }
    else { btn.disabled = false; btn.textContent = 'Place Order'; showError(res.error || 'Could not place the order.'); }
  });
  go(1);
})();
