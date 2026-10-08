/* Equipment rental: booking form, cancel, seller actions */
(() => {
  const $ = id => document.getElementById(id);
  const root = $('rent');
  if (root) {
    const id = root.dataset.id, s = $('rStart'), e = $('rEnd'), q = $('rQuote'), go = $('rGo'), form = $('rentForm');
    let ok = false;
    s.addEventListener('change', () => { if (!e.value || e.value < s.value) e.value = s.value; e.min = s.value; check(); }); e.addEventListener('change', check);
    async function check() {
      ok = false; if (go) go.disabled = true; if (!s.value || !e.value) return;
      const r = await api(`/api/rental/${id}/availability?start=${s.value}&end=${e.value}`);
      if (!r.ok) { q.className = 'quote no'; q.textContent = r.error; return; }
      q.className = 'quote ' + (r.available ? 'ok' : 'no');
      q.innerHTML = r.available
        ? `<div class="row"><span>Rent (${r.days} day${r.days > 1 ? 's' : ''})</span><span>${formatINR(r.rent)}</span></div><div class="row"><span>Refundable deposit</span><span>${formatINR(r.deposit)}</span></div><div class="row t"><span>Total</span><span>${formatINR(r.total)}</span></div><small>${r.free} unit(s) free for these dates</small>`
        : 'Sorry, this equipment is fully booked for some of these dates. Try different dates.';
      ok = r.available; if (go) go.disabled = !ok;
    }
    if (form && go) form.addEventListener('submit', async ev => {
      ev.preventDefault(); if (!ok) return; const err = $('rError'); err.hidden = true; go.disabled = true;
      const r = await api(`/api/rental/${id}/book`, { method: 'POST', body: { start: s.value, end: e.value, name: $('rName').value, phone: $('rPhone').value, address: $('rAddr').value, note: $('rNote').value } });
      if (r.ok) { toast('✓ ' + r.message); setTimeout(() => location.href = r.redirect, 900); } else { go.disabled = false; err.textContent = r.error || 'Could not book.'; err.hidden = false; }
    });
  }
  document.addEventListener('click', async ev => {
    const c = ev.target.closest('[data-cancel]'), st = ev.target.closest('[data-set]');
    if (c && confirm('Cancel this booking?')) { const r = await api(`/api/rental/booking/${c.dataset.cancel}/cancel`, { method: 'POST', body: {} }); if (r.ok) location.reload(); else toast(r.error || 'Could not cancel', 'error'); }
    if (st) { const [bid, status] = st.dataset.set.split(':'); const r = await api(`/api/rental/booking/${bid}/status`, { method: 'POST', body: { status } }); if (r.ok) location.reload(); else toast(r.error || 'Could not update', 'error'); }
  });
})();
